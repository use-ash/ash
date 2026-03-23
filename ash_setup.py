#!/usr/bin/env python3
"""ASH Setup — interactive onboarding and configuration.

Creates ~/.ash/config.json with your preferred settings.
Run this once after installing ASH, or again any time to change settings.

Usage:
    python3 ash_setup.py           # interactive
    python3 ash_setup.py --show    # print current config
    python3 ash_setup.py --reset   # delete config and start fresh
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_CONFIG_ENV   = os.environ.get("ASH_CONFIG", "~/.ash/config.json")
CONFIG_PATH   = Path(_CONFIG_ENV).expanduser()
LOG_PATH_DEFAULT = str(Path("~/.ash/audit.jsonl").expanduser())

# ── Colours ──────────────────────────────────────────────────────────────────

def _c(text: str, code: str) -> str:
    if not sys.stdout.isatty():
        return text
    return f"\033[{code}m{text}\033[0m"

BOLD  = lambda t: _c(t, "1")
DIM   = lambda t: _c(t, "2")
CYAN  = lambda t: _c(t, "36")
GREEN = lambda t: _c(t, "32")
YELLOW= lambda t: _c(t, "33")
RED   = lambda t: _c(t, "31")


# ── Prompt helpers ────────────────────────────────────────────────────────────

def ask(prompt: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    try:
        val = input(f"  {prompt}{hint}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)
    return val if val else default


def ask_choice(prompt: str, choices: list[tuple[str, str]], default: str = "1") -> str:
    """choices = [(key, label), ...]  Returns the key."""
    print(f"\n  {prompt}")
    for key, label in choices:
        marker = "●" if key == default else " "
        print(f"    {DIM(marker)} ({key}) {label}")
    raw = ask("Enter choice", default)
    valid = {k for k, _ in choices}
    return raw if raw in valid else default


def ask_bool(prompt: str, default: bool = False) -> bool:
    hint = "Y/n" if default else "y/N"
    raw = ask(f"{prompt} [{hint}]").lower()
    if not raw:
        return default
    return raw in ("y", "yes")


# ── Config I/O ────────────────────────────────────────────────────────────────

def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(cfg: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")


# ── Display helpers ───────────────────────────────────────────────────────────

def show_config(cfg: dict) -> None:
    print(f"\n  {BOLD('Current config')} ({CONFIG_PATH})\n")
    audit = cfg.get("audit_log", {})
    print(f"  Audit log file   : {audit.get('file', LOG_PATH_DEFAULT)}")
    print(f"  Log level        : {audit.get('level', 'all')}")
    print(f"  Log to stdout    : {audit.get('stdout', False)}")
    print(f"  Safety port      : {cfg.get('safety_server_port', 8000)}")
    print(f"  Memory port      : {cfg.get('memory_server_port', 8001)}")
    print()


def show_summary(cfg: dict) -> None:
    audit = cfg.get("audit_log", {})
    level = audit.get("level", "all")

    print(f"\n  {GREEN('✓')} Config saved to {CONFIG_PATH}\n")

    if level == "off":
        print(f"  {YELLOW('Audit logging: OFF')}")
        print(f"  {DIM('No audit events will be written to disk.')}")
    else:
        log_file = audit.get("file", LOG_PATH_DEFAULT)
        print(f"  Audit log  → {log_file}")
        print(f"  Log level  → {level}")
        if audit.get("stdout"):
            print(f"  Stdout     → {GREEN('enabled')} (JSON lines to stdout)")

    port_s = cfg.get("safety_server_port", 8000)
    port_m = cfg.get("memory_server_port", 8001)
    print(f"\n  Safety server  → port {port_s}")
    print(f"  Memory server  → port {port_m}")
    print(f"\n  {DIM('Start the servers:')}")
    print(f"    python3 ash_safety_server.py")
    print(f"    python3 ash_memory_server.py")
    print(f"\n  {DIM('Both servers read')} {CONFIG_PATH}")
    print(f"  {DIM('Override location:')} ASH_CONFIG=/path/to/config.json\n")


# ── Main flow ─────────────────────────────────────────────────────────────────

def run_setup() -> None:
    existing = load_config()

    print(f"\n{BOLD('  ASH Setup')}  {DIM('— Agent Safety Harness')}\n")
    print(f"  This creates {CONFIG_PATH}")
    print(f"  Both ASH servers read this file at startup.\n")

    # ── Audit log ─────────────────────────────────────────────────────────────

    print(f"  {BOLD('Audit Logging')}")
    print(f"  {DIM('Every tool call can be written to a JSONL file for review.')}")

    level_key = ask_choice(
        "What events should be logged?",
        [
            ("1", "All tool calls  (every allow, block, and finding)"),
            ("2", "Blocks only     (BLOCK, FOUND, QUARANTINED events)"),
            ("3", "Off             (no file logging)"),
        ],
        default={"all": "1", "blocks_only": "2", "off": "3"}.get(
            existing.get("audit_log", {}).get("level", "all"), "1"
        ),
    )
    level_map = {"1": "all", "2": "blocks_only", "3": "off"}
    level = level_map[level_key]

    log_file = LOG_PATH_DEFAULT
    log_stdout = False

    if level != "off":
        existing_file = existing.get("audit_log", {}).get("file", LOG_PATH_DEFAULT)
        log_file = ask("\n  Audit log file path", existing_file)

        existing_stdout = existing.get("audit_log", {}).get("stdout", False)
        log_stdout = ask_bool(
            "\n  Also print log entries to stdout (useful for log aggregators)?",
            existing_stdout,
        )

    # ── Ports ─────────────────────────────────────────────────────────────────

    print(f"\n  {BOLD('Server Ports')}")
    port_s = ask(
        "Safety server port",
        str(existing.get("safety_server_port", 8000)),
    )
    port_m = ask(
        "Memory server port",
        str(existing.get("memory_server_port", 8001)),
    )

    try:
        port_s = int(port_s)
        port_m = int(port_m)
    except ValueError:
        print(RED("  Invalid port number. Using defaults 8000/8001."))
        port_s, port_m = 8000, 8001

    # ── Build and save ────────────────────────────────────────────────────────

    cfg: dict = {
        "audit_log": {
            "file":   log_file,
            "level":  level,
            "stdout": log_stdout,
        },
        "safety_server_port": port_s,
        "memory_server_port": port_m,
    }

    save_config(cfg)
    show_summary(cfg)


# ── CLI entry point ───────────────────────────────────────────────────────────

def main() -> None:
    args = sys.argv[1:]

    if "--show" in args:
        cfg = load_config()
        if not cfg:
            print(f"\n  {YELLOW('No config found.')} Run python3 ash_setup.py to create one.\n")
        else:
            show_config(cfg)
        return

    if "--reset" in args:
        if CONFIG_PATH.exists():
            CONFIG_PATH.unlink()
            print(f"\n  {GREEN('Config deleted.')} Run python3 ash_setup.py to create a new one.\n")
        else:
            print(f"\n  {DIM('No config found at')} {CONFIG_PATH}\n")
        return

    run_setup()


if __name__ == "__main__":
    main()
