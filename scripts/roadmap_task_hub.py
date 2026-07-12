"""Roadmap Task Hub backend."""

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import importlib.util
import ipaddress
import json
from pathlib import Path
import secrets
import subprocess
import sys
import threading
import time
from typing import Callable, Literal, TextIO
from urllib.parse import quote, unquote, urlsplit
import webbrowser


@dataclass(frozen=True)
class CodexThread:
    id: str
    title: str
    cwd: str
    status: str
    created_at: int
    updated_at: int


@dataclass(frozen=True)
class ProviderSnapshot:
    threads: tuple[CodexThread, ...]
    connected: bool
    synced_at: str
    error: str | None = None


@dataclass(frozen=True)
class MemoryTask:
    path: Path
    title: str
    thread_id: str | None
    project_path: str | None
    task_state: str | None
    approval_state: str | None
    updated_at: str
    summary: dict[str, object]
    detail: dict[str, object]


@dataclass(frozen=True)
class TaskMatch:
    confirmed: MemoryTask | None
    candidates: tuple[MemoryTask, ...]


@dataclass(frozen=True)
class UnifiedTask:
    id: str
    title: str
    section: Literal["running", "waiting", "recent_completed"]
    explicit_state: str
    freshness: str
    updated_at: str
    thread_id: str | None
    memory_path: str | None
    match_state: Literal["exact", "candidate", "unmatched"]
    match_candidates: tuple[dict[str, object], ...]
    summary: dict[str, object]
    detail: dict[str, object]


class ProviderError(RuntimeError):
    """Raised when the Codex app-server protocol cannot be completed."""


class TaskHubSession:
    def __init__(
        self,
        heartbeat_timeout: float = 10.0,
        monotonic: Callable[[], float] = time.monotonic,
        index_builder: Callable[[], dict[str, object]] | None = None,
    ):
        self.key = secrets.token_urlsafe(32)
        self.timeout = heartbeat_timeout
        self.monotonic = monotonic
        self.last_heartbeat = monotonic()
        self._index_builder = index_builder
        self._lock = threading.Lock()
        self._tasks: tuple[UnifiedTask, ...] = ()
        self._archived_count = 0
        self._fingerprint: str | None = None
        self.connected = False
        self.last_successful_sync: str | None = None
        self.error: str | None = None

    def heartbeat(self) -> None:
        self.last_heartbeat = self.monotonic()

    def should_stop(self) -> bool:
        return self.monotonic() - self.last_heartbeat > self.timeout

    def start_url(self, port: int) -> str:
        return f"http://127.0.0.1:{port}/#session={quote(self.key)}"

    def refresh(self) -> bool:
        if self._index_builder is None:
            return False
        try:
            update = self._index_builder()
            provider = update["provider"]
            if not isinstance(provider, ProviderSnapshot):
                raise TypeError("index builder provider is not a ProviderSnapshot")
            if not provider.connected:
                with self._lock:
                    self.connected = False
                    self.error = provider.error or "provider unavailable"
                return False
            index = update.get("index")
            if not isinstance(index, dict):
                raise TypeError("index builder result has no index")
            tasks = tuple(index.get("tasks", ()))
            fingerprint = json.dumps(
                {
                    "tasks": [_task_to_dict(task) for task in tasks],
                    "archivedCount": int(index.get("archivedCount", 0)),
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            with self._lock:
                changed = fingerprint != self._fingerprint
                if changed:
                    self._tasks = tasks
                    self._archived_count = int(index.get("archivedCount", 0))
                    self._fingerprint = fingerprint
                self.connected = True
                self.last_successful_sync = provider.synced_at
                self.error = None
            return changed
        except Exception as error:
            with self._lock:
                self.connected = False
                self.error = str(error)
            return False

    def payload(self) -> dict[str, object]:
        with self._lock:
            return {
                "connected": self.connected,
                "lastSuccessfulSync": self.last_successful_sync,
                "error": self.error,
                "tasks": [_task_to_dict(task) for task in self._tasks],
                "archivedCount": self._archived_count,
            }

    def task(self, task_id: str) -> dict[str, object] | None:
        with self._lock:
            for task in self._tasks:
                if task.id == task_id:
                    return _task_to_dict(task)
        return None


def _task_to_dict(task: UnifiedTask) -> dict[str, object]:
    return {
        "id": task.id,
        "title": task.title,
        "section": task.section,
        "explicitState": task.explicit_state,
        "freshness": task.freshness,
        "updatedAt": task.updated_at,
        "threadId": task.thread_id,
        "memoryPath": task.memory_path,
        "matchState": task.match_state,
        "matchCandidates": list(task.match_candidates),
        "summary": task.summary,
        "detail": task.detail,
    }


class TaskHubRequestHandler(BaseHTTPRequestHandler):
    server_version = "RoadmapTaskHub/0.1"

    @property
    def session(self) -> TaskHubSession:
        return self.server.session  # type: ignore[attr-defined]

    def log_message(self, format: str, *args: object) -> None:
        # Header values are intentionally never included in request logs.
        super().log_message(format, *args)

    def _authorized(self) -> bool:
        supplied = self.headers.get("X-Roadmap-Session", "")
        return hmac.compare_digest(supplied, self.session.key)

    def _send_json(self, status: int, payload: object | None = None) -> None:
        body = b"" if payload is None else json.dumps(
            payload, ensure_ascii=False, separators=(",", ":")
        ).encode()
        self.send_response(status)
        self.send_header("Cache-Control", "no-store")
        if body:
            self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _send_viewer(self) -> None:
        viewer = Path(__file__).parents[1] / "tools" / "roadmap_viewer.html"
        body = viewer.read_bytes()
        self.send_response(200)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _require_auth(self) -> bool:
        if self._authorized():
            return True
        self._send_json(403, {"error": "forbidden"})
        return False

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path == "/":
            self._send_viewer()
            return
        if not self._require_auth():
            return
        if path == "/api/session":
            payload = self.session.payload()
            payload.pop("tasks", None)
            self._send_json(200, payload)
            return
        if path == "/api/tasks":
            self._send_json(200, self.session.payload())
            return
        prefix = "/api/tasks/"
        if path.startswith(prefix):
            task = self.session.task(unquote(path[len(prefix):]))
            self._send_json(200, task) if task else self._send_json(
                404, {"error": "task not found"}
            )
            return
        self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:
        if not self._require_auth():
            return
        path = urlsplit(self.path).path
        if path == "/api/heartbeat":
            self.session.heartbeat()
            self._send_json(204)
            return
        prefix, suffix = "/api/tasks/", "/open"
        if path.startswith(prefix) and path.endswith(suffix):
            task_id = unquote(path[len(prefix):-len(suffix)])
            task = self.session.task(task_id)
            if task is None:
                self._send_json(404, {"error": "task not found"})
                return
            self._send_json(
                409,
                {
                    "error": "host navigation unavailable",
                    "threadId": task["threadId"],
                },
            )
            return
        self._send_json(404, {"error": "not found"})


def create_task_hub_server(
    address: tuple[str, int], session: TaskHubSession
) -> ThreadingHTTPServer:
    host, port = address
    try:
        loopback = host == "localhost" or ipaddress.ip_address(host).is_loopback
    except ValueError:
        loopback = False
    if not loopback:
        raise ValueError("Task Hub must bind to a loopback address")
    server = ThreadingHTTPServer((host, port), TaskHubRequestHandler)
    server.session = session  # type: ignore[attr-defined]
    return server


def run_refresh_lifecycle(
    session: TaskHubSession,
    *,
    poll_interval: float = 2.0,
    wait: Callable[[float], object] = time.sleep,
) -> None:
    """Refresh the index until the viewer heartbeat expires."""
    while not session.should_stop():
        session.refresh()
        wait(poll_interval)


def make_task_index_builder(
    provider: object, memory_roots: list[Path]
) -> Callable[[], dict[str, object]]:
    """Compose the provider and memory discovery into a session refresh."""
    def build() -> dict[str, object]:
        try:
            snapshot = provider.list_threads()  # type: ignore[attr-defined]
        except Exception as error:
            snapshot = ProviderSnapshot(
                (), False, _now_iso(), str(error)
            )
        result: dict[str, object] = {"provider": snapshot}
        if snapshot.connected:
            result["index"] = build_task_index(
                snapshot, discover_memory_tasks(memory_roots)
            )
        return result

    return build


class CodexAppServerProvider:
    def __init__(self, process_factory: Callable[[], object] | None = None):
        self._process_factory = process_factory or self._start_process

    @staticmethod
    def _start_process() -> subprocess.Popen[str]:
        return subprocess.Popen(
            ["codex", "app-server", "--listen", "stdio://"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )

    @staticmethod
    def _send(stream: TextIO, message: dict[str, object]) -> None:
        stream.write(json.dumps(message, ensure_ascii=False) + "\n")
        stream.flush()

    @staticmethod
    def _read_response(stream: TextIO, request_id: int) -> dict[str, object]:
        while True:
            line = stream.readline()
            if not line:
                raise ProviderError(
                    f"codex app-server closed before response {request_id}"
                )
            try:
                message = json.loads(line)
            except json.JSONDecodeError as error:
                raise ProviderError(f"invalid JSON from codex app-server: {error}") from error
            if message.get("id") != request_id:
                continue
            if "error" in message:
                error = message["error"]
                if isinstance(error, dict):
                    detail = error.get("message", json.dumps(error, ensure_ascii=False))
                else:
                    detail = str(error)
                raise ProviderError(f"codex app-server request failed: {detail}")
            result = message.get("result")
            if not isinstance(result, dict):
                raise ProviderError(
                    f"codex app-server response {request_id} has no result object"
                )
            return result

    def list_threads(self) -> ProviderSnapshot:
        process = self._process_factory()
        stdin = getattr(process, "stdin", None)
        stdout = getattr(process, "stdout", None)
        if stdin is None or stdout is None:
            raise ProviderError("codex app-server process has no stdio streams")

        try:
            self._send(
                stdin,
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "clientInfo": {
                            "name": "roadmap-task-hub",
                            "version": "0.1.0",
                        }
                    },
                },
            )
            self._read_response(stdout, 1)
            self._send(
                stdin,
                {"jsonrpc": "2.0", "method": "initialized", "params": {}},
            )

            threads: list[CodexThread] = []
            cursor: str | None = None
            request_id = 2
            while True:
                params: dict[str, object] = {
                    "limit": 100,
                    "sortKey": "updated_at",
                }
                if cursor:
                    params["cursor"] = cursor
                self._send(
                    stdin,
                    {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "method": "thread/list",
                        "params": params,
                    },
                )
                result = self._read_response(stdout, request_id)
                data = result.get("data", [])
                if not isinstance(data, list):
                    raise ProviderError("thread/list result data is not a list")
                threads.extend(self._to_thread(item) for item in data)
                cursor_value = result.get("nextCursor")
                cursor = cursor_value if isinstance(cursor_value, str) else None
                if not cursor:
                    break
                request_id += 1

            return ProviderSnapshot(
                threads=tuple(threads),
                connected=True,
                synced_at=_now_iso(),
            )
        finally:
            terminate = getattr(process, "terminate", None)
            if callable(terminate):
                terminate()

    @staticmethod
    def _to_thread(item: object) -> CodexThread:
        if not isinstance(item, dict):
            raise ProviderError("thread/list returned a non-object thread")
        thread_id = str(item.get("id", ""))
        name = item.get("name")
        preview = item.get("preview")
        title = (
            name.strip()
            if isinstance(name, str) and name.strip()
            else preview[:80]
            if isinstance(preview, str) and preview
            else thread_id
        )
        status_value = item.get("status")
        status = (
            str(status_value.get("type", ""))
            if isinstance(status_value, dict)
            else str(status_value or "")
        )
        return CodexThread(
            id=thread_id,
            title=title,
            cwd=str(item.get("cwd", "")),
            status=status,
            created_at=int(item.get("createdAt", 0)),
            updated_at=int(item.get("updatedAt", 0)),
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_provider_snapshot(provider: CodexAppServerProvider) -> ProviderSnapshot:
    try:
        return provider.list_threads()
    except Exception as error:
        return ProviderSnapshot(
            threads=(), connected=False, synced_at=_now_iso(), error=str(error)
        )


def _roadmap_snapshot(task_dir: Path) -> dict[str, object]:
    module_path = Path(__file__).with_name("generate-roadmap-view.py")
    spec = importlib.util.spec_from_file_location("roadmap_snapshot_builder", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load roadmap snapshot builder: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_snapshot(task_dir)


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def discover_memory_tasks(roots: list[Path]) -> tuple[MemoryTask, ...]:
    tasks: list[MemoryTask] = []
    for root in roots:
        if not root.is_dir() or root.is_symlink():
            continue
        for task_dir in sorted(root.iterdir(), key=lambda path: path.name):
            if not task_dir.is_dir() or task_dir.is_symlink():
                continue
            metadata: dict[str, object] = {}
            metadata_error: str | None = None
            metadata_path = task_dir / "task-meta.json"
            if metadata_path.is_file() and not metadata_path.is_symlink():
                try:
                    loaded = json.loads(metadata_path.read_text())
                    if not isinstance(loaded, dict):
                        raise ValueError("metadata root is not an object")
                    metadata = loaded
                except (OSError, json.JSONDecodeError, ValueError) as error:
                    metadata_error = str(error)
            try:
                snapshot = _roadmap_snapshot(task_dir)
            except (OSError, ValueError) as error:
                snapshot = {
                    "title": task_dir.name.replace("_", " "),
                    "taskDir": str(task_dir),
                    "files": {},
                    "sources": [],
                    "artifacts": [],
                }
                if metadata_error is None:
                    metadata_error = str(error)
            updated_at = _optional_string(metadata.get("updated_at"))
            if updated_at is None:
                timestamps = [
                    child.stat().st_mtime
                    for child in task_dir.iterdir()
                    if child.is_file() and not child.is_symlink()
                ]
                updated_at = datetime.fromtimestamp(
                    max(timestamps, default=task_dir.stat().st_mtime), timezone.utc
                ).isoformat()
            detail = dict(snapshot)
            detail["metadata"] = metadata
            if metadata_error is not None:
                detail["metadataError"] = metadata_error
            tasks.append(
                MemoryTask(
                    path=task_dir,
                    title=_optional_string(metadata.get("task_title"))
                    or str(snapshot.get("title", task_dir.name)),
                    thread_id=_optional_string(metadata.get("thread_id")),
                    project_path=_optional_string(metadata.get("project_path")),
                    task_state=_optional_string(metadata.get("task_state")),
                    approval_state=_optional_string(metadata.get("approval_state")),
                    updated_at=updated_at,
                    summary={
                        "taskDir": str(task_dir),
                        "artifactCount": len(snapshot.get("artifacts", [])),
                    },
                    detail=detail,
                )
            )
    return tuple(tasks)


def match_thread_to_memory(
    thread: CodexThread, memories: tuple[MemoryTask, ...] | list[MemoryTask]
) -> TaskMatch:
    exact = sorted(
        (memory for memory in memories if memory.thread_id == thread.id),
        key=lambda memory: str(memory.path),
    )
    if exact:
        return TaskMatch(confirmed=exact[0], candidates=())

    scored: list[tuple[int, MemoryTask]] = []
    for memory in memories:
        score = _candidate_score(thread, memory)
        if score >= 3:
            scored.append((score, memory))
    scored.sort(key=lambda item: (-item[0], str(item[1].path)))
    return TaskMatch(confirmed=None, candidates=tuple(item[1] for item in scored))


def classify_task(
    provider_state: str | None,
    explicit_state: str | None,
    age_minutes: float,
    artifact_count: int,
) -> Literal["running", "waiting", "recent_completed"] | None:
    del artifact_count
    if explicit_state == "completed":
        return "recent_completed" if age_minutes <= 24 * 60 else None
    if explicit_state == "waiting":
        return "waiting"
    if explicit_state == "running":
        return "running" if provider_state == "active" and age_minutes <= 15 else "waiting"
    if provider_state == "active" and age_minutes <= 15:
        return "running"
    return "waiting"


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed


def _candidate_score(thread: CodexThread, memory: MemoryTask) -> int:
    score = 3 if memory.project_path == thread.cwd else 0
    if memory.title == thread.title:
        score += 2
    try:
        if abs(_parse_time(memory.updated_at).timestamp() - thread.updated_at) <= 15 * 60:
            score += 1
    except ValueError:
        pass
    return score


def _freshness(age_minutes: float) -> str:
    if age_minutes <= 15:
        return "fresh"
    if age_minutes <= 24 * 60:
        return "stale"
    return "archived"


def build_task_index(
    provider: ProviderSnapshot,
    memories: tuple[MemoryTask, ...] | list[MemoryTask],
    *,
    now: datetime | None = None,
) -> dict[str, object]:
    current_time = now or datetime.now(timezone.utc)
    unified: list[UnifiedTask] = []
    consumed_paths: set[Path] = set()
    archived_count = 0

    for thread in provider.threads:
        match = match_thread_to_memory(thread, memories)
        memory = match.confirmed
        if memory is not None:
            consumed_paths.add(memory.path)
        thread_time = datetime.fromtimestamp(thread.updated_at, timezone.utc)
        memory_time = _parse_time(memory.updated_at) if memory is not None else None
        updated_time = max(thread_time, memory_time) if memory_time else thread_time
        age_minutes = max(0.0, (current_time - updated_time).total_seconds() / 60)
        explicit_state = None
        if memory is not None:
            explicit_state = memory.approval_state or memory.task_state
        section = classify_task(thread.status, explicit_state, age_minutes, 1)
        if section is None:
            archived_count += 1
            continue
        candidates = tuple(
            {
                "path": str(candidate.path),
                "title": candidate.title,
                "score": _candidate_score(thread, candidate),
            }
            for candidate in match.candidates
        )
        summary = {
            "providerStatus": thread.status,
            **(memory.summary if memory is not None else {}),
        }
        detail = {
            "thread": {
                "id": thread.id,
                "title": thread.title,
                "cwd": thread.cwd,
                "status": thread.status,
            },
            **(memory.detail if memory is not None else {}),
        }
        unified.append(
            UnifiedTask(
                id=thread.id,
                title=memory.title if memory is not None else thread.title,
                section=section,
                explicit_state=explicit_state or thread.status or "unknown",
                freshness=_freshness(age_minutes),
                updated_at=updated_time.isoformat(),
                thread_id=thread.id,
                memory_path=str(memory.path) if memory is not None else None,
                match_state=(
                    "exact" if memory is not None else "candidate" if candidates else "unmatched"
                ),
                match_candidates=candidates,
                summary=summary,
                detail=detail,
            )
        )

    for memory in memories:
        if memory.path in consumed_paths:
            continue
        updated_time = _parse_time(memory.updated_at)
        age_minutes = max(0.0, (current_time - updated_time).total_seconds() / 60)
        explicit_state = memory.approval_state or memory.task_state
        section = classify_task(None, explicit_state, age_minutes, 1)
        if section is None:
            archived_count += 1
            continue
        unified.append(
            UnifiedTask(
                id=f"memory:{memory.path}",
                title=memory.title,
                section=section,
                explicit_state=explicit_state or "unknown",
                freshness=_freshness(age_minutes),
                updated_at=updated_time.isoformat(),
                thread_id=memory.thread_id,
                memory_path=str(memory.path),
                match_state="unmatched",
                match_candidates=(),
                summary=memory.summary,
                detail=memory.detail,
            )
        )

    section_order = {"running": 0, "waiting": 1, "recent_completed": 2}
    unified.sort(
        key=lambda task: (
            section_order[task.section],
            -_parse_time(task.updated_at).timestamp(),
            task.title,
            task.id,
        )
    )
    return {"tasks": tuple(unified), "archivedCount": archived_count}


def run_task_hub(
    memory_roots: list[Path],
    *,
    host: str = "127.0.0.1",
    port: int = 0,
    open_browser: bool = False,
) -> int:
    provider = CodexAppServerProvider()
    session = TaskHubSession(
        index_builder=make_task_index_builder(provider, memory_roots)
    )
    server = create_task_hub_server((host, port), session)
    server.timeout = 2.0
    url = session.start_url(server.server_address[1])
    print(url, flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        while not session.should_stop():
            session.refresh()
            server.handle_request()
    except KeyboardInterrupt:
        print("\nstopping roadmap task hub", file=sys.stderr)
    finally:
        server.server_close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe-provider", action="store_true")
    args = parser.parse_args()
    if not args.probe_provider:
        parser.error("one of --probe-provider is required")

    snapshot = safe_provider_snapshot(CodexAppServerProvider())
    payload = {
        "connected": snapshot.connected,
        "syncedAt": snapshot.synced_at,
        "error": snapshot.error,
        "threads": [
            {
                "id": thread.id,
                "title": thread.title,
                "cwd": thread.cwd,
                "status": thread.status,
                "updatedAt": thread.updated_at,
            }
            for thread in snapshot.threads
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if snapshot.connected else 1


if __name__ == "__main__":
    raise SystemExit(main())
