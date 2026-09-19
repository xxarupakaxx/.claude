import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "analyze.py"
FIELDS = (
    "input_tokens",
    "uncached_input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
)


def codex_meta(session_id, version="0.1"):
    return {"type": "session_meta", "payload": {"id": session_id, "cli_version": version}}


def codex_context(model="gpt-test"):
    return {"type": "turn_context", "payload": {"model": model}}


def codex_usage(session_id, response_id, input_tokens, output_tokens,
                cached=0, cache_write=0, reasoning=0):
    usage = {
        "input_tokens": input_tokens,
        "cached_input_tokens": cached,
        "cache_write_input_tokens": cache_write,
        "output_tokens": output_tokens,
        "reasoning_output_tokens": reasoning,
        "total_tokens": input_tokens + output_tokens,
    }
    return {
        "type": "token_usage_record",
        "payload": {
            "thread_id": session_id,
            "response_id": response_id,
            "usage": usage,
        },
    }


def legacy_count(input_tokens, output_tokens, cached=0, cache_write=0):
    usage = {
        "input_tokens": input_tokens,
        "cached_input_tokens": cached,
        "cache_write_input_tokens": cache_write,
        "output_tokens": output_tokens,
    }
    return {
        "type": "event_msg",
        "payload": {"type": "token_count", "info": {"total_token_usage": usage}},
    }


def claude_message(session_id, message_id, request_id, input_tokens,
                   output_tokens, cache_read=0, cache_write=0, thinking=0):
    return {
        "sessionId": session_id,
        "requestId": request_id,
        "message": {
            "id": message_id,
            "model": "claude-test",
            "usage": {
                "input_tokens": input_tokens,
                "cache_read_input_tokens": cache_read,
                "cache_creation_input_tokens": cache_write,
                "output_tokens": output_tokens,
                "output_tokens_details": {"thinking_tokens": thinking},
            },
        },
    }


class AnalyzeCliTests(unittest.TestCase):
    def run_cli(self, *args):
        env = os.environ.copy()
        for key in ("CODEX_THREAD_ID", "CLAUDE_SESSION_ID", "CODEX_HOME", "CLAUDE_CONFIG_DIR"):
            env.pop(key, None)
        return subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, args)],
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    def report(self, *args):
        result = self.run_cli(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        return json.loads(result.stdout)

    def failure(self, *args):
        result = self.run_cli(*args)
        self.assertEqual(result.returncode, 2, result.stdout)
        return json.loads(result.stderr)

    def write_jsonl(self, directory, name, rows):
        path = Path(directory) / name
        path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n")
        return path

    def assert_tokens(self, actual, **values):
        for field in FIELDS:
            if field in values:
                self.assertEqual(actual[field], values[field], field)

    def test_codex_modern_deduplicates_and_keeps_cache_and_reasoning(self):
        session = "modern-1"
        with tempfile.TemporaryDirectory() as directory:
            rows = [
                codex_meta(session),
                codex_context(),
                codex_usage(session, "response-a", 100, 30, 40, 5, 10),
                codex_usage(session, "response-a", 100, 30, 40, 5, 10),
                codex_usage(session, "response-b", 50, 8, 20, 0, 2),
                legacy_count(150, 38, 60, 5),
            ]
            path = self.write_jsonl(directory, "run-modern-1.jsonl", rows)
            report = self.report("--provider", "codex", "--session-id", session, "--log", path)

        self.assertEqual(report["measurement_status"], "recorded")
        self.assertEqual(report["sources"][0]["transcript_name"], path.name)
        self.assertEqual(report["sources"][0]["requests_observed"], 2)
        self.assertEqual(report["sources"][0]["duplicates_removed"], 1)
        self.assert_tokens(
            report["tokens"], input_tokens=150, uncached_input_tokens=90,
            cached_input_tokens=60, cache_write_input_tokens=5,
            output_tokens=38, reasoning_output_tokens=12, total_tokens=188,
        )

    def test_legacy_cumulative_duplicate_and_reset_are_explicit(self):
        session = "legacy-1"
        with tempfile.TemporaryDirectory() as directory:
            rows = [
                codex_meta(session),
                codex_context("legacy-model"),
                legacy_count(100, 10, 20),
                legacy_count(100, 10, 20),
                legacy_count(140, 15, 30),
                legacy_count(20, 3, 5),
                legacy_count(45, 5, 10),
            ]
            path = self.write_jsonl(directory, "legacy-1.jsonl", rows)
            report = self.report("--provider", "codex", "--session-id", session, "--log", path)

        source = report["sources"][0]
        self.assertEqual(source["requests_observed"], 3)
        self.assertEqual(source["duplicates_removed"], 1)
        self.assertEqual(report["measurement_status"], "qualified")
        self.assertIn("legacy_cumulative_adapter", source["warnings"])
        self.assertIn("counter_reset_totals_are_partial", source["warnings"])
        self.assert_tokens(
            report["tokens"], input_tokens=165, uncached_input_tokens=130,
            cached_input_tokens=35, cache_write_input_tokens=0,
            output_tokens=17, reasoning_output_tokens=None, total_tokens=182,
        )

    def test_missing_counters_are_null_and_flagged(self):
        session = "missing-1"
        row = {
            "type": "token_usage_record",
            "payload": {
                "thread_id": session,
                "response_id": "partial",
                "usage": {"input_tokens": 12, "cached_input_tokens": 4,
                           "cache_write_input_tokens": 0},
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_jsonl(directory, "missing-1.jsonl", [codex_meta(session), row])
            report = self.report("--provider", "codex", "--session-id", session, "--log", path)

        self.assert_tokens(
            report["tokens"], input_tokens=12, uncached_input_tokens=8,
            cached_input_tokens=4, cache_write_input_tokens=0,
            output_tokens=None, reasoning_output_tokens=None, total_tokens=None,
        )
        self.assertIn("required_usage_fields_missing", report["sources"][0]["warnings"])
        self.assertEqual(report["measurement_status"], "qualified")

    def test_claude_deduplicates_message_and_request_and_sums_cache(self):
        session = "claude-1"
        first = claude_message(session, "msg-1", "req-1", 10, 4, 30, 5, 1)
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_jsonl(directory, "claude-1.jsonl", [
                first,
                claude_message(session, "msg-1", "req-1", 10, 4, 30, 5, 1),
                claude_message(session, "msg-2", "req-2", 2, 3, 4, 1, 2),
            ])
            report = self.report("--provider", "claude", "--session-id", session, "--log", path)

        self.assertEqual(report["sources"][0]["requests_observed"], 2)
        self.assertEqual(report["sources"][0]["duplicates_removed"], 1)
        self.assert_tokens(
            report["tokens"], input_tokens=52, uncached_input_tokens=12,
            cached_input_tokens=34, cache_write_input_tokens=6,
            output_tokens=7, reasoning_output_tokens=3, total_tokens=59,
        )

    def test_claude_usage_without_session_id_is_excluded(self):
        session = "claude-scope"
        unscoped = claude_message(session, "unscoped", "unscoped-req", 99, 9)
        unscoped.pop("sessionId")
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_jsonl(directory, "claude-scope.jsonl", [
                claude_message(session, "scoped", "scoped-req", 3, 1), unscoped,
            ])
            report = self.report("--provider", "claude", "--session-id", session, "--log", path)

        source = report["sources"][0]
        self.assertEqual(source["requests_observed"], 1)
        self.assertIn("usage_without_session_id_excluded", source["warnings"])
        self.assertEqual(report["tokens"]["input_tokens"], 3)
        self.assertEqual(report["tokens"]["output_tokens"], 1)

    def test_optional_breakdown_missing_makes_baseline_unusable(self):
        session = "partial-1"
        partial = {
            "sessionId": session,
            "requestId": "partial-req",
            "message": {"id": "partial-msg", "usage": {"input_tokens": 5, "output_tokens": 1}},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_jsonl(directory, "partial-1.jsonl", [partial])
            snapshot = Path(directory) / "partial.snapshot"
            saved = self.report("--provider", "claude", "--session-id", session,
                                "--log", path, "--save-snapshot", snapshot)
            self.assertEqual(saved["measurement_status"], "qualified")
            self.assertIn("usage_breakdown_incomplete", saved["sources"][0]["warnings"])
            error = self.failure("--provider", "claude", "--session-id", session,
                                 "--log", path, "--baseline", snapshot)

        self.assertEqual(error["error"],
                         "baseline_or_current_measurement_qualified: inspect warnings before comparison")

    def test_malformed_middle_and_incomplete_tail_are_reported_without_losing_rows(self):
        session = "tail-1"
        valid = json.dumps(codex_usage(session, "ok", 10, 2, 3, 0, 1))
        lines = [json.dumps(codex_meta(session)), valid, "{malformed-middle}", "{incomplete-tail"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tail-1.jsonl"
            path.write_text("\n".join(lines))
            report = self.report("--provider", "codex", "--session-id", session, "--log", path)

        source = report["sources"][0]
        self.assertEqual(source["requests_observed"], 1)
        self.assertIn("malformed_record", source["warnings"])
        self.assertIn("incomplete_tail", source["warnings"])
        self.assertEqual(report["measurement_status"], "qualified")
        self.assertEqual(report["tokens"]["total_tokens"], 12)

    def test_identity_and_ambiguous_discovery_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            wrong = self.write_jsonl(directory, "wrong.jsonl", [codex_meta("actual")])
            error = self.failure("--provider", "codex", "--session-id", "wanted",
                                 "--log", wrong)
            self.assertEqual(error["error"], "session_identity_mismatch")

            invalid = self.failure("--provider", "codex", "--session-id", "bad/id",
                                   "--root", directory)
            self.assertEqual(invalid["error"], "session_id_required: use the current runtime ID, never the latest log")

            self.write_jsonl(directory, "one-wanted.jsonl", [codex_meta("wanted")])
            self.write_jsonl(directory, "two-wanted.jsonl", [codex_meta("wanted")])
            ambiguous = self.failure("--provider", "codex", "--session-id", "wanted",
                                     "--root", directory)
            self.assertEqual(ambiguous["error"],
                             "session_not_unique: supply --log for the intended session")

    def test_claude_children_with_shared_session_id_are_separate_sources(self):
        session = "claude-parent"
        with tempfile.TemporaryDirectory() as directory:
            main = self.write_jsonl(directory, session + ".jsonl", [
                claude_message(session, "main-msg", "main-req", 1, 1),
            ])
            child_dir = Path(directory) / session / "subagents"
            child_dir.mkdir(parents=True)
            child = self.write_jsonl(child_dir, "child.jsonl", [
                claude_message(session, "child-msg", "child-req", 2, 1),
            ])
            report = self.report("--provider", "claude", "--session-id", session,
                                 "--log", main, "--include-children")

        self.assertEqual(report["scope"], "local_family")
        self.assertEqual(report["tokens"]["input_tokens"], 3)
        self.assertEqual(report["tokens"]["output_tokens"], 2)
        self.assertEqual(len(report["sources"]), 2)
        self.assertEqual(report["sources"][1]["transcript_name"], child.name)

    def test_foreign_codex_usage_is_excluded_without_suppressing_legacy(self):
        session = "foreign-1"
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_jsonl(directory, "foreign-1.jsonl", [
                codex_meta(session),
                legacy_count(10, 2),
                codex_usage("other-thread", "foreign", 99, 9),
            ])
            report = self.report("--provider", "codex", "--session-id", session, "--log", path)

        source = report["sources"][0]
        self.assertIn("foreign_thread_usage_excluded", source["warnings"])
        self.assertEqual(source["requests_observed"], 1)
        self.assertEqual(report["tokens"]["input_tokens"], 10)
        self.assertEqual(report["tokens"]["output_tokens"], 2)

    def test_qualified_baseline_is_refused(self):
        session = "qualified-1"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "qualified-1.jsonl"
            valid = [codex_meta(session), codex_usage(session, "one", 5, 1)]
            path.write_text("\n".join(json.dumps(row) for row in valid) + "\n{broken-tail")
            snapshot = Path(directory) / "qualified.snapshot"
            saved = self.report("--provider", "codex", "--session-id", session,
                                "--log", path, "--save-snapshot", snapshot)
            self.assertEqual(saved["measurement_status"], "qualified")
            self.write_jsonl(directory, path.name, valid)
            error = self.failure("--provider", "codex", "--session-id", session,
                                 "--log", path, "--baseline", snapshot)

        self.assertEqual(error["error"],
                         "baseline_or_current_measurement_qualified: inspect warnings before comparison")

    def test_same_session_different_transcript_cannot_compare(self):
        session = "target-1"
        with tempfile.TemporaryDirectory() as directory:
            rows = [codex_meta(session), codex_usage(session, "one", 5, 1)]
            first = self.write_jsonl(directory, "first.jsonl", rows)
            second = self.write_jsonl(directory, "second.jsonl", rows)
            snapshot = Path(directory) / "target.snapshot"
            self.report("--provider", "codex", "--session-id", session,
                        "--log", first, "--save-snapshot", snapshot)
            error = self.failure("--provider", "codex", "--session-id", session,
                                 "--log", second, "--baseline", snapshot)

        self.assertEqual(error["error"], "baseline_scope_mismatch")

    def test_duplicate_codex_child_session_ids_are_rejected(self):
        session = "parent-dupe"
        child_meta = {"type": "session_meta", "payload": {
            "id": "same-child",
            "source": {"subagent": {"thread_spawn": {"parent_thread_id": session}}},
        }}
        with tempfile.TemporaryDirectory() as directory:
            self.write_jsonl(directory, "main-parent-dupe.jsonl", [codex_meta(session)])
            self.write_jsonl(directory, "child-a.jsonl", [child_meta])
            self.write_jsonl(directory, "child-b.jsonl", [child_meta])
            error = self.failure("--provider", "codex", "--session-id", session,
                                 "--root", directory, "--include-children")

        self.assertEqual(error["error"], "child_session_not_unique: narrow --root")

    def test_children_are_opt_in_and_unrelated_sessions_stay_out(self):
        session = "parent-1"
        child = "child-1"
        with tempfile.TemporaryDirectory() as directory:
            main = self.write_jsonl(directory, "main-parent-1.jsonl", [
                codex_meta(session), codex_usage(session, "p", 10, 1),
            ])
            self.write_jsonl(directory, "child.jsonl", [
                {"type": "session_meta", "payload": {
                    "id": child,
                    "source": {"subagent": {"thread_spawn": {"parent_thread_id": session}}},
                }},
                codex_usage(child, "c", 20, 2),
            ])
            self.write_jsonl(directory, "unrelated.jsonl", [
                codex_meta("other"), codex_usage("other", "x", 100, 10),
            ])
            main_only = self.report("--provider", "codex", "--session-id", session,
                                    "--root", directory)
            family = self.report("--provider", "codex", "--session-id", session,
                                 "--root", directory, "--include-children")

        self.assertEqual(main_only["scope"], "main_only")
        self.assertEqual(main_only["tokens"]["input_tokens"], 10)
        self.assertEqual(family["scope"], "local_family")
        self.assertEqual(family["tokens"]["input_tokens"], 30)
        self.assertEqual(family["tokens"]["output_tokens"], 3)
        self.assertEqual(len(family["sources"]), 2)
        self.assertEqual(family["sources"][0]["transcript_name"], main.name)

    def test_privacy_excludes_raw_tool_output_and_identical_proxy_is_numeric(self):
        session = "privacy-1"
        secret = "TOP_SECRET_TOOL_OUTPUT_42"
        with tempfile.TemporaryDirectory() as directory:
            rows = [
                codex_meta(session),
                codex_usage(session, "usage", 1, 1),
                {"type": "response_item", "payload": {"type": "function_call",
                 "call_id": "call-a", "name": "read_file"}},
                {"type": "response_item", "payload": {"type": "function_call_output",
                 "call_id": "call-a", "output": secret}},
                {"type": "response_item", "payload": {"type": "function_call_output",
                 "call_id": "call-b", "output": "repeat"}},
                {"type": "response_item", "payload": {"type": "function_call_output",
                 "call_id": "call-c", "output": "repeat"}},
            ]
            path = self.write_jsonl(directory, "privacy-1.jsonl", rows)
            result = self.run_cli("--provider", "codex", "--session-id", session, "--log", path)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn(secret, result.stdout + result.stderr)
            report = json.loads(result.stdout)

        activity = report["sources"][0]["activity"]
        self.assertEqual(activity["tool_results"], 3)
        self.assertGreater(activity["identical_result_bytes_proxy"], 0)
        self.assertEqual(report["findings"][0]["fact"], "identical_tool_output_observed")

    def test_snapshot_reports_added_records_and_refuses_history_changes(self):
        session = "snapshot-1"
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_jsonl(directory, "snapshot-1.jsonl", [
                codex_meta(session), codex_usage(session, "old", 10, 1),
            ])
            snapshot = Path(directory) / "baseline.json"
            first = self.report("--provider", "codex", "--session-id", session,
                                "--log", path, "--save-snapshot", snapshot)
            saved = json.loads(snapshot.read_text())
            self.assertEqual(saved["measurement_status"], "recorded")
            self.assertEqual(first["measurement_status"], "recorded")

            self.write_jsonl(directory, "snapshot-1.jsonl", [
                codex_meta(session), codex_usage(session, "old", 10, 1),
                codex_usage(session, "new", 4, 2),
            ])
            added = self.report("--provider", "codex", "--session-id", session,
                                "--log", path, "--baseline", snapshot)
            self.assertEqual(added["since_baseline"]["requests_added"], 1)
            self.assert_tokens(added["since_baseline"]["tokens"], input_tokens=4,
                               uncached_input_tokens=4, cached_input_tokens=0,
                               cache_write_input_tokens=0, output_tokens=2,
                               reasoning_output_tokens=0, total_tokens=6)

            self.write_jsonl(directory, "snapshot-1.jsonl", [
                codex_meta(session), codex_usage(session, "old", 99, 1),
                codex_usage(session, "new", 4, 2),
            ])
            error = self.failure("--provider", "codex", "--session-id", session,
                                 "--log", path, "--baseline", snapshot)
            self.assertEqual(error["error"],
                             "baseline_history_changed: no reliable before_after_delta")

    def test_snapshot_scope_mismatch_and_private_no_overwrite(self):
        session = "snapshot-2"
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_jsonl(directory, "snapshot-2.jsonl", [
                codex_meta(session), codex_usage(session, "one", 5, 1),
            ])
            snapshot = Path(directory) / "baseline.json"
            self.report("--provider", "codex", "--session-id", session, "--log", path,
                        "--save-snapshot", snapshot)
            self.assertEqual(stat.S_IMODE(snapshot.stat().st_mode), 0o600)
            original = snapshot.read_bytes()
            overwrite = self.failure("--provider", "codex", "--session-id", session,
                                     "--log", path, "--save-snapshot", snapshot)
            self.assertEqual(overwrite["error"].split(":", 1)[0], "snapshot_not_written")
            self.assertEqual(snapshot.read_bytes(), original)

            mismatch = self.failure("--provider", "codex", "--session-id", session,
                                    "--log", path, "--baseline", snapshot,
                                    "--include-children")
            self.assertEqual(mismatch["error"], "baseline_scope_mismatch")


if __name__ == "__main__":
    unittest.main()
