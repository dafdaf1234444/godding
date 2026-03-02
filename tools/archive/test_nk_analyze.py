#!/usr/bin/env python3
"""
test_nk_analyze.py — Regression tests for nk_analyze.py

Tests cover:
1. Module listing (list_modules)
2. Import extraction (extract_imports) — including sub-package resolution
3. Cycle detection (detect_cycles)
4. Architecture classification (classify_architecture)
5. Full analysis on stdlib packages (integration)
6. Regression: sub-package import resolution bug (S39 fix)

Usage:
    python3 tools/test_nk_analyze.py
    python3 tools/test_nk_analyze.py -v          # verbose
    python3 tools/test_nk_analyze.py TestCycles   # single class
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent))
from nk_analyze import (
    analyze_lazy_imports,
    analyze_package,
    analyze_path,
    classify_architecture,
    compare_refs,
    detect_cycles,
    extract_imports,
    extract_imports_layered,
    list_modules,
    print_compare_report,
)


class TestDetectCycles(unittest.TestCase):
    """Test cycle detection in dependency graphs."""

    def test_no_cycles(self):
        deps = {"a": ["b"], "b": ["c"], "c": []}
        cycles = detect_cycles(deps)
        self.assertEqual(len(cycles), 0)

    def test_simple_cycle(self):
        deps = {"a": ["b"], "b": ["a"]}
        cycles = detect_cycles(deps)
        self.assertEqual(len(cycles), 1)
        # Cycle should contain both a and b
        cycle_mods = set(cycles[0][:-1])
        self.assertEqual(cycle_mods, {"a", "b"})

    def test_triangle_cycle(self):
        deps = {"a": ["b"], "b": ["c"], "c": ["a"]}
        cycles = detect_cycles(deps)
        self.assertEqual(len(cycles), 1)
        cycle_mods = set(cycles[0][:-1])
        self.assertEqual(cycle_mods, {"a", "b", "c"})

    def test_multiple_independent_cycles(self):
        deps = {"a": ["b"], "b": ["a"], "c": ["d"], "d": ["c"], "e": []}
        cycles = detect_cycles(deps)
        self.assertEqual(len(cycles), 2)

    def test_nested_cycles(self):
        # a→b→c→a and a→b→a (nested)
        deps = {"a": ["b"], "b": ["a", "c"], "c": ["a"]}
        cycles = detect_cycles(deps)
        self.assertGreaterEqual(len(cycles), 2)

    def test_empty_graph(self):
        cycles = detect_cycles({})
        self.assertEqual(len(cycles), 0)

    def test_self_loop_not_counted(self):
        # Self-loops shouldn't appear in our deps (filtered in analyze_package)
        deps = {"a": ["b"], "b": []}
        cycles = detect_cycles(deps)
        self.assertEqual(len(cycles), 0)

    def test_star_topology_no_cycles(self):
        deps = {"hub": ["a", "b", "c"], "a": [], "b": [], "c": []}
        cycles = detect_cycles(deps)
        self.assertEqual(len(cycles), 0)


class TestClassifyArchitecture(unittest.TestCase):
    """Test architecture classification."""

    def test_monolith(self):
        arch = classify_architecture(n=3, k_avg=1.0, k_max=2, cycles=0, hub_pct=0.5)
        self.assertEqual(arch, "monolith")

    def test_tangled(self):
        arch = classify_architecture(n=20, k_avg=3.5, k_max=10, cycles=10, hub_pct=0.2)
        self.assertEqual(arch, "tangled")

    def test_hub_and_spoke(self):
        arch = classify_architecture(n=10, k_avg=1.5, k_max=8, cycles=0, hub_pct=0.6)
        self.assertEqual(arch, "hub-and-spoke")

    def test_framework(self):
        arch = classify_architecture(n=10, k_avg=3.0, k_max=5, cycles=1, hub_pct=0.2)
        self.assertEqual(arch, "framework")

    def test_registry(self):
        arch = classify_architecture(n=10, k_avg=1.5, k_max=6, cycles=0, hub_pct=0.2)
        self.assertEqual(arch, "registry")

    def test_facade(self):
        arch = classify_architecture(n=10, k_avg=1.0, k_max=3, cycles=0, hub_pct=0.4)
        self.assertEqual(arch, "facade")

    def test_distributed(self):
        arch = classify_architecture(n=10, k_avg=1.0, k_max=2, cycles=0, hub_pct=0.1)
        self.assertEqual(arch, "distributed")


class SyntheticPackageMixin:
    """Mixin to create temporary synthetic packages for testing."""

    def create_package(self, name, modules):
        """Create a temporary package with given module files.

        Args:
            name: package name (directory name)
            modules: dict of {filename: source_code}
                     e.g. {"__init__.py": "from . import utils", "utils.py": "x = 1"}
        Returns:
            Path to the package directory
        """
        pkg_dir = Path(self._tmpdir.name) / name
        pkg_dir.mkdir(parents=True, exist_ok=True)
        for filename, source in modules.items():
            filepath = pkg_dir / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(source)
        return pkg_dir

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self._tmpdir.cleanup()


class TestListModules(SyntheticPackageMixin, unittest.TestCase):
    """Test module listing."""

    def test_simple_package(self):
        pkg = self.create_package("mypkg", {
            "__init__.py": "",
            "a.py": "",
            "b.py": "",
        })
        modules = list_modules(pkg)
        self.assertEqual(set(modules.keys()), {"__init__", "a", "b"})

    def test_sub_package(self):
        pkg = self.create_package("mypkg", {
            "__init__.py": "",
            "core.py": "",
            "sub/__init__.py": "",
            "sub/helpers.py": "",
        })
        modules = list_modules(pkg)
        self.assertIn("sub", modules)
        self.assertIn("sub.helpers", modules)
        self.assertIn("core", modules)

    def test_skips_pycache(self):
        pkg = self.create_package("mypkg", {
            "__init__.py": "",
            "a.py": "",
            "__pycache__/a.cpython-311.pyc": "binary",
        })
        modules = list_modules(pkg)
        self.assertNotIn("__pycache__", str(modules))

    def test_skips_test_dirs(self):
        pkg = self.create_package("mypkg", {
            "__init__.py": "",
            "core.py": "",
            "tests/__init__.py": "",
            "tests/test_core.py": "",
        })
        modules = list_modules(pkg)
        self.assertNotIn("tests.test_core", modules)
        self.assertNotIn("tests", modules)

    def test_nested_sub_packages(self):
        pkg = self.create_package("mypkg", {
            "__init__.py": "",
            "a/__init__.py": "",
            "a/b/__init__.py": "",
            "a/b/c.py": "",
        })
        modules = list_modules(pkg)
        self.assertIn("a.b.c", modules)
        self.assertIn("a.b", modules)
        self.assertIn("a", modules)


class TestExtractImports(SyntheticPackageMixin, unittest.TestCase):
    """Test import extraction, especially relative import resolution."""

    def test_absolute_import(self):
        pkg = self.create_package("mypkg", {
            "__init__.py": "",
            "a.py": "from mypkg.b import something",
            "b.py": "",
        })
        imports = extract_imports(pkg / "a.py", "mypkg")
        self.assertIn("b", imports)

    def test_relative_import_dot(self):
        pkg = self.create_package("mypkg", {
            "__init__.py": "",
            "a.py": "from .b import something",
            "b.py": "",
        })
        imports = extract_imports(pkg / "a.py", "mypkg")
        self.assertIn("b", imports)

    def test_relative_import_from_dot(self):
        pkg = self.create_package("mypkg", {
            "__init__.py": "",
            "a.py": "from . import b",
            "b.py": "",
        })
        imports = extract_imports(pkg / "a.py", "mypkg")
        self.assertIn("b", imports)

    def test_sub_package_relative_import(self):
        """Regression test for S39 sub-package import resolution bug.

        When sub/child.py does 'from .sibling import X', it should resolve
        to 'sub.sibling', NOT to top-level 'sibling'.
        """
        pkg = self.create_package("mypkg", {
            "__init__.py": "",
            "sibling.py": "# top-level sibling",
            "sub/__init__.py": "",
            "sub/sibling.py": "# sub-package sibling",
            "sub/child.py": "from .sibling import something",
        })
        imports = extract_imports(pkg / "sub" / "child.py", "mypkg")
        self.assertIn("sub.sibling", imports)
        # Should NOT resolve to just "sibling" (the top-level one)
        self.assertNotIn("sibling", imports)

    def test_sub_package_init_relative_import(self):
        """Regression: sub/__init__.py 'from .mod import X' → 'sub.mod'."""
        pkg = self.create_package("mypkg", {
            "__init__.py": "",
            "sub/__init__.py": "from .helpers import util_func",
            "sub/helpers.py": "def util_func(): pass",
        })
        imports = extract_imports(pkg / "sub" / "__init__.py", "mypkg")
        self.assertIn("sub.helpers", imports)

    def test_double_dot_relative(self):
        """from ..module import X in nested sub-package."""
        pkg = self.create_package("mypkg", {
            "__init__.py": "",
            "top.py": "",
            "sub/__init__.py": "",
            "sub/deep/__init__.py": "",
            "sub/deep/mod.py": "from ...top import something",
        })
        imports = extract_imports(pkg / "sub" / "deep" / "mod.py", "mypkg")
        self.assertIn("top", imports)

    def test_absolute_deep_import(self):
        pkg = self.create_package("mypkg", {
            "__init__.py": "",
            "a.py": "from mypkg.sub.deep import something",
            "sub/__init__.py": "",
            "sub/deep.py": "",
        })
        imports = extract_imports(pkg / "a.py", "mypkg")
        self.assertIn("sub.deep", imports)
        self.assertIn("sub", imports)

    def test_import_statement(self):
        pkg = self.create_package("mypkg", {
            "__init__.py": "",
            "a.py": "import mypkg.b",
            "b.py": "",
        })
        imports = extract_imports(pkg / "a.py", "mypkg")
        self.assertIn("b", imports)

    def test_external_import_ignored(self):
        pkg = self.create_package("mypkg", {
            "__init__.py": "",
            "a.py": "import os\nfrom collections import defaultdict\nfrom .b import x",
            "b.py": "",
        })
        imports = extract_imports(pkg / "a.py", "mypkg")
        self.assertNotIn("os", imports)
        self.assertNotIn("collections", imports)
        self.assertIn("b", imports)

    def test_syntax_error_returns_empty(self):
        pkg = self.create_package("mypkg", {
            "__init__.py": "",
            "bad.py": "def f(:\n    pass",
        })
        imports = extract_imports(pkg / "bad.py", "mypkg")
        self.assertEqual(imports, [])


class TestAnalyzePackageIntegration(unittest.TestCase):
    """Integration tests using real stdlib packages."""

    def test_json_package(self):
        result = analyze_package("json")
        if "error" in result:
            self.skipTest("json package not available")
        self.assertGreater(result["n"], 0)
        self.assertGreaterEqual(result["k_avg"], 0)
        self.assertEqual(result["cycles"], 0, "json should have 0 cycles")
        self.assertLess(result["composite"], 10, "json composite should be low")

    def test_logging_package(self):
        result = analyze_package("logging")
        if "error" in result:
            self.skipTest("logging package not available")
        self.assertGreater(result["n"], 0)
        self.assertEqual(result["cycles"], 0, "logging should have 0 cycles")

    def test_email_package(self):
        result = analyze_package("email")
        if "error" in result:
            self.skipTest("email package not available")
        self.assertGreater(result["n"], 15)
        # After S39 fix: static cycles should be low (lazy imports hide runtime cycles)
        self.assertLess(result["cycles"], 10,
                        "email static cycles should be < 10 (lazy imports hide runtime cycles)")

    def test_single_file_module(self):
        result = analyze_package("os")
        self.assertIn("error", result, "os is single-file, should return error")

    def test_nonexistent_package(self):
        result = analyze_package("definitely_not_a_real_package_xyz")
        self.assertIn("error", result)

    def test_multiprocessing_cycles(self):
        result = analyze_package("multiprocessing")
        if "error" in result:
            self.skipTest("multiprocessing not available")
        self.assertGreater(result["cycles"], 5,
                           "multiprocessing should have many cycles (context hub)")

    def test_composite_ordering(self):
        """Composite scores should maintain correct ordinal ranking."""
        packages = ["json", "email", "asyncio"]
        results = {}
        for pkg in packages:
            r = analyze_package(pkg)
            if "error" not in r:
                results[pkg] = r["composite"]

        if len(results) < 3:
            self.skipTest("Not all packages available")

        self.assertLess(results["json"], results["email"],
                        "json should rank lower than email")
        self.assertLess(results["email"], results["asyncio"],
                        "email should rank lower than asyncio")


class TestSubPackageResolution(SyntheticPackageMixin, unittest.TestCase):
    """Targeted regression tests for the S39 sub-package resolution bug.

    The bug: pkg_base was calculated as pkg_root.parent instead of
    pkg_root.parent.parent, causing relative imports in sub-packages
    to resolve to wrong modules.
    """

    def test_resources_abc_resolution(self):
        """Simulate importlib/resources/__init__.py importing from .abc.

        Before fix: resolved to top-level 'abc' module
        After fix: resolves to 'resources.abc' sub-module
        """
        pkg = self.create_package("fakepkg", {
            "__init__.py": "",
            "abc.py": "# top-level abc",
            "resources/__init__.py": "from .abc import ResourceReader",
            "resources/abc.py": "class ResourceReader: pass",
        })
        imports = extract_imports(
            pkg / "resources" / "__init__.py", "fakepkg"
        )
        self.assertIn("resources.abc", imports)

    def test_deep_subpackage_relative(self):
        """Three levels deep: a/b/c.py importing from .d."""
        pkg = self.create_package("fakepkg", {
            "__init__.py": "",
            "a/__init__.py": "",
            "a/b/__init__.py": "",
            "a/b/c.py": "from .d import something",
            "a/b/d.py": "",
        })
        imports = extract_imports(pkg / "a" / "b" / "c.py", "fakepkg")
        self.assertIn("a.b.d", imports)

    def test_cross_subpackage_import(self):
        """sub1/mod.py importing from ..sub2.mod."""
        pkg = self.create_package("fakepkg", {
            "__init__.py": "",
            "sub1/__init__.py": "",
            "sub1/mod.py": "from ..sub2 import helper",
            "sub2/__init__.py": "",
            "sub2/helper.py": "",
        })
        imports = extract_imports(pkg / "sub1" / "mod.py", "fakepkg")
        self.assertIn("sub2", imports)


class TestExtractImportsLayered(SyntheticPackageMixin, unittest.TestCase):
    """Test scope-aware import extraction (top-level vs lazy)."""

    def test_all_top_level(self):
        """All imports at module level should be top_level."""
        pkg = self.create_package("mypkg", {
            "__init__.py": "",
            "a.py": "from . import b\nfrom . import c",
            "b.py": "",
            "c.py": "",
        })
        result = extract_imports_layered(pkg / "a.py", "mypkg")
        self.assertIn("b", result["top_level"])
        self.assertIn("c", result["top_level"])
        self.assertEqual(result["lazy"], [])

    def test_lazy_in_function(self):
        """Import inside a function should be lazy."""
        pkg = self.create_package("mypkg", {
            "__init__.py": "",
            "a.py": "def foo():\n    from . import b\n",
            "b.py": "",
        })
        result = extract_imports_layered(pkg / "a.py", "mypkg")
        self.assertEqual(result["top_level"], [])
        self.assertIn("b", result["lazy"])
        self.assertEqual(len(result["lazy_locations"]), 1)
        self.assertEqual(result["lazy_locations"][0]["func"], "foo")

    def test_mixed_imports(self):
        """Mix of top-level and lazy imports."""
        pkg = self.create_package("mypkg", {
            "__init__.py": "",
            "a.py": "from . import b\ndef foo():\n    from . import c\n",
            "b.py": "",
            "c.py": "",
        })
        result = extract_imports_layered(pkg / "a.py", "mypkg")
        self.assertIn("b", result["top_level"])
        self.assertNotIn("b", result["lazy"])
        self.assertIn("c", result["lazy"])
        self.assertNotIn("c", result["top_level"])

    def test_async_function_is_lazy(self):
        """Import inside async function should be lazy."""
        pkg = self.create_package("mypkg", {
            "__init__.py": "",
            "a.py": "async def bar():\n    from . import b\n",
            "b.py": "",
        })
        result = extract_imports_layered(pkg / "a.py", "mypkg")
        self.assertIn("b", result["lazy"])
        self.assertEqual(result["lazy_locations"][0]["func"], "bar")

    def test_class_method_is_lazy(self):
        """Import inside a class method should be lazy."""
        pkg = self.create_package("mypkg", {
            "__init__.py": "",
            "a.py": "class Foo:\n    def bar(self):\n        from . import b\n",
            "b.py": "",
        })
        result = extract_imports_layered(pkg / "a.py", "mypkg")
        self.assertIn("b", result["lazy"])
        self.assertEqual(result["lazy_locations"][0]["func"], "bar")

    def test_lazy_location_tracks_line(self):
        """Lazy location should track the correct line number."""
        pkg = self.create_package("mypkg", {
            "__init__.py": "",
            "a.py": "# line 1\n# line 2\ndef foo():\n    # line 4\n    from . import b\n",
            "b.py": "",
        })
        result = extract_imports_layered(pkg / "a.py", "mypkg")
        self.assertEqual(result["lazy_locations"][0]["line"], 5)

    def test_empty_file(self):
        """Empty file should return empty results."""
        pkg = self.create_package("mypkg", {
            "__init__.py": "",
            "a.py": "",
        })
        result = extract_imports_layered(pkg / "a.py", "mypkg")
        self.assertEqual(result["top_level"], [])
        self.assertEqual(result["lazy"], [])


class TestAnalyzeLazyImports(SyntheticPackageMixin, unittest.TestCase):
    """Test the full lazy import analysis pipeline."""

    def _add_to_syspath(self, parent_dir):
        sys.path.insert(0, str(parent_dir))
        self.addCleanup(lambda: sys.path.remove(str(parent_dir)))

    def test_no_lazy_verdict(self):
        """Package with no lazy imports gets NO_LAZY verdict."""
        pkg = self.create_package("nolazy", {
            "__init__.py": "",
            "a.py": "from . import b",
            "b.py": "",
        })
        self._add_to_syspath(pkg.parent)
        result = analyze_lazy_imports("nolazy")
        if "error" in result:
            self.skipTest("Could not analyze synthetic package")
        self.assertEqual(result["hypothesis_f44"], "NO_LAZY")
        self.assertEqual(result["total_lazy_imports"], 0)

    def test_cycle_breaking_lazy(self):
        """Lazy import that prevents a cycle should be detected."""
        pkg = self.create_package("cycbrk", {
            "__init__.py": "",
            "a.py": "from . import b",
            "b.py": "def foo():\n    from . import a\n",
        })
        self._add_to_syspath(pkg.parent)
        result = analyze_lazy_imports("cycbrk")
        if "error" in result:
            self.skipTest("Could not analyze synthetic package")
        self.assertEqual(result["total_lazy_imports"], 1)
        self.assertEqual(result["cycle_breaking_lazy"], 1)
        self.assertEqual(result["static_cycles"], 0)
        self.assertGreater(result["runtime_cycles"], 0)
        self.assertEqual(result["hypothesis_f44"], "SUPPORTS")

    def test_non_cycle_breaking_lazy(self):
        """Lazy import that doesn't break a cycle → REFUTES."""
        pkg = self.create_package("ncblazy", {
            "__init__.py": "",
            "a.py": "def foo():\n    from . import b\n",
            "b.py": "",
        })
        self._add_to_syspath(pkg.parent)
        result = analyze_lazy_imports("ncblazy")
        if "error" in result:
            self.skipTest("Could not analyze synthetic package")
        self.assertEqual(result["total_lazy_imports"], 1)
        self.assertEqual(result["cycle_breaking_lazy"], 0)
        self.assertEqual(result["hypothesis_f44"], "REFUTES")

    def test_partial_verdict(self):
        """Mix of cycle-breaking and non-cycle-breaking → PARTIAL."""
        pkg = self.create_package("partial", {
            "__init__.py": "",
            "a.py": "from . import b\ndef foo():\n    from . import c\n",
            "b.py": "def bar():\n    from . import a\n",
            "c.py": "",
        })
        self._add_to_syspath(pkg.parent)
        result = analyze_lazy_imports("partial")
        if "error" in result:
            self.skipTest("Could not analyze synthetic package")
        self.assertGreater(result["cycle_breaking_lazy"], 0)
        self.assertGreater(result["non_cycle_breaking_lazy"], 0)
        self.assertEqual(result["hypothesis_f44"], "PARTIAL")

    def test_hidden_cycles_count(self):
        """Hidden cycles = runtime - static."""
        pkg = self.create_package("hidden", {
            "__init__.py": "",
            "a.py": "from . import b",
            "b.py": "def foo():\n    from . import a\n",
        })
        self._add_to_syspath(pkg.parent)
        result = analyze_lazy_imports("hidden")
        if "error" in result:
            self.skipTest("Could not analyze synthetic package")
        self.assertEqual(result["hidden_cycles"], result["runtime_cycles"] - result["static_cycles"])
        self.assertGreater(result["hidden_cycles"], 0)


class TestEndToEnd(SyntheticPackageMixin, unittest.TestCase):
    """End-to-end tests with synthetic packages."""

    def _add_to_syspath(self, parent_dir):
        """Temporarily add a directory to sys.path for import resolution."""
        sys.path.insert(0, str(parent_dir))
        self.addCleanup(lambda: sys.path.remove(str(parent_dir)))

    def test_zero_cycle_package(self):
        """Package with no cycles should score K_avg * N."""
        pkg = self.create_package("zerocycle", {
            "__init__.py": "from . import a, b, c",
            "a.py": "",
            "b.py": "from . import a",
            "c.py": "from . import a, b",
        })
        self._add_to_syspath(pkg.parent)
        result = analyze_package("zerocycle")
        if "error" in result:
            self.skipTest("Could not analyze synthetic package")
        self.assertEqual(result["cycles"], 0)
        self.assertAlmostEqual(result["composite"], result["k_avg"] * result["n"], places=1)

    def test_cyclic_package(self):
        """Package with cycles should show cycles > 0."""
        pkg = self.create_package("cyclic", {
            "__init__.py": "",
            "a.py": "from . import b",
            "b.py": "from . import a",
        })
        self._add_to_syspath(pkg.parent)
        result = analyze_package("cyclic")
        if "error" in result:
            self.skipTest("Could not analyze synthetic package")
        self.assertGreater(result["cycles"], 0)


class TestLazyImportsRealPackages(unittest.TestCase):
    """Integration tests: lazy import detection on real stdlib packages."""

    def test_email_has_lazy_imports(self):
        result = analyze_lazy_imports("email")
        if "error" in result:
            self.skipTest("email not available")
        self.assertGreater(result["total_lazy_imports"], 0)

    def test_asyncio_has_lazy_import(self):
        result = analyze_lazy_imports("asyncio")
        if "error" in result:
            self.skipTest("asyncio not available")
        self.assertGreater(result["total_lazy_imports"], 0)

    def test_multiprocessing_heavy_lazy(self):
        """multiprocessing should have many lazy imports."""
        result = analyze_lazy_imports("multiprocessing")
        if "error" in result:
            self.skipTest("multiprocessing not available")
        self.assertGreater(result["total_lazy_imports"], 20)
        self.assertGreater(result["cycle_breaking_lazy"], 10)
        self.assertGreater(result["hidden_cycles"], 5)


class TestAnalyzePath(SyntheticPackageMixin, unittest.TestCase):
    """Test analyze_path — filesystem-based NK analysis."""

    def test_basic_analysis(self):
        """analyze_path should produce same structure as analyze_package."""
        pkg = self.create_package("pathpkg", {
            "__init__.py": "from . import a, b",
            "a.py": "from . import b",
            "b.py": "",
        })
        result = analyze_path(pkg, "pathpkg")
        self.assertNotIn("error", result)
        self.assertEqual(result["n"], 3)
        self.assertEqual(result["cycles"], 0)
        self.assertIn("composite", result)
        self.assertIn("architecture", result)
        self.assertIn("modules", result)

    def test_cyclic_path(self):
        """analyze_path should detect cycles."""
        pkg = self.create_package("cyclepath", {
            "__init__.py": "",
            "a.py": "from . import b",
            "b.py": "from . import a",
        })
        result = analyze_path(pkg, "cyclepath")
        self.assertNotIn("error", result)
        self.assertGreater(result["cycles"], 0)

    def test_nonexistent_path(self):
        """analyze_path should return error for nonexistent path."""
        result = analyze_path(Path("/tmp/definitely_not_existing_pkg_xyz"), "fake")
        self.assertIn("error", result)

    def test_empty_package(self):
        """analyze_path on empty dir should return error."""
        pkg = self.create_package("emptypkg", {})
        result = analyze_path(pkg, "emptypkg")
        self.assertIn("error", result)

    def test_result_keys(self):
        """analyze_path result should have all expected keys."""
        pkg = self.create_package("keypkg", {
            "__init__.py": "",
            "mod.py": "",
        })
        result = analyze_path(pkg, "keypkg")
        self.assertNotIn("error", result)
        expected_keys = ["package", "path", "n", "k_total", "k_avg", "k_n",
                         "k_max", "k_max_file", "cycles", "cycle_details",
                         "composite", "architecture", "hub_pct", "total_loc",
                         "modules", "in_degree"]
        for key in expected_keys:
            self.assertIn(key, result, f"Missing key: {key}")


class TestCompareRefs(SyntheticPackageMixin, unittest.TestCase):
    """Test compare_refs — git-based ΔNK comparison."""

    def _create_git_repo_with_two_versions(self):
        """Create a temp git repo with two tagged versions of a package."""
        import subprocess

        repo_dir = Path(self._tmpdir.name) / "testrepo"
        repo_dir.mkdir()
        pkg_dir = repo_dir / "src" / "testpkg"
        pkg_dir.mkdir(parents=True)

        subprocess.run(["git", "init"], cwd=repo_dir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"],
                       cwd=repo_dir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"],
                       cwd=repo_dir, capture_output=True)

        # Version 1: simple package, no cycles
        (pkg_dir / "__init__.py").write_text("from . import a")
        (pkg_dir / "a.py").write_text("from . import b")
        (pkg_dir / "b.py").write_text("")
        subprocess.run(["git", "add", "."], cwd=repo_dir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "v1"], cwd=repo_dir, capture_output=True)
        subprocess.run(["git", "tag", "v1.0"], cwd=repo_dir, capture_output=True)

        # Version 2: add a cycle and a module
        (pkg_dir / "b.py").write_text("from . import a")  # creates a→b→a cycle
        (pkg_dir / "c.py").write_text("from . import a")
        subprocess.run(["git", "add", "."], cwd=repo_dir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "v2"], cwd=repo_dir, capture_output=True)
        subprocess.run(["git", "tag", "v2.0"], cwd=repo_dir, capture_output=True)

        return repo_dir

    def test_compare_basic(self):
        """compare_refs should return before, after, and delta."""
        repo = self._create_git_repo_with_two_versions()
        result = compare_refs(str(repo), "src/testpkg", "testpkg", "v1.0", "v2.0")

        self.assertNotIn("error", result)
        self.assertIn("before", result)
        self.assertIn("after", result)
        self.assertIn("delta", result)
        self.assertEqual(result["ref_before"], "v1.0")
        self.assertEqual(result["ref_after"], "v2.0")

    def test_compare_delta_values(self):
        """Delta should correctly compute after - before."""
        repo = self._create_git_repo_with_two_versions()
        result = compare_refs(str(repo), "src/testpkg", "testpkg", "v1.0", "v2.0")

        self.assertNotIn("error", result)
        b = result["before"]
        a = result["after"]
        d = result["delta"]

        self.assertEqual(d["n"], a["n"] - b["n"])
        self.assertEqual(d["cycles"], a["cycles"] - b["cycles"])
        self.assertGreater(d["cycles"], 0, "v2 added a cycle, delta should be positive")

    def test_compare_cycles_increase(self):
        """v1→v2 should show cycles increased."""
        repo = self._create_git_repo_with_two_versions()
        result = compare_refs(str(repo), "src/testpkg", "testpkg", "v1.0", "v2.0")

        self.assertEqual(result["before"]["cycles"], 0)
        self.assertGreater(result["after"]["cycles"], 0)

    def test_compare_invalid_repo(self):
        """compare_refs should return error for non-git dir."""
        result = compare_refs("/tmp", "src/pkg", "pkg", "v1", "v2")
        self.assertIn("error", result)

    def test_compare_restores_head(self):
        """After compare, repo should be back to original HEAD."""
        import subprocess

        repo = self._create_git_repo_with_two_versions()
        orig = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo, capture_output=True, text=True
        ).stdout.strip()

        compare_refs(str(repo), "src/testpkg", "testpkg", "v1.0", "v2.0")

        after = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo, capture_output=True, text=True
        ).stdout.strip()

        self.assertEqual(orig, after, "HEAD should be restored after compare")

    def test_print_compare_report_no_crash(self):
        """print_compare_report should not crash with valid input."""
        repo = self._create_git_repo_with_two_versions()
        result = compare_refs(str(repo), "src/testpkg", "testpkg", "v1.0", "v2.0")
        # Should not raise
        import io
        from contextlib import redirect_stdout
        f = io.StringIO()
        with redirect_stdout(f):
            print_compare_report(result)
        output = f.getvalue()
        # Accept both spellings to avoid Unicode/header drift across hosts.
        self.assertRegex(output, r"(?:ΔNK|DeltaNK) COMPARISON")
        self.assertIn("VERDICT", output)

    def test_print_compare_report_error(self):
        """print_compare_report should handle error results."""
        import io
        from contextlib import redirect_stdout
        f = io.StringIO()
        with redirect_stdout(f):
            print_compare_report({"error": "test error"})
        self.assertIn("ERROR", f.getvalue())


if __name__ == "__main__":
    unittest.main()
