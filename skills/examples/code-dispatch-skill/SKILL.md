# Code Dispatch Skill

## Purpose

Use this skill when a bounded coding, audit, or design-review task should be delegated to a code-focused worker.

## When To Use This Skill

- the task is mostly about source files
- the task can be clearly bounded
- a specialist code worker is a better fit than the main orchestrator

## Inputs

- task objective
- relevant files or modules
- constraints or non-goals
- expected deliverable

## Procedure

1. Read this file.
2. Read `feedback.log`.
3. Define a bounded task.
4. Pass only the context needed for the task.
5. Request a concrete deliverable.
6. Review the returned result before accepting it.

## Output

Return one of:

- a patch proposal
- a review with findings
- a focused design answer

## Failure Modes

- the task is too broad
- the worker has insufficient file context
- the worker spends budget exploring unrelated areas

## Feedback Application

Apply all relevant entries in `feedback.log` before dispatching work.
