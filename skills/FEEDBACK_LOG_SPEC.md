# Feedback Log Spec

This document defines how skill-local feedback logs should work.

## Purpose

A skill feedback log stores corrections that improve one specific capability.

This prevents local lessons from getting lost in chat history or mixed into global memory when they only matter for one skill.

## Behavior rule

The agent should:

1. read the feedback log before executing the skill
2. apply relevant entries during execution
3. append new durable corrections after execution

If the feedback log exists but is never read, the skill is not improving.

## File format

The format can be simple plain text, Markdown, or line-oriented entries.

The important requirements are:

- append-friendly
- easy to read quickly
- easy to parse by an agent

## Recommended entry structure

Each entry should include:

- date
- issue or lesson
- correction
- application guidance

Example:

```text
[2026-03-21]
Issue: The skill returned too much raw source material.
Correction: Summarize findings before presenting supporting detail.
Apply: Use short summaries first unless exact quotation is required.
```

## What belongs in a skill feedback log

Good fits:

- repeated mistakes specific to the skill
- formatting preferences specific to the skill output
- safety rules specific to the skill
- efficiency improvements that change how the skill should operate

Bad fits:

- broad workspace rules that belong in global memory
- one-off transient incidents with no durable lesson
- project state unrelated to the skill itself

## Reading rule

Before running the skill:

- read the newest entries first if the log is long
- identify entries relevant to the current invocation
- apply them as constraints or preferences during execution

## Writing rule

Append an entry when:

- the user corrects the skill's behavior
- the skill fails in a repeatable way
- a better stable procedure is discovered

Do not append minor noise after every run.

## Maintenance

Condense or rewrite the log if it becomes too long to read efficiently.

When condensing:

- preserve the durable lessons
- merge duplicates
- remove obsolete entries

## Success criteria

The feedback log is working when the skill behaves better over time without requiring the user to repeat the same correction for that skill.
