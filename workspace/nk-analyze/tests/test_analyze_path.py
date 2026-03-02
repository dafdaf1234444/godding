"""Tests for analyze_path — filesystem-based NK analysis."""

import os
import tempfile
import unittest
from pathlib import Path

from nk_analyze.core import analyze_path


class TestAnalyzePath(unittest.TestCase):
    def _make_package(self, files: dict[str, str]) -> tuple[Path, str]:
        """Create a temporary package with given file contents."""
        tmpdir = tempfile.mkdtemp()
        pkg_name = "testpkg"
        pkg_dir = Path(tmpdir) / pkg_name
        pkg_dir.mkdir()
        for name, content in files.items():
            filepath = pkg_dir / name
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(content)
        self.addCleanup(lambda: __import__("shutil").rmtree(tmpdir))
        return pkg_dir, pkg_name

    def test_basic_analysis(self):
        pkg_dir, pkg_name = self._make_package({
            "__init__.py": "from testpkg import core",
            "core.py": "x = 1",
            "utils.py": "from testpkg import core",
        })
        result = analyze_path(pkg_dir, pkg_name)
        self.assertNotIn("error", result)
        self.assertEqual(result["n"], 3)
        self.assertEqual(result["cycles"], 0)
        self.assertIn("burden", result)

    def test_with_cycles(self):
        pkg_dir, pkg_name = self._make_package({
            "__init__.py": "",
            "a.py": "from testpkg.b import x",
            "b.py": "from testpkg.a import y\nx = 1\ny = 2",
        })
        result = analyze_path(pkg_dir, pkg_name)
        self.assertNotIn("error", result)
        self.assertEqual(result["cycles"], 1)
        self.assertGreater(result["composite"], 0)

    def test_nonexistent_path(self):
        result = analyze_path(Path("/nonexistent/path"), "fake")
        self.assertIn("error", result)

    def test_empty_directory(self):
        tmpdir = tempfile.mkdtemp()
        self.addCleanup(lambda: os.rmdir(tmpdir))
        result = analyze_path(Path(tmpdir), "empty")
        self.assertIn("error", result)

    def test_matches_analyze_package(self):
        """analyze_path on a stdlib package should match analyze_package."""
        from nk_analyze.core import analyze_package, find_package_path
        pkg_path = find_package_path("json")
        if pkg_path is None:
            self.skipTest("json package not found")
        path_result = analyze_path(pkg_path, "json")
        pkg_result = analyze_package("json")
        self.assertEqual(path_result["n"], pkg_result["n"])
        self.assertEqual(path_result["k_avg"], pkg_result["k_avg"])
        self.assertEqual(path_result["cycles"], pkg_result["cycles"])
        self.assertEqual(path_result["composite"], pkg_result["composite"])

    def test_result_has_burden_field(self):
        pkg_dir, pkg_name = self._make_package({
            "__init__.py": "",
            "core.py": "x = 1",
        })
        result = analyze_path(pkg_dir, pkg_name)
        self.assertIn("burden", result)
        self.assertEqual(result["burden"], 0.2)  # 0 cycles + 0.1 * 2 modules


if __name__ == "__main__":
    unittest.main()
