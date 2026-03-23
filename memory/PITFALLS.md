# Pitfalls

This document lists the common failure modes in file-based memory systems and the rules that prevent them.

## 1. Stale memory

Problem:

A note was true when it was written, but the code, policy, or external system has changed since then.

Why it is dangerous:

The agent retrieves the note and acts with false confidence.

Prevention rules:

- verify retrieved memory against current source or state before acting
- add `updated_at` when possible
- review active notes on a regular schedule
- archive or rewrite notes that conflict with current reality

## 2. Duplicate memory

Problem:

The same topic exists in multiple notes.

Why it is dangerous:

One note gets updated. Another does not. Retrieval becomes inconsistent.

Prevention rules:

- one topic per file
- one canonical note per durable rule or fact
- update the canonical file instead of creating a new variant
- merge duplicates as soon as they are found

## 3. Memory bloat

Problem:

The index or note set grows without structure.

Why it is dangerous:

Session startup becomes slow. Retrieval quality drops. The agent misses the important note because too much low-value text exists.

Prevention rules:

- keep the index short
- move detail into topic files
- avoid storing raw transcripts
- archive obsolete notes
- add semantic retrieval when scale demands it

## 4. Over-trust

Problem:

The agent treats retrieved memory as proven truth.

Why it is dangerous:

Memory becomes a substitute for verification.

Prevention rules:

- treat memory as a lead, not a verdict
- check current code, state, or source of truth before acting
- prefer evidence that survives inspection

## 5. Time drift

Problem:

A note uses relative phrases such as "tomorrow" or "next week."

Why it is dangerous:

The meaning changes or disappears as time passes.

Prevention rules:

- use absolute dates such as `2026-03-21`
- rewrite old relative phrasing into durable language
- include date context whenever action depends on timing

## 6. Mixed-purpose notes

Problem:

A single note contains unrelated topics.

Why it is dangerous:

Retrieval becomes noisy and updates become risky.

Prevention rules:

- split unrelated topics into separate notes
- write note titles and descriptions for one topic only

## 7. Missing behavior change

Problem:

Feedback is stored, but future behavior does not change.

Why it is dangerous:

The system creates the appearance of learning without actual learning.

Prevention rules:

- load important feedback at session start
- load task-specific feedback when relevant
- write feedback in rule form with trigger and application steps

## Cleanup checklist

Run this check regularly:

1. Are any active notes contradicted by current code or policy?
2. Are any two notes covering the same topic?
3. Is the index still short enough to load every session?
4. Are old project notes still active when they should be archived?
5. Are feedback notes changing behavior in later sessions?

If the answer to any item is no, repair the memory store before adding more notes.
