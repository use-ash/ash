# Handoff Patterns

This document explains how to hand off work between models, channels, and sessions without losing context.

## The handoff rule

Before any handoff, update the thread ledger.

Do not rely on the receiving model or future session to reconstruct the missing context from chat history.

Every handoff should preserve:

- current summary
- next step
- blockers
- relevant constraints

## Model-to-model handoff

Use this when one model delegates work to another.

Before dispatch:

1. update the thread summary
2. define the exact delegated subtask
3. record what output is expected back

After return:

1. merge the result into the parent thread
2. update the summary
3. set the next step

The delegated worker should not become the new orchestrator by accident. Keep the handoff bounded.

## Channel-to-channel handoff

Use this when work continues in a different communication channel.

Preserve:

- current thread ID
- summary
- user-visible next step
- channel history in `channels_seen`

Do not create a new thread just because the channel changed. The work is the same work unless the goal changed.

## Session-to-session handoff

Use this at the end of a session or before an expected interruption.

Before ending:

1. update every active thread touched in the session
2. record what just happened
3. make the next step explicit
4. move completed work to closed

This is the difference between continuity and guesswork.

## Parent and child task pattern

When a large thread produces smaller delegated tasks:

- keep the parent thread as the main record
- record child task outcomes inside the parent summary or linked metadata
- close child work promptly when it returns

Avoid turning every subtask into a permanent top-level thread unless it truly deserves independent tracking.

## Budget control pattern

Handoffs can waste budget when the receiving model explores blindly.

Prevent that by handing off:

- the exact question
- the exact files or sources that matter
- the expected deliverable
- the stop condition

The more bounded the handoff, the less context gets lost and the less budget gets wasted.

## Failure modes

### Missing next step

The receiving model knows what happened but not what to do next.

Fix:

- require `next_step` before handoff

### Summary too vague

The receiving model restarts exploration from zero.

Fix:

- write summary as decision-quality context, not a placeholder

### Duplicate threads after channel switch

The same work appears active in multiple places.

Fix:

- keep a stable thread ID across channels

### Oversized handoff

The handoff contains too much irrelevant detail and becomes expensive to load.

Fix:

- summarize what matters now
- link out to detail instead of copying everything
