#!/usr/bin/env python3
"""nodes.py — Programmatic interface to the NODES.md node model (v1.0, S340).

Operationalizes memory/NODES.md so tools can import node types/properties
rather than hardcoding strings. Fixes SIG-1 gap: 0/207 tools used NODES.md
despite spec existing 69 sessions (L-814).

Usage:
    from tools.nodes import VALID_NODE_TYPES, NODE_HUMAN, NODE_AI_SESSION

    if source not in VALID_NODE_TYPES:
        raise ValueError(f"Unknown node type: {source}")
"""

from __future__ import annotations

# Node type constants — must match memory/NODES.md "Node Instances" section
NODE_HUMAN = "human"
NODE_AI_SESSION = "ai-session"
NODE_CHILD_SWARM = "child-swarm"
NODE_EXTERNAL = "external"
NODE_BROADCAST = "broadcast"  # virtual target: all nodes

VALID_NODE_TYPES: frozenset[str] = frozenset(
    {NODE_HUMAN, NODE_AI_SESSION, NODE_CHILD_SWARM, NODE_EXTERNAL}
)

# broadcast is a valid signal target but not a node type itself
VALID_SIGNAL_TARGETS: frozenset[str] = VALID_NODE_TYPES | {NODE_BROADCAST}

# Node capability sets — per memory/NODES.md
NODE_CAPABILITIES: dict[str, list[str]] = {
    NODE_HUMAN: [
        "session-initiate",
        "kill-switch",
        "directional-authority",
        "philosophical-reframe",
    ],
    NODE_AI_SESSION: [
        "read-state",
        "decide",
        "act",
        "compress",
        "signal",
        "spawn-child",
        "expert-dispatch",
    ],
    NODE_CHILD_SWARM: [
        "read-state",
        "decide",
        "act",
        "compress",
        "signal",
        "challenge-beliefs",
    ],
    NODE_EXTERNAL: [
        "domain-knowledge",
        "challenge-beliefs",
        "correction",
    ],
}

# Node persistence classes — per memory/NODES.md
NODE_PERSISTENCE: dict[str, str] = {
    NODE_HUMAN: "permanent",
    NODE_AI_SESSION: "session",
    NODE_CHILD_SWARM: "spawned",
    NODE_EXTERNAL: "episodic",
}

# Node bandwidth classes — per memory/NODES.md
NODE_BANDWIDTH: dict[str, str] = {
    NODE_HUMAN: "low",
    NODE_AI_SESSION: "high",
    NODE_CHILD_SWARM: "medium",
    NODE_EXTERNAL: "very-low",
}


def validate_node(node_id: str, allow_broadcast: bool = False) -> bool:
    """Return True if node_id is a known node type or instance.

    Args:
        node_id: Node identifier to validate (e.g. "human", "ai-session").
        allow_broadcast: If True, also accept "broadcast" as a valid target.
    """
    valid = VALID_SIGNAL_TARGETS if allow_broadcast else VALID_NODE_TYPES
    # Also allow session-scoped IDs like "S409-claude" or "child-v1"
    if node_id in valid:
        return True
    if node_id.startswith(("S", "child-", "ext-")):
        return True
    return False


def node_summary() -> str:
    """Return one-line summary of the node model for display."""
    types = ", ".join(sorted(VALID_NODE_TYPES))
    return f"Node model v1.0: {len(VALID_NODE_TYPES)} types ({types})"


if __name__ == "__main__":
    print(node_summary())
    for ntype, caps in NODE_CAPABILITIES.items():
        print(f"  {ntype}: {', '.join(caps)}")
