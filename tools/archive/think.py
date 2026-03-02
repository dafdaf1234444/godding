#!/usr/bin/env python3
"""
think.py — swarm reasoning engine.

The swarm has 435+ lessons, 168+ principles, 17+ beliefs, 38+ frontiers.
But it cannot THINK with them. This tool provides:

  1. Knowledge retrieval:    "what do I know about X?"
  2. Hypothesis testing:     "does evidence support X?"
  3. Citation chain walking: "how does L-N connect to the rest?"
  4. Contradiction scan:     "where do I disagree with myself?"
  5. Gap analysis:           "what SHOULD I know about X?"

Addresses B1 known gap (semantic retrieval), GAP-1 (diagnostic-execution
bridge from L-496), and PCI improvement (evidence findability).

Usage:
    python3 tools/think.py "belief staleness"
    python3 tools/think.py --test "quality gates accelerate citation growth"
    python3 tools/think.py --chain L-492
    python3 tools/think.py --contradict
    python3 tools/think.py --gaps "context management"
    python3 tools/think.py --stale
"""

import argparse
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Use swarm_io if available, else fallback
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from swarm_io import REPO_ROOT, read_text, session_number
except ImportError:
    REPO_ROOT = Path(__file__).resolve().parent.parent

    def read_text(path):
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return ""

    def session_number():
        return 0


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _tokenize(text):
    """Extract lowercase tokens (>=3 chars) for matching."""
    return re.findall(r"[a-z][a-z0-9_-]{2,}", text.lower())


def load_lessons():
    """Parse all lesson files into structured records."""
    lessons = []
    lesson_dir = REPO_ROOT / "memory" / "lessons"
    if not lesson_dir.exists():
        return lessons
    for f in sorted(
        lesson_dir.glob("L-*.md"),
        key=lambda p: int(re.search(r"\d+", p.stem).group()),
    ):
        try:
            num = int(re.search(r"\d+", f.stem).group())
        except (AttributeError, ValueError):
            continue
        text = read_text(f)
        if not text:
            continue

        title_m = re.search(r"^#\s+L-\d+:\s*(.+)", text, re.M)
        title = title_m.group(1).strip() if title_m else f.stem

        session_m = re.search(r"Session:\s*S?(\d+)", text)
        session = int(session_m.group(1)) if session_m else 0

        conf_m = re.search(r"Confidence:\s*(\w+)", text)
        confidence = conf_m.group(1) if conf_m else "Unknown"

        cites_line = ""
        cites_m = re.search(r"Cites?:\s*(.+)", text)
        if cites_m:
            cites_line = cites_m.group(1)

        finding_m = re.search(
            r"##\s*Finding\s*\n(.+?)(?=\n##|\Z)", text, re.S
        )
        finding = finding_m.group(1).strip() if finding_m else ""

        rule_m = re.search(r"##\s*Rule\s*\n(.+?)(?=\n##|\Z)", text, re.S)
        rule = rule_m.group(1).strip() if rule_m else ""

        full_text = title + " " + finding + " " + rule
        tokens = _tokenize(full_text)

        lessons.append(
            {
                "id": f"L-{num}",
                "num": num,
                "title": title,
                "session": session,
                "confidence": confidence,
                "finding": finding,
                "rule": rule,
                "cited_L": set(re.findall(r"L-\d+", cites_line)),
                "cited_P": set(re.findall(r"P-\d+", cites_line)),
                "cited_B": set(re.findall(r"B-?\w+", cites_line)),
                "cited_ISO": set(re.findall(r"ISO-\d+", cites_line)),
                "cited_PHIL": set(re.findall(r"PHIL-\d+", cites_line)),
                "tokens": tokens,
                "text": full_text,
            }
        )
    return lessons


def load_principles():
    """Parse principles from PRINCIPLES.md."""
    principles = []
    p_path = REPO_ROOT / "memory" / "PRINCIPLES.md"
    if not p_path.exists():
        return principles
    text = read_text(p_path)
    # Skip header (before first ## section heading)
    first_section = text.find("\n## ")
    if first_section > 0:
        text = text[first_section:]
    for m in re.finditer(r"(P-(\d+))\s+([^|P\n]+)", text):
        pid = m.group(1)
        ptext = m.group(3).strip()
        if ptext and len(ptext) > 5:
            principles.append(
                {"id": pid, "text": ptext, "tokens": _tokenize(ptext)}
            )
    return principles


def load_beliefs():
    """Parse beliefs from DEPS.md."""
    beliefs = []
    b_path = REPO_ROOT / "beliefs" / "DEPS.md"
    if not b_path.exists():
        return beliefs
    text = read_text(b_path)
    for m in re.finditer(
        r"###\s+(B[\w-]+):\s*(.+?)(?=\n###|\Z)", text, re.S
    ):
        bid = m.group(1)
        block = m.group(2).strip()
        summary = block.split("\n")[0]
        last_m = re.search(r"Last tested.*?S(\d+)", block)
        if last_m:
            last_tested = int(last_m.group(1))
        elif re.search(r"Last tested", block):
            # Tested but session not recorded (early beliefs used dates)
            last_tested = 1  # sentinel: tested but unknown session
        else:
            last_tested = 0
        evidence_m = re.search(r"Evidence.*?:\s*(\w+)", block)
        evidence = evidence_m.group(1) if evidence_m else "unknown"
        beliefs.append(
            {
                "id": bid,
                "text": summary,
                "last_tested": last_tested,
                "evidence": evidence,
                "tokens": _tokenize(summary),
            }
        )
    return beliefs


def load_frontiers():
    """Parse frontier questions from FRONTIER.md."""
    frontiers = []
    f_path = REPO_ROOT / "tasks" / "FRONTIER.md"
    if not f_path.exists():
        return frontiers
    text = read_text(f_path)
    for m in re.finditer(
        r"- \*\*(F[\w-]+)\*\*:\s*(.+?)(?=\n- \*\*F|\n##|\Z)", text, re.S
    ):
        fid = m.group(1)
        ftext = m.group(2).strip()
        status = "OPEN"
        if "RESOLVED" in ftext:
            status = "RESOLVED"
        elif "PARTIAL" in ftext:
            status = "PARTIAL"
        first_line = ftext.split("\n")[0][:200]
        frontiers.append(
            {
                "id": fid,
                "text": first_line,
                "status": status,
                "tokens": _tokenize(ftext),
            }
        )
    return frontiers


# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------


def build_index(lessons, principles, beliefs, frontiers):
    """Build inverted index: token -> [(type, id, weight, text)]."""
    index = defaultdict(list)

    # IDF for lessons
    doc_freq = Counter()
    for L in lessons:
        for t in set(L["tokens"]):
            doc_freq[t] += 1
    n_docs = max(len(lessons), 1)

    for L in lessons:
        tf = Counter(L["tokens"])
        for token, count in tf.items():
            idf = math.log(n_docs / (1 + doc_freq[token]))
            weight = count * idf
            if weight > 0:
                index[token].append(("lesson", L["id"], weight, L["title"]))

    # Principles get a 2x boost (distilled knowledge)
    for P in principles:
        for t in set(P["tokens"]):
            index[t].append(("principle", P["id"], 2.0, P["text"][:100]))

    # Beliefs get a 3x boost (foundational claims)
    for B in beliefs:
        for t in set(B["tokens"]):
            index[t].append(("belief", B["id"], 3.0, B["text"][:100]))

    # Frontiers get 1.5x (open questions)
    for F in frontiers:
        for t in set(F["tokens"]):
            index[t].append(("frontier", F["id"], 1.5, F["text"][:100]))

    return index


# ---------------------------------------------------------------------------
# Reasoning modes
# ---------------------------------------------------------------------------


def query(query_text, index, top_n=15):
    """Retrieve knowledge relevant to a query, ranked by TF-IDF relevance."""
    tokens = _tokenize(query_text)
    if not tokens:
        return []
    scores = defaultdict(float)
    items = {}
    for token in tokens:
        for typ, kid, weight, text in index.get(token, []):
            key = (typ, kid)
            scores[key] += weight
            items[key] = text

    ranked = sorted(scores.items(), key=lambda x: -x[1])[:top_n]
    return [(typ, kid, items[(typ, kid)], scores[(typ, kid)])
            for (typ, kid), _ in ranked]


def test_hypothesis(hypothesis, lessons, index, top_n=20):
    """Test a hypothesis: find supporting, contradicting, neutral evidence."""
    results = query(hypothesis, index, top_n=top_n * 2)

    by_id = {L["id"]: L for L in lessons}
    supporting, contradicting, neutral = [], [], []

    neg_words = {"not", "no", "doesn't", "failed", "refuted", "wrong",
                 "false", "contradicts", "disproved", "never", "zero",
                 "reject", "invalid", "cannot", "broken"}
    pos_words = {"confirmed", "supports", "validated", "consistent",
                 "verified", "demonstrated", "works", "correct",
                 "successful", "proven", "effective", "achieved"}

    for typ, kid, text, score in results:
        if typ != "lesson":
            continue
        L = by_id.get(kid)
        if not L:
            continue
        content_tokens = set(_tokenize(L["finding"] + " " + L["rule"]))
        neg = len(content_tokens & neg_words)
        pos = len(content_tokens & pos_words)

        entry = {
            "id": kid, "title": L["title"],
            "confidence": L["confidence"], "score": score,
        }
        if score < 1.5:
            continue  # too weak to classify
        if neg > pos:
            contradicting.append(entry)
        elif pos > neg:
            supporting.append(entry)
        else:
            neutral.append(entry)

    return supporting[:top_n], contradicting[:top_n], neutral[:top_n]


def follow_chain(start_id, lessons, max_depth=3):
    """Walk citation graph forward and backward from a lesson."""
    by_id = {L["id"]: L for L in lessons}

    # Forward walk (what does start_id cite?)
    forward = []
    visited = set()
    queue = [(start_id, 0)]
    while queue:
        current, depth = queue.pop(0)
        if current in visited or depth > max_depth:
            continue
        visited.add(current)
        L = by_id.get(current)
        if not L:
            continue
        if depth > 0:
            forward.append((current, depth, L["title"]))
        for cited in L["cited_L"]:
            queue.append((cited, depth + 1))

    # Backward walk (what cites start_id?)
    backward = []
    for L in lessons:
        if start_id in L["cited_L"]:
            backward.append((L["id"], L["title"]))

    # Connected knowledge
    start = by_id.get(start_id, {})
    return {
        "forward": forward,
        "backward": backward,
        "principles": sorted(start.get("cited_P", set())),
        "beliefs": sorted(start.get("cited_B", set())),
        "isos": sorted(start.get("cited_ISO", set())),
        "phils": sorted(start.get("cited_PHIL", set())),
    }


def find_contradictions(lessons):
    """Find lessons citing same principle with mixed confidence levels."""
    by_principle = defaultdict(list)
    for L in lessons:
        for p in L["cited_P"]:
            by_principle[p].append(L)

    contradictions = []
    for pid, group in sorted(by_principle.items()):
        if len(group) < 2:
            continue
        confidences = {L["confidence"] for L in group}
        # Flag when a principle has both Measured/Observed AND Refuted/Theorized
        high = confidences & {"Measured", "Observed"}
        low = confidences & {"Refuted", "Theorized"}
        if high and low:
            contradictions.append({
                "principle": pid,
                "lessons": [(L["id"], L["confidence"], L["title"][:60])
                            for L in group],
                "high": high,
                "low": low,
            })
    return contradictions


def detect_gaps(topic, index, lessons, principles, frontiers, top_n=10):
    """Identify what knowledge is missing for a topic."""
    results = query(topic, index, top_n=40)
    found = defaultdict(list)
    for typ, kid, text, score in results:
        found[typ].append(kid)

    gaps = []
    if not found.get("lesson"):
        gaps.append("NO_LESSONS: No lessons found — uncharted territory.")
    elif len(found["lesson"]) < 3:
        gaps.append(
            f"SPARSE: Only {len(found['lesson'])} lessons. Low evidence density."
        )

    if found.get("lesson") and not found.get("principle"):
        gaps.append(
            "NO_PRINCIPLES: Lessons exist but no distilled principles. "
            "Compression opportunity."
        )

    if not found.get("frontier"):
        gaps.append("NO_FRONTIER: No open question. Consider filing one.")

    # Staleness check
    if found.get("lesson"):
        relevant = [L for L in lessons if L["id"] in found["lesson"]]
        if relevant:
            newest = max(L["session"] for L in relevant)
            oldest = min(L["session"] for L in relevant)
            if newest < 300:
                gaps.append(f"STALE: Newest lesson from S{newest}. Outdated?")
            if newest - oldest < 10 and len(relevant) > 2:
                gaps.append(
                    f"CLUSTERED: S{oldest}-S{newest}. Single burst, not sustained."
                )

    # Confidence check
    if found.get("lesson"):
        relevant = [L for L in lessons if L["id"] in found["lesson"]]
        theorized = sum(
            1 for L in relevant
            if L["confidence"] in ("Theorized", "Unknown")
        )
        if theorized > len(relevant) * 0.5:
            gaps.append(
                f"LOW_CONFIDENCE: {theorized}/{len(relevant)} lessons "
                f"Theorized/Unknown."
            )

    return gaps, results[:top_n]


def find_stale(beliefs, current_session, threshold=50):
    """Find beliefs not re-tested in >threshold sessions."""
    stale = []
    for B in beliefs:
        if B["last_tested"] == 0:
            gap = "never"
        elif B["last_tested"] == 1:
            gap = current_session  # tested early, session unknown
        else:
            gap = current_session - B["last_tested"]
        if gap == "never" or gap > threshold:
            stale.append({
                "id": B["id"],
                "text": B["text"][:80],
                "last_tested": B["last_tested"],
                "gap": gap,
                "evidence": B["evidence"],
            })
    return sorted(stale, key=lambda x: 0 if x["gap"] == "never"
                  else -x["gap"])


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

_ICONS = {"lesson": "L", "principle": "P", "belief": "B", "frontier": "F"}


def _banner(lessons, principles, beliefs, frontiers):
    return (
        f"=== THINK ({len(lessons)}L {len(principles)}P "
        f"{len(beliefs)}B {len(frontiers)}F) ===\n"
    )


def print_query(query_text, results):
    print(f'Query: "{query_text}"\n')
    if not results:
        print("  No results found.")
        return
    for typ, kid, text, score in results:
        icon = _ICONS[typ]
        print(f"  [{icon}] {kid:12s} ({score:5.1f})  {text[:78]}")


def print_hypothesis(hypothesis, supporting, contradicting, neutral):
    print(f'Hypothesis: "{hypothesis}"\n')
    if supporting:
        print(f"  SUPPORTING ({len(supporting)}):")
        for s in supporting[:7]:
            print(f"    + {s['id']} [{s['confidence']}] {s['title'][:65]}")
    if contradicting:
        print(f"\n  CONTRADICTING ({len(contradicting)}):")
        for c in contradicting[:7]:
            print(f"    - {c['id']} [{c['confidence']}] {c['title'][:65]}")
    if neutral:
        print(f"\n  NEUTRAL ({len(neutral)}):")
        for n in neutral[:5]:
            print(f"    ~ {n['id']} [{n['confidence']}] {n['title'][:65]}")

    total = len(supporting) + len(contradicting) + len(neutral)
    if total == 0:
        print("  NO EVIDENCE FOUND. Hypothesis is untested territory.")
        return

    ratio = len(supporting) / max(total, 1)
    if ratio > 0.6:
        verdict = "SUPPORTED"
    elif contradicting and ratio < 0.3:
        verdict = "UNSUPPORTED"
    elif contradicting:
        verdict = "CONTESTED"
    else:
        verdict = "INSUFFICIENT"

    n_label = "HIGH" if total > 5 else "MEDIUM" if total > 2 else "LOW"
    print(f"\n  Verdict: {verdict} "
          f"({len(supporting)}+ {len(contradicting)}- {len(neutral)}~)")
    print(f"  Evidence density: {n_label} (n={total})")


def print_chain(start_id, chain_data, by_id):
    L = by_id.get(start_id)
    if not L:
        print(f"  {start_id} not found.")
        return
    print(f"Chain: {start_id} — {L['title'][:70]}\n")

    if chain_data["forward"]:
        print(f"  CITES ({len(chain_data['forward'])} downstream):")
        for kid, depth, title in chain_data["forward"]:
            indent = "  " * depth
            print(f"    {indent}-> {kid} {title[:60]}")

    if chain_data["backward"]:
        print(f"\n  CITED BY ({len(chain_data['backward'])} upstream):")
        for kid, title in chain_data["backward"]:
            print(f"    <- {kid} {title[:60]}")

    for label, key in [("PRINCIPLES", "principles"), ("BELIEFS", "beliefs"),
                       ("ISOMORPHISMS", "isos"), ("PHILOSOPHY", "phils")]:
        if chain_data[key]:
            print(f"\n  {label}: {', '.join(chain_data[key])}")

    if not chain_data["forward"] and not chain_data["backward"]:
        print("  ISOLATED: No citation connections. Sink node.")


def print_contradictions(contradictions):
    if not contradictions:
        print("  No contradictions detected.")
        return
    print(f"  CONTRADICTIONS ({len(contradictions)}):\n")
    for c in contradictions[:15]:
        print(f"  {c['principle']}: mixed {c['high']} vs {c['low']}")
        for kid, conf, title in c["lessons"]:
            print(f"    {kid} [{conf}] {title}")
        print()


def print_gaps(topic, gaps, results):
    print(f'Gap analysis: "{topic}"\n')
    if gaps:
        print("  GAPS:")
        for g in gaps:
            print(f"    ! {g}")
        print()
    if results:
        print("  EXISTING KNOWLEDGE:")
        for typ, kid, text, score in results:
            icon = _ICONS[typ]
            print(f"    [{icon}] {kid:12s} ({score:5.1f})  {text[:68]}")


def print_stale(stale_beliefs):
    if not stale_beliefs:
        print("  All beliefs recently tested.")
        return
    print(f"  STALE BELIEFS ({len(stale_beliefs)}):\n")
    for b in stale_beliefs:
        gap_str = b["gap"] if b["gap"] == "never" else f"{b['gap']}s ago"
        print(f"  {b['id']:6s} [{b['evidence']:10s}] "
              f"(last: S{b['last_tested']}, {gap_str})")
        print(f"         {b['text']}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Swarm reasoning engine — think with your own knowledge"
    )
    parser.add_argument(
        "query", nargs="?", help="Topic to retrieve knowledge about"
    )
    parser.add_argument(
        "--test", metavar="HYP", help="Test a hypothesis against evidence"
    )
    parser.add_argument(
        "--chain", metavar="L-NNN", help="Follow citation chain from a lesson"
    )
    parser.add_argument(
        "--contradict", action="store_true", help="Find internal contradictions"
    )
    parser.add_argument(
        "--gaps", metavar="TOPIC", help="Identify knowledge gaps for a topic"
    )
    parser.add_argument(
        "--stale", action="store_true",
        help="Find beliefs not re-tested in >50 sessions",
    )
    parser.add_argument(
        "--top", type=int, default=15, help="Max results (default: 15)"
    )
    args = parser.parse_args()

    if not any([args.query, args.test, args.chain,
                args.contradict, args.gaps, args.stale]):
        parser.print_help()
        sys.exit(1)

    # Load all knowledge
    lessons = load_lessons()
    principles = load_principles()
    beliefs = load_beliefs()
    frontiers = load_frontiers()
    index = build_index(lessons, principles, beliefs, frontiers)

    print(_banner(lessons, principles, beliefs, frontiers))

    if args.query:
        results = query(args.query, index, args.top)
        print_query(args.query, results)

    elif args.test:
        sup, con, neu = test_hypothesis(args.test, lessons, index, args.top)
        print_hypothesis(args.test, sup, con, neu)

    elif args.chain:
        chain_data = follow_chain(args.chain, lessons)
        by_id = {L["id"]: L for L in lessons}
        print_chain(args.chain, chain_data, by_id)

    elif args.contradict:
        contradictions = find_contradictions(lessons)
        print_contradictions(contradictions)

    elif args.gaps:
        gaps, results = detect_gaps(
            args.gaps, index, lessons, principles, frontiers, args.top
        )
        print_gaps(args.gaps, gaps, results)

    elif args.stale:
        cur = session_number()
        stale = find_stale(beliefs, cur)
        print_stale(stale)


if __name__ == "__main__":
    main()
