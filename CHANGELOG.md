# ASH Changelog

## 0.2.0 — 2026-03-23

### Security Fixes
- **fix: audit log secret redaction** — `command_snippet`, `error_snippet`, and alert messages now pass through `redact_secrets()` before writing to JSONL logs, Firestore, or Telegram alerts. 15 secret patterns (Anthropic, OpenAI, GitHub, AWS, Stripe, Bearer, generic credentials). Affects both the local audit hook and the hosted safety server `_log()`.
- **fix: cp/mv bypass on protected files** — `extract_mv_cp_targets()` now breaks at shell separators (`2>&1;`, `;`) instead of filtering by exact match. Previously, a command like `cp /tmp/evil.py protected_file.py 2>&1; echo done` would pick the wrong token as the destination and allow the write. All 5 attack variants verified blocked.

### New Features
- **feat: tool gateway / registry** — `ash/registry/` with trust analyzer (`trust.py`), wrapper generator (`wrap_tool.py`), CLI (`ash_registry.py`), hook config generator, and 5 seed tools. Wraps MCP tools with automatic secret scanning and audit logging.
- **feat: marketing content engine** — `ash/content/` with templates (incident, analogy, feature demo, substack essay), content calendar, draft-from-lead tool, outreach templates, and narrative framework.
- **feat: substack posting skill** — `skills/substack/` posts markdown to Substack via Chrome CDP + Playwright.
- **feat: issue tracker** — `ash/ISSUES.md` for local bug tracking.

### Improvements
- **fix: Codex wrapper MCP disable** — `run_codex.sh` swaps config to remove MCP servers during exec mode (ASH servers fail Codex's handshake). Restores after.
- **fix: Codex wrapper prompt delivery** — Resolved `WORKSPACE` variable ordering bug and added absolute path resolution for prompts.
- **docs: wiki security sections** — Added integration model comparison table, Codex guardrails docs, post-incident validation, hook failure modes (fail-open vs fail-closed), post-run diff check context, Codex MCP lesson learned.

## 0.1.0 — 2026-03-21

### Initial Release
- Safety MCP server (4 tools: scan_for_secrets, check_syntax, audit_tool_call, pipeline_gate)
- Memory MCP server (7 tools with behavioral policy engine)
- Multi-tenant service layer (Firestore, API key auth, webhooks)
- Stripe billing integration ($49/mo Team tier)
- Landing page at use-ash.com
- Claude Code integration guide (hooks)
- Codex Desktop integration guide (sandbox + approval + deny)
- ASH wiki deployed to use-ash.github.io/ash/
