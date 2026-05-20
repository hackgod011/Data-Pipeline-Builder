import pytest
from app.core.sandbox import validate_code, SandboxViolationError


def test_safe_pandas_code_passes():
    code = "import pandas as pd\ndf = pd.DataFrame({'a': [1, 2]})\n"
    validate_code(code)  # should not raise


def test_os_import_blocked():
    with pytest.raises(SandboxViolationError, match="os"):
        validate_code("import os\nos.system('ls')\n")


def test_subprocess_import_blocked():
    with pytest.raises(SandboxViolationError, match="subprocess"):
        validate_code("import subprocess\n")


def test_open_builtin_blocked():
    with pytest.raises(SandboxViolationError, match="open"):
        validate_code("f = open('/etc/passwd', 'r')\n")


def test_network_import_blocked():
    with pytest.raises(SandboxViolationError, match="socket"):
        validate_code("import socket\n")
