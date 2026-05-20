import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.core.sandbox import SandboxViolationError, validate_code

_STRIP_ENV_KEYS = {"PYTHONSTARTUP", "PYTHONDONTWRITEBYTECODE"}


@dataclass
class ExecutionResult:
    status: str  # success | failed
    error_message: str = ""
    stdout: str = ""
    stderr: str = ""
    output_file_path: str | None = None


def run_pipeline_code(
    code: str,
    timeout: int = 60,
    output_dir: Path | None = None,
) -> ExecutionResult:
    # Gate 1: AST sandbox check
    try:
        validate_code(code)
    except SandboxViolationError as exc:
        return ExecutionResult(status="failed", error_message=str(exc))

    # Gate 2: subprocess execution with timeout
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(code)
        script_path = tmp.name

    # Build a clean environment — strip a few dangerous overrides but keep
    # the full PATH so Python can find its stdlib on all platforms (Windows/Linux/Mac).
    safe_env = {k: v for k, v in os.environ.items() if k not in _STRIP_ENV_KEYS}

    try:
        proc = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=safe_env,
        )
        if proc.returncode == 0:
            return ExecutionResult(
                status="success",
                stdout=proc.stdout[-4000:],
                stderr=proc.stderr[-2000:],
            )
        return ExecutionResult(
            status="failed",
            error_message=(proc.stderr or proc.stdout)[-2000:],
            stdout=proc.stdout[-4000:],
            stderr=proc.stderr[-2000:],
        )
    except subprocess.TimeoutExpired:
        return ExecutionResult(
            status="failed",
            error_message=f"Execution timeout after {timeout} seconds",
        )
    except Exception as exc:
        return ExecutionResult(status="failed", error_message=str(exc))
    finally:
        Path(script_path).unlink(missing_ok=True)


@dataclass
class StepExecutionLog:
    step_id: str
    description: str
    status: str = "pending"
    start_time: str | None = None
    end_time: str | None = None
    rows_in: int | None = None
    rows_out: int | None = None
    message: str = ""
