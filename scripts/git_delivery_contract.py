#!/usr/bin/env python3
"""Read-only Git snapshots for evidence-bound commit and PR drafts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Sequence


SECRET_PATTERNS = (
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"AKIA[0-9A-Z]{16}"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(rb"glpat-[A-Za-z0-9_-]{20,}"),
    re.compile(rb"sk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
    re.compile(rb"xox[baprs]-[A-Za-z0-9-]{20,}"),
    re.compile(rb"(?i)bearer\s+[A-Za-z0-9._~+/-]{20,}"),
    re.compile(rb"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"),
    re.compile(rb"(?i)(?:api[_-]?key|secret|token|password)\s*[:=]\s*[^\s]{12,}"),
    re.compile(
        rb"(?i)(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^:/\s]+:[^@/\s]{4,}@"
    ),
)
SENSITIVE_FILE_NAMES = {".env", ".npmrc", ".pypirc", "credentials", "credentials.json"}
SENSITIVE_FILE_SUFFIXES = {".key", ".pem", ".p12", ".pfx"}
MAX_WORKER_PATCH_BYTES = 1024 * 1024


def _git(repo: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ["git", *arguments], cwd=repo, check=True, capture_output=True
    ).stdout


def _branch_name(repo: Path) -> str | None:
    result = subprocess.run(
        ["git", "symbolic-ref", "--quiet", "--short", "HEAD"],
        cwd=repo,
        check=False,
        capture_output=True,
    )
    return result.stdout.decode().strip() if result.returncode == 0 else None


def _bounded_git_diff(repo: Path, arguments: Sequence[str], limit: int) -> tuple[bytes, bool]:
    process = subprocess.Popen(
        ["git", "diff", *arguments],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdout is not None
    chunk = process.stdout.read(limit + 1)
    if len(chunk) > limit:
        process.kill()
        process.communicate()
        return chunk, True
    remainder, stderr = process.communicate()
    if process.returncode:
        raise subprocess.CalledProcessError(
            process.returncode, process.args, output=chunk + remainder, stderr=stderr
        )
    patch = chunk + remainder
    return patch, len(patch) > limit


def _nul_paths(value: bytes) -> list[str]:
    return sorted(
        item.decode("utf-8", errors="surrogateescape")
        for item in value.split(b"\0")
        if item
    )


def _name_status(value: bytes) -> list[dict[str, Any]]:
    tokens = [item for item in value.split(b"\0") if item]
    entries: list[dict[str, Any]] = []
    index = 0
    while index < len(tokens):
        status = tokens[index].decode("ascii", errors="replace")
        index += 1
        path_count = 2 if status.startswith(("R", "C")) else 1
        paths = [
            tokens[index + offset].decode("utf-8", errors="surrogateescape")
            for offset in range(path_count)
        ]
        index += path_count
        entries.append({"status": status, "paths": paths})
    return entries


def _source_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def validate_worker_patch(
    patch: Any,
    changed_paths: Sequence[str],
    *,
    max_patch_bytes: int = 64 * 1024,
) -> list[str]:
    if patch is None:
        return []
    if not isinstance(patch, str):
        return ["worker_patch must be text or null"]
    patch_bytes = patch.encode("utf-8")
    errors: list[str] = []
    if len(patch_bytes) > max_patch_bytes or max_patch_bytes > MAX_WORKER_PATCH_BYTES:
        errors.append("worker_patch exceeds size limit")
    if "\x00" in patch:
        errors.append("worker_patch contains binary content")
    if any(
        Path(path).name.lower() in SENSITIVE_FILE_NAMES
        or Path(path).suffix.lower() in SENSITIVE_FILE_SUFFIXES
        for path in changed_paths
    ) or any(pattern.search(patch_bytes) for pattern in SECRET_PATTERNS):
        errors.append("worker_patch contains secret-like content")
    return errors


def _collect_diff_snapshot(
    root: Path,
    *,
    source: dict[str, Any],
    prefix_args: Sequence[str] = (),
    revisions: Sequence[str] = (),
    allowed_paths: Sequence[str] | None = None,
    allow_deletes: bool = False,
    allow_renames: bool = False,
    max_patch_bytes: int = 64 * 1024,
    unmerged_paths: Sequence[str] = (),
) -> dict[str, Any]:
    def diff(*options: str) -> bytes:
        return _git(
            root,
            "diff",
            "--no-ext-diff",
            "--no-textconv",
            *prefix_args,
            *options,
            *revisions,
        )

    effective_limit = min(max(max_patch_bytes, 1), MAX_WORKER_PATCH_BYTES)
    patch_bytes, patch_too_large = _bounded_git_diff(
        root,
        (
            "--no-ext-diff",
            "--no-textconv",
            *prefix_args,
            "--binary",
            *revisions,
        ),
        effective_limit,
    )
    changed_paths = _nul_paths(diff("--name-only", "-z"))
    name_status = _name_status(diff("--name-status", "-z", "--find-renames"))
    numstat = diff("--numstat", "-z").decode("utf-8", errors="surrogateescape")
    all_diff_paths = sorted(
        set(changed_paths).union(
            path for entry in name_status for path in entry["paths"]
        )
    )
    contains_secret = "worker_patch contains secret-like content" in validate_worker_patch(
        patch_bytes.decode("utf-8", errors="replace"),
        all_diff_paths,
        max_patch_bytes=effective_limit,
    )
    contains_binary = any(line.startswith("-\t-\t") for line in numstat.split("\0"))
    allowed = set(allowed_paths) if allowed_paths is not None else None
    violations = []
    if allowed is None:
        violations.append("allowed_paths_required")
    else:
        violations.extend(
            f"path_not_allowed:{path}" for path in all_diff_paths if path not in allowed
        )
    if not changed_paths:
        violations.append("empty_diff")
    for entry in name_status:
        status, paths = entry["status"], entry["paths"]
        if status.startswith("D") and not allow_deletes:
            violations.append(f"delete_not_allowed:{paths[0]}")
        if status.startswith(("R", "C")) and not allow_renames:
            violations.append(f"rename_not_allowed:{' -> '.join(paths)}")
    violations.extend(f"unmerged:{path}" for path in unmerged_paths)
    if contains_secret:
        violations.append("secret_in_patch")
    if max_patch_bytes <= 0 or max_patch_bytes > MAX_WORKER_PATCH_BYTES:
        violations.append("max_patch_bytes_invalid")
    if patch_too_large:
        violations.append("patch_too_large")
    policy = {
        "allowed_paths": sorted(allowed_paths) if allowed_paths is not None else None,
        "allow_deletes": allow_deletes,
        "allow_renames": allow_renames,
        "max_patch_bytes": max_patch_bytes,
    }
    bound_source = {**source, "changed_paths": changed_paths, **policy}
    return {
        **bound_source,
        "source_hash": _source_hash(bound_source),
        "worker_patch": (
            patch_bytes.decode("utf-8", errors="replace")
            if not patch_too_large and not contains_secret and not contains_binary
            else None
        ),
        "name_status": name_status,
        "numstat": numstat,
        "violations": violations,
        "draft_status": "DRAFT_BLOCKED" if violations else "DRAFT_READY",
    }


def collect_staged_snapshot(
    repo: str | Path,
    *,
    allowed_paths: Sequence[str] | None = None,
    allow_deletes: bool = False,
    allow_renames: bool = False,
    max_patch_bytes: int = 64 * 1024,
) -> dict[str, Any]:
    """Collect only index-versus-HEAD evidence without modifying the repository."""
    root = Path(repo).resolve()
    source = {
        "mode": "staged",
        "repository_root": str(root),
        "branch": _branch_name(root),
        "head_sha": _git(root, "rev-parse", "HEAD").decode().strip(),
        "index_fingerprint": hashlib.sha256(_git(root, "ls-files", "--stage", "-z")).hexdigest(),
    }
    unmerged = _nul_paths(_git(root, "diff", "--name-only", "--diff-filter=U", "-z"))
    return _collect_diff_snapshot(
        root,
        source=source,
        prefix_args=("--cached",),
        allowed_paths=allowed_paths,
        allow_deletes=allow_deletes,
        allow_renames=allow_renames,
        max_patch_bytes=max_patch_bytes,
        unmerged_paths=unmerged,
    )


def collect_range_snapshot(
    repo: str | Path,
    *,
    base_sha: str,
    head_sha: str,
    allowed_paths: Sequence[str] | None = None,
    allow_deletes: bool = False,
    allow_renames: bool = False,
    max_patch_bytes: int = 64 * 1024,
) -> dict[str, Any]:
    """Collect an explicit base/head range without reading the worktree."""
    root = Path(repo).resolve()
    base = _git(root, "rev-parse", "--verify", f"{base_sha}^{{commit}}").decode().strip()
    head = _git(root, "rev-parse", "--verify", f"{head_sha}^{{commit}}").decode().strip()
    return _collect_diff_snapshot(
        root,
        source={
            "mode": "range",
            "repository_root": str(root),
            "base_sha": base,
            "head_sha": head,
        },
        revisions=(base, head),
        allowed_paths=allowed_paths,
        allow_deletes=allow_deletes,
        allow_renames=allow_renames,
        max_patch_bytes=max_patch_bytes,
    )


def validate_snapshot_fresh(
    repo: str | Path,
    snapshot: dict[str, Any],
    *,
    expected_source_hash: str,
    allowed_paths: Sequence[str] | None,
    allow_deletes: bool,
    allow_renames: bool,
    max_patch_bytes: int,
) -> dict[str, Any]:
    if allowed_paths is None:
        return {"status": "DRAFT_BLOCKED", "violations": ["allowed_paths_required"]}
    if snapshot.get("source_hash") != expected_source_hash:
        return {"status": "DRAFT_STALE", "current": None}
    expected_policy = {
        "allowed_paths": sorted(allowed_paths),
        "allow_deletes": allow_deletes,
        "allow_renames": allow_renames,
        "max_patch_bytes": max_patch_bytes,
    }
    current = collect_staged_snapshot(
        repo,
        allowed_paths=allowed_paths,
        allow_deletes=allow_deletes,
        allow_renames=allow_renames,
        max_patch_bytes=max_patch_bytes,
    )
    if any(snapshot.get(key) != value for key, value in expected_policy.items()):
        return {"status": "DRAFT_STALE", "current": _without_worker_patch(current)}
    if current["source_hash"] != snapshot.get("source_hash"):
        return {"status": "DRAFT_STALE", "current": _without_worker_patch(current)}
    return {
        "status": "DRAFT_BLOCKED" if current["violations"] else "READY",
        "current": _without_worker_patch(current),
    }


def validate_range_refs(
    repo: str | Path,
    snapshot: dict[str, Any],
    *,
    expected_source_hash: str,
    base_ref: str,
    head_ref: str,
    allowed_paths: Sequence[str] | None,
    allow_deletes: bool,
    allow_renames: bool,
    max_patch_bytes: int,
) -> dict[str, Any]:
    if allowed_paths is None:
        return {"status": "DRAFT_BLOCKED", "violations": ["allowed_paths_required"]}
    if snapshot.get("source_hash") != expected_source_hash:
        return {"status": "DRAFT_STALE", "current": None}
    root = Path(repo).resolve()
    base = _git(root, "rev-parse", "--verify", f"{base_ref}^{{commit}}").decode().strip()
    head = _git(root, "rev-parse", "--verify", f"{head_ref}^{{commit}}").decode().strip()
    current = collect_range_snapshot(
        root,
        base_sha=base,
        head_sha=head,
        allowed_paths=allowed_paths,
        allow_deletes=allow_deletes,
        allow_renames=allow_renames,
        max_patch_bytes=max_patch_bytes,
    )
    expected_policy = {
        "allowed_paths": sorted(allowed_paths),
        "allow_deletes": allow_deletes,
        "allow_renames": allow_renames,
        "max_patch_bytes": max_patch_bytes,
    }
    status = "READY"
    if base != snapshot.get("base_sha") or head != snapshot.get("head_sha"):
        status = "DRAFT_STALE"
    elif any(snapshot.get(key) != value for key, value in expected_policy.items()):
        status = "DRAFT_STALE"
    elif current["source_hash"] != snapshot.get("source_hash"):
        status = "DRAFT_STALE"
    elif current.get("violations"):
        status = "DRAFT_BLOCKED"
    return {
        "status": status,
        "base_sha": base,
        "head_sha": head,
        "current": _without_worker_patch(current),
    }


def _add_policy_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--allowed-path", action="append", dest="allowed_paths")
    parser.add_argument("--allow-delete", action="store_true")
    parser.add_argument("--allow-rename", action="store_true")
    parser.add_argument("--max-patch-bytes", type=int, default=64 * 1024)


def _add_snapshot_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("repo")
    _add_policy_options(parser)


def _options(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "allowed_paths": args.allowed_paths,
        "allow_deletes": args.allow_delete,
        "allow_renames": args.allow_rename,
        "max_patch_bytes": args.max_patch_bytes,
    }


def _read_json(path: str) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("snapshot must be a JSON object")
    return value


def _without_worker_patch(snapshot: dict[str, Any]) -> dict[str, Any]:
    persistent = dict(snapshot)
    patch = persistent.get("worker_patch")
    persistent["worker_patch_sha256"] = (
        hashlib.sha256(patch.encode("utf-8")).hexdigest()
        if isinstance(patch, str)
        else None
    )
    persistent["worker_patch"] = None
    return persistent


def main() -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    staged = commands.add_parser("staged")
    _add_snapshot_options(staged)
    staged.add_argument("--include-worker-patch", action="store_true")
    ranged = commands.add_parser("range")
    _add_snapshot_options(ranged)
    ranged.add_argument("--include-worker-patch", action="store_true")
    ranged.add_argument("--base", required=True)
    ranged.add_argument("--head", required=True)
    check_staged = commands.add_parser("check-staged")
    check_staged.add_argument("repo")
    check_staged.add_argument("snapshot")
    check_staged.add_argument("--expected-source-hash", required=True)
    _add_policy_options(check_staged)
    check_range = commands.add_parser("check-range")
    check_range.add_argument("repo")
    check_range.add_argument("snapshot")
    check_range.add_argument("--expected-source-hash", required=True)
    check_range.add_argument("--base-ref", required=True)
    check_range.add_argument("--head-ref", required=True)
    _add_policy_options(check_range)
    args = parser.parse_args()

    try:
        if args.command == "staged":
            result = collect_staged_snapshot(args.repo, **_options(args))
            status = result["draft_status"]
            if not args.include_worker_patch:
                result = _without_worker_patch(result)
        elif args.command == "range":
            result = collect_range_snapshot(
                args.repo, base_sha=args.base, head_sha=args.head, **_options(args)
            )
            status = result["draft_status"]
            if not args.include_worker_patch:
                result = _without_worker_patch(result)
        elif args.command == "check-staged":
            result = validate_snapshot_fresh(
                args.repo,
                _read_json(args.snapshot),
                expected_source_hash=args.expected_source_hash,
                **_options(args),
            )
            status = result["status"]
        else:
            result = validate_range_refs(
                args.repo,
                _read_json(args.snapshot),
                expected_source_hash=args.expected_source_hash,
                base_ref=args.base_ref,
                head_ref=args.head_ref,
                **_options(args),
            )
            status = result["status"]
    except (subprocess.CalledProcessError, OSError, ValueError, json.JSONDecodeError):
        result = {
            "draft_status": "DRAFT_BLOCKED",
            "violations": ["git_contract_error"],
        }
        status = "DRAFT_BLOCKED"
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if status in {"DRAFT_READY", "READY"} else 3


if __name__ == "__main__":
    raise SystemExit(main())
