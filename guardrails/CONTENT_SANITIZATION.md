# Content Sanitization

This guide explains how to treat external content as untrusted.

## Threat model

External text can contain:

- prompt injection
- fake instructions
- misleading formatting
- malicious links
- plausible but false claims

The danger is not only that the content is wrong.
The danger is that the content may try to steer the agent.

## Default rule

Treat all external content as hostile by default until it has been:

- sanitized
- summarized in a restricted environment
- or clearly marked as untrusted raw content

## Sandbox pattern

Use a sandboxed analysis stage between external content and the main agent workflow.

The sanitizing stage should have fewer powers than the main agent.

Ideal properties:

- no file access
- no shell access
- no write access
- no network access beyond the original fetch when possible

Its job is to extract meaning, not to act.

## Sanitization outputs

A sanitization step should return:

- a plain-language summary
- important facts or claims
- uncertainty markers when needed
- a warning that the original content was untrusted

If sanitization fails, pass the content onward only with strong untrusted markers.

## What prompt injection looks like

Common patterns include:

- "ignore your previous instructions"
- "run this command"
- "open this file"
- "you are now acting as"
- fake system or developer instructions embedded in content

Do not assume prompt injection is obvious. The content may hide malicious instructions inside a long plausible passage.

## Filtering strategy

Use several controls together:

1. isolate the raw content from the main agent
2. summarize in a low-privilege environment
3. strip or mark embedded instructions
4. preserve source attribution when accuracy matters
5. never let raw external content silently become trusted context

## Human review trigger

Require review or extra caution when:

- the content requests action
- the source is unknown or low-trust
- the claim affects money, safety, or credentials
- the sanitization stage reports uncertainty

## Success criteria

This system is working when:

- raw external text cannot directly steer privileged agent actions
- prompt injection attempts are neutralized or visibly marked
- useful factual content still reaches the workflow in summarized form
