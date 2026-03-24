#!/bin/bash
# FM-03: Ghost-lesson resurrection guard (I9/MC-SAFE, L-346).
# After 'git mv memory/lessons/L-NNN.md memory/lessons/archive/L-NNN.md', WSL may leave
# ghost copies in the source directory. If staged as new-file, they undo the archiving.
ARCHIVE_DIR="memory/lessons/archive"
if [ -d "$ARCHIVE_DIR" ]; then
    GHOST_FILES=""
    while IFS= read -r filepath; do
        lesson_name="$(basename "$filepath")"
        if [ -f "$ARCHIVE_DIR/$lesson_name" ]; then
            GHOST_FILES="$GHOST_FILES $filepath"
        fi
    done < <(git status --porcelain 2>/dev/null | { grep '^A ' || true; } | { grep 'memory/lessons/L-' || true; } | { grep -v '/archive/' || true; } | awk '{print $2}')
    if [ -n "$GHOST_FILES" ]; then
        echo "FAIL: Ghost-lesson resurrection detected —${GHOST_FILES}"
        echo "  These staged new-files already exist in archive/; staging would undo compaction."
        echo "  Fix: git restore --staged${GHOST_FILES}"
        if [ "${ALLOW_GHOST_LESSONS:-0}" != "1" ]; then
            exit 1
        fi
        echo "  ALLOW_GHOST_LESSONS=1 set — bypassing ghost-lesson guard."
    fi
    echo "  Ghost-lesson guard: PASS"
fi
