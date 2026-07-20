#!/usr/bin/env python3
"""Read-only governance utilities for third-party Agent Skills.

This module never installs, updates, promotes, retires, or deletes a skill.
Exit codes: 0 = completed, 2 = blocking findings, 3 = configuration/dependency error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import re
import ssl
import stat
import subprocess
import sys
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = 1
LOCK_SCHEMA_VERSION = 1
CATALOG_SCHEMA_VERSION = 1
ESTATE_SCHEMA_VERSION = 2
REPUTATION_SCHEMA_VERSION = 1
HASH_ALGORITHM = "skill-tree-sha256-v1"
MAX_FILES = 2_048
MAX_FILE_BYTES = 4 * 1024 * 1024
MAX_TOTAL_BYTES = 32 * 1024 * 1024
MAX_DIRECTORIES = 2_048
MAX_DEPTH = 64
MAX_GITHUB_RESPONSE = 32 * 1024 * 1024
MAX_YAML_EVENTS = 2_048
MAX_YAML_DEPTH = 32
BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = BASE_DIR / "registry.toml"
DEFAULT_LOCK = BASE_DIR / "registry.lock.json"
DEFAULT_CATALOG = BASE_DIR / "catalog.lock.json"
DEFAULT_ESTATE = BASE_DIR / "estate.lock.json"
DEFAULT_REPUTATION = BASE_DIR / "reputation.lock.json"

VALID_STATES = {
    "watch",
    "quarantined",
    "reviewed",
    "approved",
    "active",
    "legacy-active",
    "update-available",
    "rejected",
    "deprecated",
    "retired",
    "revoked",
}
VALID_ADAPTATIONS = {"shared-identical", "platform-adapted", "single-target"}
CANDIDATE_STATES = {"quarantined", "reviewed", "approved", "active", "update-available", "deprecated"}
REVIEW_STATES = {"reviewed", "approved", "active", "update-available", "deprecated"}
RUNTIME_STATES = {"active", "legacy-active", "update-available", "deprecated"}
APPROVAL_LINEAGE_STATES = {"approved", "active", "update-available", "deprecated"}
APPROVED_RUNTIME_STATES = {"active", "update-available", "deprecated"}
GITHUB_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
BRANCH_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._/-]*[A-Za-z0-9._-])?$")
KEY_RE = re.compile(r"^[A-Za-z0-9_-]+$")
VALID_SOURCE_ORIGINS = {"community-maintainer", "open-standard", "vendor-official", "vendor-security-tool"}
VALID_SOURCE_MODES = {"distribution-reference", "optional-scanner", "selective-adoption", "specification", "watch"}
ARCHIVE_SUFFIXES = {
    ".7z",
    ".bz2",
    ".gz",
    ".jar",
    ".rar",
    ".tar",
    ".tgz",
    ".whl",
    ".xz",
    ".zip",
}
CODE_SUFFIXES = {".bash", ".js", ".mjs", ".py", ".rb", ".sh", ".ts", ".zsh"}
COMMON_FRONTMATTER_KEYS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}
CLAUDE_FRONTMATTER_KEYS = COMMON_FRONTMATTER_KEYS | {
    "argument-hint",
    "disable-model-invocation",
    "user-invocable",
    "model",
    "context",
    "agent",
    "hooks",
}
FULL_YAML_SUPERSEDED_CODES = {
    "frontmatter_tab",
    "frontmatter_nested",
    "frontmatter_unverified",
}

CANONICAL_OPENAI_ADAPTER = (
    b'interface:\n'
    b'  display_name: "Skill Governance"\n'
    b'  short_description: "Inspect and govern third-party Agent Skills safely"\n'
    b'  default_prompt: "Audit the Agent Skill estate without making changes."\n'
    b'policy:\n'
    b'  allow_implicit_invocation: false\n'
)


class StrictJSONError(ValueError):
    """Raised when JSON uses semantics outside the governance subset."""


def _strict_json_loads(raw: bytes | str) -> Any:
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "strict")

    def object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise StrictJSONError(f"duplicate JSON key: {key}")
            value[key] = item
        return value

    def reject_constant(value: str) -> Any:
        raise StrictJSONError(f"non-finite JSON number: {value}")

    return json.loads(raw, object_pairs_hook=object_pairs, parse_constant=reject_constant)


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    path: str = ""


@dataclass
class FileRecord:
    path: str
    size: int
    executable: bool
    sha256: str
    data: bytes = field(repr=False)

    def public(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "size": self.size,
            "executable": self.executable,
            "sha256": self.sha256,
        }


@dataclass
class TreeResult:
    root: str
    tree_sha256: str | None
    files: list[FileRecord]
    findings: list[Finding]


def blocker(code: str, message: str, path: str = "") -> Finding:
    return Finding("BLOCKING", code, message, path)


def advisory(code: str, message: str, path: str = "") -> Finding:
    return Finding("ADVISORY", code, message, path)


def has_blockers(findings: Iterable[Finding]) -> bool:
    return any(item.severity == "BLOCKING" for item in findings)


def expand_path(value: str | Path) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(str(value))))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _git_object_sha1(kind: bytes, data: bytes) -> str:
    return hashlib.sha1(kind + b" " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    return _git_object_sha1(b"blob", data)


def git_tree_sha1(files: Iterable[FileRecord]) -> str:
    """Reproduce a Git tree object SHA from a captured regular-file manifest."""
    root: dict[bytes, Any] = {}
    for record in files:
        try:
            parts = tuple(part.encode("utf-8", "strict") for part in Path(record.path).parts)
        except UnicodeEncodeError as exc:
            raise ValueError(f"non-UTF-8 Git path: {record.path}") from exc
        if not parts or any(part in {b"", b".", b".."} or b"/" in part or b"\0" in part for part in parts):
            raise ValueError(f"invalid Git path: {record.path}")
        node = root
        for part in parts[:-1]:
            existing = node.setdefault(part, {})
            if not isinstance(existing, dict):
                raise ValueError(f"Git path collides with a file: {record.path}")
            node = existing
        if parts[-1] in node:
            raise ValueError(f"duplicate Git path: {record.path}")
        node[parts[-1]] = record

    def hash_directory(node: dict[bytes, Any]) -> str:
        entries: list[tuple[bytes, bool, bytes, str]] = []
        for name, value in node.items():
            if isinstance(value, dict):
                entries.append((name, True, b"40000", hash_directory(value)))
            else:
                mode = b"100755" if value.executable else b"100644"
                entries.append((name, False, mode, git_blob_sha1(value.data)))
        entries.sort(key=lambda item: item[0] + (b"/" if item[1] else b""))
        body = b"".join(mode + b" " + name + b"\0" + bytes.fromhex(sha) for name, _, mode, sha in entries)
        return _git_object_sha1(b"tree", body)

    return hash_directory(root)


def _length_prefix(value: bytes) -> bytes:
    return len(value).to_bytes(8, "big") + value


def _secure_traversal_supported() -> bool:
    return bool(
        os.name == "posix"
        and getattr(os, "O_NOFOLLOW", 0)
        and getattr(os, "O_DIRECTORY", 0)
        and os.open in os.supports_dir_fd
        and os.scandir in os.supports_fd
        and os.stat in os.supports_dir_fd
        and os.stat in os.supports_follow_symlinks
    )


def _directory_snapshot(info: os.stat_result) -> tuple[int, int, int, int, int]:
    return (info.st_dev, info.st_ino, info.st_mode, info.st_mtime_ns, info.st_ctime_ns)


def _file_snapshot(info: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _open_root_directory(path: Path) -> tuple[int | None, os.stat_result | None, Finding | None]:
    if not _secure_traversal_supported():
        return None, None, blocker(
            "secure_traversal_unsupported",
            "FD-anchored no-follow traversal is unavailable; no path-based fallback is allowed",
            str(path),
        )
    path = path.absolute()
    try:
        expected = path.lstat()
    except OSError as exc:
        return None, None, blocker("root_unavailable", str(exc), str(path))
    if stat.S_ISLNK(expected.st_mode):
        return None, None, blocker("root_symlink", "Root must not be a symlink", str(path))
    if not stat.S_ISDIR(expected.st_mode):
        return None, None, blocker("root_not_directory", "Root is not a directory", str(path))
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        return None, None, blocker("root_open_failed", str(exc), str(path))
    opened = os.fstat(fd)
    if not stat.S_ISDIR(opened.st_mode) or _directory_snapshot(opened) != _directory_snapshot(expected):
        os.close(fd)
        return None, None, blocker("toctou_root_identity", "Root changed while it was opened", str(path))
    return fd, opened, None


def _open_child_directory_at(
    parent_fd: int,
    name: str,
    expected: os.stat_result,
    relative: str,
) -> tuple[int | None, Finding | None]:
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(name, flags, dir_fd=parent_fd)
    except OSError as exc:
        return None, blocker("directory_open_failed", str(exc), relative)
    opened = os.fstat(fd)
    if not stat.S_ISDIR(opened.st_mode) or _directory_snapshot(opened) != _directory_snapshot(expected):
        os.close(fd)
        return None, blocker("toctou_directory_identity", "Directory changed while it was opened", relative)
    return fd, None


def _read_regular_file_at(
    parent_fd: int,
    name: str,
    expected: os.stat_result,
    relative: str,
) -> tuple[bytes | None, Finding | None]:
    flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(name, flags, dir_fd=parent_fd)
    except OSError as exc:
        return None, blocker("file_open_failed", f"Could not open regular file: {exc}", relative)
    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode):
            return None, blocker("toctou_file_type", "File type changed while opening", relative)
        if _file_snapshot(opened) != _file_snapshot(expected):
            return None, blocker("toctou_file_identity", "File changed while it was opened", relative)
        if opened.st_size > MAX_FILE_BYTES:
            return None, blocker("file_too_large", f"File exceeds {MAX_FILE_BYTES} bytes", relative)
        chunks: list[bytes] = []
        remaining = MAX_FILE_BYTES + 1
        while remaining:
            chunk = os.read(fd, min(1024 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        after = os.fstat(fd)
        if len(data) > MAX_FILE_BYTES:
            return None, blocker("file_too_large", "File grew beyond the size limit", relative)
        if _file_snapshot(opened) != _file_snapshot(after):
            return None, blocker("toctou_changed", "File changed while it was being read", relative)
        return data, None
    finally:
        os.close(fd)


def _capture_regular_file_at(
    parent_fd: int,
    name: str,
    expected: os.stat_result,
    relative: str,
) -> tuple[bytes | None, os.stat_result | None, int | None, Finding | None]:
    """Capture one file and keep its fd open for end-of-tree revalidation."""
    flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(name, flags, dir_fd=parent_fd)
    except OSError as exc:
        return None, None, None, blocker("file_open_failed", f"Could not open regular file: {exc}", relative)
    opened = os.fstat(fd)
    if not stat.S_ISREG(opened.st_mode):
        os.close(fd)
        return None, None, None, blocker("toctou_file_type", "File type changed while opening", relative)
    if _file_snapshot(opened) != _file_snapshot(expected):
        os.close(fd)
        return None, None, None, blocker("toctou_file_identity", "File changed while it was opened", relative)
    if opened.st_size > MAX_FILE_BYTES:
        os.close(fd)
        return None, None, None, blocker("file_too_large", f"File exceeds {MAX_FILE_BYTES} bytes", relative)
    try:
        chunks: list[bytes] = []
        remaining = MAX_FILE_BYTES + 1
        while remaining:
            chunk = os.read(fd, min(1024 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        after = os.fstat(fd)
        if len(data) > MAX_FILE_BYTES:
            os.close(fd)
            return None, None, None, blocker("file_too_large", "File grew beyond the size limit", relative)
        if _file_snapshot(opened) != _file_snapshot(after):
            os.close(fd)
            return None, None, None, blocker("toctou_changed", "File changed while it was being read", relative)
        return data, after, fd, None
    except BaseException:
        os.close(fd)
        raise


def _read_regular_file(path: Path, expected: os.stat_result) -> tuple[bytes | None, Finding | None]:
    parent = Path(os.path.realpath(path.parent))
    parent_fd, _, finding = _open_root_directory(parent)
    if finding or parent_fd is None:
        return None, finding or blocker("file_parent_unavailable", "Parent directory unavailable", str(path))
    try:
        return _read_regular_file_at(parent_fd, path.name, expected, str(path))
    finally:
        os.close(parent_fd)


def _tree_hash(records: list[FileRecord], findings: list[Finding]) -> str | None:
    if has_blockers(findings):
        return None
    digest = hashlib.sha256()
    digest.update((HASH_ALGORITHM + "\0").encode("ascii"))
    for record in records:
        for part in (
            b"file",
            record.path.encode("utf-8"),
            b"1" if record.executable else b"0",
            bytes.fromhex(record.sha256),
        ):
            digest.update(_length_prefix(part))
    return digest.hexdigest()


def _scan_tree_fd(root_fd: int, display_root: str) -> TreeResult:
    findings: list[Finding] = []
    records: list[FileRecord] = []
    total_bytes = 0
    directory_count = 0
    captured_fds: list[tuple[int, os.stat_result, str]] = []
    captured_directories: list[tuple[int, os.stat_result, str]] = []
    owned_directory_fds: list[int] = []

    def walk(directory_fd: int, parts: tuple[str, ...], depth: int) -> None:
        nonlocal total_bytes, directory_count
        directory_count += 1
        relative_directory = "/".join(parts) or "."
        before = os.fstat(directory_fd)
        captured_directories.append((directory_fd, before, relative_directory))
        if directory_count > MAX_DIRECTORIES:
            findings.append(blocker("too_many_directories", f"Tree exceeds {MAX_DIRECTORIES} directories", relative_directory))
            return
        if depth > MAX_DEPTH:
            findings.append(blocker("tree_too_deep", f"Tree exceeds depth {MAX_DEPTH}", relative_directory))
            return
        try:
            with os.scandir(directory_fd) as iterator:
                entries = sorted(iterator, key=lambda entry: os.fsencode(entry.name))
        except OSError as exc:
            findings.append(blocker("directory_read_failed", str(exc), relative_directory))
            return
        for entry in entries:
            try:
                entry.name.encode("utf-8", "strict")
            except UnicodeEncodeError:
                findings.append(blocker("non_utf8_path", "Path is not strict UTF-8", relative_directory))
                continue
            relative = "/".join((*parts, entry.name))
            try:
                info = os.stat(entry.name, dir_fd=directory_fd, follow_symlinks=False)
            except OSError as exc:
                findings.append(blocker("lstat_failed", str(exc), relative))
                continue
            mode = info.st_mode
            if stat.S_ISLNK(mode):
                findings.append(blocker("symlink", "Symlinks are not followed or accepted", relative))
                continue
            if stat.S_ISDIR(mode):
                if entry.name == ".git":
                    findings.append(blocker("embedded_git", "Embedded .git directory is not accepted", relative))
                    continue
                child_fd, open_finding = _open_child_directory_at(directory_fd, entry.name, info, relative)
                if open_finding or child_fd is None:
                    findings.append(open_finding or blocker("directory_open_failed", "Directory unavailable", relative))
                    continue
                owned_directory_fds.append(child_fd)
                walk(child_fd, (*parts, entry.name), depth + 1)
                continue
            if not stat.S_ISREG(mode):
                findings.append(blocker("special_file", "Only regular files and directories are accepted", relative))
                continue
            if len(records) >= MAX_FILES:
                findings.append(blocker("too_many_files", f"Tree exceeds {MAX_FILES} files", relative))
                continue
            data, captured, file_fd, read_finding = _capture_regular_file_at(directory_fd, entry.name, info, relative)
            if read_finding:
                findings.append(read_finding)
                continue
            assert data is not None and captured is not None and file_fd is not None
            captured_fds.append((file_fd, captured, relative))
            total_bytes += len(data)
            if total_bytes > MAX_TOTAL_BYTES:
                findings.append(blocker("tree_too_large", f"Tree exceeds {MAX_TOTAL_BYTES} bytes", relative))
                continue
            records.append(
                FileRecord(
                    path=relative,
                    size=len(data),
                    executable=bool(info.st_mode & 0o111),
                    sha256=sha256_bytes(data),
                    data=data,
                )
            )
        after = os.fstat(directory_fd)
        if _directory_snapshot(before) != _directory_snapshot(after):
            findings.append(blocker("directory_changed", "Directory changed while it was scanned", relative_directory))

    try:
        walk(root_fd, (), 0)
        for file_fd, captured, relative in captured_fds:
            try:
                current = os.fstat(file_fd)
            except OSError as exc:
                findings.append(blocker("toctou_revalidation_failed", str(exc), relative))
                continue
            if _file_snapshot(current) != _file_snapshot(captured):
                findings.append(blocker("toctou_changed_after_read", "File changed after capture and before tree finalization", relative))
        for directory_fd, captured, relative in captured_directories:
            try:
                current = os.fstat(directory_fd)
            except OSError as exc:
                findings.append(blocker("toctou_directory_revalidation_failed", str(exc), relative))
                continue
            if _directory_snapshot(current) != _directory_snapshot(captured):
                findings.append(
                    blocker(
                        "toctou_directory_changed_after_scan",
                        "Directory changed after capture and before tree finalization",
                        relative,
                    )
                )
    finally:
        for file_fd, _, _ in captured_fds:
            try:
                os.close(file_fd)
            except OSError:
                pass
        for directory_fd in reversed(owned_directory_fds):
            try:
                os.close(directory_fd)
            except OSError:
                pass
    records.sort(key=lambda record: record.path.encode("utf-8"))
    return TreeResult(display_root, _tree_hash(records, findings), records, findings)


def scan_tree(root: Path) -> TreeResult:
    root = root.absolute()
    root_fd, _, finding = _open_root_directory(root)
    if finding or root_fd is None:
        return TreeResult(str(root), None, [], [finding or blocker("root_unavailable", "Root unavailable", str(root))])
    try:
        return _scan_tree_fd(root_fd, str(root))
    finally:
        os.close(root_fd)


def _scan_canonical_tree(root: Path, parts: tuple[str, ...], display_root: str, scope: str) -> TreeResult:
    """Scan a canonical child while retaining and revalidating its complete path chain."""
    opened: list[tuple[int, os.stat_result, str]] = []
    root_fd, root_snapshot, finding = _open_root_directory(root)
    if finding or root_fd is None or root_snapshot is None:
        return TreeResult(
            display_root,
            None,
            [],
            [finding or blocker(f"{scope}_root_unavailable", "Canonical root unavailable", str(root))],
        )
    opened.append((root_fd, root_snapshot, "."))
    try:
        current_fd = root_fd
        for index, part in enumerate(parts):
            relative_part = "/".join(parts[: index + 1])
            try:
                expected = os.stat(part, dir_fd=current_fd, follow_symlinks=False)
            except OSError as exc:
                return TreeResult(
                    display_root,
                    None,
                    [],
                    [blocker(f"{scope}_component_unavailable", str(exc), relative_part)],
                )
            if stat.S_ISLNK(expected.st_mode) or not stat.S_ISDIR(expected.st_mode):
                return TreeResult(
                    display_root,
                    None,
                    [],
                    [
                        blocker(
                            f"{scope}_component_type",
                            "Every canonical component must be a real directory",
                            relative_part,
                        )
                    ],
                )
            child_fd, open_finding = _open_child_directory_at(current_fd, part, expected, relative_part)
            if open_finding or child_fd is None:
                return TreeResult(
                    display_root,
                    None,
                    [],
                    [open_finding or blocker(f"{scope}_component_unavailable", "Component unavailable", relative_part)],
                )
            opened.append((child_fd, os.fstat(child_fd), relative_part))
            current_fd = child_fd

        tree = _scan_tree_fd(current_fd, display_root)
        findings = list(tree.findings)

        for fd, snapshot, relative_part in opened:
            try:
                current = os.fstat(fd)
            except OSError as exc:
                findings.append(blocker("canonical_path_revalidation_failed", str(exc), relative_part))
                continue
            if _directory_snapshot(current) != _directory_snapshot(snapshot):
                findings.append(
                    blocker(
                        "canonical_path_changed",
                        "Canonical ancestor changed before tree finalization",
                        relative_part,
                    )
                )

        reopened: list[tuple[int, os.stat_result, str]] = []
        check_fd, check_snapshot, check_finding = _open_root_directory(root)
        if check_finding or check_fd is None or check_snapshot is None:
            findings.append(
                check_finding
                or blocker("canonical_path_unavailable_after_scan", "Canonical root unavailable after scan", str(root))
            )
        else:
            reopened.append((check_fd, check_snapshot, "."))
            try:
                if _directory_snapshot(check_snapshot) != _directory_snapshot(opened[0][1]):
                    findings.append(blocker("canonical_path_replaced", "Canonical root identity changed during scan", str(root)))
                current_check_fd = check_fd
                for index, part in enumerate(parts):
                    relative_part = "/".join(parts[: index + 1])
                    try:
                        expected = os.stat(part, dir_fd=current_check_fd, follow_symlinks=False)
                    except OSError as exc:
                        findings.append(blocker("canonical_path_unavailable_after_scan", str(exc), relative_part))
                        break
                    if stat.S_ISLNK(expected.st_mode) or not stat.S_ISDIR(expected.st_mode):
                        findings.append(
                            blocker(
                                "canonical_path_replaced",
                                "Canonical component is no longer a real directory",
                                relative_part,
                            )
                        )
                        break
                    child_fd, open_finding = _open_child_directory_at(
                        current_check_fd,
                        part,
                        expected,
                        relative_part,
                    )
                    if open_finding or child_fd is None:
                        findings.append(
                            open_finding
                            or blocker("canonical_path_unavailable_after_scan", "Component unavailable", relative_part)
                        )
                        break
                    child_snapshot = os.fstat(child_fd)
                    reopened.append((child_fd, child_snapshot, relative_part))
                    if _directory_snapshot(child_snapshot) != _directory_snapshot(opened[index + 1][1]):
                        findings.append(
                            blocker(
                                "canonical_path_replaced",
                                "Canonical component identity changed during scan",
                                relative_part,
                            )
                        )
                    current_check_fd = child_fd

                for index, (fd, snapshot, relative_part) in enumerate(reopened):
                    try:
                        if index == 0:
                            mapped = root.lstat()
                        else:
                            mapped = os.stat(parts[index - 1], dir_fd=reopened[index - 1][0], follow_symlinks=False)
                    except OSError as exc:
                        findings.append(blocker("canonical_path_revalidation_failed", str(exc), relative_part))
                        continue
                    if stat.S_ISLNK(mapped.st_mode) or _directory_snapshot(mapped) != _directory_snapshot(snapshot):
                        findings.append(
                            blocker(
                                "canonical_path_replaced",
                                "Canonical path mapping changed during final revalidation",
                                relative_part,
                            )
                        )
            finally:
                for fd, _, _ in reversed(reopened):
                    try:
                        os.close(fd)
                    except OSError:
                        pass

        return TreeResult(display_root, _tree_hash(tree.files, findings), tree.files, findings)
    finally:
        for fd, _, _ in reversed(opened):
            try:
                os.close(fd)
            except OSError:
                pass


def scan_quarantined_tree(candidate: Path, quarantine_root: Path) -> TreeResult:
    raw_parts = candidate.parts
    if ".." in raw_parts:
        return TreeResult(str(candidate), None, [], [blocker("quarantine_path_escape", "Candidate path contains ..", str(candidate))])
    quarantine = Path(os.path.abspath(str(quarantine_root)))
    absolute = Path(os.path.abspath(str(candidate)))
    try:
        common = Path(os.path.commonpath((str(quarantine), str(absolute))))
        relative = absolute.relative_to(quarantine)
    except (ValueError, OSError):
        return TreeResult(str(absolute), None, [], [blocker("quarantine_path_escape", "Candidate is outside quarantine", str(absolute))])
    if common != quarantine or absolute == quarantine:
        return TreeResult(str(absolute), None, [], [blocker("quarantine_path_escape", "Candidate must be below quarantine", str(absolute))])
    parts = relative.parts
    if (
        len(parts) != 3
        or not NAME_RE.fullmatch(parts[0])
        or not SHA_RE.fullmatch(parts[1])
        or not NAME_RE.fullmatch(parts[2])
    ):
        return TreeResult(
            str(absolute),
            None,
            [],
            [blocker("quarantine_layout", "Expected <source-id>/<40-char-sha>/<skill-name>", str(relative))],
        )
    return _scan_canonical_tree(quarantine, parts, str(absolute), "quarantine")


def scan_reviewed_tree(
    collection_id: str,
    skill_name: str,
    target: str,
    review_root: Path,
) -> TreeResult:
    parts = (collection_id, skill_name, target)
    if any(not NAME_RE.fullmatch(part) for part in parts):
        return TreeResult(
            str(review_root.joinpath(*parts)),
            None,
            [],
            [blocker("review_layout", "Expected canonical <collection-id>/<skill-name>/<target>", "/".join(parts))],
        )
    root = Path(os.path.abspath(str(review_root)))
    absolute = root.joinpath(*parts)
    return _scan_canonical_tree(root, parts, str(absolute), "review")


def _decode_strict_scalar(value: str) -> tuple[Any | None, str | None]:
    stripped = value.strip()
    if not stripped:
        return None, "empty values and nested mappings require full YAML validation"
    if stripped[0] in "|>&*!{[" or stripped.startswith("<<:"):
        return None, "multiline, anchor, alias, tag, merge, or flow syntax requires full YAML validation"
    if "\t" in stripped or " #" in stripped or ": " in stripped:
        return None, "ambiguous scalar syntax requires full YAML validation"
    if stripped.startswith('"'):
        if not stripped.endswith('"'):
            return None, "unterminated double-quoted scalar"
        try:
            decoded = json.loads(stripped)
        except json.JSONDecodeError as exc:
            return None, f"unsupported double-quoted scalar: {exc}"
        if not isinstance(decoded, str):
            return None, "quoted scalar must decode to a string"
        return decoded, None
    if stripped.startswith("'"):
        if not stripped.endswith("'"):
            return None, "unterminated single-quoted scalar"
        return stripped[1:-1].replace("''", "'"), None
    if stripped == "true":
        return True, None
    if stripped == "false":
        return False, None
    return stripped, None


def parse_frontmatter_strict(data: bytes, path: str = "SKILL.md") -> tuple[dict[str, Any], list[Finding]]:
    findings: list[Finding] = []
    try:
        text = data.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        return {}, [blocker("frontmatter_non_utf8", str(exc), path)]
    if "\t" in text:
        findings.append(blocker("frontmatter_tab", "Tabs require full YAML validation", path))
    if any(ord(char) < 32 and char not in "\n\r\t" for char in text):
        findings.append(blocker("frontmatter_control_character", "Control character in SKILL.md", path))
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return {}, findings + [blocker("frontmatter_missing", "SKILL.md must start with ---", path)]
    try:
        end = lines.index("---", 1)
    except ValueError:
        return {}, findings + [blocker("frontmatter_unclosed", "Frontmatter closing --- is missing", path)]
    values: dict[str, Any] = {}
    for line_number, line in enumerate(lines[1:end], start=2):
        if not line or line.lstrip().startswith("#"):
            continue
        if line[0].isspace():
            findings.append(
                blocker(
                    "frontmatter_nested",
                    "Nested mapping or multiline content requires full YAML validation",
                    f"{path}:{line_number}",
                )
            )
            continue
        if ":" not in line:
            findings.append(blocker("frontmatter_syntax", "Expected key: value", f"{path}:{line_number}"))
            continue
        key, raw_value = line.split(":", 1)
        if not KEY_RE.fullmatch(key):
            findings.append(blocker("frontmatter_key", f"Unsupported key syntax: {key}", f"{path}:{line_number}"))
            continue
        if key in values:
            findings.append(blocker("frontmatter_duplicate_key", f"Duplicate key: {key}", f"{path}:{line_number}"))
            continue
        value, error = _decode_strict_scalar(raw_value)
        if error:
            findings.append(blocker("frontmatter_unverified", error, f"{path}:{line_number}"))
            continue
        values[key] = value
    return values, findings


def _bound_ref_valid(value: Any, directory: str) -> bool:
    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        return False
    path = value.get("path")
    digest = value.get("sha256")
    if not isinstance(path, str) or not isinstance(digest, str):
        return False
    candidate = Path(path)
    return (
        not candidate.is_absolute()
        and len(candidate.parts) >= 2
        and candidate.parts[0] == directory
        and ".." not in candidate.parts
        and re.fullmatch(r"[0-9a-f]{64}", digest) is not None
    )


def _receipt_ref_valid(value: Any) -> bool:
    return _bound_ref_valid(value, "receipts")


def _valid_date_string(value: Any) -> bool:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        return datetime.fromisoformat(value).date().isoformat() == value
    except ValueError:
        return False


def load_registry(path: Path) -> tuple[dict[str, Any], list[Finding]]:
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return {}, [blocker("registry_unreadable", str(exc), str(path))]
    return data, validate_registry(data)


def validate_registry(data: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    if data.get("schema_version") != SCHEMA_VERSION:
        findings.append(blocker("registry_schema", f"Expected schema_version {SCHEMA_VERSION}"))
    generation = data.get("generation")
    if not isinstance(generation, int) or generation < 1:
        findings.append(blocker("registry_generation", "generation must be a positive integer"))
    if data.get("authority") != "codex":
        findings.append(blocker("registry_authority", "authority must be codex until the ADR is superseded"))
    if data.get("hash_algorithm") != HASH_ALGORITHM:
        findings.append(blocker("registry_hash_algorithm", f"hash_algorithm must be {HASH_ALGORITHM}"))
    quarantine_value = data.get("quarantine_root")
    if not isinstance(quarantine_value, str) or not quarantine_value:
        findings.append(blocker("registry_quarantine", "quarantine_root must be a non-empty path"))
    review_value = data.get("review_root")
    if not isinstance(review_value, str) or not review_value:
        findings.append(blocker("registry_review_root", "review_root must be a non-empty path"))
    policy = data.get("policy")
    if not isinstance(policy, dict):
        findings.append(blocker("registry_policy", "policy table is required"))
    else:
        for key in ("auto_install", "auto_update", "auto_retire", "auto_delete", "candidate_code_execution"):
            if policy.get(key) is not False:
                findings.append(blocker("unsafe_policy", f"{key} must be false"))
        if policy.get("promotion_requires_human_approval") is not True:
            findings.append(blocker("approval_policy", "promotion_requires_human_approval must be true"))

    coverage_policy = data.get("coverage_policy")
    if not isinstance(coverage_policy, dict):
        findings.append(blocker("coverage_policy", "coverage_policy table is required"))
    else:
        if not isinstance(coverage_policy.get("scope_bases"), list) or not coverage_policy.get("scope_bases"):
            findings.append(blocker("coverage_scope_bases", "scope_bases must be a non-empty array"))
        excluded_dir_names = coverage_policy.get("excluded_dir_names")
        excluded_dir_reasons = coverage_policy.get("excluded_dir_reasons")
        if not isinstance(excluded_dir_names, list):
            findings.append(blocker("coverage_excluded_names", "excluded_dir_names must be an array"))
        if (
            not isinstance(excluded_dir_reasons, dict)
            or not isinstance(excluded_dir_names, list)
            or set(excluded_dir_reasons) != set(excluded_dir_names)
            or any(not isinstance(reason, str) or not reason for reason in excluded_dir_reasons.values())
        ):
            findings.append(blocker("coverage_excluded_reasons", "Every excluded directory name needs an explicit reason"))
    exclusions = data.get("coverage_exclusions")
    if not isinstance(exclusions, list):
        findings.append(blocker("coverage_exclusions", "coverage_exclusions must be an array"))
    else:
        for index, exclusion in enumerate(exclusions):
            if (
                not isinstance(exclusion, dict)
                or not isinstance(exclusion.get("path"), str)
                or not isinstance(exclusion.get("reason"), str)
                or not exclusion.get("reason")
            ):
                findings.append(blocker("coverage_exclusion_shape", "Every exclusion needs path and reason", str(index)))

    roots = data.get("roots")
    if not isinstance(roots, list) or not roots:
        findings.append(blocker("registry_roots", "At least one root is required"))
        roots = []
    root_ids: set[str] = set()
    for root in roots:
        if not isinstance(root, dict) or not isinstance(root.get("id"), str):
            findings.append(blocker("registry_root_shape", "Each root needs a string id"))
            continue
        root_id = root["id"]
        if root_id in root_ids:
            findings.append(blocker("duplicate_root_id", f"Duplicate root id: {root_id}"))
        root_ids.add(root_id)
        if not isinstance(root.get("path"), str) or not isinstance(root.get("runtimes"), list):
            findings.append(blocker("registry_root_fields", f"Invalid root fields: {root_id}"))
        if not isinstance(root.get("precedence"), int):
            findings.append(blocker("registry_root_precedence", f"Missing integer precedence: {root_id}"))
        if root.get("scan_mode") not in {"direct", "recursive"}:
            findings.append(blocker("registry_root_scan_mode", f"Invalid scan_mode: {root_id}"))
        if root.get("collision_scope") not in {"runtime", "namespaced", "catalog-only"}:
            findings.append(blocker("registry_root_collision_scope", f"Invalid collision_scope: {root_id}"))
        if root.get("namespace_mode") not in {"none", "plugin", "root"}:
            findings.append(blocker("registry_root_namespace", f"Invalid namespace_mode: {root_id}"))
        if not isinstance(root.get("targetable"), bool):
            findings.append(blocker("registry_root_targetable", f"targetable must be boolean: {root_id}"))
        if not isinstance(root.get("required"), bool):
            findings.append(blocker("registry_root_required", f"required must be boolean: {root_id}"))

    symlink_paths: set[str] = set()
    for entry in data.get("coverage_symlinks", []):
        path = entry.get("path") if isinstance(entry, dict) else None
        root_id = entry.get("root_id") if isinstance(entry, dict) else None
        if (
            not isinstance(path, str)
            or not path
            or path in symlink_paths
            or root_id not in root_ids
            or not isinstance(entry.get("expected_target"), str)
            or not isinstance(entry.get("reason"), str)
            or not entry.get("reason")
            or not isinstance(entry.get("allow_missing_target"), bool)
        ):
            findings.append(blocker("coverage_symlink_shape", f"Invalid symlink allowlist entry: {path}"))
            continue
        symlink_paths.add(path)
        root = next((item for item in roots if isinstance(item, dict) and item.get("id") == root_id), {})
        if root.get("collision_scope") == "runtime":
            findings.append(blocker("coverage_symlink_runtime", f"Runtime symlinks cannot be allowlisted: {path}"))

    inference_keys: set[tuple[str, str]] = set()
    for entry in data.get("name_inferences", []):
        root_id = entry.get("root_id") if isinstance(entry, dict) else None
        relative_path = entry.get("relative_path") if isinstance(entry, dict) else None
        inferred_name = entry.get("inferred_name") if isinstance(entry, dict) else None
        key = (str(root_id), str(relative_path))
        if (
            root_id not in root_ids
            or key in inference_keys
            or not isinstance(relative_path, str)
            or not relative_path
            or not isinstance(inferred_name, str)
            or not NAME_RE.fullmatch(inferred_name)
            or not re.fullmatch(r"[0-9a-f]{64}", str(entry.get("tree_sha256", "")))
            or not isinstance(entry.get("reason"), str)
            or not entry.get("reason")
        ):
            findings.append(blocker("name_inference_shape", f"Invalid name inference: {key}"))
            continue
        inference_keys.add(key)
        root = next((item for item in roots if isinstance(item, dict) and item.get("id") == root_id), {})
        if root.get("collision_scope") != "runtime":
            findings.append(blocker("name_inference_scope", f"Name inference is only valid for runtime collision roots: {key}"))

    normalization_keys: set[tuple[str, str]] = set()
    allowed_control_files = {"estate.lock.json", "reputation.lock.json"}
    expected_normalizations = {("codex", "skill-governance"), ("claude", "skill-governance"), ("vault-codex", "skill-governance")}
    for entry in data.get("estate_hash_normalizations", []):
        root_id = entry.get("root_id") if isinstance(entry, dict) else None
        relative_path = entry.get("relative_path") if isinstance(entry, dict) else None
        files = entry.get("files") if isinstance(entry, dict) else None
        key = (str(root_id), str(relative_path))
        root = next((item for item in roots if isinstance(item, dict) and item.get("id") == root_id), {})
        if (
            key in normalization_keys
            or key not in expected_normalizations
            or root.get("collision_scope") != "runtime"
            or not isinstance(relative_path, str)
            or not relative_path
            or relative_path.startswith("/")
            or ".." in Path(relative_path).parts
            or not isinstance(files, list)
            or not files
            or set(files) != allowed_control_files
            or len(files) != len(set(files))
            or not isinstance(entry.get("reason"), str)
            or not entry.get("reason")
        ):
            findings.append(blocker("estate_hash_normalization", f"Invalid control-file normalization: {key}"))
            continue
        normalization_keys.add(key)
    if normalization_keys != expected_normalizations:
        findings.append(
            blocker(
                "estate_hash_normalization_coverage",
                f"Control-file normalization must be exactly {sorted(expected_normalizations)}",
            )
        )

    if isinstance(quarantine_value, str) and quarantine_value and isinstance(review_value, str) and review_value:
        quarantine = Path(os.path.realpath(expand_path(quarantine_value)))
        review_root = Path(os.path.realpath(expand_path(review_value)))
        if quarantine == review_root or _is_relative_to(quarantine, review_root) or _is_relative_to(review_root, quarantine):
            findings.append(blocker("review_quarantine_overlap", "Review staging and quarantine roots must be disjoint"))
        for root in roots:
            if not isinstance(root, dict) or root.get("collision_scope") != "runtime" or not isinstance(root.get("path"), str):
                continue
            runtime_root = Path(os.path.realpath(expand_path(root["path"])))
            if quarantine == runtime_root or _is_relative_to(quarantine, runtime_root) or _is_relative_to(runtime_root, quarantine):
                findings.append(blocker("quarantine_runtime_overlap", "Quarantine and runtime roots must be disjoint", root.get("id", "")))
            if review_root == runtime_root or _is_relative_to(review_root, runtime_root) or _is_relative_to(runtime_root, review_root):
                findings.append(blocker("review_runtime_overlap", "Review staging and runtime roots must be disjoint", root.get("id", "")))

    sources = data.get("sources")
    if not isinstance(sources, list):
        findings.append(blocker("registry_sources", "sources must be an array"))
        sources = []
    source_ids: set[str] = set()
    expected_source_keys = {
        "id",
        "github",
        "default_branch",
        "observed_revision",
        "observed_at",
        "origin",
        "mode",
        "update_policy",
        "catalog_required",
    }
    for source in sources:
        source_id = source.get("id") if isinstance(source, dict) else None
        if not isinstance(source, dict) or set(source) != expected_source_keys or not isinstance(source_id, str):
            findings.append(blocker("registry_source_shape", "Each source needs a string id"))
            continue
        if source_id in source_ids:
            findings.append(blocker("duplicate_source_id", f"Duplicate source id: {source_id}"))
        source_ids.add(source_id)
        if not GITHUB_RE.fullmatch(str(source.get("github", ""))):
            findings.append(blocker("source_github", f"Invalid GitHub owner/repo: {source_id}"))
        if not SHA_RE.fullmatch(str(source.get("observed_revision", ""))):
            findings.append(blocker("source_revision", f"Invalid observed revision: {source_id}"))
        branch = source.get("default_branch")
        if (
            not isinstance(branch, str)
            or not BRANCH_RE.fullmatch(branch)
            or branch.startswith("/")
            or branch.endswith("/")
            or ".." in branch.split("/")
            or "//" in branch
        ):
            findings.append(blocker("source_default_branch", f"Invalid default branch: {source_id}"))
        if not _valid_date_string(source.get("observed_at")):
            findings.append(blocker("source_observed_at", f"observed_at must be YYYY-MM-DD: {source_id}"))
        if source.get("origin") not in VALID_SOURCE_ORIGINS:
            findings.append(blocker("source_origin", f"Invalid source origin: {source_id}"))
        if source.get("mode") not in VALID_SOURCE_MODES:
            findings.append(blocker("source_mode", f"Invalid source mode: {source_id}"))
        if source.get("update_policy") != "notify-only":
            findings.append(blocker("source_update_policy", f"Source must be notify-only: {source_id}"))
        if source.get("catalog_required") is not True:
            findings.append(blocker("source_catalog_policy", f"catalog_required must be true: {source_id}"))

    reputation_policy = data.get("reputation_policy")
    if (
        not isinstance(reputation_policy, dict)
        or reputation_policy.get("popularity_is_approval") is not False
        or reputation_policy.get("approval_use") != "advisory-only"
        or not isinstance(reputation_policy.get("snapshot_document"), str)
        or not str(reputation_policy.get("snapshot_document", "")).startswith("references/")
        or reputation_policy.get("snapshot_data") != "reputation.lock.json"
    ):
        findings.append(blocker("reputation_policy", "Reputation must be a dated advisory signal and never an approval proxy"))

    collections = data.get("collections")
    if not isinstance(collections, list):
        findings.append(blocker("registry_collections", "collections must be an array"))
        collections = []
    collection_ids: set[str] = set()
    local_names: set[str] = set()
    for collection in collections:
        collection_id = collection.get("id") if isinstance(collection, dict) else None
        if not isinstance(collection_id, str) or not NAME_RE.fullmatch(collection_id):
            findings.append(blocker("collection_shape", "Each collection needs a string id"))
            continue
        if collection_id in collection_ids:
            findings.append(blocker("duplicate_collection_id", f"Duplicate collection id: {collection_id}"))
        collection_ids.add(collection_id)
        if collection.get("source_id") not in source_ids:
            findings.append(blocker("collection_source", f"Unknown source in {collection_id}"))
        state = collection.get("local_state")
        if state not in VALID_STATES:
            findings.append(blocker("collection_state", f"Unknown lifecycle state in {collection_id}: {state}"))
        adaptation = collection.get("adaptation")
        if adaptation not in VALID_ADAPTATIONS:
            findings.append(blocker("collection_adaptation", f"Invalid adaptation in {collection_id}: {adaptation}"))
        revision = collection.get("default_revision")
        if not isinstance(revision, str) or not SHA_RE.fullmatch(revision):
            findings.append(blocker("collection_revision", f"default_revision must be a full commit SHA: {collection_id}"))
        overrides = collection.get("revision_overrides", {})
        if not isinstance(overrides, dict) or any(
            not isinstance(name, str)
            or name not in set(collection.get("skills", []))
            or not isinstance(value, str)
            or not SHA_RE.fullmatch(value)
            for name, value in (overrides.items() if isinstance(overrides, dict) else [])
        ):
            findings.append(blocker("collection_revision_overrides", f"revision_overrides must map names to commit SHAs: {collection_id}"))
        if collection.get("risk_tier") not in {"unclassified", "L0", "L1", "L2", "L3"}:
            findings.append(blocker("collection_risk_tier", f"Invalid risk_tier: {collection_id}"))
        if not isinstance(collection.get("license"), str) or not collection.get("license"):
            findings.append(blocker("collection_license", f"license is required: {collection_id}"))
        if not _valid_date_string(collection.get("baseline_at")):
            findings.append(blocker("collection_baseline_date", f"baseline_at must be YYYY-MM-DD: {collection_id}"))
        targets = collection.get("targets")
        if not isinstance(targets, list) or not targets or any(target not in root_ids for target in targets):
            findings.append(blocker("collection_targets", f"Invalid targets in {collection_id}"))
        else:
            targetable = {
                root["id"]
                for root in roots
                if isinstance(root, dict) and root.get("targetable") is True
            }
            if any(target not in targetable for target in targets):
                findings.append(blocker("collection_untargetable_root", f"Collection targets non-targetable root: {collection_id}"))
            if adaptation == "single-target" and len(targets) != 1:
                findings.append(blocker("single_target_cardinality", f"single-target requires exactly one target: {collection_id}"))
            if adaptation in {"shared-identical", "platform-adapted"} and len(targets) < 2:
                findings.append(blocker("multi_target_cardinality", f"{adaptation} requires at least two targets: {collection_id}"))
        skills = collection.get("skills")
        if not isinstance(skills, list) or not skills:
            findings.append(blocker("collection_skills", f"No skills in {collection_id}"))
            continue
        for name in skills:
            if not isinstance(name, str) or not NAME_RE.fullmatch(name):
                findings.append(blocker("collection_skill_name", f"Invalid skill name in {collection_id}: {name}"))
                continue
            key = f"{collection_id}/{name}"
            if key in local_names:
                findings.append(blocker("duplicate_artifact_id", f"Duplicate artifact: {key}"))
            local_names.add(key)
        if state in CANDIDATE_STATES:
            upstream_paths = collection.get("upstream_paths")
            if (
                not isinstance(upstream_paths, dict)
                or set(upstream_paths) != set(skills)
                or any(
                    not isinstance(path, str)
                    or posixpath.basename(path) != "SKILL.md"
                    or path.startswith("/")
                    or ".." in Path(path).parts
                    for path in upstream_paths.values()
                )
            ):
                findings.append(blocker("candidate_upstream_paths", f"Candidate state must map every local skill to one catalog SKILL.md path: {collection_id}"))
        if state in REVIEW_STATES:
            frontmatter_receipts = collection.get("frontmatter_receipts")
            if not isinstance(frontmatter_receipts, dict) or set(frontmatter_receipts) != set(skills):
                findings.append(blocker("frontmatter_receipt_map", f"Review state must map every skill to validation receipts: {collection_id}"))
            else:
                expected_surfaces = {"quarantine", *(targets if isinstance(targets, list) else [])}
                for name, references in frontmatter_receipts.items():
                    if (
                        not isinstance(references, dict)
                        or set(references) != expected_surfaces
                        or any(not _receipt_ref_valid(reference) for reference in references.values())
                    ):
                        findings.append(blocker("frontmatter_receipt_map", f"Invalid frontmatter receipt surfaces for {collection_id}/{name}"))
        if state in APPROVAL_LINEAGE_STATES:
            if collection.get("review_state") != "approved":
                findings.append(blocker("approved_review_state", f"Approved state requires review_state=approved: {collection_id}"))
            if collection.get("risk_tier") == "unclassified":
                findings.append(blocker("approved_risk_unclassified", f"Approved state needs a classified risk tier: {collection_id}"))
            if collection.get("risk_tier") in {"L2", "L3"}:
                findings.append(blocker("approved_risk_no_go", f"{collection.get('risk_tier')} cannot use the standard approval path: {collection_id}"))
            if not _bound_ref_valid(collection.get("adaptation_diff"), "adaptations"):
                findings.append(blocker("approved_adaptation_diff", f"Approved state must bind an adaptations/* artifact by SHA-256: {collection_id}"))
            for field_name in ("safety_receipt", "approval_receipt", "value_receipt"):
                if not _receipt_ref_valid(collection.get(field_name)):
                    findings.append(blocker("invalid_receipt_reference", f"{field_name} must be a bound receipts/*.json reference: {collection_id}"))
            if state in APPROVED_RUNTIME_STATES and not _receipt_ref_valid(collection.get("promotion_receipt")):
                findings.append(blocker("invalid_receipt_reference", f"promotion_receipt is required for runtime approval-lineage state: {collection_id}"))
        if state == "legacy-active" and collection.get("review_state") != "evidence-gap":
            findings.append(blocker("legacy_review_state", f"legacy-active must keep evidence-gap: {collection_id}"))

    relation_ids: set[str] = set()
    for relation in data.get("route_relations", []):
        relation_id = relation.get("id") if isinstance(relation, dict) else None
        if not isinstance(relation_id, str) or not relation_id:
            findings.append(blocker("route_relation_shape", "Each route relation needs a string id"))
            continue
        if relation_id in relation_ids:
            findings.append(blocker("duplicate_route_relation", f"Duplicate route relation: {relation_id}"))
        relation_ids.add(relation_id)
        members = relation.get("members")
        routing = relation.get("routing")
        if not isinstance(members, list) or len(members) < 2 or any(not isinstance(item, str) for item in members):
            findings.append(blocker("route_relation_members", f"Invalid members: {relation_id}"))
        if not isinstance(routing, list) or len(routing) != len(members or []):
            findings.append(blocker("route_relation_routing", f"Routing must cover every member: {relation_id}"))

    local_origin_names: set[str] = set()
    for origin in data.get("local_origins", []):
        name = origin.get("name") if isinstance(origin, dict) else None
        if not isinstance(name, str) or not NAME_RE.fullmatch(name):
            findings.append(blocker("local_origin_name", f"Invalid local origin name: {name}"))
            continue
        if name in local_origin_names:
            findings.append(blocker("duplicate_local_origin", f"Duplicate local origin: {name}"))
        local_origin_names.add(name)
        commit = str(origin.get("historical_origin_commit", ""))
        if not SHA_RE.fullmatch(commit):
            findings.append(blocker("local_origin_commit", f"Invalid historical commit: {name}"))

    hold_ids: set[str] = set()
    for hold in data.get("holds", []):
        hold_id = hold.get("id") if isinstance(hold, dict) else None
        if not isinstance(hold_id, str) or not hold_id:
            findings.append(blocker("hold_shape", "Each hold needs a string id"))
            continue
        if hold_id in hold_ids:
            findings.append(blocker("duplicate_hold", f"Duplicate hold: {hold_id}"))
        hold_ids.add(hold_id)
        if not isinstance(hold.get("repo"), str) or not isinstance(hold.get("paths"), list) or not hold.get("paths"):
            findings.append(blocker("hold_fields", f"Hold needs repo and paths: {hold_id}"))
        if hold.get("policy") != "block-mutation":
            findings.append(blocker("hold_policy", f"Hold policy must be block-mutation: {hold_id}"))
        applies = hold.get("applies_to_roots")
        if not isinstance(applies, list) or any(root_id not in root_ids for root_id in applies):
            findings.append(blocker("hold_roots", f"Hold references unknown roots: {hold_id}"))

    parity = data.get("parity")
    if not isinstance(parity, dict):
        findings.append(blocker("parity_config", "parity table is required"))
    else:
        for key in ("authority_package", "replica_package", "shared_paths", "adapter_paths", "shared_repo_paths"):
            if key not in parity:
                findings.append(blocker("parity_config", f"Missing parity field: {key}"))
        checks = parity.get("integration_checks")
        if not isinstance(checks, list) or not checks:
            findings.append(blocker("parity_integration_checks", "integration_checks must be non-empty"))
        else:
            for check in checks:
                if (
                    not isinstance(check, dict)
                    or not isinstance(check.get("codex_path"), str)
                    or not isinstance(check.get("claude_path"), str)
                    or not isinstance(check.get("start_marker"), str)
                    or not check.get("start_marker")
                    or not isinstance(check.get("end_marker"), str)
                    or not check.get("end_marker")
                    or not re.fullmatch(r"[0-9a-f]{64}", str(check.get("sha256", "")))
                ):
                    findings.append(blocker("parity_integration_shape", "Invalid integration check"))

    delivery = data.get("delivery")
    if not isinstance(delivery, dict) or delivery.get("branch") != "main" or delivery.get("remote") != "origin":
        findings.append(blocker("delivery_config", "delivery must pin origin/main"))
    elif not isinstance(delivery.get("repos"), list) or len(delivery["repos"]) != 2:
        findings.append(blocker("delivery_repos", "delivery must declare Codex and Claude repos"))
    else:
        delivery_ids: set[str] = set()
        for repo in delivery["repos"]:
            repo_id = repo.get("id") if isinstance(repo, dict) else None
            if (
                not isinstance(repo_id, str)
                or repo_id in delivery_ids
                or set(repo) != {"id", "path", "remote_url", "required_paths"}
                or not isinstance(repo.get("path"), str)
                or not isinstance(repo.get("remote_url"), str)
                or not repo.get("remote_url")
                or not isinstance(repo.get("required_paths"), list)
                or not repo.get("required_paths")
            ):
                findings.append(blocker("delivery_repo_shape", f"Invalid delivery repo: {repo_id}"))
                continue
            delivery_ids.add(repo_id)
        if delivery_ids != {"codex", "claude"}:
            findings.append(blocker("delivery_repo_ids", "delivery repos must be codex and claude"))

    update_ids: set[str] = set()
    for candidate in data.get("update_candidates", []):
        candidate_id = candidate.get("id") if isinstance(candidate, dict) else None
        if not isinstance(candidate_id, str) or not candidate_id:
            findings.append(blocker("update_candidate_shape", "Each update candidate needs a string id"))
            continue
        if candidate_id in update_ids:
            findings.append(blocker("duplicate_update_candidate", f"Duplicate update candidate: {candidate_id}"))
        update_ids.add(candidate_id)
        if candidate.get("source_id") not in source_ids:
            findings.append(blocker("update_candidate_source", f"Unknown source: {candidate_id}"))
        if not NAME_RE.fullmatch(str(candidate.get("source_name", ""))) or not NAME_RE.fullmatch(str(candidate.get("local_name", ""))):
            findings.append(blocker("update_candidate_name", f"Invalid skill name: {candidate_id}"))
        if not SHA_RE.fullmatch(str(candidate.get("revision", ""))):
            findings.append(blocker("update_candidate_revision", f"Invalid revision: {candidate_id}"))
        if candidate.get("state") != "update-available":
            findings.append(blocker("update_candidate_state", f"State must be update-available: {candidate_id}"))
        targets = candidate.get("targets")
        if not isinstance(targets, list) or not targets or any(target not in root_ids for target in targets):
            findings.append(blocker("update_candidate_targets", f"Invalid targets: {candidate_id}"))
        if candidate.get("runtime_content_updated") is not False:
            findings.append(blocker("update_candidate_runtime", f"Pending update cannot claim runtime mutation: {candidate_id}"))
        if candidate.get("blocked_by_hold") not in hold_ids:
            findings.append(blocker("update_candidate_blocker", f"Pending update needs a registered hold: {candidate_id}"))
    return findings


def load_lock(path: Path) -> tuple[dict[str, Any], list[Finding]]:
    try:
        data = _strict_json_loads(path.read_bytes())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, StrictJSONError) as exc:
        return {}, [blocker("lock_unreadable", str(exc), str(path))]
    if not isinstance(data, dict):
        return {}, [blocker("lock_top_level", "Lock JSON must be an object", str(path))]
    findings: list[Finding] = []
    if data.get("schema_version") != LOCK_SCHEMA_VERSION:
        findings.append(blocker("lock_schema", f"Expected lock schema {LOCK_SCHEMA_VERSION}"))
    if data.get("hash_algorithm") != HASH_ALGORITHM:
        findings.append(blocker("lock_hash_algorithm", f"Expected {HASH_ALGORITHM}"))
    if not isinstance(data.get("generation"), int):
        findings.append(blocker("lock_generation", "Lock generation must be an integer"))
    if not re.fullmatch(r"[0-9a-f]{64}", str(data.get("registry_sha256", ""))):
        findings.append(blocker("lock_registry_digest", "registry_sha256 must be SHA-256"))
    if not _valid_date_string(data.get("generated_at")):
        findings.append(blocker("lock_generated_at", "generated_at must be a valid YYYY-MM-DD date"))
    if not isinstance(data.get("artifacts"), dict):
        findings.append(blocker("lock_artifacts", "artifacts must be an object"))
    return data, findings


def load_catalog(path: Path) -> tuple[dict[str, Any], list[Finding]]:
    try:
        data = _strict_json_loads(path.read_bytes())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, StrictJSONError) as exc:
        return {}, [blocker("catalog_unreadable", str(exc), str(path))]
    if not isinstance(data, dict):
        return {}, [blocker("catalog_top_level", "Catalog JSON must be an object", str(path))]
    findings: list[Finding] = []
    if data.get("schema_version") != CATALOG_SCHEMA_VERSION:
        findings.append(blocker("catalog_schema", f"Expected catalog schema {CATALOG_SCHEMA_VERSION}"))
    if not isinstance(data.get("generation"), int):
        findings.append(blocker("catalog_generation", "Catalog generation must be an integer"))
    if not re.fullmatch(r"[0-9a-f]{64}", str(data.get("registry_sha256", ""))):
        findings.append(blocker("catalog_registry_digest", "registry_sha256 must be SHA-256"))
    if not isinstance(data.get("sources"), dict):
        findings.append(blocker("catalog_sources", "sources must be an object"))
    return data, findings


def load_reputation(path: Path, registry: dict[str, Any]) -> tuple[dict[str, Any], list[Finding]]:
    try:
        data = _strict_json_loads(path.read_bytes())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, StrictJSONError) as exc:
        return {}, [blocker("reputation_unreadable", str(exc), str(path))]
    if not isinstance(data, dict):
        return {}, [blocker("reputation_top_level", "Reputation JSON must be an object", str(path))]
    findings: list[Finding] = []
    if set(data) != {"schema_version", "generated_at", "policy", "snapshots"}:
        findings.append(blocker("reputation_fields", "Reputation evidence has unknown or missing top-level fields", str(path)))
    if data.get("schema_version") != REPUTATION_SCHEMA_VERSION:
        findings.append(blocker("reputation_schema", f"Expected reputation schema {REPUTATION_SCHEMA_VERSION}"))
    if not _valid_date_string(data.get("generated_at")):
        findings.append(blocker("reputation_date", "generated_at must be YYYY-MM-DD"))
    if data.get("policy") != {"popularity_is_approval": False, "approval_use": "advisory-only"}:
        findings.append(blocker("reputation_policy_binding", "Popularity must remain advisory-only"))
    snapshots = data.get("snapshots")
    if not isinstance(snapshots, list):
        return data, findings + [blocker("reputation_snapshots", "snapshots must be an array")]
    sources = {
        str(source.get("id")): source
        for source in registry.get("sources", [])
        if isinstance(source, dict) and isinstance(source.get("id"), str)
    }
    expected_keys = {
        "source_id",
        "github",
        "observed_revision",
        "observed_at",
        "head_matches_pin",
        "archived",
        "stars",
        "forks",
        "open_issues",
        "issues_enabled",
        "security_policy",
        "license_signal",
        "trust_role",
        "assessment",
        "evidence_urls",
    }
    seen: set[str] = set()
    for index, row in enumerate(snapshots):
        source_id = row.get("source_id") if isinstance(row, dict) else None
        location = str(source_id) if isinstance(source_id, str) else str(index)
        if not isinstance(row, dict) or set(row) != expected_keys:
            findings.append(blocker("reputation_shape", "Snapshot fields differ from the schema", location))
            continue
        source = sources.get(str(source_id))
        if source is None or source_id in seen:
            findings.append(blocker("reputation_source", "Unknown or duplicate source snapshot", location))
            continue
        seen.add(str(source_id))
        urls = row.get("evidence_urls")
        expected_repo_url = f"https://github.com/{source.get('github')}"
        if (
            row.get("github") != source.get("github")
            or row.get("observed_revision") != source.get("observed_revision")
            or not _valid_date_string(row.get("observed_at"))
            or str(row.get("observed_at", "")) < str(source.get("observed_at", ""))
            or not isinstance(row.get("head_matches_pin"), bool)
            or not isinstance(row.get("archived"), bool)
            or any(
                not isinstance(row.get(field_name), int)
                or isinstance(row.get(field_name), bool)
                or row.get(field_name) < 0
                for field_name in ("stars", "forks", "open_issues")
            )
            or not isinstance(row.get("issues_enabled"), bool)
            or not isinstance(row.get("security_policy"), bool)
            or any(
                not isinstance(row.get(field_name), str) or not row.get(field_name)
                for field_name in ("license_signal", "trust_role", "assessment")
            )
            or not isinstance(urls, list)
            or not urls
            or any(not isinstance(url, str) or not url.startswith("https://github.com/") for url in urls)
            or expected_repo_url not in urls
        ):
            findings.append(blocker("reputation_binding", "Snapshot identity, revision, date, metrics, or evidence URLs are invalid", location))
        if row.get("archived") is True:
            findings.append(advisory("reputation_archived", "Source was archived at the snapshot", location))
        if row.get("head_matches_pin") is False:
            findings.append(advisory("reputation_head_drift", "Pinned revision was not default-branch HEAD at the snapshot", location))
    if seen != set(sources):
        findings.append(blocker("reputation_coverage", f"Snapshot must cover every source exactly once: missing={sorted(set(sources) - seen)} extra={sorted(seen - set(sources))}"))
    expected_date = max(
        (str(row.get("observed_at", "")) for row in snapshots if isinstance(row, dict)),
        default="",
    )
    if data.get("generated_at") != expected_date:
        findings.append(blocker("reputation_generation_date", "generated_at must match the newest source observation date"))
    return data, findings


def reputation_promotion_findings(registry: dict[str, Any], reputation: dict[str, Any]) -> list[Finding]:
    by_source = {
        row.get("source_id"): row
        for row in reputation.get("snapshots", [])
        if isinstance(row, dict)
    }
    findings: list[Finding] = []
    for collection in registry.get("collections", []):
        if not isinstance(collection, dict) or collection.get("local_state") not in APPROVAL_LINEAGE_STATES:
            continue
        row = by_source.get(collection.get("source_id"))
        if not isinstance(row, dict) or row.get("archived") is not False or row.get("head_matches_pin") is not True:
            findings.append(blocker("approved_reputation_hold", "Approved state requires a current, non-archived source snapshot whose pin matched HEAD", str(collection.get("id", ""))))
    return findings


def load_estate_lock(path: Path) -> tuple[dict[str, Any], list[Finding]]:
    try:
        data = _strict_json_loads(path.read_bytes())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, StrictJSONError) as exc:
        return {}, [blocker("estate_lock_unreadable", str(exc), str(path))]
    if not isinstance(data, dict):
        return {}, [blocker("estate_lock_top_level", "Estate lock JSON must be an object", str(path))]
    findings: list[Finding] = []
    expected_keys = {"schema_version", "generation", "registry_sha256", "hash_algorithm", "generated_at", "records"}
    if set(data) != expected_keys:
        findings.append(blocker("estate_lock_fields", f"Expected exact fields: {sorted(expected_keys)}", str(path)))
    if data.get("schema_version") != ESTATE_SCHEMA_VERSION:
        findings.append(blocker("estate_lock_schema", f"Expected estate schema {ESTATE_SCHEMA_VERSION}"))
    if data.get("hash_algorithm") != HASH_ALGORITHM:
        findings.append(blocker("estate_lock_hash_algorithm", f"Expected {HASH_ALGORITHM}"))
    if not isinstance(data.get("generation"), int):
        findings.append(blocker("estate_lock_generation", "generation must be an integer"))
    if not re.fullmatch(r"[0-9a-f]{64}", str(data.get("registry_sha256", ""))):
        findings.append(blocker("estate_lock_registry_digest", "registry_sha256 must be SHA-256"))
    if not _valid_date_string(data.get("generated_at")):
        findings.append(blocker("estate_lock_date", "generated_at must be a valid date"))
    records = data.get("records")
    if not isinstance(records, list):
        findings.append(blocker("estate_lock_records", "records must be an array"))
    else:
        expected_record_keys = {
            "root_id",
            "relative_path",
            "resolved_name",
            "name_resolution",
            "tree_sha256",
            "classification",
            "hash_normalizations",
        }
        seen: set[tuple[str, str]] = set()
        for index, record in enumerate(records):
            if not isinstance(record, dict) or set(record) != expected_record_keys:
                findings.append(blocker("estate_lock_record_shape", "Estate record fields differ", str(index)))
                continue
            key = (str(record.get("root_id")), str(record.get("relative_path")))
            if key in seen:
                findings.append(blocker("estate_lock_duplicate", "Duplicate root/path record", f"{key[0]}:{key[1]}"))
            seen.add(key)
            if (
                not NAME_RE.fullmatch(str(record.get("resolved_name", "")))
                or not re.fullmatch(r"[0-9a-f]{64}", str(record.get("tree_sha256", "")))
                or record.get("classification")
                not in RUNTIME_STATES | {"platform-managed", "snapshot-managed", "preexisting-unclassified"}
                or not isinstance(record.get("hash_normalizations"), list)
                or any(path not in {"estate.lock.json", "reputation.lock.json"} for path in record.get("hash_normalizations", []))
            ):
                findings.append(blocker("estate_lock_record_value", "Estate record contains an invalid name, hash, or classification", f"{key[0]}:{key[1]}"))
    return data, findings


def planned_estate_lock(
    registry: dict[str, Any],
    registry_path: Path,
    inventory: dict[str, Any],
) -> dict[str, Any]:
    runtime_root_ids = {
        root["id"]
        for root in registry.get("roots", [])
        if isinstance(root, dict) and root.get("collision_scope") == "runtime"
    }
    governed: dict[tuple[str, str], str] = {}
    for collection in registry.get("collections", []):
        state = str(collection.get("local_state", "preexisting-unclassified"))
        if state not in RUNTIME_STATES:
            continue
        classification = state
        for target in collection.get("targets", []):
            for name in collection.get("skills", []):
                governed[(str(target), str(name))] = classification
    records: list[dict[str, Any]] = []
    for record in inventory.get("records", []):
        if record.get("disabled_by_selector") is True:
            continue
        root_id = str(record.get("root_id", ""))
        if root_id not in runtime_root_ids:
            continue
        relative = str(record.get("relative_path", ""))
        classification = governed.get((root_id, str(record.get("resolved_name", ""))))
        if classification is None:
            if relative.startswith(".system/") or "/.system/" in relative:
                classification = "platform-managed"
            elif "scheduled" in root_id or "mirror" in root_id:
                classification = "snapshot-managed"
            else:
                classification = "preexisting-unclassified"
        records.append(
            {
                "root_id": root_id,
                "relative_path": relative,
                "resolved_name": record.get("resolved_name"),
                "name_resolution": record.get("name_resolution"),
                "tree_sha256": record.get("tree_sha256"),
                "classification": classification,
                "hash_normalizations": record.get("estate_hash_normalizations", []),
            }
        )
    records.sort(key=lambda item: (str(item["root_id"]).encode(), str(item["relative_path"]).encode()))
    return {
        "schema_version": ESTATE_SCHEMA_VERSION,
        "generation": registry.get("generation"),
        "registry_sha256": sha256_path(registry_path),
        "hash_algorithm": HASH_ALGORITHM,
        "generated_at": max(
            (str(collection.get("baseline_at", "")) for collection in registry.get("collections", [])),
            default="",
        ),
        "records": records,
    }


def runtime_state_presence_findings(registry: dict[str, Any], inventory: dict[str, Any]) -> list[Finding]:
    present = {
        (str(record.get("root_id", "")), str(record.get("resolved_name", "")))
        for record in inventory.get("records", [])
        if isinstance(record, dict) and record.get("disabled_by_selector") is not True
    }
    findings: list[Finding] = []
    for collection in registry.get("collections", []):
        if not isinstance(collection, dict):
            continue
        state = str(collection.get("local_state", ""))
        if state in RUNTIME_STATES:
            continue
        code = "forbidden_runtime_present" if state in {"rejected", "retired", "revoked"} else "runtime_present_before_promotion"
        for target in collection.get("targets", []):
            for name in collection.get("skills", []):
                key = (str(target), str(name))
                if key in present:
                    findings.append(
                        blocker(
                            code,
                            f"Lifecycle state {state} cannot expose the Skill in a runtime root",
                            f"{key[0]}:{key[1]}",
                        )
                    )
    return findings


def estate_consistency_findings(actual: dict[str, Any], expected: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    for field_name in ("schema_version", "generation", "registry_sha256", "hash_algorithm", "generated_at"):
        if actual.get(field_name) != expected.get(field_name):
            findings.append(blocker("estate_lock_binding", f"{field_name} differs from the current registry/inventory"))
    actual_records = actual.get("records", []) if isinstance(actual.get("records"), list) else []
    expected_records = expected.get("records", []) if isinstance(expected.get("records"), list) else []
    actual_by_key = {
        (str(item.get("root_id")), str(item.get("relative_path"))): item
        for item in actual_records
        if isinstance(item, dict)
    }
    expected_by_key = {
        (str(item.get("root_id")), str(item.get("relative_path"))): item
        for item in expected_records
        if isinstance(item, dict)
    }
    for key in sorted(set(expected_by_key) - set(actual_by_key)):
        findings.append(blocker("runtime_estate_added", "Runtime Skill is absent from the governed estate lock", f"{key[0]}:{key[1]}"))
    for key in sorted(set(actual_by_key) - set(expected_by_key)):
        findings.append(blocker("runtime_estate_removed", "Governed runtime Skill is missing", f"{key[0]}:{key[1]}"))
    for key in sorted(set(actual_by_key) & set(expected_by_key)):
        if actual_by_key[key] != expected_by_key[key]:
            findings.append(blocker("runtime_estate_drift", "Runtime Skill name, hash, resolution, or classification differs", f"{key[0]}:{key[1]}"))
    return findings


def canonical_json_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8", "strict")
    return sha256_bytes(encoded)


def catalog_payload(
    registry: dict[str, Any],
    registry_path: Path,
    catalog_path: Path,
    live: bool = False,
    selected: str | None = None,
) -> tuple[dict[str, Any], list[Finding]]:
    catalog, findings = load_catalog(catalog_path)
    if has_blockers(findings):
        return {
            "command": "catalog",
            "status": "blocked",
            "findings": [asdict(item) for item in findings],
        }, findings

    if catalog.get("generation") != registry.get("generation"):
        findings.append(blocker("catalog_generation_mismatch", "Registry and catalog generation differ"))
    if catalog.get("registry_sha256") != sha256_path(registry_path):
        findings.append(blocker("catalog_registry_binding", "Catalog is not bound to the current registry"))

    registered = {source["id"]: source for source in registry.get("sources", [])}
    if selected and selected not in registered:
        findings.append(blocker("source_unknown", f"Unknown source: {selected}"))
    protected = [registry_path, catalog_path, *(expand_path(root["path"]) for root in registry.get("roots", []))]
    before = _manifest_digest(protected) if live else None
    catalog_sources = catalog.get("sources", {})
    for source_id in sorted(set(catalog_sources) - set(registered)):
        findings.append(blocker("catalog_unknown_source", "Catalog contains an unregistered source", source_id))

    rows: list[dict[str, Any]] = []
    all_names: dict[str, set[str]] = {}
    total_skills = 0
    extracted_names = 0
    license_gaps = 0
    complete_sources = 0
    live_checked = 0
    live_verified = 0
    for source_id, source in sorted(registered.items()):
        entry = catalog_sources.get(source_id)
        if not isinstance(entry, dict):
            severity = blocker if source.get("catalog_required") else advisory
            findings.append(severity("catalog_source_missing", "Pinned source has no catalog entry", source_id))
            continue
        if entry.get("github") != source.get("github"):
            findings.append(blocker("catalog_source_identity", "GitHub identity differs from registry", source_id))
        if entry.get("revision") != source.get("observed_revision"):
            findings.append(blocker("catalog_source_revision", "Catalog revision differs from registry", source_id))
        if not SHA_RE.fullmatch(str(entry.get("tree_sha", ""))):
            findings.append(blocker("catalog_tree_sha", "Catalog tree_sha must be a full Git SHA", source_id))
        complete = entry.get("complete") is True
        tree_truncated = entry.get("tree_truncated") is True
        archive_match = entry.get("tree_archive_blob_paths_match") is True
        if not complete or tree_truncated or not archive_match:
            findings.append(blocker("catalog_incomplete", "Full pinned tree enumeration is not verified", source_id))
        else:
            complete_sources += 1

        skills = entry.get("skills")
        if not isinstance(skills, list):
            findings.append(blocker("catalog_skill_list", "skills must be an array", source_id))
            skills = []
        if entry.get("skill_count") != len(skills):
            findings.append(blocker("catalog_skill_count", "skill_count does not match skills", source_id))

        paths: list[str] = []
        source_names = 0
        for index, skill in enumerate(skills):
            location = f"{source_id}:{index}"
            if not isinstance(skill, dict):
                findings.append(blocker("catalog_skill_shape", "Skill entry must be an object", location))
                continue
            path = skill.get("path")
            if (
                not isinstance(path, str)
                or posixpath.basename(path) != "SKILL.md"
                or path.startswith("/")
                or ".." in Path(path).parts
            ):
                findings.append(blocker("catalog_skill_path", f"Invalid SKILL.md path: {path}", location))
                continue
            paths.append(path)
            name = skill.get("name")
            if name is not None:
                if not isinstance(name, str):
                    findings.append(blocker("catalog_skill_name_type", "name must be a string or null", location))
                else:
                    source_names += 1
                    extracted_names += 1
                    all_names.setdefault(name, set()).add(source_id)
                    if not NAME_RE.fullmatch(name):
                        findings.append(advisory("catalog_skill_name_invalid", f"Candidate name is non-canonical: {name}", location))
            role = skill.get("role")
            if not isinstance(role, str) or not role:
                findings.append(blocker("catalog_skill_role", "role must be a non-empty string", location))
            if not SHA_RE.fullmatch(str(skill.get("blob_sha", ""))):
                findings.append(blocker("catalog_blob_sha", "blob_sha must be a Git blob SHA", location))
            if not SHA_RE.fullmatch(str(skill.get("package_tree_sha", ""))):
                findings.append(blocker("catalog_package_tree_sha", "package_tree_sha must bind the complete directory containing SKILL.md", location))
            license_paths = skill.get("license_paths")
            if (
                not isinstance(license_paths, list)
                or any(
                    not isinstance(item, str)
                    or not item
                    or item.startswith("/")
                    or ".." in Path(item).parts
                    for item in license_paths
                )
            ):
                findings.append(blocker("catalog_license_shape", "license_paths must be a string array", location))
            elif not license_paths:
                license_gaps += 1

        if paths != sorted(paths, key=lambda value: value.encode("utf-8")):
            findings.append(blocker("catalog_path_order", "Skill paths must be byte-sorted", source_id))
        if len(paths) != len(set(paths)):
            findings.append(blocker("catalog_duplicate_path", "Duplicate SKILL.md path", source_id))
        if entry.get("name_extracted_count") != source_names:
            findings.append(blocker("catalog_name_count", "name_extracted_count does not match skills", source_id))
        if entry.get("catalog_sha256") != canonical_json_sha256(skills):
            findings.append(blocker("catalog_content_digest", "Catalog skill list digest differs", source_id))

        live_status = "not-requested"
        if live and (selected is None or selected == source_id):
            live_checked += 1
            remote, error = _github_pinned_tree(source)
            if error or remote is None:
                live_status = "unavailable"
                findings.append(blocker("catalog_live_unavailable", error or "Pinned tree unavailable", source_id))
            else:
                expected_pairs = sorted((skill.get("path"), skill.get("blob_sha")) for skill in skills if isinstance(skill, dict))
                remote_pairs = remote.get("skill_blobs", [])
                remote_blob_paths = set(remote.get("blob_paths", []))
                remote_tree_shas = remote.get("tree_shas", {})
                if remote.get("commit_sha") != source.get("observed_revision"):
                    findings.append(blocker("catalog_live_commit", "Pinned commit identity differs", source_id))
                if remote.get("tree_sha") != entry.get("tree_sha"):
                    findings.append(blocker("catalog_live_tree", "Pinned tree SHA differs", source_id))
                if remote.get("truncated") is not False:
                    findings.append(blocker("catalog_live_truncated", "GitHub recursive tree is truncated", source_id))
                if remote_pairs != expected_pairs:
                    findings.append(blocker("catalog_live_mismatch", "Remote pinned SKILL.md path/blob set differs", source_id))
                package_tree_mismatches = sorted(
                    skill.get("path")
                    for skill in skills
                    if isinstance(skill, dict)
                    and isinstance(skill.get("path"), str)
                    and skill.get("package_tree_sha")
                    != (
                        remote.get("tree_sha")
                        if posixpath.dirname(skill["path"]) == ""
                        else remote_tree_shas.get(posixpath.dirname(skill["path"]))
                    )
                )
                if package_tree_mismatches:
                    findings.append(blocker("catalog_live_package_tree", f"Catalog package tree SHA differs from the pinned tree: {package_tree_mismatches[:20]}", source_id))
                missing_license_paths = sorted(
                    {
                        license_path
                        for skill in skills
                        if isinstance(skill, dict)
                        for license_path in skill.get("license_paths", [])
                        if isinstance(license_path, str) and license_path not in remote_blob_paths
                    }
                )
                if missing_license_paths:
                    findings.append(blocker("catalog_live_license_missing", f"Catalog license paths are absent from the pinned tree: {missing_license_paths[:20]}", source_id))
                if not any(item.path == source_id and item.severity == "BLOCKING" for item in findings):
                    live_status = "verified"
                    live_verified += 1
                else:
                    live_status = "mismatch"

        total_skills += len(skills)
        rows.append(
            {
                "id": source_id,
                "revision": entry.get("revision"),
                "skill_count": len(skills),
                "name_extracted_count": source_names,
                "complete": complete and not tree_truncated and archive_match,
                "catalog_sha256": entry.get("catalog_sha256"),
                "live_status": live_status,
            }
        )

    cross_source_collisions = sum(1 for source_ids in all_names.values() if len(source_ids) > 1)
    expected_summary = catalog.get("summary", {})
    computed_summary = {
        "source_count": len(registered),
        "complete_source_count": complete_sources,
        "skill_file_count": total_skills,
        "name_extracted_count": extracted_names,
        "unique_extracted_name_count": len(all_names),
        "cross_source_name_collision_groups": cross_source_collisions,
        "license_evidence_missing_count": license_gaps,
    }
    if expected_summary != computed_summary:
        findings.append(blocker("catalog_summary_mismatch", "Catalog summary differs from computed values"))
    if license_gaps:
        findings.append(advisory("catalog_license_evidence_gap", f"No nearest license file for {license_gaps} catalog entries"))
    after = _manifest_digest(protected) if live else None
    if live and before != after:
        findings.append(blocker("network_read_mutation", "Protected local manifest changed during catalog --live"))

    return {
        "command": "catalog",
        "status": "DEGRADED" if has_blockers(findings) else "ok",
        "generation": registry.get("generation"),
        "summary": computed_summary,
        "capability": "network-read" if live else "offline-read",
        "external_verification": "live-pinned-git-tree" if live else "recorded-pinned-evidence-only",
        "live_summary": {"checked": live_checked, "verified": live_verified},
        "local_manifest_before": before,
        "local_manifest_after": after,
        "sources": rows,
        "findings": [asdict(item) for item in findings],
    }, findings


def reputation_payload(
    registry: dict[str, Any],
    reputation_path: Path = DEFAULT_REPUTATION,
) -> tuple[dict[str, Any], list[Finding]]:
    reputation, findings = load_reputation(reputation_path, registry)
    findings.extend(reputation_promotion_findings(registry, reputation))
    snapshots = reputation.get("snapshots", []) if isinstance(reputation.get("snapshots"), list) else []
    return {
        "command": "reputation",
        "status": "DEGRADED" if has_blockers(findings) else "ok",
        "generated_at": reputation.get("generated_at"),
        "summary": {
            "source_count": len(snapshots),
            "archived_count": sum(1 for row in snapshots if isinstance(row, dict) and row.get("archived") is True),
            "head_mismatch_count": sum(1 for row in snapshots if isinstance(row, dict) and row.get("head_matches_pin") is False),
            "security_policy_count": sum(1 for row in snapshots if isinstance(row, dict) and row.get("security_policy") is True),
        },
        "policy": reputation.get("policy"),
        "snapshots": snapshots,
        "findings": [asdict(item) for item in findings],
    }, findings


def registry_roots(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {entry["id"]: entry for entry in registry.get("roots", []) if isinstance(entry, dict) and "id" in entry}


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _canonical_leaf(path: Path) -> Path:
    """Resolve trusted parent components while preserving the leaf identity."""
    return Path(os.path.realpath(path.parent)) / path.name


def coverage_symlink_policy(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    policy: dict[str, dict[str, Any]] = {}
    for entry in registry.get("coverage_symlinks", []):
        if isinstance(entry, dict) and isinstance(entry.get("path"), str):
            policy[str(_canonical_leaf(expand_path(entry["path"])))] = entry
    return policy


def discover_skill_directories(
    root: Path,
    scan_mode: str,
    *,
    required: bool = True,
    excluded_names: set[str] | None = None,
    skip_prefixes: set[str] | None = None,
    symlink_policy: dict[str, dict[str, Any]] | None = None,
    symlink_records: list[dict[str, Any]] | None = None,
    excluded_skill_records: list[dict[str, str]] | None = None,
    record_only_symlinks: bool = False,
) -> tuple[list[Path], list[Finding]]:
    findings: list[Finding] = []
    relative_skills: list[str] = []
    if excluded_names is None:
        excluded_names = {".git", "__pycache__"}
    skip_prefixes = skip_prefixes or set()
    symlink_policy = symlink_policy or {}
    symlink_records = symlink_records if symlink_records is not None else []
    excluded_skill_records = excluded_skill_records if excluded_skill_records is not None else []
    root = root.absolute()
    root_fd, _, open_finding = _open_root_directory(root)
    if open_finding or root_fd is None:
        finding = open_finding or blocker("root_unavailable", "Configured root is unavailable", str(root))
        if not required and finding.code in {"root_unavailable", "root_open_failed"}:
            finding = advisory("root_missing", finding.message, finding.path)
        return [], [finding]
    directory_count = 0

    def skipped(relative: str) -> bool:
        return any(relative == prefix or relative.startswith(prefix + "/") for prefix in skip_prefixes)

    def walk(
        directory_fd: int,
        parts: tuple[str, ...],
        depth: int,
        included: bool = True,
        exclusion_name: str = "",
    ) -> None:
        nonlocal directory_count
        directory_count += 1
        relative_directory = "/".join(parts)
        if directory_count > MAX_DIRECTORIES * 8:
            findings.append(blocker("discovery_too_many_directories", "Discovery directory limit exceeded", relative_directory))
            return
        if depth > MAX_DEPTH * 2:
            findings.append(blocker("discovery_too_deep", "Discovery depth limit exceeded", relative_directory))
            return
        before = os.fstat(directory_fd)
        try:
            with os.scandir(directory_fd) as iterator:
                entries = sorted(iterator, key=lambda entry: os.fsencode(entry.name))
        except OSError as exc:
            findings.append(blocker("discovery_unreadable", str(exc), relative_directory or str(root)))
            return
        has_skill = False
        for entry in entries:
            relative = "/".join((*parts, entry.name))
            try:
                entry.name.encode("utf-8", "strict")
                info = os.stat(entry.name, dir_fd=directory_fd, follow_symlinks=False)
            except OSError as exc:
                findings.append(blocker("discovery_lstat_failed", str(exc), relative))
                continue
            except UnicodeEncodeError:
                findings.append(blocker("non_utf8_path", "Path is not strict UTF-8", relative_directory))
                continue
            if stat.S_ISLNK(info.st_mode):
                link_path = _canonical_leaf(root / relative)
                try:
                    target = os.readlink(entry.name, dir_fd=directory_fd)
                except OSError as exc:
                    findings.append(blocker("discovery_symlink_unreadable", str(exc), str(link_path)))
                    continue
                declared = symlink_policy.get(str(link_path))
                target_path = Path(target) if os.path.isabs(target) else link_path.parent / target
                target_exists = target_path.exists()
                row = {
                    "path": str(link_path),
                    "target": target,
                    "target_exists": target_exists,
                    "allowlisted": declared is not None,
                    "root_relative_path": relative,
                    "excluded": not included or record_only_symlinks,
                }
                symlink_records.append(row)
                if not included or record_only_symlinks:
                    findings.append(advisory("discovery_excluded_symlink_recorded", f"Excluded-surface symlink recorded without following: {target}", str(link_path)))
                elif declared is None:
                    findings.append(blocker("discovery_symlink_unreviewed", "Symlink is not followed and has no explicit non-runtime allowlist", str(link_path)))
                elif target != declared.get("expected_target"):
                    findings.append(blocker("discovery_symlink_target_drift", f"expected={declared.get('expected_target')} actual={target}", str(link_path)))
                elif not target_exists and not declared.get("allow_missing_target"):
                    findings.append(blocker("discovery_symlink_target_missing", "Allowlisted symlink target is missing", str(link_path)))
                else:
                    findings.append(advisory("discovery_symlink_allowlisted", f"Symlink recorded without following: {target}", str(link_path)))
                continue
            if stat.S_ISDIR(info.st_mode):
                if skipped(relative):
                    continue
                if included and scan_mode == "direct" and depth >= 1:
                    continue
                child_fd, child_finding = _open_child_directory_at(directory_fd, entry.name, info, relative)
                if child_finding or child_fd is None:
                    findings.append(child_finding or blocker("directory_open_failed", "Directory unavailable", relative))
                    continue
                try:
                    if included and entry.name in excluded_names:
                        walk(child_fd, (*parts, entry.name), depth + 1, False, entry.name)
                    else:
                        walk(child_fd, (*parts, entry.name), depth + 1, included, exclusion_name)
                finally:
                    os.close(child_fd)
            elif stat.S_ISREG(info.st_mode) and entry.name == "SKILL.md":
                has_skill = True
        if has_skill:
            if included and (scan_mode == "recursive" or depth == 1):
                relative_skills.append(relative_directory)
            elif not included:
                excluded_skill_records.append({"path": str(_canonical_leaf(root / relative_directory)), "excluded_name": exclusion_name})
        after = os.fstat(directory_fd)
        if _directory_snapshot(before) != _directory_snapshot(after):
            findings.append(blocker("discovery_directory_changed", "Directory changed during discovery", relative_directory or "."))

    try:
        walk(root_fd, (), 0)
    finally:
        os.close(root_fd)
    relative_skills.sort(key=lambda value: value.encode("utf-8"))
    return [root / relative for relative in relative_skills], findings


def coverage_probe(registry: dict[str, Any]) -> tuple[dict[str, Any], list[Finding]]:
    findings: list[Finding] = []
    policy = registry.get("coverage_policy", {})
    scope_values = policy.get("scope_bases", []) if isinstance(policy, dict) else []
    excluded_names = set(policy.get("excluded_dir_names", [])) if isinstance(policy, dict) else set()
    excluded_reasons = policy.get("excluded_dir_reasons", {}) if isinstance(policy, dict) else {}
    symlink_policy = coverage_symlink_policy(registry)
    symlink_records: list[dict[str, Any]] = []
    excluded_name_records: list[dict[str, str]] = []
    exclusions = registry.get("coverage_exclusions", [])
    root_paths = {
        root["id"]: Path(os.path.realpath(expand_path(root["path"])))
        for root in registry.get("roots", [])
        if isinstance(root, dict) and isinstance(root.get("id"), str) and isinstance(root.get("path"), str)
    }
    exclusion_rows: list[dict[str, Any]] = []
    exclusion_paths: list[Path] = []
    for exclusion in exclusions if isinstance(exclusions, list) else []:
        path = Path(os.path.realpath(expand_path(exclusion.get("path", ""))))
        exclusion_paths.append(path)
        skills, excluded_findings = discover_skill_directories(
            path,
            "recursive",
            required=False,
            excluded_names=set(),
            symlink_policy=symlink_policy,
            symlink_records=symlink_records,
            record_only_symlinks=True,
        )
        findings.extend(excluded_findings)
        exclusion_rows.append(
            {
                "path": str(path),
                "reason": exclusion.get("reason"),
                "excluded_skill_count": len(skills),
            }
        )

    discovered_paths: set[str] = set()
    scope_rows: list[dict[str, Any]] = []
    for scope_value in scope_values if isinstance(scope_values, list) else []:
        scope = Path(os.path.realpath(expand_path(scope_value)))
        skip = {
            exclusion.relative_to(scope).as_posix()
            for exclusion in exclusion_paths
            if exclusion != scope and _is_relative_to(exclusion, scope)
        }
        skills, scope_findings = discover_skill_directories(
            scope,
            "recursive",
            required=True,
            excluded_names=excluded_names,
            skip_prefixes=skip,
            symlink_policy=symlink_policy,
            symlink_records=symlink_records,
            excluded_skill_records=excluded_name_records,
        )
        findings.extend(scope_findings)
        for skill in skills:
            discovered_paths.add(str(Path(os.path.realpath(skill))))
        scope_rows.append({"path": str(scope), "discovered_skill_count": len(skills), "skipped_prefixes": sorted(skip)})

    classified: dict[str, int] = {root_id: 0 for root_id in root_paths}
    unregistered: list[str] = []
    for value in sorted(discovered_paths):
        skill = Path(value)
        matches = [(root_id, root) for root_id, root in root_paths.items() if _is_relative_to(skill, root)]
        if not matches:
            unregistered.append(value)
            findings.append(blocker("unregistered_skill_surface", "SKILL.md is outside every registered root", value))
            continue
        root_id, _ = max(matches, key=lambda item: len(item[1].parts))
        classified[root_id] += 1

    scope_paths = [Path(row["path"]) for row in scope_rows]
    uncovered_roots = [
        root_id
        for root_id, root in root_paths.items()
        if not any(root == scope or _is_relative_to(root, scope) for scope in scope_paths)
    ]
    for root_id in uncovered_roots:
        findings.append(blocker("root_outside_coverage_scope", "Registered root is outside every scope base", root_id))
    excluded_by_name = [
        {
            "name": name,
            "reason": excluded_reasons.get(name),
            "excluded_skill_count": len({item["path"] for item in excluded_name_records if item["excluded_name"] == name}),
            "paths": sorted({item["path"] for item in excluded_name_records if item["excluded_name"] == name}),
        }
        for name in sorted(excluded_names)
    ]
    unique_symlinks = {item["path"]: item for item in symlink_records}
    payload = {
        "scope_bases": scope_rows,
        "exclusions": exclusion_rows,
        "directory_name_exclusions": excluded_by_name,
        "symlinks": [unique_symlinks[path] for path in sorted(unique_symlinks)],
        "classified_counts": classified,
        "unregistered": unregistered,
        "uncovered_roots": uncovered_roots,
        "complete": not has_blockers(findings) and not unregistered and not uncovered_roots,
    }
    return payload, findings


def _plugin_namespace(relative: Path) -> str:
    parts = list(relative.parts)
    skill_indexes = [index for index, part in enumerate(parts) if part == "skills"]
    if skill_indexes:
        index = skill_indexes[-1] - 1
        while index >= 0:
            candidate = parts[index]
            if candidate not in {"local", "cache"} and not re.match(r"^v?\d", candidate):
                return candidate
            index -= 1
    return parts[0] if parts else "plugin"


def _logical_name(root: dict[str, Any], root_path: Path, skill_path: Path, name: str) -> tuple[str, str]:
    relative = skill_path.relative_to(root_path)
    if ".system" in relative.parts:
        return f"system:{name}", "system-managed"
    mode = root.get("namespace_mode")
    if mode == "plugin":
        namespace = _plugin_namespace(relative)
        return f"{namespace}:{name}", "plugin-managed"
    if mode == "root":
        return f"{root['id']}:{name}", str(root.get("role", "catalog"))
    return name, str(root.get("role", "active"))


def estate_hash_normalization_policy(registry: dict[str, Any]) -> dict[tuple[str, str], list[str]]:
    return {
        (str(entry["root_id"]), str(entry["relative_path"])): sorted(str(path) for path in entry["files"])
        for entry in registry.get("estate_hash_normalizations", [])
        if isinstance(entry, dict)
        and isinstance(entry.get("root_id"), str)
        and isinstance(entry.get("relative_path"), str)
        and isinstance(entry.get("files"), list)
    }


def _root_for_skill_path(registry: dict[str, Any], skill_file: Path) -> dict[str, Any] | None:
    for root in registry.get("roots", []):
        if not isinstance(root, dict) or not isinstance(root.get("path"), str):
            continue
        root_path = Path(os.path.realpath(expand_path(root["path"])))
        try:
            if _is_relative_to(skill_file, root_path) and skill_file.name == "SKILL.md":
                return root
        except OSError:
            continue
    return None


def _declared_skill_path_root(registry: dict[str, Any], declared_path: Path) -> tuple[dict[str, Any], Path, Path] | None:
    declared_absolute = declared_path.absolute()
    declared_real = Path(os.path.realpath(declared_path))
    for root in registry.get("roots", []):
        if not isinstance(root, dict) or not isinstance(root.get("path"), str):
            continue
        root_declared = expand_path(root["path"]).absolute()
        root_real = Path(os.path.realpath(root_declared))
        if not _is_relative_to(declared_real, root_real):
            continue
        if _is_relative_to(declared_absolute, root_declared):
            return root, root_declared, declared_absolute.relative_to(root_declared)
        if _is_relative_to(declared_absolute, root_real):
            return root, root_real, declared_absolute.relative_to(root_real)
    return None


def _disabled_skill_component_findings(registry: dict[str, Any], declared_path: Path) -> list[Finding]:
    root = _declared_skill_path_root(registry, declared_path)
    if root is None:
        return []
    _, root_path, relative = root
    findings: list[Finding] = []
    current = root_path
    parts = relative.parts
    for index, part in enumerate(parts):
        current = current / part
        try:
            info = current.lstat()
        except OSError as exc:
            findings.append(blocker("codex_disabled_skill_missing", str(exc), str(current)))
            break
        if stat.S_ISLNK(info.st_mode):
            findings.append(blocker("codex_disabled_skill_symlink", "Disabled skill path component cannot be a symlink", str(current)))
            break
        if index < len(parts) - 1 and not stat.S_ISDIR(info.st_mode):
            findings.append(blocker("codex_disabled_skill_path", "Disabled skill path component must be a directory", str(current)))
            break
    return findings


def codex_disabled_skill_paths(registry: dict[str, Any]) -> tuple[set[Path], list[Finding]]:
    selector = registry.get("codex_selector", {})
    config_value = selector.get("config_path") if isinstance(selector, dict) else None
    if not isinstance(config_value, str) or not config_value:
        return set(), []
    config_path = expand_path(config_value)
    raw, read_finding = _read_regular_path(config_path, config_path.parent)
    if read_finding or raw is None:
        return set(), [read_finding or blocker("codex_selector_config_unavailable", "Codex selector config is unavailable", str(config_path))]
    try:
        config = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        return set(), [blocker("codex_selector_config_invalid", str(exc), str(config_path))]
    entries = config.get("skills", {}).get("config", []) if isinstance(config.get("skills"), dict) else []
    if not isinstance(entries, list):
        return set(), [blocker("codex_selector_config_shape", "skills.config must be an array", str(config_path))]
    disabled: set[Path] = set()
    findings: list[Finding] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or entry.get("enabled") is not False:
            continue
        raw_path = entry.get("path")
        location = f"skills.config:{index}"
        if not isinstance(raw_path, str) or not raw_path:
            findings.append(blocker("codex_disabled_skill_path", "Disabled skill config requires an exact SKILL.md path", location))
            continue
        declared_path = expand_path(raw_path)
        if declared_path.name != "SKILL.md":
            findings.append(blocker("codex_disabled_skill_path", "Disabled skill path must point to SKILL.md", str(declared_path)))
            continue
        try:
            info = declared_path.lstat()
        except OSError as exc:
            findings.append(blocker("codex_disabled_skill_missing", str(exc), str(declared_path)))
            continue
        if stat.S_ISLNK(info.st_mode):
            findings.append(blocker("codex_disabled_skill_symlink", "Disabled skill path cannot be a symlink", str(declared_path)))
            continue
        if not stat.S_ISREG(info.st_mode):
            findings.append(blocker("codex_disabled_skill_path", "Disabled skill path must be a regular file", str(declared_path)))
            continue
        declared_root = _declared_skill_path_root(registry, declared_path)
        if declared_root is None:
            findings.append(blocker("codex_disabled_skill_root", "Disabled skill path is outside every registered root", str(declared_path)))
            continue
        component_findings = _disabled_skill_component_findings(registry, declared_path)
        if component_findings:
            findings.extend(component_findings)
            continue
        path = Path(os.path.realpath(declared_path))
        if path in disabled:
            findings.append(blocker("codex_disabled_skill_duplicate", "Duplicate disabled skill path", str(path)))
            continue
        root = declared_root[0]
        if root is None:
            findings.append(blocker("codex_disabled_skill_root", "Disabled skill path is outside every registered root", str(path)))
            continue
        if "codex" not in root.get("runtimes", []):
            findings.append(blocker("codex_disabled_skill_runtime", "Disabled skill path must belong to a Codex runtime root", str(path)))
            continue
        disabled.add(path)
    return disabled, findings


def normalized_estate_tree_hash(tree: TreeResult, normalized_paths: list[str]) -> tuple[str | None, list[Finding]]:
    if not normalized_paths:
        return tree.tree_sha256, []
    by_path = {record.path: record for record in tree.files}
    findings: list[Finding] = []
    missing = sorted(set(normalized_paths) - set(by_path))
    if missing:
        findings.append(blocker("estate_normalization_missing", f"Configured control files are absent: {missing}", tree.root))
        return None, findings
    normalized: list[FileRecord] = []
    for record in tree.files:
        if record.path not in normalized_paths:
            normalized.append(record)
            continue
        marker = f"skill-governance-normalized-control-file-v1:{record.path}\n".encode("utf-8")
        normalized.append(
            FileRecord(
                path=record.path,
                size=len(marker),
                executable=record.executable,
                sha256=sha256_bytes(marker),
                data=marker,
            )
        )
    return _tree_hash(normalized, findings), findings


def inventory_payload(registry: dict[str, Any]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    findings: list[Finding] = []
    coverage: dict[str, dict[str, Any]] = {}
    symlink_policy = coverage_symlink_policy(registry)
    symlink_records: list[dict[str, Any]] = []
    name_inferences = {
        (entry["root_id"], entry["relative_path"]): entry
        for entry in registry.get("name_inferences", [])
        if isinstance(entry, dict) and "root_id" in entry and "relative_path" in entry
    }
    estate_normalizations = estate_hash_normalization_policy(registry)
    disabled_skill_paths, disabled_findings = codex_disabled_skill_paths(registry)
    findings.extend(disabled_findings)
    for root in sorted(registry.get("roots", []), key=lambda item: (item.get("precedence", 999), item.get("id", ""))):
        root_id = root["id"]
        root_path = expand_path(root["path"])
        skill_directories, discovery_findings = discover_skill_directories(
            root_path,
            root.get("scan_mode", "direct"),
            required=root.get("required") is True,
            symlink_policy=symlink_policy,
            symlink_records=symlink_records,
        )
        findings.extend(discovery_findings)
        recorded_before = len(records)
        for child in skill_directories:
            relative_skill_path = child.relative_to(root_path).as_posix()
            skill_file = Path(os.path.realpath(child / "SKILL.md"))
            disabled_by_selector = skill_file in disabled_skill_paths
            tree = scan_tree(child)
            normalized_paths = estate_normalizations.get((root_id, relative_skill_path), [])
            estate_tree_sha256, normalization_findings = normalized_estate_tree_hash(tree, normalized_paths)
            findings.extend(normalization_findings)
            skill_record = next((item for item in tree.files if item.path == "SKILL.md"), None)
            values: dict[str, Any] = {}
            frontmatter_findings: list[Finding] = []
            if skill_record:
                values, frontmatter_findings = parse_frontmatter_strict(skill_record.data, f"{child}/SKILL.md")
            verified_name = values.get("name")
            name_resolution = "frontmatter"
            name_is_ambiguous = any(
                item.code == "frontmatter_duplicate_key" and "name" in item.message
                for item in frontmatter_findings
            )
            strict_name_verified = (
                isinstance(verified_name, str)
                and NAME_RE.fullmatch(verified_name) is not None
                and not name_is_ambiguous
            )
            active_runtime = root.get("collision_scope") == "runtime" and not disabled_by_selector
            if active_runtime and not strict_name_verified:
                inference = name_inferences.get((root_id, relative_skill_path))
                if (
                    isinstance(inference, dict)
                    and inference.get("tree_sha256") == tree.tree_sha256
                    and inference.get("inferred_name") == child.name
                ):
                    verified_name = inference["inferred_name"]
                    name_resolution = "hash-bound-directory-inference"
                    findings.append(advisory("runtime_skill_name_inferred", "Legacy command-format name is bound to its exact tree hash", f"{root_id}:{relative_skill_path}"))
                else:
                    findings.append(
                        blocker(
                            "runtime_skill_name_unverified",
                            "Runtime collision checks require a valid captured frontmatter name or hash-bound inference",
                            f"{root_id}:{relative_skill_path}/SKILL.md",
                        )
                    )
            if (
                active_runtime
                and isinstance(verified_name, str)
                and NAME_RE.fullmatch(verified_name)
                and name_resolution == "frontmatter"
                and verified_name != child.name
            ):
                findings.append(
                    blocker(
                        "runtime_skill_identity_mismatch",
                        f"Frontmatter name {verified_name} differs from directory {child.name}",
                        f"{root_id}:{relative_skill_path}/SKILL.md",
                    )
                )
            raw_name = str(verified_name or child.name)
            logical_name, record_scope = _logical_name(root, root_path, child, raw_name)
            if active_runtime:
                for item in tree.findings:
                    if item.severity == "BLOCKING":
                        findings.append(
                            blocker(
                                "governed_estate_structure",
                                f"{item.code}: {item.message}",
                                f"{root_id}:{relative_skill_path}/{item.path}",
                            )
                        )
            records.append(
                {
                    "root_id": root_id,
                    "root_role": root.get("role"),
                    "record_scope": record_scope,
                    "runtimes": root.get("runtimes", []),
                    "precedence": root.get("precedence"),
                    "relative_path": relative_skill_path,
                    "directory_name": child.name,
                    "frontmatter_name": values.get("name"),
                    "resolved_name": raw_name,
                    "name_resolution": name_resolution,
                    "logical_name": logical_name,
                    "frontmatter_state": "strict" if not frontmatter_findings else "requires-full-yaml-validation",
                    "tree_sha256": estate_tree_sha256,
                    "raw_tree_sha256": tree.tree_sha256,
                    "estate_hash_normalizations": normalized_paths,
                    "disabled_by_selector": disabled_by_selector,
                    "tree_finding_codes": sorted({item.code for item in tree.findings}),
                    "frontmatter_finding_codes": sorted({item.code for item in frontmatter_findings}),
                }
            )
        recorded = len(records) - recorded_before
        root_blocked = has_blockers(discovery_findings)
        coverage[root_id] = {
            "path": str(root_path),
            "scan_mode": root.get("scan_mode"),
            "required": root.get("required"),
            "discovered": len(skill_directories),
            "recorded": recorded,
            "complete": len(skill_directories) == recorded and not root_blocked,
        }
        if len(skill_directories) != recorded:
            findings.append(blocker("coverage_mismatch", f"discovered={len(skill_directories)} recorded={recorded}", root_id))
    by_name: dict[str, list[dict[str, Any]]] = {}
    by_raw_name: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_name.setdefault(record["logical_name"], []).append(record)
        raw_name = record.get("resolved_name") or record["directory_name"]
        by_raw_name.setdefault(str(raw_name), []).append(record)
    collisions = {
        name: [
            {"root_id": item["root_id"], "tree_sha256": item["tree_sha256"], "precedence": item["precedence"]}
            for item in items
        ]
        for name, items in sorted(by_name.items())
        if len(items) > 1
    }
    raw_collisions = {
        name: [
            {"root_id": item["root_id"], "relative_path": item["relative_path"], "logical_name": item["logical_name"]}
            for item in items
        ]
        for name, items in sorted(by_raw_name.items())
        if len(items) > 1
    }
    surface_probe, surface_findings = coverage_probe(registry)
    findings.extend(surface_findings)
    coverage_complete = (
        all(item["complete"] for item in coverage.values())
        and surface_probe["complete"]
        and not has_blockers(findings)
    )
    unique_symlinks = {item["path"]: item for item in [*symlink_records, *surface_probe.get("symlinks", [])]}
    status = "blocked" if has_blockers(findings) else "ok"
    return {
        "command": "inventory",
        "status": status,
        "hash_algorithm": HASH_ALGORITHM,
        "summary": {
            "total_entries": len(records),
            "unique_names": len(by_name),
            "collision_names": len(collisions),
            "raw_name_collision_names": len(raw_collisions),
            "coverage_complete": coverage_complete,
            "roots": {
                root_id: sum(1 for record in records if record["root_id"] == root_id)
                for root_id in sorted(coverage)
            },
        },
        "coverage": coverage,
        "surface_probe": surface_probe,
        "symlinks": [unique_symlinks[path] for path in sorted(unique_symlinks)],
        "collisions": collisions,
        "raw_name_collisions": raw_collisions,
        "records": records,
        "findings": [asdict(item) for item in findings],
    }


def _expected_revision(collection: dict[str, Any], name: str) -> str:
    overrides = collection.get("revision_overrides", {})
    if isinstance(overrides, dict) and name in overrides:
        return str(overrides[name])
    return str(collection.get("default_revision", ""))


def _collection_upstream_bindings(
    registry: dict[str, Any],
    collection: dict[str, Any],
    catalog: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], list[Finding]]:
    if collection.get("local_state") not in CANDIDATE_STATES:
        return {}, []
    findings: list[Finding] = []
    source_id = str(collection.get("source_id", ""))
    registered_source = next(
        (item for item in registry.get("sources", []) if isinstance(item, dict) and item.get("id") == source_id),
        None,
    )
    source = catalog.get("sources", {}).get(source_id) if isinstance(catalog.get("sources"), dict) else None
    if not isinstance(source, dict) or not isinstance(registered_source, dict):
        return {}, [blocker("approved_catalog_source", "Approved collection source is absent from the pinned catalog", collection["id"])]
    if source.get("github") != registered_source.get("github") or source.get("revision") != registered_source.get("observed_revision"):
        findings.append(blocker("approved_catalog_source_binding", "Catalog source identity or revision differs from the registry", collection["id"]))
    catalog_skills = source.get("skills", [])
    by_path = {
        item.get("path"): item
        for item in catalog_skills
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    }
    bindings: dict[str, dict[str, Any]] = {}
    upstream_paths = collection.get("upstream_paths", {})
    for name in sorted(collection.get("skills", [])):
        revision = _expected_revision(collection, name)
        path = upstream_paths.get(name) if isinstance(upstream_paths, dict) else None
        item = by_path.get(path)
        if revision != source.get("revision"):
            findings.append(blocker("approved_catalog_revision", f"Collection revision {revision} differs from catalog revision {source.get('revision')}", f"{collection['id']}/{name}"))
            continue
        if not isinstance(item, dict):
            findings.append(blocker("approved_catalog_path", f"Pinned catalog has no exact SKILL.md path: {path}", f"{collection['id']}/{name}"))
            continue
        blob_sha = item.get("blob_sha")
        tree_sha = source.get("tree_sha")
        catalog_sha256 = source.get("catalog_sha256")
        package_tree_sha = item.get("package_tree_sha")
        license_paths = item.get("license_paths")
        upstream_name = item.get("name")
        if (
            not isinstance(blob_sha, str)
            or not SHA_RE.fullmatch(blob_sha)
            or not isinstance(tree_sha, str)
            or not SHA_RE.fullmatch(tree_sha)
            or not isinstance(catalog_sha256, str)
            or not re.fullmatch(r"[0-9a-f]{64}", catalog_sha256)
            or not isinstance(package_tree_sha, str)
            or not SHA_RE.fullmatch(package_tree_sha)
            or not isinstance(license_paths, list)
            or not license_paths
            or any(
                not isinstance(license_path, str)
                or not license_path
                or license_path.startswith("/")
                or ".." in Path(license_path).parts
                for license_path in license_paths
            )
            or not isinstance(upstream_name, str)
            or not NAME_RE.fullmatch(upstream_name)
        ):
            findings.append(blocker("approved_catalog_binding", "Catalog path lacks a valid blob, tree, digest, or license evidence", f"{collection['id']}/{name}"))
            continue
        bindings[name] = {
            "source_id": source_id,
            "github": str(source.get("github", "")),
            "revision": revision,
            "tree_sha": tree_sha,
            "path": str(path),
            "blob_sha": blob_sha,
            "catalog_sha256": catalog_sha256,
            "package_tree_sha": package_tree_sha,
            "license_paths": sorted(set(license_paths)),
            "upstream_name": upstream_name,
        }
    return bindings, findings


def _collection_subject(
    collection: dict[str, Any],
    target_hashes: dict[str, dict[str, str]],
    upstream_bindings: dict[str, dict[str, Any]] | None = None,
    candidate_hashes: dict[str, str] | None = None,
    candidate_manifests: dict[str, list[dict[str, Any]]] | None = None,
    target_manifests: dict[str, dict[str, list[dict[str, Any]]]] | None = None,
    license_evidence: dict[str, dict[str, list[dict[str, str]]]] | None = None,
    candidate_inspections: dict[str, dict[str, Any]] | None = None,
) -> str:
    subject = {
        "collection_id": collection.get("id"),
        "source_id": collection.get("source_id"),
        "source_revisions": {
            name: _expected_revision(collection, name)
            for name in sorted(collection.get("skills", []))
        },
        "adaptation": collection.get("adaptation"),
        "risk_tier": collection.get("risk_tier"),
        "license": collection.get("license"),
        "targets": {
            name: {target: target_hashes.get(name, {}).get(target) for target in sorted(collection.get("targets", []))}
            for name in sorted(collection.get("skills", []))
        },
    }
    if upstream_bindings:
        subject["baseline_at"] = collection.get("baseline_at")
        subject["adaptation_diff"] = collection.get("adaptation_diff")
        subject["upstream"] = {
            name: upstream_bindings[name]
            for name in sorted(upstream_bindings)
        }
        subject["quarantine"] = {
            name: candidate_hashes[name]
            for name in sorted(candidate_hashes or {})
        }
        subject["candidate_manifests"] = {
            name: candidate_manifests[name]
            for name in sorted(candidate_manifests or {})
        }
        subject["target_manifests"] = {
            name: target_manifests[name]
            for name in sorted(target_manifests or {})
        }
        subject["license_evidence"] = {
            name: license_evidence[name]
            for name in sorted(license_evidence or {})
        }
        subject["candidate_inspections"] = {
            name: candidate_inspections[name]
            for name in sorted(candidate_inspections or {})
        }
        subject["frontmatter_receipts"] = collection.get("frontmatter_receipts")
    return canonical_json_sha256(subject)


def _tree_artifact_evidence(
    tree: TreeResult,
    expected_name: str,
    revision: str,
    *,
    require_source: bool,
    require_license: bool,
    require_identity: bool,
    allow_candidate_invisible_controls: bool = False,
) -> tuple[str | None, list[dict[str, Any]], list[dict[str, str]], list[Finding]]:
    findings = list(tree.findings)
    if not tree.tree_sha256:
        return None, [], [], findings
    skill_record = next((record for record in tree.files if record.path == "SKILL.md"), None)
    if skill_record is None:
        findings.append(blocker("target_skill_missing", "Captured artifact must contain a regular SKILL.md", tree.root))
    elif require_identity:
        values, frontmatter_findings = parse_frontmatter_strict(skill_record.data, f"{tree.root}/SKILL.md")
        if frontmatter_findings:
            findings.extend(
                advisory(
                    "target_frontmatter_requires_full_validation",
                    f"{item.code}: {item.message}",
                    item.path,
                )
                for item in frontmatter_findings
            )
        if values.get("name") != expected_name or not NAME_RE.fullmatch(str(values.get("name", ""))):
            findings.append(blocker("target_skill_identity", f"SKILL.md name must be {expected_name}", f"{tree.root}/SKILL.md"))
    source_record = next((record for record in tree.files if record.path == "SOURCE.md"), None)
    if require_source:
        if source_record is None:
            findings.append(blocker("source_evidence_missing", "SOURCE.md missing from captured tree", tree.root))
        else:
            try:
                source_text = source_record.data.decode("utf-8", "strict")
            except UnicodeDecodeError as exc:
                findings.append(blocker("source_evidence_invalid", str(exc), f"{tree.root}/SOURCE.md"))
            else:
                if not revision or not re.search(rf"(?<![0-9a-f]){re.escape(revision)}(?![0-9a-f])", source_text):
                    findings.append(blocker("source_revision_mismatch", f"Expected revision {revision}", f"{tree.root}/SOURCE.md"))
    license_records = [
        {"path": record.path, "sha256": record.sha256}
        for record in tree.files
        if Path(record.path).name.lower() in {"license", "license.txt", "copying", "copying.txt"}
    ]
    if require_license and not license_records:
        findings.append(blocker("license_evidence_missing", "No captured local license file", tree.root))
    if not allow_candidate_invisible_controls:
        for record in tree.files:
            try:
                text = record.data.decode("utf-8", "strict")
            except UnicodeDecodeError:
                continue
            if BIDI_OR_ZERO_WIDTH.search(text):
                findings.append(
                    blocker(
                        "target_invisible_control",
                        "Approved review and runtime targets cannot contain bidi or zero-width control characters",
                        f"{tree.root}/{record.path}",
                    )
                )
    return tree.tree_sha256, [record.public() for record in tree.files], license_records, findings


def _candidate_tree_evidence(
    collection: dict[str, Any],
    local_name: str,
    binding: dict[str, Any],
    quarantine_root: Path,
) -> tuple[str | None, list[dict[str, Any]], list[dict[str, str]], list[Finding]]:
    revision = _expected_revision(collection, local_name)
    upstream_name = str(binding.get("upstream_name", ""))
    path = quarantine_root / str(collection.get("source_id", "")) / revision / upstream_name
    tree = scan_quarantined_tree(path, quarantine_root)
    digest, manifest, licenses, findings = _tree_artifact_evidence(
        tree,
        upstream_name,
        revision,
        require_source=False,
        require_license=False,
        require_identity=True,
        allow_candidate_invisible_controls=True,
    )
    skill_record = next((record for record in tree.files if record.path == "SKILL.md"), None)
    if skill_record is not None and git_blob_sha1(skill_record.data) != binding.get("blob_sha"):
        findings.append(blocker("candidate_blob_mismatch", "Captured SKILL.md does not match the pinned Git blob", str(path / "SKILL.md")))
    if tree.tree_sha256:
        try:
            observed_package_tree = git_tree_sha1(tree.files)
        except ValueError as exc:
            findings.append(blocker("candidate_package_tree_invalid", str(exc), str(path)))
        else:
            if observed_package_tree != binding.get("package_tree_sha"):
                findings.append(
                    blocker(
                        "candidate_package_tree_mismatch",
                        "Every quarantined file, path, and executable bit must exactly match the pinned upstream Git directory tree",
                        str(path),
                    )
                )
    return digest, manifest, licenses, findings


def _candidate_static_inspection(path: Path, quarantine_root: Path) -> tuple[dict[str, Any], list[Finding]]:
    payload, raw_findings = inspect_candidate(path, quarantine_root)
    enforceable = [
        item
        for item in raw_findings
        if item.code not in FULL_YAML_SUPERSEDED_CODES
    ]
    evidence = {
        "tree_sha256": payload.get("tree_sha256"),
        "files": payload.get("files", []),
        "blocking_findings": [
            asdict(item) for item in enforceable if item.severity == "BLOCKING"
        ],
        "advisory_findings": [
            asdict(item) for item in enforceable if item.severity == "ADVISORY"
        ],
        "full_yaml_pending_codes": sorted(
            {item.code for item in raw_findings if item.code in FULL_YAML_SUPERSEDED_CODES}
        ),
        "candidate_code_execution": False,
    }
    return evidence, enforceable


def build_lock_plan(
    registry: dict[str, Any],
    registry_path: Path,
    catalog: dict[str, Any] | None = None,
    catalog_path: Path | None = None,
    runtime_inventory: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], list[Finding]]:
    findings: list[Finding] = []
    if catalog is None:
        catalog, catalog_findings = load_catalog(catalog_path or DEFAULT_CATALOG)
        findings.extend(catalog_findings)
    if catalog is None:
        catalog = {}
    roots = registry_roots(registry)
    quarantine_root = expand_path(registry.get("quarantine_root", ""))
    review_root = expand_path(registry.get("review_root", ""))
    artifacts: dict[str, Any] = {}
    baseline_dates: list[str] = []
    needs_runtime_absence_check = any(
        isinstance(collection, dict)
        and collection.get("local_state") not in RUNTIME_STATES
        and collection.get("targets")
        and collection.get("skills")
        for collection in registry.get("collections", [])
    )
    if needs_runtime_absence_check:
        if runtime_inventory is None:
            runtime_inventory = inventory_payload(registry)
            findings.extend(Finding(**item) for item in runtime_inventory.get("findings", []))
        findings.extend(runtime_state_presence_findings(registry, runtime_inventory))
    for collection in registry.get("collections", []):
        collection_id = collection["id"]
        state = collection.get("local_state")
        baseline_dates.append(str(collection.get("baseline_at", "")))
        upstream_bindings, upstream_findings = _collection_upstream_bindings(registry, collection, catalog)
        findings.extend(upstream_findings)
        candidate_hashes: dict[str, str] = {}
        candidate_manifests: dict[str, list[dict[str, Any]]] = {}
        candidate_licenses: dict[str, list[dict[str, str]]] = {}
        candidate_inspections: dict[str, dict[str, Any]] = {}
        review_hashes: dict[str, dict[str, str]] = {}
        review_manifests: dict[str, dict[str, list[dict[str, Any]]]] = {}
        review_licenses: dict[str, dict[str, list[dict[str, str]]]] = {}
        runtime_hashes: dict[str, dict[str, str]] = {}
        runtime_manifests: dict[str, dict[str, list[dict[str, Any]]]] = {}
        runtime_licenses: dict[str, dict[str, list[dict[str, str]]]] = {}
        for name in sorted(collection["skills"]):
            key = f"{collection_id}/{name}"
            revision = _expected_revision(collection, name)
            if state in CANDIDATE_STATES:
                binding = upstream_bindings.get(name)
                if not isinstance(binding, dict):
                    findings.append(blocker("candidate_binding_missing", "Candidate state requires a pinned upstream binding", key))
                else:
                    digest, manifest, licenses, evidence_findings = _candidate_tree_evidence(
                        collection,
                        name,
                        binding,
                        quarantine_root,
                    )
                    findings.extend(evidence_findings)
                    if digest:
                        candidate_hashes[name] = digest
                        candidate_manifests[name] = manifest
                        candidate_licenses[name] = licenses
                    candidate_path = quarantine_root / str(collection.get("source_id", "")) / revision / str(binding.get("upstream_name", ""))
                    inspection, inspection_findings = _candidate_static_inspection(candidate_path, quarantine_root)
                    candidate_inspections[name] = inspection
                    findings.extend(inspection_findings)
                    if digest and inspection.get("tree_sha256") != digest:
                        findings.append(
                            blocker(
                                "candidate_inspection_snapshot_mismatch",
                                "Static inspection did not bind the same candidate tree capture as provenance evidence",
                                key,
                            )
                        )

            if state in REVIEW_STATES:
                review_hashes[name] = {}
                review_manifests[name] = {}
                review_licenses[name] = {}
                for target in collection["targets"]:
                    tree = scan_reviewed_tree(collection_id, name, target, review_root)
                    digest, manifest, licenses, evidence_findings = _tree_artifact_evidence(
                        tree,
                        name,
                        revision,
                        require_source=True,
                        require_license=True,
                        require_identity=True,
                    )
                    findings.extend(evidence_findings)
                    if digest:
                        review_hashes[name][target] = digest
                        review_manifests[name][target] = manifest
                        review_licenses[name][target] = licenses

            if state in RUNTIME_STATES:
                runtime_hashes[name] = {}
                runtime_manifests[name] = {}
                runtime_licenses[name] = {}
                for target in collection["targets"]:
                    root = roots.get(target)
                    if not root:
                        findings.append(blocker("lock_target", f"Unknown target {target}", key))
                        continue
                    skill_path = expand_path(root["path"]) / name
                    tree = scan_tree(skill_path)
                    digest, manifest, licenses, evidence_findings = _tree_artifact_evidence(
                        tree,
                        name,
                        revision,
                        require_source=True,
                        require_license=True,
                        require_identity=state in APPROVED_RUNTIME_STATES,
                    )
                    findings.extend(evidence_findings)
                    if digest:
                        runtime_hashes[name][target] = digest
                        runtime_manifests[name][target] = manifest
                        runtime_licenses[name][target] = licenses

            if state in APPROVED_RUNTIME_STATES and review_hashes.get(name) != runtime_hashes.get(name):
                findings.append(blocker("promotion_target_drift", "Runtime approval-lineage hashes must equal the approved review-stage hashes", key))

        if state in REVIEW_STATES:
            target_hashes = runtime_hashes if state in APPROVED_RUNTIME_STATES else review_hashes
            target_manifests = review_manifests
            license_evidence = review_licenses
        elif state in RUNTIME_STATES:
            target_hashes = runtime_hashes
            target_manifests = runtime_manifests
            license_evidence = runtime_licenses
        else:
            target_hashes = {}
            target_manifests = {}
            license_evidence = {}

        if state in REVIEW_STATES | RUNTIME_STATES:
            for name in sorted(collection["skills"]):
                key = f"{collection_id}/{name}"
                captured_targets = target_hashes.get(name, {})
                if set(captured_targets) != set(collection["targets"]):
                    findings.append(blocker("target_hash_incomplete", "Every declared target must produce a tree hash", key))
                elif collection.get("adaptation") == "shared-identical" and len(set(captured_targets.values())) != 1:
                    findings.append(blocker("shared_identical_drift", "shared-identical targets must have the same tree hash", key))

        subject_sha256 = _collection_subject(
            collection,
            target_hashes,
            upstream_bindings,
            candidate_hashes,
            candidate_manifests,
            target_manifests,
            license_evidence,
            candidate_inspections,
        )
        for name in sorted(collection["skills"]):
            key = f"{collection_id}/{name}"
            artifact = {
                "collection_id": collection_id,
                "local_name": name,
                "source_revision": _expected_revision(collection, name),
                "local_state": collection["local_state"],
                "review_state": collection.get("review_state", ""),
                "approval_receipt": collection.get("approval_receipt") or None,
                "value_receipt": collection.get("value_receipt") or None,
                "promotion_receipt": collection.get("promotion_receipt") or None,
                "subject_sha256": subject_sha256,
                "targets": {
                    target: {"tree_sha256": digest}
                    for target, digest in sorted(target_hashes.get(name, {}).items())
                },
            }
            if state in CANDIDATE_STATES:
                artifact["upstream"] = upstream_bindings.get(name)
                artifact["quarantine"] = {
                    "tree_sha256": candidate_hashes.get(name),
                    "manifest": candidate_manifests.get(name, []),
                    "license_evidence": candidate_licenses.get(name, []),
                    "static_inspection": candidate_inspections.get(name, {}),
                }
            if state in REVIEW_STATES:
                artifact["review_targets"] = {
                    target: {
                        "tree_sha256": digest,
                        "manifest": review_manifests.get(name, {}).get(target, []),
                        "license_evidence": review_licenses.get(name, {}).get(target, []),
                    }
                    for target, digest in sorted(review_hashes.get(name, {}).items())
                }
            if state in APPROVAL_LINEAGE_STATES:
                artifact["safety_receipt"] = collection.get("safety_receipt")
                artifact["adaptation_diff"] = collection.get("adaptation_diff")
            artifacts[key] = artifact
    lock = {
        "schema_version": LOCK_SCHEMA_VERSION,
        "generation": registry["generation"],
        "registry_sha256": sha256_path(registry_path),
        "hash_algorithm": HASH_ALGORITHM,
        "generated_at": max(baseline_dates) if baseline_dates else "",
        "artifacts": {key: artifacts[key] for key in sorted(artifacts)},
    }
    return lock, findings


def _read_regular_path(path: Path, trusted_root: Path) -> tuple[bytes | None, Finding | None]:
    """Read a regular file beneath a trusted root without following inner symlinks."""
    declared_root = trusted_root.absolute()
    root = Path(os.path.realpath(declared_root)).absolute()
    absolute = path.absolute()
    try:
        relative = absolute.relative_to(declared_root)
    except ValueError:
        return None, blocker("file_root_escape", "File is outside its trusted root", str(path))
    if not relative.parts or ".." in relative.parts:
        return None, blocker("file_root_escape", "File path is not a strict child of its trusted root", str(path))
    root_fd, root_snapshot, root_finding = _open_root_directory(root)
    if root_finding or root_fd is None or root_snapshot is None:
        return None, root_finding or blocker("file_root_unavailable", "Trusted root unavailable", str(root))
    opened: list[tuple[int, os.stat_result, str]] = [(root_fd, root_snapshot, ".")]
    try:
        current_fd = root_fd
        for index, part in enumerate(relative.parts[:-1]):
            display = "/".join(relative.parts[: index + 1])
            try:
                info = os.stat(part, dir_fd=current_fd, follow_symlinks=False)
            except OSError as exc:
                return None, blocker("file_component_unavailable", str(exc), display)
            if stat.S_ISLNK(info.st_mode):
                return None, blocker("file_component_symlink", "Intermediate symlink is not allowed", display)
            if not stat.S_ISDIR(info.st_mode):
                return None, blocker("file_component_not_directory", "Intermediate component is not a directory", display)
            child_fd, child_finding = _open_child_directory_at(current_fd, part, info, display)
            if child_finding or child_fd is None:
                return None, child_finding or blocker("file_component_unavailable", "Intermediate component unavailable", display)
            opened.append((child_fd, os.fstat(child_fd), display))
            current_fd = child_fd
        leaf = relative.parts[-1]
        try:
            info = os.stat(leaf, dir_fd=current_fd, follow_symlinks=False)
        except OSError as exc:
            return None, blocker("file_unavailable", str(exc), str(path))
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            return None, blocker("file_not_regular", "Expected a non-symlink regular file", str(path))
        data, read_finding = _read_regular_file_at(current_fd, leaf, info, str(path))
        if read_finding or data is None:
            return None, read_finding or blocker("file_unavailable", "Regular file unavailable", str(path))

        for fd, snapshot, display in opened:
            try:
                current = os.fstat(fd)
            except OSError as exc:
                return None, blocker("file_path_revalidation_failed", str(exc), display)
            if _directory_snapshot(current) != _directory_snapshot(snapshot):
                return None, blocker("file_path_changed", "Trusted path ancestor changed while reading", display)

        reopened: list[tuple[int, os.stat_result, str]] = []
        check_fd, check_snapshot, check_finding = _open_root_directory(root)
        if check_finding or check_fd is None or check_snapshot is None:
            return None, check_finding or blocker("file_path_unavailable_after_read", "Trusted root unavailable after read", str(root))
        reopened.append((check_fd, check_snapshot, "."))
        try:
            if _directory_snapshot(check_snapshot) != _directory_snapshot(opened[0][1]):
                return None, blocker("file_path_replaced", "Trusted root identity changed while reading", str(root))
            current_check_fd = check_fd
            for index, part in enumerate(relative.parts[:-1]):
                display = "/".join(relative.parts[: index + 1])
                try:
                    mapped = os.stat(part, dir_fd=current_check_fd, follow_symlinks=False)
                except OSError as exc:
                    return None, blocker("file_path_unavailable_after_read", str(exc), display)
                if stat.S_ISLNK(mapped.st_mode) or not stat.S_ISDIR(mapped.st_mode):
                    return None, blocker("file_path_replaced", "Trusted path component was replaced", display)
                child_fd, child_finding = _open_child_directory_at(current_check_fd, part, mapped, display)
                if child_finding or child_fd is None:
                    return None, child_finding or blocker("file_path_unavailable_after_read", "Component unavailable", display)
                child_snapshot = os.fstat(child_fd)
                reopened.append((child_fd, child_snapshot, display))
                if _directory_snapshot(child_snapshot) != _directory_snapshot(opened[index + 1][1]):
                    return None, blocker("file_path_replaced", "Trusted path component identity changed", display)
                current_check_fd = child_fd
            try:
                mapped_leaf = os.stat(leaf, dir_fd=current_check_fd, follow_symlinks=False)
            except OSError as exc:
                return None, blocker("file_path_unavailable_after_read", str(exc), str(path))
            if stat.S_ISLNK(mapped_leaf.st_mode) or _file_snapshot(mapped_leaf) != _file_snapshot(info):
                return None, blocker("file_path_replaced", "Trusted file mapping changed while reading", str(path))
            for index, (_, snapshot, display) in enumerate(reopened):
                try:
                    if index == 0:
                        mapped = root.lstat()
                    else:
                        mapped = os.stat(
                            relative.parts[index - 1],
                            dir_fd=reopened[index - 1][0],
                            follow_symlinks=False,
                        )
                except OSError as exc:
                    return None, blocker("file_path_revalidation_failed", str(exc), display)
                if stat.S_ISLNK(mapped.st_mode) or _directory_snapshot(mapped) != _directory_snapshot(snapshot):
                    return None, blocker("file_path_replaced", "Trusted path mapping changed during final revalidation", display)
        finally:
            for fd, _, _ in reversed(reopened):
                try:
                    os.close(fd)
                except OSError:
                    pass
        return data, None
    finally:
        for fd, _, _ in reversed(opened):
            try:
                os.close(fd)
            except OSError:
                pass


def _frontmatter_and_body(data: bytes, path: str) -> tuple[dict[str, Any], bytes, list[Finding]]:
    values, findings = parse_frontmatter_strict(data, path)
    lines = data.splitlines(keepends=True)
    end = next((index for index, line in enumerate(lines[1:], start=1) if line.rstrip(b"\r\n") == b"---"), None)
    if end is None:
        return values, b"", findings
    return values, b"".join(lines[end + 1 :]), findings


def _extract_contract(raw: bytes, start_marker: str, end_marker: str, path: str) -> tuple[bytes | None, Finding | None]:
    start = start_marker.encode("utf-8")
    end = end_marker.encode("utf-8")
    if raw.count(start) != 1 or raw.count(end) != 1:
        return None, blocker("integration_contract_marker", "Contract markers must each occur exactly once", path)
    start_index = raw.find(start)
    end_index = raw.find(end)
    if end_index < start_index + len(start):
        return None, blocker("integration_contract_order", "Contract end marker must follow its start marker", path)
    if end_index <= start_index + len(start):
        return None, blocker("integration_contract_empty", "Contract block must be non-empty", path)
    return raw[start_index : end_index + len(end)], None


def _openai_policy_findings(raw: bytes, path: str) -> list[Finding]:
    if raw != CANONICAL_OPENAI_ADAPTER:
        return [
            blocker(
                "openai_adapter_policy_shape",
                "OpenAI adapter bytes must match the reviewed canonical non-implicit policy",
                path,
            )
        ]
    return []


def parity_payload(registry: dict[str, Any]) -> tuple[dict[str, Any], list[Finding]]:
    findings: list[Finding] = []
    parity = registry.get("parity", {})
    authority_declared = expand_path(parity.get("authority_package", "")).absolute()
    replica_declared = expand_path(parity.get("replica_package", "")).absolute()
    for side, declared in (("authority", authority_declared), ("replica", replica_declared)):
        try:
            info = declared.lstat()
        except OSError as exc:
            findings.append(blocker("package_root_unavailable", str(exc), side))
        else:
            if stat.S_ISLNK(info.st_mode):
                findings.append(blocker("package_root_symlink", "Governance package root cannot be a symlink", side))
    authority = Path(os.path.realpath(authority_declared))
    replica = Path(os.path.realpath(replica_declared))
    checked: list[dict[str, Any]] = []
    authority_tree = scan_tree(authority)
    replica_tree = scan_tree(replica)
    findings.extend(authority_tree.findings)
    findings.extend(replica_tree.findings)
    authority_files = {record.path: record for record in authority_tree.files}
    replica_files = {record.path: record for record in replica_tree.files}
    authority_paths = set(authority_files)
    replica_paths = set(replica_files)
    if authority_paths != replica_paths:
        findings.append(
            blocker(
                "package_file_set_drift",
                f"authority_only={sorted(authority_paths - replica_paths)} replica_only={sorted(replica_paths - authority_paths)}",
                "skill-governance",
            )
        )
    for relative in sorted(authority_paths & replica_paths):
        if relative == "SKILL.md":
            continue
        left_record = authority_files[relative]
        right_record = replica_files[relative]
        equal = left_record.data == right_record.data and left_record.executable == right_record.executable
        checked.append({"path": relative, "equal": equal, "sha256": left_record.sha256})
        if not equal:
            findings.append(blocker("replica_drift", "Authority and replica package bytes or mode differ", relative))
    configured_shared = set(parity.get("shared_paths", []))
    if not configured_shared.issubset(authority_paths & replica_paths):
        findings.append(
            blocker(
                "parity_missing",
                f"Configured shared paths missing: {sorted(configured_shared - (authority_paths & replica_paths))}",
            )
        )

    codex_skill = authority / "SKILL.md"
    claude_skill = replica / "SKILL.md"
    codex_data, codex_read_finding = _read_regular_path(codex_skill, authority)
    claude_data, claude_read_finding = _read_regular_path(claude_skill, replica)
    if codex_read_finding or claude_read_finding or codex_data is None or claude_data is None:
        findings.extend(item for item in (codex_read_finding, claude_read_finding) if item is not None)
        findings.append(blocker("adapter_missing", "Platform SKILL.md is missing or unsafe"))
    else:
        codex_values, codex_body, codex_findings = _frontmatter_and_body(codex_data, str(codex_skill))
        claude_values, claude_body, claude_findings = _frontmatter_and_body(claude_data, str(claude_skill))
        findings.extend(codex_findings)
        findings.extend(claude_findings)
        normalized_claude = dict(claude_values)
        normalized_claude.pop("disable-model-invocation", None)
        if codex_values != normalized_claude:
            findings.append(blocker("adapter_frontmatter_drift", "Platform frontmatter differs beyond the permitted Claude key", "SKILL.md"))
        if codex_body != claude_body:
            findings.append(blocker("adapter_body_drift", "Codex and Claude SKILL.md bodies differ", "SKILL.md"))
        if authority_files.get("SKILL.md") and replica_files.get("SKILL.md") and (
            authority_files["SKILL.md"].executable != replica_files["SKILL.md"].executable
        ):
            findings.append(blocker("adapter_mode_drift", "Codex and Claude SKILL.md executable bits differ", "SKILL.md"))
        if "disable-model-invocation" in codex_values:
            findings.append(blocker("codex_claude_key", "Codex SKILL.md contains Claude-only invocation key", str(codex_skill)))
        if claude_values.get("disable-model-invocation") is not True:
            findings.append(blocker("claude_implicit_invocation", "Claude must disable model invocation", str(claude_skill)))

    for package in (authority, replica):
        openai_yaml = package / "agents/openai.yaml"
        raw, read_finding = _read_regular_path(openai_yaml, package)
        if read_finding or raw is None:
            findings.append(read_finding or blocker("openai_adapter_missing", "Adapter missing", str(openai_yaml)))
        else:
            findings.extend(_openai_policy_findings(raw, str(openai_yaml)))

    authority_repo = Path(os.path.realpath(authority.parents[1]))
    replica_repo = Path(os.path.realpath(replica.parents[1]))
    for relative in parity.get("shared_repo_paths", []):
        left = authority_repo / relative
        right = replica_repo / relative
        left_data, left_finding = _read_regular_path(left, authority_repo)
        right_data, right_finding = _read_regular_path(right, replica_repo)
        if left_finding or right_finding or left_data is None or right_data is None or left_data != right_data:
            findings.extend(item for item in (left_finding, right_finding) if item is not None)
            findings.append(blocker("integration_replica_drift", "Shared integration artifact differs", relative))

    for check in parity.get("integration_checks", []):
        check_id = str(check.get("id", "integration"))
        contract_by_side: dict[str, bytes] = {}
        for side, repo, path_key in (
            ("codex", authority_repo, "codex_path"),
            ("claude", replica_repo, "claude_path"),
        ):
            relative = str(check.get(path_key, ""))
            raw, read_finding = _read_regular_path(repo / relative, repo)
            if read_finding or raw is None:
                findings.append(read_finding or blocker("integration_missing", "Integration file missing", f"{side}:{relative}"))
                continue
            contract, contract_finding = _extract_contract(
                raw,
                str(check.get("start_marker", "")),
                str(check.get("end_marker", "")),
                f"{side}:{relative}",
            )
            if contract_finding or contract is None:
                findings.append(contract_finding or blocker("integration_contract_missing", "Contract block missing", f"{side}:{relative}"))
                continue
            contract_by_side[side] = contract
            if sha256_bytes(contract) != check.get("sha256"):
                findings.append(blocker("integration_contract_digest", "Contract block differs from the registered digest", f"{check_id}:{side}:{relative}"))
        if set(contract_by_side) == {"codex", "claude"} and contract_by_side["codex"] != contract_by_side["claude"]:
            findings.append(blocker("integration_contract_replica_drift", "Codex and Claude contract blocks differ", check_id))
    status = "DEGRADED" if has_blockers(findings) else "ok"
    return {
        "command": "parity",
        "status": status,
        "authority": str(authority),
        "replica": str(replica),
        "generation": registry.get("generation"),
        "checked": checked,
        "findings": [asdict(item) for item in findings],
    }, findings


def usage_evidence() -> dict[str, Any]:
    result: dict[str, Any] = {
        "codex": {"observability": "unobservable", "reason": "no configured skill usage log"},
        "claude": {"observability": "unobservable"},
    }
    path = expand_path("~/.claude/skill-usage.jsonl")
    if not path.is_file():
        result["claude"]["reason"] = "usage log missing"
        return result
    latest = ""
    events = 0
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = _strict_json_loads(line)
            timestamp = str(payload.get("timestamp", ""))
            latest = max(latest, timestamp)
            events += 1
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, StrictJSONError) as exc:
        result["claude"] = {"observability": "unreliable", "reason": str(exc)}
        return result
    result["claude"] = {
        "observability": "partial",
        "events": events,
        "latest_event": latest,
        "note": "usage is advisory; zero events is not a retire verdict",
    }
    return result


def active_collision_findings(registry: dict[str, Any], runtime: str, name: str) -> list[Finding]:
    findings: list[Finding] = []
    matching: list[tuple[str, str, int | None]] = []
    for root_id, root in registry_roots(registry).items():
        if runtime not in root.get("runtimes", []):
            continue
        if root.get("collision_scope") != "runtime":
            continue
        candidate = expand_path(root["path"]) / name
        if not (candidate / "SKILL.md").is_file():
            continue
        tree = scan_tree(candidate)
        findings.extend(tree.findings)
        if tree.tree_sha256:
            precedence = root.get("precedence") if isinstance(root.get("precedence"), int) else None
            matching.append((root_id, tree.tree_sha256, precedence))
    if len({digest for _, digest, _ in matching}) > 1:
        priorities = [precedence for _, _, precedence in matching if precedence is not None]
        if len(priorities) != len(matching):
            findings.append(blocker("active_name_collision", f"Different content with unknown precedence in {runtime}: {matching}", name))
        else:
            winning_precedence = min(priorities)
            winners = [item for item in matching if item[2] == winning_precedence]
            if len(winners) != 1:
                findings.append(blocker("active_name_collision", f"Ambiguous same-precedence content in {runtime}: {matching}", name))
            else:
                findings.append(
                    advisory(
                        "active_shadow_override",
                        f"Deterministic project/root precedence selects {winners[0][0]} in {runtime}: {matching}",
                        name,
                    )
                )
    return findings


def estate_collision_findings(registry: dict[str, Any], inventory: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    roots = registry_roots(registry)
    by_name: dict[str, list[dict[str, Any]]] = {}
    for record in inventory.get("records", []):
        if record.get("disabled_by_selector") is True:
            continue
        root = roots.get(record.get("root_id"), {})
        if root.get("collision_scope") != "runtime":
            continue
        by_name.setdefault(str(record.get("logical_name")), []).append(record)
    for name, records in sorted(by_name.items()):
        runtimes = sorted({runtime for record in records for runtime in record.get("runtimes", [])})
        for runtime in runtimes:
            matching = [record for record in records if runtime in record.get("runtimes", [])]
            hashes = {record.get("tree_sha256") for record in matching if record.get("tree_sha256")}
            if len(matching) < 2 or len(hashes) < 2:
                continue
            priorities = [record.get("precedence") for record in matching]
            if any(not isinstance(value, int) for value in priorities):
                findings.append(blocker("active_name_collision", f"Different content with unknown precedence in {runtime}", name))
                continue
            winning_precedence = min(priorities)
            winners = [record for record in matching if record.get("precedence") == winning_precedence]
            if len(winners) != 1:
                findings.append(blocker("active_name_collision", f"Ambiguous same-precedence content in {runtime}", name))
                continue
            findings.append(
                advisory(
                    "active_shadow_override",
                    f"{winners[0]['root_id']} wins by precedence in {runtime}; shadowed roots remain inventoried",
                    name,
                )
            )
    return findings


def _load_receipt(reference: dict[str, Any]) -> tuple[dict[str, Any] | None, list[Finding]]:
    findings: list[Finding] = []
    if not _receipt_ref_valid(reference):
        return None, [blocker("invalid_receipt_reference", "Receipt reference is not path/hash bound")]
    path = BASE_DIR / reference["path"]
    raw, read_finding = _read_regular_path(path, BASE_DIR)
    if read_finding or raw is None:
        return None, [read_finding or blocker("receipt_unreadable", "Receipt unavailable", str(path))]
    if sha256_bytes(raw) != reference["sha256"]:
        findings.append(blocker("receipt_digest_mismatch", "Receipt bytes differ from the registered SHA-256", str(path)))
    try:
        payload = _strict_json_loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError, StrictJSONError) as exc:
        findings.append(blocker("receipt_invalid_json", str(exc), str(path)))
        return None, findings
    if not isinstance(payload, dict):
        findings.append(blocker("receipt_shape", "Receipt must be a JSON object", str(path)))
        return None, findings
    return payload, findings


def _load_bound_artifact(reference: dict[str, Any], directory: str) -> tuple[bytes | None, list[Finding]]:
    if not _bound_ref_valid(reference, directory):
        return None, [blocker("invalid_artifact_reference", f"Artifact must be a path/hash-bound {directory}/* file")]
    path = BASE_DIR / reference["path"]
    raw, read_finding = _read_regular_path(path, BASE_DIR)
    if read_finding or raw is None:
        return None, [read_finding or blocker("artifact_unreadable", "Bound artifact unavailable", str(path))]
    if sha256_bytes(raw) != reference["sha256"]:
        return None, [blocker("artifact_digest_mismatch", "Artifact bytes differ from the registered SHA-256", str(path))]
    return raw, []


def _valid_score(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value <= 1


def _skill_sha_from_manifest(manifest: list[dict[str, Any]]) -> str | None:
    record = next((item for item in manifest if item.get("path") == "SKILL.md"), None)
    digest = record.get("sha256") if isinstance(record, dict) else None
    return digest if isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest) else None


def audit_frontmatter_receipts(
    registry: dict[str, Any],
    collection: dict[str, Any],
    upstream_bindings: dict[str, dict[str, Any]],
    candidate_manifests: dict[str, list[dict[str, Any]]],
    target_manifests: dict[str, dict[str, list[dict[str, Any]]]],
) -> list[Finding]:
    findings: list[Finding] = []
    references = collection.get("frontmatter_receipts")
    if not isinstance(references, dict):
        return [blocker("frontmatter_receipt_map", "Full frontmatter validation receipts are required", collection["id"])]
    roots = registry_roots(registry)
    for name in sorted(collection.get("skills", [])):
        by_surface = references.get(name)
        if not isinstance(by_surface, dict):
            findings.append(blocker("frontmatter_receipt_map", "Skill receipt map is missing", f"{collection['id']}/{name}"))
            continue
        surfaces = {
            "quarantine": (
                {"common", "claude"},
                str(upstream_bindings.get(name, {}).get("upstream_name", "")),
                candidate_manifests.get(name, []),
                {
                    "kind": "quarantine",
                    "source_id": str(collection.get("source_id", "")),
                    "revision": _expected_revision(collection, name),
                    "skill_name": str(upstream_bindings.get(name, {}).get("upstream_name", "")),
                },
            )
        }
        for target in collection.get("targets", []):
            runtimes = set(roots.get(target, {}).get("runtimes", []))
            target_schema = "codex" if runtimes == {"codex"} else "claude" if runtimes == {"claude"} else "common"
            surfaces[target] = (
                {target_schema},
                name,
                target_manifests.get(name, {}).get(target, []),
                {
                    "kind": "review",
                    "collection_id": str(collection.get("id", "")),
                    "skill_name": name,
                    "target_id": target,
                },
            )
        for surface, (target_schemas, expected_name, manifest, expected_surface) in surfaces.items():
            reference = by_surface.get(surface)
            receipt, receipt_findings = _load_receipt(reference)
            findings.extend(receipt_findings)
            expected_skill_sha = _skill_sha_from_manifest(manifest)
            if receipt is None:
                continue
            if (
                receipt.get("command") != "validate-frontmatter"
                or receipt.get("status") != "validated"
                or receipt.get("target") not in target_schemas
                or receipt.get("surface") != expected_surface
                or receipt.get("validator") != "pyyaml-6.0.2-safe-loader"
                or receipt.get("skill_sha256") != expected_skill_sha
                or not isinstance(receipt.get("values"), dict)
                or receipt["values"].get("name") != expected_name
                or receipt.get("findings") != []
            ):
                findings.append(blocker("frontmatter_receipt_binding", "Full validator receipt does not bind the captured SKILL.md and expected platform/name", f"{collection['id']}/{name}:{surface}"))
    return findings


def audit_collection_receipts(
    registry: dict[str, Any],
    collection: dict[str, Any],
    subject_sha256: str,
    upstream_bindings: dict[str, dict[str, Any]],
    target_hashes: dict[str, dict[str, str]],
    candidate_hashes: dict[str, str],
    candidate_manifests: dict[str, list[dict[str, Any]]],
    target_manifests: dict[str, dict[str, list[dict[str, Any]]]],
    license_evidence: dict[str, dict[str, list[dict[str, str]]]],
    candidate_inspections: dict[str, dict[str, Any]],
    approved_target_hashes: dict[str, dict[str, str]] | None = None,
    as_of: str | None = None,
) -> list[Finding]:
    if collection.get("local_state") not in APPROVAL_LINEAGE_STATES:
        return []
    findings: list[Finding] = []
    audit_date = as_of or datetime.now(timezone.utc).date().isoformat()
    if not _valid_date_string(audit_date):
        return [blocker("audit_date", "as_of must be YYYY-MM-DD", collection["id"])]
    findings.extend(
        audit_frontmatter_receipts(
            registry,
            collection,
            upstream_bindings,
            candidate_manifests,
            target_manifests,
        )
    )
    _, adaptation_findings = _load_bound_artifact(collection.get("adaptation_diff"), "adaptations")
    findings.extend(adaptation_findings)
    safety, safety_findings = _load_receipt(collection["safety_receipt"])
    findings.extend(safety_findings)
    if safety is not None:
        required_safety = {
            "schema_version",
            "kind",
            "collection_id",
            "generation",
            "subject_sha256",
            "upstream",
            "targets",
            "quarantine",
            "candidate_manifests",
            "target_manifests",
            "license_evidence",
            "license_review",
            "static_inspection",
            "adaptation_review",
            "adaptation_diff",
            "capabilities",
            "dependencies",
            "external_urls",
            "reviewer",
            "date",
            "next_review_date",
            "decision",
        }
        missing = sorted(required_safety - set(safety))
        if missing:
            findings.append(blocker("safety_receipt_fields", f"Missing fields: {missing}", collection["id"]))
        expected_upstream_licenses = {
            name: binding.get("license_paths", [])
            for name, binding in sorted(upstream_bindings.items())
        }
        expected_license_review = {
            "declared": collection.get("license"),
            "upstream_paths": expected_upstream_licenses,
            "local_evidence": license_evidence,
            "decision": "pass",
        }
        if (
            safety.get("schema_version") != 1
            or safety.get("kind") != "safety"
            or safety.get("collection_id") != collection["id"]
            or safety.get("generation") != registry.get("generation")
            or safety.get("subject_sha256") != subject_sha256
            or safety.get("upstream") != upstream_bindings
            or safety.get("targets") != target_hashes
            or safety.get("quarantine") != candidate_hashes
            or safety.get("candidate_manifests") != candidate_manifests
            or safety.get("target_manifests") != target_manifests
            or safety.get("license_evidence") != license_evidence
            or safety.get("license_review") != expected_license_review
            or safety.get("adaptation_diff") != collection.get("adaptation_diff")
            or safety.get("decision") != "pass"
            or safety.get("static_inspection") != candidate_inspections
            or safety.get("adaptation_review") in (None, "", [], {})
            or not isinstance(safety.get("capabilities"), list)
            or not safety.get("capabilities")
            or not isinstance(safety.get("dependencies"), list)
            or not isinstance(safety.get("external_urls"), list)
            or safety.get("reviewer") in (None, "", [], {})
        ):
            findings.append(blocker("safety_receipt_binding", "Safety receipt must bind provenance, full manifests, license evidence, static inspection, and adaptation review", collection["id"]))
        if not _valid_date_string(safety.get("date")):
            findings.append(blocker("receipt_date", "Safety receipt date must be YYYY-MM-DD", collection["id"]))
        if (
            not _valid_date_string(safety.get("next_review_date"))
            or str(safety.get("next_review_date", "")) < str(safety.get("date", ""))
        ):
            findings.append(blocker("receipt_next_review_date", "next_review_date must be a valid date on or after the review date", collection["id"]))
        elif str(safety.get("next_review_date")) < audit_date:
            findings.append(blocker("review_expired", f"Safety review expired before {audit_date}", collection["id"]))

    value, value_findings = _load_receipt(collection["value_receipt"])
    findings.extend(value_findings)
    if value is not None:
        required_value = {
            "schema_version",
            "kind",
            "collection_id",
            "generation",
            "subject_sha256",
            "representative_prompts",
            "baseline",
            "candidate",
            "trial_count",
            "pass_at_1",
            "trigger_precision",
            "trigger_recall",
            "outcome_rubric",
            "reviewer",
            "date",
            "decision",
        }
        missing = sorted(required_value - set(value))
        if missing:
            findings.append(blocker("value_receipt_fields", f"Missing fields: {missing}", collection["id"]))
        if (
            value.get("schema_version") != 1
            or value.get("kind") != "value"
            or value.get("collection_id") != collection["id"]
            or value.get("generation") != registry.get("generation")
            or value.get("subject_sha256") != subject_sha256
            or value.get("decision") != "pass"
        ):
            findings.append(blocker("value_receipt_binding", "Value receipt identity or subject binding differs", collection["id"]))
        if not isinstance(value.get("representative_prompts"), list) or not value.get("representative_prompts"):
            findings.append(blocker("value_receipt_prompts", "Representative prompts must be non-empty", collection["id"]))
        if not isinstance(value.get("trial_count"), int) or value.get("trial_count", 0) < 1:
            findings.append(blocker("value_receipt_trials", "trial_count must be positive", collection["id"]))
        for field_name in ("pass_at_1", "trigger_precision", "trigger_recall"):
            if not _valid_score(value.get(field_name)):
                findings.append(blocker("value_receipt_metric", f"{field_name} must be in [0,1]", collection["id"]))
        for field_name in ("baseline", "candidate", "outcome_rubric", "reviewer"):
            if value.get(field_name) in (None, "", [], {}):
                findings.append(blocker("value_receipt_evidence", f"{field_name} must be non-empty", collection["id"]))
        if not _valid_date_string(value.get("date")):
            findings.append(blocker("receipt_date", "Value receipt date must be YYYY-MM-DD", collection["id"]))

    approval, approval_findings = _load_receipt(collection["approval_receipt"])
    findings.extend(approval_findings)
    if approval is not None:
        approver = approval.get("approver")
        if (
            approval.get("schema_version") != 1
            or approval.get("kind") != "approval"
            or approval.get("collection_id") != collection["id"]
            or approval.get("generation") != registry.get("generation")
            or approval.get("subject_sha256") != subject_sha256
            or approval.get("safety_receipt_sha256") != collection["safety_receipt"]["sha256"]
            or approval.get("value_receipt_sha256") != collection["value_receipt"]["sha256"]
            or approval.get("decision") != "approved"
            or not isinstance(approver, dict)
            or approver.get("type") != "human"
            or not approver.get("name")
        ):
            findings.append(blocker("approval_receipt_binding", "Approval must be human and bind subject plus safety and value receipts", collection["id"]))
        if not _valid_date_string(approval.get("date")):
            findings.append(blocker("receipt_date", "Approval receipt date must be YYYY-MM-DD", collection["id"]))

    if collection.get("local_state") in APPROVED_RUNTIME_STATES:
        promotion, promotion_findings = _load_receipt(collection["promotion_receipt"])
        findings.extend(promotion_findings)
        approved_targets = approved_target_hashes or {}
        if approved_targets != target_hashes:
            findings.append(blocker("promotion_target_drift", "Approved review hashes differ from active runtime hashes", collection["id"]))
        if promotion is not None:
            required_promotion = {
                "schema_version",
                "kind",
                "collection_id",
                "generation",
                "subject_sha256",
                "approval_receipt_sha256",
                "quarantine",
                "approved_targets",
                "runtime_targets",
                "date",
                "decision",
            }
            if sorted(required_promotion - set(promotion)):
                findings.append(blocker("promotion_receipt_fields", f"Missing fields: {sorted(required_promotion - set(promotion))}", collection["id"]))
            if (
                promotion.get("schema_version") != 1
                or promotion.get("kind") != "promotion"
                or promotion.get("collection_id") != collection["id"]
                or promotion.get("generation") != registry.get("generation")
                or promotion.get("subject_sha256") != subject_sha256
                or promotion.get("approval_receipt_sha256") != collection["approval_receipt"]["sha256"]
                or promotion.get("quarantine") != candidate_hashes
                or promotion.get("approved_targets") != approved_targets
                or promotion.get("runtime_targets") != target_hashes
                or promotion.get("decision") != "promoted"
            ):
                findings.append(blocker("promotion_receipt_binding", "Promotion receipt must bind quarantine plus identical approved/runtime hashes", collection["id"]))
            if not _valid_date_string(promotion.get("date")):
                findings.append(blocker("receipt_date", "Promotion receipt date must be YYYY-MM-DD", collection["id"]))
    return findings


def audit_holds(registry: dict[str, Any]) -> tuple[list[dict[str, Any]], list[Finding]]:
    findings: list[Finding] = []
    rows: list[dict[str, Any]] = []
    for hold in registry.get("holds", []):
        repo = expand_path(hold["repo"])
        raw, error = _run_git(repo, ["ls-files", "-u", "-z", "--", *hold["paths"]])
        if error or raw is None:
            findings.append(blocker("hold_probe_failed", error or "Hold probe unavailable", hold["id"]))
            rows.append({"id": hold["id"], "status": "unavailable"})
            continue
        conflicts = sorted(
            {
                record.split(b"\t", 1)[1].decode("utf-8", "strict")
                for record in raw.split(b"\0")
                if b"\t" in record
            }
        )
        dirty_raw, dirty_error = _run_git(repo, ["status", "--porcelain=v1", "-z", "--", *hold["paths"]])
        if dirty_error or dirty_raw is None:
            findings.append(blocker("hold_probe_failed", dirty_error or "Hold dirty probe unavailable", hold["id"]))
            rows.append({"id": hold["id"], "status": "unavailable"})
            continue
        dirty = sorted(
            {
                record[3:].decode("utf-8", "strict") if len(record) > 3 else record.decode("utf-8", "strict")
                for record in dirty_raw.split(b"\0")
                if record
            }
        )
        if conflicts or dirty:
            findings.append(blocker("active_mutation_hold", f"Unmerged or dirty paths block governed mutation: conflicts={conflicts} dirty={dirty}", hold["id"]))
            status = "active"
        else:
            findings.append(advisory("stale_hold", "Configured hold has no matching unmerged or dirty path", hold["id"]))
            status = "stale"
        rows.append({"id": hold["id"], "status": status, "conflicts": conflicts, "dirty": dirty, "applies_to_roots": hold["applies_to_roots"]})
    return rows, findings


def lock_consistency_findings(lock: dict[str, Any], planned_lock: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    allowed_lock_keys = {"schema_version", "generation", "registry_sha256", "hash_algorithm", "generated_at", "artifacts"}
    missing_top_level = sorted(allowed_lock_keys - set(lock))
    extra_top_level = sorted(set(lock) - allowed_lock_keys)
    if missing_top_level:
        findings.append(blocker("lock_missing_fields", f"Missing top-level fields: {missing_top_level}"))
    if extra_top_level:
        findings.append(blocker("lock_unknown_fields", f"Unknown top-level fields: {extra_top_level}"))
    if lock.get("generated_at") != planned_lock.get("generated_at"):
        findings.append(blocker("lock_generated_at_mismatch", "generated_at differs from the deterministic plan"))
    artifacts = lock.get("artifacts", {}) if isinstance(lock.get("artifacts"), dict) else {}
    planned_artifacts = planned_lock.get("artifacts", {}) if isinstance(planned_lock.get("artifacts"), dict) else {}
    actual_keys = set(artifacts)
    expected_keys = set(planned_artifacts)
    for key in sorted(expected_keys - actual_keys):
        findings.append(blocker("lock_artifact_missing", "Artifact missing from lock", key))
    for key in sorted(actual_keys - expected_keys):
        findings.append(blocker("lock_artifact_extra", "Stale artifact is not present in registry", key))
    for key in sorted(actual_keys & expected_keys):
        entry = artifacts[key]
        expected = planned_artifacts[key]
        if not isinstance(entry, dict) or not isinstance(expected, dict):
            findings.append(blocker("lock_artifact_shape", "Artifact entries must be objects", key))
            continue
        if set(entry) != set(expected):
            findings.append(
                blocker(
                    "lock_artifact_fields",
                    f"expected={sorted(expected)} actual={sorted(entry)}",
                    key,
                )
            )
        expected_targets = set(expected.get("targets", {}))
        actual_targets = set(entry.get("targets", {})) if isinstance(entry.get("targets"), dict) else set()
        if expected_targets != actual_targets:
            findings.append(blocker("lock_target_set_mismatch", f"expected={sorted(expected_targets)} actual={sorted(actual_targets)}", key))
        for target, target_value in entry.get("targets", {}).items() if isinstance(entry.get("targets"), dict) else []:
            if not isinstance(target_value, dict) or set(target_value) != {"tree_sha256"}:
                findings.append(blocker("lock_target_fields", "Target entries must contain only tree_sha256", f"{key}:{target}"))
        for field_name in sorted(set(expected) - {"targets"}):
            if entry.get(field_name) != expected.get(field_name):
                findings.append(blocker("lock_field_mismatch", f"{field_name} differs", key))
        if entry.get("targets") != expected.get("targets"):
            findings.append(blocker("baseline_drift", "Installed target tree differs from lock", key))
    return findings


def audit_payload(
    registry_path: Path,
    lock_path: Path,
    catalog_path: Path,
    estate_path: Path = DEFAULT_ESTATE,
    reputation_path: Path = DEFAULT_REPUTATION,
) -> tuple[dict[str, Any], list[Finding]]:
    registry, findings = load_registry(registry_path)
    if has_blockers(findings):
        payload = {"command": "audit", "status": "blocked", "findings": [asdict(item) for item in findings]}
        return payload, findings
    lock, lock_findings = load_lock(lock_path)
    findings.extend(lock_findings)
    if not lock_findings:
        if lock.get("generation") != registry.get("generation"):
            findings.append(blocker("generation_mismatch", "Registry and lock generation differ"))
        if lock.get("registry_sha256") != sha256_path(registry_path):
            findings.append(blocker("registry_lock_binding", "Lock is not bound to the current registry"))

    estate_inventory = inventory_payload(registry)
    findings.extend(Finding(**item) for item in estate_inventory.get("findings", []))
    findings.extend(estate_collision_findings(registry, estate_inventory))
    estate_lock, estate_lock_findings = load_estate_lock(estate_path)
    findings.extend(estate_lock_findings)
    planned_estate = planned_estate_lock(registry, registry_path, estate_inventory)
    if not estate_lock_findings:
        findings.extend(estate_consistency_findings(estate_lock, planned_estate))
    catalog, catalog_findings = catalog_payload(registry, registry_path, catalog_path)
    findings.extend(catalog_findings)
    catalog_lock, catalog_lock_findings = load_catalog(catalog_path)
    findings.extend(catalog_lock_findings)
    reputation, reputation_findings = load_reputation(reputation_path, registry)
    findings.extend(reputation_findings)
    findings.extend(reputation_promotion_findings(registry, reputation))

    artifacts = lock.get("artifacts", {}) if isinstance(lock, dict) else {}
    planned_lock, plan_findings = build_lock_plan(
        registry,
        registry_path,
        catalog_lock,
        runtime_inventory=estate_inventory,
    )
    findings.extend(plan_findings)
    planned_artifacts = planned_lock.get("artifacts", {})
    findings.extend(lock_consistency_findings(lock, planned_lock))
    checked = sum(len(entry.get("targets", {})) for entry in planned_artifacts.values())
    legacy_count = 0
    for collection in registry.get("collections", []):
        if collection.get("local_state") == "legacy-active":
            legacy_count += len(collection.get("skills", []))
        subject_sha256 = ""
        receipt_targets: dict[str, dict[str, str]] = {}
        receipt_upstream: dict[str, dict[str, Any]] = {}
        receipt_candidates: dict[str, str] = {}
        receipt_candidate_manifests: dict[str, list[dict[str, Any]]] = {}
        receipt_candidate_inspections: dict[str, dict[str, Any]] = {}
        receipt_target_manifests: dict[str, dict[str, list[dict[str, Any]]]] = {}
        receipt_license_evidence: dict[str, dict[str, list[dict[str, str]]]] = {}
        receipt_approved_targets: dict[str, dict[str, str]] = {}
        for name in collection.get("skills", []):
            key = f"{collection['id']}/{name}"
            entry = artifacts.get(key)
            expected = planned_artifacts.get(key)
            if not isinstance(entry, dict) or not isinstance(expected, dict):
                continue
            subject_sha256 = str(expected.get("subject_sha256", ""))
            receipt_targets[name] = {
                target: str(value.get("tree_sha256", ""))
                for target, value in expected.get("targets", {}).items()
                if isinstance(value, dict)
            }
            if isinstance(expected.get("upstream"), dict):
                receipt_upstream[name] = expected["upstream"]
            quarantine = expected.get("quarantine")
            if isinstance(quarantine, dict):
                if isinstance(quarantine.get("tree_sha256"), str):
                    receipt_candidates[name] = quarantine["tree_sha256"]
                if isinstance(quarantine.get("manifest"), list):
                    receipt_candidate_manifests[name] = quarantine["manifest"]
                if isinstance(quarantine.get("static_inspection"), dict):
                    receipt_candidate_inspections[name] = quarantine["static_inspection"]
            review_targets = expected.get("review_targets")
            if isinstance(review_targets, dict):
                receipt_target_manifests[name] = {}
                receipt_license_evidence[name] = {}
                receipt_approved_targets[name] = {}
                for target, evidence in review_targets.items():
                    if not isinstance(evidence, dict):
                        continue
                    if isinstance(evidence.get("tree_sha256"), str):
                        receipt_approved_targets[name][target] = evidence["tree_sha256"]
                    if isinstance(evidence.get("manifest"), list):
                        receipt_target_manifests[name][target] = evidence["manifest"]
                    if isinstance(evidence.get("license_evidence"), list):
                        receipt_license_evidence[name][target] = evidence["license_evidence"]
        if subject_sha256:
            findings.extend(
                audit_collection_receipts(
                    registry,
                    collection,
                    subject_sha256,
                    receipt_upstream,
                    receipt_targets,
                    receipt_candidates,
                    receipt_candidate_manifests,
                    receipt_target_manifests,
                    receipt_license_evidence,
                    receipt_candidate_inspections,
                    receipt_approved_targets,
                )
            )

    holds, hold_findings = audit_holds(registry)
    findings.extend(hold_findings)

    parity, parity_findings = parity_payload(registry)
    findings.extend(parity_findings)
    status = "DEGRADED" if has_blockers(findings) else "ok"
    payload = {
        "command": "audit",
        "status": status,
        "generation": registry.get("generation"),
        "registry_sha256": sha256_path(registry_path),
        "checked_target_artifacts": checked,
        "legacy_active_count": legacy_count,
        "legacy_notice": "integrity baseline only; not approval evidence",
        "estate_summary": estate_inventory.get("summary", {}),
        "runtime_estate_lock_records": len(planned_estate.get("records", [])),
        "estate_coverage": estate_inventory.get("coverage", {}),
        "surface_probe": estate_inventory.get("surface_probe", {}),
        "catalog_status": catalog.get("status"),
        "catalog_summary": catalog.get("summary", {}),
        "reputation_snapshot": {
            "generated_at": reputation.get("generated_at"),
            "source_count": len(reputation.get("snapshots", [])) if isinstance(reputation.get("snapshots"), list) else 0,
            "policy": reputation.get("policy"),
        },
        "usage": usage_evidence(),
        "parity_status": parity["status"],
        "holds": holds,
        "mutation_allowed": not has_blockers(findings),
        "findings": [asdict(item) for item in findings],
    }
    return payload, findings


DANGEROUS_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "download_and_execute",
        re.compile(r"(?is)\b(?:curl|wget)\b[^\n|]{0,240}\|\s*(?:sh|bash|zsh|python)\b"),
        "Download-and-execute instruction",
    ),
    (
        "encoded_execute",
        re.compile(r"(?is)\bbase64\b[^\n]{0,200}(?:--decode|-d)[^\n|]{0,200}\|\s*(?:sh|bash|zsh|python)\b"),
        "Decode-and-execute instruction",
    ),
    (
        "credential_path",
        re.compile(r"(?i)(?:~/?\.(?:ssh|aws|gnupg)|\b\.env\b|keychain|browser\s+profile|wallet)"),
        "Credential or sensitive profile reference",
    ),
    (
        "global_agent_config",
        re.compile(r"(?i)(?:~/?\.codex/(?:config\.toml|AGENTS\.md)|~/?\.claude/(?:CLAUDE\.md|settings\.json))"),
        "Global agent configuration reference",
    ),
    (
        "destructive_command",
        re.compile(r"(?i)(?:\brm\s+-rf\b|\bgit\s+reset\s+--hard\b)"),
        "Destructive command",
    ),
    (
        "dynamic_eval",
        re.compile(r"(?i)\beval\s*(?:\(|['\"$])"),
        "Dynamic eval instruction",
    ),
)
BIDI_OR_ZERO_WIDTH = re.compile("[\u200b-\u200f\u202a-\u202e\u2060\u2066-\u2069\ufeff]")
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
MARKDOWN_REFERENCE = re.compile(r"(?m)^\s*\[[^\]]+\]:\s*(\S+)")
URL_RE = re.compile(r"https?://[^\s)>\]]+")


def _inspect_package_json(record: FileRecord, findings: list[Finding]) -> None:
    try:
        payload = _strict_json_loads(record.data)
    except (UnicodeDecodeError, json.JSONDecodeError, StrictJSONError) as exc:
        findings.append(blocker("package_json_invalid", str(exc), record.path))
        return
    scripts = payload.get("scripts", {}) if isinstance(payload, dict) else {}
    for key in ("preinstall", "install", "postinstall"):
        if isinstance(scripts, dict) and key in scripts:
            findings.append(blocker("package_lifecycle_hook", f"package.json contains {key}", record.path))
    for section in ("dependencies", "devDependencies", "optionalDependencies"):
        dependencies = payload.get(section, {}) if isinstance(payload, dict) else {}
        if not isinstance(dependencies, dict):
            continue
        for name, version in dependencies.items():
            version_text = str(version)
            if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?", version_text):
                findings.append(blocker("unpinned_dependency", f"{name}={version_text}", record.path))
            else:
                findings.append(advisory("dependency_present", f"Pinned dependency: {name}={version_text}", record.path))


def _decode_link_target(target: str) -> tuple[str | None, str | None]:
    value = target.strip()
    if value.startswith("<") and ">" in value:
        value = value[1 : value.index(">")]
    else:
        value = value.split(maxsplit=1)[0]
    for _ in range(4):
        try:
            decoded = urllib.parse.unquote_to_bytes(value).decode("utf-8", "strict")
        except UnicodeDecodeError as exc:
            return None, f"invalid UTF-8 escape: {exc}"
        if decoded == value:
            break
        value = decoded
    if re.search(r"%[0-9A-Fa-f]{2}", value):
        return None, "nested percent encoding exceeds the decode limit"
    return value, None


def _inspect_markdown_target(record_path: str, target: str, known_files: set[str]) -> Finding | None:
    decoded, error = _decode_link_target(target)
    if error or decoded is None:
        return blocker("markdown_target_invalid", error or "Invalid target", record_path)
    if not decoded or decoded.startswith("#"):
        return None
    if any(ord(char) < 32 for char in decoded) or "\x00" in decoded:
        return blocker("markdown_target_invalid", "Control character in link target", record_path)
    decoded = decoded.replace("\\", "/")
    try:
        parsed = urllib.parse.urlsplit(decoded)
    except ValueError as exc:
        return blocker("markdown_target_invalid", f"Malformed URI: {exc}", record_path)
    if parsed.scheme:
        if parsed.scheme.lower() in {"http", "https", "mailto"}:
            return None
        return blocker("markdown_unsafe_scheme", f"Unapproved URI scheme: {parsed.scheme}", record_path)
    local = parsed.path
    if parsed.netloc or local.startswith(("/", "//", "~")) or re.match(r"^[A-Za-z]:", local):
        return blocker("markdown_path_escape", f"Absolute or host path is not allowed: {target}", record_path)
    stack = [part for part in Path(record_path).parent.as_posix().split("/") if part and part != "."]
    for part in local.split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            if not stack:
                return blocker("markdown_path_escape", f"Reference escapes candidate root: {target}", record_path)
            stack.pop()
        else:
            stack.append(part)
    normalized = posixpath.join(*stack) if stack else ""
    if normalized not in known_files:
        return blocker("broken_relative_reference", f"Missing captured target: {target}", record_path)
    return None


def inspect_candidate(path: Path, quarantine_root: Path) -> tuple[dict[str, Any], list[Finding]]:
    tree = scan_quarantined_tree(path, quarantine_root)
    findings = list(tree.findings)
    skill_record = next((record for record in tree.files if record.path == "SKILL.md"), None)
    frontmatter: dict[str, Any] = {}
    if not skill_record:
        findings.append(blocker("skill_file_missing", "Candidate must contain SKILL.md"))
    else:
        frontmatter, frontmatter_findings = parse_frontmatter_strict(skill_record.data, "SKILL.md")
        findings.extend(frontmatter_findings)
        for key in frontmatter:
            if key not in CLAUDE_FRONTMATTER_KEYS:
                findings.append(advisory("unknown_frontmatter_key", f"Review non-standard key: {key}", "SKILL.md"))
        for required in ("name", "description"):
            if not isinstance(frontmatter.get(required), str) or not frontmatter.get(required):
                findings.append(blocker("frontmatter_required", f"Missing string field: {required}", "SKILL.md"))
        name = frontmatter.get("name")
        if isinstance(name, str):
            if not NAME_RE.fullmatch(name):
                findings.append(blocker("frontmatter_name", "name must be lowercase hyphen-case", "SKILL.md"))
            if name != path.name:
                findings.append(blocker("directory_name_mismatch", f"name={name}, directory={path.name}", "SKILL.md"))

    known_files = {record.path for record in tree.files}
    for record in tree.files:
        lower_path = record.path.lower()
        suffix = Path(lower_path).suffix
        if Path(lower_path).name == ".gitmodules":
            findings.append(blocker("git_submodule", "Git submodules are not accepted", record.path))
        if suffix in ARCHIVE_SUFFIXES:
            findings.append(blocker("archive", "Nested archive requires separate review", record.path))
        if record.executable:
            findings.append(advisory("executable_file", "Executable bit requires capability review", record.path))
        if suffix in CODE_SUFFIXES:
            findings.append(advisory("code_present", "Executable source requires code review", record.path))
        if any(part.startswith(".") for part in Path(record.path).parts):
            findings.append(advisory("hidden_path", "Hidden path requires review", record.path))
        if b"\x00" in record.data:
            findings.append(blocker("binary_file", "Unreviewed binary content", record.path))
            continue
        try:
            text = record.data.decode("utf-8", "strict")
        except UnicodeDecodeError as exc:
            findings.append(blocker("non_utf8_content", str(exc), record.path))
            continue
        if BIDI_OR_ZERO_WIDTH.search(text):
            findings.append(
                advisory(
                    "candidate_invisible_control",
                    "Bidi or zero-width control character must be removed from every approved target",
                    record.path,
                )
            )
        for code, pattern, message in DANGEROUS_PATTERNS:
            if pattern.search(text):
                findings.append(blocker(code, message, record.path))
        urls = sorted(set(URL_RE.findall(text)))
        for url in urls:
            findings.append(advisory("external_url", f"External reference: {url}", record.path))
        if suffix == ".md":
            targets = [match.group(1) for match in MARKDOWN_LINK.finditer(text)]
            targets.extend(match.group(1) for match in MARKDOWN_REFERENCE.finditer(text))
            for target in targets:
                link_finding = _inspect_markdown_target(record.path, target, known_files)
                if link_finding:
                    findings.append(link_finding)
        if Path(lower_path).name == "package.json":
            _inspect_package_json(record, findings)

    blockers = sum(1 for item in findings if item.severity == "BLOCKING")
    advisories = sum(1 for item in findings if item.severity == "ADVISORY")
    payload = {
        "command": "inspect",
        "status": "blocked" if blockers else "review-required",
        "candidate": str(path.absolute()),
        "hash_algorithm": HASH_ALGORITHM,
        "tree_sha256": tree.tree_sha256,
        "frontmatter": frontmatter,
        "summary": {"files": len(tree.files), "blocking": blockers, "advisory": advisories},
        "files": [record.public() for record in tree.files],
        "findings": [asdict(item) for item in findings],
        "security_guarantee": "Static findings only; no findings is not a safety proof.",
    }
    return payload, findings


def _json_safe_yaml_findings(value: Any, path: str) -> list[Finding]:
    if value is None or isinstance(value, (str, bool, int)):
        return []
    if isinstance(value, float):
        if value != value or value in {float("inf"), float("-inf")}:
            return [blocker("frontmatter_value_type", "Non-finite floats are not JSON-safe", path)]
        return []
    if isinstance(value, list):
        findings: list[Finding] = []
        for index, item in enumerate(value):
            findings.extend(_json_safe_yaml_findings(item, f"{path}[{index}]"))
        return findings
    if isinstance(value, dict):
        findings = []
        for key, item in value.items():
            if not isinstance(key, str):
                findings.append(blocker("frontmatter_key_type", f"Nested key must be a string: {key!r}", path))
                continue
            findings.extend(_json_safe_yaml_findings(item, f"{path}.{key}"))
        return findings
    return [blocker("frontmatter_value_type", f"Unsupported YAML value type: {type(value).__name__}", path)]


def _validate_frontmatter_bytes(
    raw: bytes,
    target: str,
    expected_dir: str,
    display_path: str,
    surface: dict[str, str] | None = None,
) -> tuple[dict[str, Any], list[Finding]]:
    findings: list[Finding] = []
    if len(raw) > 64 * 1024:
        findings.append(blocker("frontmatter_file_too_large", "SKILL.md exceeds 64 KiB adapter limit", display_path))
        return {"command": "validate-frontmatter", "status": "blocked"}, findings
    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError:
        findings.append(blocker("pyyaml_missing", "Run with pinned pyyaml==6.0.2", display_path))
        return {"command": "validate-frontmatter", "status": "dependency-missing"}, findings
    if getattr(yaml, "__version__", "") != "6.0.2":
        findings.append(blocker("pyyaml_version", f"Expected PyYAML 6.0.2, got {getattr(yaml, '__version__', 'unknown')}"))
        return {"command": "validate-frontmatter", "status": "dependency-mismatch"}, findings

    try:
        text = raw.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        findings.append(blocker("frontmatter_non_utf8", str(exc), display_path))
        return {"command": "validate-frontmatter", "status": "blocked"}, findings
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        findings.append(blocker("frontmatter_missing", "SKILL.md must start with ---", display_path))
        return {"command": "validate-frontmatter", "status": "blocked"}, findings
    try:
        end = lines.index("---", 1)
    except ValueError:
        findings.append(blocker("frontmatter_unclosed", "Frontmatter closing --- is missing", display_path))
        return {"command": "validate-frontmatter", "status": "blocked"}, findings
    body = "\n".join(lines[1:end])

    class DuplicateSafeLoader(yaml.SafeLoader):
        pass

    def construct_mapping(loader: Any, node: Any, deep: bool = False) -> dict[Any, Any]:
        mapping: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            try:
                hash(key)
            except TypeError as exc:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"unhashable mapping key: {exc}",
                    key_node.start_mark,
                ) from exc
            if key in mapping:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"duplicate key: {key}",
                    key_node.start_mark,
                )
            mapping[key] = loader.construct_object(value_node, deep=deep)
        return mapping

    DuplicateSafeLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping,
    )
    yaml_subset_blocked = False
    try:
        depth = 0
        event_count = 0
        for event in yaml.parse(body, Loader=DuplicateSafeLoader):
            event_count += 1
            if event_count > MAX_YAML_EVENTS:
                findings.append(
                    blocker(
                        "yaml_event_budget",
                        f"Frontmatter exceeds {MAX_YAML_EVENTS} YAML parser events",
                        display_path,
                    )
                )
                yaml_subset_blocked = True
                break
            if isinstance(event, yaml.events.AliasEvent) or getattr(event, "anchor", None) is not None:
                findings.append(
                    blocker(
                        "yaml_graph_unsupported",
                        "YAML anchors and aliases are not accepted in governed frontmatter",
                        display_path,
                    )
                )
                yaml_subset_blocked = True
                break
            if isinstance(event, (yaml.events.MappingStartEvent, yaml.events.SequenceStartEvent)):
                depth += 1
                if depth > MAX_YAML_DEPTH:
                    findings.append(
                        blocker(
                            "yaml_depth_budget",
                            f"Frontmatter exceeds YAML depth {MAX_YAML_DEPTH}",
                            display_path,
                        )
                    )
                    yaml_subset_blocked = True
                    break
            elif isinstance(event, (yaml.events.MappingEndEvent, yaml.events.SequenceEndEvent)):
                depth -= 1
    except (yaml.YAMLError, RecursionError) as exc:
        findings.append(blocker("yaml_invalid", str(exc), display_path))
        yaml_subset_blocked = True

    try:
        values = {} if yaml_subset_blocked else yaml.load(body, Loader=DuplicateSafeLoader)
    except (yaml.YAMLError, RecursionError) as exc:
        findings.append(blocker("yaml_invalid", str(exc), display_path))
        values = {}
    if not isinstance(values, dict):
        findings.append(blocker("frontmatter_mapping", "Frontmatter must be a mapping", display_path))
        values = {}
    allowed = COMMON_FRONTMATTER_KEYS if target in {"common", "codex"} else CLAUDE_FRONTMATTER_KEYS
    non_string_keys = [repr(key) for key in values if not isinstance(key, str)]
    if non_string_keys:
        findings.append(blocker("frontmatter_key_type", f"Frontmatter keys must be strings: {non_string_keys}", display_path))
    json_type_findings = _json_safe_yaml_findings(values, display_path)
    findings.extend(json_type_findings)
    unknown = sorted(key for key in values if isinstance(key, str) and key not in allowed)
    if unknown:
        findings.append(blocker("frontmatter_unknown_keys", f"Unknown keys for {target}: {unknown}", display_path))
    for required in ("name", "description"):
        if not isinstance(values.get(required), str) or not values.get(required):
            findings.append(blocker("frontmatter_required", f"Missing string field: {required}", display_path))
    if isinstance(values.get("name"), str):
        if values["name"] != expected_dir or not NAME_RE.fullmatch(values["name"]):
            findings.append(blocker("frontmatter_name", f"name must match directory {expected_dir}", display_path))
    payload = {
        "command": "validate-frontmatter",
        "status": "blocked" if has_blockers(findings) else "validated",
        "target": target,
        "surface": surface,
        "validator": "pyyaml-6.0.2-safe-loader",
        "skill_sha256": sha256_bytes(raw),
        "frontmatter_sha256": sha256_bytes(body.encode("utf-8")),
        "values": values if not json_type_findings else {},
        "findings": [asdict(item) for item in findings],
    }
    return payload, findings


def validate_frontmatter_full(
    path: Path,
    target: str,
    quarantine_root: Path,
    review_root: Path | None = None,
) -> tuple[dict[str, Any], list[Finding]]:
    absolute = Path(os.path.abspath(str(path)))
    quarantine = Path(os.path.abspath(str(quarantine_root)))
    review = Path(os.path.abspath(str(review_root))) if review_root is not None else None
    try:
        quarantine_relative = absolute.relative_to(quarantine)
    except ValueError:
        quarantine_relative = None
    try:
        review_relative = absolute.relative_to(review) if review is not None else None
    except ValueError:
        review_relative = None

    expected_name = path.name
    surface: dict[str, str] | None = None
    if quarantine_relative is not None:
        tree = scan_quarantined_tree(absolute, quarantine)
        if len(quarantine_relative.parts) == 3:
            source_id, revision, expected_name = quarantine_relative.parts
            surface = {
                "kind": "quarantine",
                "source_id": source_id,
                "revision": revision,
                "skill_name": expected_name,
            }
    elif review_relative is not None and len(review_relative.parts) == 3:
        collection_id, expected_name, target_id = review_relative.parts
        tree = scan_reviewed_tree(collection_id, expected_name, target_id, review)
        surface = {
            "kind": "review",
            "collection_id": collection_id,
            "skill_name": expected_name,
            "target_id": target_id,
        }
    else:
        finding = blocker(
            "frontmatter_surface_escape",
            "Path must use the canonical quarantine or review-stage layout configured in the registry",
            str(absolute),
        )
        return {"command": "validate-frontmatter", "status": "blocked", "findings": [asdict(finding)]}, [finding]
    if has_blockers(tree.findings):
        return {
            "command": "validate-frontmatter",
            "status": "blocked",
            "findings": [asdict(item) for item in tree.findings],
        }, tree.findings
    skill_record = next((record for record in tree.files if record.path == "SKILL.md"), None)
    if skill_record is None:
        finding = blocker("skill_file_missing", "Candidate must contain a regular SKILL.md", str(path))
        return {"command": "validate-frontmatter", "status": "blocked", "findings": [asdict(finding)]}, [finding]
    return _validate_frontmatter_bytes(skill_record.data, target, expected_name, f"{absolute}/SKILL.md", surface)


def _manifest_digest(paths: list[Path]) -> str:
    digest = hashlib.sha256(b"skill-governance-estate-manifest-v1\0")
    for base in sorted(paths, key=lambda path: str(path).encode("utf-8")):
        label = str(base).encode("utf-8")
        digest.update(_length_prefix(label))
        if not base.exists() and not base.is_symlink():
            digest.update(_length_prefix(b"missing"))
            continue
        stack = [base]
        while stack:
            current = stack.pop()
            try:
                info = current.lstat()
            except OSError as exc:
                digest.update(_length_prefix(f"error:{exc}".encode("utf-8")))
                continue
            try:
                relative = current.relative_to(base).as_posix().encode("utf-8", "strict")
            except (ValueError, UnicodeEncodeError):
                relative = os.fsencode(str(current))
            if stat.S_ISLNK(info.st_mode):
                digest.update(_length_prefix(b"link" + relative + os.fsencode(os.readlink(current))))
            elif stat.S_ISDIR(info.st_mode):
                digest.update(_length_prefix(b"dir" + relative))
                try:
                    children = sorted(current.iterdir(), key=lambda path: os.fsencode(path.name), reverse=True)
                except OSError:
                    children = []
                stack.extend(children)
            elif stat.S_ISREG(info.st_mode):
                data, finding = _read_regular_file(current, info)
                if finding or data is None:
                    digest.update(_length_prefix(b"read-error" + relative))
                else:
                    mode = b"1" if info.st_mode & 0o111 else b"0"
                    digest.update(_length_prefix(b"file" + relative + mode + bytes.fromhex(sha256_bytes(data))))
            else:
                digest.update(_length_prefix(b"special" + relative))
    return digest.hexdigest()


class _RejectRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request: Any, fp: Any, code: int, message: str, headers: Any, new_url: str) -> None:
        return None


def _tls_context() -> ssl.SSLContext:
    system_bundle = Path("/etc/ssl/cert.pem")
    context = ssl.create_default_context(cafile=str(system_bundle) if system_bundle.is_file() else None)
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    return context


def _github_request_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "local-skill-governance/1",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        if len(token) > 4_096 or not re.fullmatch(r"[!-~]+", token):
            raise ValueError("invalid GitHub token environment value")
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _github_json(repo: str, endpoint: str) -> tuple[dict[str, Any] | None, str | None]:
    if not GITHUB_RE.fullmatch(repo):
        return None, "invalid owner/repo"
    url = f"https://api.github.com/repos/{repo}/{endpoint.lstrip('/')}"
    try:
        request = urllib.request.Request(url, headers=_github_request_headers(), method="GET")
    except ValueError as exc:
        return None, str(exc)
    opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=_tls_context()),
        _RejectRedirects(),
    )
    try:
        with opener.open(request, timeout=20) as response:  # noqa: S310 - fixed GitHub host
            final = urllib.parse.urlparse(response.geturl())
            if final.scheme != "https" or final.hostname != "api.github.com":
                return None, f"redirected to unapproved host: {final.hostname}"
            declared = response.headers.get("Content-Length")
            if declared and int(declared) > MAX_GITHUB_RESPONSE:
                return None, "response exceeds size cap"
            raw = response.read(MAX_GITHUB_RESPONSE + 1)
            if len(raw) > MAX_GITHUB_RESPONSE:
                return None, "response exceeds size cap"
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        return None, str(exc)
    try:
        payload = _strict_json_loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError, StrictJSONError) as exc:
        return None, str(exc)
    if not isinstance(payload, dict):
        return None, "GitHub response must be a JSON object"
    return payload, None


def _github_head(source: dict[str, Any]) -> tuple[str | None, str | None]:
    branch = urllib.parse.quote(str(source["default_branch"]), safe="")
    payload, error = _github_json(source["github"], f"commits/{branch}")
    if error or payload is None:
        return None, error or "GitHub response unavailable"
    sha = payload.get("sha")
    if not isinstance(sha, str) or not SHA_RE.fullmatch(sha):
        return None, "GitHub response did not contain a full commit SHA"
    return sha, None


def _github_pinned_tree(source: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    revision = str(source["observed_revision"])
    commit, error = _github_json(source["github"], f"git/commits/{revision}")
    if error or commit is None:
        return None, error or "Pinned commit unavailable"
    commit_sha = commit.get("sha")
    tree = commit.get("tree")
    tree_sha = tree.get("sha") if isinstance(tree, dict) else None
    if commit_sha != revision or not isinstance(tree_sha, str) or not SHA_RE.fullmatch(tree_sha):
        return None, "Pinned commit response has an invalid commit or tree SHA"
    tree_payload, error = _github_json(source["github"], f"git/trees/{tree_sha}?recursive=1")
    if error or tree_payload is None:
        return None, error or "Pinned tree unavailable"
    if tree_payload.get("sha") != tree_sha:
        return None, "Pinned tree response SHA does not match the commit tree SHA"
    entries = tree_payload.get("tree")
    if not isinstance(entries, list):
        return None, "Pinned tree response has no tree array"
    skill_blobs: list[tuple[str, str]] = []
    blob_paths: list[str] = []
    tree_shas: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            return None, "Pinned tree entry must be an object"
        path = entry.get("path")
        blob_sha = entry.get("sha")
        if isinstance(path, str) and entry.get("type") == "tree":
            if not isinstance(blob_sha, str) or not SHA_RE.fullmatch(blob_sha):
                return None, f"Invalid tree SHA: {path}"
            tree_shas[path] = blob_sha
        if isinstance(path, str) and entry.get("type") == "blob":
            blob_paths.append(path)
        if isinstance(path, str) and posixpath.basename(path) == "SKILL.md" and entry.get("type") == "blob":
            if not isinstance(blob_sha, str) or not SHA_RE.fullmatch(blob_sha):
                return None, f"Invalid SKILL.md blob SHA: {path}"
            skill_blobs.append((path, blob_sha))
    skill_blobs.sort(key=lambda item: item[0].encode("utf-8"))
    blob_paths.sort(key=lambda item: item.encode("utf-8"))
    return {
        "commit_sha": commit_sha,
        "tree_sha": tree_payload.get("sha"),
        "truncated": tree_payload.get("truncated"),
        "skill_blobs": skill_blobs,
        "blob_paths": blob_paths,
        "tree_shas": tree_shas,
    }, None


def sources_payload(
    registry: dict[str, Any],
    registry_path: Path,
    lock_path: Path,
    catalog_path: Path,
    live: bool,
    selected: str | None,
) -> tuple[dict[str, Any], list[Finding]]:
    findings: list[Finding] = []
    sources = [source for source in registry.get("sources", []) if selected is None or source.get("id") == selected]
    if selected and not sources:
        findings.append(blocker("source_unknown", f"Unknown source: {selected}"))
    roots = [expand_path(root["path"]) for root in registry.get("roots", [])]
    protected = [registry_path, lock_path, catalog_path, *roots]
    before = _manifest_digest(protected) if live else None
    rows: list[dict[str, Any]] = []
    for source in sources:
        row = {
            "id": source["id"],
            "github": source["github"],
            "observed_revision": source["observed_revision"],
            "observed_at": source["observed_at"],
            "mode": source["mode"],
            "update_policy": source["update_policy"],
        }
        if live:
            current, error = _github_head(source)
            if error:
                row.update({"live_status": "unavailable", "error": error})
                findings.append(blocker("source_live_unavailable", error, source["id"]))
            else:
                row.update(
                    {
                        "live_status": "current" if current == source["observed_revision"] else "update-available",
                        "current_revision": current,
                    }
                )
        rows.append(row)
    after = _manifest_digest(protected) if live else None
    if live and before != after:
        findings.append(blocker("network_read_mutation", "Protected local manifest changed during --live"))
    return {
        "command": "sources",
        "status": "blocked" if has_blockers(findings) else "ok",
        "capability": "network-read" if live else "offline-read",
        "local_manifest_before": before,
        "local_manifest_after": after,
        "sources": rows,
        "findings": [asdict(item) for item in findings],
    }, findings


def _run_git(repo: Path, arguments: list[str]) -> tuple[bytes | None, str | None]:
    environment = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=repo,
            env=environment,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        return None, str(exc)
    if result.returncode != 0:
        return None, result.stderr.decode("utf-8", "replace").strip() or f"git exited {result.returncode}"
    return result.stdout, None


def _parse_git_config_records(raw: bytes, *, show_origin: bool = False) -> tuple[list[tuple[str, str]], str | None]:
    try:
        parts = [part.decode("utf-8", "strict") for part in raw.split(b"\0") if part]
    except UnicodeDecodeError as exc:
        return [], str(exc)
    records: list[tuple[str, str]] = []
    if show_origin:
        if len(parts) % 2:
            return [], "git config --show-origin returned an incomplete record"
        values = parts[1::2]
    else:
        values = parts
    for value in values:
        key, separator, item = value.partition("\n")
        if not separator or not key:
            return [], "git config returned an invalid key/value record"
        records.append((key.lower(), item))
    return records, None


def delivery_payload(registry: dict[str, Any], live: bool) -> tuple[dict[str, Any], list[Finding]]:
    findings: list[Finding] = []
    if isinstance(registry.get("parity"), dict):
        parity, parity_findings = parity_payload(registry)
        findings.extend(parity_findings)
    else:
        parity = {"status": "DEGRADED"}
        findings.append(blocker("delivery_parity_config", "Delivery proof requires the configured Codex/Claude parity contract"))
    if not live:
        findings.append(blocker("delivery_live_required", "Remote delivery proof requires explicit --live"))
    delivery = registry.get("delivery", {})
    branch = delivery.get("branch")
    remote = delivery.get("remote")
    rows: list[dict[str, Any]] = []
    for entry in delivery.get("repos", []):
        repo_id = entry["id"]
        repo = Path(os.path.realpath(expand_path(entry["path"])))
        required_paths = entry["required_paths"]
        before = _manifest_digest([repo / path for path in required_paths])
        row: dict[str, Any] = {"id": repo_id, "path": str(repo), "required_paths": required_paths}
        expected_remote_url = entry["remote_url"]
        row["remote_identity"] = {"name": remote, "expected_url": expected_remote_url}
        local_config_raw, error = _run_git(repo, ["config", "--local", "--list", "--null"])
        if error or local_config_raw is None:
            findings.append(blocker("delivery_remote_identity", error or "Local Git config unavailable", repo_id))
        else:
            local_config, parse_error = _parse_git_config_records(local_config_raw)
            if parse_error:
                findings.append(blocker("delivery_remote_identity", parse_error, repo_id))
            else:
                fetch_key = f"remote.{str(remote).lower()}.url"
                push_key = f"remote.{str(remote).lower()}.pushurl"
                raw_fetch = [value for key, value in local_config if key == fetch_key]
                raw_push = [value for key, value in local_config if key == push_key]
                row["remote_identity"]["raw_fetch_urls"] = raw_fetch
                row["remote_identity"]["raw_push_urls"] = raw_push
                if raw_fetch != [expected_remote_url] or raw_push not in ([], [expected_remote_url]):
                    findings.append(
                        blocker(
                            "delivery_remote_identity",
                            f"Raw remote config differs: fetch={raw_fetch} push={raw_push}",
                            repo_id,
                        )
                    )
        all_config_raw, error = _run_git(repo, ["config", "--list", "--show-origin", "--null"])
        if error or all_config_raw is None:
            findings.append(blocker("delivery_remote_rewrite", error or "Git rewrite config unavailable", repo_id))
        else:
            all_config, parse_error = _parse_git_config_records(all_config_raw, show_origin=True)
            if parse_error:
                findings.append(blocker("delivery_remote_rewrite", parse_error, repo_id))
            else:
                rewrite_keys = sorted(
                    key
                    for key, _ in all_config
                    if re.fullmatch(r"url\..+\.(?:insteadof|pushinsteadof)", key)
                )
                row["remote_identity"]["rewrite_keys"] = rewrite_keys
                if rewrite_keys:
                    findings.append(
                        blocker(
                            "delivery_remote_rewrite",
                            f"Git URL rewrite rules are not accepted for delivery proof: {rewrite_keys}",
                            repo_id,
                        )
                    )
        package_root = repo / "skills" / "skill-governance"
        package_tree = scan_tree(package_root)
        findings.extend(package_tree.findings)
        physical_package_paths = {
            f"skills/skill-governance/{record.path}"
            for record in package_tree.files
        }
        tracked_package_raw, tracked_package_error = _run_git(
            repo,
            ["ls-files", "-z", "--", "skills/skill-governance"],
        )
        if tracked_package_error or tracked_package_raw is None:
            findings.append(blocker("delivery_package_tracking_probe", tracked_package_error or "Package tracking unavailable", repo_id))
        else:
            try:
                tracked_package_paths = {
                    item.decode("utf-8", "strict")
                    for item in tracked_package_raw.split(b"\0")
                    if item
                }
            except UnicodeDecodeError as exc:
                findings.append(blocker("delivery_package_tracking_probe", str(exc), repo_id))
            else:
                if tracked_package_paths != physical_package_paths:
                    findings.append(
                        blocker(
                            "delivery_package_tracking_mismatch",
                            f"physical_only={sorted(physical_package_paths - tracked_package_paths)} tracked_only={sorted(tracked_package_paths - physical_package_paths)}",
                            repo_id,
                        )
                    )
        registry_raw, registry_finding = _read_regular_path(package_root / "registry.toml", package_root)
        lock_raw, lock_finding = _read_regular_path(package_root / "registry.lock.json", package_root)
        estate_raw, estate_finding = _read_regular_path(package_root / "estate.lock.json", package_root)
        reputation_raw, reputation_finding = _read_regular_path(package_root / "reputation.lock.json", package_root)
        if registry_finding or registry_raw is None:
            findings.append(registry_finding or blocker("delivery_registry_unavailable", "Package registry unavailable", repo_id))
        else:
            row["governance_registry_sha256"] = sha256_bytes(registry_raw)
            try:
                package_registry = tomllib.loads(registry_raw.decode("utf-8", "strict"))
            except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
                findings.append(blocker("delivery_registry_invalid", str(exc), repo_id))
            else:
                if package_registry.get("generation") != registry.get("generation"):
                    findings.append(blocker("delivery_generation_mismatch", "Package registry generation differs", repo_id))
        if lock_finding or lock_raw is None:
            findings.append(lock_finding or blocker("delivery_lock_unavailable", "Package lock unavailable", repo_id))
        else:
            try:
                package_lock = _strict_json_loads(lock_raw)
            except (UnicodeDecodeError, json.JSONDecodeError, StrictJSONError) as exc:
                findings.append(blocker("delivery_lock_invalid", str(exc), repo_id))
            else:
                if not isinstance(package_lock, dict):
                    findings.append(blocker("delivery_lock_invalid", "Package lock must be a JSON object", repo_id))
                elif package_lock.get("generation") != registry.get("generation"):
                    findings.append(blocker("delivery_generation_mismatch", "Package lock generation differs", repo_id))
                if isinstance(package_lock, dict) and registry_raw is not None and package_lock.get("registry_sha256") != sha256_bytes(registry_raw):
                    findings.append(blocker("delivery_registry_lock_binding", "Package lock is not bound to its registry bytes", repo_id))
        if estate_finding or estate_raw is None:
            findings.append(estate_finding or blocker("delivery_estate_lock_unavailable", "Package estate lock unavailable", repo_id))
        else:
            try:
                package_estate = _strict_json_loads(estate_raw)
            except (UnicodeDecodeError, json.JSONDecodeError, StrictJSONError) as exc:
                findings.append(blocker("delivery_estate_lock_invalid", str(exc), repo_id))
            else:
                if not isinstance(package_estate, dict):
                    findings.append(blocker("delivery_estate_lock_invalid", "Package estate lock must be a JSON object", repo_id))
                elif package_estate.get("generation") != registry.get("generation"):
                    findings.append(blocker("delivery_generation_mismatch", "Package estate lock generation differs", repo_id))
                if isinstance(package_estate, dict) and registry_raw is not None and package_estate.get("registry_sha256") != sha256_bytes(registry_raw):
                    findings.append(blocker("delivery_registry_estate_binding", "Package estate lock is not bound to its registry bytes", repo_id))
        if reputation_finding or reputation_raw is None:
            findings.append(reputation_finding or blocker("delivery_reputation_unavailable", "Package reputation snapshot unavailable", repo_id))
        else:
            try:
                package_reputation = _strict_json_loads(reputation_raw)
            except (UnicodeDecodeError, json.JSONDecodeError, StrictJSONError) as exc:
                findings.append(blocker("delivery_reputation_invalid", str(exc), repo_id))
            else:
                if not isinstance(package_reputation, dict):
                    findings.append(blocker("delivery_reputation_invalid", "Package reputation must be a JSON object", repo_id))
                elif package_reputation.get("schema_version") != REPUTATION_SCHEMA_VERSION:
                    findings.append(blocker("delivery_reputation_schema", "Package reputation schema differs", repo_id))
        branch_raw, error = _run_git(repo, ["symbolic-ref", "--quiet", "--short", "HEAD"])
        if error or branch_raw is None:
            findings.append(blocker("delivery_branch_probe", error or "Branch unavailable", repo_id))
        else:
            current_branch = branch_raw.decode("utf-8", "strict").strip()
            row["branch"] = current_branch
            if current_branch != branch:
                findings.append(blocker("delivery_branch", f"Expected {branch}, got {current_branch}", repo_id))
        head_raw, error = _run_git(repo, ["rev-parse", "HEAD"])
        local_head = head_raw.decode("ascii", "strict").strip() if head_raw is not None and not error else ""
        if error or not SHA_RE.fullmatch(local_head):
            findings.append(blocker("delivery_head_probe", error or "Invalid local HEAD", repo_id))
        row["local_head"] = local_head or None
        for direction, arguments in (
            ("fetch", ["remote", "get-url", "--all", str(remote)]),
            ("push", ["remote", "get-url", "--push", "--all", str(remote)]),
        ):
            urls_raw, error = _run_git(repo, arguments)
            urls: list[str] = []
            if error or urls_raw is None:
                findings.append(blocker("delivery_remote_identity", error or "Remote URL unavailable", f"{repo_id}:{direction}"))
            else:
                try:
                    urls = urls_raw.decode("utf-8", "strict").splitlines()
                except UnicodeDecodeError as exc:
                    findings.append(blocker("delivery_remote_identity", str(exc), f"{repo_id}:{direction}"))
                else:
                    if urls != [expected_remote_url]:
                        findings.append(
                            blocker(
                                "delivery_remote_identity",
                                f"Expected exactly {expected_remote_url}, got {urls}",
                                f"{repo_id}:{direction}",
                            )
                        )
            row["remote_identity"][f"{direction}_urls"] = urls
        for required_path in required_paths:
            tracked_raw, error = _run_git(repo, ["ls-files", "-z", "--", required_path])
            if error or tracked_raw is None or not tracked_raw:
                findings.append(blocker("delivery_paths_untracked", error or "Required governed path is not tracked", f"{repo_id}:{required_path}"))
        status_raw, error = _run_git(repo, ["status", "--porcelain=v1", "-z", "--untracked-files=all", "--", *required_paths])
        if error:
            findings.append(blocker("delivery_status_probe", error, repo_id))
        elif status_raw:
            findings.append(blocker("delivery_scoped_dirty", "Governed delivery paths differ from HEAD", repo_id))
        if live:
            remote_raw, error = _run_git(
                repo,
                ["ls-remote", "--exit-code", expected_remote_url, f"refs/heads/{branch}"],
            )
            if error or remote_raw is None:
                findings.append(blocker("delivery_remote_probe", error or "Remote head unavailable", repo_id))
            else:
                fields = remote_raw.decode("ascii", "strict").split()
                remote_head = fields[0] if fields else ""
                row["remote_head"] = remote_head or None
                if remote_head != local_head:
                    findings.append(blocker("delivery_remote_mismatch", f"local={local_head} remote={remote_head}", repo_id))
        after = _manifest_digest([repo / path for path in required_paths])
        row["local_manifest_before"] = before
        row["local_manifest_after"] = after
        if before != after:
            findings.append(blocker("delivery_read_mutation", "Governed files changed during delivery proof", repo_id))
        rows.append(row)
    registry_digests = {row.get("governance_registry_sha256") for row in rows if row.get("governance_registry_sha256")}
    if len(registry_digests) != 1:
        findings.append(blocker("delivery_registry_replica_drift", "Codex and Claude governance registry digests differ"))
    return {
        "command": "delivery",
        "status": "DEGRADED" if has_blockers(findings) else "ok",
        "capability": "network-read+credential-helper-read" if live else "offline-read",
        "generation": registry.get("generation"),
        "parity_status": parity.get("status"),
        "repos": rows,
        "findings": [asdict(item) for item in findings],
    }, findings


def emit(payload: dict[str, Any], json_output: bool) -> None:
    if json_output:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return
    print(f"{payload.get('command', 'governance')}: {payload.get('status', 'unknown')}")
    summary = payload.get("summary")
    if summary:
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    if "generation" in payload:
        print(f"generation: {payload['generation']}")
    if "legacy_active_count" in payload:
        print(f"legacy-active: {payload['legacy_active_count']} (integrity baseline only)")
    for item in payload.get("sources", []):
        live = item.get("live_status", "offline")
        source_id = item.get("id") or item.get("source_id") or "unknown"
        revision = item.get("observed_revision") or item.get("revision") or "unknown"
        print(f"- {source_id}: {live} @ {revision[:12]}")
    findings = payload.get("findings", [])
    if findings:
        counts: dict[str, int] = {}
        for item in findings:
            counts[item["severity"]] = counts.get(item["severity"], 0) + 1
        print("findings: " + ", ".join(f"{key}={counts[key]}" for key in sorted(counts)))
        for item in findings[:40]:
            location = f" [{item['path']}]" if item.get("path") else ""
            print(f"- {item['severity']} {item['code']}{location}: {item['message']}")
        if len(findings) > 40:
            print(f"- ... {len(findings) - 40} more; use --json")


def _common_options(parser: argparse.ArgumentParser, include_lock: bool = True) -> None:
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    if include_lock:
        parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--json", action="store_true", dest="json_output")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inventory = subparsers.add_parser("inventory", help="Inventory configured skill roots")
    _common_options(inventory, include_lock=False)

    catalog = subparsers.add_parser("catalog", help="Validate the complete pinned source catalog")
    _common_options(catalog, include_lock=False)
    catalog.add_argument("--live", action="store_true", help="Verify exact pinned trees against api.github.com")
    catalog.add_argument("--source", help="Limit live verification to one source id")

    audit = subparsers.add_parser("audit", help="Validate registry, locks, baselines, and collisions")
    _common_options(audit)
    audit.add_argument("--estate", type=Path, default=DEFAULT_ESTATE)
    audit.add_argument("--reputation", type=Path, default=DEFAULT_REPUTATION)

    reputation = subparsers.add_parser("reputation", help="Validate the dated advisory source-reputation snapshot")
    reputation.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    reputation.add_argument("--reputation", type=Path, default=DEFAULT_REPUTATION)
    reputation.add_argument("--json", action="store_true", dest="json_output")

    inspect = subparsers.add_parser("inspect", help="Statically inspect a quarantined candidate")
    inspect.add_argument("path", type=Path)
    inspect.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    inspect.add_argument("--json", action="store_true", dest="json_output")

    validate = subparsers.add_parser("validate-frontmatter", help="Run the pinned full YAML adapter")
    validate.add_argument("path", type=Path)
    validate.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    validate.add_argument("--target", choices=("common", "codex", "claude"), default="common")
    validate.add_argument("--json", action="store_true", dest="json_output")

    sources = subparsers.add_parser("sources", help="List or check watched sources")
    _common_options(sources)
    sources.add_argument("--live", action="store_true", help="Explicit network-read against api.github.com")
    sources.add_argument("--source", help="Limit live check to one source id")

    parity = subparsers.add_parser("parity", help="Compare authority and replica")
    _common_options(parity, include_lock=False)

    lock_plan = subparsers.add_parser("lock-plan", help="Print a proposed lock to stdout; never writes files")
    _common_options(lock_plan, include_lock=False)

    estate_plan = subparsers.add_parser("estate-plan", help="Print the exact runtime estate baseline; never writes files")
    estate_plan.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    estate_plan.add_argument("--json", action="store_true", dest="json_output")

    delivery = subparsers.add_parser("delivery", help="Verify scoped local commits and origin/main heads")
    delivery.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    delivery.add_argument("--live", action="store_true", help="Use git ls-remote for explicit remote proof")
    delivery.add_argument("--json", action="store_true", dest="json_output")
    return parser


def main(argv: list[str] | None = None) -> int:
    if sys.version_info < (3, 11):
        print("Python 3.11 or newer is required", file=sys.stderr)
        return 3
    args = build_parser().parse_args(argv)
    if args.command in {"inspect", "validate-frontmatter"}:
        registry, findings = load_registry(args.registry.absolute())
        if has_blockers(findings):
            payload = {"command": args.command, "status": "blocked", "findings": [asdict(item) for item in findings]}
        else:
            quarantine_root = expand_path(registry["quarantine_root"])
            review_root = expand_path(registry["review_root"])
            if args.command == "inspect":
                payload, findings = inspect_candidate(args.path, quarantine_root)
            else:
                payload, findings = validate_frontmatter_full(args.path, args.target, quarantine_root, review_root)
    else:
        registry_path = args.registry.absolute()
        registry, findings = load_registry(registry_path)
        if has_blockers(findings):
            payload = {
                "command": args.command,
                "status": "blocked",
                "findings": [asdict(item) for item in findings],
            }
            emit(payload, args.json_output)
            return 3
        if args.command == "inventory":
            payload = inventory_payload(registry)
            findings = [Finding(**item) for item in payload.get("findings", [])]
        elif args.command == "catalog":
            payload, findings = catalog_payload(registry, registry_path, args.catalog.absolute(), args.live, args.source)
        elif args.command == "audit":
            payload, findings = audit_payload(
                registry_path,
                args.lock.absolute(),
                args.catalog.absolute(),
                args.estate.absolute(),
                args.reputation.absolute(),
            )
        elif args.command == "reputation":
            payload, findings = reputation_payload(registry, args.reputation.absolute())
        elif args.command == "parity":
            payload, findings = parity_payload(registry)
        elif args.command == "sources":
            payload, findings = sources_payload(
                registry,
                registry_path,
                args.lock.absolute(),
                args.catalog.absolute(),
                args.live,
                args.source,
            )
        elif args.command == "lock-plan":
            _, catalog_findings = catalog_payload(registry, registry_path, args.catalog.absolute())
            lock, plan_findings = build_lock_plan(registry, registry_path, catalog_path=args.catalog.absolute())
            findings = [*catalog_findings, *plan_findings]
            payload = lock if args.json_output else {
                "command": "lock-plan",
                "status": "blocked" if has_blockers(findings) else "planned",
                "generation": lock["generation"],
                "summary": {"artifacts": len(lock["artifacts"])},
                "proposed_lock": lock,
                "findings": [asdict(item) for item in findings],
            }
            if args.json_output and findings:
                payload = {"proposed_lock": lock, "findings": [asdict(item) for item in findings]}
        elif args.command == "estate-plan":
            inventory = inventory_payload(registry)
            findings = [Finding(**item) for item in inventory.get("findings", [])]
            findings.extend(runtime_state_presence_findings(registry, inventory))
            estate = planned_estate_lock(registry, registry_path, inventory)
            payload = {
                "command": "estate-plan",
                "status": "DEGRADED" if has_blockers(findings) else "ok",
                "estate": estate,
                "findings": [asdict(item) for item in findings],
            }
        elif args.command == "delivery":
            payload, findings = delivery_payload(registry, args.live)
        else:  # pragma: no cover - argparse enforces the command set
            raise AssertionError(args.command)
    emit(payload, args.json_output)
    return 2 if has_blockers(findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
