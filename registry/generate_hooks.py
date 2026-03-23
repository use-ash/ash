#!/opt/homebrew/bin/python3
"""Generate ASH MCP server and hook config for a registry tool."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
INDEX_PATH = SCRIPT_DIR / "index.json"
PYTHON = "/opt/homebrew/bin/python3"


def load_index(index_path: Path = INDEX_PATH) -> dict:
    with index_path.open(encoding="utf-8") as handle:
        return json.load(handle)


def get_manifest(tool_name: str, index_path: Path = INDEX_PATH) -> dict | None:
    index = load_index(index_path)
    for tool in index.get("tools", []):
        if tool.get("name") == tool_name:
            return tool
    return None


def get_wrapper_path(tool_name: str, wrapper_path: str | None = None) -> str:
    if wrapper_path is not None:
        return wrapper_path
    return os.path.expanduser(f"~/.ash/tools/{tool_name}/ash_wrapped_server.py")


def generate_mcp_config(
    tool_name: str,
    wrapper_path: str | None = None,
    *,
    manifest: dict | None = None,
) -> dict:
    if manifest is None:
        manifest = get_manifest(tool_name)
    if manifest is None:
        raise KeyError(f"tool '{tool_name}' not found in registry")

    return {
        f"ash-{tool_name}": {
            "command": PYTHON,
            "args": [get_wrapper_path(tool_name, wrapper_path)],
        }
    }


def generate_hook_config(tool_name: str, *, manifest: dict | None = None) -> dict:
    if manifest is None:
        manifest = get_manifest(tool_name)
    if manifest is None:
        raise KeyError(f"tool '{tool_name}' not found in registry")

    return {
        "type": "preToolUse",
        "matcher": f"mcp__ash-{tool_name}__*",
        "hook": {
            "type": "mcp",
            "server": "ash-safety",
            "tool": "audit_tool_call",
            "args": {
                "tool_name": f"ash-{tool_name}",
            },
        },
    }


def generate_full_config(
    tool_name: str,
    wrapper_path: str | None = None,
) -> dict:
    manifest = get_manifest(tool_name)
    if manifest is None:
        if wrapper_path is None:
            raise KeyError(f"tool '{tool_name}' not found in registry")
        manifest = {"name": tool_name}

    return {
        "mcpServers": generate_mcp_config(
            tool_name,
            wrapper_path,
            manifest=manifest,
        ),
        "hooks": [generate_hook_config(tool_name, manifest=manifest)],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate ASH hook config for a registry tool.",
    )
    parser.add_argument("tool_name", help="Tool name from ash/registry/index.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        config = generate_full_config(args.tool_name)
    except KeyError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    print(json.dumps(config, indent=2))


if __name__ == "__main__":
    main()
