"""CLI commands for sui-memory management."""

from __future__ import annotations

import sys
from pathlib import Path

from .db import DEFAULT_DB_PATH, get_connection, init_db
from .knowledge import sync_knowledge


def main() -> None:
    """CLI entry point. Usage: python -m sui_memory.cli [command] [args]"""
    args = sys.argv[1:]
    if not args:
        _print_usage()
        return

    command = args[0]

    if command == "sync":
        _sync(args[1:])
    elif command == "stats":
        _stats(args[1:])
    elif command == "search":
        _search(args[1:])
    else:
        print(f"Unknown command: {command}")
        _print_usage()


def _sync(args: list[str]) -> None:
    """Sync memories/ and solutions/ Markdown files to SQLite."""
    memory_dir = Path(args[0]) if args else Path.home() / ".claude" / ".local"
    db_path = memory_dir / "memory.db"

    print(f"Syncing knowledge from {memory_dir} to {db_path}...")
    conn = get_connection(db_path)
    init_db(conn)

    try:
        sync_knowledge(conn, memory_dir)
        # Show stats
        chunks = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        knowledge = conn.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]
        sessions = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        print(f"Done. DB stats: {sessions} sessions, {chunks} chunks, {knowledge} knowledge records")
    finally:
        conn.close()


def _stats(args: list[str]) -> None:
    """Show database statistics."""
    db_path = Path(args[0]) if args else DEFAULT_DB_PATH
    if not db_path.exists():
        print(f"DB not found: {db_path}")
        return

    conn = get_connection(db_path)
    try:
        sessions = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        chunks = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        chunks_with_emb = conn.execute("SELECT COUNT(*) FROM chunks WHERE embedding IS NOT NULL").fetchone()[0]
        knowledge = conn.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]
        knowledge_with_emb = conn.execute("SELECT COUNT(*) FROM knowledge WHERE embedding IS NOT NULL").fetchone()[0]

        print(f"Database: {db_path}")
        print(f"  Sessions: {sessions}")
        print(f"  Chunks: {chunks} ({chunks_with_emb} with embeddings)")
        print(f"  Knowledge: {knowledge} ({knowledge_with_emb} with embeddings)")
    finally:
        conn.close()


def _search(args: list[str]) -> None:
    """Search memories."""
    if not args:
        print("Usage: python -m sui_memory.cli search <query> [db_path]")
        return

    query = args[0]
    db_path = Path(args[1]) if len(args) > 1 else DEFAULT_DB_PATH
    if not db_path.exists():
        print(f"DB not found: {db_path}")
        return

    from .retriever import search

    conn = get_connection(db_path)
    init_db(conn)

    try:
        results = search(conn, query, limit=10)
        if not results:
            print("No results found.")
            return

        for i, r in enumerate(results, 1):
            print(f"\n--- Result {i} (score: {r.score:.4f}, source: {r.source}) ---")
            if r.source == "knowledge":
                print(f"  Title: {r.title}")
                print(f"  File: {r.file_path}")
                print(f"  Summary: {(r.summary or '')[:200]}")
            else:
                print(f"  Session: {r.session_id}")
                print(f"  Time: {r.timestamp}")
                print(f"  Q: {r.user_text[:150]}")
                print(f"  A: {r.assistant_text[:150]}")
    finally:
        conn.close()


def _print_usage() -> None:
    print("Usage: python -m sui_memory.cli <command> [args]")
    print()
    print("Commands:")
    print("  sync [memory_dir]   - Sync Markdown files to SQLite (default: ~/.claude/.local/)")
    print("  stats [db_path]     - Show database statistics")
    print("  search <query>      - Search memories and knowledge")


if __name__ == "__main__":
    main()
