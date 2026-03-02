#!/usr/bin/env python3
"""Regression tests for bulletin.py inter-swarm messaging."""

import io
import re
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bulletin  # noqa: E402


class TestBulletin(unittest.TestCase):
    """Validate bulletin write/read/scan/help flows in an isolated temp repo."""

    def setUp(self):
        self._tmpdir = Path(tempfile.mkdtemp(prefix="bulletin-test-"))

        self._orig_repo_root = bulletin.REPO_ROOT
        self._orig_bulletins_dir = bulletin.BULLETINS_DIR
        self._orig_children_dir = bulletin.CHILDREN_DIR

        bulletin.REPO_ROOT = self._tmpdir
        bulletin.BULLETINS_DIR = self._tmpdir / "experiments" / "inter-swarm" / "bulletins"
        bulletin.CHILDREN_DIR = self._tmpdir / "experiments" / "children"

    def tearDown(self):
        bulletin.REPO_ROOT = self._orig_repo_root
        bulletin.BULLETINS_DIR = self._orig_bulletins_dir
        bulletin.CHILDREN_DIR = self._orig_children_dir
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _read_request_id(self, swarm_name: str) -> str:
        path = bulletin.BULLETINS_DIR / f"{swarm_name}.md"
        text = path.read_text()
        m = re.search(r"Request-ID:\s*(\S+)", text)
        self.assertIsNotNone(m, "Expected Request-ID in help-request bulletin")
        return m.group(1)

    def _quiet_call(self, fn, *args):
        sink = io.StringIO()
        with redirect_stdout(sink):
            return fn(*args)

    def test_scan_counts_hyphenated_types(self):
        self._quiet_call(bulletin.write_bulletin, "alpha", "sibling-sync", "sync message")
        self._quiet_call(bulletin.write_help_request, "alpha", "need help with validation")

        out = io.StringIO()
        with redirect_stdout(out):
            bulletin.scan_bulletins()
        text = out.getvalue()

        self.assertIn("sibling-sync: 1", text)
        self.assertIn("help-request: 1", text)
        self.assertNotIn("help: 1", text)

    def test_help_queue_open_then_resolved(self):
        self._quiet_call(bulletin.write_help_request, "alpha", "need proof")
        request_id = self._read_request_id("alpha")

        first = io.StringIO()
        with redirect_stdout(first):
            bulletin.help_queue()
        self.assertIn("Open: 1", first.getvalue())
        self.assertIn(request_id, first.getvalue())

        self._quiet_call(bulletin.write_help_response, "beta", request_id, "here is evidence")

        second = io.StringIO()
        with redirect_stdout(second):
            bulletin.help_queue()
        self.assertIn("Open: 0", second.getvalue())
        self.assertIn("No open help requests.", second.getvalue())

    def test_sync_skips_own_bulletin(self):
        child_name = "child-a"
        child_workspace = bulletin.CHILDREN_DIR / child_name / "workspace"
        child_workspace.mkdir(parents=True, exist_ok=True)

        self._quiet_call(bulletin.write_bulletin, "alpha", "discovery", "d1")
        self._quiet_call(bulletin.write_bulletin, child_name, "discovery", "own")

        self._quiet_call(bulletin.sync_to_child, child_name)

        child_bulletins = child_workspace / "bulletins"
        self.assertTrue((child_bulletins / "alpha.md").exists())
        self.assertFalse((child_bulletins / f"{child_name}.md").exists())


if __name__ == "__main__":
    unittest.main()
