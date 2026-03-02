#!/usr/bin/env python3
"""Regression tests for orient.py helper detectors."""

import unittest

try:
    from tools import orient  # type: ignore
except Exception:
    import orient  # type: ignore


class TestUnderusedCoreTools(unittest.TestCase):
    def test_marks_tools_used_when_explicitly_logged(self):
        log_text = "\n".join(
            [
                "S180 | ran python3 tools/orient.py and python3 tools/maintenance.py --quick",
                "S181 | state sync via tools/sync_state.py and tools/validate_beliefs.py",
                "S182 | checks with tools/check.sh and tools/check.ps1",
            ]
        )
        underused, latest, start = orient.check_underused_core_tools(log_text, window_sessions=5)
        self.assertEqual(latest, 182)
        self.assertEqual(start, 178)
        self.assertNotIn("tools/orient.py", underused)
        self.assertNotIn("tools/maintenance.py", underused)
        self.assertNotIn("tools/sync_state.py", underused)
        self.assertNotIn("tools/validate_beliefs.py", underused)
        self.assertIn("tools/compact.py", underused)

    def test_session_window_filters_old_references(self):
        log_text = "\n".join(
            [
                "S180 | ran python3 tools/orient.py",
                "S181 | maintenance pass via tools/maintenance.py",
                "S182 | maintenance pass via tools/maintenance.py",
            ]
        )
        underused, latest, start = orient.check_underused_core_tools(log_text, window_sessions=2)
        self.assertEqual(latest, 182)
        self.assertEqual(start, 181)
        self.assertIn("tools/orient.py", underused)
        self.assertNotIn("tools/maintenance.py", underused)

    def test_normalizes_windows_paths(self):
        log_text = "S186 | ran py -3 tools\\proxy_k.py --save"
        underused, _, _ = orient.check_underused_core_tools(log_text, window_sessions=2)
        self.assertNotIn("tools/proxy_k.py", underused)

    def test_returns_empty_when_no_session_rows(self):
        underused, latest, start = orient.check_underused_core_tools("no session markers", window_sessions=2)
        self.assertEqual(underused, [])
        self.assertIsNone(latest)
        self.assertIsNone(start)


class TestClassifyRouting(unittest.TestCase):
    def test_task_recognizer_in_core_tools(self):
        self.assertIn("tools/task_recognizer.py", orient.CORE_SWARM_TOOLS)

    def test_get_classify_task_long_form(self):
        import sys
        original = sys.argv[:]
        sys.argv = ["orient.py", "--classify", "build something"]
        try:
            result = orient._get_classify_task()
        finally:
            sys.argv = original
        self.assertEqual(result, "build something")

    def test_get_classify_task_equals_form(self):
        import sys
        original = sys.argv[:]
        sys.argv = ["orient.py", "--classify=check for drift"]
        try:
            result = orient._get_classify_task()
        finally:
            sys.argv = original
        self.assertEqual(result, "check for drift")

    def test_get_classify_task_absent(self):
        import sys
        original = sys.argv[:]
        sys.argv = ["orient.py", "--brief"]
        try:
            result = orient._get_classify_task()
        finally:
            sys.argv = original
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
