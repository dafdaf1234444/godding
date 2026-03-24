#!/bin/bash
# EAD enforcement (Council S3, L-484): new session notes should have expect+actual fields.
if git diff --cached --name-only 2>/dev/null | grep -q 'tasks/NEXT.md'; then
    NEXT_DIFF=$(git diff --cached tasks/NEXT.md 2>/dev/null)
    if echo "$NEXT_DIFF" | grep -q '^+## S[0-9]'; then
        if ! echo "$NEXT_DIFF" | grep -q '^\+.*\*\*expect\*\*'; then
            echo "  EAD NOTICE: New session note in NEXT.md is missing **expect** field (P-182, L-484)"
            echo "    Add: - **expect**: <your prediction before acting>"
        fi
        if ! echo "$NEXT_DIFF" | grep -q '^\+.*\*\*actual\*\*'; then
            echo "  EAD NOTICE: New session note in NEXT.md is missing **actual** field (P-182, L-484)"
            echo "    Add: - **actual**: <what actually happened>"
        fi
    fi
fi
