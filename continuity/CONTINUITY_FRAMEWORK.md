# Continuity Framework

This document explains how to preserve conversational and task context across sessions.

For conceptual background, see:

- <https://use-ash.github.io/ash/>
- <https://use-ash.github.io/ash/memory-and-continuity/>

## The problem

An agent's context window ends when the session ends.

Without continuity:

- half-finished work disappears into chat history
- model handoffs lose important detail
- channel switches create parallel confusion
- the user has to restate what was already known

## The solution

Keep session state in files.

Use a persistent thread ledger that records:

- what work is active
- what work is closed
- what the current summary says
- what the next step should be
- which model or channel last touched the thread

The state file becomes the handoff point between sessions.

## Core components

Build continuity from three parts:

1. A persistent conversation state file
2. A session start process that reads and interprets that file
3. A handoff process that updates the file before context changes

## Relationship to memory

Continuity and memory are related but different.

Continuity stores the current shape of ongoing work.

Memory stores durable facts, rules, and references that should survive longer than a thread.

Use continuity for active thread tracking.
Use memory for lasting knowledge.

## State model

Use a state structure with at least:

- active threads
- closed threads
- global context
- session metadata

The exact field names may differ in your system. The meaning should not.

## Thread model

A thread is a unit of ongoing work that can survive:

- a new session
- a channel change
- a delegated subtask
- an interrupted workflow

Each active thread should be compact enough to reload quickly and clear enough that a different model can continue it.

## Summary rule

A thread summary should explain:

- what the thread is about
- what has already happened
- what matters now

Do not store full transcripts in the state file. Store decision-quality summaries.

## Next-step rule

Every active thread should have a next step.

If the thread has no next step, the agent will reopen the thread and still not know what to do.

The next step should be specific enough to act on immediately.

Bad:

```text
Continue later.
```

Good:

```text
Review the guardrails draft and verify each required file exists.
```

## Closure rule

A thread should move from active to closed when:

- the work is complete
- the user explicitly cancels it
- it is superseded by a newer thread

Closed threads still matter. They provide history and prevent the same work from being reopened accidentally.

## Success criteria

Continuity is working when:

- a new session can recover ongoing work from the ledger alone
- the user does not need to repeat recently active context
- a delegated subtask can return without losing the parent thread
- channel changes do not split the same work into multiple conflicting threads
