---
name: Verify Before Claiming Completion
description: The agent must not report task completion until the relevant verification step has been run.
type: feedback
updated_at: 2026-03-21
status: active
---

# Rule

Do not claim a task is complete until the smallest meaningful verification step has run successfully.

# Why This Exists

A prior task was reported as finished after editing, but the behavior had not been checked.

# Trigger

Apply this rule whenever the agent changes files, updates configuration, or reports that a fix is done.

# How To Apply

Run a relevant verification step, capture the result, and report that evidence with the outcome.
