"""SessionStartHook: Search past memories and inject context via stdout.

Called when a new session starts.
Reads JSON from stdin: {session_id, transcript_path, cwd, source, model, ...}
Outputs Markdown context to stdout (injected into Claude's context).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .db import DEFAULT_DB_PATH, get_connection, init_db
from .retriever import SearchResult, search


MAX_RESULTS = 5
MAX_CONTEXT_LENGTH = 3000  # characters


def main() -> None:
    """Entry point for the SessionStartHook."""
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    source = input_data.get("source", "")
    # Only inject on fresh startup, not resume/clear/compact
    if source != "startup":
        return

    cwd = input_data.get("cwd", "")
    if not cwd:
        return

    # Resolve DB path
    db_path = _resolve_db_path(cwd)
    if not db_path.exists():
        return

    conn = get_connection(db_path)
    init_db(conn)

    try:
        # Build search query from project context
        project_name = Path(cwd).name
        query = f"{project_name}"

        results = search(
            conn,
            query,
            limit=MAX_RESULTS,
            include_chunks=True,
            include_knowledge=True,
        )

        if not results:
            return

        # Format and output context
        context = _format_context(results)
        if context:
            print(context)

    finally:
        conn.close()


def _resolve_db_path(cwd: str) -> Path:
    """Resolve the database path."""
    if cwd:
        local_db = Path(cwd) / ".local" / "memory.db"
        if local_db.exists():
            return local_db
    return DEFAULT_DB_PATH


def _format_context(results: list[SearchResult]) -> str:
    """Format search results as Markdown context for injection."""
    lines = ["<sui-memory>", "# 過去のセッションから関連する記憶", ""]

    total_len = 0
    for r in results:
        if r.source == "knowledge":
            entry = _format_knowledge(r)
        else:
            entry = _format_chunk(r)

        if total_len + len(entry) > MAX_CONTEXT_LENGTH:
            break
        lines.append(entry)
        total_len += len(entry)

    lines.append("</sui-memory>")
    return "\n".join(lines)


def _format_chunk(r: SearchResult) -> str:
    """Format a chunk result."""
    user_preview = r.user_text[:200]
    assistant_preview = r.assistant_text[:300]
    ts = r.timestamp or "unknown"
    return (
        f"## セッション記録 ({ts})\n"
        f"**Q:** {user_preview}\n"
        f"**A:** {assistant_preview}\n"
    )


def _format_knowledge(r: SearchResult) -> str:
    """Format a knowledge result."""
    title = r.title or r.file_path or "untitled"
    summary = r.summary or r.assistant_text[:200]
    return (
        f"## 知見: {title}\n"
        f"{summary}\n"
    )


if __name__ == "__main__":
    main()
