#!/usr/bin/env python3
"""Per-claim philosophy audit — structural wiring of L-1116.

L-1230: Three classes of impossibility (constitutive/persistent/logical).
Constitutive impossibilities ARE the swarm — don't fix. Persistent failures
LIMIT it — fix. Test: would removing this destroy identity?

Replaces the expensive manual claim-vs-evidence periodic with automated
per-claim health checks. Makes the audit cheap enough to run every session
instead of every 20 sessions (L-1116: reduce cost, not increase priority).

Usage:
    python3 tools/philosophy_audit.py              # full report
    python3 tools/philosophy_audit.py --stale 30   # only claims stale >30 sessions
    python3 tools/philosophy_audit.py --pick        # pick ONE claim to challenge this session
"""

import re
import sys
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHIL_PATH = ROOT / "beliefs" / "PHILOSOPHY.md"
CHALLENGE_ARCHIVE = ROOT / "beliefs" / "PHILOSOPHY-CHALLENGE-ARCHIVE.md"
SESSION_LOG = ROOT / "domains" / "meta" / "SESSION-LOG.md"


def current_session():
    """Get current session number from recent git log."""
    import subprocess
    try:
        out = subprocess.run(
            ["git", "log", "--oneline", "-20"],
            capture_output=True, text=True, cwd=ROOT,
        ).stdout
        sessions = [int(s) for s in re.findall(r"\[S(\d+)\]", out)]
        return max(sessions) if sessions else 500
    except Exception:
        return 500


def parse_claims_table(text):
    """Parse the claims table from PHILOSOPHY.md."""
    claims = {}
    in_claims = False
    for line in text.split("\n"):
        if "| ID | Claim (short)" in line:
            in_claims = True
            continue
        if in_claims and line.startswith("|---"):
            continue
        if in_claims and line.startswith("|"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 5:
                cid = parts[0]
                claims[cid] = {
                    "claim": parts[1],
                    "type": parts[2],
                    "grounding": parts[3],
                    "status": parts[4],
                }
        elif in_claims and not line.strip():
            break
    return claims


def parse_challenges(text):
    """Parse challenges from PHILOSOPHY.md challenges section."""
    challenges = {}
    in_challenges = False
    for line in text.split("\n"):
        if "| Claim | Session | Challenge" in line:
            in_challenges = True
            continue
        if in_challenges and line.startswith("|---"):
            continue
        if in_challenges and line.startswith("|"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 4:
                claim_id = parts[0]
                session_match = re.search(r"S(\d+)", parts[1])
                session = int(session_match.group(1)) if session_match else 0
                if claim_id not in challenges:
                    challenges[claim_id] = []
                challenges[claim_id].append({
                    "session": session,
                    "text": parts[2][:80],
                    "status": parts[3][:60],
                })
        elif in_challenges and not line.strip():
            break
    return challenges


def parse_archived_challenges():
    """Count archived challenges per claim."""
    archived = {}
    if not CHALLENGE_ARCHIVE.exists():
        return archived
    text = CHALLENGE_ARCHIVE.read_text()
    for m in re.finditer(r"\|\s*(PHIL-\d+\w*)\s*\|", text):
        cid = m.group(1)
        archived[cid] = archived.get(cid, 0) + 1
    return archived


def parse_drop_criteria(text):
    """Parse DROP criteria table."""
    criteria = {}
    in_drop = False
    for line in text.split("\n"):
        if "| ID | Class | DROP criterion" in line:
            in_drop = True
            continue
        if in_drop and line.startswith("|---"):
            continue
        if in_drop and line.startswith("|"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 3:
                criteria[parts[0]] = {
                    "class": parts[1],
                    "criterion": parts[2][:100],
                }
        elif in_drop and not line.strip():
            break
    return criteria


def audit():
    now = current_session()
    text = PHIL_PATH.read_text()

    claims = parse_claims_table(text)
    challenges = parse_challenges(text)
    archived = parse_archived_challenges()
    drop_criteria = parse_drop_criteria(text)

    stale_threshold = 30
    pick_mode = False
    for arg in sys.argv[1:]:
        if arg == "--pick":
            pick_mode = True
        elif arg == "--stale":
            idx = sys.argv.index("--stale")
            if idx + 1 < len(sys.argv):
                stale_threshold = int(sys.argv[idx + 1])

    results = []
    for cid, info in sorted(claims.items(), key=lambda x: x[0]):
        status = info.get("status", "")
        if "SUPERSEDED" in status or "DROPPED" in status:
            continue

        claim_challenges = challenges.get(cid, [])
        archive_count = archived.get(cid, 0)
        total_challenges = len(claim_challenges) + archive_count

        last_session = max((c["session"] for c in claim_challenges), default=0)
        staleness = now - last_session if last_session > 0 else now

        has_drop = cid in drop_criteria
        drop_class = drop_criteria.get(cid, {}).get("class", "?")

        # Health flags
        flags = []
        if total_challenges == 0:
            flags.append("NEVER-CHALLENGED")
        if staleness > stale_threshold:
            flags.append(f"STALE({staleness}s)")
        if info["grounding"] in ("unverified", "aspirational"):
            flags.append(f"WEAK-GROUND({info['grounding']})")
        if not has_drop:
            flags.append("NO-DROP")
        if drop_class == "U":
            flags.append("UNFALSIFIABLE")

        # Persistent challenges (unresolved)
        persistent = [c for c in claim_challenges if "PERSISTENT" in c.get("status", "")]
        if persistent:
            flags.append(f"PERSISTENT({len(persistent)})")

        results.append({
            "id": cid,
            "claim": info["claim"][:50],
            "grounding": info["grounding"],
            "challenges": total_challenges,
            "last_challenged": f"S{last_session}" if last_session else "never",
            "staleness": staleness,
            "flags": flags,
        })

    if "--stale" in sys.argv:
        results = [r for r in results if r["staleness"] > stale_threshold]

    if pick_mode:
        # Weighted random: stale + weak grounding + never-challenged get higher weight
        weights = []
        for r in results:
            w = 1.0
            if "NEVER-CHALLENGED" in r["flags"]:
                w += 5.0
            if r["staleness"] > 50:
                w += 3.0
            elif r["staleness"] > 30:
                w += 1.5
            if "WEAK-GROUND" in " ".join(r["flags"]):
                w += 2.0
            weights.append(w)
        if results:
            pick = random.choices(results, weights=weights, k=1)[0]
            print(f"=== PHILOSOPHY AUDIT — PICK ONE (S{now}) ===")
            print(f"  Challenge this session: {pick['id']} — {pick['claim']}")
            print(f"  Grounding: {pick['grounding']} | Last: {pick['last_challenged']} | Flags: {', '.join(pick['flags']) or 'none'}")
            drop = drop_criteria.get(pick["id"], {})
            if drop:
                print(f"  DROP criterion ({drop['class']}): {drop['criterion']}")
            print(f"\n  Action: find evidence FOR or AGAINST this claim. File challenge row.")
        return

    # Full report
    print(f"=== PHILOSOPHY AUDIT — S{now} ({len(results)} active claims) ===")
    print()

    stale_count = sum(1 for r in results if r["staleness"] > stale_threshold)
    never_count = sum(1 for r in results if "NEVER-CHALLENGED" in r["flags"])
    weak_count = sum(1 for r in results if any("WEAK-GROUND" in f for f in r["flags"]))

    print(f"  Summary: {stale_count} stale (>{stale_threshold}s) | {never_count} never-challenged | {weak_count} weak grounding")
    print()

    for r in results:
        flag_str = " ".join(f"[{f}]" for f in r["flags"]) if r["flags"] else "[OK]"
        print(f"  {r['id']:12s} {r['grounding']:12s} ch={r['challenges']:2d}  last={r['last_challenged']:6s}  {flag_str}")

    print()
    print(f"  Claim health: {len(results) - len([r for r in results if r['flags']])}/{len(results)} clean")
    print(f"  Use --pick to get one claim to challenge this session")
    print(f"  Use --stale N to filter for claims stale >N sessions")


if __name__ == "__main__":
    audit()
