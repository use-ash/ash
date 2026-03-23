# Decision Matrix

This document provides a template for deciding which model should handle which kind of task.

Do not copy the example rows blindly. Replace them with the models and constraints in your own environment.

## Template matrix

| Task type | Primary role | Why this role fits | Required context | Budget rule | Fallback role |
|---|---|---|---|---|---|
| Code change or code review | coding specialist | Strong file and patch reasoning | Exact files, task scope, constraints | Keep scope narrow | orchestrator or secondary coding model |
| Live web research | research specialist | Access to current external information | Research question, recency need, source requirements | Require sources and uncertainty notes | orchestrator with browsing or secondary research model |
| Maintenance triage | low-cost triage model | Cheap fast analysis for routine reports | Raw report and expected output format | Prefer low cost unless confidence is too low | research model or orchestrator |
| Workflow planning or final judgment | orchestrator | Needs cross-task reasoning and decision ownership | Thread context, relevant memory, returned evidence | Keep specialists out of broad planning | none |

## How to use the matrix

For each task, answer:

1. What kind of task is this?
2. Which role is the best fit?
3. What context does that role actually need?
4. What is the budget limit?
5. What should happen if the primary role is unavailable?

## Context rule

Pass only the context needed for the selected role.

Too little context causes errors.
Too much context causes waste.

## Budget rule

Define budget in terms meaningful to your environment, such as:

- token spend
- time limit
- number of research rounds
- maximum file set

Budget should be set before dispatch, not after overspending.

## Review rule

Review the matrix when:

- a new model is added
- a model quality or cost profile changes
- a repeated failure shows the routing decision is wrong

## Success criteria

The decision matrix is healthy when routing decisions are easy to explain, easy to repeat, and easy to revise.
