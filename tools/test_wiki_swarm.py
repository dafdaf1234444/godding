#!/usr/bin/env python3
"""Regression tests for wiki_swarm generic invocation handling."""

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wiki_swarm


class TestWikiSwarm(unittest.TestCase):
    def test_generic_invocation_variants(self):
        self.assertTrue(wiki_swarm.is_generic_invocation("swarm"))
        self.assertTrue(wiki_swarm.is_generic_invocation("wiki swarm"))
        self.assertTrue(wiki_swarm.is_generic_invocation("swarm the wiki swarm"))
        self.assertTrue(wiki_swarm.is_generic_invocation("Swarm, the wiki swarm!"))
        self.assertTrue(
            wiki_swarm.is_generic_invocation("swarm expert builder to swarm the swarm")
        )
        self.assertTrue(
            wiki_swarm.is_generic_invocation(
                "swarm domain expert on the swarm command to swarm it swarmer"
            )
        )

    def test_generic_invocation_does_not_capture_specific_topic(self):
        self.assertFalse(wiki_swarm.is_generic_invocation("swarm intelligence"))

    def test_main_uses_auto_for_generic_phrase(self):
        with patch.object(
            wiki_swarm,
            "choose_auto_topic",
            return_value=("Swarm intelligence", "auto(default)"),
        ) as choose_auto, patch.object(
            wiki_swarm,
            "swarm_topic",
            return_value=("Swarm intelligence", []),
        ) as swarm_topic, patch.object(
            wiki_swarm, "render_markdown", return_value="report\n"
        ), patch("sys.stdout", new_callable=io.StringIO):
            rc = wiki_swarm.main(["swarm", "the", "wiki", "swarm"])

        self.assertEqual(rc, 0)
        choose_auto.assert_called_once()
        swarm_topic.assert_called_once_with("Swarm intelligence", 1, 5, "en")

    def test_main_keeps_manual_topic_when_specific(self):
        with patch.object(wiki_swarm, "choose_auto_topic") as choose_auto, patch.object(
            wiki_swarm,
            "swarm_topic",
            return_value=("Swarm intelligence", []),
        ) as swarm_topic, patch.object(
            wiki_swarm, "render_markdown", return_value="report\n"
        ), patch("sys.stdout", new_callable=io.StringIO):
            rc = wiki_swarm.main(["Swarm intelligence"])

        self.assertEqual(rc, 0)
        choose_auto.assert_not_called()
        swarm_topic.assert_called_once_with("Swarm intelligence", 1, 5, "en")

    def test_coordination_experiment_sync_is_more_correlated(self):
        payload = wiki_swarm.run_coordination_experiment(trials=1000, error_rate=0.2, seed=155)

        self.assertGreater(payload["sync"]["leader_follower_error_correlation"], 0.95)
        self.assertLess(abs(payload["async"]["leader_follower_error_correlation"]), 0.2)
        self.assertGreater(
            payload["sync"]["joint_error_rate"],
            payload["async"]["joint_error_rate"],
        )

    def test_main_coord_experiment_json_out(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "coord.json"
            with patch("sys.stdout", new_callable=io.StringIO):
                rc = wiki_swarm.main(
                    [
                        "--coord-experiment",
                        "--trials",
                        "200",
                        "--error-rate",
                        "0.25",
                        "--seed",
                        "7",
                        "--json-out",
                        str(out),
                    ]
                )

            self.assertEqual(rc, 0)
            self.assertTrue(out.exists())
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["experiment"], "F-AI2/F-HLT2")
            self.assertIn("sync", data)
            self.assertIn("async", data)

    def test_perturb_topic_query_changes_nontrivial_input(self):
        rng = wiki_swarm.random.Random(155)
        topic = "Swarm intelligence"
        perturbed = wiki_swarm._perturb_topic_query(topic, rng)
        self.assertNotEqual(perturbed, topic)
        self.assertTrue(len(perturbed) >= len(topic) - 1)

    def test_live_coordination_experiment_shape(self):
        def fake_summary(query: str, lang: str):
            q = query.lower().replace(" ", "")
            if "swarmintelligence" in q:
                return {"title": "Swarm intelligence", "summary": "x", "url": "u"}
            if "distributedsystems" in q:
                return {"title": "Distributed systems", "summary": "x", "url": "u"}
            return {"title": query, "summary": "x", "url": "u"}

        with patch.object(wiki_swarm, "fetch_summary", side_effect=fake_summary):
            payload = wiki_swarm.run_live_coordination_experiment(
                trials=30,
                perturb_rate=0.5,
                seed=7,
                lang="en",
            )

        self.assertEqual(payload["mode"], "live-perturbation")
        self.assertEqual(payload["experiment"], "F-AI2/F-HLT2")
        self.assertIn("sync", payload)
        self.assertIn("async", payload)
        self.assertIn("mismatch_samples", payload)
        self.assertGreaterEqual(
            payload["sync"]["leader_follower_error_correlation"],
            payload["async"]["leader_follower_error_correlation"],
        )

    def test_live_partial_sync_sits_between_async_and_full_sync(self):
        def fake_summary(query: str, lang: str):
            q = query.lower().replace(" ", "")
            if "swarmintelligence" in q:
                return {"title": "Swarm intelligence", "summary": "x", "url": "u"}
            if "distributedsystems" in q:
                return {"title": "Distributed systems", "summary": "x", "url": "u"}
            return {"title": query, "summary": "x", "url": "u"}

        with patch.object(wiki_swarm, "fetch_summary", side_effect=fake_summary):
            full = wiki_swarm.run_live_coordination_experiment(
                trials=120,
                perturb_rate=0.6,
                seed=11,
                lang="en",
                sync_inherit_prob=1.0,
            )
            partial = wiki_swarm.run_live_coordination_experiment(
                trials=120,
                perturb_rate=0.6,
                seed=11,
                lang="en",
                sync_inherit_prob=0.5,
            )

        self.assertEqual(full["sync"]["leader_follower_error_correlation"], 1.0)
        self.assertLess(
            partial["sync"]["leader_follower_error_correlation"],
            full["sync"]["leader_follower_error_correlation"],
        )
        self.assertGreaterEqual(partial["sync_inherit_prob"], 0.0)

    def test_live_ai1_evidence_surfacing_direction(self):
        def fake_summary(query: str, lang: str):
            q = query.lower().replace(" ", "")
            if q in {"swarmintelligence", "distributedsystems", "stigmergy"}:
                return {"title": query.title(), "summary": "x", "url": "u"}
            return {"title": query, "summary": "x", "url": "u"}

        with patch.object(wiki_swarm, "fetch_summary", side_effect=fake_summary):
            payload = wiki_swarm.run_live_ai1_evidence_experiment(
                trials=400,
                perturb_rate=0.35,
                seed=186,
                lang="en",
                leader_high_conf_prob=0.6,
                leader_high_conf_perturb_rate=0.0,
                leader_low_conf_perturb_rate=1.0,
            )

        self.assertEqual(payload["mode"], "live-evidence-surfacing")
        self.assertEqual(payload["experiment"], "F-AI1")
        self.assertLess(
            payload["evidence_surfacing"]["follower_error_rate"],
            payload["async"]["follower_error_rate"],
        )
        self.assertGreater(
            payload["sync"]["leader_follower_error_correlation"],
            payload["evidence_surfacing"]["leader_follower_error_correlation"],
        )


if __name__ == "__main__":
    unittest.main()
