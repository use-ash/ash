# Fallback Chains

This document explains how to design fallback paths for model routing.

## Why fallbacks matter

Primary models fail.

Reasons include:

- service outage
- quota exhaustion
- latency spike
- cost constraint
- task mismatch discovered after dispatch

Without a fallback, the whole workflow may stop.

## Fallback design rule

Define fallback chains before they are needed.

A fallback chain should answer:

- what is the primary choice
- what is the secondary choice
- what quality tradeoff is expected
- when to stop retrying

## Common patterns

### Local model to cloud model

Use when:

- cheap local triage is preferred first
- cloud capacity exists for higher-confidence fallback

Tradeoff:

- local model is cheaper
- cloud model may be stronger but slower or more expensive

### Primary specialist to secondary specialist

Use when:

- two models can perform the same role at different cost or quality levels

Tradeoff:

- fallback may have lower quality or different formatting

### Specialist to orchestrator

Use when:

- the orchestrator can do the task less efficiently but still safely

Tradeoff:

- higher orchestrator load
- possible cost or latency increase

## Fallback trigger examples

Trigger fallback when:

- the primary call errors
- the response does not meet minimum quality
- the budget threshold is exceeded
- the required capability is unavailable

Do not fallback endlessly.

Define a stop point and escalate when needed.

## Response labeling

Record which model produced the result.

This matters because:

- fallback outputs may have different confidence profiles
- later reviews need to know which path was used

## Success criteria

Fallbacks are working when:

- a primary failure does not automatically become a workflow failure
- the operator can tell which path produced the final result
- the quality and cost tradeoffs are explicit
