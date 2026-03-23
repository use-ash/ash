#!/opt/homebrew/bin/python3
"""ASH Safety MCP Server — Phase 1 Prototype

Four tools:
  scan_for_secrets  — detect API keys, tokens, passwords in text or diffs
  check_syntax      — validate code before execution (Python)
  audit_tool_call   — flag dangerous shell patterns and system path writes
  pipeline_gate     — checkpoint before destructive actions

Two resources:
  ash://deny-list   — current blocked patterns and protected paths
  ash://audit-log   — last 50 audit entries this session

Install (4 lines):
  import mcp
  ash = mcp.connect("ash_safety_server.py")        # local
  # ash = mcp.connect("https://safety.use-ash.com") # hosted (Phase 4)
  client = anthropic.Anthropic(mcp_servers=[ash])

Run standalone:
  python3 ash_safety_server.py
"""

from __future__ import annotations

import ast
import json
import os
import re
from datetime import datetime
from pathlib import Path
from fastmcp import FastMCP

mcp = FastMCP("ASH Safety")

# ---------------------------------------------------------------------------
# Config loader — reads ~/.ash/config.json or ASH_CONFIG env var
# ---------------------------------------------------------------------------
_CFG_DEFAULT = {
    "audit_log": {
        "file":   "~/.ash/audit.jsonl",
        "level":  "all",   # "all" | "blocks_only" | "off"
        "stdout": False,
    },
    "safety_server_port": 8000,
    "memory_server_port": 8001,
}

def _load_config() -> dict:
    path = os.environ.get("ASH_CONFIG", "~/.ash/config.json")
    path = Path(path).expanduser()
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            pass
    return _CFG_DEFAULT

_CFG = _load_config()
_AUDIT_CFG = _CFG.get("audit_log", _CFG_DEFAULT["audit_log"])
_LOG_FILE   = Path(_AUDIT_CFG.get("file", "~/.ash/audit.jsonl")).expanduser() \
              if _AUDIT_CFG.get("level", "all") != "off" else None
_LOG_LEVEL  = _AUDIT_CFG.get("level", "all")   # "all" | "blocks_only" | "off"
_LOG_STDOUT = _AUDIT_CFG.get("stdout", False)

_BLOCK_RESULTS = {"BLOCK", "FOUND", "INVALID", "REVIEW_REQUIRED"}

def _ensure_log_dir() -> None:
    if _LOG_FILE:
        _LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

_ensure_log_dir()

# ---------------------------------------------------------------------------
# In-memory audit log (500-entry ring buffer)
# ---------------------------------------------------------------------------
_AUDIT_LOG: list[dict] = []


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _log(tool: str, result: str, details: dict) -> None:
    entry = {"ts": _now(), "server": "safety", "tool": tool, "result": result, **details}
    _AUDIT_LOG.append(entry)
    if len(_AUDIT_LOG) > 500:
        _AUDIT_LOG.pop(0)

    # File / stdout logging
    if _LOG_LEVEL == "off":
        return
    if _LOG_LEVEL == "blocks_only" and result not in _BLOCK_RESULTS:
        return
    if _LOG_FILE:
        try:
            with open(_LOG_FILE, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass
    if _LOG_STDOUT:
        print(json.dumps(entry), flush=True)


# ---------------------------------------------------------------------------
# Secret patterns (self-contained — no workspace imports)
# ---------------------------------------------------------------------------
SECRET_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("Anthropic API Key",       re.compile(r"sk-ant-api\S{10,}")),
    ("Anthropic OAuth",         re.compile(r"sk-ant-oat\S{10,}")),
    ("Telegram Bot Token",      re.compile(r"\b\d{8,10}:AA[A-Za-z0-9_-]{30,}\b")),
    ("GitHub PAT",              re.compile(r"ghp_[A-Za-z0-9]{36,}")),
    ("GitHub OAuth Token",      re.compile(r"gho_[A-Za-z0-9]{36,}")),
    ("GitHub App Token",        re.compile(r"ghs_[A-Za-z0-9]{36,}")),
    ("xAI API Key",             re.compile(r"xai-[A-Za-z0-9_-]{10,}")),
    ("OpenAI API Key",          re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("AWS Access Key",          re.compile(r"AKIA[0-9A-Z]{16}")),
    ("Private Key Block",       re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("Bearer Token",            re.compile(r"(?i)Bearer\s+[A-Za-z0-9._-]{20,}")),
    ("Stripe Live Key",          re.compile(r"sk_live_[A-Za-z0-9]{20,}")),
    ("Stripe Webhook Secret",    re.compile(r"whsec_[A-Za-z0-9]{20,}")),
    ("Generic Secret",          re.compile(r"(?i)(?:password|passwd|secret|api[_\-]?key)\s*=\s*[\"']?[A-Za-z0-9#$@!%^&*()\-_+=]{8,}[\"']?")),
    ("Credentials in URL",       re.compile(r"(?i)(?:redis|postgres|mysql|mongodb)://[^:]*:[^@\s]{4,}@")),
]

PLACEHOLDER_RE = re.compile(
    r"your_\w+_here|example|testkey|placeholder|REDACTED|xxx+|dummy|changeme|fake",
    re.IGNORECASE,
)

BYPASS_MARKER = "ash: allow-secret-fixture"


def _scan_text(text: str) -> list[tuple[str, str, int]]:
    """Returns [(pattern_name, redacted_match, line_number), ...]"""
    findings: list[tuple[str, str, int]] = []
    for line_num, line in enumerate(text.splitlines(), 1):
        if BYPASS_MARKER in line:
            continue
        for name, pattern in SECRET_PATTERNS:
            for match in pattern.finditer(line):
                matched = match.group(0)
                if PLACEHOLDER_RE.search(matched):
                    continue
                # Redact middle — show first 4 and last 2 chars only
                if len(matched) > 8:
                    redacted = matched[:4] + "****" + matched[-2:]
                else:
                    redacted = "****"
                findings.append((name, redacted, line_num))
    return findings


# ---------------------------------------------------------------------------
# Dangerous bash patterns
# ---------------------------------------------------------------------------
DANGEROUS_PATTERNS: list[tuple[str, str]] = [
    (r"\brm\b.*-[^\s]*r",                  "rm recursive"),
    (r"\bgit\s+push\b.*(?:--force|-f)\b",  "git force push"),
    (r"\bgit\s+reset\s+--hard\b",          "git reset --hard"),
    (r"\bcurl\b.*\|\s*(?:sh|bash)\b",      "curl pipe to shell"),
    (r"\bwget\b.*\|\s*(?:sh|bash)\b",      "wget pipe to shell"),
    (r"\bchmod\s+(?:-\S+\s+)*777\b",       "chmod 777"),
    (r"\bdrop\s+(?:table|database)\b",     "SQL DROP"),
    (r"\btruncate\s+table\b",              "SQL TRUNCATE"),
    (r"\bdd\s+if=",                        "dd disk write"),
    (r">\s*/dev/",                         "write to device file"),
]

SYSTEM_PATHS = ("/etc/", "/usr/", "/bin/", "/sbin/", "/System/", "/Library/")

HIGH_RISK_KEYWORDS = (
    "delete", "drop", "destroy", "purge", "wipe", "truncate",
    "force push", "force-push", "reset --hard", "rm -rf",
)


# ---------------------------------------------------------------------------
# Tool 1: scan_for_secrets
# ---------------------------------------------------------------------------
@mcp.tool()
def scan_for_secrets(text: str) -> str:
    """Scan text, code, or a git diff for leaked API keys, tokens, and passwords.

    Call this before writing any file that contains credentials, environment
    variables, configuration, or code that handles authentication.

    Returns CLEAN if nothing found, or FOUND with details of each finding.
    Matched values are redacted — only pattern type and line number are reported.
    """
    findings = _scan_text(text)

    if not findings:
        _log("scan_for_secrets", "CLEAN", {"lines": text.count("\n") + 1})
        return "CLEAN — no secrets detected"

    lines = [f"  Line {ln}: {name} → {redacted}" for name, redacted, ln in findings]
    msg = f"FOUND {len(findings)} potential secret(s):\n" + "\n".join(lines)
    msg += "\n\nDo not write this content to a file or send it to an external service."
    _log("scan_for_secrets", "FOUND", {"count": len(findings), "types": list({n for n, _, _ in findings})})
    return msg


# ---------------------------------------------------------------------------
# Tool 2: check_syntax
# ---------------------------------------------------------------------------
@mcp.tool()
def check_syntax(code: str, language: str = "python") -> str:
    """Validate code syntax before execution or writing to disk.

    Call this after generating any code block that will be executed or saved.
    Currently supports Python. Returns VALID or INVALID with error location.
    """
    lang = language.lower().strip()

    if lang not in ("python", "py", "python3"):
        _log("check_syntax", "SKIP", {"language": language})
        return f"SKIP — syntax check not yet implemented for '{language}'"

    try:
        ast.parse(code)
        _log("check_syntax", "VALID", {"language": lang, "lines": code.count("\n") + 1})
        return "VALID — syntax OK"
    except SyntaxError as exc:
        detail = f"SyntaxError at line {exc.lineno}: {exc.msg}"
        if exc.text:
            detail += f"\n  {exc.text.rstrip()}"
            if exc.offset:
                detail += "\n  " + " " * (exc.offset - 1) + "^"
        _log("check_syntax", "INVALID", {"language": lang, "error": str(exc)})
        return f"INVALID — {detail}"


# ---------------------------------------------------------------------------
# Tool 3: audit_tool_call
# ---------------------------------------------------------------------------
@mcp.tool()
def audit_tool_call(
    tool_name: str,
    command: str = "",
    file_path: str = "",
) -> str:
    """Audit a tool call for dangerous patterns before execution.

    Call this before any Bash command or file write when operating in an
    automated or production context. Pass the tool name and either the shell
    command or file path being modified.

    Returns ALLOW or BLOCK with reason. Respect BLOCK — do not proceed.
    """
    # Check shell command for dangerous patterns
    if command:
        for pattern_str, label in DANGEROUS_PATTERNS:
            if re.search(pattern_str, command, re.IGNORECASE):
                msg = f"BLOCK — dangerous pattern detected: {label}\nCommand: {command[:120]}"
                _log("audit_tool_call", "BLOCK", {"tool": tool_name, "reason": label})
                return msg

    # Check file path for system directory writes
    if file_path:
        for sys_path in SYSTEM_PATHS:
            if file_path.startswith(sys_path):
                msg = f"BLOCK — write to system path: {file_path}"
                _log("audit_tool_call", "BLOCK", {"tool": tool_name, "reason": "system path write", "path": file_path})
                return msg

    snippet = (command or file_path)[:60] or "(no target)"
    _log("audit_tool_call", "ALLOW", {"tool": tool_name, "target": snippet})
    return "ALLOW"


# ---------------------------------------------------------------------------
# Tool 4: pipeline_gate
# ---------------------------------------------------------------------------
@mcp.tool()
def pipeline_gate(
    action: str,
    target: str,
    destructive: bool = False,
) -> str:
    """Checkpoint before executing a significant or irreversible action.

    Call this before: file deletes, database mutations, deployments, git pushes,
    sending external messages, or any action that cannot be easily undone.

    Describe what you are about to do (action) and what it affects (target).
    Set destructive=True for actions that cannot be reversed.

    Returns PROCEED (log only) or REVIEW_REQUIRED (stop and confirm with user).
    """
    # Explicit destructive flag
    if destructive:
        msg = (
            f"REVIEW_REQUIRED — destructive=True\n"
            f"Action: {action}\n"
            f"Target: {target}\n"
            f"This action may be irreversible. Stop and confirm with the user before proceeding."
        )
        _log("pipeline_gate", "REVIEW_REQUIRED", {"action": action, "target": target, "reason": "destructive flag"})
        return msg

    # High-risk keywords in action description
    action_lower = action.lower()
    for kw in HIGH_RISK_KEYWORDS:
        if kw in action_lower:
            msg = (
                f"REVIEW_REQUIRED — high-risk keyword: '{kw}'\n"
                f"Action: {action}\n"
                f"Target: {target}\n"
                f"Stop and confirm with the user before proceeding."
            )
            _log("pipeline_gate", "REVIEW_REQUIRED", {"action": action, "target": target, "reason": f"keyword: {kw}"})
            return msg

    _log("pipeline_gate", "PROCEED", {"action": action, "target": target})
    return f"PROCEED — action logged\nAction: {action}\nTarget: {target}"


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------
@mcp.resource("ash://deny-list")
def deny_list() -> str:
    """The current set of patterns and paths that ASH Safety blocks."""
    return json.dumps({
        "dangerous_bash_patterns": [label for _, label in DANGEROUS_PATTERNS],
        "system_paths_blocked": list(SYSTEM_PATHS),
        "secret_pattern_names": [name for name, _ in SECRET_PATTERNS],
        "high_risk_keywords": list(HIGH_RISK_KEYWORDS),
    }, indent=2)


@mcp.resource("ash://audit-log")
def audit_log_resource() -> str:
    """The last 50 audit entries from this session (newest last)."""
    return json.dumps(_AUDIT_LOG[-50:], indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    mcp.settings.port = port
    mcp.run(transport="sse")
