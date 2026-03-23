# Coordination Framework

This document explains why one model should not do everything and how to route work by role.

For conceptual background, see:

- <https://use-ash.github.io/ash/model-coordination/>

## Why one model is not enough

Different tasks benefit from different strengths.

Examples:

- coding tasks need strong file and patch reasoning
- live research needs fresh external information
- cheap maintenance triage benefits from low-cost fast responses
- orchestration needs judgment across the whole workflow

If one model handles every task, the system pays for mismatched work with cost, latency, or lower quality.

## Roles, not rankings

Model coordination should be role-based, not prestige-based.

The question is not "which model is best overall?"
The question is "which model is the best fit for this task right now?"

Typical roles:

- orchestrator
- coding specialist
- research specialist
- low-cost triage model

Your environment may use different names or providers. The role concept remains the same.

## Orchestrator role

The orchestrator should:

- read the current workspace context
- choose the right worker for the task
- shape delegated tasks
- judge returned results
- merge results back into the main workflow

Do not let delegation quietly turn the worker into a second orchestrator.

## Specialist role

A specialist should receive:

- a bounded task
- the exact context it needs
- a clear output requirement
- a stop condition

This keeps delegation efficient and reduces context loss.

## Routing principles

Use these principles:

- route by fit
- keep prompts bounded
- keep the orchestrator responsible for the final judgment
- use direct evidence when comparing outputs

## Success criteria

Coordination is working when:

- tasks go to the model best suited for them
- specialists do not waste budget exploring unrelated context
- the orchestrator can explain routing decisions clearly
- model handoffs preserve enough context to continue work cleanly
