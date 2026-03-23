#!/opt/homebrew/bin/python3
"""Static trust scoring for ASH registry Python tools."""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from typing import Any


BASE_SCORE = 100
NETWORK_IMPORT_MODULES = {"requests", "urllib", "httpx", "aiohttp"}
SENSITIVE_ENV_RE = re.compile(
    r".*(_KEY|_SECRET|_TOKEN|_PASSWORD)$",
    re.IGNORECASE,
)
SYSTEM_PATH_MARKERS = ("/etc/", "/usr/", "/bin/", "~/.ssh/")
DANGEROUS_BUILTINS = {"eval", "exec", "compile"}
SUBPROCESS_CALLS = {
    "run",
    "call",
    "check_call",
    "check_output",
    "Popen",
}


class TrustAnalyzer(ast.NodeVisitor):
    """Collect findings and derived permissions from a Python AST."""

    def __init__(self, source: str) -> None:
        self.lines = source.splitlines()
        self.findings: list[dict[str, Any]] = []
        self.permissions = {
            "network": False,
            "filesystem": False,
            "shell": False,
            "env_vars": False,
        }
        self.os_aliases = {"os"}
        self.getenv_aliases: set[str] = set()
        self.environ_aliases: set[str] = set()
        self.subprocess_aliases = {"subprocess"}
        self.subprocess_member_aliases: set[str] = set()
        self.shutil_aliases = {"shutil"}
        self.shutil_member_aliases: set[str] = set()

    def _snippet(self, lineno: int) -> str:
        if 1 <= lineno <= len(self.lines):
            return self.lines[lineno - 1].strip()
        return ""

    def _add_finding(self, finding: str, impact: int, lineno: int) -> None:
        self.findings.append(
            {
                "finding": finding,
                "impact": impact,
                "line": lineno,
                "snippet": self._snippet(lineno),
            }
        )

    @staticmethod
    def _resolve_name(node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parent = TrustAnalyzer._resolve_name(node.value)
            return f"{parent}.{node.attr}" if parent else node.attr
        return ""

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            root = alias.name.split(".")[0]
            bound_name = alias.asname or root
            if root in NETWORK_IMPORT_MODULES:
                self._add_finding(f"Network import: {alias.name}", -5, node.lineno)
                self.permissions["network"] = True
            if root == "socket":
                self._add_finding(f"Raw socket import: {alias.name}", -10, node.lineno)
                self.permissions["network"] = True
            if root == "os":
                self.os_aliases.add(bound_name)
            if root == "subprocess":
                self.subprocess_aliases.add(bound_name)
            if root == "shutil":
                self.shutil_aliases.add(bound_name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        root = module.split(".")[0] if module else ""
        for alias in node.names:
            bound_name = alias.asname or alias.name
            if root in NETWORK_IMPORT_MODULES:
                self._add_finding(
                    f"Network import: from {module} import {alias.name}",
                    -5,
                    node.lineno,
                )
                self.permissions["network"] = True
            if root == "socket":
                self._add_finding(
                    f"Raw socket import: from {module} import {alias.name}",
                    -10,
                    node.lineno,
                )
                self.permissions["network"] = True
            if root == "os":
                if alias.name == "getenv":
                    self.getenv_aliases.add(bound_name)
                if alias.name == "environ":
                    self.environ_aliases.add(bound_name)
            if root == "subprocess":
                self.subprocess_member_aliases.add(bound_name)
            if root == "shutil":
                self.shutil_member_aliases.add(bound_name)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func_name = self._resolve_name(node.func)
        if func_name in DANGEROUS_BUILTINS:
            self._add_finding(f"Dangerous builtin: {func_name}()", -30, node.lineno)

        if func_name in {"open", "builtins.open"}:
            self._check_open_write(node)
        if self._is_path_write_text(node.func):
            self._add_finding("Filesystem write: Path.write_text()", -10, node.lineno)
            self.permissions["filesystem"] = True
        if self._is_os_remove(func_name):
            self._add_finding(f"Filesystem write: {func_name}()", -10, node.lineno)
            self.permissions["filesystem"] = True
        if self._is_shutil_call(func_name):
            self._add_finding(f"Filesystem write: {func_name}()", -10, node.lineno)
            self.permissions["filesystem"] = True
        if self._is_subprocess_call(func_name):
            self._check_shell_true(node, func_name)
        if self._is_sensitive_env_call(func_name):
            self._check_sensitive_env_call(node, func_name)

        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        if self._is_os_environ_access(node.value):
            key = self._constant_string(node.slice)
            if key and SENSITIVE_ENV_RE.match(key):
                self._add_finding(f"Sensitive env var read: {key}", -15, node.lineno)
                self.permissions["env_vars"] = True
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str):
            for marker in SYSTEM_PATH_MARKERS:
                if marker in node.value:
                    self._add_finding(
                        f"System path reference: {node.value}",
                        -15,
                        node.lineno,
                    )
                    break
        self.generic_visit(node)

    def _check_open_write(self, node: ast.Call) -> None:
        mode = None
        if len(node.args) >= 2:
            mode = self._constant_string(node.args[1])
        for keyword in node.keywords:
            if keyword.arg == "mode":
                mode = self._constant_string(keyword.value)
        if mode and any(flag in mode for flag in ("w", "a")):
            self._add_finding(f"Filesystem write: open(mode='{mode}')", -10, node.lineno)
            self.permissions["filesystem"] = True

    def _check_shell_true(self, node: ast.Call, func_name: str) -> None:
        for keyword in node.keywords:
            if keyword.arg == "shell" and self._constant_bool(keyword.value) is True:
                self._add_finding(
                    f"Shell subprocess: {func_name}(shell=True)",
                    -20,
                    node.lineno,
                )
                self.permissions["shell"] = True
                break

    def _check_sensitive_env_call(self, node: ast.Call, func_name: str) -> None:
        if not node.args:
            return
        key = self._constant_string(node.args[0])
        if key and SENSITIVE_ENV_RE.match(key):
            self._add_finding(f"Sensitive env var read: {key}", -15, node.lineno)
            self.permissions["env_vars"] = True

    def _is_path_write_text(self, func: ast.AST) -> bool:
        return isinstance(func, ast.Attribute) and func.attr == "write_text"

    def _is_os_remove(self, func_name: str) -> bool:
        if not func_name:
            return False
        if func_name == "remove":
            return False
        for alias in self.os_aliases:
            if func_name == f"{alias}.remove":
                return True
        return False

    def _is_shutil_call(self, func_name: str) -> bool:
        if not func_name:
            return False
        for alias in self.shutil_aliases:
            if func_name.startswith(f"{alias}."):
                return True
        return func_name in self.shutil_member_aliases

    def _is_subprocess_call(self, func_name: str) -> bool:
        if not func_name:
            return False
        if func_name in self.subprocess_member_aliases:
            return func_name in SUBPROCESS_CALLS
        for alias in self.subprocess_aliases:
            for call_name in SUBPROCESS_CALLS:
                if func_name == f"{alias}.{call_name}":
                    return True
        return False

    def _is_sensitive_env_call(self, func_name: str) -> bool:
        if not func_name:
            return False
        if func_name in self.getenv_aliases:
            return True
        for alias in self.os_aliases:
            if func_name == f"{alias}.getenv" or func_name == f"{alias}.environ.get":
                return True
        for alias in self.environ_aliases:
            if func_name == f"{alias}.get":
                return True
        return False

    def _is_os_environ_access(self, value: ast.AST) -> bool:
        name = self._resolve_name(value)
        for alias in self.os_aliases:
            if name == f"{alias}.environ":
                return True
        return name in self.environ_aliases

    @staticmethod
    def _constant_string(node: ast.AST | None) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

    @staticmethod
    def _constant_bool(node: ast.AST | None) -> bool | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, bool):
            return node.value
        return None


def analyze_file(path: str) -> dict[str, Any]:
    resolved_path = os.path.expanduser(path)
    try:
        with open(resolved_path, "r", encoding="utf-8") as handle:
            source = handle.read()
    except OSError as exc:
        return {
            "file": path,
            "score": 0,
            "findings": [
                {
                    "finding": f"File read error: {exc.strerror}",
                    "impact": -100,
                    "line": 0,
                    "snippet": "",
                }
            ],
            "permissions": {
                "network": False,
                "filesystem": False,
                "shell": False,
                "env_vars": False,
            },
        }

    try:
        tree = ast.parse(source, filename=resolved_path)
    except SyntaxError as exc:
        return {
            "file": path,
            "score": 0,
            "findings": [
                {
                    "finding": f"Syntax error: {exc.msg}",
                    "impact": -100,
                    "line": exc.lineno or 0,
                    "snippet": "",
                }
            ],
            "permissions": {
                "network": False,
                "filesystem": False,
                "shell": False,
                "env_vars": False,
            },
        }

    analyzer = TrustAnalyzer(source)
    analyzer.visit(tree)

    unique_findings = []
    seen: set[tuple[str, int, str]] = set()
    for finding in analyzer.findings:
        key = (finding["finding"], finding["line"], finding["snippet"])
        if key in seen:
            continue
        seen.add(key)
        unique_findings.append(finding)

    score = BASE_SCORE + sum(item["impact"] for item in unique_findings)
    score = max(0, score)

    return {
        "file": path,
        "score": score,
        "findings": unique_findings,
        "permissions": analyzer.permissions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze a Python file and compute an ASH trust score.",
    )
    parser.add_argument("path", help="Python file to analyze")
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    args = parser.parse_args()

    result = analyze_file(args.path)
    json.dump(result, sys.stdout, indent=2 if args.pretty else None)
    sys.stdout.write("\n")
    return 0 if result["score"] >= 50 else 1


if __name__ == "__main__":
    sys.exit(main())
