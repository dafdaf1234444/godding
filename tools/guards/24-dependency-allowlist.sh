#!/bin/bash
# Dependency allowlist guard (L-601 structural enforcement)
# Ensures new external (non-stdlib) imports are intentional, not accidental.
# Allowlist: numpy, scipy (F-SP8 numerical tools only)

ALLOWLIST="numpy|scipy"

# Only check staged .py files in tools/
STAGED_PY=$(git diff --cached --name-only 2>/dev/null | { grep '^tools/.*\.py$' || true; })
if [ -z "$STAGED_PY" ]; then
    echo "  Dependency allowlist: SKIP (no staged tools)"
    exit 0
fi

VIOLATIONS=0
while IFS= read -r pyfile; do
    [ -f "$pyfile" ] || continue
    # Parse imports structurally so sibling tools/*.py modules count as local.
    EXTERN=$("${PYTHON_CMD[@]}" - "$pyfile" "$REPO_ROOT" "$ALLOWLIST" <<'PY'
import ast
import pathlib
import re
import sys

pyfile = pathlib.Path(sys.argv[1])
repo_root = pathlib.Path(sys.argv[2])
allowlist = {item for item in sys.argv[3].split("|") if item}
lines = pyfile.read_text(encoding="utf-8", errors="replace").splitlines()

stdlib = set(getattr(sys, "stdlib_module_names", set()))
stdlib.update({
    "__future__",
})
local_modules = {p.stem for p in (repo_root / "tools").glob("*.py")}
local_modules.update({p.stem for p in repo_root.glob("*.py")})
local_modules.update({"lesson_header", "compact_core", "lesson_meta", "tools"})

def is_allowed(module: str) -> bool:
    if not module:
        return True
    root = module.split(".", 1)[0]
    return (
        root in stdlib
        or root in allowlist
        or root in local_modules
        or root.startswith("swarm_")
    )

try:
    tree = ast.parse("\n".join(lines), filename=str(pyfile))
except SyntaxError as exc:
    print(f"{exc.lineno}:syntax-error: {exc.msg}")
    raise SystemExit(0)

violations: list[str] = []
seen: set[tuple[int, str]] = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        modules = [alias.name for alias in node.names]
    elif isinstance(node, ast.ImportFrom):
        if node.level:
            continue
        modules = [node.module or ""]
    else:
        continue

    for module in modules:
        if is_allowed(module):
            continue
        key = (node.lineno, module)
        if key in seen:
            continue
        seen.add(key)
        source = lines[node.lineno - 1] if 0 < node.lineno <= len(lines) else module
        violations.append(f"{node.lineno}:{source}")

print("\n".join(violations))
PY
)
    if [ -n "$EXTERN" ]; then
        echo "  FAIL: ${pyfile} has non-allowlisted imports:"
        echo "$EXTERN" | sed 's/^/    /'
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
done <<< "$STAGED_PY"

if [ "$VIOLATIONS" -gt 0 ]; then
    echo "  Dependency allowlist: FAIL — ${VIOLATIONS} file(s) with unapproved external imports"
    echo "  To add a new dep: update ALLOWLIST in tools/guards/24-dependency-allowlist.sh + requirements.txt"
    exit 1
else
    echo "  Dependency allowlist: PASS"
fi
