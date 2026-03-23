# Audit Trail Guide

This guide describes how to build an audit trail for agent actions.

## Purpose

The audit trail is the forensic record of what the agent did.

It should answer:

- who acted
- when they acted
- what tool was used
- what target was touched
- whether the action was allowed, warned, or blocked

## Where to log

Log at the action boundary, as close as possible to actual tool execution.

This is more reliable than asking the agent to summarize its own actions after the fact.

## Recommended storage format

Use append-only line-oriented records.

JSON Lines is a strong fit because:

- each event is one record
- new events can be appended without rewriting the file
- logs are easy to parse later

## Entry schema

Each log entry should include at least:

| Field | Type | Meaning |
|---|---|---|
| `timestamp` | string | Absolute timestamp |
| `session_id` | string | Session identifier |
| `actor` | string | Model, agent, or process that acted |
| `tool_name` | string | Tool or action surface |
| `target` | string or null | File path, service, or resource touched |
| `status` | string | `allowed`, `warning`, `blocked`, or `error` |
| `summary` | string | Short description of the action |
| `channel` | string or null | Where the action originated |

Recommended optional fields:

- `thread_id`
- `command_snippet`
- `policy_reason`
- `duration_ms`
- `request_id`

Example entry:

```json
{
  "timestamp": "2026-03-21T19:22:00Z",
  "session_id": "session-2026-03-21-001",
  "actor": "orchestrator",
  "tool_name": "write_file",
  "target": "docs/release-plan.md",
  "status": "allowed",
  "summary": "Updated release plan documentation.",
  "channel": "webchat",
  "thread_id": "thread-release-plan"
}
```

## Rotation and retention

Plan for logs to grow.

Define:

- max file size or time-based rotation
- retention window
- archive location
- cleanup rule

Do not wait until the log file becomes too large to inspect.

## Error handling

Keep a separate error path for audit system failures.

If the logging infrastructure itself breaks, record that separately so debugging the safety layer does not pollute the normal log stream.

## Fail-open guidance

If the audit logger fails, the agent may still need to continue working.

Recommended rule:

- block only when a safety policy explicitly requires blocking
- otherwise record the logger failure and allow the underlying action to proceed

This prevents the logging system from becoming a single point of failure.

## Review use cases

The audit trail should support:

- incident review
- model behavior analysis
- compliance or operator review
- debugging unexplained changes
- measuring how often blocks or warnings occur

## Quality checks

The audit trail is healthy when:

- every important action creates a record
- blocked actions are visibly different from allowed actions
- the logs are readable by both humans and machines
- retention is defined before scale becomes a problem
