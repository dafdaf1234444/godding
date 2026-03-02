"""NK landscape analysis for Go projects."""

__version__ = "0.1.0"

from nk_analyze_go.core import (
    analyze_go_project,
    classify_architecture,
    count_lines,
    detect_cycles,
    extract_imports,
    extract_package_name,
    filter_internal_imports,
    find_module_path,
    list_packages,
    pkg_display_name,
)

__all__ = [
    "analyze_go_project",
    "classify_architecture",
    "count_lines",
    "detect_cycles",
    "extract_imports",
    "extract_package_name",
    "filter_internal_imports",
    "find_module_path",
    "list_packages",
    "pkg_display_name",
]
