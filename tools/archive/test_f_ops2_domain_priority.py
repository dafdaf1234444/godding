#!/usr/bin/env python3
"""Unit tests for F-OPS2 domain-priority allocator."""

import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f_ops2_domain_priority as mod


class TestFOps2DomainPriority(unittest.TestCase):
    def test_updated_session_from_state_header(self):
        text = "# State\nUpdated: 2026-02-27 S186\n"
        self.assertEqual(mod._updated_session_from_state_header(text), 186)

    def test_parse_active_frontiers(self):
        text = """# Example
## Active
- **F-IS3**: one
- **F-IS4**: two
- ~~**F-IS2**~~: resolved
- ~~F-IS1~~: also resolved

## Resolved
- **F-IS2**: old
"""
        self.assertEqual(mod.parse_active_frontiers(text), ["F-IS3", "F-IS4"])

    def test_parse_next_demand_with_priority_weights(self):
        next_text = """# State
## For next session
1. **F-IS3 / F-FIN1** do this.
2. **F-EVO1** do that.
"""
        frontier_map = {"F-IS3": "information-science", "F-FIN1": "finance", "F-EVO1": "evolution"}
        mentions, weights = mod.parse_next_demand(next_text, frontier_map)
        self.assertEqual(mentions["information-science"], 1)
        self.assertEqual(mentions["finance"], 1)
        self.assertEqual(mentions["evolution"], 1)
        self.assertGreater(weights["information-science"], weights["evolution"])
        self.assertGreater(weights["finance"], weights["evolution"])

    def test_parse_findings_demand_prefers_recent_caveated_lines(self):
        next_text = """# State
## What just happened
S186: F-FIN1 rerun completed with caveat: mean remains unstable; next step is extraction hardening.
S186: F-IS5 intake pass resolved lane packing issue.
S185: F-EVO2 baseline merged.
"""
        frontier_map = {"F-FIN1": "finance", "F-IS5": "information-science", "F-EVO2": "evolution"}
        mentions, weights = mod.parse_findings_demand(next_text, frontier_map, max_lines=3)
        self.assertEqual(mentions["finance"], 1)
        self.assertEqual(mentions["information-science"], 1)
        self.assertEqual(mentions["evolution"], 1)
        self.assertGreater(weights["finance"], weights["evolution"])

    def test_parse_active_lane_pressure_prefers_latest_lane_row(self):
        lanes_text = """| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-02-27 | L-1 | S186 | codex | local | - | GPT-5 | codex-cli | domains/finance/tasks/FRONTIER.md | setup=x,focus=global | ACTIVE | a |
| 2026-02-27 | L-1 | S186 | codex | local | - | GPT-5 | codex-cli | domains/finance/tasks/FRONTIER.md | setup=x,focus=global | MERGED | b |
| 2026-02-27 | L-2 | S186 | codex | local | - | GPT-5 | codex-cli | tools/wiki_swarm.py | setup=x,focus=global,frontier=F-IS3 | READY | c |
"""
        pressure = mod.parse_active_lane_pressure(lanes_text, {"F-IS3": "information-science"})
        # L-1 latest status is MERGED so it should not contribute pressure.
        self.assertNotIn("finance", pressure)
        self.assertEqual(pressure.get("information-science"), 1)

    def test_parse_dispatchable_capacity_honors_available_and_blocked(self):
        lanes_text = """| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-02-27 | L-1 | S186 | codex | local | - | GPT-5 | codex-cli | domains/finance/tasks/FRONTIER.md | setup=x; available=yes; blocked=none | READY | a |
| 2026-02-27 | L-2 | S186 | codex | local | - | GPT-5 | codex-cli | domains/finance/tasks/FRONTIER.md | setup=x; available=partial; blocked=none | ACTIVE | b |
| 2026-02-27 | L-3 | S186 | codex | local | - | GPT-5 | codex-cli | domains/finance/tasks/FRONTIER.md | setup=x; available=yes; blocked=await-human | READY | c |
| 2026-02-27 | L-4 | S186 | codex | local | - | GPT-5 | codex-cli | tools/wiki_swarm.py | setup=x; frontier=F-IS3; available=yes; blocked=none | CLAIMED | d |
"""
        capacity = mod.parse_dispatchable_capacity(lanes_text, {"F-IS3": "information-science"})
        self.assertAlmostEqual(capacity.get("finance", 0.0), 1.5)
        self.assertAlmostEqual(capacity.get("information-science", 0.0), 1.0)

    def test_parse_dispatchable_capacity_treats_available_ready_as_yes(self):
        lanes_text = """| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-02-27 | L-R1 | S186 | codex | local | - | GPT-5 | codex-cli | domains/finance/tasks/FRONTIER.md | setup=x; available=ready; blocked=none | READY | a |
"""
        capacity = mod.parse_dispatchable_capacity(lanes_text, {})
        self.assertAlmostEqual(capacity.get("finance", 0.0), 1.0)

    def test_parse_domain_expert_coverage_filters_to_domex_lanes(self):
        lanes_text = """| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-02-27 | L-S186-DOMEX-AI | S186 | codex | local | - | GPT-5 | codex-cli | domains/ai/tasks/FRONTIER.md | setup=x; available=yes; blocked=none; dispatch=domain-expert-swarm-s186 | READY | a |
| 2026-02-27 | L-S186-DOMEX-AI | S186 | codex | local | - | GPT-5 | codex-cli | domains/ai/tasks/FRONTIER.md | setup=x; available=partial; blocked=none; dispatch=domain-expert-swarm-s186 | ACTIVE | b |
| 2026-02-27 | L-S186-DOMEX-OPS | S186 | codex | local | - | GPT-5 | codex-cli | domains/operations-research/tasks/FRONTIER.md | setup=x; available=yes; blocked=await-human; dispatch=domain-expert-swarm-s186 | READY | c |
| 2026-02-27 | L-OTHER | S186 | codex | local | - | GPT-5 | codex-cli | domains/ai/tasks/FRONTIER.md | setup=x; available=yes; blocked=none | READY | d |
"""
        capacity, active_counts = mod.parse_domain_expert_coverage(lanes_text, {})
        self.assertAlmostEqual(capacity.get("ai", 0.0), 0.5)
        self.assertEqual(active_counts.get("ai"), 1)
        self.assertEqual(active_counts.get("operations-research"), 1)
        self.assertNotIn("operations-research", capacity)

    def test_build_expert_generator_flags_shortfall(self):
        states = [
            mod.DomainState(
                name="ai",
                frontier_path="domains/ai/tasks/FRONTIER.md",
                active_frontiers=["F-AI1", "F-AI2"],
                updated_session=186,
                age_sessions=0,
                next_mentions=2,
                next_priority_weight=6.0,
                active_lane_pressure=0,
            )
        ]
        generator = mod.build_expert_generator(
            states,
            recommended_alloc={"ai": 2},
            dispatchable_capacity={"ai": 0.0},
            domain_expert_capacity={"ai": 0.0},
            domain_expert_active_counts={},
            current_session=186,
        )
        self.assertTrue(generator["spawn_required"])
        self.assertEqual(generator["triggered_domains"], 1)
        self.assertGreaterEqual(generator["total_new_experts"], 1)
        req = generator["requests"][0]
        self.assertIn("no_active_domain_expert_lane", req["trigger_reasons"])
        self.assertIn("dispatch_capacity_shortfall", req["trigger_reasons"])
        self.assertTrue(req["lane_ids"][0].startswith("L-S186-DOMEX-GEN-AI"))

    def test_compute_automability_uses_capacity_cap(self):
        allocations = {"finance": 2, "information-science": 1, "ai": 1}
        dispatchable_capacity = {"finance": 1.5, "information-science": 0.5}
        auto = mod.compute_automability(allocations, dispatchable_capacity)
        self.assertEqual(auto["total_decisions"], 4)
        self.assertAlmostEqual(auto["accepted_decisions"], 2.0)
        self.assertAlmostEqual(auto["rejected_decisions"], 2.0)
        self.assertAlmostEqual(auto["automability_rate"], 0.5)

    def test_allocate_agents_gives_more_slots_to_higher_signal_domain(self):
        states = [
            mod.DomainState(
                name="information-science",
                frontier_path="domains/information-science/tasks/FRONTIER.md",
                active_frontiers=["F-IS3", "F-IS4", "F-IS5"],
                updated_session=186,
                age_sessions=0,
                next_mentions=2,
                next_priority_weight=7.0,
                active_lane_pressure=0,
            ),
            mod.DomainState(
                name="finance",
                frontier_path="domains/finance/tasks/FRONTIER.md",
                active_frontiers=["F-FIN1"],
                updated_session=186,
                age_sessions=0,
                next_mentions=0,
                next_priority_weight=0.0,
                active_lane_pressure=0,
            ),
        ]
        alloc = mod.allocate_agents(states, "hybrid", 4)
        self.assertGreater(alloc["information-science"], alloc["finance"])

    def test_allocate_agents_capacity_bias_penalizes_over_capacity(self):
        states = [
            mod.DomainState(
                name="alpha",
                frontier_path="domains/alpha/tasks/FRONTIER.md",
                active_frontiers=["F-A1"],
                updated_session=186,
                age_sessions=0,
                next_mentions=1,
                next_priority_weight=20.0,
                active_lane_pressure=0,
            ),
            mod.DomainState(
                name="beta",
                frontier_path="domains/beta/tasks/FRONTIER.md",
                active_frontiers=["F-B1"],
                updated_session=186,
                age_sessions=0,
                next_mentions=1,
                next_priority_weight=3.0,
                active_lane_pressure=0,
            ),
        ]
        alloc_no_bias = mod.allocate_agents(
            states,
            "value_density",
            3,
            dispatchable_capacity={"beta": 1.0},
            capacity_bias=0.0,
        )
        alloc_with_bias = mod.allocate_agents(
            states,
            "value_density",
            3,
            dispatchable_capacity={"beta": 1.0},
            capacity_bias=1.0,
        )
        self.assertEqual(alloc_no_bias["alpha"], 3)
        self.assertGreater(alloc_with_bias["beta"], 0)

    def test_capacity_bias_improves_automability_rate(self):
        states = [
            mod.DomainState(
                name="alpha",
                frontier_path="domains/alpha/tasks/FRONTIER.md",
                active_frontiers=["F-A1"],
                updated_session=186,
                age_sessions=0,
                next_mentions=1,
                next_priority_weight=20.0,
                active_lane_pressure=0,
            ),
            mod.DomainState(
                name="beta",
                frontier_path="domains/beta/tasks/FRONTIER.md",
                active_frontiers=["F-B1"],
                updated_session=186,
                age_sessions=0,
                next_mentions=1,
                next_priority_weight=3.0,
                active_lane_pressure=0,
            ),
        ]
        dispatchable_capacity = {"beta": 1.0}
        alloc_no_bias = mod.allocate_agents(
            states,
            "value_density",
            3,
            dispatchable_capacity=dispatchable_capacity,
            capacity_bias=0.0,
        )
        alloc_with_bias = mod.allocate_agents(
            states,
            "value_density",
            3,
            dispatchable_capacity=dispatchable_capacity,
            capacity_bias=1.0,
        )
        no_bias_auto = mod.compute_automability(alloc_no_bias, dispatchable_capacity)["automability_rate"]
        with_bias_auto = mod.compute_automability(alloc_with_bias, dispatchable_capacity)["automability_rate"]
        self.assertGreater(with_bias_auto, no_bias_auto)

    def test_apply_automability_guard_penalizes_shortfall(self):
        base = {"net_score": 100.0, "automability_rate": 0.1}
        guarded = mod.apply_automability_guard(base, automability_floor=0.25, guard_penalty=200.0)
        self.assertFalse(guarded["guard"]["pass"])
        self.assertAlmostEqual(guarded["guard"]["shortfall"], 0.15)
        self.assertAlmostEqual(guarded["guard"]["penalty"], 30.0)
        self.assertAlmostEqual(guarded["effective_net_score"], 70.0)

    def test_evaluate_policy_reports_automability_fields(self):
        states = [
            mod.DomainState(
                name="information-science",
                frontier_path="domains/information-science/tasks/FRONTIER.md",
                active_frontiers=["F-IS3"],
                updated_session=186,
                age_sessions=0,
                next_mentions=1,
                next_priority_weight=4.0,
                active_lane_pressure=0,
            ),
            mod.DomainState(
                name="finance",
                frontier_path="domains/finance/tasks/FRONTIER.md",
                active_frontiers=["F-FIN1"],
                updated_session=186,
                age_sessions=0,
                next_mentions=0,
                next_priority_weight=0.0,
                active_lane_pressure=0,
            ),
        ]
        metrics = mod.evaluate_policy(
            states,
            {"information-science": 2, "finance": 1},
            dispatchable_capacity={"information-science": 1.0, "finance": 0.0},
            automability_weight=10.0,
        )
        self.assertIn("automability_rate", metrics)
        self.assertIn("accepted_decisions", metrics)
        self.assertIn("automability_bonus", metrics)
        self.assertGreater(metrics["net_score"], metrics["projected_gain"] - 1.5 * metrics["collision_risk"])

    def test_load_domain_frontiers_from_temp_tree(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            d = root / "domains" / "demo" / "tasks"
            d.mkdir(parents=True)
            (d / "FRONTIER.md").write_text(
                "# Demo\nUpdated: 2026-02-27 S180 | Active: 1\n\n## Active\n- **F-DEMO1**: x\n",
                encoding="utf-8",
            )
            states, f_map = mod.load_domain_frontiers(root / "domains", current_session=186)
            self.assertEqual(len(states), 1)
            self.assertEqual(states[0].name, "demo")
            self.assertEqual(states[0].age_sessions, 6)
            self.assertEqual(f_map["F-DEMO1"], "demo")


if __name__ == "__main__":
    unittest.main()
