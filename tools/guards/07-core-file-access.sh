#!/bin/bash
# FM-02: WSL filesystem corruption guard (F-CAT1, S444).
# Verify core identity files are accessible — WSL corruption manifests as inaccessible git-tracked files.
CORE_FILES="beliefs/CORE.md SWARM.md memory/INDEX.md"
CORE_INACCESSIBLE=0
for cf in $CORE_FILES; do
    if [ ! -f "$cf" ] || [ ! -r "$cf" ]; then
        echo "FAIL: FM-02 core file inaccessible — $cf"
        echo "  WSL filesystem corruption or unexpected deletion detected."
        echo "  If git-tracked file is missing: git checkout HEAD -- $cf"
        CORE_INACCESSIBLE=1
    fi
done
if [ "$CORE_INACCESSIBLE" -eq 1 ]; then
    if [ "${ALLOW_CORE_MISSING:-0}" != "1" ]; then
        exit 1
    fi
    echo "  ALLOW_CORE_MISSING=1 set — bypassing FM-02 guard."
else
    echo "  FM-02 core-file accessibility: PASS"
fi
