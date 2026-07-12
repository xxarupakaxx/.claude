import importlib.util
import io
import json
from http.client import HTTPConnection
from datetime import datetime, timezone
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest import mock


SCRIPT = Path(__file__).parents[1] / "scripts" / "roadmap_task_hub.py"
SPEC = importlib.util.spec_from_file_location("roadmap_task_hub", SCRIPT)
hub = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = hub
SPEC.loader.exec_module(hub)


class FakeProcess:
    def __init__(self, responses):
        self.stdin = io.StringIO()
        self.stdout = io.StringIO(
            "".join(json.dumps(response) + "\n" for response in responses)
        )


class CodexAppServerProviderTest(unittest.TestCase):
    def test_provider_initializes_and_paginates(self):
        process = FakeProcess([
            {"id": 1, "result": {"codexHome": "/tmp/.codex", "platformFamily": "unix", "platformOs": "macos", "userAgent": "test"}},
            {"id": 2, "result": {"data": [{"id": "t1", "name": "設計", "preview": "", "cwd": "/repo", "status": {"type": "active"}, "createdAt": 10, "updatedAt": 20}], "nextCursor": "next"}},
            {"id": 3, "result": {"data": [{"id": "t2", "name": None, "preview": "実装", "cwd": "/repo", "status": {"type": "idle"}, "createdAt": 11, "updatedAt": 21}], "nextCursor": None}},
        ])
        result = hub.CodexAppServerProvider(
            process_factory=lambda: process
        ).list_threads()
        self.assertEqual([item.id for item in result.threads], ["t1", "t2"])
        self.assertEqual([item.title for item in result.threads], ["設計", "実装"])
        messages = [json.loads(line) for line in process.stdin.getvalue().splitlines()]
        self.assertEqual(
            [message["method"] for message in messages],
            ["initialize", "initialized", "thread/list", "thread/list"],
        )
        self.assertEqual(messages[2]["params"]["limit"], 100)
        self.assertEqual(messages[2]["params"]["sortKey"], "updated_at")
        self.assertEqual(messages[3]["params"]["cursor"], "next")

    def test_safe_provider_snapshot_exposes_failure(self):
        provider = hub.CodexAppServerProvider(
            process_factory=lambda: (_ for _ in ()).throw(OSError("missing codex"))
        )
        result = hub.safe_provider_snapshot(provider)
        self.assertFalse(result.connected)
        self.assertIn("missing codex", result.error or "")

    def test_provider_skips_notifications_and_exposes_json_rpc_error(self):
        process = FakeProcess([
            {"method": "server/notification", "params": {}},
            {"id": 1, "result": {}},
            {"method": "thread/updated", "params": {}},
            {"id": 2, "error": {"code": -32603, "message": "failed"}},
        ])
        provider = hub.CodexAppServerProvider(process_factory=lambda: process)
        with self.assertRaisesRegex(hub.ProviderError, "failed"):
            provider.list_threads()

    def test_provider_keeps_app_server_session_path_for_live_activity(self):
        thread = hub.CodexAppServerProvider._to_thread({
            "id": "t1", "name": "Live", "cwd": "/repo",
            "status": {"type": "active"}, "createdAt": 10, "updatedAt": 20,
            "path": "/tmp/session.jsonl",
        })
        self.assertEqual(thread.session_path, "/tmp/session.jsonl")


class SessionActivityTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary_directory.name) / "session.jsonl"

    def tearDown(self):
        self.temporary_directory.cleanup()

    def write_events(self, events):
        self.path.write_text("".join(json.dumps(event) + "\n" for event in events))

    def test_reads_only_recent_live_signals_without_exposing_arguments_or_outputs(self):
        self.write_events([
            {"timestamp": "2026-07-12T08:00:00Z", "type": "event_msg", "payload": {"type": "task_started", "started_at": 1783843200, "turn_id": "turn-1"}},
            {"timestamp": "2026-07-12T08:00:01Z", "type": "response_item", "payload": {"type": "agent_message", "phase": "commentary", "message": "Live activityを実装しています", "author": "assistant"}},
            {"timestamp": "2026-07-12T08:00:02Z", "type": "response_item", "payload": {"type": "function_call", "call_id": "call-1", "name": "exec_command", "namespace": "functions", "arguments": "SECRET-COMMAND"}},
            {"timestamp": "2026-07-12T08:00:03Z", "type": "event_msg", "payload": {"type": "sub_agent_activity", "kind": "started", "agent_thread_id": "agent-1", "agent_path": "/root/worker"}},
        ])
        activity = hub.read_session_activity(
            self.path, now=datetime(2026, 7, 12, 8, 1, tzinfo=timezone.utc)
        )
        self.assertEqual(activity["turnState"], "running")
        self.assertEqual(activity["currentAction"], "Live activityを実装しています")
        self.assertEqual(activity["runningTools"][0]["name"], "functions.exec_command")
        self.assertEqual(activity["activeSubagentCount"], 1)
        self.assertNotIn("SECRET-COMMAND", json.dumps(activity))

    def test_completed_turn_is_user_waiting_and_keeps_recent_completion(self):
        self.write_events([
            {"timestamp": "2026-07-12T08:00:00Z", "type": "event_msg", "payload": {"type": "task_started", "started_at": 1783843200, "turn_id": "turn-1"}},
            {"timestamp": "2026-07-12T08:02:00Z", "type": "event_msg", "payload": {"type": "task_complete", "completed_at": 1783843320, "duration_ms": 120000, "last_agent_message": "実装が完了しました", "turn_id": "turn-1"}},
        ])
        activity = hub.read_session_activity(
            self.path, now=datetime(2026, 7, 12, 8, 3, tzinfo=timezone.utc)
        )
        self.assertEqual(activity["turnState"], "user_waiting")
        self.assertEqual(activity["lastCompleted"], "実装が完了しました")
        self.assertEqual(activity["activeSubagentCount"], 0)
        self.assertEqual(activity["elapsedSeconds"], 120)

    def test_explicit_blocked_message_sets_blocker(self):
        self.write_events([
            {"timestamp": "2026-07-12T08:00:00Z", "type": "event_msg", "payload": {"type": "task_started", "started_at": 1783843200, "turn_id": "turn-1"}},
            {"timestamp": "2026-07-12T08:00:01Z", "type": "response_item", "payload": {"type": "agent_message", "phase": "commentary", "message": "BLOCKED: API権限がありません", "author": "assistant"}},
        ])
        activity = hub.read_session_activity(
            self.path, now=datetime(2026, 7, 12, 8, 1, tzinfo=timezone.utc)
        )
        self.assertEqual(activity["turnState"], "blocked")
        self.assertEqual(activity["blocker"], "API権限がありません")


class MemoryDiscoveryTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_discovers_roots_and_exact_thread_id_wins(self):
        alpha = self.root / "one/memory/alpha"
        beta = self.root / "two/memory/beta"
        alpha.mkdir(parents=True)
        beta.mkdir(parents=True)
        (alpha / "00_spec.md").write_text("# Alpha\n")
        (alpha / "task-meta.json").write_text(
            '{"thread_id":"t1","project_path":"/repo"}'
        )
        (beta / "30_plan.md").write_text("# Beta\n")

        memories = hub.discover_memory_tasks([alpha.parent, beta.parent])
        thread = hub.CodexThread("t1", "Alpha", "/repo", "active", 0, 0)
        match = hub.match_thread_to_memory(thread, memories)

        self.assertEqual(match.confirmed.path, alpha)

    def test_heuristic_match_is_never_confirmed(self):
        task_dir = self.root / "memory/design"
        task_dir.mkdir(parents=True)
        (task_dir / "00_spec.md").write_text("# 設計\n")
        (task_dir / "task-meta.json").write_text(
            '{"project_path":"/repo","task_title":"設計"}'
        )
        memory = hub.discover_memory_tasks([task_dir.parent])[0]

        result = hub.match_thread_to_memory(
            hub.CodexThread("t2", "設計", "/repo", "active", 0, 0), [memory]
        )

        self.assertIsNone(result.confirmed)
        self.assertEqual(result.candidates[0].path, memory.path)

    def test_discovery_is_stable_skips_symlinks_and_keeps_invalid_metadata(self):
        first = self.root / "memory/a"
        second = self.root / "memory/b"
        first.mkdir(parents=True)
        second.mkdir()
        (first / "00_spec.md").write_text("# A\n")
        (second / "00_spec.md").write_text("# B\n")
        (second / "task-meta.json").write_text("{")
        (self.root / "memory/link").symlink_to(first, target_is_directory=True)

        memories = hub.discover_memory_tasks([first.parent])

        self.assertEqual([memory.path.name for memory in memories], ["a", "b"])
        self.assertIn("metadataError", memories[1].detail)

    def test_candidates_require_score_three_and_include_fifteen_minute_boundary(self):
        base = datetime(2026, 7, 12, 12, 0, tzinfo=timezone.utc)

        def memory(name, title, project_path, age):
            return hub.MemoryTask(
                Path("/memory") / name,
                title,
                None,
                project_path,
                None,
                None,
                datetime.fromtimestamp(base.timestamp() - age * 60, timezone.utc).isoformat(),
                {},
                {},
            )

        thread = hub.CodexThread(
            "t1", "Design", "/repo", "active", 0, int(base.timestamp())
        )
        memories = [
            memory("path", "Other", "/repo", 60),
            memory("title-time", "Design", "/other", 15),
            memory("title-only", "Design", "/other", 15.01),
        ]

        result = hub.match_thread_to_memory(thread, memories)

        self.assertEqual(
            [candidate.path.name for candidate in result.candidates],
            ["path", "title-time"],
        )


class TaskStateTest(unittest.TestCase):
    def test_explicit_state_precedes_freshness(self):
        cases = [
            ("active", "running", 15, "running"),
            ("active", "running", 16, "waiting"),
            ("idle", "waiting", 1, "waiting"),
            ("idle", "completed", 60, "recent_completed"),
            ("systemError", None, 1, "waiting"),
        ]

        for provider, explicit, age, expected in cases:
            with self.subTest(provider=provider, explicit=explicit, age=age):
                self.assertEqual(hub.classify_task(provider, explicit, age, 1), expected)

    def test_completed_is_recent_through_exactly_24_hours(self):
        self.assertEqual(
            hub.classify_task("idle", "completed", 24 * 60, 1),
            "recent_completed",
        )
        self.assertIsNone(
            hub.classify_task("idle", "completed", 24 * 60 + 0.01, 1)
        )


class UnifiedTaskIndexTest(unittest.TestCase):
    NOW = datetime(2026, 7, 12, 12, 0, tzinfo=timezone.utc)

    def memory(self, name, title, age_minutes, state=None, thread_id=None):
        updated = datetime.fromtimestamp(
            self.NOW.timestamp() - age_minutes * 60, timezone.utc
        ).isoformat()
        return hub.MemoryTask(
            path=Path("/memory") / name,
            title=title,
            thread_id=thread_id,
            project_path="/repo",
            task_state=state,
            approval_state=None,
            updated_at=updated,
            summary={"artifactCount": 1},
            detail={"files": {"00_spec.md": "# Spec"}},
        )

    def test_builds_provider_only_memory_only_exact_and_candidate_tasks(self):
        exact = self.memory("exact", "Exact", 5, "running", "t1")
        candidate = self.memory("candidate", "Candidate", 5)
        memory_only = self.memory("memory-only", "Memory only", 20, "waiting")
        threads = (
            hub.CodexThread("t1", "Exact", "/repo", "active", 0, int(self.NOW.timestamp() - 5 * 60)),
            hub.CodexThread("t2", "Candidate", "/repo", "active", 0, int(self.NOW.timestamp() - 5 * 60)),
            hub.CodexThread("t3", "Provider only", "/elsewhere", "idle", 0, int(self.NOW.timestamp() - 20 * 60)),
        )
        snapshot = hub.ProviderSnapshot(threads, True, self.NOW.isoformat())

        index = hub.build_task_index(
            snapshot, [exact, candidate, memory_only], now=self.NOW
        )

        by_id = {task.id: task for task in index["tasks"]}
        self.assertEqual(by_id["t1"].match_state, "exact")
        self.assertEqual(by_id["t2"].match_state, "candidate")
        self.assertEqual(by_id["t3"].match_state, "unmatched")
        self.assertIn("memory:/memory/memory-only", by_id)

    def test_sorts_sections_and_counts_only_expired_completed_as_archived(self):
        memories = [
            self.memory("z", "Zulu", 5, "waiting"),
            self.memory("a", "Alpha", 5, "waiting"),
            self.memory("recent", "Recent", 24 * 60, "completed"),
            self.memory("old", "Old", 24 * 60 + 1, "completed"),
        ]

        index = hub.build_task_index(
            hub.ProviderSnapshot((), True, self.NOW.isoformat()),
            memories,
            now=self.NOW,
        )

        self.assertEqual(
            [(task.section, task.title) for task in index["tasks"]],
            [
                ("waiting", "Alpha"),
                ("waiting", "Zulu"),
                ("recent_completed", "Recent"),
            ],
        )
        self.assertEqual(index["archivedCount"], 1)


class FakeClock:
    def __init__(self):
        self.value = 0.0

    def monotonic(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


class TaskHubSessionTest(unittest.TestCase):
    def test_server_handles_heartbeat_while_refresh_is_slow(self):
        refresh_started = threading.Event()
        release_refresh = threading.Event()

        def slow_builder():
            refresh_started.set()
            release_refresh.wait(timeout=1)
            return {
                "provider": hub.ProviderSnapshot(
                    (), True, "2026-07-12T00:00:00+00:00"
                ),
                "index": {"tasks": (), "archivedCount": 0},
            }

        session = hub.TaskHubSession(heartbeat_timeout=1, index_builder=slow_builder)
        server = hub.create_task_hub_server(("127.0.0.1", 0), session)
        thread = threading.Thread(
            target=hub.serve_task_hub, args=(server, session), daemon=True
        )
        thread.start()
        self.addCleanup(release_refresh.set)
        self.addCleanup(server.server_close)

        self.assertTrue(refresh_started.wait(timeout=1))
        connection = HTTPConnection(*server.server_address, timeout=0.5)
        connection.request(
            "POST", "/api/heartbeat", headers={"X-Roadmap-Session": session.key}
        )
        response = connection.getresponse()
        response.read()
        self.assertEqual(response.status, 204)

        release_refresh.set()

    def test_session_stops_after_heartbeat_timeout(self):
        clock = FakeClock()
        session = hub.TaskHubSession(
            heartbeat_timeout=10, monotonic=clock.monotonic
        )

        session.heartbeat()
        clock.advance(11)

        self.assertTrue(session.should_stop())

    def test_api_requires_session_key_and_sets_no_store(self):
        session = hub.TaskHubSession(index_builder=lambda: {
            "provider": hub.ProviderSnapshot((), True, "2026-07-12T00:00:00+00:00"),
            "index": {"tasks": (), "archivedCount": 0},
        })
        session.refresh()
        server = hub.create_task_hub_server(("127.0.0.1", 0), session)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        connection = HTTPConnection(*server.server_address)

        connection.request("GET", "/api/tasks")
        forbidden = connection.getresponse()
        forbidden.read()
        self.assertEqual(forbidden.status, 403)
        self.assertEqual(forbidden.getheader("Cache-Control"), "no-store")

        connection.request(
            "GET", "/api/tasks", headers={"X-Roadmap-Session": session.key}
        )
        response = connection.getresponse()
        payload = json.loads(response.read())
        self.assertEqual(response.status, 200)
        self.assertEqual(payload["tasks"], [])

    def test_refresh_keeps_last_good_tasks_and_recovers(self):
        states = [
            {
                "provider": hub.ProviderSnapshot(
                    (hub.CodexThread("t1", "One", "/repo", "active", 0, 1),),
                    True,
                    "2026-07-12T00:00:00+00:00",
                ),
                "index": {
                    "tasks": (
                        hub.UnifiedTask("t1", "One", "running", "active", "fresh", "1970-01-01T00:00:01+00:00", "t1", None, "unmatched", (), {}, {}),
                    ),
                    "archivedCount": 0,
                },
            },
            {"provider": hub.ProviderSnapshot((), False, "2026-07-12T00:00:02+00:00", "offline")},
            {
                "provider": hub.ProviderSnapshot((), True, "2026-07-12T00:00:04+00:00"),
                "index": {"tasks": (), "archivedCount": 0},
            },
        ]
        session = hub.TaskHubSession(index_builder=lambda: states.pop(0))

        self.assertTrue(session.refresh())
        last_success = session.payload()["lastSuccessfulSync"]
        self.assertFalse(session.refresh())
        degraded = session.payload()
        self.assertFalse(degraded["connected"])
        self.assertEqual(degraded["error"], "offline")
        self.assertEqual(degraded["lastSuccessfulSync"], last_success)
        self.assertEqual(degraded["tasks"][0]["id"], "t1")
        self.assertTrue(session.refresh())
        self.assertTrue(session.payload()["connected"])
        self.assertEqual(session.payload()["tasks"], [])

    def test_routes_return_detail_404_heartbeat_and_open_fallback(self):
        task = hub.UnifiedTask(
            "t/1", "One", "waiting", "idle", "fresh",
            "2026-07-12T00:00:00+00:00", "thread-1", None,
            "unmatched", (), {"x": 1}, {"body": "detail"},
        )
        session = hub.TaskHubSession(index_builder=lambda: {
            "provider": hub.ProviderSnapshot((), True, "2026-07-12T00:00:00+00:00"),
            "index": {"tasks": (task,), "archivedCount": 0},
        })
        session.refresh()
        server = hub.create_task_hub_server(("127.0.0.1", 0), session)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        headers = {"X-Roadmap-Session": session.key}
        connection = HTTPConnection(*server.server_address)

        connection.request("GET", "/api/session", headers=headers)
        self.assertEqual(connection.getresponse().status, 200)
        connection.request("GET", "/api/tasks/t%2F1", headers=headers)
        detail = connection.getresponse()
        self.assertEqual(json.loads(detail.read())["detail"]["body"], "detail")
        connection.request("GET", "/api/tasks/missing", headers=headers)
        missing = connection.getresponse()
        missing.read()
        self.assertEqual(missing.status, 404)
        connection.request("POST", "/api/heartbeat", headers=headers)
        heartbeat = connection.getresponse()
        heartbeat.read()
        self.assertEqual(heartbeat.status, 204)
        connection.request("POST", "/api/tasks/t%2F1/open", headers=headers)
        opened = connection.getresponse()
        opened_payload = json.loads(opened.read())
        self.assertEqual(opened.status, 409)
        self.assertEqual(opened_payload["threadId"], "thread-1")

    def test_root_serves_viewer_without_exposing_session_and_api_stays_protected(self):
        session = hub.TaskHubSession()
        server = hub.create_task_hub_server(("127.0.0.1", 0), session)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        connection = HTTPConnection(*server.server_address)

        connection.request("GET", "/")
        response = connection.getresponse()
        body = response.read().decode()
        self.assertEqual(response.status, 200)
        self.assertEqual(response.getheader("Cache-Control"), "no-store")
        self.assertIn('id="task-hub"', body)
        self.assertNotIn(session.key, body)

        connection.request("GET", "/api/tasks")
        protected = connection.getresponse()
        protected.read()
        self.assertEqual(protected.status, 403)

    def test_server_rejects_non_loopback_bind(self):
        session = hub.TaskHubSession()
        with self.assertRaisesRegex(ValueError, "loopback"):
            hub.create_task_hub_server(("0.0.0.0", 0), session)

    def test_start_url_keeps_key_in_fragment(self):
        session = hub.TaskHubSession()
        url = session.start_url(3210)
        self.assertEqual(url.split("#", 1)[0], "http://127.0.0.1:3210/")
        self.assertEqual(url.split("#", 1)[1], f"session={session.key}")

    def test_lifecycle_refreshes_every_two_seconds_until_heartbeat_expires(self):
        clock = FakeClock()
        refreshes = []
        waits = []
        session = hub.TaskHubSession(
            heartbeat_timeout=3,
            monotonic=clock.monotonic,
            index_builder=lambda: refreshes.append(clock.monotonic()) or {
                "provider": hub.ProviderSnapshot((), True, str(clock.monotonic())),
                "index": {"tasks": (), "archivedCount": 0},
            },
        )

        def wait(seconds):
            waits.append(seconds)
            clock.advance(seconds)

        hub.run_refresh_lifecycle(session, wait=wait)

        self.assertEqual(waits, [2.0, 2.0])
        self.assertEqual(refreshes, [0.0, 2.0])

    def test_index_builder_consumes_provider_and_memory_roots(self):
        class Provider:
            def list_threads(self):
                return hub.ProviderSnapshot((), True, "sync")

        builder = hub.make_task_index_builder(Provider(), [])

        result = builder()

        self.assertTrue(result["provider"].connected)
        self.assertEqual(result["index"]["tasks"], ())

    def test_run_task_hub_builds_loopback_server_for_memory_roots(self):
        memory_roots = [Path("/tmp/memory")]
        session = mock.Mock()
        session.should_stop.return_value = True
        session.start_url.return_value = "http://127.0.0.1:4321/#session=key"
        server = mock.Mock()
        server.server_address = ("127.0.0.1", 4321)

        with (
            mock.patch.object(hub, "CodexAppServerProvider") as provider_type,
            mock.patch.object(hub, "make_task_index_builder", return_value="builder") as make_builder,
            mock.patch.object(hub, "TaskHubSession", return_value=session) as session_type,
            mock.patch.object(hub, "create_task_hub_server", return_value=server) as create_server,
        ):
            result = hub.run_task_hub(memory_roots, host="localhost", port=0)

        self.assertEqual(result, 0)
        make_builder.assert_called_once_with(provider_type.return_value, memory_roots)
        session_type.assert_called_once_with(index_builder="builder")
        create_server.assert_called_once_with(("localhost", 0), session)
        server.server_close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
