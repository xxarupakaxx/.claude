"""Black-box contracts for the launcher of the sui-memory hooks."""

import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "hooks/sui-memory-hook.sh"
BASE_PATH = "/usr/bin:/bin"


def stub(path, label):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'#!/bin/sh\necho "{label} $*"\n', encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


class SuiMemoryHookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / "home"
        self.bin = Path(self.temp.name) / "bin"
        self.home.mkdir()
        self.bin.mkdir()

    def run_hook(self, *args):
        env = {"HOME": str(self.home), "PATH": f"{self.bin}:{BASE_PATH}"}
        return subprocess.run(["bash", str(HOOK), *args], capture_output=True, text=True, env=env, input="{}")

    def test_should_run_the_module_with_the_virtualenv_python(self):
        stub(self.home / ".claude/sui-memory/.venv/bin/python", "venv")
        stub(self.bin / "uv", "uv")
        done = self.run_hook("hook_stop")
        self.assertEqual((done.returncode, done.stdout.strip()), (0, "venv -m sui_memory.hook_stop"))

    def test_should_use_uv_when_the_virtualenv_is_missing(self):
        stub(self.bin / "uv", "uv")
        done = self.run_hook("hook_session_start")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(done.stdout.strip(), f"uv run --project {self.home}/.claude/sui-memory python -m sui_memory.hook_session_start")

    def test_should_fail_visibly_when_neither_is_available(self):
        if shutil.which("uv", path=BASE_PATH):
            self.skipTest("uv is installed in the base PATH")
        done = self.run_hook("hook_stop")
        self.assertEqual(done.returncode, 1)
        self.assertIn("uv sync", done.stderr)
        self.assertEqual(done.stdout, "")

    def test_should_pass_through_the_exit_code_of_the_module(self):
        target = self.home / ".claude/sui-memory/.venv/bin/python"
        stub(target, "venv")
        target.write_text("#!/bin/sh\nexit 3\n", encoding="utf-8")
        self.assertEqual(self.run_hook("hook_stop").returncode, 3)

    def test_should_require_the_module_name(self):
        self.assertNotEqual(self.run_hook().returncode, 0)


if __name__ == "__main__":
    unittest.main()
