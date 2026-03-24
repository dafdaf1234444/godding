#!/bin/bash
# Tool-size gate (L-469, L-476): warn when staged tool files exceed T4 ceiling.
# Prevents maintenance.py-style unbounded growth (28k tokens = 47% of all drift).
T4_TOKEN_CEILING=5000
STAGED_TOOLS=$(git diff --cached --name-only 2>/dev/null | { grep '^tools/.*\.py$' || true; })
if [ -n "$STAGED_TOOLS" ]; then
    OVERSIZED=0
    while IFS= read -r tool_path; do
        if [ -f "$tool_path" ]; then
            CHARS=$(wc -c < "$tool_path" | tr -d ' ')
            EST_TOKENS=$((CHARS / 4))
            if [ "$EST_TOKENS" -gt "$T4_TOKEN_CEILING" ]; then
                echo "  NOTICE: ${tool_path} ~${EST_TOKENS}t exceeds T4 ceiling (${T4_TOKEN_CEILING}t) — consider splitting (L-469)"
                OVERSIZED=$((OVERSIZED + 1))
            fi
        fi
    done <<< "$STAGED_TOOLS"
    if [ "$OVERSIZED" -eq 0 ]; then
        echo "  Tool-size gate: PASS"
    else
        echo "  Tool-size gate: ${OVERSIZED} tool(s) over ceiling (NOTICE — not blocking)"
    fi
fi
