from app.services.executor import run_pipeline_code


def test_simple_code_executes_and_returns_success(tmp_path):
    out = str(tmp_path / "out.csv").replace("\\", "/")
    code = f"""import pandas as pd
from pathlib import Path
df = pd.DataFrame({{"a": [1, 2, 3]}})
Path("{out}").parent.mkdir(parents=True, exist_ok=True)
df.to_csv("{out}", index=False)
"""
    result = run_pipeline_code(code, timeout=30)
    assert result.status == "success"
    assert (tmp_path / "out.csv").exists()


def test_syntax_error_returns_failed():
    result = run_pipeline_code("def broken(: pass", timeout=5)
    assert result.status == "failed"
    assert result.error_message != ""


def test_blocked_import_returns_failed():
    result = run_pipeline_code("import os\nos.system('echo hi')\n", timeout=5)
    assert result.status == "failed"
    assert "Blocked" in result.error_message


def test_timeout_kills_process():
    code = "import time\nwhile True:\n    time.sleep(1)\n"
    result = run_pipeline_code(code, timeout=3)
    assert result.status == "failed"
    assert "timeout" in result.error_message.lower()


def test_runtime_error_captured():
    code = "raise ValueError('bad data')\n"
    result = run_pipeline_code(code, timeout=5)
    assert result.status == "failed"
    assert result.error_message != ""
