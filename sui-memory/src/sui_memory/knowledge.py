"""Sync memories/ and solutions/ Markdown files to SQLite knowledge table."""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

from .db import (
    delete_knowledge_by_path,
    get_knowledge_by_path,
    update_knowledge_embedding,
    upsert_knowledge,
)
from .embedder import encode_documents, to_blob


def sync_knowledge(conn: sqlite3.Connection, memory_dir: Path) -> None:
    """Sync all Markdown files in memories/ and solutions/ to the knowledge table.

    Only processes files that have been modified since last sync (mtime-based).
    """
    memories_dir = memory_dir / "memories"
    solutions_dir = memory_dir / "solutions"

    all_files: list[tuple[str, Path]] = []

    if memories_dir.is_dir():
        for md_file in memories_dir.rglob("*.md"):
            all_files.append(("memory", md_file))

    if solutions_dir.is_dir():
        for md_file in solutions_dir.rglob("*.md"):
            all_files.append(("solution", md_file))

    if not all_files:
        return

    # Track existing paths for deletion detection
    existing_paths = set()

    for type_, md_file in all_files:
        file_path_str = str(md_file)
        existing_paths.add(file_path_str)

        mtime = md_file.stat().st_mtime

        # Check if already indexed and up-to-date
        existing = get_knowledge_by_path(conn, file_path_str)
        if existing and existing["file_mtime"] and existing["file_mtime"] >= mtime:
            continue

        # Parse and upsert
        content = md_file.read_text(encoding="utf-8")
        frontmatter = _parse_frontmatter(content)
        body = _strip_frontmatter(content)

        category = _extract_category(md_file, type_)

        knowledge_id = upsert_knowledge(
            conn,
            type_=type_,
            file_path=file_path_str,
            category=category,
            title=frontmatter.get("title") or _extract_title(body),
            summary=frontmatter.get("summary"),
            tags=json.dumps(frontmatter.get("tags", []), ensure_ascii=False)
            if frontmatter.get("tags")
            else None,
            root_cause=frontmatter.get("root_cause"),
            solution_summary=frontmatter.get("solution_summary"),
            content=body,
            file_mtime=mtime,
        )

        # Compute embedding for the combined searchable text
        searchable = _build_searchable_text(frontmatter, body)
        if searchable and knowledge_id:
            embeddings = encode_documents([searchable])
            if embeddings:
                update_knowledge_embedding(conn, knowledge_id, to_blob(embeddings[0]))

    # Delete records for files that no longer exist
    _cleanup_deleted(conn, existing_paths)


def _parse_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from Markdown content."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return {}

    frontmatter = {}
    for line in match.group(1).split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        colon_idx = line.find(":")
        if colon_idx < 0:
            continue

        key = line[:colon_idx].strip()
        value = line[colon_idx + 1 :].strip()

        # Handle YAML arrays [tag1, tag2]
        if value.startswith("[") and value.endswith("]"):
            items = [
                item.strip().strip("'\"")
                for item in value[1:-1].split(",")
                if item.strip()
            ]
            frontmatter[key] = items
        # Handle quoted strings
        elif value.startswith('"') and value.endswith('"'):
            frontmatter[key] = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            frontmatter[key] = value[1:-1]
        else:
            frontmatter[key] = value

    return frontmatter


def _strip_frontmatter(content: str) -> str:
    """Remove YAML frontmatter from content."""
    match = re.match(r"^---\s*\n.*?\n---\s*\n", content, re.DOTALL)
    if match:
        return content[match.end() :]
    return content


def _extract_category(file_path: Path, type_: str) -> str | None:
    """Extract category from file path (parent directory name)."""
    # e.g., solutions/performance-issues/file.md → performance-issues
    # e.g., memories/database/file.md → database
    parts = file_path.parts
    base_dir = "solutions" if type_ == "solution" else "memories"
    try:
        idx = parts.index(base_dir)
        if idx + 1 < len(parts) - 1:
            return parts[idx + 1]
    except ValueError:
        pass
    return None


def _extract_title(body: str) -> str | None:
    """Extract the first H1 heading from Markdown body."""
    match = re.match(r"^#\s+(.+)$", body.strip(), re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None


def _build_searchable_text(frontmatter: dict, body: str) -> str:
    """Build searchable text from frontmatter and body for embedding."""
    parts = []
    if frontmatter.get("title"):
        parts.append(frontmatter["title"])
    if frontmatter.get("summary"):
        parts.append(frontmatter["summary"])
    if frontmatter.get("tags"):
        tags = frontmatter["tags"]
        if isinstance(tags, list):
            parts.append(" ".join(tags))
    if frontmatter.get("root_cause"):
        parts.append(frontmatter["root_cause"])
    # Add first 500 chars of body for context
    if body:
        parts.append(body[:500])
    return " ".join(parts)


def _cleanup_deleted(conn: sqlite3.Connection, existing_paths: set[str]) -> None:
    """Delete knowledge records for files that no longer exist."""
    rows = conn.execute("SELECT file_path FROM knowledge").fetchall()
    for row in rows:
        if row["file_path"] not in existing_paths:
            # Verify the file really doesn't exist (not just excluded from scan)
            if not Path(row["file_path"]).exists():
                delete_knowledge_by_path(conn, row["file_path"])
