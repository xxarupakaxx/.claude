"""The thin wrapper must never fail a session start when the shared script is missing."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

WRAPPER = Path(__file__).resolve().parents[1] / "scripts/lint-hook-wiring.py"


class LintHookWiringWrapperTests(unittest.TestCase):
    def run_without_shared_script(self, *args):
        with tempfile.TemporaryDirectory() as empty_home:
            return subprocess.run(
                [sys.executable, str(WRAPPER), *args],
                capture_output=True,
                text=True,
                env=dict(os.environ, HOME=empty_home),
            )

    def test_should_exit_zero_with_notice_in_hook_mode(self):
        done = self.run_without_shared_script("--hook")
        self.assertEqual(done.returncode, 0)
        self.assertTrue(done.stdout.startswith("[hook-wiring]"))

    def test_should_fail_loudly_when_run_by_hand(self):
        done = self.run_without_shared_script()
        self.assertEqual(done.returncode, 1)
        self.assertIn("missing", done.stderr)


if __name__ == "__main__":
    unittest.main()
