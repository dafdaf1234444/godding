"""
substrate_detect.py — Detect repo type from indicator files.
Used by /swarm to orient in foreign repos without assuming swarm structure.

Usage:
    python3 tools/substrate_detect.py [path]
    from tools.substrate_detect import detect  # returns SubstrateInfo dict
"""

import json
import os
import sys
from pathlib import Path


# Ordered: first match wins for primary language detection
LANGUAGE_INDICATORS = [
    # Language + ecosystem
    ("rust",       ["Cargo.toml"]),
    ("go",         ["go.mod"]),
    ("python",     ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "Pipfile", "uv.lock", "poetry.lock"]),
    ("javascript", ["package.json"]),
    ("ruby",       ["Gemfile"]),
    ("java",       ["pom.xml", "build.gradle", "build.gradle.kts"]),
    ("kotlin",     ["build.gradle.kts"]),
    ("scala",      ["build.sbt"]),
    ("dotnet",     ["*.csproj", "*.sln"]),
    ("php",        ["composer.json"]),
    ("dart",       ["pubspec.yaml"]),
    ("elixir",     ["mix.exs"]),
    ("haskell",    ["*.cabal", "stack.yaml"]),
    ("c",          ["CMakeLists.txt", "configure.ac", "meson.build"]),
]

# Framework indicators within a language
FRAMEWORK_INDICATORS = {
    "python":     [("django", ["manage.py"]),
                   ("fastapi", ["main.py"]),           # heuristic
                   ("flask",   []),
                   ("pytest",  ["pytest.ini", "conftest.py"])],
    "javascript": [("react",   ["src/App.jsx", "src/App.tsx", "src/App.js"]),
                   ("nextjs",  ["next.config.js", "next.config.mjs", "next.config.ts"]),
                   ("vue",     ["vue.config.js"]),
                   ("angular", ["angular.json"]),
                   ("svelte",  ["svelte.config.js"]),
                   ("express", []),
                   ("jest",    ["jest.config.js", "jest.config.ts"])],
    "rust":       [("tokio",   []),
                   ("axum",    []),
                   ("wasm",    ["wasm-pack.toml"])],
}

# Tooling indicators (CI, containerization, docs, etc.)
TOOLING_INDICATORS = [
    ("ci_github",   [".github/workflows"]),
    ("ci_gitlab",   [".gitlab-ci.yml"]),
    ("ci_circleci", [".circleci/config.yml"]),
    ("docker",      ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"]),
    ("make",        ["Makefile"]),
    ("nix",         ["flake.nix", "shell.nix", "default.nix"]),
    ("devcontainer", [".devcontainer"]),
    ("terraform",   ["*.tf", "terraform.tfvars"]),
    ("kubernetes",  ["k8s", "helm"]),
]

# Swarm/AI tool indicators — detect swarm context
SWARM_INDICATORS = [
    ("swarm",      ["SWARM.md", "beliefs/PHILOSOPHY.md"]),
    ("claude",     ["CLAUDE.md", ".claude"]),
    ("codex",      ["AGENTS.md"]),
    ("cursor",     [".cursorrules"]),
    ("copilot",    [".github/copilot-instructions.md"]),
    ("windsurf",   [".windsurfrules"]),
    ("gemini",     ["GEMINI.md"]),
]

# Key entry files to read when orienting in a foreign repo (per language)
ENTRY_FILES = {
    "rust":       ["README.md", "Cargo.toml", "src/main.rs", "src/lib.rs"],
    "go":         ["README.md", "go.mod", "main.go"],
    "python":     ["README.md", "pyproject.toml", "setup.py", "requirements.txt", "src/"],
    "javascript": ["README.md", "package.json", "src/index.js", "src/index.ts", "index.js"],
    "ruby":       ["README.md", "Gemfile", "lib/"],
    "java":       ["README.md", "pom.xml", "build.gradle"],
    "dotnet":     ["README.md", "*.csproj"],
    "php":        ["README.md", "composer.json"],
    "dart":       ["README.md", "pubspec.yaml"],
    "elixir":     ["README.md", "mix.exs"],
    "c":          ["README.md", "CMakeLists.txt"],
    "_default":   ["README.md", "docs/", "CONTRIBUTING.md"],
}


def _glob_match(root: Path, pattern: str) -> bool:
    """Check if any file matching pattern exists under root."""
    if "*" in pattern:
        return any(True for _ in root.glob(pattern))
    p = root / pattern
    return p.exists()


def detect(repo_path: str = ".") -> dict:
    """
    Detect substrate of a repo. Returns:
    {
        "is_swarm": bool,
        "swarm_tools": [str],       # which AI tools are present
        "language": str | None,
        "frameworks": [str],
        "tooling": [str],
        "entry_files": [str],       # files to read first when orienting
        "summary": str,             # one-line description
    }
    """
    root = Path(repo_path).resolve()
    result = {
        "is_swarm": False,
        "swarm_tools": [],
        "language": None,
        "frameworks": [],
        "tooling": [],
        "entry_files": [],
        "summary": "unknown",
    }

    # Check swarm/AI tool indicators
    for name, indicators in SWARM_INDICATORS:
        if any(_glob_match(root, ind) for ind in indicators):
            result["swarm_tools"].append(name)
    result["is_swarm"] = "swarm" in result["swarm_tools"]

    # Detect primary language (first match wins)
    for lang, indicators in LANGUAGE_INDICATORS:
        if any(_glob_match(root, ind) for ind in indicators):
            result["language"] = lang
            break

    # Detect frameworks for detected language
    lang = result["language"]
    if lang and lang in FRAMEWORK_INDICATORS:
        for fw, indicators in FRAMEWORK_INDICATORS[lang]:
            if not indicators or any(_glob_match(root, ind) for ind in indicators):
                # For frameworks with no indicators, skip auto-detect (require explicit indicators)
                if indicators:
                    result["frameworks"].append(fw)

    # Detect tooling
    for name, indicators in TOOLING_INDICATORS:
        if any(_glob_match(root, ind) for ind in indicators):
            result["tooling"].append(name)

    # Entry files to read for orientation
    entry_patterns = ENTRY_FILES.get(lang or "_default", ENTRY_FILES["_default"])
    for pattern in entry_patterns:
        p = root / pattern
        if p.exists():
            result["entry_files"].append(str(p.relative_to(root)))

    # Build summary
    parts = []
    if result["is_swarm"]:
        tools_str = "+".join(t for t in result["swarm_tools"] if t != "swarm")
        parts.append(f"swarm-repo" + (f" ({tools_str})" if tools_str else ""))
    if lang:
        fw_str = "+".join(result["frameworks"])
        parts.append(lang + (f"/{fw_str}" if fw_str else ""))
    if result["tooling"]:
        parts.append(",".join(result["tooling"]))
    result["summary"] = " | ".join(parts) if parts else "foreign repo (unrecognized)"

    return result


def orient_text(info: dict) -> str:
    """
    Return a short orientation paragraph for a node entering this repo.
    Used in /swarm foreign-repo path.
    """
    if info["is_swarm"]:
        return "Swarm repo detected. Follow full swarm protocol."

    lines = [f"Foreign repo — {info['summary']}."]

    if info["language"]:
        lines.append(f"Primary stack: {info['language']}"
                     + (f" ({', '.join(info['frameworks'])})" if info["frameworks"] else "") + ".")

    if info["entry_files"]:
        lines.append("Read first: " + ", ".join(f"`{f}`" for f in info["entry_files"][:4]) + ".")

    if info["tooling"]:
        lines.append("Tooling present: " + ", ".join(info["tooling"]) + ".")

    lines.append("No swarm infrastructure — behavioral norms only. Contribute, don't corrupt.")
    return " ".join(lines)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    info = detect(path)
    print(json.dumps(info, indent=2))
    print()
    print("--- Orientation ---")
    print(orient_text(info))
