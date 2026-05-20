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


def _set_api_key() -> None:
    """Push the right env var for whichever provider is configured."""
    model = settings.llm_model
    if model.startswith("groq/"):
        if settings.groq_api_key:
            os.environ["GROQ_API_KEY"] = settings.groq_api_key
        elif not os.environ.get("GROQ_API_KEY"):
            raise RuntimeError("GROQ_API_KEY is not configured. Set it in the .env file.")
    elif model.startswith("gemini/"):
        if settings.gemini_api_key:
            os.environ["GEMINI_API_KEY"] = settings.gemini_api_key
        elif not os.environ.get("GEMINI_API_KEY"):
            raise RuntimeError("GEMINI_API_KEY is not configured. Set it in the .env file.")
    elif model.startswith("claude") or model.startswith("anthropic/"):
        if settings.anthropic_api_key:
            os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
        elif not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY is not configured. Set it in the .env file.")
    elif model.startswith("openrouter/"):
        if settings.openrouter_api_key:
            os.environ["OPENROUTER_API_KEY"] = settings.openrouter_api_key
        elif not os.environ.get("OPENROUTER_API_KEY"):
            raise RuntimeError("OPENROUTER_API_KEY is not configured. Set it in the .env file.")


async def _call_llm(messages: list[dict]) -> str:
    _set_api_key()
    response = await litellm.acompletion(
        model=settings.llm_model,
        messages=messages,
        temperature=0.1,
        timeout=60,
    )
    return response.choices[0].message.content or ""


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
