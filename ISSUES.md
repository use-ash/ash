# ASH Issue Tracker

## Open

### ISS-003: Codex MCP handshake failure
**Severity:** Medium | **Found:** 2026-03-23 | **Component:** MCP servers
**Status:** Workaround in place

ASH MCP servers fail to initialize under Codex Desktop's MCP client: `connection closed: initialize response`. Blocks all Codex exec mode runs.

**Workaround:** `run_codex.sh` swaps config to remove `[mcp_servers.*]` sections before exec, restores after.
**Root cause:** Unknown. Likely transport/protocol mismatch between Codex v0.116.0-alpha.10 and FastMCP stdio.
**Next:** Test with minimal FastMCP server to isolate. Check Python 3.14 vs 3.11.
**Memory:** `memory/project_codex_mcp_bug.md`

---

### ISS-004: Codex exec silent exit on large prompts
**Severity:** Low | **Found:** 2026-03-23 | **Component:** Codex wrapper
**Status:** Workaround in place

Prompts over ~100-150 lines cause Codex exec to read the prompt, begin one reasoning step, then exit without creating files. Small/medium prompts work fine.

**Workaround:** Break large tasks into 30-50 line modules, run sequentially.
**Root cause:** Unknown. Possibly token budget or context limit in exec mode.
**Memory:** `memory/feedback_codex_task_sizing.md`

---

### ISS-005: Codex exec cannot run in parallel
**Severity:** Low | **Found:** 2026-03-23 | **Component:** Codex wrapper
**Status:** Workaround in place

Multiple concurrent `codex exec` processes fight over shared resources. All but one silently exit with zero output.

**Workaround:** Run Codex tasks sequentially only.
**Memory:** `memory/feedback_codex_task_sizing.md`

---

## Resolved

### ISS-001: cp/mv to protected files bypasses audit hook
**Severity:** Critical | **Found:** 2026-03-23 | **Fixed:** 2026-03-23 | **Component:** audit hook

`cp /tmp/evil.py scripts/guardrails/agent_audit_hook.py` succeeded without the hook blocking it. An agent could overwrite the hook itself, disabling all protections.

**Root cause:** `shlex.split` merges `2>&1;` into one token. `extract_mv_cp_targets` filtered separators by exact match (`";"`) but `"2>&1;"` didn't match. Function scanned past the semicolon and picked the wrong token as the cp destination.
**Fix:** New `_is_shell_separator()` function checking `endswith(";")` and `startswith(";")`. Changed arg collection to `break` at separators instead of filtering. All 5 attack variants verified blocked.
**File:** `scripts/guardrails/agent_audit_hook.py` lines 325-340
**Memory:** `memory/project_cp_bypass_bug.md`

---

### ISS-002: Audit log leaking secrets in command snippets
**Severity:** High | **Found:** 2026-03-23 | **Fixed:** 2026-03-23 | **Component:** audit hook + safety server

Full bash command strings logged to JSONL without redaction. Commands containing API keys, bearer tokens, or credentials in arguments would persist secrets in the audit log and Firestore.

**Root cause:** `build_log_entry()` logged raw `command_snippet`. `_log()` in safety server logged raw `details` dict.
**Fix:** Added `redact_secrets()` function to audit hook (15 secret patterns, placeholder filter). All `command_snippet`, `error_snippet`, and alert messages now pass through redaction before logging. Safety server `_log()` now calls `_redact_for_log()` on all string values.
**Files:** `scripts/guardrails/agent_audit_hook.py`, `ash/servers/safety/ash_safety_server.py`

---

### ISS-006: Codex Desktop rules format — deny/ask invalid
**Severity:** Low | **Found:** 2026-03-23 | **Fixed:** 2026-03-23 | **Component:** Codex config

`~/.codex/rules/default.rules` only supports `decision="allow"`. Both `"deny"` and `"ask"` cause startup abort.

**Fix:** Removed deny/ask rules. Blocking handled by audit hook and `approval_policy = "untrusted"`.
**Memory:** `memory/feedback_codex_rules_format.md`
