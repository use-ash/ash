# Dispatch Patterns

This document describes patterns for sending work to other models or workers.

## Goal

A dispatch should transfer enough context to complete the task without transferring so much context that the worker wastes budget or becomes confused.

## Minimal dispatch packet

A good dispatch includes:

- task objective
- exact scope
- relevant context only
- expected output
- stop condition

Example shape:

```text
Objective: Review the memory schema draft.
Scope: Only the schema document and example notes.
Context: The repository must remain code-free and agent-readable.
Output: Findings list with any missing requirements.
Stop condition: Do not inspect unrelated repositories.
```

## Prompt-file in, response-file out pattern

One reliable pattern is to serialize the request and response into files or equivalent structured payloads.

Why this helps:

- the worker receives a stable task packet
- the result is durable and reviewable
- the orchestrator can inspect the response before acting

The exact transport does not matter. The structured handoff does.

## Context transfer rule

Do not assume the worker can inspect the whole environment safely or cheaply.

Pass:

- the files that matter
- the policy constraints
- the expected deliverable

Do not pass unrelated memory, side conversations, or broad workspace context unless required.

## Budget control

Before dispatch, define:

- maximum exploration scope
- acceptable source set
- expected output length
- retry policy

Specialists waste budget when they explore first and solve second.

## Return handling

When a worker returns:

1. inspect the output
2. compare it to the request
3. verify evidence if the task is high impact
4. merge the useful result into the parent workflow

The orchestrator remains responsible for the final action.

## Second-opinion pattern

Use a second opinion only when the question matters enough to justify the extra cost.

To make second opinions useful:

- ask the same concrete question
- require evidence
- compare the evidence, not just the confidence

## Success criteria

Dispatch is working when:

- delegated tasks are narrowly scoped
- specialists return the expected deliverable
- the orchestrator can integrate results without redoing the whole task
- budget burn from blind exploration stays low
