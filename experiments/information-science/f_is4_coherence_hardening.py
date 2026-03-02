#!/usr/bin/env python3
"""F-IS4 Coherence Hardening — measures self-knowledge coherence in concurrent DOMEX.

Five measurements:
1. Merge collision rate (same-domain concurrent lanes)
2. Cross-domain transfer rate (citations across domain boundaries)
3. INDEX.md bucket overflow (coherence degradation proxy)
4. Numerical claim drift (stale numbers in FRONTIER/NEXT)
5. Dark citation mass (body L-NNN refs not in Cites: header)

Output: experiments/information-science/f-is4-coherence-hardening-s389.json
"""

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
LANES_FILE = REPO / "tasks" / "SWARM-LANES.md"
LANES_ARCHIVE = REPO / "tasks" / "SWARM-LANES-ARCHIVE.md"
LESSONS_DIR = REPO / "memory" / "lessons"
INDEX_FILE = REPO / "memory" / "INDEX.md"
FRONTIER_FILE = REPO / "tasks" / "FRONTIER.md"
NEXT_FILE = REPO / "tasks" / "NEXT.md"
OUTPUT_FILE = REPO / "experiments" / "information-science" / "f-is4-coherence-hardening-s389.json"

# From tools/dispatch_optimizer.py
LANE_ABBREV_TO_DOMAIN = {
    "NK": "nk-complexity", "LNG": "linguistics", "EXP": "expert-swarm",
    "STAT": "statistics", "PHI": "philosophy", "CTX": "meta", "MECH": "meta",
    "FLD": "fluid-dynamics", "BRN": "brain", "HLP": "helper-swarm",
    "ECO": "economy", "PHY": "physics", "SCI": "evaluation", "EVO": "evolution",
    "DNA": "meta", "IS": "information-science", "HS": "human-systems",
    "COMP": "competitions", "INFO": "information-science",
    "META": "meta", "SP": "stochastic-processes", "EMP": "empathy",
    "AI": "ai", "CON": "conflict", "CONFLICT": "conflict",
    "CAT": "catastrophic-risks", "DS": "distributed-systems",
    "FIN": "finance", "GOV": "governance", "EVAL": "evaluation",
    "FRA": "fractals", "FRACTALS": "fractals", "GT": "graph-theory",
    "GTH": "graph-theory", "GAME": "gaming", "GAMING": "gaming",
    "SEC": "security", "SECURITY": "security",
    "GUE": "guesstimates", "GAM": "game-theory", "PSY": "psychology",
    "SOC": "social-media", "STR": "strategy", "QC": "quality",
    "QUALITY": "quality", "OR": "operations-research", "OPS": "operations-research",
    "FARMING": "farming", "FAR": "farming", "COORD": "meta", "HUMAN": "human-systems",
    "INFOFLOW": "information-science", "INFRA": "meta", "GEN": "meta",
    "DREAM": "dream", "BRAIN": "brain", "ECON": "economy", "ECONOMY": "economy",
    "EMPATHY": "empathy", "EVOLUTION": "evolution", "EXPERT": "expert-swarm",
    "AGENT": "meta", "CT": "meta", "CTL": "control-theory",
    "CC": "cryptocurrency", "CRY": "cryptography", "CRYPTO": "cryptocurrency",
    "CRYPTOGRAPHY": "cryptography",
    "PRO": "protocol-engineering", "README": "meta",
    "SCHED": "meta", "PRIORITY": "meta", "UNIVERSALITY": "meta",
    "PERSONALITY": "psychology", "IC": "security",
}


def _domain_from_lane_id(lane_id: str) -> str | None:
    """Extract domain from a lane ID like DOMEX-META-S378."""
    m = re.match(r"DOMEX-([A-Z]+)\d*-S\d+", lane_id)
    if m:
        return LANE_ABBREV_TO_DOMAIN.get(m.group(1))
    return None


def _domain_from_etc(etc: str) -> str | None:
    """Extract domain from the Etc field's focus= value."""
    fm = re.search(r"focus=(?:domains/)?([a-z0-9-]+)", etc)
    if fm and fm.group(1) not in ("global", ""):
        return fm.group(1)
    return None


def _parse_session(sess_str: str) -> int | None:
    """Extract session number from a session column like 'S378' or '378'."""
    m = re.search(r"S?(\d+)", sess_str)
    return int(m.group(1)) if m else None


def _parse_lane_rows(filepath: Path) -> list[dict]:
    """Parse lane log rows from a SWARM-LANES file into structured records."""
    rows = []
    try:
        text = filepath.read_text(encoding="utf-8")
    except FileNotFoundError:
        return rows

    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cols = [c.strip() for c in line.split("|")]
        # Expect at least 13 columns (date through notes) after split
        if len(cols) < 12:
            continue
        # Skip header rows
        if cols[1].startswith("Date") or cols[1].startswith("---"):
            continue

        lane_id = cols[2] if len(cols) > 2 else ""
        session_str = cols[3] if len(cols) > 3 else ""
        etc = cols[10] if len(cols) > 10 else ""
        status = cols[11].strip() if len(cols) > 11 else ""
        notes = cols[12] if len(cols) > 12 else ""

        if status not in ("MERGED", "ABANDONED", "ACTIVE", "CLAIMED", "BLOCKED", "READY"):
            continue

        domain = _domain_from_lane_id(lane_id)
        if not domain:
            domain = _domain_from_etc(etc)

        session = _parse_session(session_str)

        rows.append({
            "lane_id": lane_id,
            "domain": domain,
            "session": session,
            "status": status,
            "notes": notes,
            "etc": etc,
        })
    return rows


# ---------------------------------------------------------------------------
# 1. Merge collision rate
# ---------------------------------------------------------------------------
def measure_merge_collisions() -> dict:
    """Find same-domain concurrent lanes and count collision outcomes."""
    all_rows = _parse_lane_rows(LANES_FILE) + _parse_lane_rows(LANES_ARCHIVE)

    # Keep only closed DOMEX lanes with domain + session
    domex_rows = [
        r for r in all_rows
        if r["domain"] and r["session"] and r["status"] in ("MERGED", "ABANDONED")
        and r["lane_id"].startswith("DOMEX-")
    ]

    # Deduplicate: keep last status per lane_id
    latest = {}
    for r in domex_rows:
        lid = r["lane_id"]
        if lid not in latest or (r["session"] and latest[lid]["session"]
                                 and r["session"] >= latest[lid]["session"]):
            latest[lid] = r
    lanes = list(latest.values())

    # Group by domain, find session overlaps
    by_domain: dict[str, list[dict]] = defaultdict(list)
    for lane in lanes:
        by_domain[lane["domain"]].append(lane)

    collisions = []
    collision_merged = 0
    collision_abandoned = 0

    for domain, domain_lanes in by_domain.items():
        if len(domain_lanes) < 2:
            continue
        # Sort by session
        domain_lanes.sort(key=lambda x: x["session"] or 0)
        # Check pairs with overlapping sessions (same session number)
        session_groups: dict[int, list[dict]] = defaultdict(list)
        for lane in domain_lanes:
            if lane["session"]:
                session_groups[lane["session"]].append(lane)

        for sess, group in session_groups.items():
            if len(group) >= 2:
                for lane in group:
                    collisions.append({
                        "lane_id": lane["lane_id"],
                        "domain": domain,
                        "session": sess,
                        "status": lane["status"],
                    })
                    if lane["status"] == "MERGED":
                        collision_merged += 1
                    elif lane["status"] == "ABANDONED":
                        collision_abandoned += 1

    # Also check for adjacent-session overlaps (sessions within 1 of each other)
    adjacent_collisions = []
    for domain, domain_lanes in by_domain.items():
        if len(domain_lanes) < 2:
            continue
        domain_lanes.sort(key=lambda x: x["session"] or 0)
        for i in range(len(domain_lanes)):
            for j in range(i + 1, len(domain_lanes)):
                s_i = domain_lanes[i]["session"]
                s_j = domain_lanes[j]["session"]
                if s_i and s_j and abs(s_i - s_j) <= 1 and s_i != s_j:
                    adjacent_collisions.append({
                        "lane_a": domain_lanes[i]["lane_id"],
                        "lane_b": domain_lanes[j]["lane_id"],
                        "domain": domain,
                        "sessions": [s_i, s_j],
                        "statuses": [domain_lanes[i]["status"], domain_lanes[j]["status"]],
                    })

    total_lanes = len(lanes)
    collision_rate = len(collisions) / total_lanes if total_lanes else 0

    # Determine verdict
    if collision_rate < 0.05:
        verdict = "HEALTHY: low collision rate"
    elif collision_rate < 0.15:
        verdict = "WATCH: moderate collision rate"
    else:
        verdict = "DEGRADED: high collision rate — scope partitioning needed"

    return {
        "total_domex_lanes": total_lanes,
        "same_session_collisions": len(collisions),
        "collision_merged": collision_merged,
        "collision_abandoned": collision_abandoned,
        "adjacent_session_overlaps": len(adjacent_collisions),
        "collision_rate": round(collision_rate, 4),
        "collision_abandon_rate": round(
            collision_abandoned / len(collisions), 4
        ) if collisions else 0,
        "top_collision_domains": _top_collision_domains(collisions),
        "verdict": verdict,
    }


def _top_collision_domains(collisions: list[dict]) -> list[dict]:
    """Rank domains by collision count."""
    counts: dict[str, int] = defaultdict(int)
    for c in collisions:
        counts[c["domain"]] += 1
    return sorted(
        [{"domain": d, "count": n} for d, n in counts.items()],
        key=lambda x: -x["count"],
    )[:10]


# ---------------------------------------------------------------------------
# 2. Cross-domain transfer rate
# ---------------------------------------------------------------------------
def _get_lesson_domain(filepath: Path) -> str | None:
    """Extract domain from a lesson file by reading the header."""
    try:
        with open(filepath, encoding="utf-8") as f:
            lines = [f.readline() for _ in range(6)]
    except (FileNotFoundError, UnicodeDecodeError):
        return None

    for line in lines:
        # "Session: S390 | Domain: strategy | ..."
        m = re.search(r"Domain:\s*([a-zA-Z0-9_ /-]+?)(?:\s*\||$)", line)
        if m:
            raw = m.group(1).strip().lower().replace(" ", "-")
            # Normalize: take first part before '/'
            raw = raw.split("/")[0]
            # Map through abbreviation table
            return LANE_ABBREV_TO_DOMAIN.get(raw.upper(), raw)

        # Standalone "Domain: xxx" line
        m2 = re.match(r"Domain:\s*(.+)", line)
        if m2:
            raw = m2.group(1).strip().lower().split("|")[0].strip().replace(" ", "-")
            raw = raw.split("/")[0]
            return LANE_ABBREV_TO_DOMAIN.get(raw.upper(), raw)

    return None


def _get_lesson_cites_header(filepath: Path) -> list[str]:
    """Extract L-NNN references from the Cites: header line."""
    try:
        with open(filepath, encoding="utf-8") as f:
            lines = [f.readline() for _ in range(8)]
    except (FileNotFoundError, UnicodeDecodeError):
        return []

    for line in lines:
        if line.startswith("Cites:"):
            return re.findall(r"\bL-(\d+)\b", line)
    return []


def _get_lesson_body_refs(filepath: Path) -> list[str]:
    """Extract ALL L-NNN references from the full body of a lesson."""
    try:
        text = filepath.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError):
        return []
    return re.findall(r"\bL-(\d+)\b", text)


def measure_cross_domain_transfers() -> dict:
    """Measure cross-domain citation flow."""
    lesson_files = sorted(LESSONS_DIR.glob("L-*.md"))

    # Build domain map for all lessons
    domain_map: dict[str, str] = {}  # lesson_num -> domain
    for lf in lesson_files:
        m = re.match(r"L-(\d+)\.md", lf.name)
        if not m:
            continue
        num = m.group(1)
        dom = _get_lesson_domain(lf)
        if dom:
            domain_map[num] = dom

    total_citations = 0
    cross_domain_citations = 0
    domain_pairs: dict[tuple[str, str], int] = defaultdict(int)
    lessons_with_domain = 0
    lessons_without_domain = 0

    for lf in lesson_files:
        m = re.match(r"L-(\d+)\.md", lf.name)
        if not m:
            continue
        src_num = m.group(1)
        src_domain = domain_map.get(src_num)
        if not src_domain:
            lessons_without_domain += 1
            continue
        lessons_with_domain += 1

        cites = _get_lesson_cites_header(lf)
        for cited_num in cites:
            total_citations += 1
            cited_domain = domain_map.get(cited_num)
            if cited_domain and cited_domain != src_domain:
                cross_domain_citations += 1
                pair = tuple(sorted([src_domain, cited_domain]))
                domain_pairs[pair] += 1

    transfer_rate = cross_domain_citations / total_citations if total_citations else 0

    # Top domain pairs
    top_pairs = sorted(domain_pairs.items(), key=lambda x: -x[1])[:15]

    if transfer_rate > 0.30:
        verdict = "HEALTHY: strong cross-domain flow"
    elif transfer_rate > 0.15:
        verdict = "MODERATE: some cross-pollination"
    else:
        verdict = "SILOED: low cross-domain transfer — domain boundaries are walls"

    return {
        "total_citations_in_headers": total_citations,
        "cross_domain_citations": cross_domain_citations,
        "transfer_rate": round(transfer_rate, 4),
        "unique_domain_pairs": len(domain_pairs),
        "lessons_with_domain": lessons_with_domain,
        "lessons_without_domain": lessons_without_domain,
        "domain_coverage_pct": round(
            lessons_with_domain / (lessons_with_domain + lessons_without_domain) * 100, 1
        ) if (lessons_with_domain + lessons_without_domain) else 0,
        "top_transfer_pairs": [
            {"pair": list(p), "count": c} for p, c in top_pairs
        ],
        "verdict": verdict,
    }


# ---------------------------------------------------------------------------
# 3. INDEX.md bucket overflow
# ---------------------------------------------------------------------------
def measure_index_overflow() -> dict:
    """Count lines per ## heading section in INDEX.md."""
    try:
        text = INDEX_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {"error": "INDEX.md not found", "verdict": "ERROR"}

    buckets: dict[str, int] = {}
    current_bucket = None
    line_count = 0

    for line in text.splitlines():
        if line.startswith("## "):
            if current_bucket is not None:
                buckets[current_bucket] = line_count
            current_bucket = line.strip("# ").strip()
            line_count = 0
        else:
            line_count += 1

    if current_bucket is not None:
        buckets[current_bucket] = line_count

    overflow_buckets = {k: v for k, v in buckets.items() if v > 40}
    total_lines = sum(buckets.values())

    if not overflow_buckets:
        verdict = "HEALTHY: no bucket exceeds 40 lines"
    elif len(overflow_buckets) <= 2:
        verdict = "WATCH: 1-2 buckets overflowing — consider splitting"
    else:
        verdict = "DEGRADED: multiple buckets overflowing — retrieval suffers"

    return {
        "total_buckets": len(buckets),
        "total_lines": total_lines,
        "buckets": {k: v for k, v in sorted(buckets.items(), key=lambda x: -x[1])},
        "overflow_buckets": overflow_buckets,
        "overflow_count": len(overflow_buckets),
        "verdict": verdict,
    }


# ---------------------------------------------------------------------------
# 4. Numerical claim drift
# ---------------------------------------------------------------------------
def measure_numerical_drift() -> dict:
    """Sample numerical claims from FRONTIER.md and NEXT.md and verify them."""
    claims = []

    # Parse FRONTIER.md for numerical claims
    try:
        frontier_text = FRONTIER_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        frontier_text = ""

    try:
        next_text = NEXT_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        next_text = ""

    # Extract claims: look for state-summary lines like "692L 185P 20B 21F"
    # and specific metric patterns like "K_avg=2.09", "N sessions"
    claim_patterns = [
        # State summary: "NL NP NB NF" pattern
        (r"(\d{2,})L\s+\d+P\s+\d+B\s+\d+F", "lesson_count", next_text, "NEXT.md",
         lambda m: re.match(r"(\d+)L", m.group(0)).group(1)),
        (r"\d+L\s+(\d{2,})P\s+\d+B\s+\d+F", "principle_count", next_text, "NEXT.md",
         lambda m: m.group(1)),
        (r"\d+L\s+\d+P\s+(\d{1,})B\s+\d+F", "belief_count", next_text, "NEXT.md",
         lambda m: m.group(1)),
        (r"\d+L\s+\d+P\s+\d+B\s+(\d{1,})F", "frontier_count", next_text, "NEXT.md",
         lambda m: m.group(1)),
        # "21 active" in FRONTIER header
        (r"(\d+)\s+active", "frontier_count", frontier_text, "FRONTIER.md",
         lambda m: m.group(1)),
        # "389 sessions" (in frontier or NEXT)
        (r"(\d{3})\s+sessions", "session_count", frontier_text, "FRONTIER.md",
         lambda m: m.group(1)),
        (r"(\d{3})\s+sessions", "session_count", next_text, "NEXT.md",
         lambda m: m.group(1)),
        # K_avg=X.XX
        (r"K_avg\s*[=≈]\s*(\d+\.\d+)", "k_avg", frontier_text, "FRONTIER.md",
         lambda m: m.group(1)),
        (r"K_avg\s*[=≈]\s*(\d+\.\d+)", "k_avg", next_text, "NEXT.md",
         lambda m: m.group(1)),
        # "NNN lessons" standalone (but only >=100 to filter incidentals)
        (r"(\d{3,})\s*lessons", "lesson_count", frontier_text, "FRONTIER.md",
         lambda m: m.group(1)),
        # "N principles" in headers
        (r"(\d{2,})\s*(?:live\s+)?principles", "principle_count", frontier_text, "FRONTIER.md",
         lambda m: m.group(1)),
    ]

    # Collect unique claims (deduplicate by type+value+source)
    seen = set()
    raw_claims = []
    for entry in claim_patterns:
        pattern, ctype, text, source, extractor = entry
        for m in re.finditer(pattern, text):
            value = extractor(m)
            key = (ctype, value, source)
            if key not in seen:
                seen.add(key)
                # Get surrounding context (the line)
                start = text.rfind("\n", 0, m.start()) + 1
                end = text.find("\n", m.end())
                if end == -1:
                    end = len(text)
                context = text[start:end].strip()[:200]
                raw_claims.append({
                    "type": ctype,
                    "value": value,
                    "source": source,
                    "context": context,
                })

    # Sample up to 10 meaningful claims — prioritize recent state summaries
    # Take one per type first, then fill with older state lines
    sampled = []
    seen_types = set()
    # First pass: one per type (most recent = first match from top of file)
    for c in raw_claims:
        if c["type"] not in seen_types and len(sampled) < 10:
            sampled.append(c)
            seen_types.add(c["type"])
    # Second pass: fill with remaining
    for c in raw_claims:
        if c not in sampled and len(sampled) < 10:
            sampled.append(c)

    # Verify claims against source data
    verified = 0
    unverified = 0
    stale = 0
    results = []

    # Ground truth for counts
    actual_lessons = len(list(LESSONS_DIR.glob("L-*.md")))
    actual_principles = _count_principles()
    actual_beliefs = _count_beliefs()
    actual_frontiers = _count_frontiers()

    ground_truth = {
        "lesson_count": actual_lessons,
        "principle_count": actual_principles,
        "belief_count": actual_beliefs,
        "frontier_count": actual_frontiers,
    }

    for claim in sampled:
        ctype = claim["type"]
        value = claim["value"]
        status = "unverified"

        if ctype in ground_truth:
            actual = ground_truth[ctype]
            claimed = int(value)
            if claimed == actual:
                status = "verified"
                verified += 1
            elif abs(claimed - actual) / max(actual, 1) < 0.05:
                status = "close"
                verified += 1  # close enough
            else:
                status = f"stale (actual={actual})"
                stale += 1
        elif ctype == "session_count":
            # We cannot verify session count precisely, mark as unverified
            status = "unverifiable"
            unverified += 1
        elif ctype == "k_avg":
            # K_avg is derived from a tool run; mark as unverifiable without running it
            status = "unverifiable-without-tool"
            unverified += 1
        elif ctype == "percentage":
            # Percentages need context-specific verification — mark unverifiable
            status = "unverifiable"
            unverified += 1
        else:
            unverified += 1

        results.append({
            "type": ctype,
            "claimed": value,
            "source": claim["source"],
            "status": status,
            "context": claim["context"][:120],
        })

    total = verified + stale + unverified
    drift_rate = stale / total if total else 0

    if drift_rate < 0.10:
        verdict = "HEALTHY: low numerical drift"
    elif drift_rate < 0.30:
        verdict = "WATCH: some stale numbers — sync_state.py coverage gap"
    else:
        verdict = "DEGRADED: high drift — automated claim verification needed"

    return {
        "sampled_claims": len(results),
        "verified": verified,
        "stale": stale,
        "unverified": unverified,
        "drift_rate": round(drift_rate, 4),
        "claims": results,
        "ground_truth": {
            "lessons": actual_lessons,
            "principles": actual_principles,
            "beliefs": actual_beliefs,
            "frontiers": actual_frontiers,
        },
        "verdict": verdict,
    }


def _count_principles() -> int:
    """Count P-NNN entries in PRINCIPLES.md (inline format: P-008, P-011, etc.)."""
    pfile = REPO / "memory" / "PRINCIPLES.md"
    try:
        text = pfile.read_text(encoding="utf-8")
    except FileNotFoundError:
        return 0
    # Principles are inline: "P-008 validate by usage" — find unique P-NNN
    return len(set(re.findall(r"\bP-(\d+)\b", text)))


def _count_beliefs() -> int:
    """Count beliefs in DEPS.md."""
    bfile = REPO / "beliefs" / "DEPS.md"
    try:
        text = bfile.read_text(encoding="utf-8")
    except FileNotFoundError:
        return 0
    return len(re.findall(r"^###\s+B-?\w+", text, re.MULTILINE))


def _count_frontiers() -> int:
    """Count active frontiers in FRONTIER.md."""
    try:
        text = FRONTIER_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        return 0
    # Count lines starting with "- **F" (active frontier entries)
    return len(re.findall(r"^-\s+\*\*F", text, re.MULTILINE))


# ---------------------------------------------------------------------------
# 5. Dark citation mass
# ---------------------------------------------------------------------------
def measure_dark_citations() -> dict:
    """Find L-NNN body references NOT in the Cites: header."""
    lesson_files = sorted(LESSONS_DIR.glob("L-*.md"))

    total_lessons = 0
    lessons_with_dark = 0
    total_header_refs = 0
    total_body_refs = 0
    total_dark_refs = 0
    dark_examples = []

    for lf in lesson_files:
        m = re.match(r"L-(\d+)\.md", lf.name)
        if not m:
            continue
        lesson_num = m.group(1)
        total_lessons += 1

        header_refs = set(_get_lesson_cites_header(lf))
        total_header_refs += len(header_refs)

        # Get ALL body refs (including header), then subtract the lesson itself
        all_body_refs = set(_get_lesson_body_refs(lf))
        all_body_refs.discard(lesson_num)  # Remove self-reference

        # Body refs that are NOT in Cites: header = dark citations
        dark_refs = all_body_refs - header_refs
        total_body_refs += len(all_body_refs)
        total_dark_refs += len(dark_refs)

        if dark_refs:
            lessons_with_dark += 1
            if len(dark_examples) < 10:
                dark_examples.append({
                    "lesson": f"L-{lesson_num}",
                    "dark_count": len(dark_refs),
                    "dark_refs": sorted([f"L-{r}" for r in list(dark_refs)[:5]]),
                    "header_count": len(header_refs),
                })

    dark_mass_pct = (total_dark_refs / total_body_refs * 100) if total_body_refs else 0

    if dark_mass_pct < 20:
        verdict = "HEALTHY: dark citation mass below 20%"
    elif dark_mass_pct < 30:
        verdict = "WATCH: dark citations 20-30% — run lesson_quality_fixer.py --fix"
    else:
        verdict = "DEGRADED: dark citations >30% — tool graph is incomplete"

    return {
        "total_lessons": total_lessons,
        "lessons_with_dark_citations": lessons_with_dark,
        "total_header_refs": total_header_refs,
        "total_body_refs": total_body_refs,
        "total_dark_refs": total_dark_refs,
        "dark_mass_pct": round(dark_mass_pct, 2),
        "dark_lesson_pct": round(
            lessons_with_dark / total_lessons * 100, 1
        ) if total_lessons else 0,
        "examples": dark_examples,
        "verdict": verdict,
    }


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
def compute_coherence_score(results: dict) -> tuple[float, str, str]:
    """Compute 0-5 coherence score from all measurements."""
    scores = []

    # 1. Collision rate: 0.0=5, 0.05=4, 0.10=3, 0.20=2, 0.30+=1
    cr = results["merge_collisions"]["collision_rate"]
    if cr < 0.03:
        scores.append(5.0)
    elif cr < 0.08:
        scores.append(4.0)
    elif cr < 0.15:
        scores.append(3.0)
    elif cr < 0.25:
        scores.append(2.0)
    else:
        scores.append(1.0)

    # 2. Cross-domain transfer: >0.30=5, >0.20=4, >0.15=3, >0.10=2, else=1
    tr = results["cross_domain_transfers"]["transfer_rate"]
    if tr > 0.30:
        scores.append(5.0)
    elif tr > 0.20:
        scores.append(4.0)
    elif tr > 0.15:
        scores.append(3.0)
    elif tr > 0.10:
        scores.append(2.0)
    else:
        scores.append(1.0)

    # 3. Index overflow: 0 overflow=5, 1=4, 2=3, 3=2, 4+=1
    oc = results["index_overflow"]["overflow_count"]
    scores.append(max(1.0, 5.0 - oc))

    # 4. Numerical drift: <0.10=5, <0.20=4, <0.30=3, <0.50=2, else=1
    dr = results["numerical_drift"]["drift_rate"]
    if dr < 0.10:
        scores.append(5.0)
    elif dr < 0.20:
        scores.append(4.0)
    elif dr < 0.30:
        scores.append(3.0)
    elif dr < 0.50:
        scores.append(2.0)
    else:
        scores.append(1.0)

    # 5. Dark citation mass: <15%=5, <20%=4, <25%=3, <35%=2, else=1
    dm = results["dark_citations"]["dark_mass_pct"]
    if dm < 15:
        scores.append(5.0)
    elif dm < 20:
        scores.append(4.0)
    elif dm < 25:
        scores.append(3.0)
    elif dm < 35:
        scores.append(2.0)
    else:
        scores.append(1.0)

    avg = round(sum(scores) / len(scores), 2)

    # Determine key finding
    weakest_idx = scores.index(min(scores))
    dimension_names = [
        "merge collisions", "cross-domain transfer", "index overflow",
        "numerical drift", "dark citations"
    ]
    weakest = dimension_names[weakest_idx]

    key_finding = (
        f"Coherence score {avg}/5 — weakest dimension is {weakest} "
        f"(score {min(scores)}/5)."
    )

    # Prescription based on weakest
    prescriptions = {
        "merge collisions": (
            "Add domain-lock in dispatch_optimizer.py: if domain has active lane, "
            "skip or add COLLISION_WARNING to lane Etc field."
        ),
        "cross-domain transfer": (
            "Run lesson_quality_fixer.py --fix to surface implicit cross-domain "
            "citations; add domain tags to untagged lessons."
        ),
        "index overflow": (
            "Split overflowing INDEX.md buckets (>40 lines) into sub-themes; "
            "run compact.py on large buckets."
        ),
        "numerical drift": (
            "Extend sync_state.py to cover all numerical claims (B/F counts, "
            "K_avg, rates); wire into maintenance.py periodic."
        ),
        "dark citations": (
            "Run lesson_quality_fixer.py --fix to promote body L-NNN refs to "
            "Cites: headers; target dark mass <20%."
        ),
    }
    prescription = prescriptions[weakest]

    return avg, key_finding, prescription


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("F-IS4 Coherence Hardening — measuring 5 dimensions...\n")

    print("  [1/5] Merge collision rate...")
    mc = measure_merge_collisions()
    print(f"    -> {mc['same_session_collisions']} same-session collisions "
          f"in {mc['total_domex_lanes']} DOMEX lanes "
          f"(rate={mc['collision_rate']})")

    print("  [2/5] Cross-domain transfer rate...")
    cdt = measure_cross_domain_transfers()
    print(f"    -> {cdt['cross_domain_citations']}/{cdt['total_citations_in_headers']} "
          f"cross-domain ({cdt['transfer_rate']})")

    print("  [3/5] INDEX.md bucket overflow...")
    io = measure_index_overflow()
    print(f"    -> {io['overflow_count']}/{io['total_buckets']} buckets overflowing "
          f"(>40 lines)")

    print("  [4/5] Numerical claim drift...")
    nd = measure_numerical_drift()
    print(f"    -> {nd['verified']} verified, {nd['stale']} stale, "
          f"{nd['unverified']} unverified (drift={nd['drift_rate']})")

    print("  [5/5] Dark citation mass...")
    dc = measure_dark_citations()
    print(f"    -> {dc['dark_mass_pct']}% dark ({dc['total_dark_refs']}"
          f"/{dc['total_body_refs']} refs)")

    results = {
        "merge_collisions": mc,
        "cross_domain_transfers": cdt,
        "index_overflow": io,
        "numerical_drift": nd,
        "dark_citations": dc,
    }

    score, finding, prescription = compute_coherence_score(results)
    results["coherence_score"] = score
    results["key_finding"] = finding
    results["prescription"] = prescription
    results["session"] = "S389"
    results["method"] = (
        "5-dimension coherence probe: merge collisions (lane overlap), "
        "cross-domain transfer (citation flow), INDEX overflow (retrieval), "
        "numerical drift (claim verification), dark citations (implicit flow)"
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"  Coherence Score: {score}/5")
    print(f"  Key Finding: {finding}")
    print(f"  Prescription: {prescription}")
    print(f"{'='*60}")
    print(f"\nArtifact saved to: {OUTPUT_FILE.relative_to(REPO)}")


if __name__ == "__main__":
    main()
