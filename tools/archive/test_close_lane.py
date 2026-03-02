"""Tests for close_lane.py merge-on-close behavior (L-340)."""
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from close_lane import count_prior_rows, remove_prior_rows, append_closure_row, LANES_FILE


def make_test_lanes(tmp_path: Path, lane_id: str, n_rows: int) -> Path:
    """Write n_rows for a given lane to a temp SWARM-LANES file."""
    f = tmp_path / "SWARM-LANES.md"
    with open(f, "w") as fh:
        fh.write("| header row placeholder |\n")
        for i in range(n_rows):
            fh.write(
                f"| 2026-02-28 | {lane_id} | S{180+i} | test | master | - | model | tool | scope |"
                f" progress=row{i} | ACTIVE | note{i} |\n"
            )
        # Another lane — should NOT be touched
        fh.write("| 2026-02-28 | OTHER-LANE | S180 | test | master | - | model | tool | scope | x | ACTIVE | y |\n")
    return f


def test_remove_prior_rows(monkeypatch, tmp_path):
    f = make_test_lanes(tmp_path, "TEST-LANE-1", 5)
    monkeypatch.setattr("close_lane.LANES_FILE", f)
    removed = remove_prior_rows("TEST-LANE-1")
    assert removed == 5, f"Expected 5 removed, got {removed}"
    assert count_prior_rows("TEST-LANE-1") == 0
    # OTHER-LANE preserved
    assert count_prior_rows("OTHER-LANE") == 1


def test_merge_on_close_default(monkeypatch, tmp_path):
    f = make_test_lanes(tmp_path, "TEST-LANE-2", 8)
    monkeypatch.setattr("close_lane.LANES_FILE", f)
    append_closure_row("TEST-LANE-2", "ABANDONED", "test close", "S301", "tester", "test-model", merge=True)
    # After merge-on-close: exactly 1 row for TEST-LANE-2 (the closure row)
    assert count_prior_rows("TEST-LANE-2") == 1, f"Expected 1, got {count_prior_rows('TEST-LANE-2')}"
    # OTHER-LANE still there
    assert count_prior_rows("OTHER-LANE") == 1


def test_no_merge_preserves_rows(monkeypatch, tmp_path):
    f = make_test_lanes(tmp_path, "TEST-LANE-3", 4)
    monkeypatch.setattr("close_lane.LANES_FILE", f)
    append_closure_row("TEST-LANE-3", "MERGED", "no-merge test", "S301", "tester", "test-model", merge=False)
    # With --no-merge: prior 4 rows + 1 closure = 5
    assert count_prior_rows("TEST-LANE-3") == 5, f"Expected 5, got {count_prior_rows('TEST-LANE-3')}"


def test_closure_row_has_correct_status(monkeypatch, tmp_path):
    f = make_test_lanes(tmp_path, "TEST-LANE-4", 3)
    monkeypatch.setattr("close_lane.LANES_FILE", f)
    append_closure_row("TEST-LANE-4", "MERGED", "done note", "S301", "tester", "test-model", merge=True)
    with open(f) as fh:
        content = fh.read()
    assert "| MERGED |" in content
    assert "done note" in content


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
