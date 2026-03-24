"""StopHook: Parse transcript and save new chunks to SQLite with embeddings.

Called after each Claude response completes.
Reads JSON from stdin: {session_id, transcript_path, cwd, stop_hook_active, ...}
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from .chunker import parse_transcript
from .db import (
    DEFAULT_DB_PATH,
    get_connection,
    get_session_chunk_count,
    init_db,
    insert_chunks,
    update_chunk_embeddings_batch,
    upsert_session,
)
from .embedder import encode_documents, to_blob
from .knowledge import sync_knowledge


def main() -> None:
    """Entry point for the StopHook."""
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    # Prevent infinite loop
    if input_data.get("stop_hook_active"):
        return

    session_id = input_data.get("session_id", "")
    transcript_path = input_data.get("transcript_path", "")
    cwd = input_data.get("cwd", "")

    if not session_id or not transcript_path:
        return

    # Resolve DB path: use project-local .local/memory.db if it exists,
    # otherwise fall back to global
    db_path = _resolve_db_path(cwd)
    conn = get_connection(db_path)
    init_db(conn)

    try:
        # Parse transcript
        all_chunks = parse_transcript(transcript_path)
        if not all_chunks:
            return

        # Determine branch
        branch = _get_git_branch(cwd)

        # Upsert session
        timestamps = [c["timestamp"] for c in all_chunks if c.get("timestamp")]
        upsert_session(
            conn,
            session_id,
            project=all_chunks[0].get("project"),
            cwd=cwd,
            branch=branch,
            started_at=timestamps[0] if timestamps else None,
            ended_at=timestamps[-1] if timestamps else None,
            message_count=len(all_chunks),
        )

        # Only insert new chunks (delta)
        existing_count = get_session_chunk_count(conn, session_id)
        new_chunks = all_chunks[existing_count:]
        if not new_chunks:
            return

        # Insert chunks (without embeddings first)
        chunk_ids = insert_chunks(conn, new_chunks)

        # Compute embeddings for new chunks
        texts = [
            f"{c['user_text']}\n{c['assistant_text']}" for c in new_chunks
        ]
        embeddings = encode_documents(texts)

        # Update embeddings in batch
        pairs = [
            (cid, to_blob(emb)) for cid, emb in zip(chunk_ids, embeddings)
        ]
        update_chunk_embeddings_batch(conn, pairs)

        # Sync knowledge (memories/ and solutions/) if they exist
        memory_dir = _resolve_memory_dir(cwd)
        if memory_dir:
            sync_knowledge(conn, memory_dir)

    finally:
        conn.close()


def _resolve_db_path(cwd: str) -> Path:
    """Resolve the database path, preferring project-local .local/memory.db."""
    if cwd:
        local_dir = Path(cwd) / ".local"
        if local_dir.is_dir():
            return local_dir / "memory.db"
    return DEFAULT_DB_PATH


def _resolve_memory_dir(cwd: str) -> Path | None:
    """Resolve the memory directory (.local/) for knowledge sync."""
    if cwd:
        local_dir = Path(cwd) / ".local"
        if local_dir.is_dir():
            return local_dir
    global_dir = Path.home() / ".claude" / ".local"
    if global_dir.is_dir():
        return global_dir
    return None


def _get_git_branch(cwd: str) -> str | None:
    """Get the current git branch name."""
    if not cwd:
        return None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return None


if __name__ == "__main__":
    main()
