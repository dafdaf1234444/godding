import tempfile
import unittest
from pathlib import Path

import science_quality


class ScienceQualitySessionSourceTest(unittest.TestCase):
    def test_current_session_prefers_shared_helper(self):
        original_shared = science_quality._shared_session_number
        try:
            science_quality._shared_session_number = lambda: 612
            self.assertEqual(science_quality._current_session(), 612)
        finally:
            science_quality._shared_session_number = original_shared

    def test_current_session_falls_back_to_session_log(self):
        original_root = science_quality.REPO_ROOT
        original_shared = science_quality._shared_session_number
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir)
                session_log = root / "memory" / "SESSION-LOG.md"
                session_log.parent.mkdir(parents=True)
                session_log.write_text("S530 | old\nS538 | current\n", encoding="utf-8")

                science_quality.REPO_ROOT = root
                science_quality._shared_session_number = None

                self.assertEqual(science_quality._current_session(), 538)
        finally:
            science_quality.REPO_ROOT = original_root
            science_quality._shared_session_number = original_shared


if __name__ == "__main__":
    unittest.main()
