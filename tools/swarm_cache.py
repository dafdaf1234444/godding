#!/usr/bin/env python3
"""swarm_cache.py — Shared caching layer for swarm tools.

Two cache types:
  1. HEAD cache: results keyed by git HEAD commit hash.
     Use for data derived entirely from committed state (git log, file contents at HEAD).
  2. File cache: results keyed by individual file content hash.
     Use for per-file computed metadata (lesson parsing, token counts).

Cache storage: workspace/cache/ (gitignored, ephemeral).
Invalidation: automatic via hash mismatch. No TTL needed — stale = wrong hash.

Usage:
    from swarm_cache import head_cache, file_cache

    # HEAD-keyed cache
    result = head_cache.get("maintenance_committed_checks")
    if result is None:
        result = run_expensive_checks()
        head_cache.set("maintenance_committed_checks", result)

    # File-keyed cache
    meta = file_cache.get(lesson_path, "domain_tags")
    if meta is None:
        meta = parse_lesson(lesson_path)
        file_cache.set(lesson_path, "domain_tags", meta)
"""

import hashlib
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = REPO_ROOT / "workspace" / "cache"


def _ensure_cache_dir():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _get_head_hash() -> str:
    """Get current HEAD commit hash (short, 12 chars)."""
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--short=12", "HEAD"],
            capture_output=True, text=True, cwd=REPO_ROOT, timeout=5,
        )
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    return ""


def _file_hash(path: Path) -> str:
    """SHA256 hash of file content (first 16 hex chars)."""
    try:
        content = path.read_bytes()
        return hashlib.sha256(content).hexdigest()[:16]
    except Exception:
        return ""


class HeadCache:
    """Cache keyed by git HEAD commit hash.

    All entries invalidate automatically when HEAD changes (new commit).
    """

    def __init__(self):
        self._head = ""
        self._data: dict = {}
        self._loaded = False

    def _cache_path(self) -> Path:
        return CACHE_DIR / "head_cache.json"

    def _load(self):
        if self._loaded:
            return
        self._head = _get_head_hash()
        if not self._head:
            self._loaded = True
            return
        try:
            _ensure_cache_dir()
            cp = self._cache_path()
            if cp.exists():
                raw = json.loads(cp.read_text())
                if raw.get("head") == self._head:
                    self._data = raw.get("data", {})
        except Exception:
            pass
        self._loaded = True

    def _save(self):
        try:
            _ensure_cache_dir()
            self._cache_path().write_text(json.dumps({
                "head": self._head,
                "data": self._data,
            }, separators=(",", ":")))
        except Exception:
            pass

    def get(self, key: str):
        """Get cached value for key at current HEAD. Returns None on miss."""
        self._load()
        return self._data.get(key)

    def set(self, key: str, value):
        """Cache value for key at current HEAD."""
        self._load()
        self._data[key] = value
        self._save()


class FileCache:
    """Cache keyed by individual file content hashes.

    Each file's cached data invalidates when the file content changes.
    Supports multiple named slots per file (e.g., "domain_tags", "citations").
    """

    def __init__(self, namespace: str = "files"):
        self._namespace = namespace
        self._data: dict = {}
        self._loaded = False

    def _cache_path(self) -> Path:
        return CACHE_DIR / f"file_cache_{self._namespace}.json"

    def _load(self):
        if self._loaded:
            return
        try:
            _ensure_cache_dir()
            cp = self._cache_path()
            if cp.exists():
                self._data = json.loads(cp.read_text())
        except Exception:
            self._data = {}
        self._loaded = True

    def _save(self):
        try:
            _ensure_cache_dir()
            self._cache_path().write_text(json.dumps(
                self._data, separators=(",", ":")))
        except Exception:
            pass

    def get(self, path: Path, slot: str = "default"):
        """Get cached value for file+slot. Returns None on miss or stale."""
        self._load()
        key = str(path)
        entry = self._data.get(key)
        if entry is None:
            return None
        current_hash = _file_hash(path)
        if not current_hash or entry.get("hash") != current_hash:
            return None
        return entry.get("slots", {}).get(slot)

    def set(self, path: Path, slot: str, value):
        """Cache value for file+slot with current file hash."""
        self._load()
        key = str(path)
        current_hash = _file_hash(path)
        if not current_hash:
            return
        entry = self._data.get(key, {})
        if entry.get("hash") != current_hash:
            # Hash changed — clear all slots for this file
            entry = {"hash": current_hash, "slots": {}}
        entry["slots"][slot] = value
        self._data[key] = entry
        self._save()

    def get_batch(self, paths: list[Path], slot: str = "default") -> dict[Path, any]:
        """Get cached values for multiple files. Returns {path: value} for hits only."""
        self._load()
        results = {}
        for path in paths:
            val = self.get(path, slot)
            if val is not None:
                results[path] = val
        return results

    def set_batch(self, entries: dict[Path, any], slot: str = "default"):
        """Cache values for multiple files at once (single write)."""
        self._load()
        for path, value in entries.items():
            key = str(path)
            current_hash = _file_hash(path)
            if not current_hash:
                continue
            entry = self._data.get(key, {})
            if entry.get("hash") != current_hash:
                entry = {"hash": current_hash, "slots": {}}
            entry["slots"][slot] = value
            self._data[key] = entry
        self._save()


# Module-level singletons
head_cache = HeadCache()
file_cache = FileCache("lessons")
