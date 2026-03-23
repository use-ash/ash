# Session Start Guide

This guide defines what should happen when a new session begins.

The goal is to rebuild useful context from files before the agent starts working.

## Session start sequence

Run this sequence in order.

1. Load the persistent conversation state file.
2. Read `global_context` and `session_metadata`.
3. Review `active_threads`.
4. Identify threads relevant to the current session or incoming request.
5. Load any linked or relevant memory notes.
6. Build a compact working context.
7. Begin the task.

## What to look for

At session start, answer these questions:

1. What work is currently open?
2. What changed most recently?
3. What is the next step for each active thread?
4. Which thread is relevant to the current message?
5. Is any supporting memory needed before acting?

If the agent cannot answer those questions, continuity is incomplete.

## Thread selection rule

Do not load every closed thread.

Instead:

- review all active threads
- select the active thread or threads that match the current request
- consult closed threads only when historical context is necessary

This keeps startup fast while preserving continuity.

## Context assembly rule

The session context should include:

- the relevant active thread summary
- the relevant next step
- any matching memory notes
- any immediate blockers or constraints

The session context should not include:

- full transcript history
- every unrelated active thread in detail
- stale or unverified notes

## Recovery from missing context

If the session start routine detects missing or low-quality continuity:

1. identify what is missing
2. inspect the most recent relevant thread entries
3. inspect linked memory or source files
4. rebuild the summary and next step
5. update the state file so the next session starts cleanly

Do not leave the ledger broken after discovering the gap.

## Recommended checklist

Use or adapt a startup checklist like this:

```text
[ ] Load conversation state
[ ] Review session metadata
[ ] Review active threads
[ ] Match current message to thread
[ ] Load supporting memory
[ ] Confirm next step
[ ] Update thread if context was repaired
```

## Startup output

At the end of session start, the agent should be able to produce:

- the active thread it is working on
- a one-paragraph summary of that thread
- the next concrete action
- any durable memory that affects the action

If it cannot, the startup process should keep gathering context before starting work.
