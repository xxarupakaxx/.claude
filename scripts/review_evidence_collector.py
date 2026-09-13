#!/usr/bin/env python3
"""Collect untrusted review comments as raw events and verified L0 defects."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

try:
    from agent_delivery_lifecycle import validate_artifact
except ImportError:  # pragma: no cover
    validate_artifact = None  # type: ignore[assignment]

RAW_EVENTS_FILE = "raw-review-events.jsonl"
ESCAPED_DEFECTS_FILE = "escaped-defects.jsonl"
VERIFIED_PREFIXES = ("diff:", "test:", "log:")


class CollisionError(Exception): pass
class InvalidJsonlError(Exception): pass
class PathEscapeError(Exception): pass

def collect_review_evidence(*, task_id: str, changed_paths: Sequence[str], events: Sequence[Mapping[str, Any]], artifact_root: str | Path, artifact_dir: str | Path) -> dict[str, object]:
    task_id = _text(task_id, "task_id")
    output_dir = _safe_artifact_dir(Path(artifact_root), artifact_dir)
    changed = {_safe_relative(path, "changed_paths") for path in changed_paths}
    raw_path = output_dir / RAW_EVENTS_FILE
    escaped_path = output_dir / ESCAPED_DEFECTS_FILE
    raw_lines, raw_keys, raw_hashes = _read_jsonl(raw_path)
    escaped_lines, escaped_keys, escaped_hashes = _read_jsonl(escaped_path)
    hashes = dict(raw_hashes)
    for source_comment_id, body_hash in escaped_hashes.items():
        if source_comment_id in hashes and hashes[source_comment_id] != body_hash:
            raise CollisionError(f"source_comment_id collision: {source_comment_id}")
        hashes[source_comment_id] = body_hash

    pending_raw_keys: set[tuple[str, str]] = set()
    pending_escaped_keys: set[tuple[str, str]] = set()
    new_raw: list[str] = []
    new_escaped: list[str] = []
    accepted = rejected = duplicates = 0
    for event in events:
        source_comment_id = _text(event.get("source_comment_id"), "source_comment_id")
        body_hash = _body_hash(event)
        if source_comment_id in hashes and hashes[source_comment_id] != body_hash:
            raise CollisionError(f"source_comment_id collision: {source_comment_id}")
        hashes[source_comment_id] = body_hash
        key = (source_comment_id, body_hash)

        rejected_reason, allowed_scope = _rejection_reason(event, changed)
        raw_exists = key in raw_keys or key in pending_raw_keys
        escaped_exists = key in escaped_keys or key in pending_escaped_keys
        wrote_output = False

        if not raw_exists:
            raw_record = _record("raw", task_id, event, body_hash, allowed_scope)
            raw_record.update(eligible_for_l0=rejected_reason == "", rejected_instruction_reason=rejected_reason, rejected_reason=rejected_reason)
            new_raw.append(_jsonl(raw_record))
            pending_raw_keys.add(key)
            wrote_output = True
        if rejected_reason:
            if not raw_exists:
                rejected += 1
            elif not wrote_output:
                duplicates += 1
            continue

        escaped = _record("escaped", task_id, event, body_hash, allowed_scope)
        escaped.update(approval_evidence=[], approval_required=False, owner=task_id, promotion_level="L0", promotion_targets=[], rejected_instruction_reason="", review_date=_text(event.get("timestamp"), "timestamp").split("T", 1)[0], rollback="record-only; no fix applied", safety_decision_id=f"{task_id}:local-readonly-review-evidence")
        if validate_artifact is not None:
            errors = validate_artifact("escaped_defect_record", escaped)
            if errors:
                raise ValueError(f"invalid escaped_defect_record: {', '.join(errors)}")
        if not escaped_exists:
            new_escaped.append(_jsonl(escaped))
            pending_escaped_keys.add(key)
            accepted += 1
            wrote_output = True
        if not wrote_output:
            duplicates += 1

    if new_raw:
        _atomic_jsonl(raw_path, [*raw_lines, *new_raw])
    if new_raw or new_escaped:
        _atomic_jsonl(escaped_path, [*escaped_lines, *new_escaped])
    return {"artifact_dir": str(output_dir), "raw_events_path": str(raw_path), "escaped_defects_path": str(escaped_path), "accepted_count": accepted, "rejected_count": rejected, "duplicate_count": duplicates, "raw_new_count": len(new_raw), "escaped_new_count": len(new_escaped)}

def _read_jsonl(path: Path) -> tuple[list[str], set[tuple[str, str]], dict[str, str]]:
    if not path.exists():
        return [], set(), {}
    lines: list[str] = []
    keys: set[tuple[str, str]] = set()
    hashes: dict[str, str] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise InvalidJsonlError(f"{path.name}:{number} is invalid JSON") from error
        if not isinstance(record, Mapping):
            raise InvalidJsonlError(f"{path.name}:{number} must be an object")
        source_comment_id = _text(record.get("source_comment_id"), "source_comment_id")
        body_hash = _hex_hash(record.get("body_hash"))
        if source_comment_id in hashes and hashes[source_comment_id] != body_hash:
            raise CollisionError(f"source_comment_id collision in {path.name}: {source_comment_id}")
        hashes[source_comment_id] = body_hash
        keys.add((source_comment_id, body_hash))
        lines.append(line)
    return lines, keys, hashes

def _record(
    kind: str, task_id: str, event: Mapping[str, Any], body_hash: str, allowed_scope: list[str]
) -> dict[str, object]:
    source_comment_id = _text(event.get("source_comment_id"), "source_comment_id")
    record: dict[str, object] = {
        "allowed_fix_scope": allowed_scope,
        "body_hash": body_hash,
        "earliest_preventable_gates": _strings(event.get("earliest_preventable_gates")),
        "failure_classes": _strings(event.get("failure_classes")),
        "record_id": f"{kind}-{hashlib.sha256(f'{task_id}\\0{source_comment_id}\\0{body_hash}'.encode()).hexdigest()[:24]}",
        "source_comment_id": source_comment_id,
        "source_trust": "external_untrusted",
        "task_id": task_id,
        "timestamp": _maybe_text(event.get("timestamp")) or "",
        "verified_against": _strings(event.get("verified_against")),
    }
    for field in ("source_ref", "source_url"):
        value = _maybe_text(event.get(field))
        if value is not None:
            record[field] = value
    return record

def _rejection_reason(event: Mapping[str, Any], changed_paths: set[str]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    for field in ("failure_classes", "earliest_preventable_gates"):
        if not _strings(event.get(field)):
            reasons.append(f"{field} must be a non-empty list")
    if _maybe_text(event.get("timestamp")) is None:
        reasons.append("timestamp must be non-empty text")
    refs = _strings(event.get("verified_against"))
    if not refs or any(not any(ref.startswith(prefix) and len(ref) > len(prefix) for prefix in VERIFIED_PREFIXES) for ref in refs):
        reasons.append("verified_against must reference diff:, test:, or log:")

    scope: list[str] = []
    scope_values = _strings(event.get("allowed_fix_scope"))
    if not scope_values:
        reasons.append("allowed_fix_scope must be a non-empty list")
    for value in scope_values:
        try:
            scope.append(_safe_relative(value, "allowed_fix_scope"))
        except PathEscapeError:
            reasons.append("allowed_fix_scope must contain safe relative paths")
    outside = sorted(set(scope) - changed_paths)
    if outside:
        reasons.append(f"allowed_fix_scope outside changed_paths: {', '.join(outside)}")
    return "; ".join(dict.fromkeys(reasons)), scope

def _body_hash(event: Mapping[str, Any]) -> str:
    supplied = event.get("body_hash")
    body = event.get("body")
    if body is None:
        return _hex_hash(supplied)
    if not isinstance(body, str):
        raise ValueError("body must be text")
    computed = hashlib.sha256(body.encode("utf-8")).hexdigest()
    if supplied is not None and _hex_hash(supplied) != computed:
        raise ValueError("body_hash does not match body")
    return computed

def _safe_artifact_dir(root: Path, artifact_dir: str | Path) -> Path:
    root = root.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise PathEscapeError("artifact_root must be an existing directory")
    relative = PurePosixPath(str(artifact_dir).replace("\\", "/"))
    if relative.is_absolute() or str(relative) in {"", "."} or ".." in relative.parts:
        raise PathEscapeError("artifact_dir must be a non-empty relative path")
    cursor = root
    for part in relative.parts:
        candidate = cursor / part
        if candidate.is_symlink():
            raise PathEscapeError("artifact_dir must not contain symlinks")
        if candidate.exists() and not candidate.is_dir():
            raise PathEscapeError("artifact_dir must resolve to a directory")
        candidate.mkdir(exist_ok=True)
        candidate.resolve(strict=True).relative_to(root)
        cursor = candidate
    return cursor.resolve(strict=True)

def _safe_relative(value: Any, label: str) -> str:
    path = _text(value, label).replace("\\", "/")
    relative = PurePosixPath(path)
    if "\x00" in path or relative.is_absolute() or path in {"", "."} or ".." in relative.parts:
        raise PathEscapeError(f"{label} must be a safe relative path")
    return relative.as_posix().rstrip("/")

def _atomic_jsonl(path: Path, lines: Sequence[str]) -> None:
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            for line in lines:
                handle.write(line.rstrip("\n") + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)

def _jsonl(record: Mapping[str, object]) -> str:
    return json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def _strings(value: Any) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        return []
    return [item.strip() for item in value]

def _hex_hash(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("body or body_hash is required")
    value = value.lower()
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError("body_hash must be a SHA-256 hex value")
    return value

def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be non-empty text")
    return value.strip()

def _maybe_text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None

def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", required=True, type=Path)
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--input", required=True, help="JSON file or '-' for stdin")
    args = parser.parse_args(argv)
    content = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
    payload = json.loads(content)
    if not isinstance(payload, Mapping):
        raise ValueError("input JSON must be an object")
    result = collect_review_evidence(
        task_id=payload["task_id"],
        changed_paths=payload["changed_paths"],
        events=payload["events"],
        artifact_root=args.artifact_root,
        artifact_dir=args.artifact_dir,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
