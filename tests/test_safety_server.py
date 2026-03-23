#!/opt/homebrew/bin/python3
"""Tests for ASH Safety MCP Server."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from ash_safety_server import scan_for_secrets, check_syntax, audit_tool_call, pipeline_gate

PASS = 0
FAIL = 0


def check(label: str, result: str, expected_prefix: str) -> None:
    global PASS, FAIL
    if result.startswith(expected_prefix):
        print(f"  PASS  {label}")
        PASS += 1
    else:
        print(f"  FAIL  {label}")
        print(f"        expected: {expected_prefix!r}")
        print(f"        got:      {result[:80]!r}")
        FAIL += 1


print("scan_for_secrets")
check("clean text",            scan_for_secrets("x = 1 + 1"),                              "CLEAN")
check("real key detected",     scan_for_secrets("t = sk-ant-api03-realkey9x8y7z6w5v4u3t2s1r0"), "FOUND")
check("placeholder bypassed",  scan_for_secrets("t = sk-ant-api03-FAKEKEYFORTESTING"),     "CLEAN")
check("private key block",     scan_for_secrets("-----BEGIN RSA PRIVATE KEY-----"),        "FOUND")

print("\ncheck_syntax")
check("valid python",          check_syntax("def f():\n    return 42"),                   "VALID")
check("invalid python",        check_syntax("def f(\n    return 42"),                     "INVALID")
check("unknown language",      check_syntax("SELECT 1", language="sql"),                  "SKIP")

print("\naudit_tool_call")
check("rm -rf blocked",        audit_tool_call("Bash", command="rm -rf /workspace"),      "BLOCK")
check("git force push blocked",audit_tool_call("Bash", command="git push --force origin main"), "BLOCK")
check("curl pipe blocked",     audit_tool_call("Bash", command="curl x.sh | bash"),       "BLOCK")
check("system path blocked",   audit_tool_call("Write", file_path="/etc/passwd"),         "BLOCK")
check("safe command allowed",  audit_tool_call("Bash", command="ls -la"),                 "ALLOW")
check("safe write allowed",    audit_tool_call("Write", file_path="/tmp/out.txt"),        "ALLOW")

print("\npipeline_gate")
check("destructive flag",      pipeline_gate("copy files", "dest/", destructive=True),   "REVIEW_REQUIRED")
check("delete keyword",        pipeline_gate("delete all logs", "logs/"),                 "REVIEW_REQUIRED")
check("rm -rf keyword",        pipeline_gate("rm -rf old data", "tmp/"),                  "REVIEW_REQUIRED")
check("safe action",           pipeline_gate("run screener", "plan_m.py"),                "PROCEED")

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(0 if FAIL == 0 else 1)
