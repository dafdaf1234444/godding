"""Tests for nk_analyze.core — module-level NK analysis."""
import pytest
from nk_analyze.core import (
    analyze_functions,
    analyze_functions_path,
    analyze_lazy_imports,
    analyze_package,
    classify_architecture,
    detect_cycles,
    find_package_path,
    list_modules,
)


# ---------------------------------------------------------------------------
# find_package_path
# ---------------------------------------------------------------------------

def test_find_package_path_existing():
    path = find_package_path("json")
    assert path is not None
    assert path.is_dir()


def test_find_package_path_missing():
    assert find_package_path("_nonexistent_package_xyz_") is None


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
    assert len(cycles[0]) == 4  # a → b → c → a


def test_detect_cycles_no_cycles():
    deps = {"a": ["b"], "b": ["c"], "c": []}
    assert detect_cycles(deps) == []


def test_detect_cycles_self_loop():
    deps = {"a": ["a"]}
    cycles = detect_cycles(deps)
    assert len(cycles) == 1


def test_detect_cycles_empty():
    assert detect_cycles({}) == []
    assert detect_cycles({"a": [], "b": []}) == []


# ---------------------------------------------------------------------------
# classify_architecture
# ---------------------------------------------------------------------------

def test_classify_architecture_monolith():
    # n <= 3 → monolith
    assert classify_architecture(2, 1.0, 1, 0, 0.5) == "monolith"


def test_classify_architecture_tangled():
    # cycles > 3
    assert classify_architecture(10, 2.0, 5, 4, 0.2) == "tangled"


def test_classify_architecture_hub_and_spoke():
    assert classify_architecture(10, 0.5, 4, 0, 0.6) == "hub-and-spoke"


def test_classify_architecture_framework():
    assert classify_architecture(10, 3.0, 2, 0, 0.1) == "framework"


def test_classify_architecture_distributed():
    # No dominant pattern
    assert classify_architecture(10, 0.3, 1, 0, 0.1) == "distributed"


# ---------------------------------------------------------------------------
# analyze_package — known packages
# ---------------------------------------------------------------------------

def test_analyze_json_n():
    r = analyze_package("json")
    assert "error" not in r
    assert r["n"] == 5


def test_analyze_json_cycles():
    r = analyze_package("json")
    assert r["cycles"] == 0


def test_analyze_json_architecture():
    r = analyze_package("json")
    assert r["architecture"] == "hub-and-spoke"


def test_analyze_json_k_avg():
    r = analyze_package("json")
    # json: __init__ → {decoder, encoder}, decoder → scanner = 3 edges / 5 modules = 0.6
    assert abs(r["k_avg"] - 0.6) < 0.05


def test_analyze_json_keys():
    r = analyze_package("json")
    required = {"package", "path", "n", "k_total", "k_avg", "k_n", "k_max",
                "cycles", "cycle_details", "composite", "architecture",
                "total_loc", "modules"}
    assert required.issubset(r.keys())


def test_analyze_logging_n():
    r = analyze_package("logging")
    assert "error" not in r
    assert r["n"] >= 3  # __init__, handlers, config at minimum


def test_analyze_missing_package():
    r = analyze_package("_nonexistent_xyz_")
    assert "error" in r


def test_analyze_composite_formula():
    """composite = k_avg * n + cycles"""
    r = analyze_package("json")
    expected = round(r["k_avg"] * r["n"] + r["cycles"], 2)
    assert abs(r["composite"] - expected) < 0.05


# ---------------------------------------------------------------------------
# analyze_lazy_imports
# ---------------------------------------------------------------------------

def test_analyze_lazy_imports_json():
    r = analyze_lazy_imports("json")
    assert "error" not in r
    assert "static_cycles" in r
    assert "runtime_cycles" in r
    assert isinstance(r["static_cycles"], int)
    assert isinstance(r["runtime_cycles"], int)
    assert r["static_cycles"] >= 0
    assert "lazy_imports" in r


def test_analyze_lazy_imports_missing():
    r = analyze_lazy_imports("_nonexistent_xyz_")
    assert "error" in r


# ---------------------------------------------------------------------------
# list_modules
# ---------------------------------------------------------------------------

def test_list_modules_json():
    from pathlib import Path
    path = find_package_path("json")
    assert path is not None
    mods = list_modules(path)
    assert "decoder" in mods
    assert "encoder" in mods
    assert len(mods) >= 4


# ---------------------------------------------------------------------------
# analyze_functions — function-level NK analysis
# ---------------------------------------------------------------------------

def test_analyze_functions_json_no_error():
    r = analyze_functions("json")
    assert "error" not in r


def test_analyze_functions_json_keys():
    """Result dict must contain all required keys."""
    r = analyze_functions("json")
    required = {
        "package", "path", "n", "k_total", "k_avg", "k_max",
        "k_max_func", "cycles", "cycle_details", "top_callers", "top_called",
    }
    assert required.issubset(r.keys())


def test_analyze_functions_json_n_positive():
    """json has many functions — N must be substantially larger than module count."""
    r = analyze_functions("json")
    # json has 5 modules; function count should be much higher (>20)
    assert r["n"] > 20


def test_analyze_functions_json_n_larger_than_module_n():
    """Function N must exceed module N — verifying additive granularity."""
    mod_r = analyze_package("json")
    func_r = analyze_functions("json")
    assert func_r["n"] > mod_r["n"]


def test_analyze_functions_json_types():
    """All numeric fields must have correct types."""
    r = analyze_functions("json")
    assert isinstance(r["n"], int)
    assert isinstance(r["k_total"], int)
    assert isinstance(r["k_avg"], float)
    assert isinstance(r["k_max"], int)
    assert isinstance(r["cycles"], int)


def test_analyze_functions_json_k_avg_nonneg():
    r = analyze_functions("json")
    assert r["k_avg"] >= 0.0
    assert r["k_max"] >= 0


def test_analyze_functions_json_top_callers_structure():
    """top_callers must be a list of dicts with func and k_out keys."""
    r = analyze_functions("json")
    assert isinstance(r["top_callers"], list)
    for item in r["top_callers"]:
        assert "func" in item
        assert "k_out" in item
        assert isinstance(item["k_out"], int)
        assert item["k_out"] >= 0


def test_analyze_functions_json_top_called_structure():
    """top_called must be a list of dicts with func and k_in keys."""
    r = analyze_functions("json")
    assert isinstance(r["top_called"], list)
    for item in r["top_called"]:
        assert "func" in item
        assert "k_in" in item
        assert isinstance(item["k_in"], int)
        assert item["k_in"] >= 0


def test_analyze_functions_json_top_callers_sorted():
    """top_callers must be sorted descending by k_out."""
    r = analyze_functions("json")
    k_outs = [item["k_out"] for item in r["top_callers"]]
    assert k_outs == sorted(k_outs, reverse=True)


def test_analyze_functions_logging_no_error():
    r = analyze_functions("logging")
    assert "error" not in r


def test_analyze_functions_logging_n_positive():
    r = analyze_functions("logging")
    assert r["n"] > 10


def test_analyze_functions_missing_package():
    r = analyze_functions("_nonexistent_xyz_")
    assert "error" in r


def test_analyze_functions_package_field():
    r = analyze_functions("json")
    assert r["package"] == "json"


def test_analyze_functions_k_avg_equals_k_total_over_n():
    """k_avg must equal k_total / n (within rounding)."""
    r = analyze_functions("json")
    if r["n"] > 0:
        expected = round(r["k_total"] / r["n"], 3)
        assert abs(r["k_avg"] - expected) < 0.001


def test_analyze_functions_path_json():
    """analyze_functions_path must give same result as analyze_functions for json."""
    path = find_package_path("json")
    assert path is not None
    r_path = analyze_functions_path(path, "json")
    r_pkg = analyze_functions("json")
    assert "error" not in r_path
    assert r_path["n"] == r_pkg["n"]
    assert r_path["k_total"] == r_pkg["k_total"]


def test_analyze_functions_path_missing_dir():
    from pathlib import Path
    r = analyze_functions_path(Path("/nonexistent/path/xyz"), "whatever")
    assert "error" in r
