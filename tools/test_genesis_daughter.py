#!/usr/bin/env python3
"""Test that genesis daughters pass validate_beliefs.py --quick (GAP-5 L-1618)."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


class TestDaughterValidation(unittest.TestCase):
    def test_daughter_passes_validation(self):
        """Genesis daughter must pass validate_beliefs.py --quick with 0 errors."""
        with tempfile.TemporaryDirectory() as tmp:
            daughter_dir = Path(tmp) / "daughter"
            # Generate genesis bundle
            result = subprocess.run(
                [sys.executable, str(REPO / "tools" / "genesis_extract.py"),
                 "--out", str(daughter_dir)],
                capture_output=True, text=True, cwd=REPO, timeout=120,
            )
            self.assertEqual(result.returncode, 0, f"genesis_extract failed: {result.stderr}")
            self.assertTrue(daughter_dir.exists(), "daughter dir not created")

            # Init git repo (validate_beliefs needs git)
            subprocess.run(["git", "init"], cwd=daughter_dir, capture_output=True)
            subprocess.run(["git", "add", "."], cwd=daughter_dir, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "genesis"],
                cwd=daughter_dir, capture_output=True,
            )

            # Run validate_beliefs.py --quick
            result = subprocess.run(
                [sys.executable, str(daughter_dir / "tools" / "validate_beliefs.py"),
                 "--quick"],
                capture_output=True, text=True, cwd=daughter_dir, timeout=30,
            )
            # Check for PASS
            self.assertIn("RESULT: PASS", result.stdout + result.stderr,
                          f"Daughter validation failed:\n{result.stdout}\n{result.stderr}")
            # Check for 0 errors
            self.assertNotIn("FAIL PHIL:", result.stdout,
                             f"FAIL PHIL errors in daughter:\n{result.stdout}")


if __name__ == "__main__":
    unittest.main()
