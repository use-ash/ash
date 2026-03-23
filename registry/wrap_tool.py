#!/opt/homebrew/bin/python3
"""Generate an ASH-wrapped FastMCP server for a registry tool."""

from __future__ import annotations

import argparse
import json
import stat
import textwrap
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
INDEX_PATH = SCRIPT_DIR / "index.json"
PYTHON = "/opt/homebrew/bin/python3"
REPO_ROOT = SCRIPT_DIR.parents[1]


WRAPPER_TEMPLATE = """#!/opt/homebrew/bin/python3
from __future__ import annotations

import functools
import importlib.util
import inspect
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

REPO_ROOT = Path({repo_root!r})
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ash.servers.safety.ash_safety_server import SECRET_PATTERNS

REGISTERED_TOOL_NAME = {tool_name!r}
ORIGINAL_SERVER_COMMAND = {original_command!r}
ORIGINAL_SERVER_ARGS = {original_args!r}
SCAN_INPUTS = {scan_inputs!r}
SCAN_OUTPUTS = {scan_outputs!r}
AUDIT_LOG_PATH = Path("~/.ash/audit.jsonl").expanduser()

PLACEHOLDER_RE = re.compile(
    r"your_\\w+_here|example|testkey|placeholder|REDACTED|xxx+|dummy|changeme|fake",
    re.IGNORECASE,
)


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _ensure_audit_dir() -> None:
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def _redact_match(value: str) -> str:
    if len(value) <= 8:
        return "****"
    return value[:4] + "****" + value[-2:]


def _scan_text(text: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines() or [text], start=1):
        for pattern_name, pattern in SECRET_PATTERNS:
            for match in pattern.finditer(line):
                matched = match.group(0)
                if PLACEHOLDER_RE.search(matched):
                    continue
                findings.append(
                    {{
                        "pattern": pattern_name,
                        "redacted": _redact_match(matched),
                        "line": line_number,
                    }}
                )
    return findings


def _redact_text(text: str, findings: list[dict[str, Any]]) -> str:
    redacted = text
    for pattern_name, pattern in SECRET_PATTERNS:
        def _replace(match: re.Match[str]) -> str:
            matched = match.group(0)
            if PLACEHOLDER_RE.search(matched):
                return matched
            return _redact_match(matched)

        redacted = pattern.sub(_replace, redacted)
    return redacted


def _audit(tool_name: str, tool_input: str, result_status: str, findings: list[dict[str, Any]], stage: str) -> None:
    entry = {{
        "timestamp": _now(),
        "tool_name": tool_name,
        "input": tool_input,
        "result_status": result_status,
        "findings": findings,
        "stage": stage,
        "registered_tool": REGISTERED_TOOL_NAME,
    }}
    try:
        _ensure_audit_dir()
        with AUDIT_LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\\n")
    except OSError:
        pass


def _block_message(stage: str, findings: list[dict[str, Any]]) -> str:
    patterns = ", ".join(sorted({{finding["pattern"] for finding in findings}}))
    return (
        f"ASH blocked this tool call: detected potential secrets in {{stage}} "
        f"({{patterns}})."
    )


def _load_original_mcp() -> FastMCP:
    if not ORIGINAL_SERVER_ARGS:
        raise RuntimeError(f"No server args configured for {{REGISTERED_TOOL_NAME}}")

    if "python" not in ORIGINAL_SERVER_COMMAND.lower():
        raise RuntimeError(
            "Generated wrappers currently support Python FastMCP servers only."
        )

    server_path = Path(ORIGINAL_SERVER_ARGS[0]).expanduser()
    if not server_path.is_absolute():
        server_path = (REPO_ROOT / server_path).resolve()
    if not server_path.exists():
        raise FileNotFoundError(f"Original server not found: {{server_path}}")

    server_dir = server_path.parent
    if str(server_dir) not in sys.path:
        sys.path.insert(0, str(server_dir))

    module_name = f"ash_wrapped_{{REGISTERED_TOOL_NAME.replace('-', '_')}}_original"
    spec = importlib.util.spec_from_file_location(module_name, server_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load original server: {{server_path}}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    original_mcp = getattr(module, "mcp", None)
    if not isinstance(original_mcp, FastMCP):
        raise RuntimeError(
            f"Original server {{server_path}} does not expose a FastMCP instance named 'mcp'"
        )
    return original_mcp


ORIGINAL_MCP = _load_original_mcp()
mcp = FastMCP(f"ASH Wrapped: {{REGISTERED_TOOL_NAME}}")


def _wrap_tool(original_tool: Any) -> Any:
    original_fn = original_tool.fn
    original_signature = inspect.signature(original_fn)
    original_annotations = dict(getattr(original_fn, "__annotations__", {{}}))
    context_kwarg = getattr(original_tool, "context_kwarg", None)

    @functools.wraps(original_fn)
    async def wrapped_tool(*args: Any, **kwargs: Any) -> Any:
        tool_input = dict(kwargs)
        if context_kwarg:
            tool_input.pop(context_kwarg, None)

        raw_input = str(tool_input)
        input_findings = _scan_text(raw_input) if SCAN_INPUTS else []
        if input_findings:
            _audit(
                original_tool.name,
                _redact_text(raw_input, input_findings),
                "blocked",
                input_findings,
                "input",
            )
            return _block_message("input", input_findings)

        try:
            result = original_fn(**kwargs)
            if inspect.isawaitable(result):
                result = await result
        except Exception:
            _audit(original_tool.name, raw_input, "clean", [], "error")
            raise

        raw_output = str(result)
        output_findings = _scan_text(raw_output) if SCAN_OUTPUTS else []
        if output_findings:
            _audit(
                original_tool.name,
                raw_input,
                "blocked",
                output_findings,
                "output",
            )
            return _block_message("output", output_findings)

        _audit(original_tool.name, raw_input, "clean", [], "pass")
        return result

    wrapped_tool.__signature__ = original_signature
    wrapped_tool.__annotations__ = original_annotations
    return wrapped_tool


for _tool in ORIGINAL_MCP._tool_manager.list_tools():
    mcp.add_tool(
        _wrap_tool(_tool),
        name=_tool.name,
        description=_tool.description,
    )


if __name__ == "__main__":
    mcp.run()
"""


def load_index(index_path: Path = INDEX_PATH) -> dict:
    with index_path.open(encoding="utf-8") as handle:
        return json.load(handle)


def get_manifest(tool_name: str, index_path: Path = INDEX_PATH) -> dict | None:
    index = load_index(index_path)
    for tool in index.get("tools", []):
        if tool.get("name") == tool_name:
            return tool
    return None


def _resolve_server_args(args: list[str]) -> list[str]:
    if not args:
        raise ValueError("mcp_server.args must include the original Python server path")

    resolved = list(args)
    server_path = Path(resolved[0]).expanduser()
    if not server_path.is_absolute():
        server_path = (REPO_ROOT / server_path).resolve()
    resolved[0] = str(server_path)
    return resolved


def generate_wrapper(
    tool_name: str,
    original_command: str,
    original_args: list[str],
    scan_inputs: bool,
    scan_outputs: bool,
    output_dir: Path | None = None,
) -> Path:
    if output_dir is None:
        output_dir = Path.home() / ".ash" / "tools" / tool_name
    output_dir.mkdir(parents=True, exist_ok=True)

    wrapper_content = render_wrapper_content(
        tool_name=tool_name,
        original_command=original_command,
        original_args=original_args,
        scan_inputs=scan_inputs,
        scan_outputs=scan_outputs,
    )

    wrapper_path = output_dir / "ash_wrapped_server.py"
    wrapper_path.write_text(wrapper_content, encoding="utf-8")
    mode = wrapper_path.stat().st_mode
    wrapper_path.chmod(mode | stat.S_IEXEC)
    return wrapper_path


def render_wrapper_content(
    tool_name: str,
    original_command: str,
    original_args: list[str],
    scan_inputs: bool,
    scan_outputs: bool,
) -> str:
    return textwrap.dedent(
        WRAPPER_TEMPLATE.format(
            repo_root=str(REPO_ROOT),
            tool_name=tool_name,
            original_command=original_command,
            original_args=original_args,
            scan_inputs=scan_inputs,
            scan_outputs=scan_outputs,
        )
    )


def wrap_from_manifest(tool_name: str, index_path: str | Path | None = None) -> str:
    manifest_path = Path(index_path) if index_path is not None else INDEX_PATH
    manifest = get_manifest(tool_name, manifest_path)
    if manifest is None:
        raise KeyError(f"tool '{tool_name}' not found in registry")

    mcp_server = manifest.get("mcp_server", {})
    original_command = str(mcp_server.get("command", "")).strip()
    if not original_command:
        raise ValueError(f"tool '{tool_name}' is missing mcp_server.command")

    original_args = _resolve_server_args(list(mcp_server.get("args", [])))
    if not original_args[0].endswith(".py"):
        raise ValueError(
            f"tool '{tool_name}' must point at a Python server script in mcp_server.args[0]"
        )

    policy = manifest.get("ash_policy", {})
    wrapper_path = generate_wrapper(
        tool_name=tool_name,
        original_command=original_command,
        original_args=original_args,
        scan_inputs=bool(policy.get("scan_inputs", True)),
        scan_outputs=bool(policy.get("scan_outputs", True)),
    )
    return str(wrapper_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an ASH-wrapped MCP server for a registry tool.",
    )
    parser.add_argument("tool_name", help="Tool name from ash/registry/index.json")
    parser.add_argument(
        "--index",
        default=str(INDEX_PATH),
        help="Path to the registry index.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    wrapper_path = wrap_from_manifest(args.tool_name, args.index)
    print(wrapper_path)


if __name__ == "__main__":
    main()
