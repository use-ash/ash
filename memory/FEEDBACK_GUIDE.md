# Feedback Guide

This guide describes the feedback loop that turns corrections into improved future behavior.

This is the most valuable part of the memory framework.

## Why feedback matters

Most memory describes the world. Feedback changes the agent.

Without a feedback loop:

- the user corrects the agent
- the session ends
- the correction disappears
- the same mistake happens again

With a feedback loop:

- the user corrects the agent
- the correction becomes a durable rule
- the rule is loaded in later sessions
- behavior changes

## The loop

Implement feedback as a four-stage cycle:

1. Correction happens.
2. Correction is saved as a feedback note.
3. Feedback notes are loaded in future sessions or before relevant tasks.
4. The agent changes behavior and avoids repeating the mistake.

If any stage is missing, the loop breaks.

## What counts as feedback

Save feedback when the user:

- corrects a repeated behavior
- defines a hard rule
- explains a past mistake and its prevention
- points out a workflow preference that should persist
- teaches a lesson that applies to future tasks

Do not create feedback notes for trivial one-off preferences unless they are likely to matter again.

## Structure of a feedback note

A feedback note should answer four questions:

1. What is the rule?
2. Why does the rule exist?
3. When should the rule be applied?
4. What should the agent do differently?

Recommended body structure:

```md
# Rule

State the correction in imperative form.

# Why This Exists

Describe the incident, mistake, or tradeoff that produced the rule.

# Trigger

State when this rule becomes relevant.

# How To Apply

Describe the required future behavior.
```

## Writing strong feedback

Strong feedback is:

- specific
- actionable
- narrow enough to avoid over-application
- durable across sessions

Weak feedback is:

- vague
- missing a trigger condition
- written as blame instead of instruction
- too broad to be safe

Bad:

```md
Be more careful.
```

Good:

```md
Verify the current code or state file before acting on retrieved memory.
```

## Capture triggers

The agent should actively look for capture triggers during work.

Capture feedback when it hears patterns like:

- "Do not do that again"
- "From now on"
- "Always"
- "Never"
- "Next time"
- "Remember that"
- "You should have"

These phrases do not guarantee the note belongs in memory, but they are strong candidates.

## Loading strategy

Load feedback in two ways.

### Session-level loading

Load the highest-priority feedback notes at the start of each session. These are the broad rules that shape general behavior.

Examples:

- approval rules
- verification rules
- safety rules

### Task-level loading

Load narrower feedback notes when the task category matches the note.

Examples:

- repo publishing rules during repository tasks
- communication preferences during review tasks
- deployment rules during release tasks

## Behavior change test

A feedback note is working only if it changes action.

After loading a feedback note, the agent should be able to say:

- what rule applies
- why it applies
- what it will do differently right now

If the note gets loaded but does not change behavior, rewrite it.

## Review and cleanup

Review feedback notes regularly for:

- duplicates
- conflicting rules
- rules that became outdated
- rules written too broadly

Merge overlapping notes into one canonical rule when possible.

## Failure modes

### Correction never gets saved

The same mistake repeats.

Prevention:

- define a rule for capturing durable corrections immediately

### Feedback gets saved but never loaded

The note exists but has no effect.

Prevention:

- include feedback retrieval in session start and task start logic

### Feedback is too broad

The agent applies the rule in situations where it should not.

Prevention:

- add a clear trigger section

### Feedback is buried in transcripts

The correction exists only in chat history.

Prevention:

- move durable feedback into a dedicated feedback note

## Success condition

The feedback system is successful when a user correction produces a durable improvement without the user having to repeat the same correction in later sessions.
