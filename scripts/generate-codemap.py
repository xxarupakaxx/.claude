#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_NAMES = {"codemap.json", "codemap.html", "codemap.lock"}


class CodemapValidationError(ValueError):
    pass


class CodemapStateError(RuntimeError):
    pass


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def json_text(value: object, *, compact: bool = False) -> str:
    if compact:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def require_object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CodemapValidationError(f"{label} must be an object")
    return value


def require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CodemapValidationError(f"{label} must be non-empty text")
    return value.strip()


def relative_path(value: object, label: str) -> str:
    path = require_text(value, label).replace("\\", "/")
    pure = PurePosixPath(path)
    if pure.is_absolute() or ".." in pure.parts or path in {".", ""}:
        raise CodemapValidationError(f"{label} must be a repo-relative path")
    return pure.as_posix()


def path_in_root(root: Path, relative: str, label: str) -> Path:
    target = root.joinpath(*PurePosixPath(relative).parts)
    try:
        target.resolve(strict=False).relative_to(root.resolve())
    except ValueError as error:
        raise CodemapValidationError(f"{label} must stay inside the repo") from error
    if target.is_symlink():
        raise CodemapValidationError(f"{label} must not be a symlink")
    return target


def validate_evidence(root: Path, edge_id: str, evidence: object) -> None:
    item = require_object(evidence, f"edge {edge_id} evidence")
    relative = relative_path(item.get("path"), f"edge {edge_id} evidence path")
    target = path_in_root(root, relative, f"edge {edge_id} evidence path")
    if not target.is_file():
        raise CodemapValidationError(
            f"edge {edge_id} evidence path {relative} does not exist"
        )
    line = item.get("line")
    if not isinstance(line, int) or isinstance(line, bool) or line < 1:
        raise CodemapValidationError(f"edge {edge_id} evidence line must be positive")
    lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
    line_count = len(lines)
    if line > line_count:
        raise CodemapValidationError(
            f"edge {edge_id} evidence line {line} is outside {relative}"
        )
    expected = require_text(
        item.get("contains"), f"edge {edge_id} evidence contains"
    )
    if expected not in lines[line - 1]:
        raise CodemapValidationError(
            f"edge {edge_id} evidence contains text was not found at {relative}:{line}"
        )


def validate_document(document: object, root: Path) -> dict[str, Any]:
    data = require_object(document, "codemap")
    if data.get("schemaVersion") != 1:
        raise CodemapValidationError("schemaVersion must be 1")
    require_text(data.get("title"), "title")

    scope = require_object(data.get("scope"), "scope")
    includes = scope.get("include")
    excludes = scope.get("exclude", [])
    if not isinstance(includes, list) or not includes:
        raise CodemapValidationError("scope.include must be a non-empty list")
    if not isinstance(excludes, list):
        raise CodemapValidationError("scope.exclude must be a list")
    for index, pattern in enumerate([*includes, *excludes]):
        relative_path(pattern, f"scope pattern {index + 1}")

    lanes = data.get("lanes")
    if not isinstance(lanes, list) or not lanes:
        raise CodemapValidationError("lanes must be a non-empty list")
    lane_ids: set[str] = set()
    for lane in lanes:
        item = require_object(lane, "lane")
        lane_id = require_text(item.get("id"), "lane id")
        if lane_id in lane_ids:
            raise CodemapValidationError(f"duplicate lane id: {lane_id}")
        lane_ids.add(lane_id)
        require_text(item.get("title"), f"lane {lane_id} title")

    nodes = data.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise CodemapValidationError("nodes must be a non-empty list")
    node_ids: set[str] = set()
    for node in nodes:
        item = require_object(node, "node")
        node_id = require_text(item.get("id"), "node id")
        if node_id in node_ids:
            raise CodemapValidationError(f"duplicate node id: {node_id}")
        node_ids.add(node_id)
        require_text(item.get("title"), f"node {node_id} title")
        lane_id = require_text(item.get("lane"), f"node {node_id} lane")
        if lane_id not in lane_ids:
            raise CodemapValidationError(f"node {node_id} uses unknown lane: {lane_id}")
        if item.get("path") is not None:
            relative_path(item["path"], f"node {node_id} path")

    edges = data.get("edges")
    if not isinstance(edges, list):
        raise CodemapValidationError("edges must be a list")
    edge_ids: set[str] = set()
    for edge in edges:
        item = require_object(edge, "edge")
        edge_id = require_text(item.get("id"), "edge id")
        if edge_id in edge_ids:
            raise CodemapValidationError(f"duplicate edge id: {edge_id}")
        edge_ids.add(edge_id)
        source = require_text(item.get("from"), f"edge {edge_id} from")
        target = require_text(item.get("to"), f"edge {edge_id} to")
        if source not in node_ids or target not in node_ids:
            raise CodemapValidationError(f"edge {edge_id} references an unknown node")
        require_text(item.get("relation"), f"edge {edge_id} relation")
        status = item.get("status")
        if status not in {"verified", "unknown"}:
            raise CodemapValidationError(
                f"edge {edge_id} status must be verified or unknown"
            )
        evidence = item.get("evidence", [])
        if not isinstance(evidence, list):
            raise CodemapValidationError(f"edge {edge_id} evidence must be a list")
        if status == "verified" and not evidence:
            raise CodemapValidationError(f"verified edge {edge_id} requires evidence")
        if status == "unknown" and not str(item.get("reason", "")).strip():
            raise CodemapValidationError(f"unknown edge {edge_id} requires a reason")
        for evidence_item in evidence:
            validate_evidence(root, edge_id, evidence_item)
    return data


def validate_generated_snapshot(document: object, root: Path) -> dict[str, Any]:
    data = validate_document(document, root)
    if data.get("version") != 1:
        raise CodemapValidationError("generated version must be 1")
    if data.get("kind") != "codemap":
        raise CodemapValidationError("generated kind must be codemap")
    require_text(data.get("generatedAt"), "generatedAt")
    fingerprint = require_text(data.get("sourceFingerprint"), "sourceFingerprint")
    if not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
        raise CodemapValidationError("sourceFingerprint must be a SHA-256 hex value")
    counts = require_object(data.get("counts"), "counts")
    expected_counts = {
        "lanes": len(data["lanes"]),
        "nodes": len(data["nodes"]),
        "edges": len(data["edges"]),
        "unknown": sum(edge.get("status") == "unknown" for edge in data["edges"]),
    }
    if any(
        not isinstance(counts.get(name), int)
        or isinstance(counts.get(name), bool)
        or counts.get(name) != value
        for name, value in expected_counts.items()
    ):
        raise CodemapValidationError("counts do not match lanes, nodes, and edges")
    return data


def validate_lock(document: object) -> dict[str, Any]:
    data = require_object(document, "codemap.lock")
    if data.get("schemaVersion") != 1 or data.get("kind") != "codemap-lock":
        raise CodemapValidationError("codemap.lock markers are invalid")
    require_text(data.get("generatedAt"), "lock generatedAt")
    require_text(data.get("sourceFile"), "lock sourceFile")
    for name in (
        "sourceSpecFingerprint",
        "sourceFingerprint",
        "mapFingerprint",
    ):
        fingerprint = require_text(data.get(name), f"lock {name}")
        if not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
            raise CodemapValidationError(f"lock {name} must be a SHA-256 hex value")
    if not isinstance(data.get("sourceManifest"), list):
        raise CodemapValidationError("lock sourceManifest must be a list")
    return data


def pattern_matches(path: str, pattern: str) -> bool:
    return fnmatch.fnmatchcase(path, pattern) or PurePosixPath(path).match(pattern)


def excluded_source(relative: str, excludes: list[str]) -> bool:
    name = PurePosixPath(relative).name
    if name in OUTPUT_NAMES:
        return True
    if name.startswith(".codemap.") and name.endswith(".tmp"):
        return True
    return any(pattern_matches(relative, pattern) for pattern in excludes)


def source_file_in_root(root: Path, path: Path) -> bool:
    try:
        relative = path.relative_to(root)
        path.resolve(strict=True).relative_to(root.resolve())
    except (OSError, ValueError):
        return False
    cursor = root
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink():
            return False
    return path.is_file()


def build_manifest(
    root: Path, scope: dict[str, Any], *, require_matches: bool
) -> list[dict[str, object]]:
    includes = [relative_path(item, "scope.include") for item in scope["include"]]
    excludes = [relative_path(item, "scope.exclude") for item in scope.get("exclude", [])]
    matched: dict[str, Path] = {}
    for pattern in includes:
        pattern_paths: list[Path] = []
        for path in root.glob(pattern):
            if not source_file_in_root(root, path):
                continue
            relative = path.relative_to(root).as_posix()
            if excluded_source(relative, excludes):
                continue
            pattern_paths.append(path)
            matched[relative] = path
        if require_matches and not pattern_paths:
            raise CodemapValidationError(f"scope pattern has no files: {pattern}")
    return [
        {
            "path": relative,
            "sha256": sha256_bytes(path.read_bytes()),
            "size": path.stat().st_size,
        }
        for relative, path in sorted(matched.items())
    ]


def manifest_fingerprint(manifest: list[dict[str, object]]) -> str:
    return sha256_bytes(json_text(manifest, compact=True).encode("utf-8"))


def source_relative(directory: Path, source: Path) -> str:
    try:
        return Path(os.path.abspath(source)).relative_to(
            Path(os.path.abspath(directory))
        ).as_posix()
    except ValueError as error:
        raise CodemapValidationError(
            "source spec must be inside the artifact directory"
        ) from error


def resolve_artifact_dir(root: Path, artifact_dir: Path | None) -> Path:
    workspace = Path(os.path.abspath(root))
    directory = Path(os.path.abspath(artifact_dir or workspace))
    try:
        directory.relative_to(workspace)
    except ValueError as error:
        raise CodemapValidationError(
            "artifact directory must be inside the repo"
        ) from error
    return directory


def refresh(
    root: Path,
    source: Path | None = None,
    *,
    artifact_dir: Path | None = None,
) -> dict[str, object]:
    root = Path(os.path.abspath(root))
    output_dir = resolve_artifact_dir(root, artifact_dir)
    source = Path(os.path.abspath(source or output_dir / "codemap.source.json"))
    source_name = source_relative(output_dir, source)
    source_bytes = source.read_bytes()
    try:
        draft = json.loads(source_bytes)
    except json.JSONDecodeError as error:
        raise CodemapValidationError(f"invalid JSON in {source_name}: {error}") from error
    validated = validate_document(draft, root)
    manifest = build_manifest(root, validated["scope"], require_matches=True)
    generated_at = datetime.now(timezone.utc).isoformat()
    source_fingerprint = manifest_fingerprint(manifest)
    snapshot = {
        **validated,
        "version": 1,
        "kind": "codemap",
        "generatedAt": generated_at,
        "sourceFingerprint": source_fingerprint,
        "counts": {
            "lanes": len(validated["lanes"]),
            "nodes": len(validated["nodes"]),
            "edges": len(validated["edges"]),
            "unknown": sum(
                edge.get("status") == "unknown" for edge in validated["edges"]
            ),
        },
    }
    map_content = json_text(snapshot)
    lock = {
        "schemaVersion": 1,
        "kind": "codemap-lock",
        "generatedAt": generated_at,
        "sourceFile": source_name,
        "sourceSpecFingerprint": sha256_bytes(source_bytes),
        "sourceFingerprint": source_fingerprint,
        "mapFingerprint": sha256_bytes(map_content.encode("utf-8")),
        "sourceManifest": manifest,
    }
    atomic_write(output_dir / "codemap.json", map_content)
    atomic_write(output_dir / "codemap.lock", json_text(lock))
    return lock


def read_required(path: Path) -> bytes:
    if not path.is_file():
        raise CodemapStateError(f"missing {path.name}")
    return path.read_bytes()


def check(
    root: Path,
    *,
    artifact_dir: Path | None = None,
) -> dict[str, object]:
    root = Path(os.path.abspath(root))
    output_dir = resolve_artifact_dir(root, artifact_dir)
    lock_bytes = read_required(output_dir / "codemap.lock")
    try:
        lock = validate_lock(json.loads(lock_bytes))
    except (json.JSONDecodeError, CodemapValidationError) as error:
        raise CodemapStateError("invalid codemap.lock") from error
    map_bytes = read_required(output_dir / "codemap.json")
    if sha256_bytes(map_bytes) != lock.get("mapFingerprint"):
        raise CodemapStateError("map fingerprint mismatch")

    source_name = relative_path(lock.get("sourceFile"), "lock sourceFile")
    source_path = path_in_root(output_dir, source_name, "lock sourceFile")
    source_bytes = read_required(source_path)
    if sha256_bytes(source_bytes) != lock.get("sourceSpecFingerprint"):
        raise CodemapStateError("source spec fingerprint mismatch")
    try:
        snapshot = validate_generated_snapshot(json.loads(map_bytes), root)
    except (json.JSONDecodeError, CodemapValidationError) as error:
        raise CodemapStateError(f"invalid codemap.json: {error}") from error
    if snapshot.get("generatedAt") != lock.get("generatedAt"):
        raise CodemapStateError("generated time mismatch")
    manifest = build_manifest(root, snapshot["scope"], require_matches=False)
    fingerprint = manifest_fingerprint(manifest)
    if fingerprint != lock.get("sourceFingerprint"):
        raise CodemapStateError("source fingerprint mismatch")
    if fingerprint != snapshot.get("sourceFingerprint"):
        raise CodemapStateError("snapshot source fingerprint mismatch")
    if manifest != lock.get("sourceManifest"):
        raise CodemapStateError("source manifest mismatch")
    return {
        "status": "fresh",
        "sourceFingerprint": fingerprint,
        "generatedAt": lock.get("generatedAt"),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate and verify Codemap map/lock artifacts")
    subparsers = parser.add_subparsers(dest="command", required=True)
    refresh_parser = subparsers.add_parser("refresh")
    refresh_parser.add_argument("--root", type=Path, default=Path.cwd())
    refresh_parser.add_argument("--input", type=Path)
    refresh_parser.add_argument("--artifact-dir", type=Path)
    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("--root", type=Path, default=Path.cwd())
    check_parser.add_argument("--artifact-dir", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "refresh":
            source = args.input
            if source is not None and not source.is_absolute():
                source = args.root / source
            artifact_dir = args.artifact_dir
            if artifact_dir is not None and not artifact_dir.is_absolute():
                artifact_dir = args.root / artifact_dir
            result = refresh(args.root, source, artifact_dir=artifact_dir)
            print(f"codemap: refreshed {result['sourceFingerprint']}")
        else:
            artifact_dir = args.artifact_dir
            if artifact_dir is not None and not artifact_dir.is_absolute():
                artifact_dir = args.root / artifact_dir
            result = check(args.root, artifact_dir=artifact_dir)
            print(f"codemap: fresh {result['sourceFingerprint']}")
    except (OSError, CodemapValidationError, CodemapStateError) as error:
        print(f"codemap: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
