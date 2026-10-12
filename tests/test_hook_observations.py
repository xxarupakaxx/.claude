"""Deterministic contracts for compact, diagnostic, and failure observations."""

import concurrent.futures
import hashlib
import importlib.util
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/hook_observations.py"
if not SCRIPT.is_file():
    SCRIPT = Path(__file__).with_name("hook_observations.py")
CODEX_ADAPTER = Path.home() / ".codex/hooks/tool-observation.py"
SPEC = importlib.util.spec_from_file_location("hook_observations_fixture", SCRIPT)
CORE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(CORE)


class HookObservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.work = self.root / "work"
        self.work.mkdir()
        (self.work / ".git").mkdir()
        self.state = self.root / "state"
        self.suggestions = self.root / "suggestions"
        self.transcripts = self.root / "projects"
        self.transcripts.mkdir()
        self.env = {
            **os.environ,
            "HOOK_OBSERVATIONS_STATE_DIR": str(self.state),
            "HOOK_OBSERVATIONS_SUGGEST_DIR": str(self.suggestions),
            "HOOK_OBSERVATIONS_TRANSCRIPT_ROOT": str(self.transcripts),
        }

    def payload(self, **values):
        result = {
            "session_id": "fixture-session",
            "cwd": str(self.work),
            "hook_event_name": "PostToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "pytest -q"},
        }
        result.update(values)
        return result

    def run_hook(self, command, payload=None, runtime="claude", env=None, timeout=10):
        prepared = dict(payload or self.payload())
        prepared.setdefault("tool_use_id", f"fixture-{uuid.uuid4()}")
        return subprocess.run(
            [sys.executable, str(SCRIPT), command, "--runtime", runtime],
            input=json.dumps(prepared),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=env or self.env,
        )

    def state_record(self, prefix):
        (path,) = self.state.glob(f"{prefix}-*.json")
        return path, json.loads(path.read_text())

    def failure(self, message="failed at 2026-10-13T12:34:56Z", **values):
        payload = self.payload(
            hook_event_name="PostToolUseFailure",
            is_error=True,
            error={"code": "TEST_FAILURE", "message": message},
        )
        payload.update(values)
        return payload

    def test_compact_is_per_session_worktree_and_keeps_50_100_proxy_thresholds(self):
        edit = self.payload(tool_name="Edit", tool_input={"file_path": str(self.work / "a.py")})
        outputs = [self.run_hook("compact", edit).stderr for _ in range(100)]
        self.assertIn('"edit_count":50', outputs[49])
        self.assertIn('"proxy":"edit_count_not_tokens"', outputs[49])
        self.assertIn('"edit_count":100', outputs[99])
        _, record = self.state_record("compact")
        self.assertEqual(record["count"], 0)
        other = {**edit, "session_id": "other-session"}
        self.run_hook("compact", other)
        self.assertEqual(len(list(self.state.glob("compact-*.json"))), 2)

    def test_invalid_identity_creates_no_state(self):
        payload = self.failure(session_id="../unsafe")
        result = self.run_hook("observe", payload)
        self.assertIn("invalid_identity", result.stderr)
        self.assertFalse(self.state.exists())

    def test_unknown_existing_format_is_preserved(self):
        self.run_hook("observe", self.failure())
        path, _ = self.state_record("failure")
        path.write_text('{"owner":"someone-else"}\n')
        before = path.read_bytes()
        result = self.run_hook("observe", self.failure())
        self.assertEqual(path.read_bytes(), before)
        self.assertIn("state_preserved", result.stderr)

    def test_state_rejects_directory_lock_and_leaf_symlinks(self):
        outside = self.root / "outside"
        outside.mkdir(mode=0o700)
        linked = self.root / "linked-state"
        linked.symlink_to(outside, target_is_directory=True)
        env = {**self.env, "HOOK_OBSERVATIONS_STATE_DIR": str(linked)}
        result = self.run_hook("observe", self.failure(), env=env)
        self.assertEqual(result.returncode, 0)
        self.assertIn("operational_error", result.stderr)
        self.assertEqual(list(outside.iterdir()), [])

        self.run_hook("observe", self.failure())
        state_path, _ = self.state_record("failure")
        before = state_path.read_bytes()
        (lock_path,) = self.state.glob(".failure-*.lock")
        lock_path.unlink()
        lock_target = self.root / "lock-target"
        lock_target.write_bytes(b"sentinel")
        lock_target.chmod(0o600)
        lock_path.symlink_to(lock_target)
        result = self.run_hook("observe", self.failure())
        self.assertIn("operational_error", result.stderr)
        self.assertEqual(lock_target.read_bytes(), b"sentinel")
        self.assertEqual(state_path.read_bytes(), before)

        lock_path.unlink()
        state_path.unlink()
        state_target = self.root / "state-target"
        state_target.write_bytes(b"sentinel")
        state_target.chmod(0o600)
        state_path.symlink_to(state_target)
        result = self.run_hook("observe", self.failure())
        self.assertIn("operational_error", result.stderr)
        self.assertEqual(state_target.read_bytes(), b"sentinel")

    def test_default_runtime_home_symlink_is_fixed_before_owned_subpath_checks(self):
        home = self.root / "home"
        home.mkdir()
        target = self.root / "codex-home"
        target.mkdir()
        (home / ".codex").symlink_to(target, target_is_directory=True)
        env = {key: value for key, value in self.env.items() if key != "HOOK_OBSERVATIONS_STATE_DIR"}
        env["HOME"] = str(home)
        payload = self.payload(tool_name="Edit", tool_use_id="codex-runtime-home")
        result = self.run_hook("compact", payload, runtime="codex", env=env)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        state_dir = target / ".local/hooks/state"
        self.assertEqual(state_dir.stat().st_mode & 0o777, 0o700)
        self.assertEqual(len(list(state_dir.glob("compact-*.json"))), 1)

    def test_state_rejects_same_owner_dirty_and_wrong_identity_records(self):
        self.run_hook("observe", self.failure())
        path, original = self.state_record("failure")

        dirty = dict(original)
        dirty["dirty"] = True
        unsealed = dict(dirty)
        unsealed.pop("content_hash")
        dirty["content_hash"] = hashlib.sha256(
            json.dumps(unsealed, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        path.write_text(json.dumps(dirty, sort_keys=True, separators=(",", ":")) + "\n")
        before = path.read_bytes()
        result = self.run_hook("observe", self.failure())
        self.assertIn("state_preserved", result.stderr)
        self.assertEqual(path.read_bytes(), before)

        wrong = dict(original)
        wrong["identity"] = {**wrong["identity"], "session": "other-session"}
        wrong["identity_digest"] = hashlib.sha256(
            json.dumps(wrong["identity"], sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        unsealed = dict(wrong)
        unsealed.pop("content_hash")
        wrong["content_hash"] = hashlib.sha256(
            json.dumps(unsealed, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        path.write_text(json.dumps(wrong, sort_keys=True, separators=(",", ":")) + "\n")
        before = path.read_bytes()
        result = self.run_hook("observe", self.failure())
        self.assertIn("state_preserved", result.stderr)
        self.assertEqual(path.read_bytes(), before)

    def test_operational_permission_lock_disappearance_and_replace_fail_open(self):
        self.state.mkdir(mode=0o700)
        self.state.chmod(0o500)
        result = self.run_hook("observe", self.failure())
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("operational_error", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.state.chmod(0o700)

        payload = self.failure(tool_use_id="in-process-event")
        for operation in ("disappearance", "replace"):
            stderr = io.StringIO()
            patches = [
                mock.patch.dict(os.environ, self.env, clear=False),
                mock.patch.object(sys, "argv", [str(SCRIPT), "observe", "--runtime", "claude"]),
                mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
                mock.patch.object(sys, "stderr", stderr),
            ]
            if operation == "disappearance":
                patches.append(mock.patch.object(CORE.OwnedJson, "_read", side_effect=[None, None, FileNotFoundError()]))
            else:
                patches.append(mock.patch.object(CORE.os, "replace", side_effect=PermissionError()))
            with patches[0], patches[1], patches[2], patches[3], patches[4]:
                self.assertEqual(CORE.main(), 0)
            self.assertIn("operational_error", stderr.getvalue())
            self.assertNotIn("Traceback", stderr.getvalue())

    def test_lock_creation_rival_uses_exclusive_create_then_existing_open(self):
        edit = self.payload(
            tool_name="Edit",
            tool_input={"file_path": str(self.work / "a.py")},
            tool_use_id="rival-create",
        )
        real_open = CORE.os.open
        lock_flags = []
        rival_created = False

        def rival_open(path, flags, mode=0o777, *, dir_fd=None):
            nonlocal rival_created
            if isinstance(path, str) and path.endswith(".lock"):
                lock_flags.append(flags)
                if flags & os.O_CREAT and flags & os.O_EXCL and not rival_created:
                    rival_created = True
                    rival = real_open(path, flags, mode, dir_fd=dir_fd)
                    os.close(rival)
                    raise FileExistsError(path)
            return real_open(path, flags, mode, dir_fd=dir_fd)

        stderr = io.StringIO()
        with (
            mock.patch.dict(os.environ, self.env, clear=False),
            mock.patch.object(CORE.os, "open", side_effect=rival_open),
            mock.patch.object(sys, "stderr", stderr),
        ):
            CORE.command_compact(edit, "claude")
        self.assertEqual(stderr.getvalue(), "")
        self.assertTrue(rival_created)
        self.assertTrue(lock_flags[0] & os.O_EXCL)
        self.assertFalse(lock_flags[1] & os.O_CREAT)
        _, record = self.state_record("compact")
        self.assertEqual(record["count"], 1)

    def test_concurrent_compact_updates_are_serialized_and_private(self):
        edit = self.payload(tool_name="Edit", tool_input={"file_path": str(self.work / "a.py")})
        deliveries = [{**edit, "tool_use_id": f"concurrent-{index}"} for index in range(24)]
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda payload: self.run_hook("compact", payload), deliveries))
        self.assertTrue(all(result.returncode == 0 for result in results))
        self.assertEqual([result.stderr for result in results if result.stderr], [])
        path, record = self.state_record("compact")
        self.assertEqual(record["count"], 24)
        self.assertEqual(self.state.stat().st_mode & 0o777, 0o700)
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_same_normalized_failure_notifies_once_at_three_without_raw_storage(self):
        messages = [
            "failed at 2026-10-13T12:34:56Z after 1.2s",
            "failed at 2027-01-01T01:02:03Z after 9.8s",
            "failed at 2028-02-02T02:03:04Z after 3.4s",
            "failed at 2029-03-03T03:04:05Z after 4.5s",
        ]
        outputs = [self.run_hook("observe", self.failure(message)).stderr for message in messages]
        self.assertNotIn("suggestion", outputs[0] + outputs[1])
        self.assertIn("same_structured_failure_three_times", outputs[2])
        self.assertNotIn("same_structured_failure_three_times", outputs[3])
        path, record = self.state_record("failure")
        serialized = path.read_text()
        self.assertEqual(record["count"], 4)
        self.assertNotIn("pytest", serialized)
        self.assertNotIn("failed at", serialized)
        self.assertNotIn("TEST_FAILURE", serialized)

    def test_duplicate_delivery_and_missing_event_id_never_advance_or_notify(self):
        duplicate = self.failure(tool_use_id="same-tool-use")
        outputs = [self.run_hook("observe", duplicate).stderr for _ in range(3)]
        self.assertTrue(all("suggestion" not in output for output in outputs))
        _, record = self.state_record("failure")
        self.assertEqual(record["count"], 1)
        before = record["content_hash"]
        missing = self.failure(tool_use_id=None)
        result = self.run_hook("observe", missing)
        self.assertIn("event_identity_unavailable", result.stderr)
        _, after = self.state_record("failure")
        self.assertEqual(after["content_hash"], before)

    def test_post_tool_use_structured_error_is_not_reset_as_success(self):
        payload = self.payload(
            hook_event_name="PostToolUse",
            tool_use_id="structured-error",
            is_error=True,
            error={"code": "TEST_FAILURE", "message": "structured failure"},
        )
        self.run_hook("observe", payload)
        _, record = self.state_record("failure")
        self.assertEqual((record["outcome"], record["count"]), ("failure", 1))

    def test_success_edit_different_cause_permission_and_interrupt_break_chains(self):
        for _ in range(2):
            self.run_hook("observe", self.failure())
        self.run_hook("observe", self.payload(hook_event_name="PostToolUse"))
        self.assertNotIn("suggestion", self.run_hook("observe", self.failure()).stderr)
        self.run_hook("observe", self.failure(message="different stable cause"))
        _, record = self.state_record("failure")
        self.assertEqual(record["count"], 1)
        permission = self.failure(error={"code": "permission_denied", "message": "not stored"})
        self.run_hook("observe", permission)
        _, record = self.state_record("failure")
        self.assertEqual(record["outcome"], "permission")
        self.run_hook("observe", self.failure())
        self.run_hook("observe", self.failure(is_interrupt=True))
        _, record = self.state_record("failure")
        self.assertEqual(record["outcome"], "interruption")
        edit = self.payload(hook_event_name="PostToolUse", tool_name="Edit")
        self.run_hook("observe", edit)
        _, record = self.state_record("failure")
        self.assertEqual(record["outcome"], "edit")

    def test_read_only_failure_is_not_counted(self):
        payload = self.failure(tool_input={"command": "git status"})
        self.run_hook("observe", payload)
        _, record = self.state_record("failure")
        self.assertEqual(record["outcome"], "read_only")
        self.assertEqual(record["count"], 0)

    def test_unknown_breaks_chain_without_becoming_success_or_notifying(self):
        for _ in range(2):
            self.run_hook("observe", self.failure())
        unknown = self.payload(hook_event_name="PostToolUseFailure", error=None, is_error=False)
        result = self.run_hook("observe", unknown)
        self.assertIn("structured_outcome_unavailable", result.stderr)
        _, record = self.state_record("failure")
        self.assertEqual(record["outcome"], "unknown")
        self.assertEqual(record["count"], 2)
        self.assertNotIn("suggestion", self.run_hook("observe", self.failure()).stderr)
        _, record = self.state_record("failure")
        self.assertEqual(record["count"], 1)

    def test_codex_string_response_is_unknown_and_never_notifies(self):
        payload = self.payload(tool_response="", tool_input={"command": "false"})
        outputs = [self.run_hook("observe", payload, runtime="codex").stderr for _ in range(4)]
        self.assertTrue(all("structured_outcome_unavailable" in output for output in outputs))
        self.assertTrue(all("suggestion" not in output for output in outputs))
        self.assertFalse(self.state.exists())

    def test_codex_native_adapter_passes_synthetic_payload_as_unknown(self):
        payload = self.payload(tool_response="", tool_input={"command": "false"}, tool_use_id="codex-tool-1")
        env = {**self.env, "HOOK_OBSERVATIONS_SCRIPT": str(SCRIPT)}
        result = subprocess.run(
            [sys.executable, str(CODEX_ADAPTER)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            env=env,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("structured_outcome_unavailable", result.stderr)
        self.assertNotIn("suggestion", result.stderr)
        self.assertFalse(self.state.exists())

    def typescript_project(self, script, linked_compiler=False):
        source = self.work / "src/example.ts"
        source.parent.mkdir()
        source.write_text("const value: string = 1;\n")
        (self.work / "tsconfig.json").write_text("{}\n")
        compiler = self.work / ("node_modules/typescript/bin/tsc" if linked_compiler else "node_modules/.bin/tsc")
        compiler.parent.mkdir(parents=True)
        compiler.write_text(script)
        compiler.chmod(compiler.stat().st_mode | stat.S_IXUSR)
        if linked_compiler:
            link = self.work / "node_modules/.bin/tsc"
            link.parent.mkdir(parents=True)
            link.symlink_to(Path("../typescript/bin/tsc"))
        return source

    def test_typescript_runs_local_compiler_once_and_reuses_captured_result(self):
        counter = self.root / "tsc-count"
        errors = "".join(f"echo 'src/a.ts({i},1): error TS100{i}: failure {i}'\n" for i in range(8))
        source = self.typescript_project(f"#!/bin/sh\necho x >> {counter!s}\n{errors}exit 2\n")
        payload = self.payload(tool_name="Edit", tool_input={"file_path": str(source)})
        result = self.run_hook("typescript", payload)
        self.assertEqual(counter.read_text(), "x\n")
        reported = json.loads(result.stderr)
        self.assertEqual(reported["run_count"], 1)
        self.assertEqual(reported["error_count"], 8)
        self.assertEqual(len(reported["first_errors"]), 5)
        self.assertNotIn("failure 7", result.stderr)

    def test_typescript_accepts_standard_internal_link_and_rejects_outside_links(self):
        counter = self.root / "linked-tsc-count"
        source = self.typescript_project(f"#!/bin/sh\necho x >> {counter!s}\nexit 0\n", linked_compiler=True)
        payload = self.payload(tool_name="Edit", tool_input={"file_path": str(source)})
        self.run_hook("typescript", payload)
        self.assertEqual(counter.read_text(), "x\n")

        outside_source = self.root / "outside.ts"
        outside_source.write_text("let outside = true;\n")
        source.unlink()
        source.symlink_to(outside_source)
        result = self.run_hook("typescript", payload)
        self.assertIn("edited_file_outside_worktree", result.stderr)
        self.assertEqual(counter.read_text(), "x\n")

        source.unlink()
        source.write_text("let inside = true;\n")
        link = self.work / "node_modules/.bin/tsc"
        link.unlink()
        outside_compiler = self.root / "outside-tsc"
        outside_compiler.write_text(f"#!/bin/sh\necho bad >> {counter!s}\n")
        outside_compiler.chmod(0o700)
        link.symlink_to(outside_compiler)
        result = self.run_hook("typescript", payload)
        self.assertIn("project_local_compiler_outside_worktree", result.stderr)
        self.assertEqual(counter.read_text(), "x\n")

    def test_typescript_missing_and_timeout_are_structured_unknown(self):
        source = self.work / "missing.ts"
        source.write_text("let x = 1;\n")
        (self.work / "tsconfig.json").write_text("{}\n")
        payload = self.payload(tool_name="Edit", tool_input={"file_path": str(source)})
        missing = json.loads(self.run_hook("typescript", payload).stderr)
        self.assertEqual((missing["status"], missing["reason"], missing["run_count"]), ("unknown", "project_local_compiler_missing", 0))
        marker = self.root / "orphan-marker"
        source = self.typescript_project(
            "#!/bin/sh\ntrap '' TERM\n(sleep 1; echo orphan > " + str(marker) + ") &\nsleep 60\n"
        )
        timeout_env = {**self.env, "HOOK_OBSERVATIONS_TSC_TIMEOUT": "0.1"}
        timed = json.loads(self.run_hook("typescript", payload, env=timeout_env).stderr)
        self.assertEqual((timed["status"], timed["reason"], timed["run_count"]), ("unknown", "timeout", 1))
        time.sleep(1.2)
        self.assertFalse(marker.exists())

    def write_metrics(self, body):
        script = self.root / "metrics.py"
        script.write_text(
            "import json,sys\n"
            "from pathlib import Path\n"
            f"Path({str(self.root / 'metrics-args')!r}).write_text(json.dumps(sys.argv[1:]))\n"
            f"print(json.dumps({body!r}))\n"
        )
        return script

    def qualified(self, transcript, session="fixture-session", measurement_status="not_qualified", **calls):
        tool_calls = {"success": 4, "failure": 2, "rejection": 0, "interruption": 0, "unknown": 0, "total": 6}
        tool_calls.update(calls)
        return {
            "measurement_status": measurement_status,
            "identity": {"session_id": session, "transcript_path": str(transcript), "matched": True},
            "coverage": {
                "tool_calls": {
                    "expected": 6, "observed": 6, "rate": 1.0,
                    "qualified": True, "reasons": [], "scope": "main",
                },
                "outcome": {
                    "expected": 6, "observed": 6, "rate": 1.0,
                    "qualified": True, "reasons": [], "scope": "main",
                },
            },
            "tool_calls": tool_calls,
        }

    def test_stop_uses_exact_identity_and_tool_only_metrics_without_invented_status(self):
        transcript = self.transcripts / "fixture-session.jsonl"
        transcript.write_text("{}\n")
        metrics = self.write_metrics(self.qualified(transcript))
        env = {**self.env, "HOOK_OBSERVATIONS_METRICS_SCRIPT": str(metrics)}
        payload = self.payload(transcript_path=str(transcript), hook_event_name="Stop")
        result = self.run_hook("stop", payload, env=env)
        self.assertEqual(result.stderr, "")
        args = json.loads((self.root / "metrics-args").read_text())
        self.assertEqual(
            args,
            [
                "metrics",
                "--transcript",
                str(transcript.resolve()),
                "--session-id",
                "fixture-session",
            ],
        )
        (suggestion,) = self.suggestions.glob("suggestion-*.json")
        record = json.loads(suggestion.read_text())
        self.assertEqual(record["tool_calls"]["failure"], 2)
        self.assertNotIn(str(transcript), suggestion.read_text())
        self.assertEqual(self.suggestions.stat().st_mode & 0o777, 0o700)
        self.assertEqual(suggestion.stat().st_mode & 0o777, 0o600)

    def test_stop_rejects_bool_zero_wrong_identity_and_transcript_symlink(self):
        transcript = self.transcripts / "fixture-session.jsonl"
        transcript.write_text("{}\n")
        cases = []
        boolean = self.qualified(transcript)
        boolean["coverage"]["tool_calls"].update({"expected": True, "observed": True})
        cases.append(boolean)
        zero = self.qualified(transcript)
        zero["coverage"]["tool_calls"].update({"expected": 0, "observed": 0})
        zero["coverage"]["outcome"].update({"expected": 0, "observed": 0})
        zero["tool_calls"] = {name: 0 for name in zero["tool_calls"]}
        cases.append(zero)
        wrong = self.qualified(transcript)
        wrong["identity"]["session_id"] = "other-session"
        cases.append(wrong)
        unqualified = self.qualified(transcript)
        unqualified["coverage"]["outcome"]["qualified"] = False
        unqualified["coverage"]["outcome"]["reasons"] = ["missing_outcomes"]
        cases.append(unqualified)
        for body in cases:
            metrics = self.write_metrics(body)
            env = {**self.env, "HOOK_OBSERVATIONS_METRICS_SCRIPT": str(metrics)}
            result = self.run_hook(
                "stop",
                self.payload(transcript_path=str(transcript), hook_event_name="Stop"),
                env=env,
            )
            self.assertIn("metrics_not_qualified", result.stderr)
            self.assertFalse(self.suggestions.exists())

        target = self.transcripts / "target.jsonl"
        target.write_text("{}\n")
        transcript.unlink()
        transcript.symlink_to(target)
        metrics = self.write_metrics(self.qualified(target))
        env = {**self.env, "HOOK_OBSERVATIONS_METRICS_SCRIPT": str(metrics)}
        result = self.run_hook(
            "stop",
            self.payload(transcript_path=str(transcript), hook_event_name="Stop"),
            env=env,
        )
        self.assertIn("transcript_identity_mismatch", result.stderr)

    def test_codex_stop_requires_official_rollout_filename_and_exact_collector_identity(self):
        session = "11111111-1111-4111-8111-111111111111"
        malformed = self.transcripts / f"other-prefix-{session}.jsonl"
        malformed.write_text("{}\n")
        metrics = self.write_metrics(self.qualified(malformed, session=session))
        env = {**self.env, "HOOK_OBSERVATIONS_METRICS_SCRIPT": str(metrics)}
        payload = self.payload(
            session_id=session,
            transcript_path=str(malformed),
            hook_event_name="Stop",
        )
        rejected = self.run_hook("stop", payload, runtime="codex", env=env)
        self.assertIn("transcript_identity_mismatch", rejected.stderr)
        self.assertFalse((self.root / "metrics-args").exists())

        transcript = self.transcripts / f"rollout-2026-10-13T01-02-03-{session}.jsonl"
        transcript.write_text("{}\n")
        metrics = self.write_metrics(self.qualified(transcript, session=session))
        payload["transcript_path"] = str(transcript)
        accepted = self.run_hook("stop", payload, runtime="codex", env=env)
        self.assertEqual(accepted.stderr, "")
        self.assertTrue(self.suggestions.exists())

    def test_stop_rejects_inexact_path_before_metrics_and_unknown_coverage_after(self):
        outside = self.root / "fixture-session.jsonl"
        outside.write_text("{}\n")
        metrics = self.write_metrics({})
        env = {**self.env, "HOOK_OBSERVATIONS_METRICS_SCRIPT": str(metrics)}
        bad = self.run_hook("stop", self.payload(transcript_path=str(outside)), env=env)
        self.assertIn("transcript_identity_mismatch", bad.stderr)
        self.assertFalse((self.root / "metrics-args").exists())
        transcript = self.transcripts / "fixture-session.jsonl"
        transcript.write_text("{}\n")
        metrics = self.write_metrics(self.qualified(transcript, unknown=1))
        unknown = self.run_hook(
            "stop",
            self.payload(transcript_path=str(transcript), hook_event_name="Stop"),
            env=env,
        )
        self.assertIn("metrics_not_qualified", unknown.stderr)
        self.assertFalse(self.suggestions.exists())


if __name__ == "__main__":
    unittest.main()
