#!/usr/bin/env python3
"""Regression tests for maintenance.py runner behavior."""

import sys
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import maintenance  # noqa: E402


class _FakeHeadCache:
    def __init__(self, initial=None):
        self._data = dict(initial or {})
        self.set_calls: list[tuple[str, list[list[str]]]] = []

    def get(self, key: str):
        return self._data.get(key)

    def set(self, key: str, value):
        self._data[key] = value
        self.set_calls.append((key, value))


def _named_check(name, fn):
    fn.__name__ = name
    return fn


class TestExecuteChecks(unittest.TestCase):
    def test_non_live_cache_misses_run_in_parallel_and_keep_order(self):
        barrier = threading.Barrier(2, timeout=0.5)
        cache = _FakeHeadCache({
            "maint_check_cached": [["DUE", "cached"]],
        })

        def check_cached():
            raise AssertionError("cached check should not execute")

        def check_live():
            return [("NOTICE", "live")]

        def check_parallel_a():
            barrier.wait()
            return [("NOTICE", "parallel-a")]

        def check_parallel_b():
            barrier.wait()
            return [("NOTICE", "parallel-b")]

        checks = [
            _named_check("check_cached", check_cached),
            _named_check("check_live", check_live),
            _named_check("check_parallel_a", check_parallel_a),
            _named_check("check_parallel_b", check_parallel_b),
        ]

        items, check_items = maintenance._execute_checks(
            checks,
            {"check_live"},
            head_cache=cache,
            max_workers=2,
        )

        self.assertEqual(
            items,
            [
                ("DUE", "cached"),
                ("NOTICE", "live"),
                ("NOTICE", "parallel-a"),
                ("NOTICE", "parallel-b"),
            ],
        )
        self.assertEqual(check_items["check_cached"], [("DUE", "cached")])
        self.assertEqual(check_items["check_live"], [("NOTICE", "live")])
        self.assertEqual(
            [key for key, _ in cache.set_calls],
            ["maint_check_parallel_a", "maint_check_parallel_b"],
        )

    def test_check_errors_become_notice_items(self):
        def check_bad():
            raise RuntimeError("boom")

        def check_good():
            return [("NOTICE", "good")]

        checks = [
            _named_check("check_bad", check_bad),
            _named_check("check_good", check_good),
        ]

        items, check_items = maintenance._execute_checks(checks, set(), head_cache=None, max_workers=2)

        self.assertEqual(items[0], ("NOTICE", "check_bad error: boom"))
        self.assertIn(("NOTICE", "good"), items)
        self.assertEqual(check_items["check_bad"], [])
        self.assertEqual(check_items["check_good"], [("NOTICE", "good")])


if __name__ == "__main__":
    unittest.main()
