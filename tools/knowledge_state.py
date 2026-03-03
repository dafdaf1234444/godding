#!/usr/bin/env python3
"""Classify swarm knowledge into epistemological states (L-707, F-META10).

Five states: MUST-KNOW, ACTIVE, SHOULD-KNOW, DECAYED, BLIND-SPOT.
Produces per-domain profiles, transition diagnostics, and hypothesis tests.

Usage:
  python3 tools/knowledge_state.py           # full report
  python3 tools/knowledge_state.py --domain meta  # single domain
  python3 tools/knowledge_state.py --json    # machine-readable + experiment JSON
  python3 tools/knowledge_state.py --dispatch  # dispatch-integrated scoring
  python3 tools/knowledge_state.py -v        # verbose per-item details
"""

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from swarm_io import REPO_ROOT, read_text, lesson_paths, session_number

# --- Configuration ---
STALE_WINDOW = 50  # sessions without citation → DECAYED candidate
BOOT_FILES = [
    "beliefs/CORE.md", "memory/INDEX.md", "SWARM.md",
    "CLAUDE.md", "AGENTS.md", "GEMINI.md",
]
ACTIVE_TOOL_DIR = REPO_ROOT / "tools"
DOMAINS_DIR = REPO_ROOT / "domains"

# Canonical domain names (from domains/ directory)
CANONICAL_DOMAINS: set[str] = set()


def _load_canonical_domains() -> set[str]:
    """Load canonical domain names from domains/ directory."""
    global CANONICAL_DOMAINS
    if CANONICAL_DOMAINS:
        return CANONICAL_DOMAINS
    if DOMAINS_DIR.exists():
        CANONICAL_DOMAINS = {
            d.name for d in DOMAINS_DIR.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        }
    return CANONICAL_DOMAINS


def normalize_domain(raw: str) -> str:
    """Normalize a raw domain string to a canonical domain name.

    Handles: 'meta/coordination' → 'meta', 'ai (f-ai3)' → 'ai',
    'nk complexity' → 'nk-complexity', 'finance -->' → 'finance',
    'brain (f122 extension)' → 'brain'.
    """
    if not raw or raw == "unknown":
        return "unknown"

    # Strip parenthetical annotations: 'ai (f-ai3)' → 'ai'
    cleaned = re.sub(r"\s*\([^)]*\)$", "", raw).strip()
    # Strip trailing arrows: 'finance -->' → 'finance'
    cleaned = re.sub(r"\s*-+>.*$", "", cleaned).strip()
    # Strip HTML comments
    cleaned = re.sub(r"<!--.*?-->", "", cleaned).strip()
    # Take first path component: 'meta/coordination' → 'meta'
    if "/" in cleaned:
        cleaned = cleaned.split("/")[0].strip()
    # Normalize whitespace to hyphens: 'nk complexity' → 'nk-complexity'
    cleaned = re.sub(r"\s+", "-", cleaned).strip().lower()
    # Strip backticks and other markup
    cleaned = cleaned.strip("`*_ ")

    # Match against canonical domains
    canonical = _load_canonical_domains()
    if cleaned in canonical:
        return cleaned

    # Try partial match (prefix)
    for cd in canonical:
        if cleaned.startswith(cd) or cd.startswith(cleaned):
            return cd

    # Try fuzzy: 'distributed systems' → 'distributed-systems'
    normalized = cleaned.replace(" ", "-")
    if normalized in canonical:
        return normalized

    return cleaned if cleaned else "unknown"


def parse_lesson(path: Path, current_session: int) -> dict:
    """Parse a lesson file into structured data."""
    text = read_text(path)
    num_m = re.search(r"\d+", path.stem)
    if not num_m:
        return None
    num = int(num_m.group())
    title_m = re.search(r"^#\s+L-\d+[:\s]*(.+)", text, re.M)

    # Session: try multiple formats (plain or **bold** Markdown)
    session_m = re.search(r"\*{0,2}Session\*{0,2}:\s*S?(\d+)", text)
    # Alt format: e.g. HTML comment '<!-- lesson: L-706 | session: 375 | ... -->'
    if not session_m:
        session_m = re.search(r"session:\s*S?(\d+)", text)
    session = int(session_m.group(1)) if session_m else 0
    age = current_session - session if session else current_session

    # Domain: plain or **bold** Markdown, or HTML comment
    domain_m = re.search(r"\*{0,2}[Dd]omain\*{0,2}:\s*([^\n|]+)", text)
    if not domain_m:
        domain_m = re.search(r"\|\s*domain:\s*([^|>\n]+)", text)

    conf_m = re.search(r"\*{0,2}Confidence\*{0,2}:\s*(\w+)", text, re.I)
    cites_m = re.search(r"^\*{0,2}Cites?\*{0,2}:\s*(.+)", text, re.M)

    # Citations from Cites: header
    cited_lessons = set()
    if cites_m:
        cited_lessons = {int(x) for x in re.findall(r"\bL-(\d+)\b", cites_m.group(1))
                         if int(x) != num}

    # Also scan body for implicit L-refs not in Cites: header
    body_refs = {int(x) for x in re.findall(r"\bL-(\d+)\b", text) if int(x) != num}
    all_citations = cited_lessons | body_refs

    raw_domain = domain_m.group(1).strip().split(",")[0].strip() if domain_m else "unknown"
    domain = normalize_domain(raw_domain)

    return {
        "id": f"L-{num}",
        "num": num,
        "title": title_m.group(1).strip() if title_m else "",
        "session": session,
        "age": age,
        "domain": domain,
        "confidence": conf_m.group(1).lower() if conf_m else "unknown",
        "cites": all_citations,
        "type": "lesson",
    }


def parse_principles(current_session: int, lesson_sessions: dict[int, int]) -> list[dict]:
    """Parse principles from PRINCIPLES.md. Uses lesson_sessions to approximate age."""
    text = read_text(REPO_ROOT / "memory" / "PRINCIPLES.md")
    results = []
    seen = set()
    # Match P-NNN anywhere: 'P-008 text | P-011 text' or '**P-008** text'
    for m in re.finditer(r"\bP-(\d+)\b\s+([^|*\n(]+)", text):
        pnum = int(m.group(1))
        if pnum in seen:
            continue
        seen.add(pnum)
        ptext = m.group(2).strip()
        pid = f"P-{pnum}"
        # Approximate session from cited lessons in the surrounding text
        # Look at the full line for L-refs
        line_start = text.rfind("\n", 0, m.start()) + 1
        line_end = text.find("\n", m.end())
        line = text[line_start:line_end if line_end != -1 else len(text)]
        lesson_refs = [int(x) for x in re.findall(r"\bL-(\d+)\b", line)]
        session = 0
        if lesson_refs:
            sessions = [lesson_sessions.get(lr, 0) for lr in lesson_refs]
            session = max(s for s in sessions if s > 0) if any(s > 0 for s in sessions) else 0
        age = current_session - session if session else current_session
        results.append({
            "id": pid,
            "num": pnum,
            "title": ptext[:80],
            "session": session,
            "age": age,
            "domain": "cross-domain",
            "confidence": "distilled",
            "cites": set(),
            "type": "principle",
        })
    return results


def parse_beliefs(current_session: int) -> list[dict]:
    """Parse beliefs from DEPS.md."""
    text = read_text(REPO_ROOT / "beliefs" / "DEPS.md")
    results = []
    for m in re.finditer(r"###\s+(B[\w-]+):\s*(.+?)(?=\n###|\Z)", text, re.S):
        bid = m.group(1)
        block = m.group(2).strip()
        summary = block.split("\n")[0]
        last_m = re.search(r"Last tested.*?S(\d+)", block)
        last_tested = int(last_m.group(1)) if last_m else 0
        evidence_m = re.search(r"Evidence.*?:\s*(\w+)", block)
        evidence = evidence_m.group(1).lower() if evidence_m else "unknown"

        results.append({
            "id": bid,
            "num": 0,
            "title": summary[:80],
            "session": last_tested,
            "age": current_session - last_tested if last_tested else current_session,
            "domain": "meta",
            "confidence": evidence,
            "cites": set(),
            "type": "belief",
        })
    return results


def find_must_know_refs() -> set[str]:
    """Find knowledge IDs referenced by boot files and active tools."""
    refs = set()
    # Boot files
    for rel in BOOT_FILES:
        text = read_text(REPO_ROOT / rel)
        refs.update(re.findall(r"\bL-\d+\b", text))
        refs.update(re.findall(r"\bP-\d+\b", text))
        refs.update(re.findall(r"\bB\d+\b", text))

    # Active tools (non-archived)
    archive_dir = REPO_ROOT / "tools" / "archive"
    for py in ACTIVE_TOOL_DIR.glob("*.py"):
        if archive_dir in py.parents:
            continue
        text = read_text(py)
        refs.update(re.findall(r"\bL-\d+\b", text))
        refs.update(re.findall(r"\bP-\d+\b", text))
    return refs


def find_indexed_refs() -> set[str]:
    """Find knowledge IDs referenced in INDEX.md (retrieval test)."""
    text = read_text(REPO_ROOT / "memory" / "INDEX.md")
    refs = set()
    refs.update(re.findall(r"\bL-\d+\b", text))
    refs.update(re.findall(r"\bP-\d+\b", text))
    return refs


def build_citation_index(lessons: list[dict]) -> dict[str, set[int]]:
    """Build reverse citation index: which sessions cite each L/P/B ID."""
    cited_by_session = defaultdict(set)
    for lsn in lessons:
        # L→L citations
        for cited_num in lsn["cites"]:
            cited_by_session[f"L-{cited_num}"].add(lsn["session"])
    # Also scan lesson files for P-NNN and B-NNN references
    for path in lesson_paths():
        text = read_text(path)
        num_m = re.search(r"\d+", path.stem)
        if not num_m:
            continue
        session_m = re.search(r"[Ss]ession:\s*S?(\d+)", text)
        session = int(session_m.group(1)) if session_m else 0
        for p_ref in re.findall(r"\bP-(\d+)\b", text):
            cited_by_session[f"P-{p_ref}"].add(session)
        for b_ref in re.findall(r"\bB(\d+)\b", text):
            cited_by_session[f"B{b_ref}"].add(session)
    return cited_by_session


def classify(item: dict, must_know_refs: set, cited_by_session: dict,
             indexed_refs: set, current_session: int) -> str:
    """Classify a knowledge item into an epistemological state."""
    item_id = item["id"]

    # 1. MUST-KNOW: referenced by boot/tools
    if item_id in must_know_refs:
        return "MUST-KNOW"

    # 2. For beliefs: use last-tested + evidence
    if item["type"] == "belief":
        if item["age"] <= STALE_WINDOW:
            return "ACTIVE"
        return "DECAYED"

    # 3. Check citation recency
    citing_sessions = cited_by_session.get(item_id, set())
    recent_citations = {s for s in citing_sessions if s > current_session - STALE_WINDOW}

    # 4. ACTIVE: created recently OR cited recently
    if item["age"] <= STALE_WINDOW or len(recent_citations) > 0:
        return "ACTIVE"

    # 5. BLIND-SPOT: old, never cited, not indexed, not in any tool/boot ref
    if (item["age"] > STALE_WINDOW
            and len(citing_sessions) == 0
            and item_id not in indexed_refs):
        return "BLIND-SPOT"

    # 6. DECAYED: old + no recent citations
    return "DECAYED"


def count_frontiers_per_domain() -> dict[str, int]:
    """Count open frontiers per domain (= SHOULD-KNOW count)."""
    counts = defaultdict(int)
    if DOMAINS_DIR.exists():
        for domain_dir in DOMAINS_DIR.iterdir():
            if not domain_dir.is_dir():
                continue
            frontier_file = domain_dir / "tasks" / "FRONTIER.md"
            if frontier_file.exists():
                text = read_text(frontier_file)
                # Only count in ## Active section
                active_section = text.split("## Dead Ends")[0] if "## Dead Ends" in text else text
                active_section = active_section.split("## Resolved")[0] if "## Resolved" in active_section else active_section
                active_section = active_section.split("## Legacy")[0] if "## Legacy" in active_section else active_section
                count = len(re.findall(r"^- \*\*F-", active_section, re.M))
                counts[domain_dir.name] = count

    # Global frontier file
    global_frontier = read_text(REPO_ROOT / "tasks" / "FRONTIER.md")
    active_part = global_frontier.split("## Resolved")[0] if "## Resolved" in global_frontier else global_frontier
    counts["global"] = len(re.findall(r"^- \*\*F\d+\*\*", active_part, re.M))
    return counts


def test_hypotheses(all_items: list[dict], domain_profiles: dict,
                    frontiers_per_domain: dict, revival_rate: float,
                    cited_by_session: dict, current_session: int) -> list[dict]:
    """Test F-META10 hypotheses against data."""
    results = []

    # (a) SHOULD-KNOW > ACTIVE in ≥30% of domains
    canonical = _load_canonical_domains()
    domains_with_both = 0
    should_exceeds_active = 0
    for domain in canonical:
        sk = domain_profiles.get(domain, {}).get("SHOULD-KNOW", 0) + frontiers_per_domain.get(domain, 0)
        ac = domain_profiles.get(domain, {}).get("ACTIVE", 0)
        if sk > 0 or ac > 0:
            domains_with_both += 1
            if sk > ac:
                should_exceeds_active += 1
    pct_a = (should_exceeds_active / domains_with_both * 100) if domains_with_both > 0 else 0
    results.append({
        "hypothesis": "SHOULD-KNOW > ACTIVE in ≥30% of domains",
        "result": f"{should_exceeds_active}/{domains_with_both} domains ({pct_a:.1f}%)",
        "pass": pct_a >= 30,
        "threshold": "≥30%",
    })

    # (b) DECAYED→ACTIVE transitions < 1% per session
    # Revival rate is cumulative over STALE_WINDOW. Per-session = rate / STALE_WINDOW
    per_session_revival = revival_rate / STALE_WINDOW if STALE_WINDOW > 0 else 0
    results.append({
        "hypothesis": "DECAYED→ACTIVE transitions < 1% per session",
        "result": f"{per_session_revival:.2f}% per session (cumulative {revival_rate:.1f}% over {STALE_WINDOW}s window)",
        "pass": per_session_revival < 1.0,
        "threshold": "<1%",
    })

    # (c) Dispatch incorporating knowledge-state profiles changes top-5 in ≥2/5 cases
    # Compute knowledge-gap score per domain: (SHOULD-KNOW + BLIND-SPOT) / total
    gap_scores = {}
    for domain in canonical:
        profile = domain_profiles.get(domain, {})
        sk = profile.get("SHOULD-KNOW", 0) + frontiers_per_domain.get(domain, 0)
        bs = profile.get("BLIND-SPOT", 0)
        total = sum(profile.values()) + frontiers_per_domain.get(domain, 0)
        if total > 0:
            gap_scores[domain] = (sk + bs) / total
        else:
            gap_scores[domain] = 1.0  # completely unknown = max gap

    # Sort by gap score descending
    gap_ranked = sorted(gap_scores.items(), key=lambda x: x[1], reverse=True)
    top5_gap = [d for d, _ in gap_ranked[:5]]

    # Compare with UCB1 top-5 (from dispatch_optimizer)
    try:
        out = subprocess.check_output(
            [sys.executable, str(ACTIVE_TOOL_DIR / "dispatch_optimizer.py"),
             "--json", "--mode", "ucb1"],
            cwd=str(REPO_ROOT), stderr=subprocess.DEVNULL, text=True, timeout=30
        )
        ucb1_data = json.loads(out)
        ucb1_top5 = [d.get("domain", "") for d in ucb1_data[:5]] if isinstance(ucb1_data, list) else []
    except Exception:
        ucb1_top5 = []

    differences = len(set(top5_gap) - set(ucb1_top5))
    results.append({
        "hypothesis": "Knowledge-state profiles change top-5 dispatch in ≥2/5 cases",
        "result": f"{differences}/5 different (gap-ranked: {top5_gap[:5]}, UCB1: {ucb1_top5[:5]})",
        "pass": differences >= 2,
        "threshold": "≥2/5",
    })

    return results


def main():
    parser = argparse.ArgumentParser(description="Knowledge state classifier (L-707, F-META10)")
    parser.add_argument("--domain", help="Filter to specific domain")
    parser.add_argument("--json", action="store_true", help="JSON output + experiment artifact")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show per-item details")
    parser.add_argument("--dispatch", action="store_true", help="Show dispatch-integrated scoring")
    args = parser.parse_args()

    current_session = session_number()
    print(f"=== KNOWLEDGE STATE CLASSIFIER — S{current_session} ===\n")

    # Parse all knowledge
    raw_lessons = [parse_lesson(p, current_session) for p in lesson_paths()]
    lessons = [l for l in raw_lessons if l is not None]

    # Build lesson session lookup for principle age approximation
    lesson_sessions = {l["num"]: l["session"] for l in lessons}

    principles = parse_principles(current_session, lesson_sessions)
    beliefs = parse_beliefs(current_session)
    all_items = lessons + principles + beliefs

    # Build indices
    must_know_refs = find_must_know_refs()
    indexed_refs = find_indexed_refs()
    cited_by_session = build_citation_index(lessons)
    frontiers_per_domain = count_frontiers_per_domain()

    # Classify each item
    for item in all_items:
        item["state"] = classify(item, must_know_refs, cited_by_session,
                                 indexed_refs, current_session)

    # Filter by domain if requested
    display_items = all_items
    if args.domain:
        display_items = [i for i in all_items if args.domain.lower() in i.get("domain", "").lower()]

    # Aggregate by state
    state_counts = defaultdict(int)
    for item in display_items:
        state_counts[item["state"]] += 1

    # Add SHOULD-KNOW from frontiers
    if args.domain:
        total_should_know = frontiers_per_domain.get(args.domain, 0)
    else:
        total_should_know = sum(frontiers_per_domain.values())
    state_counts["SHOULD-KNOW"] = total_should_know

    # Global summary
    total = sum(state_counts.values())
    print("--- Global Knowledge State Distribution ---")
    for state in ["MUST-KNOW", "ACTIVE", "SHOULD-KNOW", "DECAYED", "BLIND-SPOT"]:
        count = state_counts.get(state, 0)
        pct = (count / total * 100) if total > 0 else 0
        bar = "\u2588" * int(pct / 2)
        print(f"  {state:12s}  {count:4d}  ({pct:5.1f}%)  {bar}")
    print(f"  {'TOTAL':12s}  {total:4d}")
    print()

    # Per-domain profiles (using all_items, not filtered)
    domain_profiles = defaultdict(lambda: defaultdict(int))
    for item in all_items:
        domain_profiles[item["domain"]][item["state"]] += 1

    # Add frontier counts to domain profiles
    for domain, fcount in frontiers_per_domain.items():
        domain_profiles[domain]["SHOULD-KNOW"] += fcount

    # Sort domains by total knowledge
    sorted_domains = sorted(domain_profiles.items(),
                            key=lambda x: sum(x[1].values()), reverse=True)

    # Filter to meaningful domains (total >= 3 or is canonical)
    canonical = _load_canonical_domains()
    filtered_domains = [(d, c) for d, c in sorted_domains
                        if sum(c.values()) >= 3 or d in canonical]

    print("--- Per-Domain Knowledge State Profiles ---")
    print(f"  {'Domain':28s} {'MUST':>5} {'ACTV':>5} {'SHLD':>5} {'DECY':>5} {'BLND':>5} {'Total':>6}  Diagnosis")
    print(f"  {'-'*28} {'-'*5} {'-'*5} {'-'*5} {'-'*5} {'-'*5} {'-'*6}  {'-'*25}")

    for domain, counts in filtered_domains:
        mk = counts.get("MUST-KNOW", 0)
        ac = counts.get("ACTIVE", 0)
        sk = counts.get("SHOULD-KNOW", 0)
        dc = counts.get("DECAYED", 0)
        bs = counts.get("BLIND-SPOT", 0)
        tot = mk + ac + sk + dc + bs
        if tot == 0:
            continue

        # Diagnosis
        decay_ratio = dc / tot
        if bs > 0:
            diagnosis = f"BLIND-SPOT: {bs} unreachable"
        elif decay_ratio > 0.5:
            diagnosis = "DECAY-HEAVY: needs revival"
        elif sk > ac and sk > 2:
            diagnosis = "EXPLORE-RICH: needs experiments"
        elif ac > 10 and dc < 3:
            diagnosis = "HEALTHY"
        elif mk > ac and mk > 3:
            diagnosis = "OPERATIONAL: infra-critical"
        elif tot <= 2:
            diagnosis = "NASCENT"
        else:
            diagnosis = "MIXED"

        marker = "*" if domain in canonical else " "
        print(f"  {marker}{domain:27s} {mk:5d} {ac:5d} {sk:5d} {dc:5d} {bs:5d} {tot:6d}  {diagnosis}")

    # Count domains not shown
    hidden = len(sorted_domains) - len(filtered_domains)
    if hidden > 0:
        print(f"  ... {hidden} small domains hidden (total < 3, not canonical)")
    print()

    # State transition diagnostics
    print("--- State Transition Diagnostics ---")
    active_items = [i for i in display_items if i["state"] == "ACTIVE"]
    decayed_items = [i for i in display_items if i["state"] == "DECAYED"]
    must_know_items = [i for i in display_items if i["state"] == "MUST-KNOW"]
    blind_items = [i for i in display_items if i["state"] == "BLIND-SPOT"]

    print(f"  ACTIVE items:    {len(active_items)} (avg age: {sum(i['age'] for i in active_items) / max(len(active_items), 1):.0f} sessions)")
    print(f"  DECAYED items:   {len(decayed_items)} (avg age: {sum(i['age'] for i in decayed_items) / max(len(decayed_items), 1):.0f} sessions)")
    print(f"  MUST-KNOW items: {len(must_know_items)}")
    print(f"  BLIND-SPOT items: {len(blind_items)}")
    print(f"  SHOULD-KNOW:     {total_should_know} open frontiers across {len(frontiers_per_domain)} domains")

    # DECAYED→ACTIVE revival rate
    revival_candidates = 0
    for item in display_items:
        if item["age"] > STALE_WINDOW:
            citing = cited_by_session.get(item["id"], set())
            recent = {s for s in citing if s > current_session - STALE_WINDOW}
            if len(recent) > 0:
                revival_candidates += 1

    old_items = len([i for i in display_items if i["age"] > STALE_WINDOW])
    revival_rate = (revival_candidates / old_items * 100) if old_items > 0 else 0
    print(f"  Revival rate:    {revival_candidates}/{old_items} old items recently cited ({revival_rate:.1f}%)")
    print()

    # F-META10 hypothesis tests
    print("--- F-META10 Hypothesis Tests ---")
    hypotheses = test_hypotheses(
        all_items, domain_profiles, frontiers_per_domain,
        revival_rate, cited_by_session, current_session
    )
    for h in hypotheses:
        status = "PASS" if h["pass"] else "FAIL"
        print(f"  [{status}] {h['hypothesis']}")
        print(f"        {h['result']}")
    print()

    # Verbose: show specific items
    if args.verbose:
        print("--- MUST-KNOW Items ---")
        for item in sorted(must_know_items, key=lambda x: x["id"]):
            print(f"  {item['id']:10s} {item['type']:10s} {item['domain']:20s} {item['title'][:50]}")
        print()

        if blind_items:
            print("--- BLIND-SPOT Items ---")
            for item in sorted(blind_items, key=lambda x: x["age"], reverse=True):
                print(f"  {item['id']:10s} age={item['age']:3d}s  {item['domain']:20s} {item['title'][:45]}")
            print()

        print("--- DECAYED Items (top 15 by age) ---")
        for item in sorted(decayed_items, key=lambda x: x["age"], reverse=True)[:15]:
            print(f"  {item['id']:10s} age={item['age']:3d}s  {item['domain']:20s} {item['title'][:45]}")
        print()

    # Dispatch integration
    if args.dispatch:
        print("--- Knowledge-Gap Dispatch Scoring ---")
        print(f"  {'Domain':28s} {'Gap%':>6} {'SHLD':>5} {'BLND':>5} {'DECY':>5}  Action")
        print(f"  {'-'*28} {'-'*6} {'-'*5} {'-'*5} {'-'*5}  {'-'*30}")
        gap_scores = []
        for domain in canonical:
            profile = domain_profiles.get(domain, {})
            sk = profile.get("SHOULD-KNOW", 0) + frontiers_per_domain.get(domain, 0)
            bs = profile.get("BLIND-SPOT", 0)
            dc = profile.get("DECAYED", 0)
            total = sum(profile.values()) + frontiers_per_domain.get(domain, 0)
            gap = (sk + bs) / total if total > 0 else 1.0
            gap_scores.append((domain, gap, sk, bs, dc, total))
        gap_scores.sort(key=lambda x: x[1], reverse=True)
        for domain, gap, sk, bs, dc, total in gap_scores[:15]:
            if total == 0:
                action = "NEW: no knowledge yet"
            elif bs > 0:
                action = "BLIND-SPOT: needs external input"
            elif gap > 0.5:
                action = "EXPLORE: high frontier density"
            elif dc > sk:
                action = "REVIVE: decay exceeds questions"
            else:
                action = "MAINTAIN"
            print(f"  {domain:28s} {gap*100:5.1f}% {sk:5d} {bs:5d} {dc:5d}  {action}")
        print()

    # JSON output
    if args.json:
        output = {
            "session": current_session,
            "stale_window": STALE_WINDOW,
            "global_states": dict(state_counts),
            "domain_profiles": {
                d: dict(c) for d, c in domain_profiles.items()
                if sum(c.values()) >= 2 or d in canonical
            },
            "revival_rate": revival_rate,
            "revival_per_session": revival_rate / STALE_WINDOW if STALE_WINDOW > 0 else 0,
            "total_items": len(all_items),
            "total_lessons": len(lessons),
            "total_principles": len(principles),
            "total_beliefs": len(beliefs),
            "frontier_count": total_should_know,
            "frontiers_per_domain": dict(frontiers_per_domain),
            "hypotheses": hypotheses,
            "blind_spots": [
                {"id": i["id"], "domain": i["domain"], "title": i["title"][:60], "age": i["age"]}
                for i in all_items if i["state"] == "BLIND-SPOT"
            ],
        }
        json_path = REPO_ROOT / "experiments" / "meta" / f"knowledge-state-s{current_session}.json"
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(output, indent=2) + "\n")
        print(f"JSON written to {json_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
