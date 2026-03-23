# Pitfalls

This document lists common failure modes in multi-model coordination.

## 1. Model disagreement without evidence

Problem:

Two models disagree and both sound confident.

Risk:

The orchestrator chooses based on tone instead of proof.

Prevention:

- require citations, file references, logs, or other inspectable evidence
- prefer the answer that survives verification

## 2. Context loss during handoff

Problem:

The receiving model does not know what matters because the dispatch was too thin or too vague.

Risk:

The task restarts from zero or returns the wrong output.

Prevention:

- include exact scope
- include expected deliverable
- include stop condition

## 3. Budget burn from exploration

Problem:

The delegated worker spends time and tokens exploring unrelated context before addressing the task.

Risk:

Slow, expensive, or incomplete work.

Prevention:

- bound the task tightly
- pass only the needed files or sources
- define exploration limits

## 4. Role drift

Problem:

The specialist starts making orchestration decisions.

Risk:

The workflow becomes harder to reason about and harder to control.

Prevention:

- keep the orchestrator responsible for final judgment
- keep specialist tasks bounded

## 5. Missing fallback

Problem:

The preferred model fails and the workflow stalls.

Risk:

Routine outages become full stoppages.

Prevention:

- define fallback chains in advance
- record stop conditions and escalation paths

## 6. Over-delegation

Problem:

The orchestrator delegates tasks it should handle itself.

Risk:

More handoffs, more latency, and more context loss than necessary.

Prevention:

- keep urgent workflow-shaping decisions local to the orchestrator
- delegate bounded specialist work, not everything

## Review checklist

Ask these questions regularly:

1. Are routing choices still justified by quality, cost, and latency?
2. Are specialists getting enough context, but not too much?
3. Are fallback paths clear?
4. Are model disagreements resolved by evidence?
5. Are handoffs producing useful outputs without rework?
