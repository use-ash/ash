# use-ash/guardrails

Framework for agent safety, audit trails, and content protection.

This repository explains how to design guardrails around an autonomous agent so unsafe actions are logged, risky actions are blocked, external content is treated as untrusted, and operators receive useful alerts without being overwhelmed.

This repository does not contain code. It contains design patterns, schemas, and operating rules.

Start here:

1. Read [AGENT_INSTRUCTIONS.md](AGENT_INSTRUCTIONS.md).
2. Read [GUARDRAILS_FRAMEWORK.md](GUARDRAILS_FRAMEWORK.md).
3. Read [AUDIT_TRAIL_GUIDE.md](AUDIT_TRAIL_GUIDE.md).
4. Read [PROTECTED_FILES_GUIDE.md](PROTECTED_FILES_GUIDE.md).
5. Read [CONTENT_SANITIZATION.md](CONTENT_SANITIZATION.md).
6. Read [SECRET_MANAGEMENT.md](SECRET_MANAGEMENT.md).
7. Read [ALERT_GUIDE.md](ALERT_GUIDE.md).
8. Read [DEV_PIPELINE.md](DEV_PIPELINE.md).

Reference background:

- ASH wiki: <https://use-ash.github.io/ash/>
- Security and guardrails overview: <https://use-ash.github.io/ash/security-and-guardrails/>
- Dev pipeline overview: <https://use-ash.github.io/ash/dev-pipeline/>

Repository contents:

- `GUARDRAILS_FRAMEWORK.md`: the overall safety model
- `AUDIT_TRAIL_GUIDE.md`: action logging design
- `PROTECTED_FILES_GUIDE.md`: write protection model
- `CONTENT_SANITIZATION.md`: external content handling
- `SECRET_MANAGEMENT.md`: secret leakage prevention
- `ALERT_GUIDE.md`: alerting strategy
- `DEV_PIPELINE.md`: PLAN-BUILD-VERIFY-REVIEW-COMMIT-DEPLOY
