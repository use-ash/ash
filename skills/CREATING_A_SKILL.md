# Creating A Skill

This guide explains how to create a new skill using this framework.

## Step-by-step process

1. Choose one recurring capability.
2. Define the trigger conditions.
3. Define the required inputs.
4. Define the procedure.
5. Define the expected output.
6. Create the skill directory.
7. Add a `SKILL.md`.
8. Add a `feedback.log`.
9. Add templates or references if they help the skill run consistently.
10. Run the skill, gather feedback, and improve it.

## Pattern: Codex dispatch skill

Purpose:

Send a bounded coding or review task to a specialized code-focused model.

What the skill should define:

- when a code-focused worker is appropriate
- how to bound the task
- what files or context should be passed
- what deliverable should come back
- how to avoid blind exploration and budget waste

Typical inputs:

- task description
- target files or modules
- expected output format
- budget or scope limit

Typical output:

- patch, findings, or design review
- explicit verification status if applicable

Failure modes:

- task too broad
- missing file context
- delegated worker becoming a second orchestrator

## Pattern: web research skill

Purpose:

Gather current external information in a structured way.

What the skill should define:

- when live research is required
- what sources are acceptable
- how to capture links and uncertainty
- how to separate facts from inference

Typical inputs:

- research question
- scope or recency constraint
- source quality requirement

Typical output:

- concise answer
- source list
- uncertainty notes

Failure modes:

- outdated sources
- missing citation discipline
- treating external claims as confirmed without enough evidence

## Pattern: content filter skill

Purpose:

Process untrusted external content before it reaches the main agent context.

What the skill should define:

- which content is considered untrusted
- how to summarize it safely
- how to mark injection attempts
- what warnings to attach when confidence is low

Typical inputs:

- raw external text
- source type
- desired output format

Typical output:

- clean summary
- flagged instructions or suspicious passages
- warning marker if sanitization was incomplete

Failure modes:

- passing raw instructions through as trusted content
- losing important factual detail during filtering
- failing open without clearly marking the content as untrusted

## Quality checks

A new skill is ready when:

- the trigger condition is clear
- the procedure is specific
- the output is well defined
- the feedback log can improve future runs
- the skill can be used without relying on hidden chat context
