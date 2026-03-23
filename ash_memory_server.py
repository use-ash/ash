#!/opt/homebrew/bin/python3
"""ASH Memory MCP Server — Phase 3

Provides safe persistent memory for AI agents. Phase 3 adds a Memory Policy
Engine on top of Phase 2's injection scanner: every write is classified by
kind (fact, preference, operational, procedure) and assigned a status
(active, pending_review, quarantined). Suspicious content never enters the
model context — read_memory() returns only active memories by default.

Threat model:
  1. Overt injection  — "ignore previous instructions" (Phase 2 blocker)
  2. Operational poisoning — legitimate-looking text that changes tool behavior
     (Phase 3 policy engine catches this)
  3. Description-field bypass — injection in the description, not the value
     (Phase 3 scans all fields)
  4. Gradual drift — incremental rewrites that shift a fact into a policy
     (Phase 3 detects kind changes on update)
  5. Load-path amplification — flagged content reaching model context even
     after warnings (Phase 3: inactive values withheld by default)

Seven tools:
  write_memory    — classify and store; returns STORED, PENDING_REVIEW,
                    QUARANTINED, or BLOCKED
  read_memory     — returns only active memories by default; inactive content
                    is withheld until explicitly reviewed and approved
  list_memories   — enumerate keys + metadata (defaults to active only)
  delete_memory   — remove by key, logged
  review_memory   — inspect full record including raw value (for human review)
  approve_memory  — move pending_review / quarantined → active
  reject_memory   — move pending_review / quarantined → rejected

Three resources:
  ash://memory-store    — metadata for all non-rejected memories
  ash://memory-pending  — pending_review and quarantined queue
  ash://memory-audit    — last 50 memory operations this session

Run standalone:
  python3 ash_memory_server.py

Install:
  ash_mem = FastMCP.from_file("ash_memory_server.py")
  client  = anthropic.Anthropic(mcp_servers=[ash_safety, ash_mem])
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone
from fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------
mcp = FastMCP("ash-memory")

# ---------------------------------------------------------------------------
# In-memory store
# { key: MemoryRecord-as-dict }
# ---------------------------------------------------------------------------
_store: dict[str, dict] = {}
_audit: list[dict]      = []

MAX_MEMORIES    = 500
MAX_VALUE_BYTES = 4096
MAX_KEY_LEN     = 128

# Memory kinds
KIND_FACT           = "fact"
KIND_PRESENTATION   = "presentation_preference"
KIND_OPERATIONAL    = "operational_preference"
KIND_PROCEDURE      = "procedure"
KIND_UNKNOWN        = "unknown"

# Memory statuses
STATUS_ACTIVE         = "active"
STATUS_PENDING_REVIEW = "pending_review"
STATUS_QUARANTINED    = "quarantined"
STATUS_REJECTED       = "rejected"

# Trust levels (caller may pass a hint; server never trusts without verification)
TRUST_USER_DIRECT       = "user_direct"
TRUST_TOOL_RESULT       = "tool_result"
TRUST_EXTERNAL_DOCUMENT = "external_document"
TRUST_UNKNOWN           = "unknown"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log(op: str, key: str, result: str, detail: str = "") -> None:
    entry = {"ts": _now(), "op": op, "key": key, "result": result}
    if detail:
        entry["detail"] = detail
    _audit.append(entry)
    if len(_audit) > 50:
        _audit.pop(0)


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------
_ZERO_WIDTH = re.compile(r"[\u200b\u200c\u200d\u200e\u200f\ufeff\u2028\u2029]")
_WHITESPACE  = re.compile(r"\s+")


def _normalize(text: str) -> str:
    """NFKC normalize, strip zero-width chars, collapse whitespace."""
    text = unicodedata.normalize("NFKC", text)
    text = _ZERO_WIDTH.sub("", text)
    text = _WHITESPACE.sub(" ", text).strip()
    return text


# ---------------------------------------------------------------------------
# Phase 2 injection scanner (runs on normalized combined field text)
# ---------------------------------------------------------------------------
INJECTION_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("system override",      re.compile(r"(?i)\b(ignore|forget|disregard)\s+(previous|prior|above|all)\b")),
    ("instruction injection",re.compile(r"(?i)\b(new\s+instructions?|actual\s+(goal|task)|real\s+objective)\b")),
    ("system tag",           re.compile(r"(?i)(<\s*system\s*>|\[SYSTEM\]|<\s*/?inst\s*>|\[\s*INST\s*\])")),
    ("override marker",      re.compile(r"(?i)\b(override|bypass|unlock|jailbreak)\b.*\b(safety|filter|guard|restriction)\b")),
    ("deferred trigger",     re.compile(r"(?i)\b(when(ever)?\s+you\s+(see|receive|get)|before\s+respond|always\s+respond\s+with)\b")),
    ("role reassignment",    re.compile(r"(?i)\byou\s+are\s+(now|actually|really)\s+(a|an)\b")),
    ("base64 payload",       re.compile(r"(?:[A-Za-z0-9+/]{40,}={0,2})")),
    ("unicode escape block", re.compile(r"(\\u[0-9a-fA-F]{4}){4,}")),
]


def _phase2_scan(combined: str) -> list[str]:
    """Return list of matched injection pattern names, empty if clean."""
    return [name for name, pat in INJECTION_PATTERNS if pat.search(combined)]


# ---------------------------------------------------------------------------
# Phase 3 behavioral classifier
# ---------------------------------------------------------------------------

# Feature word sets (lowercase match on normalized shadow)
_TRIGGER_TERMS = re.compile(
    r"\b(if|when(ever)?|before|after|unless|once|upon|as\s+soon\s+as)\b"
)
_MODAL_TERMS = re.compile(
    r"\b(always|never|must|should|shall|need\s+to|have\s+to|avoid|make\s+sure|ensure)\b"
)
_TOOL_ACTION_TERMS = re.compile(
    r"\b(run|execute|call|invoke|command|shell|bash|write|save|store|log|send|"
    r"reply|ask|fetch|request|browse|upload|download|delete|remove|forward|"
    r"email|post|notify|read|open|close|connect|install)\b"
)
_SENSITIVE_SINK_TERMS = re.compile(
    r"(?i)(/tmp|/var/|/etc/|password|passwd|token|api[_\s]?key|credential|"
    r"secret|ssh|\.env|stdout|stderr|clipboard|exfil|webhook|private[_\s]?key|"
    r"access[_\s]?key|auth[_\s]?token|bearer)"
)
_PRESENTATION_TERMS = re.compile(
    r"\b(concise|detailed|verbose|brief|bullets?|bullet\s*points?|prose|"
    r"tone|format|markdown|code\s*block|step[- ]by[- ]step|numbered|"
    r"header|heading|table|summary|example)\b"
)
_AGENT_FRAMING = re.compile(
    r"\b(you\b|assistant|agent|when\s+respond|when\s+running|when\s+you\b)\b"
)


def _classify(combined_lower: str) -> tuple[str, int, list[str]]:
    """
    Classify combined (normalized, lowercased) field text.

    Returns (kind, risk_score, reasons).
    kind: one of KIND_* constants
    risk_score: 0–20 (higher = riskier)
    """
    reasons: list[str] = []
    score = 0

    has_trigger    = bool(_TRIGGER_TERMS.search(combined_lower))
    has_modal      = bool(_MODAL_TERMS.search(combined_lower))
    has_tool       = bool(_TOOL_ACTION_TERMS.search(combined_lower))
    has_sink       = bool(_SENSITIVE_SINK_TERMS.search(combined_lower))
    has_present    = bool(_PRESENTATION_TERMS.search(combined_lower))
    has_agent_ref  = bool(_AGENT_FRAMING.search(combined_lower))

    if has_trigger:
        score += 2
        reasons.append("trigger phrase")
    if has_modal:
        score += 2
        reasons.append("behavioral modal")
    if has_tool:
        score += 3
        reasons.append("tool action")
    if has_sink:
        score += 4
        reasons.append("sensitive sink")
    if has_agent_ref:
        score += 1
        reasons.append("agent framing")
    if has_present and not has_tool and not has_sink:
        score = max(0, score - 1)  # style-only memory is lower risk

    # Classification
    if has_sink and (has_trigger or has_tool):
        # Operational + sensitive: treat as procedure (highest risk)
        kind = KIND_PROCEDURE
    elif has_tool or (has_modal and has_agent_ref):
        kind = KIND_OPERATIONAL
    elif has_modal and not has_tool and not has_sink:
        # "always use dark mode" — borderline; still operational-ish
        kind = KIND_OPERATIONAL
    elif has_present and not has_tool and not has_sink and not has_modal:
        kind = KIND_PRESENTATION
    elif score == 0:
        kind = KIND_FACT
    else:
        kind = KIND_UNKNOWN

    return kind, score, reasons


def _policy(kind: str, score: int, prev_kind: str | None) -> str:
    """
    Map kind + score + kind-change to a memory status.

    Returns one of STATUS_* constants.
    """
    # Kind escalation: safe → operational means re-review even if low score
    kind_escalated = (
        prev_kind in (KIND_FACT, KIND_PRESENTATION)
        and kind in (KIND_OPERATIONAL, KIND_PROCEDURE, KIND_UNKNOWN)
    )

    if kind == KIND_PROCEDURE and score >= 8:
        return STATUS_QUARANTINED
    if kind in (KIND_OPERATIONAL, KIND_PROCEDURE):
        return STATUS_PENDING_REVIEW
    if kind == KIND_UNKNOWN and score >= 4:
        return STATUS_PENDING_REVIEW
    if kind_escalated:
        return STATUS_PENDING_REVIEW
    # fact / presentation_preference with low risk
    return STATUS_ACTIVE


# ---------------------------------------------------------------------------
# Tool 1: write_memory
# ---------------------------------------------------------------------------
@mcp.tool()
def write_memory(key: str, value: str, description: str = "",
                 trust: str = "unknown") -> str:
    """Store a persistent memory entry. Scanned and classified before storing.

    Facts and style preferences become active immediately. Operational
    preferences (anything that changes how tools are used) and procedures
    require explicit approval via approve_memory() before they can be read.

    Args:
        key:         Unique identifier (e.g. "user_name", "project/context")
        value:       The content to remember
        description: Optional human-readable label
        trust:       Hint about source: "user_direct", "tool_result",
                     "external_document", or "unknown" (default)

    Returns STORED, PENDING_REVIEW, QUARANTINED, or BLOCKED.
    """
    # Key validation
    if len(key) > MAX_KEY_LEN:
        return f"BLOCKED — key too long ({len(key)} chars, max {MAX_KEY_LEN})"
    if not re.match(r"^[a-zA-Z0-9_\-./]+$", key):
        return "BLOCKED — key contains invalid characters (use alphanumeric, _, -, ., /)"

    # Value size limit
    if len(value.encode()) > MAX_VALUE_BYTES:
        return f"BLOCKED — value too large ({len(value.encode())} bytes, max {MAX_VALUE_BYTES})"

    # Store size limit (updates to existing keys are always allowed)
    if key not in _store and len(_store) >= MAX_MEMORIES:
        return f"BLOCKED — memory store full ({MAX_MEMORIES} entries). Delete unused memories first."

    # Normalize all fields together for scanning
    combined_raw  = f"{key}\n{description}\n{value}"
    combined_norm = _normalize(combined_raw)
    combined_low  = combined_norm.lower()

    # Phase 2: injection pattern scan
    injection_hits = _phase2_scan(combined_norm)
    if injection_hits:
        msg = (
            f"BLOCKED — memory poisoning detected\n"
            f"Patterns matched: {', '.join(injection_hits)}\n\n"
            f"Memory content looks like an injected instruction.\n"
            f"Store facts, context, and preferences — not behavioral rules.\n"
            f"If this is a legitimate note, rephrase it as a factual statement."
        )
        _log("write", key, "BLOCKED", f"injection: {injection_hits}")
        return msg

    # Phase 3: behavioral classification
    prev      = _store.get(key)
    prev_kind = prev.get("kind") if prev else None
    kind, score, reasons = _classify(combined_low)
    status = _policy(kind, score, prev_kind)

    # Normalize trust input
    valid_trust = {TRUST_USER_DIRECT, TRUST_TOOL_RESULT,
                   TRUST_EXTERNAL_DOCUMENT, TRUST_UNKNOWN}
    trust = trust if trust in valid_trust else TRUST_UNKNOWN

    # Escalate risk for external documents regardless of kind
    if trust == TRUST_EXTERNAL_DOCUMENT and status == STATUS_ACTIVE:
        status = STATUS_PENDING_REVIEW
        reasons.append("external document source")

    now = _now()
    _store[key] = {
        "value":       value,
        "description": description,
        "kind":        kind,
        "status":      status,
        "trust":       trust,
        "risk_score":  score,
        "reasons":     reasons,
        "created_at":  prev["created_at"] if prev else now,
        "updated_at":  now,
        "write_count": (prev["write_count"] + 1) if prev else 1,
        "hash":        hashlib.sha256(value.encode()).hexdigest()[:16],
        "prev_hash":   prev["hash"] if prev else "",
        "prev_kind":   prev_kind or "",
    }

    action = "updated" if prev else "created"
    h      = _store[key]["hash"]

    if status == STATUS_ACTIVE:
        _log("write", key, "STORED", f"kind:{kind} score:{score}")
        return f"STORED — key: {key} ({action}, kind: {kind}, hash: {h})"

    if status == STATUS_PENDING_REVIEW:
        _log("write", key, "PENDING_REVIEW", f"kind:{kind} score:{score} reasons:{reasons}")
        return (
            f"PENDING_REVIEW — key: {key} ({action})\n"
            f"Kind: {kind} | Risk score: {score} | Reasons: {', '.join(reasons)}\n\n"
            f"This memory changes agent behavior and requires approval before it\n"
            f"will be returned by read_memory(). Call approve_memory('{key}') to\n"
            f"activate it, or reject_memory('{key}') to discard."
        )

    # QUARANTINED
    _log("write", key, "QUARANTINED", f"kind:{kind} score:{score} reasons:{reasons}")
    return (
        f"QUARANTINED — key: {key} ({action})\n"
        f"Kind: {kind} | Risk score: {score} | Reasons: {', '.join(reasons)}\n\n"
        f"This memory has high-risk operational content and has been quarantined.\n"
        f"It will NOT be returned by read_memory(). Review with review_memory('{key}')\n"
        f"before deciding to approve or reject."
    )


# ---------------------------------------------------------------------------
# Tool 2: read_memory
# ---------------------------------------------------------------------------
@mcp.tool()
def read_memory(key: str) -> str:
    """Retrieve an active memory entry by key.

    Only returns memories with status 'active'. Pending or quarantined
    memories are withheld — use review_memory() to inspect them and
    approve_memory() / reject_memory() to act on them.

    Args:
        key: The memory key to retrieve
    """
    if key not in _store:
        _log("read", key, "NOT_FOUND")
        return f"NOT_FOUND — no memory stored for key: {key}"

    entry = _store[key]
    status = entry["status"]

    if status == STATUS_REJECTED:
        _log("read", key, "REJECTED")
        return f"REJECTED — key: {key} has been rejected and is not loadable."

    if status == STATUS_PENDING_REVIEW:
        _log("read", key, "WITHHELD_PENDING")
        return (
            f"WITHHELD — key: {key} is pending review (kind: {entry['kind']}, "
            f"risk: {entry['risk_score']}).\n"
            f"Reasons: {', '.join(entry['reasons']) or 'none'}\n"
            f"Call review_memory('{key}') to inspect content.\n"
            f"Call approve_memory('{key}') to activate, or reject_memory('{key}') to discard."
        )

    if status == STATUS_QUARANTINED:
        _log("read", key, "WITHHELD_QUARANTINED")
        return (
            f"WITHHELD — key: {key} is quarantined (kind: {entry['kind']}, "
            f"risk: {entry['risk_score']}).\n"
            f"Reasons: {', '.join(entry['reasons']) or 'none'}\n"
            f"High-risk operational content is held until explicitly approved.\n"
            f"Call review_memory('{key}') to inspect. Approve or reject before use."
        )

    # Active — return value
    _log("read", key, "READ")
    meta = (
        f"[key: {key} | kind: {entry['kind']} | "
        f"updated: {entry['updated_at'][:10]} | writes: {entry['write_count']}]"
    )
    return f"{meta}\n{entry['value']}"


# ---------------------------------------------------------------------------
# Tool 3: list_memories
# ---------------------------------------------------------------------------
@mcp.tool()
def list_memories(prefix: str = "", status: str = "active", kind: str = "") -> str:
    """List stored memory keys and metadata (not values).

    Defaults to active memories only. Use status='all' to see everything
    including pending and quarantined entries.

    Args:
        prefix: Key prefix filter (e.g. "user/" shows user/* keys only)
        status: Filter by status: "active", "pending_review", "quarantined",
                "rejected", or "all". Default: "active"
        kind:   Filter by kind: "fact", "presentation_preference",
                "operational_preference", "procedure". Default: all kinds
    """
    if not _store:
        _log("list", prefix or "*", "EMPTY")
        return "Memory store is empty."

    matches = {
        k: v for k, v in _store.items()
        if k.startswith(prefix)
        and (status == "all" or v["status"] == status)
        and (not kind or v["kind"] == kind)
    }

    if not matches:
        filters = f"prefix={prefix!r} status={status!r} kind={kind!r}"
        _log("list", prefix or "*", "NO_MATCH")
        return f"No memories found matching filters: {filters}"

    n = len(matches)
    lines = [f"Memory store — {n} entr{'y' if n == 1 else 'ies'} [{status}]:\n"]
    for k, v in sorted(matches.items()):
        desc   = f" — {v['description']}" if v["description"] else ""
        reason = f"  reasons: {', '.join(v['reasons'])}" if v.get("reasons") else ""
        lines.append(
            f"  {k}{desc}\n"
            f"    kind: {v['kind']} | status: {v['status']} | "
            f"risk: {v['risk_score']} | writes: {v['write_count']}"
            + (f"\n   {reason}" if reason else "")
        )

    _log("list", prefix or "*", f"OK ({n} entries, status={status})")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 4: delete_memory
# ---------------------------------------------------------------------------
@mcp.tool()
def delete_memory(key: str) -> str:
    """Delete a stored memory entry by key (any status).

    Args:
        key: The memory key to delete
    """
    if key not in _store:
        _log("delete", key, "NOT_FOUND")
        return f"NOT_FOUND — no memory stored for key: {key}"

    status = _store[key]["status"]
    del _store[key]
    _log("delete", key, "DELETED", f"was:{status}")
    return f"DELETED — key: {key} (was: {status})"


# ---------------------------------------------------------------------------
# Tool 5: review_memory
# ---------------------------------------------------------------------------
@mcp.tool()
def review_memory(key: str) -> str:
    """Inspect the full record for a memory, including its raw value.

    Use this to review pending or quarantined memories before approving or
    rejecting them. Returns all metadata including risk classification.

    Args:
        key: The memory key to review
    """
    if key not in _store:
        _log("review", key, "NOT_FOUND")
        return f"NOT_FOUND — no memory stored for key: {key}"

    entry = _store[key]
    _log("review", key, "REVIEWED", f"status:{entry['status']}")

    return (
        f"REVIEW — key: {key}\n"
        f"Status:      {entry['status']}\n"
        f"Kind:        {entry['kind']}\n"
        f"Risk score:  {entry['risk_score']}\n"
        f"Reasons:     {', '.join(entry['reasons']) or 'none'}\n"
        f"Trust:       {entry['trust']}\n"
        f"Writes:      {entry['write_count']}\n"
        f"Created:     {entry['created_at'][:19]}\n"
        f"Updated:     {entry['updated_at'][:19]}\n"
        f"Hash:        {entry['hash']}\n"
        f"Description: {entry['description'] or '(none)'}\n"
        f"\nValue:\n{entry['value']}\n"
        f"\nTo activate: approve_memory('{key}')\n"
        f"To discard:  reject_memory('{key}')"
    )


# ---------------------------------------------------------------------------
# Tool 6: approve_memory
# ---------------------------------------------------------------------------
@mcp.tool()
def approve_memory(key: str) -> str:
    """Approve a pending or quarantined memory, making it active.

    Only call this after reviewing the memory content with review_memory()
    and confirming it is safe to load into future agent sessions.

    Args:
        key: The memory key to approve
    """
    if key not in _store:
        _log("approve", key, "NOT_FOUND")
        return f"NOT_FOUND — no memory stored for key: {key}"

    entry = _store[key]
    prev_status = entry["status"]

    if prev_status == STATUS_ACTIVE:
        return f"Already active — key: {key} is already in active status."

    if prev_status == STATUS_REJECTED:
        return f"REJECTED — key: {key} has been rejected and cannot be approved. Delete and re-write if needed."

    entry["status"]     = STATUS_ACTIVE
    entry["updated_at"] = _now()
    _log("approve", key, "APPROVED", f"was:{prev_status}")

    return (
        f"APPROVED — key: {key}\n"
        f"Status changed: {prev_status} → active\n"
        f"Memory will now be returned by read_memory()."
    )


# ---------------------------------------------------------------------------
# Tool 7: reject_memory
# ---------------------------------------------------------------------------
@mcp.tool()
def reject_memory(key: str, reason: str = "") -> str:
    """Reject a pending or quarantined memory, marking it as not loadable.

    Rejected memories remain in the store for audit purposes but will never
    be returned by read_memory(). Use delete_memory() to remove them entirely.

    Args:
        key:    The memory key to reject
        reason: Optional reason for the rejection (logged for audit)
    """
    if key not in _store:
        _log("reject", key, "NOT_FOUND")
        return f"NOT_FOUND — no memory stored for key: {key}"

    entry = _store[key]
    prev_status = entry["status"]

    if prev_status == STATUS_REJECTED:
        return f"Already rejected — key: {key}"

    entry["status"]      = STATUS_REJECTED
    entry["updated_at"]  = _now()
    detail = f"was:{prev_status}"
    if reason:
        detail += f" reason:{reason}"
    _log("reject", key, "REJECTED", detail)

    return (
        f"REJECTED — key: {key}\n"
        f"Status changed: {prev_status} → rejected\n"
        f"Memory will not be returned by read_memory().\n"
        f"Call delete_memory('{key}') to remove it entirely."
        + (f"\nReason: {reason}" if reason else "")
    )


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------
@mcp.resource("ash://memory-store")
def memory_store_resource() -> str:
    """All non-rejected memory keys with metadata. Values omitted."""
    visible = {k: v for k, v in _store.items() if v["status"] != STATUS_REJECTED}
    entries = {
        k: {
            "description": v["description"],
            "kind":        v["kind"],
            "status":      v["status"],
            "trust":       v["trust"],
            "risk_score":  v["risk_score"],
            "reasons":     v["reasons"],
            "created_at":  v["created_at"],
            "updated_at":  v["updated_at"],
            "write_count": v["write_count"],
            "hash":        v["hash"],
        }
        for k, v in visible.items()
    }
    return json.dumps({"count": len(visible), "entries": entries}, indent=2)


@mcp.resource("ash://memory-pending")
def memory_pending_resource() -> str:
    """All pending_review and quarantined memories — the review queue."""
    queue = {
        k: v for k, v in _store.items()
        if v["status"] in (STATUS_PENDING_REVIEW, STATUS_QUARANTINED)
    }
    entries = {
        k: {
            "description": v["description"],
            "kind":        v["kind"],
            "status":      v["status"],
            "risk_score":  v["risk_score"],
            "reasons":     v["reasons"],
            "updated_at":  v["updated_at"],
        }
        for k, v in queue.items()
    }
    return json.dumps({"count": len(queue), "entries": entries}, indent=2)


@mcp.resource("ash://memory-audit")
def memory_audit_resource() -> str:
    """Last 50 memory operations this session."""
    return json.dumps({"count": len(_audit), "entries": _audit}, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8001))
    mcp.settings.port = port
    mcp.run(transport="sse")
