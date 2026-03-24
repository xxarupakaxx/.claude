"""SessionStartHook: Search past memories via FTS5 only and inject context.

Uses FTS5 text search only (no embedding model) for fast startup.
Reads JSON from stdin: {session_id, transcript_path, cwd, source, model, ...}
Outputs Markdown context to stdout (injected into Claude's context).
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path


MAX_RESULTS = 5
MAX_CONTEXT_LENGTH = 3000  # characters


def main() -> None:
    """Entry point for the SessionStartHook."""
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    source = input_data.get("source", "")
    if source != "startup":
        return

    cwd = input_data.get("cwd", "")
    if not cwd:
        return

    # Validate cwd
    cwd = os.path.realpath(cwd)

    db_path = _resolve_db_path(cwd)
    if not db_path.exists():
        return

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=5000")
    except sqlite3.Error:
        return

    try:
        project_name = Path(cwd).name

        # FTS5 search on chunks (no embedding model needed)
        chunk_results = _fts_search_chunks(conn, project_name)
        knowledge_results = _fts_search_knowledge(conn, project_name)

        all_results = chunk_results + knowledge_results
        if not all_results:
            return

        context = _format_context(all_results[:MAX_RESULTS])
        if context:
            print(context)

    except sqlite3.Error:
        return
    finally:
        conn.close()


def _resolve_db_path(cwd: str) -> Path:
    """Resolve the database path."""
    local_db = Path(cwd) / ".local" / "memory.db"
    if local_db.exists():
        return local_db
    return Path.home() / ".claude" / ".local" / "memory.db"


def _fts_search_chunks(conn: sqlite3.Connection, query: str) -> list[dict]:
    """FTS5 trigram search on chunks. No embedding model needed."""
    escaped = query.replace('"', '""')
    try:
        rows = conn.execute(
            """
            SELECT c.id, c.session_id, c.user_text, c.assistant_text,
                   c.timestamp, c.project, 'chunk' as source
            FROM chunks_fts fts
            JOIN chunks c ON c.id = fts.rowid
            WHERE chunks_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (f'"{escaped}"', MAX_RESULTS),
        ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.OperationalError:
        return []


def _fts_search_knowledge(conn: sqlite3.Connection, query: str) -> list[dict]:
    """FTS5 trigram search on knowledge. No embedding model needed."""
    escaped = query.replace('"', '""')
    try:
        rows = conn.execute(
            """
            SELECT k.id, k.title, k.summary, k.file_path, k.type,
                   'knowledge' as source
            FROM knowledge_fts fts
            JOIN knowledge k ON k.id = fts.rowid
            WHERE knowledge_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (f'"{escaped}"', MAX_RESULTS),
        ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.OperationalError:
        return []


def _format_context(results: list[dict]) -> str:
    """Format search results as Markdown context for injection."""
    lines = ["<sui-memory>", "# 過去のセッションから関連する記憶", ""]

    total_len = 0
    for r in results:
        if r.get("source") == "knowledge":
            entry = _format_knowledge(r)
        else:
            entry = _format_chunk(r)

        if total_len + len(entry) > MAX_CONTEXT_LENGTH:
            break
        lines.append(entry)
        total_len += len(entry)

    lines.append("</sui-memory>")
    return "\n".join(lines)


def _format_chunk(r: dict) -> str:
    """Format a chunk result."""
    user_preview = (r.get("user_text") or "")[:200]
    assistant_preview = (r.get("assistant_text") or "")[:300]
    ts = r.get("timestamp") or "unknown"
    return (
        f"## セッション記録 ({ts})\n"
        f"**Q:** {user_preview}\n"
        f"**A:** {assistant_preview}\n"
    )


def _format_knowledge(r: dict) -> str:
    """Format a knowledge result."""
    title = r.get("title") or r.get("file_path") or "untitled"
    summary = r.get("summary") or ""
    return (
        f"## 知見: {title}\n"
        f"{summary}\n"
    )


if __name__ == "__main__":
    main()
