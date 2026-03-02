"""NK landscape analysis for Python packages."""

__version__ = "0.2.0"

from nk_analyze.core import (
    analyze_functions,
    analyze_functions_path,
    analyze_lazy_imports,
    analyze_package,
    analyze_path,
    classify_architecture,
    count_lines,
    detect_cycles,
    extract_imports,
    extract_imports_layered,
    find_package_path,
    list_modules,
)

__all__ = [
    "analyze_package",
    "analyze_path",
    "analyze_functions",
    "analyze_functions_path",
    "analyze_lazy_imports",
    "classify_architecture",
    "count_lines",
    "detect_cycles",
    "extract_imports",
    "extract_imports_layered",
    "find_package_path",
    "list_modules",
]
