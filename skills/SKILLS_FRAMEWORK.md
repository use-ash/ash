# Skills Framework

This document explains what a skill is and how a skill system should work.

For conceptual background, see:

- <https://use-ash.github.io/ash/tool-integrations/>

## What a skill is

A skill is a reusable capability packaged as a directory.

A skill usually contains:

- an instruction file that explains what the skill does
- a feedback log that stores corrections
- supporting files such as templates, references, or checklists

The skill directory is the unit of reuse.

## Why skills exist

Without skills, repeated procedures get buried in general system prompts or chat history.

That creates problems:

- the same instructions are rewritten repeatedly
- corrections do not stay near the capability they improve
- the agent has to remember too many procedures globally

Skills solve this by localizing capability-specific instructions.

## Skill behavior model

A skill should support this flow:

1. the agent detects that a capability is needed
2. the agent reads the skill definition
3. the agent reads the skill's feedback log
4. the agent performs the capability
5. the agent records any durable correction back into the skill

This creates a local improvement loop.

## Skill boundaries

Use skills for:

- recurring procedures
- bounded tool-use workflows
- structured external research patterns
- review or filtering processes

Do not use skills for:

- long-term user preferences
- cross-project memory
- live thread tracking

Those belong in memory or continuity.

## Self-improvement model

A skill improves when its own feedback log accumulates corrections.

This works because:

- the correction stays near the procedure
- future runs load the correction automatically
- unrelated skills do not inherit irrelevant rules

## Skill quality rules

A good skill is:

- narrow in scope
- easy to trigger
- easy to read quickly
- explicit about inputs and outputs
- updated by feedback over time

A bad skill is:

- vague
- too broad
- dependent on hidden context
- missing examples
- unable to record lessons locally

## Success criteria

The skill system is working when:

- recurring capabilities stop being re-explained in chat
- corrections to one capability improve future runs of that capability
- the agent can invoke the right skill without loading every skill in detail
