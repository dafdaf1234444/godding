#!/usr/bin/env python3
"""Tests for contract_check.py (F-META8)."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.contract_check import (
    check_active_work_pointer,
    check_identity_invariant,
    check_monotonic_state_vector,
    check_protocol_handshake,
    check_write_obligation,
    run_all,
)


class TestContractCheck(unittest.TestCase):
    def test_identity_invariant_passes(self):
        passed, detail = check_identity_invariant()
        self.assertTrue(passed, f"Identity invariant should pass: {detail}")
        self.assertIn("4 invariants", detail)

    def test_state_vector_parses(self):
        passed, detail = check_monotonic_state_vector()
        self.assertTrue(passed, f"State vector should pass: {detail}")
        self.assertIn("L", detail)
        self.assertIn("P", detail)

    def test_active_work_pointer_exists(self):
        passed, detail = check_active_work_pointer()
        self.assertTrue(passed, f"Work pointer should pass: {detail}")

    def test_protocol_handshake_valid(self):
        passed, detail = check_protocol_handshake()
        self.assertTrue(passed, f"Protocol handshake should pass: {detail}")

    def test_write_obligation_existing_session(self):
        passed, detail = check_write_obligation("S354")
        self.assertTrue(passed, f"S354 should have commits: {detail}")

    def test_run_all_returns_5_components(self):
        _, results = run_all(session_id="S354")
        self.assertEqual(len(results), 5)
        for name in [
            "identity_invariant",
            "monotonic_state_vector",
            "active_work_pointer",
            "write_obligation",
            "protocol_handshake",
        ]:
            self.assertIn(name, results)

    def test_json_output_structure(self):
        """Verify JSON mode produces valid structure."""
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            run_all(session_id="S354", as_json=True)
        data = json.loads(f.getvalue())
        self.assertIn("contract_version", data)
        self.assertIn("all_pass", data)
        self.assertIn("components", data)
        self.assertEqual(data["total"], 5)


if __name__ == "__main__":
    unittest.main()
