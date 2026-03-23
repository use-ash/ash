# use-ash/continuity

Framework for session handoff and thread tracking.

This repository describes how an agent can preserve active work across sessions, models, and channels by keeping conversation state in files instead of inside a single context window.

This repository does not contain code. It contains schemas, guides, patterns, and examples.

Start here:

1. Read [AGENT_INSTRUCTIONS.md](AGENT_INSTRUCTIONS.md).
2. Read [CONTINUITY_FRAMEWORK.md](CONTINUITY_FRAMEWORK.md).
3. Read [THREAD_SCHEMA.md](THREAD_SCHEMA.md).
4. Read [SESSION_START_GUIDE.md](SESSION_START_GUIDE.md).
5. Read [HANDOFF_PATTERNS.md](HANDOFF_PATTERNS.md).

Reference background:

- ASH wiki: <https://use-ash.github.io/ash/>
- Memory and continuity overview: <https://use-ash.github.io/ash/memory-and-continuity/>

Repository contents:

- `CONTINUITY_FRAMEWORK.md`: session persistence model
- `THREAD_SCHEMA.md`: conversation state schema
- `SESSION_START_GUIDE.md`: how to build context at session start
- `HANDOFF_PATTERNS.md`: model, channel, and session handoffs
- `examples/`: example state file and startup checklist
