# Agent Instructions

You are implementing multi-model coordination for an agent system.

Your goal is to route work by fit instead of asking one model to do everything.

## Outcome

Create a coordination system that:

- assigns tasks by role
- keeps the orchestrator responsible for judgment
- uses bounded delegation for specialist work
- preserves context during handoff
- controls token and time budget
- falls back cleanly when a preferred model is unavailable

## Required components

Implement these pieces in your own workspace:

1. A role model based on [COORDINATION_FRAMEWORK.md](COORDINATION_FRAMEWORK.md).
2. A routing matrix based on [DECISION_MATRIX.md](DECISION_MATRIX.md).
3. Dispatch rules based on [DISPATCH_PATTERNS.md](DISPATCH_PATTERNS.md).
4. Fallback rules based on [FALLBACK_CHAINS.md](FALLBACK_CHAINS.md).
5. Failure checks from [PITFALLS.md](PITFALLS.md).

## Operating rules

- route by task fit, not by model prestige
- keep the orchestrator in control of the workflow
- bound delegated tasks tightly
- pass only the context needed for the delegated work
- require evidence when models disagree
- define a fallback before you need it

## Minimum quality bar

Before you consider coordination complete, confirm:

- the system can explain why each task type goes to a given model
- delegated tasks have explicit scope and output requirements
- budget waste from blind exploration is reduced
- a failed model call does not collapse the whole workflow if a fallback exists
