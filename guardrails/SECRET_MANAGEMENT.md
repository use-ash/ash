# Secret Management

This guide explains how to reduce credential leakage in agent workflows.

## The problem

Secrets leak through normal work.

Common paths:

- reading environment files
- printing tool output into transcripts
- committing credentials to version control
- copying logs that contain tokens

Once a secret reaches a transcript, log, or commit history, cleanup becomes harder.

## Layered defense

Do not rely on one layer.

Use at least three:

1. prevention before commit or storage
2. masking before output enters conversation context
3. cleanup for historical or archived records

## Layer 1: scan before commit

Scan staged changes or pending content for common secret patterns.

The scanner should look for:

- API keys
- bot tokens
- bearer tokens
- private key blocks
- workspace-specific credential formats

When a match appears, reject or pause the commit so the leak does not enter durable history.

## Layer 2: mask tool output

Before tool output is shown to the agent or stored in transcripts, scan it for secret patterns and replace matches with clear redaction markers.

Example marker:

```text
[REDACTED:API_KEY]
```

This preserves the shape of the event without exposing the value.

## Layer 3: scrub archives

Historical transcripts and logs may contain secrets that were captured before stronger protections existed.

Add a cleanup pass that scans archived material and redacts anything that slipped through earlier layers.

## Pattern management

Maintain a curated pattern list for the credential types your system uses.

Review the pattern list whenever:

- you add a new service
- a token format changes
- a false negative or false positive is discovered

## Logging rule

Never log the raw secret value in the secret scanner or masking system.

If you need evidence that a match occurred, log:

- pattern type
- redacted preview
- file or stream source
- line number or event ID

## Human workflow

When a secret is detected:

1. stop the unsafe storage path
2. report what type of secret was found
3. identify where it appeared
4. rotate the credential if exposure is possible
5. repair the workflow that allowed the leak

## Success criteria

This system is working when:

- obvious secrets do not enter commits
- tool output is masked before it becomes durable chat context
- historical leaks can be cleaned up
- the system can prove a secret event happened without printing the secret itself
