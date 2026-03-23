# Memory Framework

This document describes how to structure a file-based memory system for an AI agent.

For conceptual background, see the ASH wiki:

- <https://use-ash.github.io/ash/>
- <https://use-ash.github.io/ash/memory-and-continuity/>

This file focuses on implementation patterns, not theory.

## Purpose

An agent loses its short-term context when a session ends. A memory system solves that by storing durable facts in files the agent can read later.

The memory system should answer four questions:

1. What should the agent remember across sessions?
2. Where should that memory live?
3. How should the agent find the right note quickly?
4. How should corrections change future behavior?

## Core structure

Use a file-based memory store with these parts:

- `MEMORY.md` or an equivalent short index file
- a directory of Markdown memory notes
- YAML frontmatter at the top of every memory note
- a retrieval method that loads relevant notes on demand
- optional semantic search or embeddings when note count grows

Keep the system inspectable. A human should be able to open the memory folder and understand what exists without special tools.

## Recommended layout

Use a layout equivalent to this:

```text
memory/
  MEMORY.md
  user_*.md
  feedback_*.md
  project_*.md
  reference_*.md
  archive/
```

The exact folder names may differ in your workspace. The pattern matters more than the names.

## File format

Each memory note is a Markdown file with:

1. YAML frontmatter for routing and indexing
2. a short body with the durable fact, rule, or reference
3. explicit dates when timing matters

Example shape:

```md
---
name: Example Topic
description: One-sentence summary of what this note is for.
type: feedback
---

# Rule

State the durable correction here.

# Why This Exists

Explain the failure or reason.

# How To Apply

Describe the future behavior.
```

## The index

The index file is the memory router. It is not the full memory store.

The index should stay short enough to load at the start of a session. It should contain:

- a brief description of the memory system
- the highest-value notes
- categories or pointers to note groups
- loading guidance for the agent

Keep the index lean. When the index turns into a transcript, retrieval quality drops.

## Retrieval model

Use two retrieval layers.

### Layer 1: always-load index

Load the index file at the start of each session. This gives the agent:

- the memory map
- the most important constraints
- the canonical paths or note names to inspect next

### Layer 2: on-demand note loading

Load individual notes only when they are relevant to the current task, thread, or user request.

Relevance signals include:

- direct keyword match
- task category match
- active project match
- recent correction match
- semantic similarity, if available

## Scaling rule

When the note count is small, a short index and manual selection are enough.

When the note count grows, add an indexer or semantic retrieval layer that can search note content by meaning. The storage can remain file-based even when retrieval becomes more advanced.

Do not wait until the memory folder becomes unusable. Introduce better retrieval as soon as session startup starts slowing down or relevant notes start getting missed.

## Memory boundaries

Use memory for:

- preferences
- constraints
- feedback and corrections
- project state that spans sessions
- references to external systems or locations

Do not use memory for:

- source code
- temporary logs
- large transcripts
- machine-generated bulk output
- information that should live in structured state instead

## Writing rules

When creating or updating memory:

- write one topic per file
- use one canonical note for each durable topic
- keep descriptions short and specific
- use absolute dates such as `2026-03-21`
- explain why a rule exists
- explain how the agent should apply it later

## Maintenance rules

Review memory regularly for:

- stale notes
- duplicate notes
- oversized notes
- outdated references
- rules that conflict with current code or policy

If a note is obsolete, either update it or archive it. Do not leave contradictory notes active.

## Success criteria

The framework is working when:

- a new session can recover useful context without asking the user to repeat it
- a prior correction changes future behavior
- project work can pause and resume across sessions
- the agent can find the right note without reading every note

If those outcomes are not happening, the memory system is storing text but not providing memory.
