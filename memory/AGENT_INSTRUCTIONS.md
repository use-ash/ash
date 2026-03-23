# Agent Instructions

You are implementing a file-based memory system in your own workspace.

Your job is not to copy this repository verbatim. Your job is to apply its patterns to the workspace you control.

## Outcome

Create a memory system that:

- persists across sessions
- is readable by both humans and agents
- separates memory from source code
- captures corrections as durable rules
- can scale from a few notes to many notes

## Required components

Implement these pieces in your own workspace:

1. A memory directory that stores one topic per Markdown file.
2. A short index file that lists the most important notes.
3. A frontmatter schema with the required fields from [SCHEMA.md](SCHEMA.md).
4. A retrieval rule for loading relevant notes at session start or task start.
5. A feedback capture rule based on [FEEDBACK_GUIDE.md](FEEDBACK_GUIDE.md).
6. A cleanup rule that prevents duplication and stale memory.

## Implementation sequence

1. Read [MEMORY_FRAMEWORK.md](MEMORY_FRAMEWORK.md) to understand the system shape.
2. Adopt the schema in [SCHEMA.md](SCHEMA.md).
3. Create an index file using [INDEX_TEMPLATE.md](INDEX_TEMPLATE.md) as a starting point.
4. Create at least one note for each memory type.
5. Implement the feedback loop before adding many other notes. Feedback memory changes behavior. It is higher value than bulk storage.
6. Apply the checks in [PITFALLS.md](PITFALLS.md).

## Operating rules

- Keep one topic per file.
- Use absolute dates when time affects action.
- Treat retrieved memory as a lead, not automatic truth.
- Verify memory against current source or state before acting.
- Update the canonical note instead of creating a duplicate note.
- Keep the index short. Put detail in topic files.

## When to write memory

Write a memory note when any of these become true:

- a user gives a durable preference
- a correction should change future behavior
- a project spans more than one session
- the agent needs to remember an external system, dependency, or location

Do not write memory for:

- temporary intermediate output
- information already captured better in code or logs
- long transcripts
- facts that will expire before the next session and have no lasting value

## Minimum quality bar

Before you consider the memory system complete, confirm:

- every note has valid frontmatter
- every note fits exactly one memory type
- the index points to canonical notes only
- at least one feedback note exists and is loaded in future sessions
- there is a documented cleanup process for stale and duplicate notes
