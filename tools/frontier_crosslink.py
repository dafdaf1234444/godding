#!/usr/bin/env python3
"""
frontier_crosslink.py — P-274 enforcement: map domain frontiers to global parent frontiers.

Addresses the 3.0% domain→global linkage rate (L-926, F-NK6).
Scans domain FRONTIER.md files for keyword overlap with global frontiers.
Outputs suggested "Cites: F-GLOBAL-X" annotations to close the namespace gap.

Usage:
  python3 tools/frontier_crosslink.py             # show suggested links
  python3 tools/frontier_crosslink.py --apply     # write links to domain FRONTIER.md files
  python3 tools/frontier_crosslink.py --stats     # show current linkage statistics
  python3 tools/frontier_crosslink.py --threshold 3  # minimum shared terms (default: 3)
"""

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GLOBAL_FRONTIER = REPO_ROOT / "tasks" / "FRONTIER.md"
DOMAINS_DIR = REPO_ROOT / "domains"
MIN_OVERLAP = 3  # shared meaningful terms for a suggestion

STOPWORDS = {
    "the", "a", "an", "is", "in", "of", "to", "and", "or", "for", "with",
    "on", "at", "by", "from", "as", "it", "its", "this", "that", "be", "can",
    "are", "was", "were", "will", "would", "how", "what", "which", "where",
    "when", "who", "has", "have", "had", "does", "do", "did", "not", "no",
    "new", "more", "than", "if", "than", "so", "but", "all", "vs", "per",
    "via", "see", "run", "each", "any", "after", "before", "between", "within",
    "across", "over", "under", "into", "out", "up", "down", "same", "other",
    "most", "some", "many", "s", "n", "l", "p", "b", "f", "open",
    "related", "test", "cites", "frontier", "session", "domain", "swarm",
    "sessions", "measure", "add", "build", "use", "using", "run", "running",
    "check", "find", "found", "show", "shows", "number", "rate", "count",
    "data", "file", "files", "tool", "tools", "path", "output", "input",
    "system", "current", "next", "last", "first", "second", "third",
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "zero", "true", "false", "none", "set", "get", "make", "made",
    "also", "only", "just", "very", "well", "good", "best", "better",
    "need", "needs", "needed", "want", "wants", "take", "takes", "give",
    "now", "then", "here", "there", "thus", "via", "yet", "still",
}


def _terms(text: str) -> set[str]:
    """Extract meaningful terms from text, normalized to lowercase."""
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", text.lower())
    return {w for w in words if w not in STOPWORDS and not re.match(r"^[sl]-\d+$", w)}


def _parse_frontiers(md_text: str, source_domain: str = "global") -> dict[str, dict]:
    """Parse frontier entries from a FRONTIER.md file.
    Returns {frontier_id: {id, text, terms, refs_global}}
    """
    frontiers = {}
    pattern = re.compile(r"- \*\*(?:~~)?(F-[A-Z0-9]+)(?:~~)?\*\*", re.IGNORECASE)
    blocks = re.split(r"\n(?=- \*\*)", md_text)

    for block in blocks:
        m = pattern.match(block.strip())
        if not m:
            continue
        fid = m.group(1).upper()
        # Skip resolved/struck-through entries
        if "~~" + fid + "~~" in block:
            continue
        # Extract existing global refs in this block
        existing_refs = set(re.findall(r"\bF-[A-Z]{2,}[0-9]*\b", block))
        existing_refs.discard(fid)
        frontiers[fid] = {
            "id": fid,
            "text": block,
            "terms": _terms(block),
            "refs": existing_refs,
            "domain": source_domain,
        }
    return frontiers


def load_global_frontiers() -> dict[str, dict]:
    if not GLOBAL_FRONTIER.exists():
        return {}
    text = GLOBAL_FRONTIER.read_text(encoding="utf-8")
    return _parse_frontiers(text, source_domain="global")


def load_domain_frontiers() -> dict[str, dict]:
    """Load all domain frontiers, keyed by frontier_id."""
    all_frontiers = {}
    for domain_dir in sorted(DOMAINS_DIR.iterdir()):
        frontier_file = domain_dir / "tasks" / "FRONTIER.md"
        if not frontier_file.exists():
            continue
        text = frontier_file.read_text(encoding="utf-8")
        domain_name = domain_dir.name
        parsed = _parse_frontiers(text, source_domain=domain_name)
        for fid, entry in parsed.items():
            entry["file"] = str(frontier_file)
            all_frontiers[fid] = entry
    return all_frontiers


def compute_suggestions(
    domain_frontiers: dict[str, dict],
    global_frontiers: dict[str, dict],
    min_overlap: int = MIN_OVERLAP,
) -> list[dict]:
    """For each domain frontier, find global frontiers with >= min_overlap term overlap."""
    suggestions = []
    for dfid, df in domain_frontiers.items():
        already_linked = {r for r in df["refs"] if r in global_frontiers}
        for gfid, gf in global_frontiers.items():
            # Skip same-ID frontiers (same frontier listed in both domain and global)
            if dfid == gfid:
                continue
            if gfid in already_linked:
                continue
            # Also skip if the global frontier already cites this domain one
            if dfid in gf["refs"]:
                continue
            overlap = df["terms"] & gf["terms"]
            if len(overlap) >= min_overlap:
                suggestions.append({
                    "domain_id": dfid,
                    "domain_name": df["domain"],
                    "global_id": gfid,
                    "overlap_count": len(overlap),
                    "overlap_terms": sorted(overlap)[:8],
                    "file": df.get("file", ""),
                })
    suggestions.sort(key=lambda x: -x["overlap_count"])
    return suggestions


def compute_stats(
    domain_frontiers: dict[str, dict],
    global_frontiers: dict[str, dict],
) -> dict:
    total_domain = len(domain_frontiers)
    linked = sum(
        1 for df in domain_frontiers.values()
        if df["refs"] & global_frontiers.keys()
    )
    # bidirectional: global → domain
    global_to_domain = sum(
        1 for gf in global_frontiers.values()
        if gf["refs"] & domain_frontiers.keys()
    )
    return {
        "total_domain": total_domain,
        "total_global": len(global_frontiers),
        "domain_linked_to_global": linked,
        "global_linked_to_domain": global_to_domain,
        "domain_linkage_pct": round(100 * linked / max(total_domain, 1), 1),
        "global_linkage_pct": round(100 * global_to_domain / max(len(global_frontiers), 1), 1),
    }


def apply_suggestions(suggestions: list[dict], dry_run: bool = True) -> int:
    """Add 'Cites: F-GLOBAL-X' to matching domain frontier entries."""
    by_file: dict[str, list[dict]] = {}
    for s in suggestions:
        by_file.setdefault(s["file"], []).append(s)

    applied = 0
    for fpath, slist in by_file.items():
        p = Path(fpath)
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        modified = text

        for s in slist:
            dfid = s["domain_id"]
            gfid = s["global_id"]
            # Find the domain frontier block and add a Cites: reference
            pattern = re.compile(
                r"(- \*\*(?:~~)?" + re.escape(dfid) + r"(?:~~)?\*\*.*?)"
                r"((?=\n- \*\*)|\Z)",
                re.DOTALL,
            )
            m = pattern.search(modified)
            if not m:
                continue
            block = m.group(1)
            # Skip if already present
            if gfid in block:
                continue
            # Add citation before closing of block
            cite_line = f"\n  → Links to global frontier: {gfid}. (auto-linked S420, frontier_crosslink.py)"
            new_block = block.rstrip() + cite_line + "\n"
            modified = modified[: m.start()] + new_block + modified[m.end() :]
            applied += 1

        if modified != text:
            if not dry_run:
                p.write_text(modified, encoding="utf-8")
            else:
                print(f"  [DRY-RUN] Would update {fpath}")
    return applied


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="Write cross-link annotations to domain FRONTIER.md files")
    parser.add_argument("--stats", action="store_true", help="Show current linkage statistics only")
    parser.add_argument("--threshold", type=int, default=MIN_OVERLAP, help=f"Minimum shared terms (default: {MIN_OVERLAP})")
    parser.add_argument("--top", type=int, default=30, help="Show top N suggestions (default: 30)")
    args = parser.parse_args()

    global_frontiers = load_global_frontiers()
    domain_frontiers = load_domain_frontiers()

    if not global_frontiers:
        print("ERROR: No global frontiers found in tasks/FRONTIER.md", file=sys.stderr)
        sys.exit(1)

    stats = compute_stats(domain_frontiers, global_frontiers)
    print(f"=== FRONTIER CROSSLINK STATS (P-274) ===")
    print(f"  Global frontiers:    {stats['total_global']}")
    print(f"  Domain frontiers:    {stats['total_domain']}")
    print(f"  Domain→global links: {stats['domain_linked_to_global']} ({stats['domain_linkage_pct']}%)")
    print(f"  Global→domain links: {stats['global_linked_to_domain']} ({stats['global_linkage_pct']}%)")
    print(f"  Linkage gap (P-274): {100 - stats['domain_linkage_pct']:.1f}% domain frontiers unlinked")
    print()

    if args.stats:
        return

    suggestions = compute_suggestions(domain_frontiers, global_frontiers, args.threshold)
    print(f"=== SUGGESTED CROSS-LINKS (threshold={args.threshold} shared terms) ===")
    print(f"  {len(suggestions)} new links suggested\n")

    for i, s in enumerate(suggestions[: args.top]):
        print(
            f"  {i+1:3d}. [{s['domain_name']}] {s['domain_id']} → {s['global_id']}"
            f"  ({s['overlap_count']} terms: {', '.join(s['overlap_terms'])})"
        )

    if len(suggestions) > args.top:
        print(f"  ... and {len(suggestions) - args.top} more")

    print()
    if args.apply:
        n = apply_suggestions(suggestions, dry_run=False)
        print(f"Applied {n} cross-link annotations to domain FRONTIER.md files.")
    else:
        n_dry = apply_suggestions(suggestions, dry_run=True)
        if n_dry:
            print(f"  Would add {n_dry} annotations (run --apply to write).")


if __name__ == "__main__":
    main()
