#!/usr/bin/env python3
"""Regression tests for references/recordings structure policy."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    from tools import maintenance  # type: ignore
except Exception:
    import maintenance  # type: ignore


def _write(path: Path, text: str = "ok\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class TestStructureLayout(unittest.TestCase):
    def _run_check(self, seed_fn) -> list[tuple[str, str]]:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            seed_fn(root)
            with patch.object(maintenance, "REPO_ROOT", root):
                return maintenance.check_structure_layout()

    def test_clean_structure_is_not_flagged(self):
        def seed(root: Path) -> None:
            _write(root / "docs/SWARM-STRUCTURE.md")
            _write(root / "references/README.md")
            _write(root / "recordings/README.md")
            _write(root / "references/finance/f-fin1-s186.md")
            _write(root / "references/finance/f-fin1-s186.json", "{}\n")
            _write(root / "recordings/swarm/2026-02-27-structure-s186.md")
            _write(root / "recordings/swarm/2026-02-27-structure-s186.log")

        results = self._run_check(seed)
        self.assertEqual(results, [], f"Expected clean structure, got: {results}")

    def test_missing_required_files_are_due(self):
        def seed(root: Path) -> None:
            (root / "references").mkdir(parents=True, exist_ok=True)
            (root / "recordings").mkdir(parents=True, exist_ok=True)

        results = self._run_check(seed)
        self.assertTrue(any(level == "DUE" and "Structure policy files missing" in msg for level, msg in results))

    def test_disallowed_extension_is_flagged(self):
        def seed(root: Path) -> None:
            _write(root / "docs/SWARM-STRUCTURE.md")
            _write(root / "references/README.md")
            _write(root / "recordings/README.md")
            _write(root / "recordings/swarm/raw-capture.mp4", "binary-placeholder")

        results = self._run_check(seed)
        self.assertTrue(any("recordings/ has disallowed file types" in msg for _, msg in results))
        self.assertTrue(any("raw-capture.mp4" in msg for _, msg in results))


if __name__ == "__main__":
    unittest.main()
