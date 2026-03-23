# Schema

This document defines the required frontmatter schema and the four memory types.

## Required frontmatter

Every memory note must include these fields:

| Field | Type | Required | Meaning |
|---|---|---|---|
| `name` | string | yes | Human-readable topic name |
| `description` | string | yes | One-sentence summary used for routing |
| `type` | enum | yes | One of `user`, `feedback`, `project`, `reference` |

Minimal example:

```yaml
---
name: Preferred Communication Style
description: How the user wants the agent to communicate during technical work.
type: user
---
```

## Recommended optional fields

These fields are not required, but they improve maintainability:

| Field | Type | Meaning |
|---|---|---|
| `updated_at` | date | Last meaningful update date in `YYYY-MM-DD` form |
| `status` | string | `active`, `archived`, or another clear state |
| `aliases` | list of strings | Alternate names the agent may search for |
| `scope` | string | Which project, workspace, or user the note applies to |

Example:

```yaml
---
name: Deployment Approval Rule
description: Deployment actions require explicit approval from the operator.
type: feedback
updated_at: 2026-03-21
status: active
aliases:
  - release approval
  - deploy permission
scope: workspace
---
```

## Type definitions

### `user`

Use `user` for durable facts about the person or team the agent is helping.

Good fits:

- communication preferences
- recurring habits
- stable preferences about workflow
- personal or team constraints that should shape interaction

Do not use `user` for project status or one-off corrections.

Example topics:

- preferred level of detail
- working hours
- approval preferences

### `feedback`

Use `feedback` for corrections that should change future behavior.

This is the highest-value memory type because it turns mistakes into durable rules.

Good fits:

- "always verify before claiming success"
- "never publish this repository"
- "check existing notes before asking the user"

A good feedback note contains:

- the rule
- the reason
- the trigger condition
- the expected future behavior

### `project`

Use `project` for work that spans sessions.

Good fits:

- current objective
- important status
- pending next steps
- decisions that affect ongoing work

Project notes should change as the work changes. They are durable across sessions, but not permanent forever.

### `reference`

Use `reference` for durable pointers to external systems, locations, or facts the agent needs to re-use.

Good fits:

- where credentials are stored
- what service owns a dataset
- where dashboards, repos, or APIs live
- canonical locations for documentation

Reference notes should point to the source of truth. They should not duplicate large amounts of source content.

## Example bodies by type

### `user` example

```md
---
name: Review Style Preference
description: The user wants concise reviews with findings first.
type: user
---

# Preference

When reviewing changes, present the findings before the summary.

# Application

Use severity ordering and keep the recap short.
```

### `feedback` example

```md
---
name: Verify Before Claiming Completion
description: The agent must not report success without execution evidence.
type: feedback
---

# Rule

Do not claim a task is complete until the relevant verification step ran.

# Why This Exists

A prior task was reported as finished after editing, but the change had not been tested.

# How To Apply

Run the smallest meaningful verification step, capture the result, and report it.
```

### `project` example

```md
---
name: Documentation Framework Rollout
description: Tracks the current state of the documentation framework work.
type: project
---

# Current State

Repository structures are drafted. Examples still need review.

# Next Step

Finalize examples and verify every required file exists.
```

### `reference` example

```md
---
name: External Status Dashboard
description: Points to the service that reports system health.
type: reference
---

# Source

The health dashboard lives in the external operations service.

# Usage

Check the dashboard before diagnosing missing scheduled outputs.
```

## Naming guidance

Use names that remain understandable months later.

Prefer:

- `feedback_verify_before_claiming_completion.md`
- `project_customer-onboarding-redesign.md`
- `reference_primary-analytics-dashboard.md`

Avoid vague names:

- `notes.md`
- `important.md`
- `stuff.md`

## Validation rules

Reject or fix a memory note when:

- required frontmatter is missing
- `type` is not one of the four allowed values
- `description` is vague
- the note mixes multiple topics
- the note duplicates an existing canonical note
