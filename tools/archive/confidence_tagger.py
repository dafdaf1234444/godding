#!/usr/bin/env python3
"""Batch confidence tagger for lessons missing Confidence: headers.

Heuristic classification (L-651):
  - Explicit n=X or measurement language → Measured
  - Distillation/synthesis/cross-domain convergence → Synthesized
  - Default → Theorized (conservative)

Usage:
  python3 tools/confidence_tagger.py              # dry-run (default)
  python3 tools/confidence_tagger.py --fix         # apply tags
  python3 tools/confidence_tagger.py --range 1000 1050  # specific range
"""

import re
import sys
import glob
import os


def classify_confidence(text):
    """Infer confidence level from lesson content."""
    lower = text.lower()

    # Check for explicit n= patterns
    n_match = re.search(r'\bn\s*=\s*(\d+)', lower)
    n_val = int(n_match.group(1)) if n_match else 0

    # Measurement signals
    measure_signals = [
        r'\bmeasured\b', r'\bcounted\b', r'\bdataset\b', r'\bsample\b',
        r'\bexperiment\b', r'\bverified\b', r'\btested\b', r'\bempirical\b',
        r'\b\d+\s*sessions?\b', r'\bbaseline\b', r'\bbefore[/-]after\b',
        r'\b\d+%\b.*\b\d+%\b',  # multiple percentages = measurement
    ]
    measure_count = sum(1 for p in measure_signals if re.search(p, lower))

    # Synthesis signals
    synth_signals = [
        r'\bdistill', r'\bsynthesi[sz]', r'\bcross-domain\b', r'\bconverg',
        r'\bcross-lesson\b', r'\bmulti-domain\b',
    ]
    synth_count = sum(1 for p in synth_signals if re.search(p, lower))

    # Structural signals
    struct_signals = [r'\bstructural\b', r'\barchitect', r'\bwired\b', r'\benforcement\b']
    struct_count = sum(1 for p in struct_signals if re.search(p, lower))

    # Classify
    if n_val > 0:
        return f"Measured (n={n_val})"
    if measure_count >= 2:
        return "Measured"
    if synth_count >= 1 and measure_count >= 1:
        return "Synthesized"
    if synth_count >= 2:
        return "Synthesized"
    if struct_count >= 2:
        return "Structural"
    return "Theorized"


def has_confidence(lines):
    """Check if file already has a Confidence or Status line in header."""
    header = "\n".join(lines[:8])
    return bool(re.search(r'\**(?:Confidence|Status)\**\s*:', header))


def find_insert_point(lines):
    """Find the line index to insert Confidence after Session/before Cites."""
    for i, line in enumerate(lines[:8]):
        stripped = line.strip()
        # Look for Session line
        if re.match(r'\**Session\**\s*:', stripped) or re.match(r'Session:', stripped):
            # Insert after Session line
            return i + 1
    # Fallback: after title line (line 0) + blank (line 1)
    return 2


def process_lesson(filepath, fix=False):
    """Process a single lesson file. Returns (filepath, action, confidence) or None."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    lines = content.split('\n')

    if has_confidence(lines):
        return None  # already tagged

    confidence = classify_confidence(content)
    insert_idx = find_insert_point(lines)

    if fix:
        # Check if the line before insert point is formatted with ** or not
        session_line = lines[insert_idx - 1] if insert_idx > 0 else ""
        if session_line.strip().startswith('**'):
            conf_line = f"**Confidence**: {confidence}"
        else:
            conf_line = f"Confidence: {confidence}"
        lines.insert(insert_idx, conf_line)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

    return (os.path.basename(filepath), "TAGGED" if fix else "WOULD TAG", confidence)


def main():
    fix = '--fix' in sys.argv
    range_start, range_end = 1000, 9999

    if '--range' in sys.argv:
        idx = sys.argv.index('--range')
        range_start = int(sys.argv[idx + 1])
        range_end = int(sys.argv[idx + 2])

    lesson_dir = os.path.join(os.path.dirname(__file__), '..', 'memory', 'lessons')
    files = sorted(glob.glob(os.path.join(lesson_dir, 'L-*.md')))

    results = []
    skipped = 0
    for f in files:
        # Extract lesson number
        m = re.search(r'L-(\d+)', os.path.basename(f))
        if not m:
            continue
        num = int(m.group(1))
        if num < range_start or num > range_end:
            continue

        result = process_lesson(f, fix=fix)
        if result:
            results.append(result)
        else:
            skipped += 1

    mode = "FIX" if fix else "DRY-RUN"
    print(f"=== CONFIDENCE TAGGER ({mode}) ===")
    print(f"Range: L-{range_start} to L-{range_end}")
    print(f"Already tagged: {skipped}")
    print(f"{'Tagged' if fix else 'Would tag'}: {len(results)}")
    print()

    # Distribution
    dist = {}
    for _, _, conf in results:
        key = conf.split('(')[0].strip()
        dist[key] = dist.get(key, 0) + 1

    if dist:
        print("Distribution:")
        for k, v in sorted(dist.items(), key=lambda x: -x[1]):
            print(f"  {k}: {v}")
        print()

    for name, action, conf in results:
        print(f"  {action}: {name} → {conf}")


if __name__ == '__main__':
    main()
