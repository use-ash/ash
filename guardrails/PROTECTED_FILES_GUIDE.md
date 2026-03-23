# Protected Files Guide

This guide explains how to block the agent from modifying critical files or paths.

## Purpose

Some targets are too risky for autonomous edits.

Examples:

- production execution paths
- guardrail configuration
- secret stores
- deployment configuration
- identity or policy files

Protected file blocking exists so an agent cannot casually modify a path where a small mistake has outsized consequences.

## What to protect

Protect targets where:

- a bad edit causes production impact
- a bad edit weakens the safety system
- a bad edit exposes credentials
- a bad edit changes deployment or infrastructure control

Protect both:

- exact critical files
- pattern-based secret-bearing or configuration paths

## How to check paths

Check the resolved real path, not only the typed path string.

Why:

- symlinks can hide the true target
- relative paths can bypass naive checks

Resolve the candidate target first, then compare it to your protected lists and globs.

## Write surfaces to guard

Do not protect only the obvious editor tool.

Block or inspect every write surface that can reach a protected target, including:

- direct file writes
- multi-file edits
- shell redirects such as `>` and `>>`
- `tee`
- copy and move operations
- in-place text replacement
- archive extraction that overwrites files
- interpreted commands that open files in write mode

If the agent can use a shell, shell-based bypasses must be part of the design.

## Bash bypass model

An agent may switch from a blocked edit tool to a shell command.

Design protections that inspect for:

- redirects into protected paths
- utilities that write to files
- file replacement patterns
- generated content that gets piped into a protected target

The goal is not to parse every possible command perfectly.
The goal is to close the common and practical bypasses.

## Symlink attacks

A safe-looking path may resolve to a protected target.

Prevention rules:

- resolve real paths before checking
- inspect destination paths after move or copy expansion
- do not trust display names alone

## Block semantics

A hard block should be distinguishable from an infrastructure failure.

Recommended behavior:

- use a clear blocked status
- include the reason
- return a recognizable deny result to the caller

This helps the orchestrator understand the difference between "unsafe action denied" and "guardrail crashed."

## Review process

Review the protected list whenever:

- new production paths are added
- new guardrail files appear
- new secret storage locations are introduced
- deployment mechanisms change

## Success criteria

The protection is working when:

- critical targets cannot be modified through direct edits
- shell-based bypasses are detected or blocked
- symlink indirection does not defeat the policy
- the agent receives a clear explanation of why the action was denied
