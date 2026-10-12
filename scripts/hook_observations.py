#!/usr/bin/env python3
"""Bounded, non-blocking observations for compact, diagnostics, and failures."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
import os
import re
import secrets
import signal
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

SCHEMA = 1
OWNER = "hook-observations"
MARKER = "hook-observations-generated-v1"
DEDUP_LIMIT = 64
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
UUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
HEX64 = re.compile(r"[0-9a-f]{64}")
CODEX_ROLLOUT = re.compile(
    rf"rollout-\d{{4}}-\d{{2}}-\d{{2}}T\d{{2}}-\d{{2}}-\d{{2}}-(?P<session>{UUID.pattern})\.jsonl"
)
EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
READ_ONLY = re.compile(
    r"^\s*(?:git\s+(?:status|log|diff|branch)|ls|grep|rg|find|cat|head|tail|wc|jq|pwd|which|stat|du|df)\b"
)
PERMISSION_CODES = {"permission_denied", "permission_rejected", "denied", "user_rejected"}


def emit(hook: str, status: str, reason: str, **extra: Any) -> None:
    print(
        json.dumps(
            {"hook": hook, "status": status, "reason": reason, **extra},
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        file=sys.stderr,
    )


def payload_from_stdin(hook: str) -> dict[str, Any] | None:
    try:
        value = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        emit(hook, "unknown", "invalid_json")
        return None
    if not isinstance(value, dict):
        emit(hook, "unknown", "invalid_payload")
        return None
    return value


def safe_identifier(payload: dict[str, Any]) -> str | None:
    value = payload.get("session_id") or payload.get("thread_id")
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value) or value in {".", ".."}:
        return None
    return value


def worktree_path(payload: dict[str, Any]) -> Path | None:
    value = payload.get("cwd")
    if not isinstance(value, str) or not os.path.isabs(value):
        return None
    path = Path(value).resolve()
    if not path.is_dir():
        return None
    for candidate in (path, *path.parents):
        if (candidate / ".git").exists():
            return candidate
    return path


def identity(payload: dict[str, Any], runtime: str) -> dict[str, str] | None:
    session = safe_identifier(payload)
    worktree = worktree_path(payload)
    if session is None or worktree is None:
        return None
    return {"runtime": runtime, "session": session, "worktree": str(worktree)}


def digest(value: Any) -> str:
    packed = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(packed.encode()).hexdigest()


def open_private_directory(path: Path) -> int:
    """Open an owner-only directory without following any path component."""
    absolute = path.absolute()
    parts = absolute.parts
    descriptor = os.open(parts[0], os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for index, part in enumerate(parts[1:], start=1):
            flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW
            try:
                child = os.open(part, flags, dir_fd=descriptor)
            except FileNotFoundError:
                try:
                    os.mkdir(part, 0o700, dir_fd=descriptor)
                except FileExistsError:
                    pass
                child = os.open(part, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
            info = os.fstat(descriptor)
            if not stat.S_ISDIR(info.st_mode):
                raise OSError("state path component is not a directory")
            if index == len(parts) - 1:
                if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
                    raise OSError("state directory is not owner-private")
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def canonical_record(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sealed_record(value: dict[str, Any]) -> dict[str, Any]:
    result = dict(value)
    result.pop("content_hash", None)
    result["content_hash"] = hashlib.sha256(canonical_record(result)).hexdigest()
    return result


RECORD_KEYS = {
    "compact": {"schema", "owner", "marker", "kind", "identity", "identity_digest", "count", "delivery_ids", "content_hash"},
    "failure": {
        "schema", "owner", "marker", "kind", "identity", "identity_digest", "chain_open", "count",
        "outcome", "delivery_ids", "content_hash", "failure_key", "notified",
    },
    "stop-suggestion": {
        "schema", "owner", "marker", "kind", "identity", "identity_digest", "transcript_digest",
        "tool_calls", "reasons", "reviewed", "content_hash",
    },
}


class OwnedJson:
    def __init__(self, directory: Path, prefix: str, key: Any, kind: str, ident: dict[str, str]):
        self.directory = directory
        self.name = f"{prefix}-{digest(key)[:24]}.json"
        self.lock_name = f".{self.name}.lock"
        self.path = directory / self.name
        self.kind = kind
        self.ident = ident

    def valid(self, value: Any) -> bool:
        if not isinstance(value, dict) or set(value) != RECORD_KEYS.get(self.kind):
            return False
        if value.get("schema") != SCHEMA or value.get("owner") != OWNER or value.get("marker") != MARKER:
            return False
        if value.get("kind") != self.kind or value.get("identity") != self.ident:
            return False
        if value.get("identity_digest") != digest(self.ident):
            return False
        deliveries = value.get("delivery_ids")
        if self.kind in {"compact", "failure"}:
            if not isinstance(deliveries, list) or len(deliveries) > DEDUP_LIMIT:
                return False
            if any(not isinstance(item, str) or HEX64.fullmatch(item) is None for item in deliveries):
                return False
        if self.kind == "compact":
            if type(value.get("count")) is not int or not 0 <= value["count"] < 100:
                return False
        elif self.kind == "failure":
            if type(value.get("chain_open")) is not bool or type(value.get("notified")) is not bool:
                return False
            if type(value.get("count")) is not int or value["count"] < 0:
                return False
            if value.get("outcome") not in {"failure", "success", "edit", "permission", "interruption", "read_only", "unknown"}:
                return False
            failure_key = value.get("failure_key")
            if failure_key is not None and (not isinstance(failure_key, str) or HEX64.fullmatch(failure_key) is None):
                return False
        elif self.kind == "stop-suggestion":
            if value.get("reasons") != ["structured_tool_failures"] or value.get("reviewed") is not False:
                return False
            if not isinstance(value.get("transcript_digest"), str) or HEX64.fullmatch(value["transcript_digest"]) is None:
                return False
            calls = value.get("tool_calls")
            wanted = {"success", "failure", "rejection", "interruption", "unknown", "total"}
            if not isinstance(calls, dict) or set(calls) != wanted:
                return False
            if any(type(calls[name]) is not int or calls[name] < 0 for name in wanted):
                return False
            if calls["total"] != sum(calls[name] for name in wanted - {"total"}):
                return False
        expected = value.get("content_hash")
        unsealed = dict(value)
        unsealed.pop("content_hash", None)
        return isinstance(expected, str) and expected == hashlib.sha256(canonical_record(unsealed)).hexdigest()

    @staticmethod
    def _open_regular(directory_fd: int, name: str, flags: int, mode: int = 0o600) -> int:
        descriptor = os.open(name, flags | os.O_CLOEXEC | os.O_NOFOLLOW, mode, dir_fd=directory_fd)
        try:
            info = os.fstat(descriptor)
            named = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            if not stat.S_ISREG(info.st_mode) or (info.st_dev, info.st_ino) != (named.st_dev, named.st_ino):
                raise OSError("state leaf is not a stable regular file")
            if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600:
                raise OSError("state leaf is not owner-private")
        except Exception:
            os.close(descriptor)
            raise
        return descriptor

    @classmethod
    def _open_or_create_lock(cls, directory_fd: int, name: str) -> int:
        try:
            return cls._open_regular(
                directory_fd,
                name,
                os.O_CREAT | os.O_EXCL | os.O_RDWR,
            )
        except FileExistsError:
            return cls._open_regular(directory_fd, name, os.O_RDWR)

    @classmethod
    def _read(cls, directory_fd: int, name: str) -> bytes | None:
        try:
            descriptor = cls._open_regular(directory_fd, name, os.O_RDONLY)
        except FileNotFoundError:
            return None
        try:
            chunks = []
            while True:
                chunk = os.read(descriptor, 65536)
                if not chunk:
                    return b"".join(chunks)
                chunks.append(chunk)
        finally:
            os.close(descriptor)

    def update(
        self, change: Callable[[dict[str, Any] | None], dict[str, Any]]
    ) -> tuple[bool, dict[str, Any] | None]:
        directory_fd = open_private_directory(self.directory)
        try:
            descriptor = self._open_or_create_lock(directory_fd, self.lock_name)
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX)
                before_bytes = self._read(directory_fd, self.name)
                before = None
                if before_bytes is not None:
                    try:
                        before = json.loads(before_bytes)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        return False, None
                    if not self.valid(before):
                        return False, None
                after = sealed_record(change(before))
                if not self.valid(after):
                    raise ValueError("owned state callback returned an invalid record")
                current = self._read(directory_fd, self.name)
                if current != before_bytes:
                    return False, None
                temp_name = f".{self.name}.{secrets.token_hex(12)}.tmp"
                temp_descriptor = os.open(
                    temp_name,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_CLOEXEC | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=directory_fd,
                )
                try:
                    output = canonical_record(after) + b"\n"
                    while output:
                        written = os.write(temp_descriptor, output)
                        if written <= 0:
                            raise OSError("short state write")
                        output = output[written:]
                    os.fsync(temp_descriptor)
                finally:
                    os.close(temp_descriptor)
                try:
                    if self._read(directory_fd, self.name) != before_bytes:
                        return False, None
                    os.replace(temp_name, self.name, src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
                    os.fsync(directory_fd)
                finally:
                    try:
                        os.unlink(temp_name, dir_fd=directory_fd)
                    except FileNotFoundError:
                        pass
                return True, after
            finally:
                try:
                    fcntl.flock(descriptor, fcntl.LOCK_UN)
                finally:
                    os.close(descriptor)
        finally:
            os.close(directory_fd)


def state_directory(runtime: str) -> Path:
    override = os.environ.get("HOOK_OBSERVATIONS_STATE_DIR")
    if override:
        return Path(override)
    runtime_home = (Path.home() / f".{runtime}").resolve(strict=True)
    return runtime_home / ".local/hooks/state"


def base_record(kind: str, ident: dict[str, str]) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "owner": OWNER,
        "marker": MARKER,
        "kind": kind,
        "identity": ident,
        "identity_digest": digest(ident),
    }


def delivery_digest(payload: dict[str, Any], runtime: str) -> str | None:
    for name in ("tool_use_id", "event_id", "hook_event_id"):
        value = payload.get(name)
        if isinstance(value, str) and 0 < len(value) <= 512:
            return digest({"runtime": runtime, "field": name, "value": value})
    return None


def bounded_deliveries(previous: dict[str, Any] | None, delivery: str) -> tuple[list[str], bool]:
    existing = list((previous or {}).get("delivery_ids", []))
    if delivery in existing:
        return existing, True
    return (existing + [delivery])[-DEDUP_LIMIT:], False


def command_compact(payload: dict[str, Any], runtime: str) -> None:
    if payload.get("tool_name") not in EDIT_TOOLS:
        return
    ident = identity(payload, runtime)
    if ident is None:
        emit("compact", "unsupported", "invalid_identity")
        return
    delivery = delivery_digest(payload, runtime)
    if delivery is None:
        emit("compact", "unknown", "event_identity_unavailable")
        return
    observed: dict[str, int] = {}

    def increment(previous: dict[str, Any] | None) -> dict[str, Any]:
        deliveries, duplicate = bounded_deliveries(previous, delivery)
        if duplicate:
            observed["duplicate"] = 1
            return dict(previous or {})
        count = int((previous or {}).get("count", 0)) + 1
        observed["count"] = count
        record = base_record("compact", ident)
        record.update({"count": 0 if count == 100 else count, "delivery_ids": deliveries})
        return record

    ok, _ = OwnedJson(state_directory(runtime), "compact", ident, "compact", ident).update(increment)
    if not ok:
        emit("compact", "unknown", "state_preserved")
        return
    if observed.get("duplicate"):
        return
    count = observed["count"]
    if count in {50, 100}:
        level = "hint" if count == 50 else "recommend"
        emit(
            "compact",
            level,
            "edit_count_proxy_threshold",
            edit_count=count,
            proxy="edit_count_not_tokens",
        )


def normalize_diagnostic(value: str) -> str:
    value = re.sub(r"\b\d{4}-\d{2}-\d{2}[T ][0-2]\d:[0-5]\d:[0-5]\d(?:\.\d+)?Z?\b", "<timestamp>", value)
    value = re.sub(r"\b[0-2]\d:[0-5]\d:[0-5]\d(?:\.\d+)?\b", "<time>", value)
    value = re.sub(r"\b\d+(?:\.\d+)?\s*(?:ms|s|seconds?)\b", "<duration>", value, flags=re.I)
    return " ".join(value.split())


def command_class(command: Any) -> str:
    if not isinstance(command, str):
        return "unknown"
    lowered = command.strip().lower()
    if READ_ONLY.search(command):
        return "read"
    if re.search(r"\b(?:pytest|unittest|test|spec)\b", lowered):
        return "test"
    if re.search(r"\b(?:tsc|typecheck)\b", lowered):
        return "typecheck"
    if re.search(r"\b(?:eslint|ruff|lint|mypy)\b", lowered):
        return "lint"
    if re.search(r"\b(?:build|compile|cargo|make)\b", lowered):
        return "build"
    if re.match(r"^\s*git\b", lowered):
        return "vcs"
    return "other"


def structured_error(payload: dict[str, Any]) -> tuple[str | None, str]:
    error = payload.get("error")
    if isinstance(error, dict):
        code = error.get("code") or error.get("type")
        text = error.get("message") or error.get("diagnostic") or ""
        return str(code) if code is not None else None, str(text)
    if isinstance(error, str):
        return None, error
    response = payload.get("tool_response")
    if isinstance(response, dict):
        code = response.get("code") or response.get("error_code")
        text = response.get("error") or response.get("stderr") or ""
        return str(code) if code is not None else None, str(text)
    return None, ""


def explicit_exit(payload: dict[str, Any]) -> int | None:
    candidates = [payload.get("exit_code"), payload.get("exitCode")]
    response = payload.get("tool_response")
    if isinstance(response, dict):
        candidates.extend([response.get("exit_code"), response.get("exitCode")])
    for value in candidates:
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    return None


def permission_denial(payload: dict[str, Any], code: str | None) -> bool:
    decision = payload.get("permission_decision") or payload.get("permissionDecision")
    return (
        payload.get("permission_denied") is True
        or decision in {"deny", "denied", "reject", "rejected"}
        or (code or "").lower() in PERMISSION_CODES
    )


def failure_state(payload: dict[str, Any], runtime: str) -> tuple[str, dict[str, Any] | None]:
    if runtime == "codex":
        return "unknown", None
    event = payload.get("hook_event_name")
    tool = str(payload.get("tool_name") or "unknown")
    command = (payload.get("tool_input") or {}).get("command") if isinstance(payload.get("tool_input"), dict) else None
    category = command_class(command)
    code, diagnostic = structured_error(payload)
    if payload.get("is_interrupt") is True or event == "Interrupt":
        return "interruption", None
    if permission_denial(payload, code):
        return "permission", None
    exit_code = explicit_exit(payload)
    response = payload.get("tool_response")
    response_error = isinstance(response, dict) and response.get("is_error") is True
    known_failure = bool(
        diagnostic
        or code
        or payload.get("is_error") is True
        or response_error
        or (exit_code is not None and exit_code != 0)
    )
    if event == "PostToolUse" and not known_failure:
        return ("edit", None) if tool in EDIT_TOOLS else ("success", None)
    if event not in {"PostToolUse", "PostToolUseFailure"}:
        return "unknown", None
    if not known_failure:
        return "unknown", None
    if category == "read":
        return "read_only", None
    key = {
        "runtime": runtime,
        "tool": tool,
        "exit": exit_code if exit_code is not None else "is_error",
        "code": code,
        "command_class": category,
        "diagnostic_digest": hashlib.sha256(normalize_diagnostic(diagnostic).encode()).hexdigest(),
    }
    return "failure", key


def command_observe(payload: dict[str, Any], runtime: str) -> None:
    ident = identity(payload, runtime)
    if ident is None:
        emit("failure-observation", "unsupported", "invalid_identity")
        return
    if runtime == "codex":
        emit("failure-observation", "unknown", "structured_outcome_unavailable")
        return
    delivery = delivery_digest(payload, runtime)
    if delivery is None:
        emit("failure-observation", "unknown", "event_identity_unavailable")
        return
    outcome, key = failure_state(payload, runtime)
    store = OwnedJson(state_directory(runtime), "failure", ident, "failure", ident)

    def record_for(
        previous: dict[str, Any] | None,
        *,
        chain_open: bool,
        count: int,
        result: str,
        failure_key: str | None = None,
        notified: bool = False,
    ) -> tuple[dict[str, Any], bool]:
        deliveries, duplicate = bounded_deliveries(previous, delivery)
        if duplicate:
            return dict(previous or {}), True
        record = base_record("failure", ident)
        record.update(
            {
                "chain_open": chain_open,
                "count": count,
                "outcome": result,
                "delivery_ids": deliveries,
                "failure_key": failure_key,
                "notified": notified,
            }
        )
        return record, False

    if outcome == "unknown":
        def break_chain(previous: dict[str, Any] | None) -> dict[str, Any]:
            record, _ = record_for(
                previous,
                chain_open=False,
                count=int((previous or {}).get("count", 0)),
                result="unknown",
            )
            return record
        ok, _ = store.update(break_chain)
        emit("failure-observation", "unknown", "structured_outcome_unavailable" if ok else "state_preserved")
        return
    if outcome != "failure":
        def reset(_previous: dict[str, Any] | None) -> dict[str, Any]:
            record, _ = record_for(_previous, chain_open=False, count=0, result=outcome)
            return record
        ok, _ = store.update(reset)
        if not ok:
            emit("failure-observation", "unknown", "state_preserved")
        return
    key_digest = digest(key)
    notified: dict[str, Any] = {}

    def advance(previous: dict[str, Any] | None) -> dict[str, Any]:
        deliveries, duplicate = bounded_deliveries(previous, delivery)
        if duplicate:
            notified.update({"duplicate": True, "send": False})
            return dict(previous or {})
        same = bool(previous and previous.get("chain_open") is True and previous.get("failure_key") == key_digest)
        count = int(previous.get("count", 0)) + 1 if same else 1
        already = bool(previous and same and previous.get("notified") is True)
        record = base_record("failure", ident)
        record.update(
            {
                "chain_open": True,
                "count": count,
                "failure_key": key_digest,
                "notified": already or count == 3,
                "outcome": "failure",
                "delivery_ids": deliveries,
            }
        )
        notified.update({"count": count, "send": count == 3 and not already})
        return record

    ok, _ = store.update(advance)
    if not ok:
        emit("failure-observation", "unknown", "state_preserved")
    elif notified.get("send"):
        emit(
            "failure-observation",
            "suggestion",
            "same_structured_failure_three_times",
            count=3,
            action="inspect_diagnostic_and_change_approach",
        )


def inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def find_typescript_root(path: Path, worktree: Path) -> Path | None:
    candidate = path.parent
    while inside(candidate, worktree):
        config = candidate / "tsconfig.json"
        if config.is_symlink():
            return None
        if config.is_file() and inside(config.resolve(strict=True), worktree):
            return candidate
        if candidate == worktree:
            break
        candidate = candidate.parent
    return None


def terminate_group(process: subprocess.Popen[str]) -> tuple[str, str]:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        return process.communicate(timeout=1)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        return process.communicate()


def command_typescript(payload: dict[str, Any], _runtime: str) -> None:
    if payload.get("tool_name") not in EDIT_TOOLS:
        return
    tool_input = payload.get("tool_input")
    raw_path = tool_input.get("file_path") if isinstance(tool_input, dict) else None
    if not isinstance(raw_path, str) or not raw_path.endswith((".ts", ".tsx")) or raw_path.endswith(".d.ts"):
        return
    worktree = worktree_path(payload)
    cwd = payload.get("cwd")
    if worktree is None or not isinstance(cwd, str) or not os.path.isabs(cwd):
        emit("typescript", "unknown", "invalid_worktree")
        return
    lexical = Path(raw_path) if Path(raw_path).is_absolute() else Path(cwd) / raw_path
    lexical = Path(os.path.abspath(lexical))
    if not inside(lexical, worktree) or lexical.is_symlink():
        emit("typescript", "unknown", "edited_file_outside_worktree")
        return
    try:
        path = lexical.resolve(strict=True)
    except OSError:
        emit("typescript", "unknown", "edited_file_missing")
        return
    if not inside(path, worktree) or not path.is_file():
        emit("typescript", "unknown", "edited_file_outside_worktree")
        return
    root = find_typescript_root(path, worktree)
    if root is None:
        return
    compiler = Path(os.path.abspath(root / "node_modules/.bin/tsc"))
    if not inside(compiler, worktree):
        emit("typescript", "unknown", "project_local_compiler_outside_worktree", run_count=0)
        return
    try:
        compiler_target = compiler.resolve(strict=True)
    except OSError:
        emit("typescript", "unknown", "project_local_compiler_missing", run_count=0)
        return
    if not inside(compiler_target, worktree) or not compiler_target.is_file():
        emit("typescript", "unknown", "project_local_compiler_outside_worktree", run_count=0)
        return
    if not os.access(compiler_target, os.X_OK):
        emit("typescript", "unknown", "project_local_compiler_missing", run_count=0)
        return
    try:
        requested = float(os.environ.get("HOOK_OBSERVATIONS_TSC_TIMEOUT", "15"))
    except ValueError:
        requested = 15
    timeout = max(0.05, min(requested, 15.0))
    try:
        process = subprocess.Popen(
            [str(compiler), "--noEmit"],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
    except OSError:
        emit("typescript", "unknown", "compiler_start_failed", run_count=1)
        return
    try:
        output, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        terminate_group(process)
        emit("typescript", "unknown", "timeout", run_count=1, timeout_seconds=timeout)
        return
    errors = [line for line in output.splitlines() if re.search(r"\berror TS\d+\b", line)]
    error_count = sum(len(re.findall(r"\berror TS\d+\b", line)) for line in errors)
    if process.returncode != 0 or errors:
        emit(
            "typescript",
            "errors" if errors else "completed_nonzero",
            "project_local_tsc_result",
            run_count=1,
            exit_code=process.returncode,
            error_count=error_count,
            first_errors=errors[:5],
        )


def transcript_for_stop(payload: dict[str, Any], runtime: str, ident: dict[str, str]) -> Path | None:
    raw = payload.get("transcript_path")
    if not isinstance(raw, str) or not os.path.isabs(raw):
        return None
    lexical = Path(os.path.abspath(raw))
    if lexical.is_symlink():
        return None
    root_override = os.environ.get("HOOK_OBSERVATIONS_TRANSCRIPT_ROOT")
    if root_override:
        root_lexical = Path(os.path.abspath(root_override))
    elif runtime == "claude":
        root_lexical = (Path.home() / ".claude/projects").absolute()
    else:
        root_lexical = (Path.home() / ".codex/sessions").absolute()
    try:
        root = root_lexical.resolve(strict=True)
        path = lexical.resolve(strict=True)
    except OSError:
        return None
    if not inside(lexical, root_lexical) or not inside(path, root) or not path.is_file():
        return None
    if runtime == "claude" and path.stem != ident["session"]:
        return None
    if runtime == "codex":
        matched = CODEX_ROLLOUT.fullmatch(path.name)
        if matched is None or matched.group("session") != ident["session"]:
            return None
    return path


def qualified_metrics(value: Any, ident: dict[str, str], transcript: Path) -> dict[str, int] | None:
    if not isinstance(value, dict):
        return None
    measured = value.get("identity")
    if not isinstance(measured, dict) or measured.get("matched") is not True:
        return None
    if measured.get("session_id") != ident["session"]:
        return None
    try:
        raw_path = measured.get("transcript_path")
        if not isinstance(raw_path, str) or not os.path.isabs(raw_path):
            return None
        measured_path = Path(raw_path).resolve(strict=True)
    except (OSError, RuntimeError):
        return None
    if measured_path != transcript:
        return None
    coverages = value.get("coverage")
    coverage = coverages.get("tool_calls") if isinstance(coverages, dict) else None
    outcome_coverage = coverages.get("outcome") if isinstance(coverages, dict) else None
    calls = value.get("tool_calls")
    if not isinstance(coverage, dict) or not isinstance(outcome_coverage, dict) or not isinstance(calls, dict):
        return None
    for item in (coverage, outcome_coverage):
        if item.get("qualified") is not True or item.get("scope") != "main":
            return None
        reasons = item.get("reasons")
        if not isinstance(reasons, list) or any(not isinstance(reason, str) for reason in reasons):
            return None
    expected = coverage.get("expected")
    observed = coverage.get("observed")
    rate = coverage.get("rate")
    if type(expected) is not int or expected <= 0 or type(observed) is not int or observed != expected:
        return None
    if isinstance(rate, bool) or not isinstance(rate, (int, float)) or not math.isfinite(rate) or rate != 1.0:
        return None
    outcome_expected = outcome_coverage.get("expected")
    outcome_observed = outcome_coverage.get("observed")
    outcome_rate = outcome_coverage.get("rate")
    if type(outcome_expected) is not int or type(outcome_observed) is not int:
        return None
    if outcome_expected != expected or outcome_observed != expected:
        return None
    if isinstance(outcome_rate, bool) or not isinstance(outcome_rate, (int, float)) or not math.isfinite(outcome_rate) or outcome_rate != 1.0:
        return None
    wanted = ("success", "failure", "rejection", "interruption", "unknown", "total")
    if any(type(calls.get(name)) is not int or calls[name] < 0 for name in wanted):
        return None
    if calls["unknown"] != 0:
        return None
    categories = ("success", "failure", "rejection", "interruption", "unknown")
    if calls["total"] != expected or calls["total"] != sum(calls[name] for name in categories):
        return None
    return {name: calls[name] for name in wanted}


def command_stop(payload: dict[str, Any], runtime: str) -> None:
    ident = identity(payload, runtime)
    if ident is None:
        emit("stop-suggestion", "unknown", "invalid_identity")
        return
    transcript = transcript_for_stop(payload, runtime, ident)
    if transcript is None:
        emit("stop-suggestion", "unknown", "transcript_identity_mismatch")
        return
    metrics_override = os.environ.get("HOOK_OBSERVATIONS_METRICS_SCRIPT")
    metrics = Path(metrics_override) if metrics_override else Path.home() / ".codex/scripts/session-metrics.py"
    if not metrics.is_file():
        emit("stop-suggestion", "unknown", "metrics_consumer_missing")
        return
    if payload.get("hook_event_name") not in {"Stop", "StopFailure"}:
        emit("stop-suggestion", "unknown", "unsupported_stop_event")
        return
    command = [
        sys.executable,
        str(metrics),
        "metrics",
        "--transcript",
        str(transcript),
        "--session-id",
        ident["session"],
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=15, check=False)
        measured = json.loads(result.stdout) if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        measured = None
    calls = qualified_metrics(measured, ident, transcript)
    if calls is None:
        emit("stop-suggestion", "unknown", "metrics_not_qualified")
        return
    if calls["failure"] == 0:
        return
    directory_override = os.environ.get("HOOK_OBSERVATIONS_SUGGEST_DIR")
    directory = Path(directory_override) if directory_override else Path.home() / ".claude/.local/harness-suggestions"
    record = base_record("stop-suggestion", ident)
    record.update({
        "transcript_digest": hashlib.sha256(str(transcript).encode()).hexdigest(),
        "tool_calls": calls,
        "reasons": ["structured_tool_failures"],
        "reviewed": False,
    })
    ok, _ = OwnedJson(directory, "suggestion", ident, "stop-suggestion", ident).update(lambda _previous: record)
    if not ok:
        emit("stop-suggestion", "unknown", "suggestion_preserved")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("compact", "observe", "typescript", "stop"))
    parser.add_argument("--runtime", choices=("claude", "codex"), required=True)
    args = parser.parse_args()
    payload = payload_from_stdin(args.command)
    if payload is None:
        return 0
    functions = {
        "compact": command_compact,
        "observe": command_observe,
        "typescript": command_typescript,
        "stop": command_stop,
    }
    try:
        functions[args.command](payload, args.runtime)
    except Exception:
        emit(args.command, "unknown", "operational_error")
    return 0


if __name__ == "__main__":
    sys.exit(main())
