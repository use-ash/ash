# Thread Schema

This document defines a recommended schema for `conversation_state.json` or an equivalent persistent thread ledger.

The schema is intentionally simple. It should be easy for both humans and agents to inspect and update.

## Top-level structure

Recommended top-level fields:

| Field | Type | Required | Meaning |
|---|---|---|---|
| `active_threads` | array | yes | Threads that still need action |
| `closed_threads` | array | yes | Threads that are complete, cancelled, or superseded |
| `global_context` | object | yes | Shared context relevant across threads |
| `session_metadata` | object | yes | Information about the last update or last session |

Minimal example:

```json
{
  "active_threads": [],
  "closed_threads": [],
  "global_context": {},
  "session_metadata": {}
}
```

## Active and closed thread entry schema

Each thread entry should include:

| Field | Type | Required | Meaning |
|---|---|---|---|
| `id` | string | yes | Stable thread identifier |
| `title` | string | yes | Short human-readable title |
| `status` | string | yes | `active`, `blocked`, `waiting`, `closed`, or another clear status |
| `summary` | string | yes | Concise summary of current state |
| `next_step` | string | yes | Concrete next action |
| `channels_seen` | array of strings | yes | Channels where this thread has been active |
| `models_seen` | array of strings | recommended | Models involved so far |
| `opened_at` | string | yes | Absolute timestamp |
| `last_activity` | string | yes | Absolute timestamp |
| `closed_at` | string or null | recommended | Absolute timestamp when closed |
| `tags` | array of strings | recommended | Search and routing hints |

Example thread:

```json
{
  "id": "thread-framework-memory",
  "title": "Design memory framework repository",
  "status": "active",
  "summary": "Core memory documents are drafted. Example notes still need review.",
  "next_step": "Verify the example files cover all four memory types.",
  "channels_seen": ["webchat"],
  "models_seen": ["orchestrator", "worker-model"],
  "opened_at": "2026-03-21T18:00:00Z",
  "last_activity": "2026-03-21T19:10:00Z",
  "closed_at": null,
  "tags": ["framework", "memory", "documentation"]
}
```

## `global_context`

Use `global_context` for information that applies across multiple threads in the current operating period.

Recommended fields:

| Field | Type | Meaning |
|---|---|---|
| `current_priorities` | array of strings | Broad priorities that shape active work |
| `known_blockers` | array of strings | Shared blockers affecting multiple threads |
| `important_dates` | array of strings | Absolute dates that matter soon |
| `shared_notes` | string | Short shared context summary |

Keep this compact. If it grows large, move durable information into memory.

## `session_metadata`

Use `session_metadata` to track recent session-level facts.

Recommended fields:

| Field | Type | Meaning |
|---|---|---|
| `last_session_id` | string | Last session identifier |
| `last_updated_by` | string | Model, agent, or process that wrote the file |
| `last_updated_at` | string | Absolute timestamp |
| `last_channel` | string | Last channel that updated the state |
| `last_session_summary` | string | Short summary of what happened in the last session |

## Schema rules

- use stable IDs
- use absolute timestamps
- keep summaries concise
- require `next_step` for active threads
- move completed work to `closed_threads`
- do not store secrets in the thread ledger

## Validation checks

Reject or repair the state file when:

- a thread is active but has no `next_step`
- timestamps are relative phrases instead of absolute values
- the same thread ID appears twice
- a closed thread remains in `active_threads`
- the summaries are so long that session startup becomes expensive
