"""Tests for nk_analyze_go.core — Go project NK analysis."""
import tempfile
from pathlib import Path
import pytest
from nk_analyze_go.core import (
    find_module_path,
    list_packages,
    extract_imports,
    extract_package_name,
    filter_internal_imports,
    count_lines,
    detect_cycles,
    classify_architecture,
    analyze_go_project,
    pkg_display_name,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def go_project(tmp_path):
    """Create a minimal Go project for testing."""
    # go.mod
    (tmp_path / "go.mod").write_text("module github.com/test/mymod\n\ngo 1.21\n")

    # root package
    (tmp_path / "main.go").write_text('''package main
import (
    "fmt"
    "github.com/test/mymod/util"
    "github.com/test/mymod/core"
)
func main() {}
''')

    # util package
    (tmp_path / "util").mkdir()
    (tmp_path / "util" / "util.go").write_text('''package util
import "fmt"
func Helper() {}
''')

    # core package
    (tmp_path / "core").mkdir()
    (tmp_path / "core" / "core.go").write_text('''package core
import "github.com/test/mymod/util"
func Run() {}
''')

    return tmp_path


@pytest.fixture
def go_project_with_cycle(tmp_path):
    """Create a Go project with a circular dependency."""
    (tmp_path / "go.mod").write_text("module github.com/test/cyclemod\n\ngo 1.21\n")

    (tmp_path / "alpha").mkdir()
    (tmp_path / "alpha" / "alpha.go").write_text('''package alpha
import "github.com/test/cyclemod/beta"
func A() {}
''')

    (tmp_path / "beta").mkdir()
    (tmp_path / "beta" / "beta.go").write_text('''package beta
import "github.com/test/cyclemod/alpha"
func B() {}
''')

    return tmp_path


# ---------------------------------------------------------------------------
# find_module_path
# ---------------------------------------------------------------------------

def test_find_module_path_returns_module(go_project):
    result = find_module_path(go_project)
    assert result == "github.com/test/mymod"


def test_find_module_path_no_gomod(tmp_path):
    result = find_module_path(tmp_path)
    assert result is None


def test_find_module_path_exact_string(go_project):
    result = find_module_path(go_project)
    assert isinstance(result, str)
    assert result.startswith("github.com/")


def test_find_module_path_nonexistent_dir():
    result = find_module_path(Path("/nonexistent/path/that/does/not/exist"))
    assert result is None


# ---------------------------------------------------------------------------
# list_packages
# ---------------------------------------------------------------------------

def test_list_packages_finds_root(go_project):
    pkgs = list_packages(go_project)
    assert "" in pkgs


def test_list_packages_finds_util(go_project):
    pkgs = list_packages(go_project)
    assert "util" in pkgs


def test_list_packages_finds_core(go_project):
    pkgs = list_packages(go_project)
    assert "core" in pkgs


def test_list_packages_count(go_project):
    pkgs = list_packages(go_project)
    assert len(pkgs) == 3


def test_list_packages_skips_vendor(tmp_path):
    (tmp_path / "go.mod").write_text("module github.com/test/mod\n\ngo 1.21\n")
    (tmp_path / "main.go").write_text("package main\nfunc main() {}\n")
    vendor = tmp_path / "vendor" / "somepkg"
    vendor.mkdir(parents=True)
    (vendor / "lib.go").write_text("package somepkg\nfunc Fn() {}\n")
    pkgs = list_packages(tmp_path)
    assert "vendor/somepkg" not in pkgs


def test_list_packages_skips_testdata(tmp_path):
    (tmp_path / "go.mod").write_text("module github.com/test/mod\n\ngo 1.21\n")
    (tmp_path / "main.go").write_text("package main\nfunc main() {}\n")
    td = tmp_path / "testdata"
    td.mkdir()
    (td / "data.go").write_text("package testdata\nfunc X() {}\n")
    pkgs = list_packages(tmp_path)
    assert "testdata" not in pkgs


def test_list_packages_skips_test_files(tmp_path):
    (tmp_path / "go.mod").write_text("module github.com/test/mod\n\ngo 1.21\n")
    (tmp_path / "main.go").write_text("package main\nfunc main() {}\n")
    (tmp_path / "main_test.go").write_text("package main\nfunc TestFoo(t testing.T) {}\n")
    pkgs = list_packages(tmp_path)
    root_files = pkgs.get("", [])
    names = [f.name for f in root_files]
    assert "main_test.go" not in names
    assert "main.go" in names


def test_list_packages_returns_path_objects(go_project):
    pkgs = list_packages(go_project)
    for suffix, files in pkgs.items():
        for f in files:
            assert isinstance(f, Path)


# ---------------------------------------------------------------------------
# extract_imports
# ---------------------------------------------------------------------------

def test_extract_imports_main_go(go_project):
    main_go = go_project / "main.go"
    imports = extract_imports(main_go)
    assert "fmt" in imports
    assert "github.com/test/mymod/util" in imports
    assert "github.com/test/mymod/core" in imports


def test_extract_imports_util_go(go_project):
    util_go = go_project / "util" / "util.go"
    imports = extract_imports(util_go)
    assert "fmt" in imports


def test_extract_imports_no_internal(go_project):
    util_go = go_project / "util" / "util.go"
    imports = extract_imports(util_go)
    # util only imports fmt — no internal imports
    assert "github.com/test/mymod" not in imports


def test_extract_imports_grouped(tmp_path):
    f = tmp_path / "grouped.go"
    f.write_text('''package main
import (
    "fmt"
    "os"
    "net/http"
)
func main() {}
''')
    imports = extract_imports(f)
    assert "fmt" in imports
    assert "os" in imports
    assert "net/http" in imports


def test_extract_imports_single_style(tmp_path):
    f = tmp_path / "single.go"
    f.write_text('''package main
import "fmt"
import "os"
func main() {}
''')
    imports = extract_imports(f)
    assert "fmt" in imports
    assert "os" in imports


def test_extract_imports_aliased(tmp_path):
    f = tmp_path / "aliased.go"
    f.write_text('''package main
import (
    myfmt "fmt"
    _ "os"
)
func main() {}
''')
    imports = extract_imports(f)
    assert "fmt" in imports
    assert "os" in imports


def test_extract_imports_nonexistent_file():
    imports = extract_imports(Path("/nonexistent/file.go"))
    assert imports == []


# ---------------------------------------------------------------------------
# extract_package_name
# ---------------------------------------------------------------------------

def test_extract_package_name_main(go_project):
    name = extract_package_name(go_project / "main.go")
    assert name == "main"


def test_extract_package_name_util(go_project):
    name = extract_package_name(go_project / "util" / "util.go")
    assert name == "util"


def test_extract_package_name_core(go_project):
    name = extract_package_name(go_project / "core" / "core.go")
    assert name == "core"


def test_extract_package_name_nonexistent():
    name = extract_package_name(Path("/nonexistent/file.go"))
    assert name is None


# ---------------------------------------------------------------------------
# filter_internal_imports
# ---------------------------------------------------------------------------

def test_filter_internal_imports_finds_internal():
    imports = ["fmt", "github.com/test/mymod/util", "github.com/test/mymod/core"]
    known = {"", "util", "core"}
    result = filter_internal_imports(imports, "github.com/test/mymod", known)
    assert "util" in result
    assert "core" in result


def test_filter_internal_imports_excludes_external():
    imports = ["fmt", "os", "net/http", "github.com/test/mymod/util"]
    known = {"", "util"}
    result = filter_internal_imports(imports, "github.com/test/mymod", known)
    assert "fmt" not in result
    assert "os" not in result
    assert "net/http" not in result


def test_filter_internal_imports_unknown_suffix_excluded():
    imports = ["github.com/test/mymod/unknown"]
    known = {"util", "core"}
    result = filter_internal_imports(imports, "github.com/test/mymod", known)
    assert result == []


def test_filter_internal_imports_root_package():
    imports = ["github.com/test/mymod"]
    known = {""}
    result = filter_internal_imports(imports, "github.com/test/mymod", known)
    assert "" in result


def test_filter_internal_imports_empty():
    result = filter_internal_imports([], "github.com/test/mymod", {"util"})
    assert result == []


# ---------------------------------------------------------------------------
# count_lines
# ---------------------------------------------------------------------------

def test_count_lines_basic(tmp_path):
    f = tmp_path / "test.go"
    f.write_text("line1\nline2\nline3\n")
    assert count_lines(f) == 3


def test_count_lines_nonexistent():
    assert count_lines(Path("/nonexistent/file.go")) == 0


# ---------------------------------------------------------------------------
# detect_cycles
# ---------------------------------------------------------------------------

def test_detect_cycles_simple_cycle():
    deps = {"a": ["b"], "b": ["a"], "c": []}
    cycles = detect_cycles(deps)
    assert len(cycles) == 1
    cycle = cycles[0]
    assert set(cycle) >= {"a", "b"}


def test_detect_cycles_three_node_cycle():
    deps = {"a": ["b"], "b": ["c"], "c": ["a"]}
    cycles = detect_cycles(deps)
    assert len(cycles) == 1
    assert len(cycles[0]) == 4  # a -> b -> c -> a


def test_detect_cycles_no_cycle():
    deps = {"a": ["b"], "b": ["c"], "c": []}
    assert detect_cycles(deps) == []


def test_detect_cycles_empty():
    assert detect_cycles({}) == []
    assert detect_cycles({"a": [], "b": []}) == []


def test_detect_cycles_self_loop():
    deps = {"a": ["a"]}
    cycles = detect_cycles(deps)
    assert len(cycles) == 1


def test_detect_cycles_two_independent_cycles():
    deps = {"a": ["b"], "b": ["a"], "c": ["d"], "d": ["c"]}
    cycles = detect_cycles(deps)
    assert len(cycles) == 2


# ---------------------------------------------------------------------------
# classify_architecture
# ---------------------------------------------------------------------------

def test_classify_architecture_monolith_small_n():
    assert classify_architecture(2, 1.0, 1, 0, 0.5) == "monolith"


def test_classify_architecture_monolith_n3():
    assert classify_architecture(3, 1.0, 1, 0, 0.1) == "monolith"


def test_classify_architecture_tangled():
    assert classify_architecture(10, 2.0, 5, 4, 0.2) == "tangled"


def test_classify_architecture_hub_and_spoke():
    assert classify_architecture(10, 0.5, 4, 0, 0.6) == "hub-and-spoke"


def test_classify_architecture_framework():
    assert classify_architecture(10, 3.0, 2, 0, 0.1) == "framework"


def test_classify_architecture_registry():
    # k_max > n * 0.4 and hub_pct <= 0.5
    assert classify_architecture(10, 0.5, 5, 0, 0.3) == "registry"


def test_classify_architecture_facade():
    # hub_pct > 0.3
    assert classify_architecture(10, 0.5, 2, 0, 0.4) == "facade"


def test_classify_architecture_distributed():
    assert classify_architecture(10, 0.3, 1, 0, 0.1) == "distributed"


# ---------------------------------------------------------------------------
# pkg_display_name
# ---------------------------------------------------------------------------

def test_pkg_display_name_root():
    assert pkg_display_name("") == "(root)"


def test_pkg_display_name_subpackage():
    assert pkg_display_name("util") == "util"


def test_pkg_display_name_nested():
    assert pkg_display_name("internal/store") == "internal/store"


# ---------------------------------------------------------------------------
# analyze_go_project
# ---------------------------------------------------------------------------

def test_analyze_go_project_n(go_project):
    result = analyze_go_project(go_project)
    assert "error" not in result
    assert result["n"] == 3


def test_analyze_go_project_no_cycles(go_project):
    result = analyze_go_project(go_project)
    assert result["cycles"] == 0


def test_analyze_go_project_architecture(go_project):
    result = analyze_go_project(go_project)
    # n=3 -> monolith
    assert result["architecture"] == "monolith"


def test_analyze_go_project_required_keys(go_project):
    result = analyze_go_project(go_project)
    required = {
        "project", "path", "language", "granularity",
        "n", "k_total", "k_avg", "k_n", "k_max", "k_max_pkg",
        "cycles", "cycle_details", "composite", "burden",
        "architecture", "hub_pct", "total_loc", "total_files",
        "packages", "in_degree",
    }
    assert required.issubset(result.keys())


def test_analyze_go_project_language(go_project):
    result = analyze_go_project(go_project)
    assert result["language"] == "Go"


def test_analyze_go_project_granularity(go_project):
    result = analyze_go_project(go_project)
    assert result["granularity"] == "package"


def test_analyze_go_project_module_path(go_project):
    result = analyze_go_project(go_project)
    assert result["project"] == "github.com/test/mymod"


def test_analyze_go_project_k_total(go_project):
    # main imports util and core (2 edges), core imports util (1 edge) = 3 total
    result = analyze_go_project(go_project)
    assert result["k_total"] == 3


def test_analyze_go_project_composite_formula(go_project):
    result = analyze_go_project(go_project)
    expected = round(result["k_avg"] * result["n"] + result["cycles"], 1)
    assert abs(result["composite"] - expected) < 0.05


def test_analyze_go_project_burden_formula(go_project):
    result = analyze_go_project(go_project)
    expected = round(result["cycles"] + 0.1 * result["n"], 1)
    assert abs(result["burden"] - expected) < 0.05


def test_analyze_go_project_packages_keys(go_project):
    result = analyze_go_project(go_project)
    pkg_keys = set(result["packages"].keys())
    assert "(root)" in pkg_keys
    assert "util" in pkg_keys
    assert "core" in pkg_keys


def test_analyze_go_project_error_not_a_dir():
    result = analyze_go_project(Path("/nonexistent/path/xyz"))
    assert "error" in result


def test_analyze_go_project_error_no_gomod(tmp_path):
    # Directory exists but has no go.mod
    (tmp_path / "main.go").write_text("package main\nfunc main() {}\n")
    result = analyze_go_project(tmp_path)
    assert "error" in result


def test_analyze_go_project_detects_cycles(go_project_with_cycle):
    result = analyze_go_project(go_project_with_cycle)
    assert "error" not in result
    assert result["cycles"] == 1


def test_analyze_go_project_cycle_details_nonempty(go_project_with_cycle):
    result = analyze_go_project(go_project_with_cycle)
    assert len(result["cycle_details"]) == 1
    assert "->" in result["cycle_details"][0]


def test_analyze_go_project_in_degree(go_project):
    result = analyze_go_project(go_project)
    # util is imported by both main (root) and core
    assert result["in_degree"].get("util", 0) == 2


def test_analyze_go_project_total_files(go_project):
    result = analyze_go_project(go_project)
    # 3 packages, 1 file each = 3 total files
    assert result["total_files"] == 3


def test_analyze_go_project_total_loc_positive(go_project):
    result = analyze_go_project(go_project)
    assert result["total_loc"] > 0
