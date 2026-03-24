#!/bin/bash
# Near-duplicate lesson guard (G-CC2-4, F-QC1, L-356, L-1070): bonding curve analog.
# Staged new lesson files are scanned against recent lesson titles for word-overlap >50%.
# FAIL at N>=1000 (L-1070): concurrent sessions produce near-dups without
# seeing each other's untracked work.
# Requires: PYTHON_CMD array and STAGED_NEW_LESSONS variable set by caller.
if [ -n "$STAGED_NEW_LESSONS" ]; then
    NEAR_DUP_EXIT=0
    "${PYTHON_CMD[@]}" - "$STAGED_NEW_LESSONS" << 'PYEOF' || NEAR_DUP_EXIT=$?
import sys, os, re

new_lessons = sys.argv[1].split() if len(sys.argv) > 1 else []
lesson_dir = "memory/lessons"

# L-NNN citation check (L-457, F9-NK): new lessons should cite at least one other lesson
no_citation_lessons = []
for new_path in new_lessons:
    try:
        with open(new_path) as f:
            content = f.read()
        lid = os.path.basename(new_path).replace('.md', '')
        cites = [c for c in re.findall(r'L-(\d{3})', content) if 'L-' + c != lid]
        if not cites:
            no_citation_lessons.append(os.path.basename(new_path))
    except Exception:
        pass
if no_citation_lessons:
    for f in no_citation_lessons:
        print(f"  NOTICE: {f} has no L-NNN citations — add Related: L-NNN to sustain K_avg>1.5 (L-457)")
else:
    print("  L-NNN citation guard: PASS")

# L-1292 typed citation nudge
untyped_lessons = []
for new_path in new_lessons:
    try:
        with open(new_path) as f:
            content = f.read()
        has_cites = bool(re.search(r'^Cites:', content, re.MULTILINE))
        has_typed = bool(re.search(r'^(Supports|Contradicts|Extends|Requires):', content, re.MULTILINE))
        if has_cites and not has_typed:
            untyped_lessons.append(os.path.basename(new_path))
    except Exception:
        pass
if untyped_lessons:
    for f in untyped_lessons:
        print(f"  NOTICE: {f} uses Cites: — consider Supports:/Contradicts:/Extends: for typed edges (L-1292)")

def get_title(path):
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("#"):
                    return re.sub(r"^#+\s*", "", line).lower()
    except Exception:
        pass
    return ""

def word_overlap(a, b):
    wa = set(re.findall(r'\w+', a)) - {"the","a","an","is","are","was","were","to","of","in","for","and","or","L","S"}
    wb = set(re.findall(r'\w+', b)) - {"the","a","an","is","are","was","were","to","of","in","for","and","or","L","S"}
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / min(len(wa), len(wb))

existing = sorted([
    f for f in os.listdir(lesson_dir)
    if f.startswith("L-") and f.endswith(".md") and not f.startswith("L-0")
], reverse=True)[:40]

warned = False
for new_path in new_lessons:
    new_title = get_title(new_path)
    if not new_title:
        continue
    for existing_file in existing:
        existing_path = os.path.join(lesson_dir, existing_file)
        if os.path.abspath(existing_path) == os.path.abspath(new_path):
            continue
        existing_title = get_title(existing_path)
        ov = word_overlap(new_title, existing_title)
        if ov >= 0.5:
            print(f"  NEAR-DUP WARNING: {os.path.basename(new_path)} overlaps {existing_file} ({ov:.0%})")
            print(f"    New:      {new_title}")
            print(f"    Existing: {existing_title}")
            print("    Consider updating the existing lesson instead (F-QC1, G-CC2-4).")
            warned = True
            break

if warned:
    print("  Near-dup guard: FAIL (see above) — update existing lesson instead of adding new one (F-QC1, L-1070).")
    print("  To bypass (with justification): set ALLOW_NEAR_DUP=1")
    sys.exit(1)
else:
    print("  Near-dup guard: PASS")
PYEOF
    if [ "${NEAR_DUP_EXIT}" -eq 1 ]; then
        if [ "${ALLOW_NEAR_DUP:-0}" != "1" ]; then
            exit 1
        fi
        echo "  ALLOW_NEAR_DUP=1 set — bypassing near-dup guard."
    fi
fi
