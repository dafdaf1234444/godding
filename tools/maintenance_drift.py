#!/usr/bin/env python3
"""Drift and observer staleness checks extracted from maintenance.py (DOMEX-META-S420).

Contains: check_proxy_k_drift, check_observer_staleness.
These checks monitor proxy-K token drift against baselines (with dirty-tree
handling, stale-floor rebaselining) and flag observer baselines that have
aged beyond usefulness.
"""

import hashlib
import json
import re
from pathlib import Path


def check_proxy_k_drift(
    REPO_ROOT: Path,
    PYTHON_CMD: str,
    _read,
    _git,
    _token_count,
    _session_number,
) -> list[tuple[str, str]]:
    results = []
    log_path = REPO_ROOT / "experiments" / "proxy-k-log.json"
    if not log_path.exists():
        return results

    try:
        entries = json.loads(_read(log_path))
    except Exception as e:
        return [("NOTICE", f"proxy-k-log.json parse failed: {e}")]

    if len(entries) < 2:
        return results

    tiers = {
        "T0-mandatory": ["SWARM.md", "CLAUDE.md", "beliefs/CORE.md", "memory/INDEX.md"],
        "T1-identity": ["beliefs/PHILOSOPHY.md", "beliefs/DEPS.md", "beliefs/INVARIANTS.md"],
        "T2-protocols": ["memory/DISTILL.md", "memory/VERIFY.md", "memory/OPERATIONS.md", "beliefs/CONFLICTS.md"],
        "T3-knowledge": ["memory/PRINCIPLES.md", "tasks/FRONTIER.md"],
        "T4-tools": ["tools/validate_beliefs.py", "tools/maintenance.py", "tools/paper_drift.py", "tools/swarm_parse.py"],
    }
    schema_payload = json.dumps(tiers, sort_keys=True, separators=(",", ":")).encode("utf-8")
    current_schema = hashlib.sha256(schema_payload).hexdigest()
    schema_entries = [e for e in entries if e.get("tier_schema") == current_schema]
    clean_schema_entries = [e for e in schema_entries if not e.get("dirty_tree")]
    baseline = clean_schema_entries if len(clean_schema_entries) >= 2 else schema_entries
    if len(baseline) < 2:
        n = len(schema_entries)
        results.append(("NOTICE",
            f"Proxy K schema baseline unavailable ({n} matching snapshot{'s' if n != 1 else ''}); run clean snapshots: {PYTHON_CMD} tools/proxy_k.py --save"))
        return results

    floor_idx = 0
    for i in range(1, len(baseline)):
        if baseline[i]["total"] < baseline[i - 1]["total"]:
            floor_idx = i

    floor_entry = baseline[floor_idx]
    floor = floor_entry["total"]
    if floor <= 0:
        return results

    # If the historical-minimum floor is stale (>= 8 sessions ago) and a more
    # recent clean baseline exists, use that as the floor to acknowledge
    # intentional tool growth without triggering false URGENT compaction. (L-273)
    _cur_s = _session_number()
    _floor_s = int(floor_entry.get("session", 0) or 0)
    if len(clean_schema_entries) >= 2 and _floor_s > 0 and _cur_s > 0 and (_cur_s - _floor_s) >= 8:
        _newer = [e for e in clean_schema_entries if int(e.get("session", 0) or 0) > _floor_s]
        if _newer:
            _latest_clean = max(_newer, key=lambda e: int(e.get("session", 0) or 0))
            if _latest_clean["total"] > floor:
                floor_entry = _latest_clean
                floor = _latest_clean["total"]

    # If floor is very stale (>50 sessions), check dirty entries for more
    # recent post-compaction baselines (where total decreased from prior).
    # Prevents false URGENT signals from legitimate tool growth. (L-550, L-555)
    _floor_s_post = int(floor_entry.get("session", 0) or 0)
    if _cur_s > 0 and _floor_s_post > 0 and (_cur_s - _floor_s_post) > 50:
        for i in range(len(schema_entries) - 1, 0, -1):
            if schema_entries[i]["total"] < schema_entries[i - 1]["total"]:
                _df = schema_entries[i]
                _df_total = _df["total"]
                _df_s = int(_df.get("session", 0) or 0)
                if _df_total > floor and _df_s > _floor_s_post:
                    floor_entry = _df
                    floor = _df_total
                break

    live_tiers: dict[str, int] = {}
    live_total = 0
    for tier, files in tiers.items():
        tier_total = sum(_token_count(REPO_ROOT / f) for f in files)
        live_tiers[tier] = tier_total
        live_total += tier_total

    latest_entry = entries[-1]
    latest_logged = latest_entry["total"]
    latest_session = int(latest_entry.get("session", 0) or 0)
    latest_marked_dirty = bool(latest_entry.get("dirty_tree", False))
    floor_session = int(floor_entry.get("session", 0) or 0)
    current_session = _session_number()
    logged_drift = (latest_logged - floor) / floor
    live_drift = (live_total - floor) / floor
    dirty = bool(_git("status", "--porcelain"))
    stale_clean_baseline = dirty and floor_session > 0 and current_session > 0 and (current_session - floor_session) >= 8

    likely_dirty_logged = latest_marked_dirty
    if not likely_dirty_logged and dirty and latest_session > 0 and current_session > 0:
        if latest_session >= max(0, current_session - 2) and abs(latest_logged - live_total) / max(1, live_total) <= 0.02:
            likely_dirty_logged = True
    same_dirty_snapshot = (likely_dirty_logged and dirty and current_session > 0
        and latest_session >= max(0, current_session - 2)
        and abs(live_total - latest_logged) / max(1, latest_logged) <= 0.01)

    def _tier_targets() -> str:
        floor_tiers = floor_entry.get("tiers", {})
        tier_deltas = [f"{tier}+{live_tiers.get(tier,0)-floor_tiers.get(tier,0)}" for tier in sorted(live_tiers) if live_tiers.get(tier,0) - floor_tiers.get(tier,0) > 0]
        return f" [{', '.join(tier_deltas[:3])}]" if tier_deltas else ""

    if logged_drift > 0.06:
        if dirty and live_drift <= 0.06:
            results.append(("NOTICE", f"Proxy K logged drift {logged_drift:.1%} ({latest_logged} vs {floor}) but live drift is {live_drift:.1%} on dirty tree; re-save clean snapshot: {PYTHON_CMD} tools/proxy_k.py --save"))
        elif likely_dirty_logged:
            if logged_drift > 0.10:
                results.append(("URGENT" if logged_drift > 0.20 else "DUE", f"Proxy K drift {logged_drift:.1%} ({latest_logged} vs {floor}) on dirty tree -- compaction overdue{_tier_targets()}; run: {PYTHON_CMD} tools/compact.py"))
            elif not same_dirty_snapshot:
                qualifier = "current dirty" if (current_session > 0 and latest_session >= current_session) else f"likely dirty S{latest_session}"
                results.append(("NOTICE", f"Proxy K logged drift {logged_drift:.1%} ({latest_logged} vs {floor}) from {qualifier}; save clean snapshot when stable: {PYTHON_CMD} tools/proxy_k.py --save"))
        elif stale_clean_baseline:
            results.append(("NOTICE", f"Proxy K baseline S{floor_session} is stale on dirty tree (current S{current_session}); re-save clean snapshot: {PYTHON_CMD} tools/proxy_k.py --save"))
        else:
            results.append(("URGENT" if logged_drift > 0.10 else "DUE", f"Proxy K drift {logged_drift:.1%} ({latest_logged} vs {floor}); run: {PYTHON_CMD} tools/compact.py"))
    elif live_drift > 0.06 and dirty:
        results.append(("NOTICE", f"Proxy K live drift {live_drift:.1%} ({live_total} vs {floor}) on dirty tree{_tier_targets()}; save when stable: {PYTHON_CMD} tools/proxy_k.py --save"))
    elif live_drift > 0.06:
        results.append(("URGENT" if live_drift > 0.10 else "DUE", f"Proxy K drift {live_drift:.1%} ({live_total} vs {floor}){_tier_targets()}; run: {PYTHON_CMD} tools/compact.py"))

    return results


def check_observer_staleness(
    REPO_ROOT: Path,
) -> list[tuple[str, str]]:
    """L-820, L-556, FM-20: detect measurement tools with stale baselines.

    Observers that compare current state to a stored baseline drift silently
    when the baseline ages. Mean staleness was 63 sessions (L-820). This check
    flags any observer baseline older than its threshold.

    Three detection layers (L-966, DOMEX-CAT-S425):
    1. Data-file baselines: proxy-K log, dispatch calibration, compaction floor
    2. Source-code baselines: hardcoded S-numbers in tool .py files
    3. Experiment artifact baselines: session-stamped JSON files tools depend on
    """
    results: list[tuple[str, str]] = []
    # Extract current session number — INDEX.md uses "Sessions: NNN" format
    # L-966: original regex S(\d+) never matched, causing 0 firings in 27+ sessions
    sess = 0
    try:
        idx = (REPO_ROOT / "memory" / "INDEX.md").read_text(encoding="utf-8", errors="replace")
        m = re.search(r"Sessions:\s*(\d+)", idx)
        if not m:
            m = re.search(r"\bS(\d+)\b", idx)
        if m:
            sess = int(m.group(1))
    except Exception:
        return []
    if sess < 50:
        return []

    stale: list[str] = []
    threshold = 50  # sessions — data file baselines

    # --- Layer 1: Data-file baselines ---

    # Check proxy-K baseline in proxy-k-log
    pk_data = None
    try:
        pk_path = REPO_ROOT / "experiments" / "proxy-k-log.json"
        if pk_path.exists():
            pk_data = json.loads(pk_path.read_text(encoding="utf-8", errors="replace"))
            if isinstance(pk_data, list) and pk_data:
                last_entry = pk_data[-1]
                last_sess_m = re.search(r"S(\d+)", str(last_entry.get("session", "")))
                if last_sess_m:
                    age = sess - int(last_sess_m.group(1))
                    if age > threshold:
                        stale.append(f"proxy-K({age}s)")
    except Exception:
        pass

    # Check dispatch calibration baseline
    try:
        dc_path = REPO_ROOT / "workspace" / "dispatch_calibration.json"
        if dc_path.exists():
            dc_data = json.loads(dc_path.read_text(encoding="utf-8", errors="replace"))
            cal_sess_m = re.search(r"S(\d+)", str(dc_data.get("calibrated_session", "")))
            if cal_sess_m:
                age = sess - int(cal_sess_m.group(1))
                if age > threshold:
                    stale.append(f"dispatch-calibration({age}s)")
    except Exception:
        pass

    # Check compact.py floor baseline
    try:
        for pk_entry in reversed(pk_data if pk_data is not None else []):
            if isinstance(pk_entry, dict) and pk_entry.get("floor"):
                floor_sess_m = re.search(r"S(\d+)", str(pk_entry.get("session", "")))
                if floor_sess_m:
                    age = sess - int(floor_sess_m.group(1))
                    if age > threshold:
                        stale.append(f"compaction-floor({age}s)")
                break
    except Exception:
        pass

    # --- Layer 2: Source-code baselines (FM-20, L-966, L-977) ---
    # Scan tool .py files for hardcoded S\d{3,} references in baseline context.
    # L-977: 71% FP rate at S427 — docstrings, examples, historical notes flagged.
    # Fix: only flag S-numbers on lines containing baseline keywords.
    source_threshold = 80  # source hardcodes have higher inertia
    _baseline_kw = re.compile(
        r"\b(?:baseline|floor|count|rate|default|fallback|sink|threshold|measured|estimated)\b",
        re.IGNORECASE,
    )
    _skip_kw = re.compile(
        r'help=|Example|example|e\.g\.|usage:|argparse|format\b|\bor\s+S\d',
        re.IGNORECASE,
    )
    exclude_files = {
        "maintenance_drift.py", "maintenance.py", "sync_state.py",
        "orient.py", "orient_sections.py", "orient_state.py",
        "orient_checks.py", "close_lane.py", "open_lane.py",
        "validate_beliefs.py", "lane_history.py",
    }
    tool_dir = REPO_ROOT / "tools"
    if tool_dir.exists():
        for py_file in sorted(tool_dir.glob("*.py")):
            if py_file.name in exclude_files or py_file.name.startswith("test_"):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="replace")
                baseline_sessions = []
                for line in content.splitlines():
                    if _skip_kw.search(line):
                        continue
                    if not _baseline_kw.search(line):
                        continue
                    for m in re.finditer(r"\bS(\d{3,})\b", line):
                        baseline_sessions.append(int(m.group(1)))
                if not baseline_sessions:
                    continue
                max_s = max(baseline_sessions)
                age = sess - max_s
                if age > source_threshold:
                    stale.append(f"{py_file.name}(S{max_s},{age}s)")
            except Exception:
                pass

    # --- Layer 3: Experiment artifact baselines ---
    # Dynamic: find the latest baseline file per pattern (not hardcoded path)
    baseline_patterns = [
        ("experiments/conflict", "f-con1-baseline-s*.json", "C1-conflict-baseline"),
    ]
    for rel_dir, pattern, label in baseline_patterns:
        art_dir = REPO_ROOT / rel_dir
        if not art_dir.exists():
            continue
        candidates = sorted(art_dir.glob(pattern))
        if not candidates:
            continue
        latest = candidates[-1]  # sorted alphabetically, s429 > s189
        art_m = re.search(r"[sS](\d{3,})", latest.name)
        if art_m:
            age = sess - int(art_m.group(1))
            if age > threshold:
                stale.append(f"{label}(S{art_m.group(1)},{age}s)")

    if stale:
        has_critical = any(
            "," in s and int(s.split(",")[1].rstrip("s)")) > 150
            for s in stale
        )
        severity = "URGENT" if has_critical else "DUE" if len(stale) >= 2 else "NOTICE"
        return [(severity, f"{len(stale)} observer baseline(s) stale: {', '.join(stale)}. "
                 f"Refresh to prevent drift blindness (L-820, FM-20)")]
    return []
