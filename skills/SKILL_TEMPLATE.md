# Skill Template

This document defines the recommended anatomy of a skill directory.

## Directory shape

Use a structure equivalent to this:

```text
skill-name/
  SKILL.md
  feedback.log
  README.md
  templates/
    TASK_TEMPLATE.md
```

Your exact filenames may vary, but every skill should contain the same concepts.

## Required files

### `SKILL.md`

This is the primary instruction file.

It should answer:

- what the skill does
- when the agent should use it
- what inputs it expects
- what steps it follows
- what output it should produce
- what safety or quality checks apply

Recommended sections:

```md
# Skill Name

## Purpose

## When To Use This Skill

## Inputs

## Procedure

## Output

## Failure Modes

## Feedback Application
```

### `feedback.log`

This file stores skill-local corrections.

The agent should read it before each skill run and append durable new lessons after execution when needed.

See [FEEDBACK_LOG_SPEC.md](FEEDBACK_LOG_SPEC.md).

### `README.md`

This optional but recommended file gives a quick human-readable overview of the skill directory and its contents.

### Supporting files

Supporting files may include:

- task templates
- checklists
- reference notes
- example inputs
- example outputs

Keep supporting files inside the skill so the capability stays self-contained.

## Template `SKILL.md`

```md
# Skill Name

## Purpose

State the capability in one sentence.

## When To Use This Skill

- trigger condition one
- trigger condition two

## Inputs

- required input one
- required input two

## Procedure

1. Read this file.
2. Read `feedback.log`.
3. Gather the required inputs.
4. Execute the skill procedure.
5. Produce the required output.

## Output

Describe the expected deliverable.

## Failure Modes

- likely failure one
- likely failure two

## Feedback Application

Apply all relevant entries from `feedback.log` before acting.
Append new durable corrections after acting.
```

## Design rules

- keep the skill narrow
- keep inputs and outputs explicit
- keep the feedback mechanism local
- keep supporting files close to the skill
- avoid hidden dependencies on unrelated workspace context
