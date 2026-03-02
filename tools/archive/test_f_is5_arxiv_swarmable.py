#!/usr/bin/env python3
"""Regression tests for F-IS5 arXiv swarmable intake harness."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f_is5_arxiv_swarmable as mod


SAMPLE_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2602.00001v1</id>
    <updated>2026-02-26T10:00:00Z</updated>
    <published>2026-02-25T10:00:00Z</published>
    <title>Safety-Aware Coordination for Multi-Agent LLM Systems</title>
    <summary>We evaluate trust and reliability in decentralized agent orchestration.</summary>
    <author><name>Alice Example</name></author>
    <category term="cs.AI" />
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2602.00002v1</id>
    <updated>2026-02-26T10:00:00Z</updated>
    <published>2026-02-24T10:00:00Z</published>
    <title>Benchmarking Tool-Using Agents at Scale</title>
    <summary>This benchmark analyzes scaling behavior of code agents.</summary>
    <author><name>Bob Example</name></author>
    <category term="cs.CL" />
  </entry>
</feed>
"""


class TestFIS5ArxivSwarmable(unittest.TestCase):
    def test_parse_feed_extracts_papers(self):
        papers = mod.parse_feed(SAMPLE_FEED)
        self.assertEqual(len(papers), 2)
        self.assertEqual(papers[0].arxiv_id, "2602.00001v1")

    def test_score_theme_prefers_safety_signal(self):
        paper = mod.parse_feed(SAMPLE_FEED)[0]
        theme, score = mod.score_theme(paper)
        self.assertEqual(theme, "safety-reliability")
        self.assertGreaterEqual(score, 2)

    def test_build_lane_plan_returns_lane_ids(self):
        papers = mod.parse_feed(SAMPLE_FEED)
        lanes, paper_theme = mod.build_lane_plan(papers, lane_size=2)
        self.assertTrue(lanes)
        self.assertTrue(lanes[0]["lane_id"].startswith("ARX-"))
        self.assertIn("2602.00002v1", paper_theme)
        self.assertIn("backlog_paper_ids", lanes[0])

    def test_lane_backlog_is_explicit_when_lane_size_small(self):
        papers = mod.parse_feed(SAMPLE_FEED)
        same_theme = [
            papers[0],
            mod.ArxivPaper(
                arxiv_id="2602.99999v1",
                title=papers[0].title,
                summary=papers[0].summary,
                published=papers[0].published,
                updated=papers[0].updated,
                authors=papers[0].authors,
                categories=papers[0].categories,
                abs_url="http://arxiv.org/abs/2602.99999v1",
            ),
        ]
        lanes, _ = mod.build_lane_plan(same_theme, lane_size=1)
        target = next((lane for lane in lanes if lane["theme"] == "safety-reliability"), None)
        self.assertIsNotNone(target)
        # Both synthetic papers map to safety-reliability, so one must be backlog when lane_size=1.
        self.assertEqual(target["selected_count"], 1)
        self.assertEqual(target["backlog_count"], 1)

    def test_payload_date_window_and_coverage_do_not_depend_on_input_order(self):
        papers = list(reversed(mod.parse_feed(SAMPLE_FEED)))
        payload = mod.build_payload(
            query="test",
            max_results=2,
            lane_size=1,
            papers=papers,
        )
        self.assertEqual(payload["date_window"]["newest_published"], "2026-02-25T10:00:00Z")
        self.assertEqual(payload["date_window"]["oldest_published"], "2026-02-24T10:00:00Z")
        coverage = payload["lane_coverage"]
        self.assertEqual(coverage["selected_count"], 2)
        self.assertEqual(coverage["backlog_count"], 0)
        self.assertEqual(coverage["selected_ratio"], 1.0)


if __name__ == "__main__":
    unittest.main()
