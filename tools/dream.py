#!/usr/bin/env python3
"""
dream.py — swarm dreaming: associative synthesis from existing corpus.

Normal swarming = goal-directed work on open frontiers.
Dreaming = free-associative cross-corpus reading that generates:
  - Theme gravity map (where is knowledge dense vs sparse?)
  - Uncited active principles (anchoring targets for new lessons)
  - Cross-domain resonances (domain isomorphisms ↔ principles)
  - Candidate frontier questions (implied by corpus combinations)

Output is actionable: routes to FRONTIER.md, memory/lessons/, CHALLENGES.md.
Run as periodic (cadence 7) or on-demand. (F125, L-256)
"""

import argparse
import re
import sys
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).parent.parent


def load_lessons():
    """Load all lessons with id, theme, and principle citations."""
    lessons = []
    lesson_dir = ROOT / "memory" / "lessons"
    if not lesson_dir.exists():
        return lessons
    for f in sorted(lesson_dir.glob("L-*.md"),
                    key=lambda p: int(re.search(r'\d+', p.stem).group())):
        text = f.read_text(encoding="utf-8", errors="replace")
        num = int(re.search(r'\d+', f.stem).group())
        # Support bold header (**Theme**: X), pipe-separated (| Theme: X |),
        # and modern Domain: field (Session: ... | Domain: X, Y | ...)
        theme_m = re.search(r'\*\*Theme\*\*:\s*([^\n|*]+)', text)
        if not theme_m:
            theme_m = re.search(r'\|\s*Theme:\s*([^|\n]+)', text)
        if theme_m:
            theme = theme_m.group(1).strip()
        else:
            # Modern format: use first Domain: value as theme
            # Handles plain (Domain: X), bold (**Domain**: X), and HTML comment (domain: X)
            domain_m = re.search(r'(?:^|\|)\s*(?:\*\*)?domain(?:\*\*)?\s*:\s*([^|\n,*>]+)', text, re.MULTILINE | re.IGNORECASE)
            theme = domain_m.group(1).strip() if domain_m else ""
        cited = list(set(re.findall(r'P-\d+', text)))
        lessons.append({"id": f"L-{num}", "num": num, "theme": theme, "cited": cited})
    return lessons


def load_principles():
    """Load active principles with ids and text.

    PRINCIPLES.md uses pipe-separated format within section blocks:
      P-NNN short-text | P-NNN short-text | ...
    """
    principles = []
    p_path = ROOT / "memory" / "PRINCIPLES.md"
    if not p_path.exists():
        return principles
    text = p_path.read_text(encoding="utf-8", errors="replace")
    # Skip the header section (before the first ## heading — contains compaction logs
    # that mention P-IDs but are not principles)
    first_section = text.find('\n## ')
    if first_section > 0:
        text = text[first_section:]
    # Split by pipe and newline separators — format:
    #   **Category**: P-NNN text | P-NNN text | P-NNN text\n**Next**: ...
    for raw_segment in re.split(r' \| |\n', text):
        segment = raw_segment.strip()
        m = re.search(r'\b(P-\d+)\s+(.+)', segment)
        if not m:
            continue
        pid, body = m.group(1), m.group(2).strip()[:300]
        if 'superseded' in body[:60].lower() or 'dropped' in body[:60].lower():
            continue
        principles.append({"id": pid, "text": body})
    return principles


def load_domains():
    """Load domain isomorphisms."""
    domains = {}
    domain_dir = ROOT / "domains"
    if not domain_dir.exists():
        return domains
    for d in domain_dir.iterdir():
        if not d.is_dir():
            continue
        f = d / "DOMAIN.md"
        if f.exists():
            text = f.read_text(encoding="utf-8", errors="replace")
            isos = [ln.strip() for ln in text.split('\n') if '→' in ln and len(ln.strip()) > 20]
            domains[d.name] = {"isos": isos[:25], "raw": text[:600]}
    return domains


def theme_gravity(lessons):
    """Show where knowledge mass is concentrated."""
    # Normalize case: lowercase for grouping, but keep display name as most common casing
    counts = Counter(l["theme"].lower() for l in lessons if l["theme"])
    total = len(lessons)
    unthemed = sum(1 for l in lessons if not l["theme"])
    print(f"\n--- Theme gravity ({total} lessons) ---")
    for theme, n in counts.most_common(10):
        bar = "▪" * min(n // 3, 20)
        print(f"  {n:3d}  {theme[:28]:28s}  {bar}")
    if unthemed:
        print(f"  {unthemed:3d}  (unthemed)")
    return counts


def find_uncited_principles(principles, lessons):
    """Find active principles with no lesson citations — anchoring targets."""
    all_cited = set(p for l in lessons for p in l["cited"])
    uncited = [p for p in principles if p["id"] not in all_cited]
    print(f"\n--- Uncited active principles ({len(uncited)} / {len(principles)}) ---")
    if uncited:
        for p in uncited[:6]:
            print(f"  {p['id']}: {p['text'][:70].rstrip()}")
        if len(uncited) > 6:
            print(f"  ... and {len(uncited) - 6} more")
    else:
        print("  All active principles cited.")
    return uncited


def cross_domain_resonances(domains, principles):
    """Find domain isomorphisms that share key concepts with existing principles."""
    resonances = []
    stop = {"swarm", "lesson", "principle", "domain", "belief", "system", "based", "using",
            "which", "their", "about", "these", "where", "other", "under", "above", "within",
            "across", "between", "through", "should", "would", "could", "there", "those"}
    for dname, data in domains.items():
        for iso in data["isos"]:
            iso_words = {w for w in re.findall(r'\b\w{5,}\b', iso.lower()) if w not in stop}
            for p in principles:
                p_words = {w for w in re.findall(r'\b\w{5,}\b', p["text"].lower()) if w not in stop}
                overlap = iso_words & p_words
                if len(overlap) >= 3:
                    resonances.append((dname, iso[:70], p["id"], sorted(overlap)[:4]))
    print(f"\n--- Cross-domain resonances ({len(resonances)}) ---")
    for dname, iso, pid, overlap in resonances[:6]:
        print(f"  [{dname}] {iso}")
        print(f"    ↔ {pid}  shared: {overlap}")
    if not resonances:
        print("  (none detected at ≥3 word overlap)")
    return resonances


def candidate_frontiers(theme_counts, lessons, domains):
    """Generate candidate frontier questions from corpus patterns."""
    candidates = []
    domain_names = set(domains.keys()) - {"meta", "nk-complexity", "distributed-systems"}
    for theme, n in theme_counts.most_common(5):
        if n >= 10 and theme.lower() not in domain_names:
            candidates.append(
                f"'{theme}' has {n} lessons — is there a structural meta-pattern not yet a principle?"
            )
    recent = lessons[-15:]
    recent_themes = Counter(l["theme"] for l in recent if l["theme"])
    if recent_themes:
        top = recent_themes.most_common(1)[0]
        if top[1] >= 5:
            candidates.append(
                f"Recent: {top[1]}/15 lessons in '{top[0]}' — orthogonal themes underexplored?"
            )
    if len(domain_names) >= 2:
        dlist = sorted(domain_names)
        candidates.append(
            f"Do {dlist[0]}+{dlist[1]} isomorphisms overlap to suggest a third unidentified mapping?"
        )
    return candidates


def auto_append_frontiers(candidates):
    """Append dream-generated frontier candidates to FRONTIER.md (GAP-1 closure).

    Deduplicates by checking if key theme words already appear in existing frontiers.
    Returns count of appended candidates.
    """
    frontier_path = ROOT / "tasks" / "FRONTIER.md"
    if not frontier_path.exists() or not candidates:
        return 0
    text = frontier_path.read_text(encoding="utf-8", errors="replace")

    # Find highest F-number
    existing_ids = [int(m) for m in re.findall(r"\bF(\d+)\b", text)]
    next_id = max(existing_ids, default=0) + 1

    # Find existing frontier text for dedup
    existing_lower = text.lower()

    appended = []
    for candidate in candidates:
        # Extract key words (5+ chars) for dedup check
        key_words = {w for w in re.findall(r'\b\w{5,}\b', candidate.lower())}
        key_words -= {"lesson", "lessons", "which", "there", "these", "about",
                      "pattern", "should", "would", "could", "where", "domain"}
        overlap = sum(1 for w in key_words if w in existing_lower)
        if overlap >= 3:
            continue  # likely duplicate
        entry = f"- **F{next_id}**: {candidate} OPEN (dream.py auto-generated S352).\n"
        appended.append(entry)
        next_id += 1

    if not appended:
        return 0

    # Insert before "## Domain frontiers" section or append to Exploratory
    insert_marker = "## Domain frontiers"
    if insert_marker in text:
        pos = text.index(insert_marker)
        text = text[:pos] + "\n".join(appended) + "\n" + text[pos:]
    else:
        text = text.rstrip() + "\n\n" + "\n".join(appended) + "\n"

    # Update active count in header
    new_count = len(re.findall(r"^- \*\*F", text, re.MULTILINE))
    text = re.sub(r"(\d+) active", f"{new_count} active", text, count=1)

    frontier_path.write_text(text, encoding="utf-8")
    return len(appended)


def dream(auto_append=False):
    print("=== SWARM DREAM CYCLE ===")
    print("Associative synthesis from corpus. Not goal-directed. Output = swarm input.")

    lessons = load_lessons()
    principles = load_principles()
    domains = load_domains()
    print(f"\nCorpus: {len(lessons)}L  {len(principles)}P  {len(domains)} domains")

    theme_counts = theme_gravity(lessons)
    uncited = find_uncited_principles(principles, lessons)
    resonances = cross_domain_resonances(domains, principles)
    candidates = candidate_frontiers(theme_counts, lessons, domains)

    print(f"\n--- Candidate frontier questions ({len(candidates)}) ---")
    for i, q in enumerate(candidates, 1):
        print(f"  {i}. {q}")

    print(f"\n--- Dream routing ---")
    if uncited:
        print(f"  Write lessons that cite: {', '.join(p['id'] for p in uncited[:4])}")
    if resonances:
        print(f"  Cross-domain: validate {len(resonances)} resonances against FRONTIER.md")

    if auto_append and candidates:
        n = auto_append_frontiers(candidates)
        if n:
            print(f"  AUTO-APPENDED {n} candidate(s) to tasks/FRONTIER.md")
        else:
            print(f"  All candidates already covered in FRONTIER.md (dedup filter)")
    elif candidates:
        print(f"  Add strongest candidates to tasks/FRONTIER.md (or use --auto-append)")

    print(f"\nDream complete. Act on what resonates; ignore what doesn't.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Swarm dream cycle")
    parser.add_argument("--auto-append", action="store_true",
                        help="Auto-append frontier candidates to FRONTIER.md (GAP-1 closure)")
    args = parser.parse_args()
    dream(auto_append=args.auto_append)
