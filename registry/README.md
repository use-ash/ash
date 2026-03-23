# ASH Tool Registry

The ASH tool registry is a package registry for MCP tools, closer to `npm` for servers than a plain manifest list, except every installed tool is wrapped with ASH safety controls. Instead of pointing an agent directly at a raw MCP server, the registry installs a wrapped entrypoint that scans inputs and outputs, audits calls, and gives you a paste-ready MCP config block.

## Install a Registry Tool

```bash
python3 ash/registry/ash_registry.py install <name>
```

Example:

```bash
python3 ash/registry/ash_registry.py install github-issues
```

What happens:

1. The CLI reads the manifest from `ash/registry/index.json`.
2. It shows the tool's trust score, permissions, and trust findings.
3. If the trust score is below `50`, installation stops unless you pass `--force`.
4. It creates `~/.ash/tools/<name>/`.
5. It calls the wrapping logic from `wrap_tool.py` to generate `ash_wrapped_server.py`.
6. It calls the config generator from `generate_hooks.py`.
7. It prints the final MCP config JSON block to paste into your editor or agent settings.

Low-trust install override:

```bash
python3 ash/registry/ash_registry.py install <name> --force
```

## Wrap an Arbitrary MCP Server

```bash
python3 ash/registry/ash_registry.py wrap <path>
```

Example:

```bash
python3 ash/registry/ash_registry.py wrap /path/to/custom_server.py
```

What happens:

1. The CLI runs the trust analysis from `trust.py` against the target file.
2. It prints the score, derived permissions, and findings.
3. It generates a wrapped server in `~/.ash/tools/<basename>/`.
4. It prints the MCP config JSON block to paste into settings.

Current limitation: the wrapper generator in `wrap_tool.py` supports Python FastMCP servers, so `wrap` expects a `.py` MCP server script.

## Trust Scoring

`trust.py` starts at a base score of `100` and subtracts points for risky behaviors discovered through static AST analysis.

| Finding | Score impact | Meaning |
|---|---:|---|
| Base score | 100 | Clean starting score before penalties. |
| Network import (`requests`, `urllib`, `httpx`, `aiohttp`) | -5 | Tool can likely talk to remote systems. |
| Raw socket import | -10 | Tool may open lower-level network connections directly. |
| Filesystem write (`open(..., "w")`, `Path.write_text()`, `os.remove()`, `shutil.*`) | -10 | Tool can modify local files. |
| Sensitive env var read (`*_KEY`, `*_SECRET`, `*_TOKEN`, `*_PASSWORD`) | -15 | Tool reads likely secrets from the environment. |
| System path reference (`/etc/`, `/usr/`, `/bin/`, `~/.ssh/`) | -15 | Tool references sensitive or privileged filesystem locations. |
| `subprocess.*(..., shell=True)` | -20 | Tool executes shell commands with higher injection risk. |
| `eval()`, `exec()`, `compile()` | -30 | Tool dynamically executes code. |
| File read error or syntax error | score becomes `0` | The file could not be safely analyzed. |

Scores below `50` are blocked by default for `install`.

## Deployment Models

### Gateway model

Use this when ASH is the only path between the agent and the tool, such as SDK-hosted agents or a gateway process that owns all MCP traffic.

Flow:

```text
Agent -> ASH gateway / wrapped server -> original MCP server
```

Why it exists:

- ASH can enforce safety policy centrally.
- Raw tool traffic never bypasses the ASH layer.
- This fits systems where the runtime controls tool registration directly.

### Hook wrapper model

Use this when the host tool runner already exists and you need ASH to sit in front of a local MCP server, such as Claude Code or Codex-style local tool integration.

Flow:

```text
Agent host hook -> ASH safety hook -> wrapped MCP server -> original MCP server
```

Why it exists:

- The host keeps its normal MCP integration model.
- ASH still gets an audit point and a safety wrapper around the server.
- `generate_hooks.py` produces the JSON block for this deployment style.

## Adding a Tool to the Registry

Registry entries live in the `tools` array of `ash/registry/index.json`. Each manifest should match `ash/registry/tool_manifest_schema.json`.

Manifest shape:

```json
{
  "name": "tool-name",
  "author": "team-or-author",
  "version": "1.0.0",
  "description": "One-line summary.",
  "mcp_server": {
    "command": "/opt/homebrew/bin/python3",
    "args": ["servers/example_server.py"],
    "env": {
      "API_TOKEN": "required"
    }
  },
  "permissions": {
    "network": true,
    "filesystem": false,
    "env_vars": ["API_TOKEN"],
    "shell": false
  },
  "trust": {
    "score": 75,
    "vetted_by": "ash-team",
    "vetted_at": "2026-03-23",
    "findings": [
      "Performs outbound network requests.",
      "Requires API_TOKEN for authenticated access."
    ]
  },
  "ash_policy": {
    "scan_inputs": true,
    "scan_outputs": true,
    "audit_all": true,
    "block_patterns": []
  },
  "install": {
    "pip": ["fastmcp"],
    "npm": [],
    "source": "https://example.com/repo"
  }
}
```

Recommended process:

1. Add the manifest to `ash/registry/index.json`.
2. Run `python3 ash/registry/trust.py /path/to/server.py --pretty`.
3. Copy the score and a concise summary of findings into the manifest.
4. Set `vetted_by` and `vetted_at` after review.
5. Verify `python3 ash/registry/ash_registry.py inspect <name>` shows the expected metadata.
