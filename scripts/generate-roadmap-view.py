#!/usr/bin/env python3
from __future__ import annotations

import argparse
import functools
import hashlib
import http.server
import importlib.util
import json
import os
import re
import stat
import sys
import threading
import time
import webbrowser
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "tools" / "roadmap_viewer.html"
PLACEHOLDER = '{"__ROADMAP_SNAPSHOT_JSON__": true}'
DEFAULT_FILES = [
    "00_spec.md",
    "10_task.md",
    "20_survey.md",
    "30_plan.md",
    "40_progress.md",
    "80_review.md",
    "05_log.md",
    "99_history.md",
    "checkpoint.md",
    "team-journal.md",
    "90_verification.md",
    "graph-map.md",
]

OUTPUT_NAMES = {"roadmap.html", "roadmap-snapshot.json"}
EMBEDDED_SNAPSHOT_RE = re.compile(
    r'<script\b(?=[^>]*\bid=["\']embedded-snapshot["\'])[^>]*>(.*?)</script\s*>',
    re.IGNORECASE | re.DOTALL,
)
TASK_HEADING_RE = re.compile(
    r"^(#{2,3})\s+(?:Task|タスク)\s+(\d+(?:\.\d+)?)\s*[:：]",
    re.IGNORECASE | re.MULTILINE,
)
MARKDOWN_HEADING_RE = re.compile(r"^(#{1,6})\s+\S", re.MULTILINE)
IMPLEMENTATION_EVIDENCE_RE = re.compile(
    r"^#### 実装根拠\s*$([\s\S]*?)(?=^####\s|\Z)",
    re.MULTILINE,
)
INLINE_CODE_RE = re.compile(r"`([^`\r\n]+)`")
LINE_RANGE_RE = re.compile(r"^L([1-9]\d*)-L([1-9]\d*)$")

DEFAULT_SOURCE_ALLOW_PREFIXES = (
    ".claude",
    ".codex",
    ".agents",
    ".github",
    "_shared-ai",
    "src",
    "app",
    "apps",
    "lib",
    "libs",
    "packages",
    "test",
    "tests",
    "scripts",
    "config",
    "docs",
)
DENIED_SOURCE_COMPONENTS = {
    "Daily",
    "Living",
    "Life",
    "Work",
    "Inbox",
    "Reading",
    "attachments",
    "Claude-note",
    "Codex-note",
    ".git",
    ".obsidian",
    ".local",
}
ALLOWED_HIDDEN_SOURCE_COMPONENTS = {".claude", ".codex", ".agents", ".github"}
SECRET_SOURCE_NAMES = {
    ".npmrc",
    ".pypirc",
    ".netrc",
    "credentials.json",
    "secrets.json",
    "id_rsa",
    "id_dsa",
    "id_ed25519",
}
SECRET_SOURCE_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}
MAX_SOURCE_FILE_BYTES = 1024 * 1024
MAX_PREVIEW_LINES = 12
MAX_PREVIEW_BYTES = 4 * 1024
MAX_TOTAL_PREVIEW_BYTES = 32 * 1024

SECRET_CONTENT_PATTERNS = (
    re.compile(
        r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
        re.IGNORECASE,
    ),
    re.compile(r"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bgh(?:p|o|u|s|r)_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{40,}\b"),
    re.compile(r"\bxox(?:a|b|p|r|s)-[A-Za-z0-9-]{20,}\b"),
    re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    re.compile(
        r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
    ),
    re.compile(r"https://hooks\.slack\.com/services/[A-Za-z0-9/_-]{20,}"),
    re.compile(
        r"https://(?:discord(?:app)?\.com)/api/webhooks/\d+/[A-Za-z0-9._-]{20,}"
    ),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{32,}", re.IGNORECASE),
)

LANGUAGE_BY_SUFFIX = {
    ".c": "c",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".cs": "csharp",
    ".css": "css",
    ".go": "go",
    ".html": "html",
    ".java": "java",
    ".js": "javascript",
    ".jsx": "jsx",
    ".json": "json",
    ".kt": "kotlin",
    ".md": "markdown",
    ".mjs": "javascript",
    ".php": "php",
    ".py": "python",
    ".rb": "ruby",
    ".rs": "rust",
    ".sh": "shell",
    ".sql": "sql",
    ".swift": "swift",
    ".toml": "toml",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".vue": "vue",
    ".xml": "xml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".zsh": "shell",
}


class RoadmapHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, format: str, *args: object) -> None:
        return


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(text)
    tmp.replace(path)


def write_text_if_changed(path: Path, text: str) -> bool:
    try:
        if path.is_file() and path.read_text() == text:
            return False
    except OSError:
        pass
    atomic_write_text(path, text)
    return True


def ensure_task_meta(
    task_dir: Path,
    source_root: Path,
    *,
    thread_id: str | None = None,
    session_id: str | None = None,
    task_state: str | None = None,
) -> dict[str, object]:
    path = task_dir / "task-meta.json"
    existing: dict[str, object] = {}
    if path.is_symlink():
        raise ValueError("task-meta.json must not be a symlink")
    if path.is_file():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"invalid task-meta.json: {error}") from error
        if not isinstance(loaded, dict):
            raise ValueError("invalid task-meta.json: root must be an object")
        existing = loaded

    now = datetime.now(timezone.utc).isoformat()
    files, _ = read_files(task_dir)
    desired = {
        **existing,
        "schema_version": 1,
        "task_id": str(existing.get("task_id") or task_dir.name),
        "task_title": str(
            existing.get("task_title") or infer_title(files, task_dir)
        ),
        "project_path": str(source_root),
        "worktree_path": str(source_root),
        "task_state": str(task_state or existing.get("task_state") or "active"),
        "code_change": bool(
            existing.get("code_change") or (task_dir / "codemap.source.json").is_file()
        ),
        "created_at": str(existing.get("created_at") or now),
    }
    if thread_id:
        desired["thread_id"] = thread_id
    if session_id:
        desired["session_id"] = session_id
    comparable_existing = {key: value for key, value in existing.items() if key != "updated_at"}
    comparable_desired = {key: value for key, value in desired.items() if key != "updated_at"}
    desired["updated_at"] = (
        str(existing.get("updated_at"))
        if comparable_existing == comparable_desired and existing.get("updated_at")
        else now
    )
    write_text_if_changed(
        path,
        json.dumps(desired, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    return desired


def read_files(task_dir: Path) -> tuple[dict[str, str], list[dict[str, object]]]:
    files: dict[str, str] = {}
    sources: list[dict[str, object]] = []
    for name in DEFAULT_FILES:
        path = task_dir / name
        if path.is_symlink():
            continue
        try:
            source_stat = path.stat(follow_symlinks=False)
        except OSError:
            continue
        if not stat.S_ISREG(source_stat.st_mode):
            continue
        text = path.read_text()
        files[name] = text
        sources.append(
            {
                "name": name,
                "path": str(path),
                "size": source_stat.st_size,
                "modifiedAt": datetime.fromtimestamp(source_stat.st_mtime, timezone.utc).isoformat(),
            }
        )
    return files, sources


def infer_source_root(task_dir: Path) -> Path | None:
    resolved = Path(os.path.abspath(task_dir))
    if (
        resolved.parent.name == "memory"
        and resolved.parent.parent.name == ".local"
    ):
        return resolved.parent.parent.parent
    return None


def parse_source_preview_references(plan: str) -> list[tuple[str, str]]:
    references: list[tuple[str, str]] = []
    task_matches = list(TASK_HEADING_RE.finditer(plan))
    for index, task_match in enumerate(task_matches):
        section_start = task_match.end()
        task_level = len(task_match.group(1))
        section_end = (
            task_matches[index + 1].start()
            if index + 1 < len(task_matches)
            else len(plan)
        )
        peer_heading = next(
            (
                heading
                for heading in MARKDOWN_HEADING_RE.finditer(
                    plan,
                    section_start,
                    section_end,
                )
                if len(heading.group(1)) <= task_level
            ),
            None,
        )
        if peer_heading is not None:
            section_end = peer_heading.start()
        task_section = plan[section_start:section_end]
        evidence = IMPLEMENTATION_EVIDENCE_RE.search(task_section)
        if not evidence:
            continue
        first_inline = INLINE_CODE_RE.search(evidence.group(1))
        if not first_inline:
            continue
        reference = first_inline.group(1).strip()
        if not reference.startswith("repo:"):
            continue
        references.append((task_match.group(2), reference))
    return references


def source_language(relative_path: str) -> str:
    return LANGUAGE_BY_SUFFIX.get(Path(relative_path).suffix.lower(), "text")


def source_preview_record(
    task_number: str,
    relative_path: str,
    anchor: str,
    *,
    status: str,
    message: str,
    start_line: int | None = None,
    end_line: int | None = None,
    code: str = "",
    truncated: bool = False,
) -> dict[str, object]:
    return {
        "taskNumber": task_number,
        "path": relative_path,
        "anchor": anchor,
        "language": source_language(relative_path),
        "startLine": start_line,
        "endLine": end_line,
        "code": code,
        "status": status,
        "message": message,
        "truncated": truncated,
    }


def split_source_reference(reference: str) -> tuple[str, str]:
    payload = reference.removeprefix("repo:")
    relative_path, separator, anchor = payload.partition("#")
    if not separator:
        return relative_path.strip(), ""
    return relative_path.strip(), anchor.strip()


def normalize_source_prefixes(prefixes: list[str] | None) -> tuple[tuple[str, ...], ...]:
    values = [*DEFAULT_SOURCE_ALLOW_PREFIXES, *(prefixes or [])]
    normalized: list[tuple[str, ...]] = []
    for value in values:
        candidate = value.strip().rstrip("/")
        raw_parts = candidate.split("/")
        if (
            not candidate
            or candidate.startswith(("/", "~", "\\"))
            or "\\" in candidate
            or any(part in {"", ".", ".."} for part in raw_parts)
            or re.match(r"^[A-Za-z]:", candidate)
        ):
            continue
        parts = tuple(raw_parts)
        if parts not in normalized:
            normalized.append(parts)
    return tuple(normalized)


def validate_source_path(
    raw_path: str,
    source_root: Path,
    allowed_prefixes: tuple[tuple[str, ...], ...],
) -> tuple[Path | None, str, str]:
    if (
        not raw_path
        or raw_path.startswith(("/", "~", "\\"))
        or "\\" in raw_path
        or re.match(r"^[A-Za-z]:", raw_path)
    ):
        return None, "source-denied", "相対パスではないため表示できません。"

    raw_parts = raw_path.split("/")
    if any(part in {"", ".", ".."} for part in raw_parts):
        return None, "source-denied", "安全でないパス指定のため表示できません。"

    denied_components = {value.casefold() for value in DENIED_SOURCE_COMPONENTS}
    for part in raw_parts:
        if part.casefold() in denied_components:
            return None, "source-denied", "表示禁止領域のため実コードを取得しません。"
        if part.startswith(".") and part not in ALLOWED_HIDDEN_SOURCE_COMPONENTS:
            return None, "source-denied", "hidden pathは表示対象にできません。"

    basename = raw_parts[-1].casefold()
    suffix = Path(basename).suffix.casefold()
    if (
        basename.startswith(".env")
        or basename in SECRET_SOURCE_NAMES
        or suffix in SECRET_SOURCE_SUFFIXES
    ):
        return None, "source-denied", "秘密情報を格納し得るファイルは表示できません。"

    path_parts = tuple(raw_parts)
    if not any(
        path_parts[: len(prefix)] == prefix
        for prefix in allowed_prefixes
    ):
        return None, "source-denied", "source allowlist外のため表示できません。"

    candidate = source_root.joinpath(*raw_parts)
    try:
        candidate.relative_to(source_root)
    except ValueError:
        return None, "source-denied", "source root外のため表示できません。"

    current = source_root
    for part in raw_parts:
        current = current / part
        try:
            current_stat = current.lstat()
        except FileNotFoundError:
            return None, "source-missing", "参照先のsource fileが見つかりません。"
        except OSError:
            return None, "source-unavailable", "source fileを安全に確認できません。"
        if stat.S_ISLNK(current_stat.st_mode):
            return None, "source-denied", "symlinkは表示対象にできません。"

    try:
        candidate_stat = candidate.stat(follow_symlinks=False)
    except OSError:
        return None, "source-unavailable", "source fileを安全に確認できません。"
    if not stat.S_ISREG(candidate_stat.st_mode):
        return None, "source-denied", "regular fileではないため表示できません。"
    if candidate_stat.st_size > MAX_SOURCE_FILE_BYTES:
        return None, "source-denied", "1MiBを超えるsource fileは読み込みません。"

    try:
        resolved_candidate = candidate.resolve(strict=True)
        resolved_candidate.relative_to(source_root)
    except (OSError, ValueError):
        return None, "source-denied", "source root外のため表示できません。"
    return candidate, "", ""


def markdown_disallows_automation(text: str, relative_path: str) -> bool:
    if Path(relative_path).suffix.casefold() != ".md":
        return False
    lines = text.splitlines()
    if not lines or lines[0].lstrip("\ufeff").strip() != "---":
        return False
    try:
        frontmatter_end = next(
            index for index, line in enumerate(lines[1:], start=1)
            if line.strip() == "---"
        )
    except StopIteration:
        return False
    frontmatter = "\n".join(lines[1:frontmatter_end])
    return bool(
        re.search(
            r"""^\s*automation_read\s*:\s*(?:false|["']false["'])(?:\s*(?:#.*)?)?$""",
            frontmatter,
            re.IGNORECASE | re.MULTILINE,
        )
    )


def contains_secret_content(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_CONTENT_PATTERNS)


def truncate_utf8(text: str, byte_limit: int) -> tuple[str, bool]:
    encoded = text.encode("utf-8")
    if len(encoded) <= byte_limit:
        return text, False
    if byte_limit <= 0:
        return "", True
    return encoded[:byte_limit].decode("utf-8", errors="ignore"), True


def extract_source_preview(
    task_number: str,
    reference: str,
    *,
    source_root: Path | None,
    allowed_prefixes: tuple[tuple[str, ...], ...],
    remaining_bytes: int,
) -> dict[str, object]:
    relative_path, anchor = split_source_reference(reference)
    if source_root is None:
        return source_preview_record(
            task_number,
            relative_path,
            anchor,
            status="source-root-unavailable",
            message="project rootを推定できません。--source-rootを指定してください。",
        )
    if not anchor:
        return source_preview_record(
            task_number,
            relative_path,
            anchor,
            status="source-denied",
            message="source anchorまたはline rangeが未指定です。",
        )

    candidate, status, message = validate_source_path(
        relative_path,
        source_root,
        allowed_prefixes,
    )
    if candidate is None:
        return source_preview_record(
            task_number,
            relative_path,
            anchor,
            status=status,
            message=message,
        )

    try:
        raw = candidate.read_bytes()
    except OSError:
        return source_preview_record(
            task_number,
            relative_path,
            anchor,
            status="source-unavailable",
            message="source fileを読み込めません。",
        )
    if b"\0" in raw:
        return source_preview_record(
            task_number,
            relative_path,
            anchor,
            status="source-denied",
            message="binary fileは表示対象にできません。",
        )
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return source_preview_record(
            task_number,
            relative_path,
            anchor,
            status="source-denied",
            message="UTF-8ではないsource fileは表示できません。",
        )
    if markdown_disallows_automation(text, relative_path):
        return source_preview_record(
            task_number,
            relative_path,
            anchor,
            status="source-denied",
            message="automation_read: falseのため本文を取得しません。",
        )

    lines = text.splitlines()
    range_match = LINE_RANGE_RE.fullmatch(anchor)
    truncated = False
    if range_match:
        requested_start = int(range_match.group(1))
        requested_end = int(range_match.group(2))
        if requested_end < requested_start or requested_start > len(lines):
            return source_preview_record(
                task_number,
                relative_path,
                anchor,
                status="anchor-missing",
                message="指定されたline rangeが見つかりません。",
            )
        start_line = requested_start
        end_line = min(requested_end, len(lines), start_line + MAX_PREVIEW_LINES - 1)
        truncated = end_line < requested_end
    else:
        start_index = next(
            (index for index, line in enumerate(lines) if anchor in line),
            None,
        )
        if start_index is None:
            return source_preview_record(
                task_number,
                relative_path,
                anchor,
                status="anchor-missing",
                message="指定されたanchorが現在のsourceに見つかりません。",
            )
        start_line = start_index + 1
        end_line = min(len(lines), start_line + MAX_PREVIEW_LINES - 1)
        truncated = end_line < len(lines)

    code = "\n".join(lines[start_line - 1 : end_line])
    if contains_secret_content(code):
        return source_preview_record(
            task_number,
            relative_path,
            anchor,
            status="secret-content",
            message="秘密情報らしき内容を検出したため本文を表示しません。",
        )

    code, preview_truncated = truncate_utf8(code, MAX_PREVIEW_BYTES)
    truncated = truncated or preview_truncated
    if remaining_bytes <= 0:
        return source_preview_record(
            task_number,
            relative_path,
            anchor,
            status="budget-exhausted",
            message="snapshotのsource preview上限に達したため本文を表示しません。",
        )
    code, total_truncated = truncate_utf8(code, remaining_bytes)
    truncated = truncated or total_truncated
    return source_preview_record(
        task_number,
        relative_path,
        anchor,
        status="resolved",
        message="",
        start_line=start_line,
        end_line=end_line,
        code=code,
        truncated=truncated,
    )


def collect_source_previews(
    plan: str,
    *,
    source_root: Path | None,
    source_allow_prefixes: list[str] | None,
) -> list[dict[str, object]]:
    references = parse_source_preview_references(plan)
    if not references:
        return []

    normalized_root = (
        source_root.expanduser().resolve(strict=False)
        if source_root is not None
        else None
    )
    allowed_prefixes = normalize_source_prefixes(source_allow_prefixes)
    previews: list[dict[str, object]] = []
    used_bytes = 0
    for task_number, reference in references:
        preview = extract_source_preview(
            task_number,
            reference,
            source_root=normalized_root,
            allowed_prefixes=allowed_prefixes,
            remaining_bytes=MAX_TOTAL_PREVIEW_BYTES - used_bytes,
        )
        previews.append(preview)
        used_bytes += len(str(preview["code"]).encode("utf-8"))
    return previews


def artifact_type(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")
    return suffix or "file"


def is_temporary_file(path: Path) -> bool:
    return path.name.endswith(".tmp")


def collect_artifacts(task_dir: Path, output: Path | None = None) -> list[dict[str, object]]:
    artifacts: list[dict[str, object]] = []
    excluded_paths: set[Path] = set()
    if output is not None:
        excluded_paths.add(output.resolve(strict=False))
        excluded_paths.add(output.with_name("roadmap-snapshot.json").resolve(strict=False))

    for current, directory_names, file_names in os.walk(task_dir, followlinks=False):
        current_dir = Path(current)
        directory_names[:] = sorted(
            name for name in directory_names if not (current_dir / name).is_symlink()
        )
        for name in sorted(file_names):
            path = current_dir / name
            if path.is_symlink() or name in OUTPUT_NAMES or is_temporary_file(path):
                continue
            if path.resolve(strict=False) in excluded_paths:
                continue
            try:
                file_stat = path.stat(follow_symlinks=False)
            except OSError:
                continue
            if not stat.S_ISREG(file_stat.st_mode):
                continue
            relative_path = path.relative_to(task_dir).as_posix()
            artifacts.append(
                {
                    "name": path.name,
                    "path": relative_path,
                    "type": artifact_type(path),
                    "size": file_stat.st_size,
                    "modifiedAt": datetime.fromtimestamp(
                        file_stat.st_mtime, timezone.utc
                    ).isoformat(),
                }
            )

    artifacts.sort(key=lambda item: str(item["path"]))
    return artifacts


def build_fingerprint(
    files: dict[str, str],
    artifacts: list[dict[str, object]],
    source_previews: list[dict[str, object]] | None = None,
    codemap_state: dict[str, object] | None = None,
) -> str:
    payload = {
        "files": files,
        "artifacts": artifacts,
        "sourcePreviews": source_previews or [],
        "codemap": codemap_state or {},
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def infer_title(files: dict[str, str], task_dir: Path) -> str:
    directory_title = re.sub(r"^\d{6,8}[_-]+", "", task_dir.name)
    directory_title = re.sub(r"[_-]+", " ", directory_title).strip()
    if directory_title:
        return directory_title

    for name in ("30_plan.md", "00_spec.md", "05_log.md"):
        text = files.get(name, "")
        for line in text.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                if title:
                    return title
    return "Roadmap"


def load_task_meta(task_dir: Path) -> dict[str, object]:
    path = task_dir / "task-meta.json"
    if not path.is_file() or path.is_symlink():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def load_codemap_state(task_dir: Path, source_root: Path) -> dict[str, object]:
    source = task_dir / "codemap.source.json"
    map_path = task_dir / "codemap.json"
    lock_path = task_dir / "codemap.lock"
    code_change = load_task_meta(task_dir).get("code_change") is True
    if not source.is_file() and not map_path.is_file() and not lock_path.is_file():
        if code_change:
            return {
                "status": "missing",
                "message": "Codemap is required for this code-change task. Run refresh, then check.",
            }
        return {"status": "not-applicable"}
    if not source.is_file() or not map_path.is_file() or not lock_path.is_file():
        return {"status": "missing", "message": "Codemap artifact is incomplete."}

    module_path = Path(__file__).with_name("generate-codemap.py")
    spec = importlib.util.spec_from_file_location("task_codemap_checker", module_path)
    if spec is None or spec.loader is None:
        return {"status": "error", "message": "Codemap checker could not be loaded."}
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        result = module.check(source_root, artifact_dir=task_dir)
        snapshot = json.loads(map_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, RuntimeError) as error:
        message = str(error)
        if "missing" in message.lower():
            status = "missing"
        elif "mismatch" in message.lower():
            status = "mismatch"
        else:
            status = "stale"
        return {"status": status, "message": message}
    counts = snapshot.get("counts")
    if isinstance(counts, dict) and int(counts.get("unknown", 0) or 0) > 0:
        return {
            "status": "insufficient",
            "message": "Codemap still contains unknown relationships.",
            "snapshot": snapshot,
        }
    return {
        "status": str(result.get("status", "fresh")),
        "snapshot": snapshot,
    }


def build_snapshot(
    task_dir: Path,
    output: Path | None = None,
    *,
    source_root: Path | None = None,
    source_allow_prefixes: list[str] | None = None,
) -> dict[str, object]:
    files, sources = read_files(task_dir)
    if not files:
        raise ValueError(f"no roadmap source files found in {task_dir}")
    artifacts = collect_artifacts(task_dir, output)
    effective_source_root = source_root or infer_source_root(task_dir) or task_dir.parent
    source_previews = collect_source_previews(
        files.get("30_plan.md", ""),
        source_root=effective_source_root,
        source_allow_prefixes=source_allow_prefixes,
    )
    codemap_state = load_codemap_state(task_dir, effective_source_root)
    snapshot: dict[str, object] = {
        "version": 1,
        "title": infer_title(files, task_dir),
        "taskDir": str(task_dir),
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "fingerprint": build_fingerprint(
            files, artifacts, source_previews, codemap_state
        ),
        "files": files,
        "sources": sources,
        "artifacts": artifacts,
        "sourcePreviews": source_previews,
        "codemapStatus": codemap_state["status"],
    }
    codemap_snapshot = codemap_state.get("snapshot")
    if isinstance(codemap_snapshot, dict):
        snapshot["codemap"] = codemap_snapshot
    codemap_message = codemap_state.get("message")
    if isinstance(codemap_message, str) and codemap_message:
        snapshot["codemapMessage"] = codemap_message
    return snapshot


def render_html(snapshot: dict[str, object]) -> str:
    template = TEMPLATE.read_text()
    if PLACEHOLDER not in template:
        raise ValueError(f"placeholder not found in {TEMPLATE}")
    payload = json.dumps(snapshot, ensure_ascii=False).replace("</", "<\\/")
    return template.replace(PLACEHOLDER, payload, 1)


def read_json_snapshot(path: Path) -> dict[str, object] | None:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def read_html_snapshot(path: Path) -> dict[str, object] | None:
    try:
        html = path.read_text()
    except OSError:
        return None
    match = EMBEDDED_SNAPSHOT_RE.search(html)
    if not match:
        return None
    try:
        value = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def previous_generated_at(
    fingerprint: str, candidates: list[dict[str, object] | None]
) -> str | None:
    for candidate in candidates:
        if not candidate or candidate.get("fingerprint") != fingerprint:
            continue
        generated_at = candidate.get("generatedAt")
        if isinstance(generated_at, str) and generated_at:
            return generated_at
    return None


def write_outputs(
    task_dir: Path,
    output: Path,
    write_json: bool,
    *,
    source_root: Path | None = None,
    source_allow_prefixes: list[str] | None = None,
    thread_id: str | None = None,
    session_id: str | None = None,
    task_state: str | None = None,
) -> dict[str, object]:
    json_path = output.with_name("roadmap-snapshot.json")
    effective_source_root = source_root or infer_source_root(task_dir) or task_dir.parent
    ensure_task_meta(
        task_dir,
        effective_source_root,
        thread_id=thread_id,
        session_id=session_id,
        task_state=task_state,
    )
    snapshot = build_snapshot(
        task_dir,
        output=output,
        source_root=source_root,
        source_allow_prefixes=source_allow_prefixes,
    )
    previous_timestamp = previous_generated_at(
        str(snapshot["fingerprint"]),
        [
            read_html_snapshot(output),
            read_json_snapshot(json_path) if write_json else None,
        ],
    )
    if previous_timestamp:
        snapshot["generatedAt"] = previous_timestamp

    write_text_if_changed(output, render_html(snapshot))

    if write_json:
        write_text_if_changed(
            json_path,
            json.dumps(snapshot, ensure_ascii=False, indent=2),
        )

    return snapshot


def watch_outputs(
    task_dir: Path,
    output: Path,
    interval: float,
    stop: threading.Event,
    *,
    source_root: Path | None = None,
    source_allow_prefixes: list[str] | None = None,
) -> None:
    while not stop.is_set():
        try:
            write_outputs(
                task_dir,
                output,
                write_json=True,
                source_root=source_root,
                source_allow_prefixes=source_allow_prefixes,
            )
        except Exception as exc:  # pragma: no cover - visible operator feedback
            print(f"watch update failed: {exc}", file=sys.stderr, flush=True)
        stop.wait(interval)


def serve_output(output: Path, host: str, port: int, open_browser: bool) -> int:
    directory = output.parent
    handler = functools.partial(RoadmapHTTPRequestHandler, directory=str(directory))
    server = http.server.ThreadingHTTPServer((host, port), handler)
    actual_host, actual_port = server.server_address[:2]
    url = f"http://{actual_host}:{actual_port}/{output.name}"
    print(url, flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping roadmap server", file=sys.stderr)
    finally:
        server.server_close()
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a browser-readable roadmap.html from a task memory directory."
    )
    parser.add_argument("task_dir", nargs="?", help="Path to .local/memory/<task>")
    parser.add_argument(
        "--hub",
        action="store_true",
        help="Open the Roadmap Task Hub instead of a single task roadmap.",
    )
    parser.add_argument(
        "--memory-root",
        action="append",
        default=[],
        help="Memory root to discover in --hub mode. May be repeated.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output HTML path. Defaults to <task_dir>/roadmap.html.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Write roadmap-snapshot.json next to the HTML as well.",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Serve the generated HTML over local HTTP. Defaults to an OS-assigned free port.",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Keep regenerating roadmap.html and roadmap-snapshot.json until interrupted.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host for --serve. Defaults to 127.0.0.1.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help="Port for --serve. Defaults to 0, letting the OS choose a free port.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Seconds between --watch refreshes. Defaults to 2.0.",
    )
    parser.add_argument(
        "--source-root",
        help=(
            "Project root used to resolve explicit repo: source previews. "
            "Defaults to the project containing .local/memory/<task>."
        ),
    )
    parser.add_argument(
        "--source-allow-prefix",
        action="append",
        default=[],
        help=(
            "Additional relative source prefix allowed for repo: previews. "
            "May be repeated."
        ),
    )
    parser.add_argument("--thread-id", help="Bind task-meta.json to an agent thread ID.")
    parser.add_argument("--session-id", help="Bind task-meta.json to a runtime session ID.")
    parser.add_argument(
        "--task-state",
        choices=("active", "waiting", "verifying", "completed", "archived"),
        help="Update the machine-owned task lifecycle state.",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the generated file or local server URL in the default browser.",
    )
    args = parser.parse_args(argv)
    if args.hub and args.task_dir:
        parser.error("task_dir cannot be used with --hub")
    if not args.hub and not args.task_dir:
        parser.error("task_dir is required unless --hub is used")
    return args


def run_task_hub(
    memory_roots: list[Path],
    *,
    host: str,
    port: int,
    open_browser: bool,
) -> int:
    hub_path = ROOT / "scripts" / "roadmap_task_hub.py"
    spec = importlib.util.spec_from_file_location("roadmap_task_hub", hub_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load Task Hub backend: {hub_path}")
    hub = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = hub
    spec.loader.exec_module(hub)
    return hub.run_task_hub(
        memory_roots,
        host=host,
        port=port,
        open_browser=open_browser,
    )


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if args.hub:
        return run_task_hub(
            [Path(root).expanduser().resolve() for root in args.memory_root],
            host=args.host,
            port=args.port,
            open_browser=args.open,
        )

    task_dir = Path(args.task_dir).expanduser().resolve()
    if not task_dir.is_dir():
        print(f"task_dir is not a directory: {task_dir}", file=sys.stderr)
        return 2

    output = Path(args.output).expanduser().resolve() if args.output else task_dir / "roadmap.html"
    source_root = (
        Path(args.source_root).expanduser().resolve()
        if args.source_root
        else None
    )
    write_json = args.json or args.serve or args.watch
    write_outputs(
        task_dir,
        output,
        write_json=write_json,
        source_root=source_root,
        source_allow_prefixes=args.source_allow_prefix,
        thread_id=args.thread_id,
        session_id=args.session_id,
        task_state=args.task_state,
    )

    print(output)
    if args.serve:
        stop = threading.Event()
        thread = None
        if args.watch:
            thread = threading.Thread(
                target=watch_outputs,
                args=(task_dir, output, args.interval, stop),
                kwargs={
                    "source_root": source_root,
                    "source_allow_prefixes": args.source_allow_prefix,
                },
                daemon=True,
            )
            thread.start()
        try:
            return serve_output(output, args.host, args.port, args.open)
        finally:
            stop.set()
            if thread:
                thread.join(timeout=1)

    if args.watch:
        stop = threading.Event()
        try:
            watch_outputs(
                task_dir,
                output,
                args.interval,
                stop,
                source_root=source_root,
                source_allow_prefixes=args.source_allow_prefix,
            )
        except KeyboardInterrupt:
            print("\nstopping roadmap watch", file=sys.stderr)
        return 0

    if args.open:
        webbrowser.open(output.as_uri())

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
