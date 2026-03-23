#!/usr/bin/env python3
"""Dogma finder — surfaces beliefs, principles, and claims that have ossified
into unquestioned dogma.

Dogma signals:
  1. UNCHALLENGED    — existed many sessions with zero challenge entries
  2. STALE-TEST      — belief "Last tested" is old relative to current session
  3. AXIOM-STUCK     — aspirational/unverified/metaphor grounding with no upgrade path
  3b.AXIOM-BY-DESIGN — design-choice axiom (low severity — DROP resistance is expected)
  4. CONFIRM-ONLY    — all challenges resolved as CONFIRMED, never DROPPED
  4b.CONFIRM-ONLY (axiom) — axiom with all CONFIRMED (lower weight — expected behavior)
  5. SELF-REFERENTIAL — evidence chain is entirely internal
  6. FOUNDING-ERA    — early-session claims still active without re-validation
  7. HIGH-CITE-LOW-TEST — cited many times but confidence never upgraded
  8. REFINE-DRIFT    — multiple refinements soften language without substance change
  9. META-DOGMA      — dogma finder's own hardcoded assumptions
 10. PROSE-STATUS-DRIFT — status text contradicts original claim prose (L-1411)

Epistemic type awareness (S505 L-1336):
  Axioms (design choices) get lower dogma scores because they resist
  falsification BY DESIGN, not due to confirmation bias. The prior version
  conflated axioms with empirical claims, making all top dogma items axioms
  that were structurally unable to be dropped.

Self-application (SIG-82): The dogma finder detects meta-dogma in its own
  assumptions (signal weights, thresholds, candidate lists). Prescriptions
  map each signal type to a concrete swarm action. The tool is recursive:
  it subjects itself to the same scrutiny it applies to beliefs.

Usage:
  python3 tools/dogma_finder.py              # full report
  python3 tools/dogma_finder.py --prescribe  # report + concrete actions
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
    # Match both **[PHIL-N]** (inline) and [PHIL-N] (section header) formats
    pat = re.compile(r"(?:\*\*)?(?:\[PHIL-(\d+)\])(?:\*\*)?\s*(.+?)(?=\n\n|\n(?:\*\*)?(?:\[PHIL-)|\Z)", re.S)
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
    # Parse claims table line-by-line to avoid cross-line regex bleed
    # Format: | ID | Claim (short) | Type | Grounding | Status |
    table_claims = {}
    for line in text.splitlines():
        m = re.match(
            r"\|\s*PHIL-(\d+)\s*\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|",
            line.strip(),
        )
        if m:
            pid = f"PHIL-{m.group(1).strip()}"
            table_claim_text = m.group(2).strip()
            claim_type = m.group(3).strip()
            grounding = m.group(4).strip()
            # Only accept entries from the Claims table (has valid type values)
            if claim_type in ("axiom", "observed"):
                table_claims[pid] = {
                    "table_claim": table_claim_text,
                    "type": claim_type,
                    "grounding": grounding,
                    "status": m.group(5).strip(),
                }
    for c in claims:
        if c["id"] in table_claims:
            c.update(table_claims[c["id"]])
    return claims


def parse_challenges() -> list[dict]:
    """Parse challenge entries from CHALLENGES.md and PHILOSOPHY.md."""
    challenges = []
    # CHALLENGES.md: 6-column | Session | Target | Challenge | Evidence | Proposed | Status |
    text = _read(CHALLENGES)
    pat6 = re.compile(
        r"\|\s*S(\d+)\s*\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|",
        re.M,
    )
    for m in pat6.finditer(text):
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
            "source": CHALLENGES.name,
        })
    # PHILOSOPHY.md: 4-column | Claim | Session | Challenge | Status |
    text = _read(PHIL)
    pat4 = re.compile(
        r"\|\s*(PHIL-\d+)\s*\|\s*S(\d+)\s*\|([^|]*)\|([^|]*)\|",
        re.M,
    )
    for m in pat4.finditer(text):
        status_raw = m.group(4).strip()
        status = "OPEN"
        for s in ("CONFIRMED", "SUPERSEDED", "DROPPED", "RESOLVED",
                   "REFINED", "PERSISTENT", "CHALLENGE", "PARTIAL",
                   "BASELINE", "OVERDUE", "DOWNGRADED", "EXECUTED"):
            if s in status_raw.upper():
                status = s
                break
        challenges.append({
            "session": int(m.group(2)),
            "target": m.group(1).strip(),
            "challenge": m.group(3).strip()[:120],
            "status": status,
            "source": PHIL.name,
        })
    # DEPS.md: inline challenges like "- **Challenge S515**: ..."
    text = _read(DEPS)
    pat_inline = re.compile(
        r"-\s*\*\*Challenge\s+S(\d+)\*\*:\s*(.*?)(?=\n-\s|\n###|\n\n|\Z)",
        re.S,
    )
    # Find which B-claim each inline challenge belongs to by scanning for ### B\d+ headers
    b_sections = list(re.finditer(r"###\s+(B\d+|B-EVAL\d+):", text))
    for m in pat_inline.finditer(text):
        # Find the B-claim this challenge belongs to
        target = "unknown"
        pos = m.start()
        for sec in reversed(b_sections):
            if sec.start() < pos:
                target = sec.group(1)
                break
        status_raw = m.group(2).strip()[:200]
        status = "OPEN"
        for s in ("CONFIRMED", "SUPERSEDED", "DROPPED", "RESOLVED",
                   "REFINED", "PERSISTENT", "PARTIAL", "FALSIFIED"):
            if s in status_raw.upper():
                status = s
                break
        challenges.append({
            "session": int(m.group(1)),
            "target": target,
            "challenge": status_raw[:120],
            "status": status,
            "source": DEPS.name,
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


def _top_cited_lessons(top_n: int = 15) -> list[str]:
    """Dynamically compute most-cited lessons from Cites: headers.

    Replaces the hardcoded candidate list (meta-dogma fix, SIG-82).
    Counts how many other lessons cite each L-NNN in their Cites: field.
    """
    cite_counts = defaultdict(int)
    for f in LESSONS_DIR.glob("L-*.md"):
        text = _read(f)
        # Only look at Cites: header line, not full body
        for line in text.split("\n")[:15]:
            if line.strip().lower().startswith("cites:") or \
               line.strip().startswith("- **Cites**:"):
                for cited in re.findall(r"L-(\d+)", line):
                    cite_counts[f"L-{cited}"] += 1
                break
    ranked = sorted(cite_counts.items(), key=lambda x: -x[1])
    return [lid for lid, _ in ranked[:top_n]]


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
        for tid in re.findall(r"(B-?\w*\d+|PHIL-\d+[a-z]?|P-\d+|L-\d+|I\d+)", target):
            norm = tid
            m_b = re.match(r"B-(\d+)$", tid)
            if m_b:
                norm = f"B{m_b.group(1)}"
            challenged_targets[norm].append(c)
        for tid in re.findall(r"(B-?\d+|PHIL-\d+[a-z]?)", c.get("challenge", "")):
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
    # L-1359 meta-reflection: flat 0.7 score hid age-dependent urgency.
    # PHIL-23 was unchallenged for 508 sessions at same score as a 50-session claim.
    # Fix: age-scaled score (0.7 base, up to 1.0 at 300+ sessions unchallenged).
    # L-1487: decomposed sub-claims (PHIL-5a, PHIL-5b) inherit parent challenges.
    for p in phil_claims:
        pid = p["id"]
        n_challenges = len(challenged_targets.get(pid, []))
        if n_challenges == 0:
            parent_match = re.match(r"(PHIL-\d+)[a-z]$", pid)
            if parent_match:
                parent_id = parent_match.group(1)
                n_challenges = len(challenged_targets.get(parent_id, []))
        if n_challenges == 0:
            # Estimate age from session where claim was added (parse from status or use session number from id)
            age = current_session  # conservative: unchallenged since creation
            score = 0.7 + min(0.3, 0.3 * age / 300)
            add(pid, "philosophy", "UNCHALLENGED",
                score, f"0 challenge entries filed against {pid}")

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
    # Distinguish axioms (design choices, expected to resist DROP) from
    # aspirational/unverified claims (should be testable but aren't).
    # Axioms get lower score — being stuck is their nature, not a defect.
    for p in phil_claims:
        grounding = p.get("grounding", "").lower()
        claim_type = p.get("type", "").lower()
        if grounding in ("aspirational", "unverified", "metaphor"):
            add(p["id"], "philosophy", "AXIOM-STUCK",
                0.6, f"Grounding: {grounding} — no path to observed/measured")
        elif grounding == "axiom" and claim_type == "axiom":
            # Axioms are design choices — flag at lower severity
            add(p["id"], "philosophy", "AXIOM-BY-DESIGN",
                0.15, f"Axiom (design choice) — expected to resist falsification")

    for b in beliefs:
        if b["evidence"] == "theorized":
            age = current_session - (b["last_tested_session"] or 0)
            score = min(1.0, 0.4 + age / 500)
            add(b["id"], "belief", "AXIOM-STUCK",
                score, f"Evidence: theorized for {age}+ sessions")

    # --- Signal 4: CONFIRM-ONLY challenges ---
    # Build lookup for PHIL claim types to discount axioms
    phil_types = {p["id"]: p.get("type", "").lower() for p in phil_claims}
    target_outcomes = defaultdict(list)
    for c in challenges:
        for tid in re.findall(r"(B-?\w+\d+|PHIL-\d+|P-\d+)", c["target"]):
            target_outcomes[tid].append(c["status"])
    for tid, outcomes in target_outcomes.items():
        resolved = [o for o in outcomes if o != "OPEN"]
        if len(resolved) >= 2:
            n_dropped = sum(1 for o in resolved if o == "DROPPED")
            if n_dropped == 0:
                is_axiom = phil_types.get(tid) == "axiom"
                if is_axiom:
                    # Axioms resist DROP by design — lower score, different label
                    score = 0.2 + 0.05 * len(resolved)
                    add(tid, "mixed", "CONFIRM-ONLY (axiom)",
                        score,
                        f"{len(resolved)} challenges, 0 DROPPED — "
                        f"axiom (design choice) — DROP resistance is expected")
                else:
                    score = 0.5 + 0.1 * len(resolved)
                    add(tid, "mixed", "CONFIRM-ONLY",
                        score,
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

    # --- Signal 7: HIGH-CITE-LOW-TEST (dynamic — SIG-82 meta-dogma fix) ---
    # Previously hardcoded 7 candidates chosen once at creation.
    # Now computed from actual Cites: headers across lesson corpus.
    confidences = sample_lesson_confidence()
    high_cite_candidates = _top_cited_lessons(top_n=15)
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

    # --- Signal 9: META-DOGMA — dogma finder's own hardcoded assumptions ---
    meta_dogmas = _detect_meta_dogma(current_session)
    findings.extend(meta_dogmas)

    # --- Signal 10: PROSE-STATUS-DRIFT (L-1411) ---
    # Detect claims where the status text contradicts the original prose.
    # E.g., prose says "without breaking" but status says "9 breakage events."
    # This is definitional drift mode 2: status evolves, claim text stays fixed.
    _contradiction_keywords = {
        "without breaking": ["breakage", "broken", "break", "deleted", "catastrophic"],
        "never hurt": ["violation", "incident", "deleted", "harm"],
        "always learn": ["decay", "blind-spot", "inaccessible"],
    }
    for p in phil_claims:
        # Check both inline statement and table claim short name
        stmt_lower = p.get("statement", "").lower()
        table_claim = p.get("table_claim", "").lower()
        combined_claim = stmt_lower + " " + table_claim
        status_text = p.get("status", "").lower()
        if not status_text:
            continue
        for phrase, contradictions in _contradiction_keywords.items():
            if phrase in combined_claim:
                found = [w for w in contradictions if w in status_text]
                if found:
                    add(p["id"], "philosophy", "PROSE-STATUS-DRIFT",
                        0.5,
                        f"Claim says '{phrase}' but status contains "
                        f"{found[:3]} — definitional drift (L-1241)")
                    break

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


def _detect_meta_dogma(current_session: int) -> list[dict]:
    """Detect dogma within the dogma finder itself (SIG-82: self-application).

    The dogma system has hardcoded assumptions that are never tested:
    - Signal weights (0.5, 0.7, 0.8, etc.) chosen once, never validated
    - HIGH-CITE-LOW-TEST candidate list is manually curated
    - SELF-REFERENTIAL detection uses a naive keyword regex
    - Threshold 0.6 for "high dogma" is arbitrary
    - FOUNDING-ERA cutoff at S100/P-030 is never updated
    """
    findings = []
    meta_items = [
        {
            "id": "DOGMA-WEIGHTS",
            "signal": "META-DOGMA",
            "score": 0.5,
            "detail": "8 signal weights hardcoded at creation (S500/S505), never empirically validated",
            "kind": "meta",
        },
        {
            "id": "DOGMA-CANDIDATES",
            "signal": "META-DOGMA",
            "score": 0.1,  # Reduced: now dynamically computed (SIG-82 S506 fix)
            "detail": "HIGH-CITE-LOW-TEST now uses dynamic citation count (was 7 hardcoded IDs)",
            "kind": "meta",
        },
        {
            "id": "DOGMA-SELFREF",
            "signal": "META-DOGMA",
            "score": 0.4,
            "detail": "SELF-REFERENTIAL detection: 5-keyword regex — naive, never tested for false-positive rate",
            "kind": "meta",
        },
        {
            "id": "DOGMA-THRESHOLD",
            "signal": "META-DOGMA",
            "score": 0.3,
            "detail": "0.6 threshold for 'high dogma' was chosen once — no sensitivity analysis",
            "kind": "meta",
        },
    ]
    return meta_items


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Prescriptions — dogma detection → swarm action (SIG-82)
# ---------------------------------------------------------------------------

SIGNAL_PRESCRIPTIONS = {
    "UNCHALLENGED": "File a falsification challenge: find evidence that would DROP this claim",
    "STALE-TEST": "Retest with current data — run the test described in 'Falsified if'",
    "AXIOM-STUCK": "Define a concrete upgrade path: what observation would move grounding to 'measured'?",
    "AXIOM-BY-DESIGN": None,  # Expected behavior, no action needed
    "CONFIRM-ONLY": "Open adversarial lane (mode=falsification) targeting this claim specifically",
    "CONFIRM-ONLY (axiom)": "Review whether axiom status is correct — if empirical, reclassify",
    "SELF-REFERENTIAL": "Find ONE external data point that bears on this claim (non-swarm evidence)",
    "FOUNDING-ERA": "Revalidate against current swarm state (N>1200) — founding-era conditions may not hold",
    "HIGH-CITE-LOW-TEST": "Upgrade confidence: design and run a test, or downgrade citations",
    "REFINE-DRIFT": "Freeze language — next challenge must result in CONFIRMED or DROPPED, not REFINED",
    "META-DOGMA": "Empirically test this assumption: measure its effect on dogma rankings",
    "PROSE-STATUS-DRIFT": "Update claim prose to match evidence, or acknowledge the gap explicitly",
}


def prescribe(findings: list[dict], top_n: int = 5) -> list[dict]:
    """Generate concrete prescriptions for top dogma items."""
    prescriptions = []
    for item in findings[:top_n]:
        actions = []
        for s in item["signals"]:
            rx = SIGNAL_PRESCRIPTIONS.get(s["signal"])
            if rx:
                actions.append({"signal": s["signal"], "action": rx})
        if actions:
            prescriptions.append({
                "id": item["id"],
                "score": item["total_score"],
                "kind": item["kind"],
                "actions": actions,
            })
    return prescriptions


def print_report(findings: list[dict], top_n: int = 0,
                 show_prescriptions: bool = False):
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

    # Meta-dogma section
    meta = [f for f in findings if f["kind"] == "meta"]
    if meta:
        print(f"{'─'*70}")
        print("  META-DOGMA (dogma in the dogma system itself):")
        for item in meta:
            for s in item["signals"]:
                print(f"    ⟳ {item['id']:20s}  {s['detail']}")
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

    if show_prescriptions:
        rxs = prescribe(findings, top_n=5)
        if rxs:
            print(f"{'='*70}")
            print("  PRESCRIPTIONS — dogma → swarm action")
            print(f"{'='*70}")
            print()
            for rx in rxs:
                print(f"  {rx['id']} (score {rx['score']:.1f}, {rx['kind']}):")
                for a in rx["actions"]:
                    print(f"    → [{a['signal']}] {a['action']}")
                print()


def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    show_prescriptions = "--prescribe" in args
    top_n = 0
    if "--top" in args:
        idx = args.index("--top")
        if idx + 1 < len(args):
            top_n = int(args[idx + 1])

    findings = detect_dogma()

    if as_json:
        out = findings[:top_n] if top_n else findings
        if show_prescriptions:
            for item in out:
                rxs = prescribe([item], top_n=1)
                item["prescriptions"] = rxs[0]["actions"] if rxs else []
        print(json.dumps(out, indent=2))
    else:
        print_report(findings, top_n, show_prescriptions=show_prescriptions)


if __name__ == "__main__":
    main()
