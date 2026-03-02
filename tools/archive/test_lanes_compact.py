#!/usr/bin/env python3
"""Tests for tools/lanes_compact.py."""

import tempfile
import unittest
from pathlib import Path

try:
    from tools import lanes_compact  # type: ignore
except Exception:
    import lanes_compact  # type: ignore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HEADER = """\
# Swarm Lanes — Multi-Agent / Multi-PR / Multi-LLM / Multi-Platform
Purpose: coordinate concurrent work streams.

## Lane Log (append-only)
| Date | Lane | Session | Agent | Branch | PR | Model | Platform | Scope-Key | Etc | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
"""

def _make_row(
    date: str = "2026-02-27",
    lane: str = "L-TEST",
    session: str = "S170",
    agent: str = "codex",
    branch: str = "local",
    pr: str = "-",
    model: str = "GPT-5",
    platform: str = "codex-cli",
    scope_key: str = "tasks/NEXT.md",
    etc: str = "setup=wsl, focus=global",
    status: str = "MERGED",
    notes: str = "test row",
) -> str:
    return (
        f"| {date} | {lane} | {session} | {agent} | {branch} | {pr} | {model} | "
        f"{platform} | {scope_key} | {etc} | {status} | {notes} |\n"
    )


def _make_lanes_file(*rows: str) -> str:
    return HEADER + "".join(rows)


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------


class TestMergedOldRowsArchived(unittest.TestCase):
    """MERGED rows whose session is old enough should be archived."""

    def test_merged_old_row_is_archived(self) -> None:
        # current_session=191, age=20 → cutoff=171
        # Row is S170 MERGED → 170 <= 171 → should be archived
        old_merged = _make_row(session="S170", status="MERGED")
        recent_merged = _make_row(lane="L-RECENT", session="S185", status="MERGED")
        lanes_text = _make_lanes_file(old_merged, recent_merged)

        header, kept, archived = lanes_compact.compact(lanes_text, current_session=191, age_threshold=20)

        archived_text = "".join(archived)
        kept_text = "".join(kept)

        self.assertIn("S170", archived_text, "S170 MERGED row should be archived")
        self.assertIn("MERGED", archived_text)
        self.assertNotIn("S170", kept_text, "S170 MERGED row must not appear in kept rows")

    def test_abandoned_old_row_is_archived(self) -> None:
        # ABANDONED at S165 with current=191, age=20 → cutoff=171 → 165 <= 171
        old_abandoned = _make_row(session="S165", status="ABANDONED", lane="L-ABANDONED")
        lanes_text = _make_lanes_file(old_abandoned)

        _, kept, archived = lanes_compact.compact(lanes_text, current_session=191, age_threshold=20)

        archived_text = "".join(archived)
        self.assertIn("L-ABANDONED", archived_text)
        self.assertIn("ABANDONED", archived_text)
        self.assertNotIn("L-ABANDONED", "".join(kept))

    def test_merged_recent_row_is_kept(self) -> None:
        # S180 MERGED with current=191, age=20 → cutoff=171 → 180 > 171 → kept
        recent = _make_row(session="S180", status="MERGED", lane="L-RECENT-MERGED")
        lanes_text = _make_lanes_file(recent)

        _, kept, archived = lanes_compact.compact(lanes_text, current_session=191, age_threshold=20)

        kept_text = "".join(kept)
        self.assertIn("L-RECENT-MERGED", kept_text)
        self.assertEqual(len(archived), 0, "recent MERGED row must not be archived")

    def test_exactly_at_cutoff_is_archived(self) -> None:
        # session == cutoff (171) → should be archived (<=)
        at_cutoff = _make_row(session="S171", status="MERGED", lane="L-AT-CUTOFF")
        lanes_text = _make_lanes_file(at_cutoff)

        _, kept, archived = lanes_compact.compact(lanes_text, current_session=191, age_threshold=20)

        self.assertIn("L-AT-CUTOFF", "".join(archived))

    def test_one_above_cutoff_is_kept(self) -> None:
        # session == cutoff + 1 (172) → should be kept
        above = _make_row(session="S172", status="MERGED", lane="L-ABOVE-CUTOFF")
        lanes_text = _make_lanes_file(above)

        _, kept, archived = lanes_compact.compact(lanes_text, current_session=191, age_threshold=20)

        self.assertIn("L-ABOVE-CUTOFF", "".join(kept))
        self.assertEqual(len(archived), 0)


class TestActiveRowsNeverArchived(unittest.TestCase):
    """ACTIVE/CLAIMED/BLOCKED/READY rows must never be archived regardless of age."""

    def _assert_not_archived(self, status: str) -> None:
        old_active = _make_row(session="S100", status=status, lane=f"L-{status}")
        lanes_text = _make_lanes_file(old_active)

        _, kept, archived = lanes_compact.compact(lanes_text, current_session=191, age_threshold=20)

        self.assertEqual(
            len(archived),
            0,
            f"{status} row from S100 must not be archived even though age exceeds threshold",
        )
        self.assertIn(f"L-{status}", "".join(kept))

    def test_active_row_never_archived(self) -> None:
        self._assert_not_archived("ACTIVE")

    def test_claimed_row_never_archived(self) -> None:
        self._assert_not_archived("CLAIMED")

    def test_blocked_row_never_archived(self) -> None:
        self._assert_not_archived("BLOCKED")

    def test_ready_row_never_archived(self) -> None:
        self._assert_not_archived("READY")

    def test_mixed_old_active_and_old_merged(self) -> None:
        """Only MERGED is archived; old ACTIVE stays."""
        old_merged = _make_row(session="S100", status="MERGED", lane="L-OLD-MERGED")
        old_active = _make_row(session="S100", status="ACTIVE", lane="L-OLD-ACTIVE")
        lanes_text = _make_lanes_file(old_merged, old_active)

        _, kept, archived = lanes_compact.compact(lanes_text, current_session=191, age_threshold=20)

        archived_text = "".join(archived)
        kept_text = "".join(kept)

        self.assertIn("L-OLD-MERGED", archived_text)
        self.assertNotIn("L-OLD-ACTIVE", archived_text)
        self.assertIn("L-OLD-ACTIVE", kept_text)


class TestDryRunProducesNoWrites(unittest.TestCase):
    """--dry-run must not write any files."""

    def test_dry_run_no_file_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            lanes_path = root / "tasks" / "SWARM-LANES.md"
            archive_path = root / "tasks" / "SWARM-LANES-ARCHIVE.md"
            index_path = root / "memory" / "INDEX.md"

            lanes_path.parent.mkdir(parents=True)
            index_path.parent.mkdir(parents=True)

            # Write a lanes file with archivable rows
            old_merged = _make_row(session="S100", status="MERGED")
            lanes_path.write_text(_make_lanes_file(old_merged), encoding="utf-8")
            original_lanes = lanes_path.read_text(encoding="utf-8")

            index_path.write_text("# Memory Index\nUpdated: 2026-02-28 | Sessions: 191\n", encoding="utf-8")

            # Monkeypatch module paths to point at temp dir
            orig_lanes = lanes_compact.LANES_PATH
            orig_archive = lanes_compact.ARCHIVE_PATH
            orig_index = lanes_compact.INDEX_PATH
            try:
                lanes_compact.LANES_PATH = lanes_path
                lanes_compact.ARCHIVE_PATH = archive_path
                lanes_compact.INDEX_PATH = index_path

                exit_code = lanes_compact.main(["--dry-run"])

                self.assertEqual(exit_code, 0)
                # SWARM-LANES.md must be unchanged
                self.assertEqual(
                    lanes_path.read_text(encoding="utf-8"),
                    original_lanes,
                    "dry-run must not modify SWARM-LANES.md",
                )
                # Archive must not be created
                self.assertFalse(
                    archive_path.exists(),
                    "dry-run must not create SWARM-LANES-ARCHIVE.md",
                )
            finally:
                lanes_compact.LANES_PATH = orig_lanes
                lanes_compact.ARCHIVE_PATH = orig_archive
                lanes_compact.INDEX_PATH = orig_index

    def test_dry_run_with_nothing_to_archive(self) -> None:
        """dry-run on a lanes file with no archivable rows should also exit cleanly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            lanes_path = root / "tasks" / "SWARM-LANES.md"
            archive_path = root / "tasks" / "SWARM-LANES-ARCHIVE.md"
            index_path = root / "memory" / "INDEX.md"

            lanes_path.parent.mkdir(parents=True)
            index_path.parent.mkdir(parents=True)

            recent = _make_row(session="S190", status="MERGED")
            lanes_path.write_text(_make_lanes_file(recent), encoding="utf-8")
            original_lanes = lanes_path.read_text(encoding="utf-8")

            index_path.write_text("# Memory Index\nUpdated: 2026-02-28 | Sessions: 191\n", encoding="utf-8")

            orig_lanes = lanes_compact.LANES_PATH
            orig_archive = lanes_compact.ARCHIVE_PATH
            orig_index = lanes_compact.INDEX_PATH
            try:
                lanes_compact.LANES_PATH = lanes_path
                lanes_compact.ARCHIVE_PATH = archive_path
                lanes_compact.INDEX_PATH = index_path

                exit_code = lanes_compact.main(["--dry-run"])

                self.assertEqual(exit_code, 0)
                self.assertEqual(lanes_path.read_text(encoding="utf-8"), original_lanes)
                self.assertFalse(archive_path.exists())
            finally:
                lanes_compact.LANES_PATH = orig_lanes
                lanes_compact.ARCHIVE_PATH = orig_archive
                lanes_compact.INDEX_PATH = orig_index


class TestSessionDetection(unittest.TestCase):
    """Auto-detect current session from INDEX.md."""

    def test_detect_session_from_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = Path(tmpdir) / "INDEX.md"
            index_path.write_text(
                "# Memory Index\nUpdated: 2026-02-28 | Sessions: 189\n",
                encoding="utf-8",
            )
            session = lanes_compact.detect_current_session(index_path)
            self.assertEqual(session, 189)

    def test_detect_session_missing_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = Path(tmpdir) / "INDEX.md"
            index_path.write_text("# Memory Index\nno session number here\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                lanes_compact.detect_current_session(index_path)


class TestHeaderPreserved(unittest.TestCase):
    """The header + separator row must always be preserved in the output."""

    def test_header_and_separator_in_output(self) -> None:
        old_row = _make_row(session="S100", status="MERGED")
        lanes_text = _make_lanes_file(old_row)

        header, kept, _ = lanes_compact.compact(lanes_text, current_session=191, age_threshold=20)
        output = lanes_compact.build_lanes_output(header, kept)

        self.assertIn("| Date | Lane | Session |", output, "column header row must be present")
        self.assertIn("| --- | --- | --- |", output, "separator row must be present")


class TestArchiveOutput(unittest.TestCase):
    """Archive file gets a header on first creation; subsequent appends get only separator."""

    def test_first_creation_includes_header(self) -> None:
        rows = [_make_row(session="S100", status="MERGED")]
        append_text = lanes_compact.build_archive_append(rows, 191, "2026-02-28", archive_exists=False)
        self.assertIn("# Swarm Lanes Archive", append_text)
        self.assertIn("<!-- compacted 2026-02-28 session=191 -->", append_text)

    def test_subsequent_append_no_header(self) -> None:
        rows = [_make_row(session="S100", status="MERGED")]
        append_text = lanes_compact.build_archive_append(rows, 192, "2026-02-28", archive_exists=True)
        self.assertNotIn("# Swarm Lanes Archive", append_text)
        self.assertIn("<!-- compacted 2026-02-28 session=192 -->", append_text)


class TestFullRoundTrip(unittest.TestCase):
    """Integration: write files, run main(), verify SWARM-LANES.md and archive."""

    def test_roundtrip_archives_old_merges_keeps_active(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            lanes_path = root / "tasks" / "SWARM-LANES.md"
            archive_path = root / "tasks" / "SWARM-LANES-ARCHIVE.md"
            index_path = root / "memory" / "INDEX.md"

            lanes_path.parent.mkdir(parents=True)
            index_path.parent.mkdir(parents=True)

            old_merged = _make_row(session="S160", status="MERGED", lane="L-OLD")
            old_active = _make_row(session="S160", status="ACTIVE", lane="L-KEEP-ACTIVE")
            recent_merged = _make_row(session="S188", status="MERGED", lane="L-RECENT")

            lanes_path.write_text(_make_lanes_file(old_merged, old_active, recent_merged), encoding="utf-8")
            index_path.write_text("# Memory Index\nUpdated: 2026-02-28 | Sessions: 191\n", encoding="utf-8")

            orig_lanes = lanes_compact.LANES_PATH
            orig_archive = lanes_compact.ARCHIVE_PATH
            orig_index = lanes_compact.INDEX_PATH
            try:
                lanes_compact.LANES_PATH = lanes_path
                lanes_compact.ARCHIVE_PATH = archive_path
                lanes_compact.INDEX_PATH = index_path

                exit_code = lanes_compact.main([])

                self.assertEqual(exit_code, 0)

                updated = lanes_path.read_text(encoding="utf-8")
                archive = archive_path.read_text(encoding="utf-8")

                # Old merged gone from lanes
                self.assertNotIn("L-OLD", updated)
                # Active preserved even though old
                self.assertIn("L-KEEP-ACTIVE", updated)
                # Recent merged preserved
                self.assertIn("L-RECENT", updated)
                # Header/separator present
                self.assertIn("| Date | Lane | Session |", updated)
                self.assertIn("| --- | --- | --- |", updated)

                # Archive has the old merged row
                self.assertIn("L-OLD", archive)
                self.assertIn("# Swarm Lanes Archive", archive)
                self.assertIn("<!-- compacted", archive)

            finally:
                lanes_compact.LANES_PATH = orig_lanes
                lanes_compact.ARCHIVE_PATH = orig_archive
                lanes_compact.INDEX_PATH = orig_index


if __name__ == "__main__":
    unittest.main()
