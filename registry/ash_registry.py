#!/opt/homebrew/bin/python3
"""CLI for listing, inspecting, installing, and wrapping ASH MCP tools."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from generate_hooks import generate_full_config
from trust import analyze_file
from wrap_tool import INDEX_PATH, PYTHON, load_index, wrap_from_manifest
from wrap_tool import generate_wrapper


def get_manifest(name: str) -> dict[str, Any] | None:
    index = load_index(INDEX_PATH)
    for tool in index.get("tools", []):
        if tool.get("name") == name:
            return tool
    return None


def print_error(message: str) -> None:
    print(message, file=sys.stderr)


def format_table(rows: list[list[str]], headers: list[str]) -> str:
    all_rows = [headers] + rows
    widths = [max(len(row[index]) for row in all_rows) for index in range(len(headers))]
    return "\n".join(
        "  ".join(row[index].ljust(widths[index]) for index in range(len(headers)))
        for row in all_rows
    )


def truncate(text: str, limit: int = 64) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def print_json_block(data: Any) -> None:
    print(json.dumps(data, indent=2))


def print_permissions(permissions: dict[str, Any]) -> None:
    print(f"network:    {bool(permissions.get('network', False))}")
    print(f"filesystem: {bool(permissions.get('filesystem', False))}")
    print(f"shell:      {bool(permissions.get('shell', False))}")
    env_vars = permissions.get("env_vars", [])
    if env_vars:
        print(f"env_vars:   {', '.join(env_vars)}")
    else:
        print("env_vars:   none")


def print_findings(findings: list[Any]) -> None:
    if not findings:
        print("- none")
        return

    for finding in findings:
        if isinstance(finding, str):
            print(f"- {finding}")
            continue

        impact = finding.get("impact", 0)
        line = finding.get("line", 0)
        label = finding.get("finding", "unknown finding")
        print(f"- [{impact:+d}] line {line}: {label}")
        snippet = finding.get("snippet", "").strip()
        if snippet:
            print(f"  {snippet}")


def print_install_instructions(install: dict[str, Any]) -> None:
    pip_packages = install.get("pip", [])
    npm_packages = install.get("npm", [])
    source = install.get("source")

    print("Install instructions:")
    if pip_packages:
        print(f"- pip: {' '.join(pip_packages)}")
    if npm_packages:
        print(f"- npm: {' '.join(npm_packages)}")
    if source:
        print(f"- source: {source}")
    if not pip_packages and not npm_packages and not source:
        print("- none")


def derive_tool_name(path: Path) -> str:
    base_name = path.stem or path.name
    normalized = re.sub(r"[^a-z0-9]+", "-", base_name.lower()).strip("-")
    return normalized or "wrapped-tool"


def cmd_list(_: argparse.Namespace) -> int:
    index = load_index(INDEX_PATH)
    tools = index.get("tools", [])
    rows: list[list[str]] = []

    for tool in tools:
        rows.append(
            [
                str(tool.get("name", "")),
                str(tool.get("version", "")),
                str(tool.get("trust", {}).get("score", "")),
                str(tool.get("author", "")),
                truncate(str(tool.get("description", ""))),
            ]
        )

    headers = ["NAME", "VERSION", "TRUST", "AUTHOR", "DESCRIPTION"]
    print(format_table(rows, headers))
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    manifest = get_manifest(args.name)
    if manifest is None:
        print_error(f"tool '{args.name}' not found in registry")
        return 1

    print(f"name:        {manifest.get('name', '')}")
    print(f"version:     {manifest.get('version', '')}")
    print(f"author:      {manifest.get('author', '')}")
    print(f"description: {manifest.get('description', '')}")
    print()

    print("MCP server config:")
    print_json_block(manifest.get("mcp_server", {}))
    print()

    print("Permissions:")
    print_permissions(manifest.get("permissions", {}))
    print()

    trust = manifest.get("trust", {})
    print(f"Trust score: {trust.get('score', 0)}/100")
    vetted_by = trust.get("vetted_by")
    vetted_at = trust.get("vetted_at")
    if vetted_by or vetted_at:
        print(f"Vetted:      {vetted_by or 'unknown'} @ {vetted_at or 'unknown'}")
    print("Trust findings:")
    print_findings(trust.get("findings", []))
    print()

    print("ASH policy:")
    print_json_block(manifest.get("ash_policy", {}))
    print()

    print_install_instructions(manifest.get("install", {}))
    return 0


def cmd_install(args: argparse.Namespace) -> int:
    manifest = get_manifest(args.name)
    if manifest is None:
        print_error(f"tool '{args.name}' not found in registry")
        return 1

    trust = manifest.get("trust", {})
    score = int(trust.get("score", 0))

    print(f"Installing {manifest.get('name', '')} {manifest.get('version', '')}")
    print(f"Trust score: {score}/100")
    print("Permissions:")
    print_permissions(manifest.get("permissions", {}))
    print("Trust findings:")
    print_findings(trust.get("findings", []))
    print()

    if score < 50 and not args.force:
        print_error(
            f"Refusing to install '{args.name}': trust score {score} is below 50. "
            "Re-run with --force to install anyway."
        )
        return 1

    install_dir = Path.home() / ".ash" / "tools" / args.name
    try:
        install_dir.mkdir(parents=True, exist_ok=True)
        wrapper_path = wrap_from_manifest(args.name, INDEX_PATH)
        config = generate_full_config(args.name, wrapper_path)
    except OSError as exc:
        print_error(f"failed to write wrapper files in {install_dir}: {exc}")
        return 1
    except Exception as exc:
        print_error(f"failed to install '{args.name}': {exc}")
        return 1

    print(f"Wrapper path: {wrapper_path}")
    print()
    print("Paste this MCP config into your settings:")
    print_json_block(config)
    return 0


def cmd_wrap(args: argparse.Namespace) -> int:
    source_path = Path(args.path).expanduser().resolve()
    if not source_path.exists():
        print_error(f"file not found: {source_path}")
        return 1
    if source_path.suffix != ".py":
        print_error("wrap currently supports Python FastMCP server files only")
        return 1

    trust_result = analyze_file(str(source_path))
    print(f"Trust score: {trust_result['score']}/100")
    print("Permissions:")
    print_permissions(trust_result.get("permissions", {}))
    print("Trust findings:")
    print_findings(trust_result.get("findings", []))
    print()

    tool_name = derive_tool_name(source_path)
    output_dir = Path.home() / ".ash" / "tools" / tool_name
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        wrapper_path = generate_wrapper(
            tool_name=tool_name,
            original_command=PYTHON,
            original_args=[str(source_path)],
            scan_inputs=True,
            scan_outputs=True,
            output_dir=output_dir,
        )
        config = generate_full_config(tool_name, str(wrapper_path))
    except OSError as exc:
        print_error(f"failed to write wrapper files in {output_dir}: {exc}")
        return 1
    except Exception as exc:
        print_error(f"failed to wrap '{source_path}': {exc}")
        return 1

    print(f"Wrapper path: {wrapper_path}")
    print()
    print("Paste this MCP config into your settings:")
    print_json_block(config)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ash_registry.py",
        description="Manage ASH registry tools and safety wrappers.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List tools in ash/registry/index.json")

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect a registry tool manifest",
    )
    inspect_parser.add_argument("name", help="Registry tool name")

    install_parser = subparsers.add_parser(
        "install",
        help="Install and wrap a registry tool",
    )
    install_parser.add_argument("name", help="Registry tool name")
    install_parser.add_argument(
        "--force",
        action="store_true",
        help="Install tools with trust scores below 50",
    )

    wrap_parser = subparsers.add_parser(
        "wrap",
        help="Wrap an arbitrary Python FastMCP server",
    )
    wrap_parser.add_argument("path", help="Path to a Python MCP server")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "list":
        return cmd_list(args)
    if args.command == "inspect":
        return cmd_inspect(args)
    if args.command == "install":
        return cmd_install(args)
    if args.command == "wrap":
        return cmd_wrap(args)

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
