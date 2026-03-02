#!/usr/bin/env python3
"""Lane-related maintenance checks extracted from maintenance.py (DOMEX-META-S420).

Contains: check_swarm_lanes, check_swarm_coordinator, check_lane_reporting_quality.
These checks validate SWARM-LANES.md lane hygiene: staleness, metadata completeness,
coordination contract, evidence fields, collision detection, and historian grounding.
"""

import re


def check_swarm_lanes(
    _active_lane_rows,
    _session_number,
    _parse_lane_tags,
    _is_lane_placeholder,
    _lane_high_risk_signal,
    _truncated,
    LANE_ACTIVE_STATUSES,
    LANE_STALE_NOTICE_SESSIONS,
    LANE_STALE_DUE_SESSIONS,
    LANE_ANTIWINDUP_ROWS,
    DOMAIN_SYNC_ALLOWED_VALUES,
    LANE_AVAILABLE_ALLOWED_VALUES,
    LANE_AVAILABLE_LEGACY_MAP,
    LANE_GLOBAL_FOCUS_VALUES,
) -> list[tuple[str, str]]:
    results = []
    parsed = _active_lane_rows()
    if not parsed: return results
    rows, active = parsed

    current_session = _session_number()
    stale_notice: list[str] = []
    stale_due: list[str] = []
    if current_session > 0:
        for row in active:
            lane = row.get("lane", "").strip() or "<unknown>"
            m = re.search(r"S(\d+)", row.get("session", ""))
            if not m: continue
            lane_session = int(m.group(1)); age = current_session - lane_session
            if age > LANE_STALE_DUE_SESSIONS: stale_due.append(f"{lane}(S{lane_session},+{age})")
            elif age > LANE_STALE_NOTICE_SESSIONS: stale_notice.append(f"{lane}(S{lane_session},+{age})")
    if stale_due: results.append(("DUE", f"{len(stale_due)} active lane(s) stale >{LANE_STALE_DUE_SESSIONS} sessions: {_truncated(stale_due, 5)}"))
    if stale_notice: results.append(("NOTICE", f"{len(stale_notice)} active lane(s) stale >{LANE_STALE_NOTICE_SESSIONS} sessions: {_truncated(stale_notice, 5)}"))

    row_counts: dict[str, int] = {}
    for row in rows:
        lane = row.get("lane", "").strip()
        if lane: row_counts[lane] = row_counts.get(lane, 0) + 1
    antiwindup = [f"{(row.get('lane','').strip() or '<unknown>')}({row_counts.get(row.get('lane','').strip(),0)}rows)"
                  for row in active if row_counts.get(row.get("lane", "").strip(), 0) >= LANE_ANTIWINDUP_ROWS]
    if antiwindup: results.append(("NOTICE", f"{len(antiwindup)} active lane(s) with >={LANE_ANTIWINDUP_ROWS} total rows (anti-windup, consider ABANDONED): {_truncated(antiwindup, 5)}"))

    latest_active: dict[str, dict] = {}
    for row in active: latest_active[row.get("lane", "")] = row
    missing_meta = [f"{row.get('lane')}({','.join(lbl for key, lbl in (('branch','branch'),('model','model'),('platform','platform'),('scope_key','scope')) if _is_lane_placeholder(row.get(key,'')))})"
                   for row in sorted(latest_active.values(), key=lambda item: item.get("lane", ""))
                   if any(_is_lane_placeholder(row.get(k, "")) for k in ("branch", "model", "platform", "scope_key"))]
    if missing_meta: results.append(("NOTICE", f"{len(missing_meta)} active lane(s) missing metadata: {_truncated(missing_meta, 5)}"))

    missing_coordination_tags: list[str] = []
    missing_domain_memory_tags: list[str] = []
    invalid_domain_sync_tags: list[str] = []
    invalid_available_tags: list[str] = []
    legacy_available_tags: list[str] = []
    high_risk_missing_human: list[str] = []
    setup_values: set[str] = set()
    has_global_focus = False
    for row in active:
        lane = row.get("lane", "").strip() or "<unknown>"
        tags = _parse_lane_tags(row.get("etc", ""))
        domain_focus = next((m.group(1) for raw in (tags.get("focus", ""), row.get("scope_key", ""))
                             for m in [re.search(r"domains/([a-z0-9][a-z0-9-]*)", (raw or "").strip().lower())] if m), None)
        if domain_focus:
            domain_missing = []
            domain_sync = tags.get("domain_sync", "").strip().lower()
            memory_target = tags.get("memory_target", "").strip().lower()
            if _is_lane_placeholder(domain_sync): domain_missing.append("domain_sync")
            elif domain_sync not in DOMAIN_SYNC_ALLOWED_VALUES: invalid_domain_sync_tags.append(f"{lane}(domain_sync={domain_sync})")
            if _is_lane_placeholder(memory_target): domain_missing.append("memory_target")
            if domain_missing: missing_domain_memory_tags.append(f"{lane}({','.join(domain_missing)})")
        missing = [k for k in ("setup", "focus") if _is_lane_placeholder(tags.get(k, ""))]
        if not any(k in tags for k in ("available", "capacity", "availability", "ready")): missing.append("available")
        if not any(k in tags for k in ("blocked", "blocker")): missing.append("blocked")
        if not any(k in tags for k in ("next_step", "next", "action", "plan")): missing.append("next_step")
        if not any(k in tags for k in ("human_open_item", "human_open")): missing.append("human_open_item")
        if missing: missing_coordination_tags.append(f"{lane}({','.join(missing)})"); continue

        human_open_value = (tags.get("human_open_item", "") or tags.get("human_open", "")).strip().lower()
        high_risk_signal = _lane_high_risk_signal(row, tags)
        if high_risk_signal and _is_lane_placeholder(human_open_value): high_risk_missing_human.append(f"{lane}({high_risk_signal})")
        available_raw = (tags.get("available", "") or "").strip().lower()
        if available_raw:
            if available_raw in LANE_AVAILABLE_LEGACY_MAP: legacy_available_tags.append(f"{lane}(available={available_raw}->{LANE_AVAILABLE_LEGACY_MAP[available_raw]})")
            elif available_raw not in LANE_AVAILABLE_ALLOWED_VALUES: invalid_available_tags.append(f"{lane}(available={available_raw})")

        setup_value = tags.get("setup", "").strip().lower()
        focus_value = tags.get("focus", "").strip().lower()
        setup_values.add(setup_value)
        if focus_value in LANE_GLOBAL_FOCUS_VALUES:
            has_global_focus = True

    if missing_coordination_tags:
        results.append(("DUE", f"{len(missing_coordination_tags)} active lane(s) missing coordination contract tags (setup/focus/available/blocked/next_step/human_open_item): {_truncated(missing_coordination_tags, 5)}"))
    if missing_domain_memory_tags:
        results.append(("DUE", f"{len(missing_domain_memory_tags)} active domain-focused lane(s) missing domain-memory coordination tags (domain_sync/memory_target): {_truncated(missing_domain_memory_tags, 5)}"))
    if invalid_domain_sync_tags:
        results.append(("NOTICE", f"{len(invalid_domain_sync_tags)} active domain-focused lane(s) with invalid domain_sync value (allowed: {','.join(sorted(DOMAIN_SYNC_ALLOWED_VALUES))}): {_truncated(invalid_domain_sync_tags, 5)}"))
    if invalid_available_tags:
        results.append(("DUE", f"{len(invalid_available_tags)} active lane(s) with invalid available value (allowed: {','.join(sorted(LANE_AVAILABLE_ALLOWED_VALUES))}): {_truncated(invalid_available_tags, 5)}"))
    if legacy_available_tags:
        results.append(("NOTICE", f"{len(legacy_available_tags)} active lane(s) using legacy available value (normalize to {','.join(sorted(LANE_AVAILABLE_ALLOWED_VALUES))}): {_truncated(legacy_available_tags, 5)}"))
    if high_risk_missing_human:
        results.append(("DUE", f"{len(high_risk_missing_human)} active lane(s) declare high-risk intent without `human_open_item=HQ-N` (MC-SAFE): {_truncated(high_risk_missing_human, 5)}"))

    missing_evidence_tags: list[str] = []
    for row in active:
        lane = row.get("lane", "").strip() or "<unknown>"
        tags = _parse_lane_tags(row.get("etc", ""))
        missing_ev = [k for k in ("expect", "artifact") if not tags.get(k, "").strip()]
        if missing_ev:
            missing_evidence_tags.append(f"{lane}({','.join(missing_ev)})")
    if missing_evidence_tags:
        results.append(("NOTICE", f"{len(missing_evidence_tags)} active lane(s) missing evidence fields (expect/artifact -- use open_lane.py, F-META1 S331): {_truncated(missing_evidence_tags, 5)}"))

    if len(setup_values) > 1 and not has_global_focus:
        results.append(("NOTICE", "Multi-setup active lanes have no global coordination focus (`focus=global|system|coordination`) in Etc"))

    # Branch values that are non-collidable trunk names (all sessions share them)
    _TRUNK_BRANCHES = {"master", "main"}

    def _detect_collisions(key_field: str, label: str) -> None:
        mapping: dict[str, set[str]] = {}
        for row in active:
            lane = row.get("lane", "")
            val = row.get(key_field, "").strip().lower()
            if not _is_lane_placeholder(val) and val not in _TRUNK_BRANCHES:
                mapping.setdefault(val, set()).add(lane)
        conflicts = sorted((k, sorted(v)) for k, v in mapping.items() if len(v) > 1)
        if conflicts:
            sample = "; ".join(f"{k}:{'/'.join(v[:3])}" for k, v in conflicts[:3])
            results.append(("DUE", f"Active lane {label} collision(s): {sample}"))

    _detect_collisions("branch", "branch")
    _detect_collisions("scope", "scope")

    return results


def check_swarm_coordinator(
    _active_lane_rows,
    _parse_lane_tags,
    _lane_has_any_tag,
    _truncated,
    LANE_GLOBAL_FOCUS_VALUES,
) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    parsed = _active_lane_rows()
    if not parsed: return results
    _, active = parsed
    if len(active) < 2:
        return results

    dispatch_rows: list[tuple[dict[str, str], dict[str, str]]] = []
    coordinator_rows: list[tuple[dict[str, str], dict[str, str]]] = []
    for row in active:
        tags = _parse_lane_tags(row.get("etc", ""))
        lane_low = (row.get("lane", "") or "").strip().lower()
        if any(k in tags for k in ("dispatch", "slot", "wip_cap")) or re.search(r"(?:^|[-_/])(msw\d*|domex|slot)(?:$|[-_/])", lane_low):
            dispatch_rows.append((row, tags))
        scope_low = (row.get("scope_key", "") or "").strip().lower()
        if re.search(r"(?:^|[-_/])(coord|coordinator)(?:$|[-_/])", lane_low) or "coordinator" in scope_low or "tasks/swarm-lanes.md" in scope_low:
            coordinator_rows.append((row, tags))

    # Single dispatch lane can run without a dedicated coordinator row; fan-out swarms cannot.
    if len(dispatch_rows) < 2:
        return results

    if not coordinator_rows:
        dispatch_lanes = [row.get("lane", "").strip() or "<unknown>" for row, _ in dispatch_rows]
        results.append(("DUE", f"{len(dispatch_rows)} active dispatch lane(s) have no active coordinator lane: {_truncated(dispatch_lanes, 5)}"))
        return results

    missing_contract: list[str] = []
    for row, tags in coordinator_rows:
        lane = row.get("lane", "").strip() or "<unknown>"
        missing: list[str] = []
        if tags.get("focus", "").strip().lower() not in LANE_GLOBAL_FOCUS_VALUES: missing.append("focus")
        if not _lane_has_any_tag(tags, ("intent", "objective", "goal")): missing.append("intent")
        if not _lane_has_any_tag(tags, ("progress", "status_note", "evidence", "artifact")): missing.append("progress")
        if not _lane_has_any_tag(tags, ("available", "capacity", "availability", "ready")): missing.append("available")
        if not _lane_has_any_tag(tags, ("blocked", "blocker")): missing.append("blocked")
        if not _lane_has_any_tag(tags, ("next_step", "next", "action", "plan")): missing.append("next_step")
        if not _lane_has_any_tag(tags, ("human_open_item", "human_open")): missing.append("human_open_item")
        if not _lane_has_any_tag(tags, ("check_focus",)): missing.append("check_focus")
        if missing: missing_contract.append(f"{lane}({','.join(missing)})")

    if missing_contract:
        results.append(("DUE", f"{len(missing_contract)} coordinator lane(s) missing coordinator contract fields (focus,intent,progress,available,blocked,next_step,human_open_item,check_focus): {_truncated(missing_contract, 5)}"))

    return results


def check_lane_reporting_quality(
    _active_lane_rows,
    _parse_lane_tags,
    _is_lane_placeholder,
    _truncated,
    LANE_REPORT_KEYS,
    CHECK_FOCUS_HISTORIAN_REQUIRED,
    HISTORIAN_SELF_ANCHOR_TOKENS,
    HISTORIAN_SURROUNDINGS_ANCHOR_TOKENS,
) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    parsed = _active_lane_rows()
    if not parsed: return results
    _, active = parsed

    missing_contract: list[str] = []
    missing_historian_contract: list[str] = []
    explicit_counts = {key: 0 for key in LANE_REPORT_KEYS}
    dispatchable = 0

    for row in sorted(active, key=lambda item: item.get("lane", "")):
        lane = row.get("lane", "").strip() or "<unknown>"
        tags = _parse_lane_tags(row.get("etc", ""))

        fields = {
            "capabilities": (
                not _is_lane_placeholder(row.get("model", ""))
                and not _is_lane_placeholder(row.get("platform", ""))
                and not _is_lane_placeholder(tags.get("setup", ""))
            ),
            "intent": any(k in tags for k in ("intent", "objective", "goal", "frontier", "dispatch", "task")),
            "progress": any(k in tags for k in ("progress", "status_note", "evidence", "artifact")),
            "available": any(k in tags for k in ("available", "capacity", "availability", "ready")),
            "blocked": "blocked" in tags or "blocker" in tags,
            "next_step": any(k in tags for k in ("next_step", "next", "action", "plan")),
            "human_open_item": "human_open_item" in tags or "human_open" in tags,
        }

        missing = [key for key in LANE_REPORT_KEYS if not fields[key]]
        if missing:
            missing_contract.append(f"{lane}({','.join(missing)})")
        else:
            dispatchable += 1
        for key, present in fields.items():
            if present:
                explicit_counts[key] += 1

        check_modes = {tok for tok in re.split(r"[+,/;|]+", (tags.get("check_focus", "") or "").strip().lower()) if tok}
        if check_modes & CHECK_FOCUS_HISTORIAN_REQUIRED:
            if "objective" in check_modes and _is_lane_placeholder(tags.get("objective_check", "")):
                missing_historian_contract.append(f"{lane}(objective_check)")
            historian_raw = tags.get("historian_check", "")
            if _is_lane_placeholder(historian_raw):
                missing_historian_contract.append(f"{lane}(historian_check)")
            else:
                _hlow = (historian_raw or "").strip().lower()
                has_self = any(t in _hlow for t in HISTORIAN_SELF_ANCHOR_TOKENS)
                has_surroundings = any(t in _hlow for t in HISTORIAN_SURROUNDINGS_ANCHOR_TOKENS)
                anchor_missing: list[str] = []
                if not has_self:
                    anchor_missing.append("self_anchor")
                if not has_surroundings:
                    anchor_missing.append("surroundings_anchor")
                if anchor_missing:
                    missing_historian_contract.append(f"{lane}({','.join(anchor_missing)})")

    lane_count = len(active)
    dispatchable_rate = dispatchable / lane_count if lane_count else 0.0
    if missing_contract:
        severity = "DUE" if dispatchable_rate < 0.5 else "NOTICE"
        results.append((severity, f"{len(missing_contract)} active lane(s) missing explicit reporting contract fields ({dispatchable}/{lane_count} dispatchable): {_truncated(missing_contract, 5)}"))
        weakest = sorted(explicit_counts.items(), key=lambda item: (item[1], item[0]))[:3]
        if weakest:
            results.append(("NOTICE", f"Lane explicit-reporting weakest keys: {', '.join(f'{k}={c}/{lane_count}' for k, c in weakest)}"))

    if missing_historian_contract:
        results.append(("DUE", f"{len(missing_historian_contract)} active lane(s) with historian/objective check focus missing historian grounding (self+surroundings anchors): {_truncated(missing_historian_contract, 5)}"))

    return results
