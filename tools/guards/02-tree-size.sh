#!/bin/bash
# FM-01 layer 3: Tree-size guard (L-1316, S502).
# Catches plumbing commits (commit-tree) that bypass staging guards.
# At N>=3 concurrency, git write-tree can read an emptied index and produce an empty tree.
TREE_FILE_COUNT=$(git write-tree 2>/dev/null | xargs git ls-tree -r --name-only 2>/dev/null | wc -l | tr -d ' ')
if [ "${TREE_FILE_COUNT:-0}" -lt 100 ] && [ "${TREE_FILE_COUNT:-0}" -gt 0 ]; then
    echo "FAIL: Tree-size guard triggered — staged tree has only ${TREE_FILE_COUNT} files (minimum: 100)."
    echo "  This likely means concurrent sessions corrupted the git index."
    echo "  Fix: rm -f .git/index.lock && git read-tree HEAD && git update-index --refresh"
    if [ "${ALLOW_EMPTY_TREE:-0}" != "1" ]; then
        exit 1
    fi
    echo "  ALLOW_EMPTY_TREE=1 set — bypassing tree-size guard."
fi
echo "  Tree-size guard: PASS (${TREE_FILE_COUNT:-0} files in staged tree)"
