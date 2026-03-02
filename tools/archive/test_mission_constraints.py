#!/usr/bin/env python3
"""Regression tests for F119 mission constraint checks (invariants, portability, learning quality)."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    # Repo-root invocation (e.g., `python3 -m unittest tools/test_mission_constraints.py`).
    from tools import maintenance  # type: ignore
except Exception:
    # tools/ cwd invocation (e.g., `cd tools && python3 test_mission_constraints.py`).
    import maintenance  # type: ignore


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_repo(root: Path, next_body: str) -> None:
    _write(
        root / "tasks/FRONTIER.md",
        "# Frontier\n- **F119**: mission constraints\n",
    )
    _write(root / "tasks/NEXT.md", next_body)
    _write(
        root / "memory/SESSION-LOG.md",
        "S156 | 2026-02-27 | runtime portability fallback with Beliefs PASS\n",
    )
    _write(
        root / "beliefs/INVARIANTS.md",
        "\n".join(
            [
                "## I9 [MC-SAFE]",
                "## I10 [MC-PORT]",
                "## I11 [MC-LEARN]",
                "## I12 [MC-CONN]",
                "",
            ]
        ),
    )
    _write(root / "tools/check.sh", "choose_python() { :; }\npython3\npython\npy -3\n")
    _write(root / "tools/maintenance.sh", "#!/bin/bash\n")
    _write(root / "tools/check.ps1", "# powershell check wrapper\n")
    _write(root / "tools/maintenance.ps1", "# powershell maintenance wrapper\n")
    _write(root / "tools/bulletin.py", "# stub\n")
    _write(root / "tools/merge_back.py", "# stub\n")
    _write(root / "tools/propagate_challenges.py", "# stub\n")
    _write(
        root / "tools/maintenance.py",
        "\n".join(
            [
                "def check_validator(): pass",
                "def check_runtime_portability(): pass",
                "def check_cross_references(): pass",
                "def check_structure_layout(): pass",
                "def check_state_header_sync(): pass",
                "def check_session_log_integrity(): pass",
                "def check_child_bulletins(): pass",
                "def check_help_requests(): pass",
                "def check_swarm_lanes(): pass",
                "def check_swarm_coordinator(): pass",
                "def check_lane_reporting_quality(): pass",
                "all_checks = [",
                "    check_validator,",
                "    check_runtime_portability,",
                "    check_cross_references,",
                "    check_structure_layout,",
                "    check_state_header_sync,",
                "    check_session_log_integrity,",
                "    check_child_bulletins,",
                "    check_help_requests,",
                "    check_swarm_lanes,",
                "    check_swarm_coordinator,",
                "    check_lane_reporting_quality,",
                "]",
                "",
            ]
        ),
    )


class TestMissionConstraintInvariantChecks(unittest.TestCase):
    """Tests for current check_mission_constraints invariant validation."""

    def _run_check(self, *, invariants_text="", frontier_text="", next_text="",
                   check_sh_text="", python_ok=True, git_status=""):
        def fake_read(path):
            rel = str(path).replace("\\", "/")
            if "INVARIANTS" in rel:
                return invariants_text
            if "FRONTIER" in rel:
                return frontier_text
            if "NEXT" in rel:
                return next_text
            if "check.sh" in rel:
                return check_sh_text
            return ""

        with patch.object(maintenance, "_read", side_effect=fake_read), \
             patch.object(maintenance, "_python_command_runs", return_value=python_ok), \
             patch.object(maintenance, "_py_launcher_runs", return_value=False), \
             patch.object(maintenance, "_exists", return_value=True), \
             patch.object(maintenance, "_command_exists", return_value=True), \
             patch.object(maintenance, "_session_number", return_value=200), \
             patch.object(maintenance, "_git", return_value=git_status):
            return maintenance.check_mission_constraints()

    def test_duplicate_invariant_ids_flagged(self):
        results = self._run_check(
            invariants_text="## I9 [MC-SAFE]\n## I9 [MC-SAFE]\n## I10 [MC-PORT]\n## I11 [MC-LEARN]\n## I12 [MC-CONN]\n## I13 [MC-XSUB]\n",
            frontier_text="- **F119**: mission constraints\n",
            next_text="F119 tracked",
            check_sh_text="choose_python() { :; }\npython3\npython\npy -3\n",
        )
        self.assertTrue(any("duplicate ID" in msg for _, msg in results))

    def test_missing_invariant_tag_flagged(self):
        results = self._run_check(
            invariants_text="## I9 [MC-SAFE]\n## I10\n## I11 [MC-LEARN]\n## I12 [MC-CONN]\n## I13 [MC-XSUB]\n",
            frontier_text="- **F119**: mission constraints\n",
            next_text="F119 tracked",
            check_sh_text="choose_python() { :; }\npython3\npython\npy -3\n",
        )
        self.assertTrue(any("mission invariants missing" in msg for _, msg in results))

    def test_missing_i13_xsub_tag_flagged(self):
        results = self._run_check(
            invariants_text="## I9 [MC-SAFE]\n## I10 [MC-PORT]\n## I11 [MC-LEARN]\n## I12 [MC-CONN]\n## I13\n",
            frontier_text="- **F119**: mission constraints\n",
            next_text="F119 tracked",
            check_sh_text="choose_python() { :; }\npython3\npython\npy -3\n",
        )
        self.assertTrue(any("I13" in msg and "mission invariants missing" in msg for _, msg in results))

    def test_learning_quality_gap_detected(self):
        # 5+ tracked changes with no knowledge-state file
        git_status = "\n".join([
            " M tools/a.py",
            " M tools/b.py",
            " M tools/c.py",
            " M tools/d.py",
            " M tools/e.py",
        ])
        results = self._run_check(
            invariants_text="## I9 [MC-SAFE]\n## I10 [MC-PORT]\n## I11 [MC-LEARN]\n## I12 [MC-CONN]\n## I13 [MC-XSUB]\n",
            frontier_text="- **F119**: mission constraints\n",
            next_text="F119 tracked",
            check_sh_text="choose_python() { :; }\npython3\npython\npy -3\n",
            git_status=git_status,
        )
        self.assertTrue(any("learning-quality gap" in msg for _, msg in results))

    def test_learning_quality_ok_with_lesson(self):
        git_status = "\n".join([
            " M tools/a.py",
            " M tools/b.py",
            " M tools/c.py",
            " M tools/d.py",
            "A  memory/lessons/L-999.md",
        ])
        results = self._run_check(
            invariants_text="## I9 [MC-SAFE]\n## I10 [MC-PORT]\n## I11 [MC-LEARN]\n## I12 [MC-CONN]\n## I13 [MC-XSUB]\n",
            frontier_text="- **F119**: mission constraints\n",
            next_text="F119 tracked",
            check_sh_text="choose_python() { :; }\npython3\npython\npy -3\n",
            git_status=git_status,
        )
        self.assertFalse(any("learning-quality gap" in msg for _, msg in results))


class TestSessionLogIntegrityBackfill(unittest.TestCase):
    def _run_check(self, lines: list[str]) -> list[tuple[str, str]]:
        text = "\n".join(lines)
        with patch.object(maintenance, "_read", return_value=text):
            return maintenance.check_session_log_integrity()

    def test_one_step_backfill_is_benign_when_session_already_seen(self):
        results = self._run_check(
            [
                "S151 | baseline",
                "S152 | baseline",
                "S153 | baseline",
                "S154 | baseline",
                "S155 | baseline",
                "S154 | backfill",
            ]
        )
        self.assertFalse(
            any("recent non-monotonic order" in msg for _, msg in results),
            f"Unexpected non-monotonic notice: {results}",
        )

    def test_one_step_backfill_is_benign_when_session_unseen(self):
        results = self._run_check(
            [
                "S151 | baseline",
                "S152 | baseline",
                "S153 | baseline",
                "S155 | baseline",
                "S154 | backfill",
            ]
        )
        self.assertFalse(
            any("recent non-monotonic order" in msg for _, msg in results),
            f"Unexpected non-monotonic notice: {results}",
        )

    def test_multi_step_backfill_is_flagged_when_session_unseen(self):
        results = self._run_check(
            [
                "S151 | baseline",
                "S152 | baseline",
                "S153 | baseline",
                "S156 | baseline",
                "S154 | backfill",
            ]
        )
        self.assertTrue(
            any("recent non-monotonic order" in msg for _, msg in results),
            f"Expected non-monotonic notice, got: {results}",
        )

    def test_control_character_is_flagged(self):
        line = "S161 | runtime recheck (" + chr(8) + "ash tools/check.sh --quick)"
        results = self._run_check(
            [
                line,
            ]
        )
        self.assertTrue(
            any("contains control character" in msg for _, msg in results),
            f"Expected control-character notice, got: {results}",
        )


class TestSwarmLaneCoordinationSignals(unittest.TestCase):
    def _run_check(self, lanes_text: str, *, session: int = 200) -> list[tuple[str, str]]:
        with patch.object(maintenance, "_read", return_value=lanes_text), patch.object(
            maintenance, "_session_number", return_value=session
        ):
            return maintenance.check_swarm_lanes()

    def test_active_lane_missing_setup_focus_is_noticed(self):
        lanes_text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | LANE-1 | S200 | codex | feature/a | - | gpt-5 | windows | tools/maintenance.py | runtime=wsl | ACTIVE | work |",
            ]
        )
        results = self._run_check(lanes_text)
        self.assertTrue(any("missing coordination contract tags" in msg for _, msg in results))

    def test_multi_setup_without_global_focus_is_noticed(self):
        lanes_text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | LANE-1 | S200 | codex | feature/a | - | gpt-5 | windows | tools/maintenance.py | setup=windows focus=parser available=ready blocked=none next_step=run human_open_item=none | ACTIVE | work |",
                "| 2026-02-27 | LANE-2 | S200 | copilot | feature/b | - | gpt-5 | wsl | tasks/SWARM-LANES.md | setup=wsl focus=parser available=ready blocked=none next_step=run human_open_item=none | READY | work |",
            ]
        )
        results = self._run_check(lanes_text)
        self.assertTrue(any("no global coordination focus" in msg for _, msg in results))

    def test_multi_setup_with_global_focus_is_not_flagged(self):
        lanes_text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | LANE-1 | S200 | codex | feature/a | - | gpt-5 | windows | tools/maintenance.py | setup=windows focus=parser available=ready blocked=none next_step=run human_open_item=none | ACTIVE | work |",
                "| 2026-02-27 | LANE-2 | S200 | copilot | feature/b | - | gpt-5 | wsl | tasks/SWARM-LANES.md | setup=wsl focus=global available=ready blocked=none next_step=run human_open_item=none | READY | work |",
            ]
        )
        results = self._run_check(lanes_text)
        self.assertFalse(any("no global coordination focus" in msg for _, msg in results))

    def test_domain_focus_missing_domain_memory_contract_is_due(self):
        lanes_text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | LANE-1 | S200 | codex | feature/a | - | gpt-5 | windows | domains/ai/tasks/FRONTIER.md | setup=windows focus=domains/ai available=ready blocked=none next_step=run human_open_item=none | READY | work |",
            ]
        )
        results = self._run_check(lanes_text)
        self.assertTrue(any("domain-memory coordination tags" in msg for _, msg in results))

    def test_domain_focus_with_domain_memory_contract_is_not_flagged(self):
        lanes_text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | LANE-1 | S200 | codex | feature/a | - | gpt-5 | windows | domains/ai/tasks/FRONTIER.md | setup=windows focus=domains/ai available=ready blocked=none next_step=run human_open_item=none domain_sync=queued memory_target=domains/ai/tasks/FRONTIER.md | READY | work |",
            ]
        )
        results = self._run_check(lanes_text)
        self.assertFalse(any("domain-memory coordination tags" in msg for _, msg in results), results)

    def test_domain_focus_invalid_domain_sync_is_notice(self):
        lanes_text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | LANE-1 | S200 | codex | feature/a | - | gpt-5 | windows | domains/ai/tasks/FRONTIER.md | setup=windows focus=domains/ai available=ready blocked=none next_step=run human_open_item=none domain_sync=waiting memory_target=domains/ai/tasks/FRONTIER.md | READY | work |",
            ]
        )
        results = self._run_check(lanes_text)
        self.assertTrue(any(priority == "NOTICE" and "invalid domain_sync value" in msg for priority, msg in results))

    def test_invalid_available_value_is_due(self):
        lanes_text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | LANE-1 | S200 | codex | feature/a | - | gpt-5 | windows | tools/maintenance.py | setup=windows focus=global available=sometimes blocked=none next_step=run human_open_item=none | ACTIVE | work |",
            ]
        )
        results = self._run_check(lanes_text)
        self.assertTrue(any(priority == "DUE" and "invalid available value" in msg for priority, msg in results))

    def test_legacy_available_value_is_notice(self):
        lanes_text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | LANE-1 | S200 | codex | feature/a | - | gpt-5 | windows | tools/maintenance.py | setup=windows focus=global available=ready blocked=none next_step=run human_open_item=none | ACTIVE | work |",
            ]
        )
        results = self._run_check(lanes_text)
        self.assertTrue(any(priority == "NOTICE" and "legacy available value" in msg for priority, msg in results))

    def test_high_risk_lane_without_human_open_item_is_due(self):
        lanes_text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | LANE-1 | S200 | codex | feature/a | - | gpt-5 | windows | tools/maintenance.py | setup=windows focus=global available=yes blocked=none next_step=reset-hard-and-rerun human_open_item=none | ACTIVE | work |",
            ]
        )
        results = self._run_check(lanes_text)
        self.assertTrue(any(priority == "DUE" and "high-risk intent" in msg for priority, msg in results))

    def test_high_risk_lane_with_human_open_item_is_not_flagged(self):
        lanes_text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | LANE-1 | S200 | codex | feature/a | - | gpt-5 | windows | tools/maintenance.py | setup=windows focus=global available=yes blocked=none next_step=reset-hard-and-rerun human_open_item=HQ-91 | ACTIVE | work |",
            ]
        )
        results = self._run_check(lanes_text)
        self.assertFalse(any("high-risk intent" in msg for _, msg in results), results)

    def test_stale_active_lane_notice(self):
        lanes_text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | LANE-1 | S198 | codex | feature/a | - | gpt-5 | windows | tools/maintenance.py | setup=windows focus=global | ACTIVE | work |",
            ]
        )
        results = self._run_check(lanes_text, session=200)
        self.assertTrue(any("stale >1 sessions" in msg for _, msg in results))

    def test_stale_active_lane_due(self):
        lanes_text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | LANE-1 | S195 | codex | feature/a | - | gpt-5 | windows | tools/maintenance.py | setup=windows focus=global | ACTIVE | work |",
            ]
        )
        results = self._run_check(lanes_text, session=200)
        self.assertTrue(any("stale >3 sessions" in msg for _, msg in results))


class TestSwarmLaneReportingQualitySignals(unittest.TestCase):
    def _run_check(self, lanes_text: str) -> list[tuple[str, str]]:
        with patch.object(maintenance, "_read", return_value=lanes_text):
            return maintenance.check_lane_reporting_quality()

    def test_missing_explicit_fields_is_due_when_not_dispatchable(self):
        lanes_text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | LANE-1 | S200 | codex | feature/a | - | gpt-5 | windows | tools/maintenance.py | setup=windows focus=global intent=repair blocked=none human_open_item=none | ACTIVE | work |",
            ]
        )
        results = self._run_check(lanes_text)
        self.assertTrue(
            any(priority == "DUE" and "missing explicit reporting contract fields" in msg for priority, msg in results),
            f"Expected DUE contract warning, got: {results}",
        )

    def test_full_explicit_contract_is_not_flagged(self):
        lanes_text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | LANE-1 | S200 | codex | feature/a | - | gpt-5 | windows | tools/maintenance.py | setup=windows focus=global intent=repair progress=queued available=now blocked=none next_step=run-check human_open_item=none | ACTIVE | work |",
            ]
        )
        results = self._run_check(lanes_text)
        self.assertFalse(any("missing explicit reporting contract fields" in msg for _, msg in results), results)

    def test_partial_dispatchable_contract_is_notice(self):
        lanes_text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | LANE-1 | S200 | codex | feature/a | - | gpt-5 | windows | tools/maintenance.py | setup=windows focus=global intent=repair progress=queued available=now blocked=none next_step=run-check human_open_item=none | ACTIVE | work |",
                "| 2026-02-27 | LANE-2 | S200 | codex | feature/b | - | gpt-5 | windows | tasks/NEXT.md | setup=windows focus=global intent=repair blocked=none human_open_item=none | READY | work |",
            ]
        )
        results = self._run_check(lanes_text)
        self.assertTrue(
            any(priority == "NOTICE" and "missing explicit reporting contract fields" in msg for priority, msg in results),
            f"Expected NOTICE contract warning, got: {results}",
        )

    def test_objective_focus_requires_historian_self_and_surroundings_anchors(self):
        lanes_text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | LANE-1 | S200 | codex | feature/a | - | gpt-5 | windows | tools/maintenance.py | setup=windows focus=global intent=repair progress=queued available=now blocked=none next_step=run-check human_open_item=none check_focus=objective objective_check=phil14 historian_check=NEXT-only | ACTIVE | work |",
            ]
        )
        results = self._run_check(lanes_text)
        self.assertTrue(
            any(priority == "DUE" and "historian grounding" in msg for priority, msg in results),
            f"Expected DUE historian-grounding warning, got: {results}",
        )

    def test_objective_focus_with_self_and_surroundings_anchors_is_not_flagged(self):
        lanes_text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | LANE-1 | S200 | codex | feature/a | - | gpt-5 | windows | tools/maintenance.py | setup=windows focus=global intent=repair progress=queued available=now blocked=none next_step=run-check human_open_item=none check_focus=objective objective_check=phil14 historian_check=NEXT+SWARM-LANES+OR-FRONTIER-FOPS1 | ACTIVE | work |",
            ]
        )
        results = self._run_check(lanes_text)
        self.assertFalse(any("historian grounding" in msg for _, msg in results), results)


class TestSwarmCoordinatorSignals(unittest.TestCase):
    def _run_check(self, lanes_text: str) -> list[tuple[str, str]]:
        with patch.object(maintenance, "_read", return_value=lanes_text):
            return maintenance.check_swarm_coordinator()

    def test_dispatch_fanout_without_coordinator_is_due(self):
        lanes_text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | L-MSW-S1 | S200 | codex | lane-1 | - | gpt-5 | windows | tools/f_stat1_gates.py | setup=windows focus=domains/statistics dispatch=multiswarm progress=queued available=ready blocked=none next_step=run-slot-1 human_open_item=none | READY | work |",
                "| 2026-02-27 | L-MSW-S2 | S200 | codex | lane-2 | - | gpt-5 | windows | tools/f_gam3_signal_contract.py | setup=windows focus=domains/game-theory dispatch=multiswarm progress=queued available=ready blocked=none next_step=run-slot-2 human_open_item=none | READY | work |",
            ]
        )
        results = self._run_check(lanes_text)
        self.assertTrue(
            any(priority == "DUE" and "no active coordinator lane" in msg for priority, msg in results),
            f"Expected coordinator-missing DUE, got: {results}",
        )

    def test_coordinator_missing_contract_fields_is_due(self):
        lanes_text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | L-MSW-S1 | S200 | codex | lane-1 | - | gpt-5 | windows | tools/f_stat1_gates.py | setup=windows focus=domains/statistics dispatch=multiswarm progress=queued available=ready blocked=none next_step=run-slot-1 human_open_item=none | READY | work |",
                "| 2026-02-27 | L-MSW-S2 | S200 | codex | lane-2 | - | gpt-5 | windows | tools/f_gam3_signal_contract.py | setup=windows focus=domains/game-theory dispatch=multiswarm progress=queued available=ready blocked=none next_step=run-slot-2 human_open_item=none | READY | work |",
                "| 2026-02-27 | L-MSW-COORD | S200 | codex | local | - | gpt-5 | windows | tasks/SWARM-LANES.md | setup=windows focus=global intent=multiswarm-dispatch blocked=none human_open_item=none | ACTIVE | coord |",
            ]
        )
        results = self._run_check(lanes_text)
        self.assertTrue(
            any(priority == "DUE" and "coordinator contract fields" in msg for priority, msg in results),
            f"Expected coordinator-contract DUE, got: {results}",
        )

    def test_valid_coordinator_contract_is_not_flagged(self):
        lanes_text = "\n".join(
            [
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| 2026-02-27 | L-MSW-S1 | S200 | codex | lane-1 | - | gpt-5 | windows | tools/f_stat1_gates.py | setup=windows focus=domains/statistics dispatch=multiswarm progress=queued available=ready blocked=none next_step=run-slot-1 human_open_item=none | READY | work |",
                "| 2026-02-27 | L-MSW-S2 | S200 | codex | lane-2 | - | gpt-5 | windows | tools/f_gam3_signal_contract.py | setup=windows focus=domains/game-theory dispatch=multiswarm progress=queued available=ready blocked=none next_step=run-slot-2 human_open_item=none | READY | work |",
                "| 2026-02-27 | L-MSW-COORD | S200 | codex | local | - | gpt-5 | windows | tasks/SWARM-LANES.md | setup=windows focus=global intent=multiswarm-dispatch progress=running available=yes blocked=none next_step=dispatch-slot-3 human_open_item=none check_focus=coordination | ACTIVE | coord |",
            ]
        )
        results = self._run_check(lanes_text)
        self.assertFalse(any("coordinator" in msg for _, msg in results), results)


class TestMissionConstraintDegradedRuntime(unittest.TestCase):
    def _run_check(
        self,
        *,
        next_lines: list[str],
        session_log_lines: list[str],
        session: int,
        python_status: dict[str, bool],
        py_launcher: bool,
        bash_available: bool,
        pwsh_available: bool = False,
        exists_overrides: dict[str, bool] | None = None,
    ) -> list[tuple[str, str]]:
        frontier_text = "- **F119**: mission constraints"
        invariants_text = "\n".join(
            [
                "## I9 - Mission safety: do no harm [MC-SAFE]",
                "## I10 - Mission portability: work everywhere [MC-PORT]",
                "## I11 - Mission learning quality: improve knowledge continuously [MC-LEARN]",
                "## I12 - Mission continuity: stay connected under constraints [MC-CONN]",
                "## I13 - Mission safety: cross-substrate safe entry [MC-XSUB]",
            ]
        )
        check_sh_text = "\n".join(
            [
                "choose_python() {",
                "python3",
                "python",
                "py -3",
                "}",
            ]
        )
        read_map = {
            "tasks/FRONTIER.md": frontier_text,
            "tasks/NEXT.md": "\n".join(next_lines),
            "beliefs/INVARIANTS.md": invariants_text,
            "tools/check.sh": check_sh_text,
            "memory/SESSION-LOG.md": "\n".join(session_log_lines),
        }
        exists_values = {
            "tools/check.sh": True,
            "tools/maintenance.sh": True,
            "tools/check.ps1": True,
            "tools/maintenance.ps1": True,
            "tools/bulletin.py": True,
            "tools/merge_back.py": True,
            "tools/propagate_challenges.py": True,
            "tasks/PR-QUEUE.json": True,
            "tasks/SWARM-LANES.md": True,
        }
        if exists_overrides:
            exists_values.update(exists_overrides)

        real_read = maintenance._read

        def fake_read(path):
            try:
                rel = path.relative_to(maintenance.REPO_ROOT).as_posix()
            except Exception:
                rel = str(path).replace("\\", "/")
            return read_map.get(rel, real_read(path))

        def fake_python_command_runs(cmd: str) -> bool:
            return python_status.get(cmd, False)

        def fake_exists(path: str) -> bool:
            return exists_values.get(path, True)

        def fake_command_exists(cmd: str) -> bool:
            if cmd == "bash":
                return bash_available
            if cmd in {"pwsh", "powershell"}:
                return pwsh_available
            return True

        with patch.object(maintenance, "_read", side_effect=fake_read), \
             patch.object(maintenance, "_python_command_runs", side_effect=fake_python_command_runs), \
             patch.object(maintenance, "_py_launcher_runs", return_value=py_launcher), \
             patch.object(maintenance, "_exists", side_effect=fake_exists), \
             patch.object(maintenance, "_command_exists", side_effect=fake_command_exists), \
             patch.object(maintenance, "_session_number", return_value=session), \
             patch.object(maintenance, "_git", return_value=""):
            return maintenance.check_mission_constraints()

    def test_runtime_portability_without_fallback_is_due(self):
        lines = [
            "F119 validation pass",
            "S200: runtime portability python alias missing in powershell",
        ]
        results = self._run_check(
            next_lines=lines,
            session_log_lines=lines,
            session=200,
            python_status={"python3": False, "python": False},
            py_launcher=False,
            bash_available=False,
            exists_overrides={
                "tools/check.sh": False,
                "tools/maintenance.sh": False,
            },
        )
        self.assertTrue(any("degraded runtime continuity broken" in msg for _, msg in results))

    def test_runtime_portability_pwsh_wrapper_path_counts_as_fallback(self):
        lines = [
            "F119 validation pass",
            "S200: runtime portability no runnable python alias; fallback via pwsh -NoProfile -File tools/check.ps1 --quick; Beliefs PASS NOTICE-only",
        ]
        results = self._run_check(
            next_lines=lines,
            session_log_lines=lines,
            session=200,
            python_status={"python3": False, "python": False},
            py_launcher=False,
            bash_available=False,
            pwsh_available=True,
            exists_overrides={
                "tools/check.sh": False,
                "tools/maintenance.sh": False,
                "tools/check.ps1": True,
                "tools/maintenance.ps1": True,
            },
        )
        messages = [msg for _, msg in results]
        self.assertFalse(any("degraded runtime continuity broken" in m for m in messages))

    def test_offline_artifacts_missing_is_due(self):
        lines = [
            "F119 validation pass",
            "S200: inter-swarm continuity offline queue sync via tasks/PR-QUEUE.json; Beliefs PASS NOTICE-only",
        ]
        results = self._run_check(
            next_lines=lines,
            session_log_lines=lines,
            session=200,
            python_status={"python3": True, "python": False},
            py_launcher=False,
            bash_available=True,
            exists_overrides={
                "tools/bulletin.py": False,
                "tools/merge_back.py": False,
                "tools/propagate_challenges.py": False,
                "tasks/PR-QUEUE.json": False,
                "tasks/SWARM-LANES.md": False,
            },
        )
        self.assertTrue(any("offline continuity artifacts missing" in msg for _, msg in results))


class TestMissionConstraintDegradedRuntimeE2E(unittest.TestCase):
    def test_offline_artifacts_missing_emits_due_end_to_end(self):
        next_body = "\n".join(
            [
                "F119 tracked in priorities.",
                "S156: inter-swarm continuity offline queue sync via tasks/PR-QUEUE.json and tasks/SWARM-LANES.md; Beliefs PASS NOTICE-only",
            ]
        )
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _seed_repo(root, next_body)
            (root / "tools/bulletin.py").unlink(missing_ok=True)
            (root / "tools/merge_back.py").unlink(missing_ok=True)
            (root / "tools/propagate_challenges.py").unlink(missing_ok=True)
            (root / "tasks/PR-QUEUE.json").unlink(missing_ok=True)
            (root / "tasks/SWARM-LANES.md").unlink(missing_ok=True)

            with patch.object(maintenance, "REPO_ROOT", root), patch.object(
                maintenance, "_git", return_value=""
            ), patch.object(
                maintenance, "_python_command_runs", side_effect=lambda cmd: cmd in {"python3", "python"}
            ), patch.object(
                maintenance, "_py_launcher_runs", return_value=False
            ), patch.object(
                maintenance, "_command_exists", return_value=True
            ), patch.object(
                maintenance, "_command_runs", return_value=True
            ):
                results = maintenance.check_mission_constraints()

        messages = [msg for _, msg in results]
        self.assertTrue(any("offline continuity artifacts missing" in msg for msg in messages))

    def test_offline_artifacts_present_no_due_end_to_end(self):
        next_body = "\n".join(
            [
                "F119 tracked in priorities.",
                "S156: inter-swarm continuity offline queue sync via tasks/PR-QUEUE.json and tasks/SWARM-LANES.md; Beliefs PASS NOTICE-only",
            ]
        )
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _seed_repo(root, next_body)
            (root / "tools/bulletin.py").unlink(missing_ok=True)
            (root / "tools/merge_back.py").unlink(missing_ok=True)
            (root / "tools/propagate_challenges.py").unlink(missing_ok=True)
            _write(root / "tasks/PR-QUEUE.json", '{"schema":"swarm-pr-queue-v1","items":[]}\n')
            _write(
                root / "tasks/SWARM-LANES.md",
                "| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |\n"
                "|---|---|---|---|---|---|---|---|---|---|---|---|\n",
            )

            with patch.object(maintenance, "REPO_ROOT", root), patch.object(
                maintenance, "_git", return_value=""
            ), patch.object(
                maintenance, "_python_command_runs", side_effect=lambda cmd: cmd in {"python3", "python"}
            ), patch.object(
                maintenance, "_py_launcher_runs", return_value=False
            ), patch.object(
                maintenance, "_command_exists", return_value=True
            ), patch.object(
                maintenance, "_command_runs", return_value=True
            ):
                results = maintenance.check_mission_constraints()

        messages = [msg for _, msg in results]
        self.assertFalse(any("offline continuity artifacts missing" in msg for msg in messages))
        self.assertFalse(any("offline/inter-swarm continuity degraded mode lacks" in msg for msg in messages))

    def test_pwsh_wrappers_prevent_degraded_runtime_due_end_to_end(self):
        next_body = "\n".join(
            [
                "F119 tracked in priorities.",
                "S156: runtime portability no runnable python alias; fallback via pwsh -NoProfile -File tools/check.ps1 --quick; Beliefs PASS NOTICE-only",
            ]
        )
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _seed_repo(root, next_body)
            (root / "tools/check.sh").unlink(missing_ok=True)
            (root / "tools/maintenance.sh").unlink(missing_ok=True)

            def fake_command_exists(cmd: str) -> bool:
                if cmd == "bash":
                    return False
                if cmd in {"pwsh", "powershell"}:
                    return True
                return True

            with patch.object(maintenance, "REPO_ROOT", root), patch.object(
                maintenance, "_git", return_value=""
            ), patch.object(
                maintenance, "_python_command_runs", return_value=False
            ), patch.object(
                maintenance, "_py_launcher_runs", return_value=False
            ), patch.object(
                maintenance, "_command_exists", side_effect=fake_command_exists
            ), patch.object(
                maintenance, "_command_runs", return_value=True
            ):
                results = maintenance.check_mission_constraints()

        messages = [msg for _, msg in results]
        self.assertFalse(any("degraded runtime continuity broken" in msg for msg in messages))


class TestRuntimePortabilityFallbacks(unittest.TestCase):
    def _run_portability(
        self,
        *,
        has_git: bool = True,
        has_bash: bool = False,
        has_pwsh: bool = True,
        has_python3: bool = True,
        has_python: bool = False,
        has_py_launcher: bool = False,
        exists_overrides: dict[str, bool] | None = None,
    ) -> list[tuple[str, str]]:
        exists_values = {
            "workspace/genesis.sh": True,
            "tools/check.sh": True,
            "tools/maintenance.sh": True,
            "tools/check.ps1": True,
            "tools/maintenance.ps1": True,
            "SWARM.md": True,
            "CLAUDE.md": True,
            "AGENTS.md": True,
            "GEMINI.md": True,
            ".cursorrules": True,
            ".windsurfrules": True,
            ".github/copilot-instructions.md": True,
        }
        if exists_overrides:
            exists_values.update(exists_overrides)

        def fake_exists(path: str) -> bool:
            return exists_values.get(path, True)

        def fake_command_exists(cmd: str) -> bool:
            command_map = {
                "git": has_git,
                "bash": has_bash,
                "pwsh": has_pwsh,
                "powershell": has_pwsh,
            }
            return command_map.get(cmd, False)

        def fake_python_command_runs(cmd: str) -> bool:
            py_map = {
                "python3": has_python3,
                "python": has_python,
            }
            return py_map.get(cmd, False)

        with patch.object(maintenance, "_exists", side_effect=fake_exists):
            with patch.object(maintenance, "_command_exists", side_effect=fake_command_exists):
                with patch.object(maintenance, "_python_command_runs", side_effect=fake_python_command_runs):
                    with patch.object(maintenance, "_py_launcher_runs", return_value=has_py_launcher):
                        with patch.object(maintenance, "_is_wsl_mnt_repo", return_value=False):
                            with patch.object(maintenance, "_git", return_value=""):
                                with patch.object(maintenance, "_read", return_value="SWARM.md\nswarm signaling\n"):
                                    return maintenance.check_runtime_portability()

    def test_no_bash_uses_powershell_wrappers_when_python_available(self):
        results = self._run_portability(
            has_bash=False,
            has_pwsh=True,
            has_python3=True,
        )
        messages = [msg for _, msg in results]
        self.assertTrue(any("use PowerShell wrappers" in msg for msg in messages))
        self.assertFalse(any("portable startup path is broken" in msg for msg in messages))

    def test_no_bash_uses_direct_python_when_ps_wrappers_missing(self):
        results = self._run_portability(
            has_bash=False,
            has_pwsh=True,
            has_python3=True,
            exists_overrides={
                "tools/check.ps1": False,
                "tools/maintenance.ps1": False,
            },
        )
        messages = [msg for _, msg in results]
        self.assertTrue(any("use direct python entrypoints" in msg for msg in messages))
        self.assertFalse(any("portable startup path is broken" in msg for msg in messages))

    def test_no_bash_and_no_python_is_due(self):
        results = self._run_portability(
            has_bash=False,
            has_pwsh=True,
            has_python3=False,
            has_python=False,
            has_py_launcher=False,
        )
        due_messages = [msg for level, msg in results if level == "DUE"]
        self.assertTrue(any("No python alias in PATH" in msg for msg in due_messages))
        self.assertTrue(any("portable startup path is broken" in msg for msg in due_messages))


class TestStateHeaderSyncParsing(unittest.TestCase):
    def _run_state_header_sync(
        self,
        *,
        frontier_header: str,
        session: int = 200,
        next_session: int = 200,
        index_session: int = 200,
        dirty: bool = True,
    ) -> list[tuple[str, str]]:
        read_map = {
            "tasks/NEXT.md": f"# State\nUpdated: 2026-02-27 S{next_session}\n",
            "memory/INDEX.md": f"# Memory Index\nUpdated: 2026-02-27 | Sessions: {index_session}\n",
            "tasks/FRONTIER.md": (
                "# Frontier - Open Questions\n\n"
                f"14 active | {frontier_header}\n"
            ),
        }

        real_read = maintenance._read

        def fake_read(path):
            try:
                rel = path.relative_to(maintenance.REPO_ROOT).as_posix()
            except Exception:
                rel = str(path).replace("\\", "/")
            return read_map.get(rel, real_read(path))

        with patch.object(maintenance, "_read", side_effect=fake_read):
            with patch.object(maintenance, "_session_number", return_value=session):
                with patch.object(maintenance, "_git", return_value=("M x" if dirty else "")):
                    return maintenance.check_state_header_sync()

    def test_frontier_header_parses_with_pipe_separator(self):
        results = self._run_state_header_sync(
            frontier_header="Last updated: 2026-02-27 | S200",
            dirty=True,
        )
        self.assertFalse(
            any("State header parse failed" in msg for _, msg in results),
            f"Unexpected parse failure: {results}",
        )

    def test_frontier_header_parses_case_insensitive(self):
        results = self._run_state_header_sync(
            frontier_header="last UPDATED: 2026-02-27 s200",
            dirty=True,
        )
        self.assertFalse(
            any("State header parse failed" in msg for _, msg in results),
            f"Unexpected parse failure: {results}",
        )

    def test_frontier_header_missing_session_is_reported(self):
        results = self._run_state_header_sync(
            frontier_header="Last updated: 2026-02-27",
            dirty=True,
        )
        self.assertTrue(
            any("State header parse failed: FRONTIER" in msg for _, msg in results),
            f"Expected FRONTIER parse failure, got: {results}",
        )


if __name__ == "__main__":
    unittest.main()
