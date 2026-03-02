#!/usr/bin/env python3
"""Domain and frontier maintenance checks extracted from maintenance.py (DOMEX-META-S420).

Contains: check_domain_frontier_consistency, check_frontier_decay, check_anxiety_zones,
check_frontier_registry, check_domain_expert_coverage, check_historian_integrity.
These checks validate domain INDEX/FRONTIER alignment, frontier decay signals,
anxiety-zone detection, frontier ID registry integrity, DOMEX coverage gaps,
and historian grounding quality.
"""

import json
import re
from datetime import date
from pathlib import Path


def check_domain_frontier_consistency(
    REPO_ROOT: Path,
    _read,
    _truncated,
    _extract_domain_frontier_active_ids,
    _parse_domain_frontier_active_count,
    _parse_domain_index_active_count,
    _parse_domain_index_active_line_ids,
    _parse_domain_index_open_ids,
    _format_frontier_id_diff,
) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    domains_dir = REPO_ROOT / "domains"
    if not domains_dir.exists():
        return results

    frontier_header_mismatch: list[str] = []
    index_count_mismatch: list[str] = []
    index_active_line_mismatch: list[str] = []
    index_open_section_mismatch: list[str] = []

    for frontier_path in sorted(domains_dir.glob("*/tasks/FRONTIER.md")):
        domain = frontier_path.parent.parent.name
        frontier_text = _read(frontier_path)
        if not frontier_text:
            continue

        frontier_ids, has_active_section = _extract_domain_frontier_active_ids(frontier_text)
        frontier_count = len(frontier_ids)
        frontier_header_count = _parse_domain_frontier_active_count(frontier_text)
        if has_active_section and frontier_header_count is not None and frontier_header_count != frontier_count:
            frontier_header_mismatch.append(f"{domain}(header={frontier_header_count}, parsed={frontier_count})")

        index_path = frontier_path.parent.parent / "INDEX.md"
        if not index_path.exists():
            continue
        index_text = _read(index_path)
        if not index_text:
            continue

        index_count = _parse_domain_index_active_count(index_text)
        if index_count is not None and index_count != frontier_count:
            index_count_mismatch.append(f"{domain}(index={index_count}, frontier={frontier_count})")

        active_line_ids = _parse_domain_index_active_line_ids(index_text)
        if active_line_ids is not None and active_line_ids != frontier_ids:
            index_active_line_mismatch.append(f"{domain}({_format_frontier_id_diff(frontier_ids, active_line_ids)})")

        has_open_section, open_ids = _parse_domain_index_open_ids(index_text)
        if has_open_section and open_ids != frontier_ids:
            index_open_section_mismatch.append(f"{domain}({_format_frontier_id_diff(frontier_ids, open_ids)})")

    if frontier_header_mismatch:
        results.append(("NOTICE", f"Domain FRONTIER Active header mismatch: {_truncated(frontier_header_mismatch, 5)}"))
    if index_count_mismatch:
        results.append(("NOTICE", f"Domain INDEX active-count mismatch vs FRONTIER: {_truncated(index_count_mismatch, 5)}"))
    if index_active_line_mismatch:
        results.append(("NOTICE", f"Domain INDEX active frontier list mismatch: {_truncated(index_active_line_mismatch, 4)}"))
    if index_open_section_mismatch:
        results.append(("NOTICE", f"Domain INDEX 'What's open' mismatch: {_truncated(index_open_section_mismatch, 4)}"))

    return results


def check_frontier_decay(
    REPO_ROOT: Path,
    _read,
) -> list[tuple[str, str]]:
    results = []
    frontier_path = REPO_ROOT / "tasks" / "FRONTIER.md"
    decay_file = REPO_ROOT / "experiments" / "frontier-decay.json"
    if not frontier_path.exists(): return results
    open_text = _read(frontier_path).split("## Archive", 1)[0]
    try: decay = json.loads(_read(decay_file)) if decay_file.exists() else {}
    except Exception as e:
        results.append(("NOTICE", f"frontier-decay JSON parse failed ({decay_file.name}): {e}"))
        decay = {}
    open_ids = {f"F{m.group(1)}" for m in re.finditer(r"^- \*\*F(\d+)\*\*:", open_text, re.MULTILINE)}
    for fid in open_ids:
        decay.setdefault(fid, {"last_active": date.today().isoformat()})
    try:
        decay_file.parent.mkdir(parents=True, exist_ok=True)
        decay_file.write_text(json.dumps(decay, indent=2))
    except Exception: pass
    today = date.today()
    weak, archive = [], []
    for fid in sorted(open_ids):
        last = decay.get(fid, {}).get("last_active", today.isoformat())
        try: strength = 0.9 ** ((today - date.fromisoformat(last)).days)
        except Exception: strength = 1.0
        if strength < 0.1: archive.append(fid)
        elif strength < 0.3: weak.append(fid)
    if archive: results.append(("DUE", f"{len(archive)} frontier(s) below archive threshold: {', '.join(archive)}"))
    if weak: results.append(("NOTICE", f"{len(weak)} frontier(s) weakening: {', '.join(weak)}"))
    return results


def check_anxiety_zones(
    REPO_ROOT: Path,
    _read,
    _session_number,
) -> list[tuple[str, str]]:
    results = []
    current = _session_number()
    ANXIETY_THRESHOLD = 15
    frontier_path = REPO_ROOT / "tasks" / "FRONTIER.md"
    if not frontier_path.exists():
        return results
    open_text = _read(frontier_path).split("## Archive", 1)[0]
    anxiety_zones = []
    for match in re.finditer(r"^- \*\*(F[^*]+)\*\*:(.*?)(?=^- \*\*F|\Z)", open_text, re.MULTILINE | re.DOTALL):
        s_nums = [int(m) for m in re.findall(r"\bS(\d+)\b", match.group(2))]
        if not s_nums: continue
        last_active = max(s_nums)
        age = current - last_active
        if age > ANXIETY_THRESHOLD:
            anxiety_zones.append((match.group(1).strip(), last_active, age))
    if anxiety_zones:
        anxiety_zones.sort(key=lambda x: x[2], reverse=True)
        ids = ", ".join(f"{fid}(S{s},+{age})" for fid, s, age in anxiety_zones[:5])
        tail = f"... +{len(anxiety_zones)-5} more" if len(anxiety_zones) > 5 else ""
        results.append(("NOTICE", f"{len(anxiety_zones)} anxiety-zone frontier(s) open >{ANXIETY_THRESHOLD} sessions without update (F-COMM1: auto-trigger multi-expert synthesis): {ids}{tail}"))
    return results


def check_frontier_registry(
    REPO_ROOT: Path,
    _read,
    _truncated,
) -> list[tuple[str, str]]:
    results = []
    active_ids = [int(m.group(1)) for m in re.finditer(r"^- \*\*F(\d+)\*\*:", _read(REPO_ROOT / "tasks" / "FRONTIER.md"), re.MULTILINE)]
    archived_ids = [int(m.group(1)) for m in re.finditer(r"\|\s*F(\d+)\s*\|", _read(REPO_ROOT / "tasks" / "FRONTIER-ARCHIVE.md"))]
    def _dupes(ids):
        counts: dict[int, int] = {}
        for fid in ids: counts[fid] = counts.get(fid, 0) + 1
        return sorted((fid, c) for fid, c in counts.items() if c > 1)
    for label, dupes in (("FRONTIER", _dupes(active_ids)), ("FRONTIER-ARCHIVE", _dupes(archived_ids))):
        if dupes: results.append(("DUE", f"{label} duplicate ID(s): {_truncated(dupes, 5, fmt=lambda x: f'F{x[0]} x{x[1]}')}"))
    overlap = sorted(set(active_ids) & set(archived_ids))
    if overlap: results.append(("DUE", f"Frontier ID(s) both open and archived: {_truncated(overlap, 8, fmt=lambda x: f'F{x}')}"))
    return results


def check_domain_expert_coverage(
    REPO_ROOT: Path,
    _read,
) -> list[tuple[str, str]]:
    domains_dir = REPO_ROOT / "domains"
    lanes_path = REPO_ROOT / "tasks" / "SWARM-LANES.md"
    if not domains_dir.exists() or not lanes_path.exists():
        return []
    lanes_text = _read(lanes_path)
    uncovered = []
    for fp in sorted(domains_dir.glob("*/tasks/FRONTIER.md")):
        domain = fp.parts[-3]
        active_section = _read(fp).split("## Resolved", 1)[0].split("## Archive", 1)[0]
        if not re.search(r"^\s*[-*]\s*\*\*F", active_section, re.MULTILINE): continue
        if not [r for r in lanes_text.splitlines() if "DOMEX" in r and domain.lower() in r.lower() and "ABANDONED" not in r and "MERGED" not in r]:
            uncovered.append(domain)
    if uncovered:
        return [("NOTICE", f"Domain expert coverage gap ({len(uncovered)} domains with active frontiers but no DOMEX lane): {', '.join(uncovered)}")]
    return []


def check_historian_integrity(
    REPO_ROOT: Path,
    _read,
    PYTHON_EXE: str,
) -> list[tuple[str, str]]:
    results = []
    _his1_path = REPO_ROOT / "tools" / "f_his1_historian_grounding.py"
    if _his1_path.exists():
        try:
            import importlib.util as _ilu
            import sys as _sys
            _mod_name = "f_his1_historian_grounding"
            if _mod_name not in _sys.modules:
                _spec = _ilu.spec_from_file_location(_mod_name, _his1_path)
                _his1 = _ilu.module_from_spec(_spec)
                _sys.modules[_mod_name] = _his1
                _spec.loader.exec_module(_his1)
            else:
                _his1 = _sys.modules[_mod_name]
            lanes_text = _read(REPO_ROOT / "tasks" / "SWARM-LANES.md")
            rows = _his1.parse_rows(lanes_text)
            analysis = _his1.analyze(rows)
            score = analysis["mean_grounding_score"]
            active = analysis["active_lane_count"]
            if active >= 3 and score < 0.40:
                results.append(("DUE", f"historian grounding low: mean_score={score:.2f} across {active} active lanes (target >=0.5) -- run python3 tools/f_his1_historian_grounding.py"))
            elif active >= 3 and score < 0.60:
                results.append(("NOTICE", f"historian grounding below target: mean_score={score:.2f} across {active} lanes"))
        except Exception as e:
            results.append(("NOTICE", f"check_historian_integrity lane-check error: {e}"))

    SESSION_ANCHOR = re.compile(r"\bS\d{2,}\b")
    domains_dir = REPO_ROOT / "domains"
    if not domains_dir.exists():
        return results
    unanchored: list[str] = []
    total_active = 0
    for fp in sorted(domains_dir.glob("*/tasks/FRONTIER.md")):
        domain = fp.parts[-3]
        active_section = _read(fp).split("## Resolved", 1)[0].split("## Archive", 1)[0]
        lines = active_section.splitlines()
        i = 0
        while i < len(lines):
            m = re.match(r"\s*[-*]\s*\*\*(\S+)\*\*", lines[i])
            if m:
                total_active += 1
                block = [lines[i]]
                j = i + 1
                while j < len(lines):
                    nxt = lines[j]
                    if re.match(r"\s*[-*]\s*\*\*\S", nxt) or re.match(r"^##", nxt): break
                    block.append(nxt)
                    j += 1
                if not SESSION_ANCHOR.search("\n".join(block)):
                    unanchored.append(f"{domain}:{m.group(1)}")
                i = j
            else:
                i += 1
    if total_active > 0:
        rate = len(unanchored) / total_active
        sample = ", ".join(unanchored[:8])
        if rate > 0.70:
            results.append(("DUE", f"domain frontier historian gap: {len(unanchored)}/{total_active} active frontiers lack session anchor (SNN): {sample}"))
        elif rate > 0.40:
            results.append(("NOTICE", f"domain frontier historian partial: {len(unanchored)}/{total_active} unanchored: {sample}"))

    return results
