#!/usr/bin/env python3
"""Dogma finder — surfaces beliefs, principles, and claims that have ossified
into unquestioned dogma.

Dogma signals:
  1. UNCHALLENGED    — existed many sessions with zero challenge entries
  2. STALE-TEST      — belief "Last tested" is old relative to current session
  3. AXIOM-STUCK     — marked axiom/theorized for a long time, no upgrade path
  4. CONFIRM-ONLY    — all challenges resolved as CONFIRMED, never DROPPED
  5. SELF-REFERENTIAL — evidence chain is entirely internal
  6. FOUNDING-ERA    — early-session claims still active without re-validation
  7. HIGH-CITE-LOW-TEST — cited many times but confidence never upgraded
  8. REFINE-DRIFT    — multiple refinements soften language without substance change

Usage:
  python3 tools/dogma_finder.py              # full report
  python3 tools/dogma_finder.py --json       # machine-readable
  python3 tools/dogma_finder.py --top 10     # top N most dogmatic items
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEPS = REPO / "beliefs" / "DEPS.md"
PHIL = REPO / "beliefs" / "PHILOSOPHY.md"
CHALLENGES = REPO / "beliefs" / "CHALLENGES.md"
PRINCIPLES = REPO / "memory" / "PRINCIPLES.md"
LESSONS_DIR = REPO / "memory" / "lessons"


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def parse_beliefs() -> list[dict]:
    """Parse beliefs from DEPS.md."""
    text = _read(DEPS)
    beliefs = []
    pat = re.compile(r"^###\s+(?P<id>B[\w-]+\d*):\s*(?P<stmt>.+?)$", re.MULTILINE)
    matches = list(pat.finditer(text))
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end]
        evidence = re.search(r"\*\*Evidence\*\*:\s*(\S+)", block, re.I)
        tested = re.search(r"\*\*Last tested\*\*:\s*(.+?)$", block, re.M | re.I)
        falsified = re.search(r"\*\*Falsified if\*\*:\s*(.+?)$", block, re.M | re.I)
        test_session = None
        if tested:
            sm = re.search(r"S(\d+)", tested.group(1))
            if sm:
                test_session = int(sm.group(1))
        beliefs.append({
            "id": m.group("id"),
            "statement": m.group("stmt").strip(),
            "evidence": evidence.group(1).strip().lower() if evidence else "",
            "last_tested_session": test_session,
            "last_tested_raw": tested.group(1).strip() if tested else "",
            "falsification": falsified.group(1).strip() if falsified else "",
            "block": block,
            "kind": "belief",
        })
    return beliefs


def parse_phil_claims() -> list[dict]:
    """Parse PHIL-N claims from PHILOSOPHY.md."""
    text = _read(PHIL)
    claims = []
    pat = re.compile(r"\*\*\[PHIL-(\d+)\]\*\*\s*(.+?)(?=\n\n|\n\*\*\[PHIL-|\Z)", re.S)
    for m in pat.finditer(text):
        phil_id = int(m.group(1))
        content = m.group(2).strip()
        stmt = content.split("\n")[0].strip()
        claims.append({
            "id": f"PHIL-{phil_id}",
            "statement": stmt,
            "content": content,
            "kind": "philosophy",
        })
    table_pat = re.compile(
        r"\|\s*PHIL-(\d+)\s*\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|", re.M
    )
    table_claims = {}
    for m in table_pat.finditer(text):
        pid = f"PHIL-{m.group(1).strip()}"
        table_claims[pid] = {
            "type": m.group(3).strip(),
            "grounding": m.group(4).strip(),
            "status": m.group(5).strip(),
        }
    for c in claims:
        if c["id"] in table_claims:
            c.update(table_claims[c["id"]])
    return claims


def parse_challenges() -> list[dict]:
    """Parse challenge entries from CHALLENGES.md and PHILOSOPHY.md."""
    challenges = []
    for path in [CHALLENGES, PHIL]:
        text = _read(path)
        pat = re.compile(
            r"\|\s*S(\d+)\s*\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|",
            re.M,
        )
        for m in pat.finditer(text):
            status_raw = m.group(6).strip()
            status = "OPEN"
            for s in ("CONFIRMED", "SUPERSEDED", "DROPPED", "RESOLVED"):
                if s in status_raw.upper():
                    status = s
                    break
            challenges.append({
                "session": int(m.group(1)),
                "target": m.group(2).strip(),
                "challenge": m.group(3).strip()[:120],
                "status": status,
                "source": path.name,
            })
    return challenges


def parse_principles() -> list[dict]:
    """Extract P-NNN identifiers and their text from PRINCIPLES.md."""
    text = _read(PRINCIPLES)
    principles = []
    pat = re.compile(r"P-(\d{3})\s+([^|P]+?)(?=P-\d{3}|\n##|\Z)", re.S)
    for m in pat.finditer(text):
        pid = f"P-{m.group(1)}"
        content = m.group(2).strip()
        evidence = ""
        for e in ("MEASURED", "OBSERVED", "THEORIZED", "PARTIALLY OBSERVED",
                   "DESIGNED", "DIRECTIONAL"):
            if e in content.upper():
                evidence = e
                break
        cites = re.findall(r"L-(\d+)", content)
        principles.append({
            "id": pid,
            "content": content[:200],
            "evidence": evidence,
            "cited_lessons": [f"L-{c}" for c in cites],
            "kind": "principle",
        })
    return principles


def get_current_session() -> int:
    """Estimate current session from recent git log."""
    import subprocess
    try:
        out = subprocess.run(
            ["git", "log", "--oneline", "-20"],
            capture_output=True, text=True, cwd=REPO,
        ).stdout
        sessions = [int(s) for s in re.findall(r"\[S(\d+)\]", out)]
        return max(sessions) if sessions else 500
    except Exception:
        return 500


def sample_lesson_confidence() -> dict[str, str]:
    """Sample confidence levels from lessons."""
    confidences = {}
    for f in sorted(LESSONS_DIR.glob("L-*.md")):
        text = _read(f)
        m = re.search(r"Confidence:\s*(\w+)", text)
        if m:
            confidences[f.stem] = m.group(1).strip()
    return confidences


# ---------------------------------------------------------------------------
# Dogma detection
# ---------------------------------------------------------------------------

def detect_dogma() -> list[dict]:
    """Run all dogma detectors, return scored findings."""
    current_session = get_current_session()
    beliefs = parse_beliefs()
    phil_claims = parse_phil_claims()
    challenges = parse_challenges()
    principles = parse_principles()

    # Build challenge target index — normalize B-1/B1 variants
    challenged_targets = defaultdict(list)
    for c in challenges:
        target = c["target"].strip()
        for tid in re.findall(r"(B-?\w*\d+|PHIL-\d+|P-\d+|L-\d+|I\d+)", target):
            norm = tid
            m_b = re.match(r"B-(\d+)$", tid)
            if m_b:
                norm = f"B{m_b.group(1)}"
            challenged_targets[norm].append(c)
        for tid in re.findall(r"(B-?\d+|PHIL-\d+)", c.get("challenge", "")):
            m_b = re.match(r"B-(\d+)$", tid)
            norm = f"B{m_b.group(1)}" if m_b else tid
            if norm not in challenged_targets or \
               c not in challenged_targets[norm]:
                challenged_targets[norm].append(c)

    findings = []

    def add(item_id, kind, signal, score, detail):
        findings.append({
            "id": item_id,
            "kind": kind,
            "signal": signal,
            "score": round(score, 2),
            "detail": detail,
        })

    # --- Signal 1: UNCHALLENGED beliefs ---
    for b in beliefs:
        bid = b["id"]
        n_challenges = len(challenged_targets.get(bid, []))
        if n_challenges == 0:
            age = current_session - (b["last_tested_session"] or 0)
            score = min(1.0, age / 300)
            add(bid, "belief", "UNCHALLENGED",
                score, f"0 challenges in {current_session}+ sessions")

    # --- Signal 1b: UNCHALLENGED PHIL claims ---
    for p in phil_claims:
        pid = p["id"]
        n_challenges = len(challenged_targets.get(pid, []))
        if n_challenges == 0:
            add(pid, "philosophy", "UNCHALLENGED",
                0.7, f"0 challenge entries filed against {pid}")

    # --- Signal 2: STALE-TEST beliefs ---
    for b in beliefs:
        if b["last_tested_session"]:
            staleness = current_session - b["last_tested_session"]
            if staleness > 50:
                score = min(1.0, staleness / 200)
                add(b["id"], "belief", "STALE-TEST",
                    score,
                    f"Last tested S{b['last_tested_session']}, "
                    f"{staleness} sessions ago")

    # --- Signal 3: AXIOM-STUCK ---
    for p in phil_claims:
        grounding = p.get("grounding", "").lower()
        if grounding in ("axiom", "aspirational", "unverified", "metaphor"):
            add(p["id"], "philosophy", "AXIOM-STUCK",
                0.6, f"Grounding: {grounding} — no path to observed/measured")

    for b in beliefs:
        if b["evidence"] == "theorized":
            age = current_session - (b["last_tested_session"] or 0)
            score = min(1.0, 0.4 + age / 500)
            add(b["id"], "belief", "AXIOM-STUCK",
                score, f"Evidence: theorized for {age}+ sessions")

    # --- Signal 4: CONFIRM-ONLY challenges ---
    target_outcomes = defaultdict(list)
    for c in challenges:
        for tid in re.findall(r"(B-?\w+\d+|PHIL-\d+|P-\d+)", c["target"]):
            target_outcomes[tid].append(c["status"])
    for tid, outcomes in target_outcomes.items():
        resolved = [o for o in outcomes if o != "OPEN"]
        if len(resolved) >= 2:
            n_dropped = sum(1 for o in resolved if o == "DROPPED")
            if n_dropped == 0:
                add(tid, "mixed", "CONFIRM-ONLY",
                    0.5 + 0.1 * len(resolved),
                    f"{len(resolved)} challenges, 0 DROPPED — "
                    f"challenge mechanism may confirm rather than test")

    # --- Signal 5: SELF-REFERENTIAL evidence ---
    for p in phil_claims:
        content = p.get("content", "")
        has_external = bool(re.search(
            r"(external|outside|independent|non-swarm|real.world)", content, re.I
        ))
        if not has_external and len(content) > 100:
            add(p["id"], "philosophy", "SELF-REFERENTIAL",
                0.5, "Evidence chain appears entirely internal to swarm")

    # --- Signal 6: FOUNDING-ERA without re-validation ---
    for b in beliefs:
        if b["last_tested_session"] and b["last_tested_session"] < 100:
            add(b["id"], "belief", "FOUNDING-ERA",
                0.8, f"Last tested S{b['last_tested_session']} "
                     f"(founding era, pre-S100)")

    for p in principles:
        pid_num = int(p["id"].replace("P-", ""))
        if pid_num <= 30 and p["evidence"] in ("", "THEORIZED"):
            add(p["id"], "principle", "FOUNDING-ERA",
                0.6, f"Early principle (#{pid_num}), evidence: "
                     f"{p['evidence'] or 'UNSPECIFIED'}")

    # --- Signal 7: HIGH-CITE-LOW-TEST (sampled) ---
    confidences = sample_lesson_confidence()
    high_cite_candidates = ["L-601", "L-223", "L-025", "L-491",
                            "L-599", "L-787", "L-804"]
    for lid in high_cite_candidates:
        conf = confidences.get(lid, "")
        if conf in ("Assumed", "Theorized"):
            add(lid, "lesson", "HIGH-CITE-LOW-TEST",
                0.7, f"Heavily cited but confidence only '{conf}'")

    # --- Signal 8: REFINE-DRIFT ---
    refine_counts = defaultdict(int)
    for c in challenges:
        if "REFINE" in c.get("status", "").upper() or \
           "REFINED" in c.get("challenge", "").upper():
            for tid in re.findall(r"(B-?\w+\d+|PHIL-\d+|P-\d+)", c["target"]):
                refine_counts[tid] += 1
    for tid, count in refine_counts.items():
        if count >= 2:
            add(tid, "mixed", "REFINE-DRIFT",
                0.4 + 0.15 * count,
                f"{count} refinements — language softening without "
                f"substantive revision?")

    # --- Score normalization and dedup ---
    merged = defaultdict(lambda: {"signals": [], "total_score": 0.0})
    for f in findings:
        key = f["id"]
        merged[key]["id"] = f["id"]
        merged[key]["kind"] = f["kind"]
        merged[key]["signals"].append({
            "signal": f["signal"],
            "score": f["score"],
            "detail": f["detail"],
        })
        merged[key]["total_score"] += f["score"]

    result = sorted(merged.values(), key=lambda x: -x["total_score"])
    return result


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_report(findings: list[dict], top_n: int = 0):
    """Human-readable dogma report."""
    if top_n:
        findings = findings[:top_n]

    print(f"{'='*70}")
    print(f"  DOGMA FINDER — {len(findings)} items with ossification signals")
    print(f"{'='*70}")
    print()

    for rank, item in enumerate(findings, 1):
        score = item["total_score"]
        bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
        print(f"  #{rank:2d}  {item['id']:12s} [{item['kind']:10s}]  "
              f"dogma: {bar} {score:.2f}")
        for s in item["signals"]:
            print(f"        ├─ {s['signal']:20s} (+{s['score']:.2f})  "
                  f"{s['detail']}")
        print()

    signals = defaultdict(int)
    for item in findings:
        for s in item["signals"]:
            signals[s["signal"]] += 1
    print(f"{'─'*70}")
    print("  Signal distribution:")
    for sig, count in sorted(signals.items(), key=lambda x: -x[1]):
        print(f"    {sig:20s}  {count:3d} instances")
    print()

    top3 = findings[:3] if findings else []
    if top3:
        print("  TOP 3 MOST DOGMATIC (investigate first):")
        for item in top3:
            print(f"    -> {item['id']}: "
                  f"{', '.join(s['signal'] for s in item['signals'])}")
    print()


def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    top_n = 0
    if "--top" in args:
        idx = args.index("--top")
        if idx + 1 < len(args):
            top_n = int(args[idx + 1])

    findings = detect_dogma()

    if as_json:
        out = findings[:top_n] if top_n else findings
        print(json.dumps(out, indent=2))
    else:
        print_report(findings, top_n)


if __name__ == "__main__":
    main()
