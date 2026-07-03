import json
import os
import litellm
from app.core.config import settings
from app.schemas.pipeline import PipelinePlan

litellm.drop_params = True  # ignore unsupported params silently

SYSTEM_PROMPT = """You are a data pipeline expert. Given a user's request and available data source schemas, output a valid JSON pipeline plan.

RULES:
1. Only reference column names that exist in the provided schemas.
2. Break the request into atomic steps: one operation per step.
3. Each extract step reads one source. Each transform step applies one operation.
4. If the request is ambiguous or references unknown columns, output: {"clarifying_questions": ["<question>"]}
5. Output ONLY valid JSON matching the PipelinePlan schema below. No markdown, no explanation.

PipelinePlan schema:
{
  "pipeline_id": "<string>",
  "name": "<string>",
  "nl_prompt": "<string>",
  "version": 1,
  "steps": [
    {
      "step_id": "step_001",
      "type": "extract|transform|load|validate",
      "operation": "read_csv|read_excel|read_json|read_parquet|filter|join|aggregate|sort|rename|drop_columns|fill_nulls|dedup|cast|write_csv|write_parquet",
      "params": {},
      "output_alias": "<snake_case_name>",
      "description": "<human readable>",
      "depends_on": ["<step_id>"]
    }
  ]
}

Supported operations and their required params:
- read_csv: {"source": "<file_path>"}
- read_excel: {"source": "<file_path>"}
- read_json: {"source": "<file_path>"}
- read_parquet: {"source": "<file_path>"}
- filter: {"input": "<alias>", "condition": "<pandas boolean expression>"}
- join: {"left": "<alias>", "right": "<alias>", "on": "<col>", "how": "inner|left|right|outer"}
- aggregate: {"input": "<alias>", "group_by": ["<col>"], "agg": {"<col>": "sum|mean|count|min|max"}}
- sort: {"input": "<alias>", "by": ["<col>"], "ascending": true}
- rename: {"input": "<alias>", "columns": {"old_name": "new_name"}}
- drop_columns: {"input": "<alias>", "columns": ["<col>"]}
- fill_nulls: {"input": "<alias>", "column": "<col>", "value": <value>}
- dedup: {"input": "<alias>", "subset": ["<col>"]}
- cast: {"input": "<alias>", "column": "<col>", "dtype": "int|float|str|datetime"}
- write_csv: {"input": "<alias>", "destination": "outputs/<filename>.csv"}
- write_parquet: {"input": "<alias>", "destination": "outputs/<filename>.parquet"}
"""


def build_schema_context(schema_context: list[dict]) -> str:
    lines = []
    for src in schema_context:
        lines.append(f"\nSource: {src['name']}")
        for col in src["columns"]:
            samples = ", ".join(str(v) for v in col["sample_values"][:5])
            lines.append(f"  - {col['name']} ({col['dtype']}) samples: [{samples}]")
    return "\n".join(lines)


# Maps a model prefix to the (settings attr, env var) that holds its API key.
_PROVIDER_KEYS: list[tuple[tuple[str, ...], str, str]] = [
    (("groq/",), "groq_api_key", "GROQ_API_KEY"),
    (("gemini/",), "gemini_api_key", "GEMINI_API_KEY"),
    (("claude", "anthropic/"), "anthropic_api_key", "ANTHROPIC_API_KEY"),
    (("openrouter/",), "openrouter_api_key", "OPENROUTER_API_KEY"),
]


def _ensure_provider_key(model: str) -> bool:
    """Push the API key env var for `model`'s provider.

    Returns True if a key is available (or the provider is unknown, so we let
    LiteLLM decide), False if the provider is recognised but no key is set — in
    which case the caller skips this model rather than crashing the whole chain.
    """
    for prefixes, attr, env_var in _PROVIDER_KEYS:
        if model.startswith(prefixes):
            key = getattr(settings, attr, "") or os.environ.get(env_var)
            if key:
                os.environ[env_var] = key
                return True
            return False
    return True  # unknown prefix — let LiteLLM handle auth


def _model_chain() -> list[str]:
    """Primary model followed by configured fallbacks, de-duplicated in order."""
    chain = [settings.llm_model]
    for m in settings.llm_fallbacks.split(","):
        m = m.strip()
        if m and m not in chain:
            chain.append(m)
    return chain


async def _call_llm(messages: list[dict]) -> str:
    last_error: Exception | None = None
    attempted = 0
    for model in _model_chain():
        if not _ensure_provider_key(model):
            continue  # no key configured for this provider; try the next model
        attempted += 1
        try:
            response = await litellm.acompletion(
                model=model,
                messages=messages,
                temperature=0.1,
                timeout=60,
            )
            return response.choices[0].message.content or ""
        except Exception as e:  # deprecation, outage, rate limit — fall back
            last_error = e

    if attempted == 0:
        raise RuntimeError(
            "No API key is configured for LLM_MODEL or any fallback. "
            "Set the matching provider key in the .env file."
        )
    raise RuntimeError(
        f"All configured LLM models failed. Last error: {last_error}"
    ) from last_error


def _parse_response(
    raw: str, pipeline_id: str, pipeline_name: str, nl_prompt: str
) -> "PipelinePlan | list[str]":
    text = raw.strip()
    # Strip markdown code fences if the model wraps the JSON
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.rsplit("```", 1)[0].strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        raise ValueError(f"LLM returned non-JSON response: {raw[:200]}")

    if "clarifying_questions" in data:
        return data["clarifying_questions"]

    data["pipeline_id"] = pipeline_id
    data["name"] = pipeline_name
    data["nl_prompt"] = nl_prompt
    return PipelinePlan(**data)


async def parse_nl_to_plan(
    nl_prompt: str,
    schema_context: list[dict],
    pipeline_id: str,
    pipeline_name: str,
) -> "PipelinePlan | list[str]":
    schema_text = build_schema_context(schema_context)
    user_message = f"Available data sources:\n{schema_text}\n\nUser request: {nl_prompt}"
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    raw = await _call_llm(messages)
    try:
        return _parse_response(raw, pipeline_id, pipeline_name, nl_prompt)
    except (ValueError, Exception):
        # Retry once with a correction nudge
        messages.append({"role": "assistant", "content": raw})
        messages.append({
            "role": "user",
            "content": "Your response was not valid JSON. Output ONLY the JSON object, no other text.",
        })
        raw2 = await _call_llm(messages)
        return _parse_response(raw2, pipeline_id, pipeline_name, nl_prompt)
