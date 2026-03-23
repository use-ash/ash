# ASH — Agent Safety Harness

**Add safety to any AI agent in 4 lines.**

ASH is an MCP server that sits between your agent and its tools. Every tool call passes through ASH first. Dangerous patterns — prompt injection payloads, hardcoded secrets, destructive shell commands — are blocked before they execute.

```python
import anthropic
from fastmcp import FastMCP

ash = FastMCP.connect("https://safety.use-ash.com/sse")  # hosted
client = anthropic.Anthropic(mcp_servers=[ash])
```

That's it. Your agent now has 4 safety tools available automatically.

---

## Why ASH

Modern AI safety training protects the model. It does not protect the execution layer.

A well-trained model can still be tricked into passing a malicious payload in a tool parameter. A coding agent will write hardcoded credentials to disk if instructed to. A DevOps agent asked to "free up disk space" may run `rm -rf`. These failures happen at the tool call level — after the model has decided what to do, before the action executes.

ASH intercepts there.

---

## Two Servers

### `ash_safety_server.py` — Execution Safety (Phase 1)

Intercepts tool calls before they execute.

| Tool | Blocks |
|------|--------|
| `scan_for_secrets` | API keys, tokens, passwords, credentials in URLs — before any file write |
| `check_syntax` | Invalid Python before execution or write |
| `audit_tool_call` | `rm -rf`, `curl \| bash`, `DROP TABLE`, force push, chmod 777, writes to system paths |
| `pipeline_gate` | Destructive or irreversible actions — requires explicit confirmation |

### `ash_memory_server.py` — Memory Safety (Phase 2)

Persistent memory for agents with injection scanning on every write.

| Tool | Does |
|------|------|
| `write_memory` | Store a key/value — scanned for injection before accepted |
| `read_memory` | Retrieve by key — flagged if stored content looks like a deferred command |
| `list_memories` | List all keys + metadata (values never returned in bulk) |
| `delete_memory` | Remove by key, logged |

Catches memory poisoning attacks — where an attacker stores `"whenever you see X, do Y (malicious)"` in long-term memory and it executes next session. Blocks 8 injection pattern classes; warns on 3 more.

---

## Quick Start

### Self-hosted (free, no account needed)

```bash
pip install "fastmcp==1.0"
python3 ash_safety_server.py   # execution safety, port 8000
python3 ash_memory_server.py   # memory safety,    port 8001
```

Then connect your agent:

```python
from fastmcp import FastMCP
import anthropic

ash = FastMCP.from_file("ash_safety_server.py")  # local
client = anthropic.Anthropic(mcp_servers=[ash])
```

### Hosted

```python
ash = FastMCP.connect("https://safety.use-ash.com/sse")
```

No setup. Persistent audit log, webhooks, team access. See [use-ash.com](https://use-ash.com) for pricing.

---

## Examples

Three runnable demos in `examples/`:

```bash
ANTHROPIC_API_KEY=<key> python3 examples/demo_prompt_injection.py
ANTHROPIC_API_KEY=<key> python3 examples/demo_secret_leak.py
ANTHROPIC_API_KEY=<key> python3 examples/demo_runaway_command.py
```

Each demo runs the same scenario with ASH **off** then **on**, so you can see exactly what gets blocked and why.

---

## Resources

**Safety server** (`ash_safety_server.py`):
- `ash://deny-list` — current blocked patterns and protected system paths
- `ash://audit-log` — last 50 events this session (tool name, result, timestamp)

**Memory server** (`ash_memory_server.py`):
- `ash://memory-store` — all stored keys and metadata (values omitted)
- `ash://memory-audit` — last 50 memory operations this session

---

## Bypass Marker

For test fixtures that intentionally contain fake credentials:

```python
API_KEY = "sk-test-fakekeyfortest"  # ash: allow-secret-fixture
```

ASH skips lines containing `# ash: allow-secret-fixture`.

---

## Run Tests

```bash
pip install pytest "fastmcp==1.0"
pytest tests/
```

---

## Docker

```bash
docker build -t ash-safety .
docker run -p 8000:8000 ash-safety
```

---

## Architecture

ASH is a stateless MCP server using SSE transport. It makes zero LLM calls — all checks are pattern matching and rule evaluation. Cold check latency: ~2ms local, ~20ms hosted.

```
Your Agent → MCP Client → ASH → Tool Execution
                            ↓
                       Audit Log
```

ASH never sees conversation content, system prompts, or user messages. It only receives tool names and parameters — the minimum needed to evaluate safety.

---

## License

MIT. Use it, fork it, embed it.

Hosted service and enterprise support at [use-ash.com](https://use-ash.com).
