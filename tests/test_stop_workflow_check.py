"""Black-box contracts for the Stop hook that checks only this session's task log."""

import json
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "hooks/stop-workflow-check.sh"
CORE = Path.home() / ".codex/scripts/session_handover.py"
SESSION = "11111111-1111-4111-8111-111111111111"
OTHER = "22222222-2222-4222-8222-222222222222"
NO_LOG_REASON = "05_log.md が存在しません"
NO_PHASE3_REASON = "Phase 3（実装）の記録がありません"


class StopWorkflowCheckTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name).resolve()
        self.home = root / "claude-home"
        (self.home / ".local/memory").mkdir(parents=True)
        self.cwd = root / "project"
        self.memory = self.cwd / ".local/memory"
        self.memory.mkdir(parents=True)

    def task(self, name, session=None, log=None, base=None, newer=False):
        directory = (base or self.memory) / name
        directory.mkdir()
        if session is not None:
            meta = {
                "schema_version": 1, "task_id": name, "task_title": name,
                "session_id": session, "project_path": str(self.cwd),
                "worktree_path": str(self.cwd), "task_state": "active",
                "code_change": True, "created_at": "2026-10-22T00:00:00+09:00",
                "updated_at": "2026-10-22T00:00:00+09:00",
            }
            (directory / "task-meta.json").write_text(json.dumps(meta))
        if log is not None:
            (directory / "05_log.md").write_text(log)
        if newer:
            future = time.time() + 3600
            os.utime(directory, (future, future))
        return directory

    def run_hook(self, message, session=SESSION, active=False):
        payload = {
            "session_id": session, "cwd": str(self.cwd),
            "last_assistant_message": message, "stop_hook_active": active,
        }
        env = {
            key: value for key, value in os.environ.items()
            if key not in ("SESSION_HANDOVER_TASK_MEMORY_ROOT", "CODEX_HOME")
        }
        env.update(CLAUDE_HOME=str(self.home), SESSION_HANDOVER_CORE=str(CORE))
        result = subprocess.run(
            ["bash", str(HOOK)], input=json.dumps(payload),
            capture_output=True, text=True, env=env, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout) if result.stdout.strip() else None

    def test_blocks_when_own_task_has_no_log(self):
        own = self.task("261022_own", session=SESSION)
        self.task("261022_other", session=OTHER, log="Phase 3\nPhase 4 PASS\n", newer=True)

        decision = self.run_hook("実装完了しました")

        self.assertEqual(decision["decision"], "block")
        self.assertIn(f"{own}/05_log.md", decision["reason"])

    def test_checks_phase_record_in_own_task_not_newest_task(self):
        self.task("261022_own", session=SESSION, log="## 調査\n")
        self.task("261022_other", session=OTHER, log="Phase 3\n", newer=True)

        decision = self.run_hook("実装完了しました")

        self.assertEqual(decision["decision"], "block")
        self.assertIn(NO_PHASE3_REASON, decision["reason"])

    def test_passes_when_own_task_has_phase_record(self):
        self.task("261022_own", session=SESSION, log="## Phase 3 実装\n")
        self.task("261022_other", session=OTHER, newer=True)

        self.assertIsNone(self.run_hook("実装完了しました"))

    def test_ignores_other_session_and_legacy_tasks(self):
        self.task("261022_other", session=OTHER, newer=True)
        self.task("261022_legacy", newer=True)

        self.assertIsNone(self.run_hook("実装完了しました"))

    def test_skips_when_multiple_tasks_match(self):
        self.task("261022_own_a", session=SESSION)
        self.task("261022_own_b", session=SESSION)

        self.assertIsNone(self.run_hook("実装完了しました"))

    def test_skips_when_metadata_is_broken(self):
        broken = self.task("261022_broken", newer=True)
        (broken / "task-meta.json").write_text("{broken")

        self.assertIsNone(self.run_hook("実装完了しました"))

    def test_never_blocks_while_stop_hook_is_active(self):
        self.task("261022_own", session=SESSION)

        self.assertIsNone(self.run_hook("実装完了しました", active=True))

    def test_skips_without_session_id(self):
        self.task("261022_own", session=SESSION)

        self.assertIsNone(self.run_hook("実装完了しました", session=""))

    def test_reads_cwd_log_for_runtime_home_metadata(self):
        self.task("261022_home", session=SESSION, base=self.home / ".local/memory")

        decision = self.run_hook("実装完了しました")

        self.assertIn(NO_LOG_REASON, decision["reason"])
        self.assertIn(f"{self.memory}/261022_home/05_log.md", decision["reason"])


if __name__ == "__main__":
    unittest.main()
