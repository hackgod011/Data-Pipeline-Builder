import ast
from typing import Final

BLOCKED_MODULES: Final[frozenset[str]] = frozenset({
    "os", "sys", "subprocess", "shutil", "socket", "requests",
    "urllib", "http", "ftplib", "smtplib", "imaplib", "poplib",
    "pickle", "shelve", "marshal", "ctypes", "cffi", "importlib",
    "builtins", "__builtin__",
})

BLOCKED_BUILTINS: Final[frozenset[str]] = frozenset({
    "open", "exec", "eval", "__import__", "compile", "input",
    "breakpoint", "exit", "quit",
})


class SandboxViolationError(Exception):
    pass


class _ImportChecker(ast.NodeVisitor):
    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            root = alias.name.split(".")[0]
            if root in BLOCKED_MODULES:
                raise SandboxViolationError(
                    f"Blocked import: '{root}' is not allowed in pipeline code"
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        root = (node.module or "").split(".")[0]
        if root in BLOCKED_MODULES:
            raise SandboxViolationError(
                f"Blocked import: '{root}' is not allowed in pipeline code"
            )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id in BLOCKED_BUILTINS:
            raise SandboxViolationError(
                f"Blocked builtin: '{node.func.id}' is not allowed in pipeline code"
            )
        self.generic_visit(node)


def validate_code(code: str) -> None:
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise SandboxViolationError(f"Syntax error in generated code: {exc}") from exc
    _ImportChecker().visit(tree)
