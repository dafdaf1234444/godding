#!/usr/bin/env python3
"""lesson_tagger.py — Auto-assign INDEX.md theme labels to unthemed lessons (F-QC4).

Usage:
  python3 tools/lesson_tagger.py              # show suggestions for unthemed lessons
  python3 tools/lesson_tagger.py --apply      # update INDEX.md with suggestions
  python3 tools/lesson_tagger.py --test       # evaluate accuracy on already-themed lessons
  python3 tools/lesson_tagger.py --json       # output JSON report
"""
import argparse, collections, glob, json, math, os, re, sys

STOP = set(
    "the a an and or but in on at to for of is it was be are from with this "
    "that by not as can has have do so if we no all its also more than each "
    "most only just both were been one two may how per see new used via".split()
)

INDEX_PATH = "memory/INDEX.md"
LESSONS_DIR = "memory/lessons"


def tokenize(text):
    """Extract content words, lowercase, length>2, not stopwords."""
    words = re.findall(r"[a-z][a-z_-]+", text.lower())
    return [w for w in words if len(w) > 2 and w not in STOP]


def parse_themes(index_path=INDEX_PATH):
    """Parse INDEX.md theme table into {name: {ids: set, desc: str, count: int}}."""
    with open(index_path) as f:
        text = f.read()

    theme_start = text.find("## Themes")
    if theme_start < 0:
        print("ERROR: ## Themes section not found in INDEX.md", file=sys.stderr)
        sys.exit(1)

    # Find end of theme table (next ## or end)
    rest = text[theme_start:]
    next_section = re.search(r"\n## (?!Themes)", rest)
    theme_block = rest[: next_section.start()] if next_section else rest

    themes = {}
    for line in theme_block.split("\n"):
        if not line.startswith("|"):
            continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 5:
            continue
        name = cols[1]
        # Skip header and separator rows
        if name in ("Theme", "") or name.startswith("-"):
            continue
        # Skip "What to load when" table rows (no count column with a number)
        count_str = cols[2]
        if not re.match(r"\d+", count_str):
            continue
        count = int(count_str)
        desc = cols[3]
        ids = set(int(x) for x in re.findall(r"L-(\d+)", desc))
        themes[name] = {"ids": ids, "desc": desc, "count": count}
    return themes


def read_lesson(lid):
    """Read a lesson file, return (title, full_text) or ('', '')."""
    path = os.path.join(LESSONS_DIR, f"L-{lid:03d}.md")
    if not os.path.exists(path):
        return "", ""
    with open(path) as f:
        content = f.read()
    title_m = re.search(r"^# (L-\d+:.+)", content, re.MULTILINE)
    title = title_m.group(1) if title_m else ""
    return title, content


def get_all_lesson_ids():
    """Get all non-archived lesson IDs."""
    ids = set()
    for f in glob.glob(os.path.join(LESSONS_DIR, "L-*.md")):
        if "/archive/" in f or "TEMPLATE" in f:
            continue
        m = re.search(r"L-(\d+)", os.path.basename(f))
        if m:
            ids.add(int(m.group(1)))
    return ids


def build_theme_profiles(themes):
    """Build TF-IDF keyword profiles per theme from themed lessons."""
    profiles = {}  # theme -> Counter of weighted terms

    for tname, tdata in themes.items():
        words = collections.Counter()
        # Boost theme name words heavily
        words.update({w: 5 for w in tokenize(tname)})
        # Add description keywords
        words.update({w: 2 for w in tokenize(tdata["desc"])})
        # Sample themed lessons (up to 20)
        for lid in sorted(tdata["ids"])[:20]:
            title, content = read_lesson(lid)
            if not title:
                continue
            for w in tokenize(title):
                words[w] += 3  # title words are strong signals
            for w in tokenize(content[:600]):
                words[w] += 1
        profiles[tname] = words

    # Compute IDF: how distinctive is each word across themes
    n_themes = len(themes)
    doc_freq = collections.Counter()
    for wf in profiles.values():
        for w in wf:
            doc_freq[w] += 1

    idf = {}
    for w, df in doc_freq.items():
        idf[w] = math.log((n_themes + 1) / (df + 1)) + 1  # smoothed IDF

    # Convert to TF-IDF scores
    tfidf = {}
    for tname, wf in profiles.items():
        scored = {w: c * idf.get(w, 1) for w, c in wf.items()}
        tfidf[tname] = scored

    return tfidf


def classify_lesson(lid, tfidf, top_n=3):
    """Classify a lesson against theme profiles. Returns [(theme, score), ...]."""
    title, content = read_lesson(lid)
    if not title and not content:
        return []

    # Build lesson word vector (title weighted 3x)
    lesson_words = collections.Counter()
    for w in tokenize(title):
        lesson_words[w] += 3
    for w in tokenize(content[:800]):
        lesson_words[w] += 1

    # Score against each theme using cosine-like overlap
    scores = []
    for tname, profile in tfidf.items():
        score = 0
        for w, wt in lesson_words.items():
            if w in profile:
                score += wt * profile[w]
        # Normalize by profile magnitude to avoid size bias
        mag = math.sqrt(sum(v * v for v in profile.values())) or 1
        scores.append((tname, score / mag))

    scores.sort(key=lambda x: -x[1])
    return scores[:top_n]


def main():
    parser = argparse.ArgumentParser(description="Auto-assign theme labels to lessons")
    parser.add_argument("--apply", action="store_true", help="Update INDEX.md with top-1 suggestions")
    parser.add_argument("--test", action="store_true", help="Evaluate accuracy on themed lessons")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    parser.add_argument("--min-score", type=float, default=0.5, help="Minimum score threshold for assignment")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of suggestions shown")
    args = parser.parse_args()

    themes = parse_themes()
    tfidf = build_theme_profiles(themes)
    all_ids = get_all_lesson_ids()

    # Build set of already-themed lesson IDs
    themed_ids = set()
    theme_for_id = {}  # ground truth: lid -> theme name
    for tname, tdata in themes.items():
        for lid in tdata["ids"]:
            themed_ids.add(lid)
            theme_for_id[lid] = tname

    unthemed_ids = all_ids - themed_ids

    if args.test:
        # Evaluate on themed lessons (leave-one-out would be ideal but too slow)
        correct = 0
        total = 0
        top3_correct = 0
        for lid in sorted(themed_ids):
            if lid not in theme_for_id:
                continue
            true_theme = theme_for_id[lid]
            predictions = classify_lesson(lid, tfidf)
            if not predictions:
                continue
            total += 1
            if predictions[0][0] == true_theme:
                correct += 1
            if any(t == true_theme for t, _ in predictions[:3]):
                top3_correct += 1

        acc1 = correct / total * 100 if total else 0
        acc3 = top3_correct / total * 100 if total else 0
        print(f"Accuracy on themed lessons (n={total}):")
        print(f"  Top-1: {correct}/{total} = {acc1:.1f}%")
        print(f"  Top-3: {top3_correct}/{total} = {acc3:.1f}%")
        return

    # Classify unthemed lessons
    suggestions = {}  # lid -> [(theme, score), ...]
    theme_additions = collections.defaultdict(list)  # theme -> [lid, ...]

    for lid in sorted(unthemed_ids):
        preds = classify_lesson(lid, tfidf)
        if not preds:
            continue
        top_theme, top_score = preds[0]
        suggestions[lid] = preds
        if top_score >= args.min_score:
            theme_additions[top_theme].append(lid)

    assignable = sum(1 for lid, preds in suggestions.items() if preds[0][1] >= args.min_score)
    new_themed = len(themed_ids) + assignable
    new_rate = (len(all_ids) - new_themed) / len(all_ids) * 100

    if args.json:
        report = {
            "total_lessons": len(all_ids),
            "previously_themed": len(themed_ids),
            "unthemed_before": len(unthemed_ids),
            "assignable": assignable,
            "new_unthemed_rate": round(new_rate, 1),
            "min_score": args.min_score,
            "theme_additions": {t: ids for t, ids in sorted(theme_additions.items())},
            "sample_suggestions": [],
        }
        # Add sample suggestions with scores
        for lid in sorted(suggestions)[:20]:
            preds = suggestions[lid]
            title, _ = read_lesson(lid)
            report["sample_suggestions"].append({
                "lesson": f"L-{lid:03d}",
                "title": title[:100],
                "top1": {"theme": preds[0][0], "score": round(preds[0][1], 3)},
                "top3": [{"theme": t, "score": round(s, 3)} for t, s in preds[:3]],
            })
        print(json.dumps(report, indent=2))
        return

    # Print summary
    print(f"=== LESSON TAGGER (F-QC4) ===")
    print(f"Total lessons: {len(all_ids)}")
    print(f"Previously themed: {len(themed_ids)} ({len(themed_ids)/len(all_ids)*100:.1f}%)")
    print(f"Unthemed: {len(unthemed_ids)} ({len(unthemed_ids)/len(all_ids)*100:.1f}%)")
    print(f"Assignable (score >= {args.min_score}): {assignable}")
    print(f"New unthemed rate: {new_rate:.1f}%")
    print()

    # Show per-theme additions
    print("Theme additions:")
    for tname in sorted(theme_additions):
        ids = theme_additions[tname]
        current = themes[tname]["count"]
        print(f"  {tname}: +{len(ids)} (was {current})")
    print()

    # Show sample suggestions
    shown = 0
    limit = args.limit or 30
    for lid in sorted(suggestions):
        if shown >= limit:
            break
        preds = suggestions[lid]
        title, _ = read_lesson(lid)
        top_theme, top_score = preds[0]
        marker = "✓" if top_score >= args.min_score else "?"
        print(f"  {marker} L-{lid:03d} → {top_theme} ({top_score:.2f})")
        if title:
            print(f"    {title[:90]}")
        shown += 1

    if not args.apply:
        print(f"\nDry run. Use --apply to update INDEX.md.")
        return

    # Apply: update INDEX.md theme counts (descriptions stay hand-curated)
    with open(INDEX_PATH) as f:
        content = f.read()

    lines = content.split("\n")
    updated = 0
    for i, line in enumerate(lines):
        if not line.startswith("|"):
            continue
        cols = line.split("|")
        if len(cols) < 5:
            continue
        tname = cols[1].strip()
        if tname not in theme_additions:
            continue

        new_ids = theme_additions[tname]
        old_count = themes[tname]["count"]
        new_count = old_count + len(new_ids)
        cols[2] = f" {new_count} "
        lines[i] = "|".join(cols)
        updated += 1

    # Update header count
    for i, line in enumerate(lines):
        m = re.match(r"^## Themes \((\d+) lessons\)", line)
        if m:
            lines[i] = f"## Themes ({len(all_ids)} lessons)"
            break

    with open(INDEX_PATH, "w") as f:
        f.write("\n".join(lines))

    # Save full mapping to experiment artifact
    mapping = {}
    for lid in sorted(unthemed_ids):
        preds = classify_lesson(lid, tfidf)
        if preds and preds[0][1] >= args.min_score:
            mapping[f"L-{lid:03d}"] = preds[0][0]
    artifact_path = "experiments/quality/f-qc4-theme-mapping-s383.json"
    os.makedirs(os.path.dirname(artifact_path), exist_ok=True)
    with open(artifact_path, "w") as f:
        json.dump(mapping, f, indent=2)

    print(f"\nApplied: {updated} themes updated, {assignable} lessons tagged.")
    print(f"Full mapping saved to {artifact_path}")
    print(f"New unthemed rate: {new_rate:.1f}%")


if __name__ == "__main__":
    main()
