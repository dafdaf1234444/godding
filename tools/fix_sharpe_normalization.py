#!/usr/bin/env python3
"""Fix Sharpe normalization in dispatch_scoring.py (L-1622, L-1637).

The hardcoded constant 7.7 is below the actual global mean Sharpe (8.24, n=345),
inflating ALL domain dispatch scores by ~7%. This script patches dispatch_scoring.py
to compute global_mean_sharpe dynamically from outcome data.

Usage:
    python3 tools/fix_sharpe_normalization.py          # dry-run (shows diff)
    python3 tools/fix_sharpe_normalization.py --apply   # apply the fix
"""
import re
import sys
from pathlib import Path

TARGET = Path("tools/dispatch_scoring.py")

# Old code: hardcoded 7.7 in the global_avg computation
OLD_BLOCK_1 = """    # Global average quality (prior for unvisited domains) — Sharpe-weighted (L-1127)
    quality_scores = []
    for oc in outcome_map.values():
        n_oc = oc["merged"] + oc["abandoned"]
        if n_oc > 0:
            mr = oc["merged"] / n_oc
            s_sum = oc.get("sharpe_sum", 0)
            s_cnt = oc.get("sharpe_count", 0)
            sf = (s_sum / s_cnt / 7.7) if s_cnt > 0 else 1.0
            quality_scores.append(mr * (1 + math.log1p(oc.get("lessons", 0))) * sf)
    global_avg = sum(quality_scores) / len(quality_scores) if quality_scores else 1.0"""

NEW_BLOCK_1 = """    # Compute global mean Sharpe dynamically (L-1622: hardcoded 7.7 was below actual
    # mean 8.24, inflating ALL domain scores by ~7%). Self-calibrating normalization.
    _sharpe_sums, _sharpe_counts = [], []
    for oc in outcome_map.values():
        _s, _c = oc.get("sharpe_sum", 0), oc.get("sharpe_count", 0)
        if _c > 0:
            _sharpe_sums.append(_s)
            _sharpe_counts.append(_c)
    global_mean_sharpe = (sum(_sharpe_sums) / sum(_sharpe_counts)
                          if _sharpe_counts else 8.0)

    # Global average quality (prior for unvisited domains) — Sharpe-weighted (L-1127)
    quality_scores = []
    for oc in outcome_map.values():
        n_oc = oc["merged"] + oc["abandoned"]
        if n_oc > 0:
            mr = oc["merged"] / n_oc
            s_sum = oc.get("sharpe_sum", 0)
            s_cnt = oc.get("sharpe_count", 0)
            sf = (s_sum / s_cnt / global_mean_sharpe) if s_cnt > 0 else 1.0
            quality_scores.append(mr * (1 + math.log1p(oc.get("lessons", 0))) * sf)
    global_avg = sum(quality_scores) / len(quality_scores) if quality_scores else 1.0"""

# Old code: hardcoded 7.7 in per-domain scoring
OLD_BLOCK_2 = """            # Sharpe-weighted quality (L-1127 Channel 3 fix, L-1141): domains producing
            # high-Sharpe lessons get a quality multiplier. Normalised against
            # global avg Sharpe (~7.7). Falls back to 1.0 if no Sharpe data.
            sharpe_sum = oc.get("sharpe_sum", 0)
            sharpe_count = oc.get("sharpe_count", 0)
            avg_sharpe = sharpe_sum / sharpe_count if sharpe_count > 0 else 7.7
            sharpe_factor = avg_sharpe / 7.7  # >1.0 for high-quality domains"""

NEW_BLOCK_2 = """            # Sharpe-weighted quality (L-1127 Channel 3 fix, L-1141): domains producing
            # high-Sharpe lessons get a quality multiplier. Normalised against
            # global mean Sharpe (dynamic, L-1622). Falls back to 1.0 if no Sharpe data.
            sharpe_sum = oc.get("sharpe_sum", 0)
            sharpe_count = oc.get("sharpe_count", 0)
            avg_sharpe = sharpe_sum / sharpe_count if sharpe_count > 0 else global_mean_sharpe
            sharpe_factor = avg_sharpe / global_mean_sharpe"""


def main():
    apply = "--apply" in sys.argv
    content = TARGET.read_text()

    if OLD_BLOCK_1 not in content:
        if NEW_BLOCK_1 in content:
            print("Block 1 already patched.")
        else:
            print("ERROR: Block 1 not found — file may have changed.")
            sys.exit(1)
    else:
        content = content.replace(OLD_BLOCK_1, NEW_BLOCK_1, 1)
        print("Block 1: will replace hardcoded 7.7 with dynamic global_mean_sharpe")

    if OLD_BLOCK_2 not in content:
        if NEW_BLOCK_2 in content:
            print("Block 2 already patched.")
        else:
            print("ERROR: Block 2 not found — file may have changed.")
            sys.exit(1)
    else:
        content = content.replace(OLD_BLOCK_2, NEW_BLOCK_2, 1)
        print("Block 2: will replace per-domain 7.7 with global_mean_sharpe")

    if apply:
        TARGET.write_text(content)
        print(f"Applied fix to {TARGET}")
    else:
        print("\nDry run — use --apply to write changes.")


if __name__ == "__main__":
    main()
