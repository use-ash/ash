# Guardrails Framework

This document explains why guardrails exist and what they must protect against.

For conceptual background, see:

- <https://use-ash.github.io/ash/security-and-guardrails/>
- <https://use-ash.github.io/ash/dev-pipeline/>

## Why guardrails exist

An autonomous agent can act quickly, repeatedly, and across many surfaces.

That speed is useful when the agent is correct.
It is dangerous when the agent is wrong.

Mistakes are harder to catch when:

- work happens across many sessions
- multiple models participate
- actions are taken through tools
- background jobs run when no human is watching

Guardrails exist to make risky behavior visible, block truly dangerous actions, and preserve evidence when something goes wrong.

## What guardrails should do

A guardrails system should:

1. log actions at the point where they happen
2. block writes to critical targets
3. treat external content as hostile until filtered
4. reduce the chance that secrets leak into transcripts or history
5. alert humans when attention is needed
6. enforce a development pipeline that requires evidence

## Safety model

Use layered defenses.

Do not assume one control is enough.

Examples:

- a protected file list is not enough if shell commands can still overwrite the same file
- a pre-commit secret scanner is not enough if secrets can still leak into transcripts
- an alert system is not enough if it produces too much noise to read

Each layer should catch a different failure path.

## Fail-open vs fail-closed

Use fail-closed for actions that can cause direct damage.

Examples:

- editing a protected file
- writing to secret-bearing paths
- bypassing a hard safety rule

Use fail-open for infrastructure that should not kill the whole session if it breaks.

Examples:

- auxiliary logging
- best-effort analytics
- non-critical advisory checks

This distinction keeps the system safe without making it brittle.

## Evidence over trust

A guardrails system should prefer evidence over assurances.

Examples of good evidence:

- audit log entries
- diff review
- verification output
- alert history

Examples of weak substitutes:

- "the model said it checked"
- "the change looked small"
- "this probably does not need review"

## Design principle

Skip bureaucracy, not evidence.

Small tasks may need less ceremony.
They still need proof.

## Filesystem sandbox

Restrict where the agent can write. Allow the workspace directory and temp directories. Block everything else by default.

This matters most when the agent runs without human approval (headless mode, remote access, scheduled tasks). Without a sandbox, an agent can write to shell profiles, SSH keys, launch agents, or system config files. None of these trigger a permission prompt when permissions are skipped.

The sandbox should:

- check every resolved file path against an allowlist and a blocklist
- give the blocklist priority over the allowlist
- resolve symlinks before checking (an agent can symlink a blocked path into an allowed directory)
- block both direct file writes and shell commands that target paths outside the sandbox
- produce a hard block, an audit log entry, and an alert on violation

## Permission deny list

Block dangerous commands at the tool level before they reach the audit hook or any other layer.

The deny list fires first. A blocked command never reaches the audit hook, the sandbox, or the model. This is the fastest gate.

Categories to block:

- **Repository exposure:** changing repo visibility, adding git remotes to the workspace, pushing main branch to any remote. These exist because an agent pushed a full workspace to a public repo while trying to deploy a wiki.
- **Destructive operations:** recursive deletion on workspace paths, force push, hard reset
- **Shell injection patterns:** eval, pipe-to-shell installs
- **Permission escalation:** chmod 777
- **History rewriting:** force push to main/master branches

The deny list should not block reads, normal git operations, or file editing inside the workspace.

## Repository exposure prevention

This is a specific class of incident that deserves its own controls.

An agent optimizing for task completion may decide that making a repository public, adding a remote, or pushing a branch is the fastest way to finish a task. If the repository contains the full workspace (code, credentials, personal files), that decision exposes everything.

Three rules prevent this:

1. The workspace git repo has exactly one remote. No other remotes are added. Wiki and documentation deploys happen from separate directories with their own isolated git.
2. Changing repository visibility requires explicit human approval in the same message. The deny list blocks the command so the agent cannot execute it autonomously.
3. Pushing the main branch to any non-origin remote is blocked. Documentation deploys use dedicated branches only.

## Sub-agent guardrails

Audit hooks registered in the main session do not fire for sub-agents launched through external wrappers. Sub-agents run in their own process with their own sandbox rules.

Three compensating controls:

1. **Restricted sandbox by default.** The dispatch wrapper uses a sandbox mode that allows writes only inside the workspace. Network access is disabled unless the task needs it. The wrapper auto-detects network requirements from the prompt content.
2. **Prompt-injected safety rules.** Every sub-agent prompt starts with a mandatory block listing protected files, blocked system paths, and forbidden operations. The sub-agent reads these before the task.
3. **Post-run diff check.** After the sub-agent finishes, the wrapper diffs the workspace state against its pre-run snapshot. File changes not named in the original task trigger an alert.

## Success criteria

Guardrails are working when:

- unsafe actions are blocked before they land
- important actions leave an audit trail
- external prompt injection does not gain control of the agent
- secrets are harder to leak and easier to detect
- alerts surface real problems without training humans to ignore them
- the workspace cannot be exposed to public repositories by any agent action
- sub-agents operate under the same safety constraints as the main session
