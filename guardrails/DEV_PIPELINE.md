# Dev Pipeline

This document defines the PLAN-BUILD-VERIFY-REVIEW-COMMIT-DEPLOY workflow for agent-driven changes.

For conceptual background, see:

- <https://use-ash.github.io/ash/dev-pipeline/>

## Why this exists

An agent can change files quickly.

That does not mean the change is correct, safe, or ready.

The pipeline exists to force evidence at the points where speed hides risk.

## The stages

### PLAN

Decide:

- what will change
- which files or systems are in scope
- what could break
- how success will be verified
- how to roll back if the change is risky

Use a full plan for larger or riskier work.
Use a lighter plan for small bounded changes.

### BUILD

Make the change.

Keep the change scoped to the plan.

### VERIFY

Prove the change behaves as claimed.

Examples:

- compile or syntax check
- run the smallest relevant test
- execute the narrowest meaningful validation

Verification is mandatory for changes.

### REVIEW

Inspect the actual change for:

- unintended edits
- secret leakage
- protected-path risk
- mismatches between claim and diff

This is where the agent checks whether it solved the right problem safely.

### COMMIT

Create a durable history point only when the operating policy or human workflow allows it.

The framework does not assume every task includes commit authority.

### DEPLOY

Move the change into a live environment only when the task explicitly includes deployment and the safety policy allows it.

## Variants

Use three variants.

### Quick fix

For one or two tightly scoped files.

May use a light plan.
Must still verify and review.

### Feature path

For broader changes, multi-file work, architecture changes, or safety-sensitive edits.

Use a full plan, stronger verification, and careful review.

### Production hotfix

For urgent but safety-sensitive fixes.

Use a micro-plan, the fastest safe verification, and strict review.

## Hard rule

Skip bureaucracy, not evidence.

The paperwork may shrink.
The proof requirement does not.

## Completion claim rule

Do not report a task as complete after BUILD alone.

A completion claim without verification evidence is false.

## Success criteria

This pipeline is working when:

- the amount of planning matches the task size
- verification happens for all meaningful changes
- review catches unintended or risky edits
- completion claims are backed by evidence
