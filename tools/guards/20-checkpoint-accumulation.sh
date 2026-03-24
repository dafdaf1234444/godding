#!/bin/bash
# FM-06: PreCompact checkpoint accumulation guard (S445, FM-06 second defense layer).
# NOTICE when checkpoint files accumulate beyond 20 (orphaned from interrupted compactions).
CHECKPOINT_COUNT=$(ls workspace/precompact-checkpoint-*.json 2>/dev/null | wc -l || echo 0)
if [ "${CHECKPOINT_COUNT}" -gt 20 ]; then
    echo "  FM-06 NOTICE: ${CHECKPOINT_COUNT} precompact checkpoints accumulated — run 'python3 tools/compact.py --cleanup-checkpoints' to prune (FM-06)"
fi
