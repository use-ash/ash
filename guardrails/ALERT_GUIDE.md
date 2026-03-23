# Alert Guide

This guide explains how to alert humans without creating alert fatigue.

## Purpose

Alerts exist to get human attention when the system needs it.

An alert that arrives too often stops being useful.

## Severity levels

Use clear severity levels.

Recommended levels:

- `info`: useful but not urgent
- `warning`: needs attention soon
- `critical`: immediate risk or active failure

Each alert should include its severity explicitly.

## What deserves a real-time alert

Strong candidates:

- protected action blocked
- critical background job failed
- secret exposure detected
- health check found a significant outage
- deployment or production control path changed

Weak candidates:

- every routine completion
- every low-impact warning
- noisy repeated failures of the same type

## Throttling

Apply cooldown windows to repeating alert types.

If the same event happens ten times in five minutes, the operator usually needs one alert, not ten.

Throttle by a stable key such as:

- event type
- resource
- first line of summary

## Aggregation

Not everything needs a real-time message.

Use aggregation for:

- routine summaries
- repeated low-severity warnings
- daily or hourly status rollups

Aggregation reduces noise and improves operator attention.

## Alert content

A good alert contains:

- severity
- what happened
- what resource or thread is affected
- what the operator should do next, if known

Keep it short enough to scan on a phone.

## Delivery redundancy

Choose at least one reliable operator-visible delivery path.

If alerts are critical, define a fallback path or escalation rule for when the primary alert channel fails.

## Feedback loop

Review alerts regularly and ask:

- which alerts mattered
- which alerts were ignored
- which alerts were repeated too often
- which important events did not alert at all

Adjust thresholds and aggregation based on observed behavior, not guesswork.

## Success criteria

Alerting is working when:

- important failures reach a human quickly
- repeated noise does not drown out important signals
- operators can tell what happened and what to do next from the alert itself
