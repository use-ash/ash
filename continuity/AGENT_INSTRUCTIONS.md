# Agent Instructions

You are implementing continuity for an agent system.

Your goal is to stop work from disappearing when a chat ends, a model changes, or the user switches channels.

## Outcome

Create a continuity system that:

- tracks open and closed threads
- survives restarts and model switches
- lets a new session recover what is still in progress
- separates conversation state from memory notes

## Required components

Implement these pieces in your own workspace:

1. A persistent state file based on [THREAD_SCHEMA.md](THREAD_SCHEMA.md).
2. A session start routine based on [SESSION_START_GUIDE.md](SESSION_START_GUIDE.md).
3. A handoff method that updates thread summaries and next steps before context changes.
4. A rule for closing completed threads and keeping only active work in the open set.

## Implementation sequence

1. Read [CONTINUITY_FRAMEWORK.md](CONTINUITY_FRAMEWORK.md).
2. Create your persistent thread ledger using [THREAD_SCHEMA.md](THREAD_SCHEMA.md).
3. Implement the startup sequence in [SESSION_START_GUIDE.md](SESSION_START_GUIDE.md).
4. Add handoff rules from [HANDOFF_PATTERNS.md](HANDOFF_PATTERNS.md).
5. Populate the file with real active and closed thread entries.

## Operating rules

- update the thread ledger whenever work meaningfully changes
- record next steps before handing work to another model or ending a session
- store concise summaries, not full transcripts
- keep closed threads accessible but separate from active threads
- use absolute timestamps in a consistent format

## Separation of concerns

Use continuity for:

- what is open
- what just happened
- what comes next
- which channels or models were involved

Do not use continuity for:

- long-term behavioral rules
- user preferences
- stable external references

Those belong in memory, not in the thread ledger.

## Minimum quality bar

Before you consider continuity complete, confirm:

- a new session can identify all active threads without reading old chat history
- every active thread has a summary and a next step
- closed work moves out of the active set
- model and channel handoffs do not lose context
