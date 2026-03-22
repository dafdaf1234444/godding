#!/usr/bin/env python3
"""foreign_orient.py — Full orientation for foreign repo swarming.

Combines substrate_detect + foreign_scope + autoresearch-style scope analysis
into a single command for foreign repo entry. Detects:
- Language, frameworks, tooling (from substrate_detect)
- Infrastructure vs editable files (from foreign_scope)
- Top-level source files (for small repos like autoresearch)
- Agent instruction files (program.md, CLAUDE.md, etc.)
- Custom metric hints from file content

Usage:
    python3 tools/foreign_orient.py /path/to/repo
"""

import json
import sys
from pathlib import Path

# Import sibling tools
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.substrate_detect import detect as substrate_detect
from tools.foreign_scope import detect_scope


CODE_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx", ".rs", ".go",
                   ".java", ".rb", ".c", ".cpp", ".h", ".cs", ".ex", ".exs"}

AGENT_FILES = ["program.md", "CLAUDE.md", "AGENTS.md", ".cursorrules",
               ".windsurfrules", "GEMINI.md", ".github/copilot-instructions.md",
               "INSTRUCTIONS.md", "PROMPT.md"]

# Patterns in file content that suggest a success metric
METRIC_HINTS = [
    ("val_bpb", "validation bits-per-byte (ML training metric)"),
    ("val_loss", "validation loss (ML training metric)"),
    ("accuracy", "accuracy metric"),
    ("f1_score", "F1 score"),
    ("assert", "test assertions"),
    ("pytest", "pytest test framework"),
    ("PASS", "pass/fail test output"),
]


def orient_foreign(repo_path: str) -> dict:
    """Full orientation for a foreign repo."""
    root = Path(repo_path).resolve()

    # Base detection
    substrate = substrate_detect(str(root))
    scope = detect_scope(str(root))

    result = {
        **substrate,
        "scope": scope,
        "top_level_source": [],
        "agent_instructions": [],
        "metric_hints": [],
    }

    # Find top-level source files (for flat repos)
    all_infra = set()
    for files in scope.get("infra", {}).values():
        all_infra.update(files)
    for p in root.iterdir():
        if p.is_file() and p.suffix in CODE_EXTENSIONS:
            rel = str(p.relative_to(root))
            if rel not in all_infra:
                result["top_level_source"].append(rel)

    # Detect agent instruction files
    for name in AGENT_FILES:
        p = root / name
        if p.exists():
            result["agent_instructions"].append(name)

    # Scan key source files for metric hints
    files_to_scan = result["top_level_source"][:5] + result.get("entry_files", [])[:3]
    for fname in files_to_scan:
        fpath = root / fname
        if fpath.exists() and fpath.is_file() and fpath.stat().st_size < 100_000:
            try:
                content = fpath.read_text(errors="ignore").lower()
                for pattern, desc in METRIC_HINTS:
                    if pattern in content and desc not in [h[1] for h in result["metric_hints"]]:
                        result["metric_hints"].append((pattern, desc))
            except (OSError, UnicodeDecodeError):
                pass

    return result


def orient_text(info: dict) -> str:
    """Human-readable orientation for foreign repo entry."""
    lines = []

    # Basic info
    lines.append(f"=== Foreign Repo Orientation ===")
    lines.append(f"Stack: {info.get('language', 'unknown')}"
                 + (f" ({', '.join(info.get('frameworks', []))})" if info.get('frameworks') else ""))

    # Editable files
    if info["top_level_source"]:
        lines.append(f"Editable source (root): {', '.join(info['top_level_source'])}")
    scope = info.get("scope", {})
    if scope.get("source_dirs"):
        lines.append(f"Source dirs: {', '.join(scope['source_dirs'])} "
                     f"(~{scope.get('editable_count', '?')} files)")
    if scope.get("test_dirs"):
        lines.append(f"Test dirs: {', '.join(scope['test_dirs'])}")

    # Infrastructure
    if scope.get("infra"):
        infra_list = []
        for cat, files in scope["infra"].items():
            infra_list.extend(files)
        lines.append(f"Infrastructure (read-only): {', '.join(infra_list[:8])}")

    # Agent instructions
    if info["agent_instructions"]:
        lines.append(f"Agent instructions: {', '.join(info['agent_instructions'])} "
                     f"<-- READ THESE FIRST, they define the research agenda")

    # Metrics
    if info["metric_hints"]:
        lines.append("Metric hints found in source:")
        for pattern, desc in info["metric_hints"][:5]:
            lines.append(f"  - '{pattern}' → {desc}")

    # Entry files
    if info.get("entry_files"):
        lines.append(f"Read first: {', '.join(info['entry_files'][:4])}")

    lines.append("")
    lines.append("Protocol: orient → identify metric → experiment loop → compress → handoff")

    return "\n".join(lines)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    info = orient_foreign(path)
    print(json.dumps(info, indent=2, default=str))
    print()
    print(orient_text(info))
