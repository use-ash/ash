# use-ash/coordination

Framework for multi-model routing and delegation.

This repository explains how to decide which model should handle which kind of work, how to hand tasks off without losing context, and how to build fallback chains when a preferred model is unavailable or too expensive.

This repository contains patterns and templates only. It does not contain routing code or model-specific implementation details.

Start here:

1. Read [AGENT_INSTRUCTIONS.md](AGENT_INSTRUCTIONS.md).
2. Read [COORDINATION_FRAMEWORK.md](COORDINATION_FRAMEWORK.md).
3. Read [DECISION_MATRIX.md](DECISION_MATRIX.md).
4. Read [DISPATCH_PATTERNS.md](DISPATCH_PATTERNS.md).
5. Read [FALLBACK_CHAINS.md](FALLBACK_CHAINS.md).
6. Read [PITFALLS.md](PITFALLS.md).

Reference background:

- ASH wiki: <https://use-ash.github.io/ash/>
- Model coordination overview: <https://use-ash.github.io/ash/model-coordination/>

Repository contents:

- `COORDINATION_FRAMEWORK.md`: overall routing model
- `DECISION_MATRIX.md`: task-to-model selection template
- `DISPATCH_PATTERNS.md`: handoff structure and budget discipline
- `FALLBACK_CHAINS.md`: primary and secondary routing patterns
- `PITFALLS.md`: common coordination failure modes
