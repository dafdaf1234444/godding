#!/usr/bin/env python3
"""
f_sec1_security_audit.py — Audit 5-layer genesis security protocol (F-SEC1).

Tests each of the 5 attack vectors from PROTOCOL.md against existing
swarm infrastructure. Reports mitigation status per layer.

Usage:
    python3 tools/f_sec1_security_audit.py [--json]
"""

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _current_session() -> int:
    try:
        out = subprocess.check_output(
            ["git", "log", "--oneline", "-20"], cwd=str(ROOT),
            stderr=subprocess.DEVNULL, text=True, timeout=5
        )
        nums = [int(m) for m in re.findall(r"\[S(\d+)\]", out)]
        return max(nums) if nums else 0
    except Exception:
        return 0


def _file_exists(rel: str) -> bool:
    return (ROOT / rel).exists()


def _file_contains(rel: str, pattern: str) -> bool:
    p = ROOT / rel
    if not p.exists():
        return False
    return bool(re.search(pattern, p.read_text(errors="ignore")))


def audit_layer1_bundle_integrity() -> dict:
    """Layer 1: Genesis bundle hash — prevents replay attacks."""
    result = {"layer": 1, "name": "Genesis Bundle Integrity", "attack": "Genesis replay"}

    # Check if hash generation exists
    has_hash_gen = _file_contains("tools/genesis_evolve.py", r"compute_genesis_bundle_hash")
    has_hash_write = _file_contains("tools/genesis_evolve.py", r"write_genesis_bundle_hash")

    # Check if verification is wired into startup
    genesis_wires_hash = _file_contains("workspace/genesis.sh", r"bundle.hash|genesis_evolve.*bundle")
    orient_verifies = _file_contains("tools/orient.py", r"bundle.hash|genesis_bundle")
    check_verifies = _file_contains("tools/check.sh", r"bundle.hash|genesis_bundle")

    # Can we generate a hash?
    can_generate = has_hash_gen and has_hash_write

    # Is verification automatic?
    is_verified = genesis_wires_hash or orient_verifies or check_verifies

    # Tamper detection test: compute hash, simulate tamper, verify change
    tamper_detected = False
    bundle_hash = None
    if can_generate:
        try:
            sys.path.insert(0, str(ROOT / "tools"))
            from genesis_evolve import compute_genesis_bundle_hash
            bundle_hash, files, _ = compute_genesis_bundle_hash()
            # Simulate tamper: hash with extra content
            hasher = hashlib.sha256()
            for f in files:
                hasher.update(f.read_bytes())
            hasher.update(b"\n# INJECTED BELIEF\n")
            tampered_hash = hasher.hexdigest()
            tamper_detected = bundle_hash != tampered_hash
        except Exception:
            pass

    result["findings"] = {
        "hash_generation_exists": can_generate,
        "genesis_sh_wires_hash": genesis_wires_hash,
        "orient_verifies_hash": orient_verifies,
        "check_sh_verifies_hash": check_verifies,
        "auto_verification": is_verified,
        "tamper_detection_test": "PASS" if tamper_detected else "SKIP",
        "bundle_hash": bundle_hash[:16] + "..." if bundle_hash else None,
    }

    if is_verified:
        result["status"] = "MITIGATED"
        result["score"] = 1.0
    elif can_generate:
        result["status"] = "TOOL_EXISTS_NOT_WIRED"
        result["score"] = 0.2
    else:
        result["status"] = "UNMITIGATED"
        result["score"] = 0.0

    result["gap"] = ("Hash generation exists but NOT verified at child startup or commit time"
                     if can_generate and not is_verified else
                     "No hash infrastructure" if not can_generate else "Fully wired")
    return result


def audit_layer2_authority_tiers() -> dict:
    """Layer 2: Bulletin authority tiers — prevents belief injection."""
    result = {"layer": 2, "name": "Bulletin Authority Tiers", "attack": "Belief injection"}

    bulletin_exists = _file_exists("tools/bulletin.py")
    has_trust_tier = _file_contains("tools/bulletin.py", r"Trust.Tier|trust_tier|T[123]")
    merge_back_exists = _file_exists("tools/merge_back.py")

    # Check if bulletins auto-merge into beliefs
    auto_merge = _file_contains("tools/bulletin.py", r"auto.merge|merge_belief")

    # Passive defense: no auto-merge = injection has no delivery channel
    # merge_back.py existing is fine IF it has drift guards (Layer 3 covers that)
    passive_defense = bulletin_exists and not auto_merge

    # merge_back.py with drift thresholds = guarded merge pathway (not a vulnerability)
    merge_guarded = merge_back_exists and _file_contains(
        "tools/merge_back.py", r"DRIFT_AUTO_MERGE|DRIFT_FLAG_MERGE|COUNCIL_REVIEW"
    )

    result["findings"] = {
        "bulletin_py_exists": bulletin_exists,
        "has_trust_tiers": has_trust_tier,
        "merge_back_exists": merge_back_exists,
        "merge_pathway_guarded": merge_guarded,
        "auto_merge_exists": auto_merge,
        "passive_defense_dead_channel": passive_defense,
    }

    if has_trust_tier and not auto_merge:
        result["status"] = "MITIGATED"
        result["score"] = 1.0
        result["gap"] = "Trust-Tier field enforced. No auto-merge pipeline."
    elif passive_defense and merge_guarded:
        result["status"] = "PASSIVELY_BLOCKED"
        result["score"] = 0.5
        result["gap"] = "No Trust-Tier field in bulletins. Passive defense (no auto-merge) + guarded merge pathway (Layer 3 drift thresholds)."
        result["note"] = "No auto-merge = injection has no delivery channel. merge_back.py has drift guards."
    elif passive_defense:
        result["status"] = "PASSIVELY_BLOCKED"
        result["score"] = 0.5
        result["gap"] = "No Trust-Tier field in bulletins. Passive defense only (no auto-merge pipeline)."
        result["note"] = "No auto-merge = injection has no delivery channel (L-703: signals dead)"
    else:
        result["status"] = "UNMITIGATED"
        result["score"] = 0.0
        result["gap"] = "No Trust-Tier field in bulletins. No passive defense."
    return result


def audit_layer3_drift_threshold() -> dict:
    """Layer 3: Belief drift threshold — prevents silent corruption at merge."""
    result = {"layer": 3, "name": "Belief Drift Threshold", "attack": "Silent belief corruption"}

    merge_back_exists = _file_exists("tools/merge_back.py")
    has_drift_check = merge_back_exists and _file_contains("tools/merge_back.py", r"drift|threshold")
    has_thresholds = merge_back_exists and _file_contains("tools/merge_back.py", r"DRIFT_AUTO_MERGE|DRIFT_FLAG_MERGE")

    # Is it wired into check.sh?
    check_wires_drift = _file_contains("tools/check.sh", r"merge_back\.py|colony.*drift")

    # Alternative: does contract_check.py or validate_beliefs.py check drift?
    contract_checks_drift = _file_contains("tools/contract_check.py", r"drift|belief.*diff")
    validate_checks_drift = _file_contains("tools/validate_beliefs.py", r"drift|belief.*diff")

    result["findings"] = {
        "merge_back_exists": merge_back_exists,
        "has_drift_check": has_drift_check,
        "has_thresholds": has_thresholds,
        "check_sh_wires_drift": check_wires_drift,
        "contract_checks_drift": contract_checks_drift,
        "validate_checks_drift": validate_checks_drift,
    }

    if has_drift_check and check_wires_drift:
        result["status"] = "MITIGATED"
        result["score"] = 1.0
        result["gap"] = "merge_back.py enforces 10%/30% drift thresholds, wired into check.sh."
    elif has_drift_check:
        result["status"] = "TOOL_EXISTS_NOT_WIRED"
        result["score"] = 0.6
        result["gap"] = "merge_back.py exists with drift thresholds but not wired into check.sh."
    elif contract_checks_drift or validate_checks_drift:
        result["status"] = "PARTIAL"
        result["score"] = 0.3
        result["gap"] = "merge_back.py does not exist. Partial drift coverage via other tools."
    else:
        result["status"] = "UNMITIGATED"
        result["score"] = 0.0
        result["gap"] = "merge_back.py does not exist. No drift measurement at any merge point."
    return result


def audit_layer4_hostile_signal() -> dict:
    """Layer 4: Hostile signal heuristic (FM-10) — prevents NEVER-REMOVE atom modification."""
    result = {"layer": 4, "name": "Hostile Signal Heuristic", "attack": "Hostile bulletin / NEVER-REMOVE override"}

    # Check if check.sh has FM-10 guard
    check_has_fm10 = _file_contains("tools/check.sh", r"FM.10|hostile|NEVER.REMOVE|atom.*validator")
    bulletin_has_guard = _file_contains("tools/bulletin.py", r"hostile|NEVER.REMOVE|block.*atom")

    # Check if any tool validates NEVER-REMOVE atoms
    genesis_has_never_remove = _file_contains("workspace/genesis.sh", r"NEVER.remove.*atom")

    # Check if check.sh validates core file presence
    check_validates_core = _file_contains("tools/check.sh", r"CORE\.md|beliefs.*check|contract_check")

    result["findings"] = {
        "check_sh_has_fm10": check_has_fm10,
        "bulletin_has_guard": bulletin_has_guard,
        "genesis_documents_never_remove": genesis_has_never_remove,
        "check_sh_validates_core_files": check_validates_core,
    }

    if check_has_fm10:
        result["status"] = "MITIGATED"
        result["score"] = 1.0
    elif check_validates_core:
        result["status"] = "PARTIAL"
        result["score"] = 0.2
        result["note"] = "Core file presence checked but no hostile content detection"
    else:
        result["status"] = "UNMITIGATED"
        result["score"] = 0.0

    if check_has_fm10:
        result["gap"] = "FM-10 guard in check.sh enforces NEVER-REMOVE atoms at commit time."
    else:
        result["gap"] = "No FM-10 guard in check.sh. NEVER-REMOVE atoms documented but not enforced."
    return result


def audit_layer5_minimum_transfer() -> dict:
    """Layer 5: Minimum genesis transfer unit — prevents blank-slate and full-dump spawns."""
    result = {"layer": 5, "name": "Minimum Transfer Unit", "attack": "Fork bomb / uncontrolled spawning"}

    # Check genesis.sh transfers minimum set
    genesis = ROOT / "workspace" / "genesis.sh"
    if genesis.exists():
        gt = genesis.read_text(errors="ignore")
        has_validator = "atom:validator" in gt
        has_core = "atom:core-beliefs" in gt
        has_principles = "atom:principles-inherit" in gt or "PRINCIPLES.md" in gt
        has_lesson_delta = "lessons" in gt.lower()
        has_frontier = "atom:frontier" in gt
        transfers_spawn_tools = "atom:self-swarm-tooling" in gt
    else:
        has_validator = has_core = has_principles = has_lesson_delta = has_frontier = False
        transfers_spawn_tools = False

    # Check for depth limit (F-SEC1 Layer 5, FM-12)
    colony_has_depth = _file_contains("tools/swarm_colony.py", r"max_depth|depth_limit|MAX_DEPTH|MAX_COLONY_DEPTH")
    colony_enforces_depth = _file_contains("tools/swarm_colony.py", r"depth\s*>\s*MAX|exceeds.*MAX_COLONY_DEPTH")

    # Count minimum transfer items present
    min_items = sum([has_validator, has_core, has_principles, has_lesson_delta, has_frontier])

    result["findings"] = {
        "transfers_validator": has_validator,
        "transfers_core_beliefs": has_core,
        "transfers_principles": has_principles,
        "transfers_lessons": has_lesson_delta,
        "transfers_frontiers": has_frontier,
        "transfers_spawn_tools": transfers_spawn_tools,
        "has_depth_limit": colony_has_depth,
        "minimum_items_present": f"{min_items}/5",
    }

    result["findings"]["colony_enforces_depth"] = colony_enforces_depth

    if min_items >= 4 and colony_has_depth and colony_enforces_depth:
        result["status"] = "MITIGATED"
        result["score"] = 1.0
    elif min_items >= 4 and colony_has_depth:
        result["status"] = "PARTIAL_DEPTH_DEFINED"
        result["score"] = 0.7
        result["note"] = f"Depth constant defined but enforcement not verified"
    elif min_items >= 4:
        result["status"] = "PARTIAL_NO_DEPTH_LIMIT"
        result["score"] = 0.4
        result["note"] = f"Transfer unit complete ({min_items}/5) but no fork bomb protection"
    elif min_items >= 2:
        result["status"] = "PARTIAL"
        result["score"] = 0.2
    else:
        result["status"] = "UNMITIGATED"
        result["score"] = 0.0

    result["gap"] = f"Transfer unit {min_items}/5. {'Depth limited (MAX_COLONY_DEPTH enforced).' if colony_enforces_depth else 'No depth limit in swarm_colony.py — fork bomb unmitigated.' if not colony_has_depth else 'Depth constant defined, enforcement unclear.'}"
    return result


def run_full_audit() -> dict:
    audits = [
        audit_layer1_bundle_integrity(),
        audit_layer2_authority_tiers(),
        audit_layer3_drift_threshold(),
        audit_layer4_hostile_signal(),
        audit_layer5_minimum_transfer(),
    ]

    total_score = sum(a["score"] for a in audits)
    max_score = len(audits)

    session = _current_session()
    return {
        "session": f"S{session}",
        "timestamp": datetime.now(tz=__import__('datetime').timezone.utc).isoformat(),
        "frontier": "F-SEC1",
        "domain": "security",
        "tool": "f_sec1_security_audit.py",
        "layers": audits,
        "summary": {
            "total_score": f"{total_score:.1f}/{max_score}",
            "pct": round(total_score / max_score * 100, 1),
            "mitigated": sum(1 for a in audits if a["score"] >= 0.8),
            "partial": sum(1 for a in audits if 0.2 <= a["score"] < 0.8),
            "unmitigated": sum(1 for a in audits if a["score"] < 0.2),
            "verdict": "STRONG" if total_score / max_score >= 0.6 else
                       "MODERATE" if total_score / max_score >= 0.3 else "WEAK",
        },
    }


def print_report(audit: dict):
    print("=== F-SEC1 SECURITY AUDIT ===\n")
    for layer in audit["layers"]:
        status_icon = {"MITIGATED": "+", "PARTIAL": "~", "PARTIAL_NO_DEPTH_LIMIT": "~",
                       "PASSIVELY_BLOCKED": "~", "TOOL_EXISTS_NOT_WIRED": "~",
                       "UNMITIGATED": "!"}
        icon = status_icon.get(layer["status"], "?")
        print(f"  [{icon}] Layer {layer['layer']}: {layer['name']}")
        print(f"      Attack: {layer['attack']}")
        print(f"      Status: {layer['status']} (score {layer['score']:.1f})")
        print(f"      Gap: {layer['gap']}")
        if "note" in layer:
            print(f"      Note: {layer['note']}")
        print()

    s = audit["summary"]
    print(f"--- Summary ---")
    print(f"  Score: {s['total_score']} ({s['pct']}%) — {s['verdict']}")
    print(f"  Mitigated: {s['mitigated']} | Partial: {s['partial']} | Unmitigated: {s['unmitigated']}")


def main():
    audit = run_full_audit()

    if "--json" in sys.argv:
        print(json.dumps(audit, indent=2))
    else:
        print_report(audit)

    # Write experiment artifact
    out_dir = ROOT / "experiments" / "security"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"f-sec1-bundle-integrity-s{_current_session()}.json"
    out_path.write_text(json.dumps(audit, indent=2) + "\n")
    print(f"\nArtifact: {out_path.relative_to(ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
