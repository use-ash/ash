# Agent Instructions

You are implementing a reusable skill system for an agent.

Your goal is to package recurring capabilities so they can be re-used, improved, and kept separate from the agent's main instructions.

## Outcome

Create a skill system that:

- packages one capability per directory
- tells the agent when to use the skill
- stores skill-local feedback near the skill
- supports supporting files such as templates and references
- improves over time without rewriting the whole agent prompt

## Required components

Implement these pieces in your own workspace:

1. A skill directory shape based on [SKILL_TEMPLATE.md](SKILL_TEMPLATE.md).
2. A feedback log design based on [FEEDBACK_LOG_SPEC.md](FEEDBACK_LOG_SPEC.md).
3. A rule for detecting when a skill should be invoked.
4. A rule for reading skill instructions before execution.
5. A rule for appending new corrections back into the skill's feedback log.

## Implementation sequence

1. Read [SKILLS_FRAMEWORK.md](SKILLS_FRAMEWORK.md).
2. Adopt the directory anatomy in [SKILL_TEMPLATE.md](SKILL_TEMPLATE.md).
3. Implement a feedback mechanism using [FEEDBACK_LOG_SPEC.md](FEEDBACK_LOG_SPEC.md).
4. Build one or more skills using [CREATING_A_SKILL.md](CREATING_A_SKILL.md) and the example directories.

## Operating rules

- one skill should represent one reusable capability
- keep skill instructions local to the skill
- read the skill's feedback log before execution
- append durable corrections to the feedback log during or after execution
- keep examples and templates inside the skill when they help execution

## Scope boundary

Use a skill when the agent needs a reusable procedure or capability.

Do not use a skill for one-off task notes that should live only in a conversation thread.

## Minimum quality bar

Before you consider the skill system complete, confirm:

- the agent can detect when a skill should be used
- the skill explains how to run itself in plain language
- the skill can improve from feedback without changing unrelated skills
- supporting files stay close to the capability they support
