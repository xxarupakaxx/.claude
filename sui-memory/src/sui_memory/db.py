"""SQLite database schema, migrations, and CRUD operations."""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

import sqlite_vec


DEFAULT_DB_PATH = Path.home() / ".claude" / ".local" / "memory.db"

SCHEMA_VERSION = 1

_SCHEMA_SQL = """
-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    project TEXT,
    cwd TEXT,
    branch TEXT,
    started_at TEXT,
    ended_at TEXT,
    message_count INTEGER DEFAULT 0,
    created_at REAL NOT NULL
);

-- Q&A chunks extracted from transcripts
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    project TEXT,
    user_text TEXT NOT NULL,
    assistant_text TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    created_at REAL NOT NULL,
    embedding BLOB,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE INDEX IF NOT EXISTS idx_chunks_session_id ON chunks(session_id);
CREATE INDEX IF NOT EXISTS idx_chunks_project ON chunks(project);
CREATE INDEX IF NOT EXISTS idx_chunks_created_at ON chunks(created_at);

-- FTS5 full-text search index for chunks (trigram tokenizer for Japanese)
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    user_text,
    assistant_text,
    content=chunks,
    content_rowid=id,
    tokenize='trigram'
);

-- Auto-sync triggers for chunks_fts
CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts(rowid, user_text, assistant_text)
    VALUES (new.id, new.user_text, new.assistant_text);
END;
CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, user_text, assistant_text)
    VALUES ('delete', old.id, old.user_text, old.assistant_text);
END;
CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, user_text, assistant_text)
    VALUES ('delete', old.id, old.user_text, old.assistant_text);
    INSERT INTO chunks_fts(rowid, user_text, assistant_text)
    VALUES (new.id, new.user_text, new.assistant_text);
END;

-- Knowledge index for memories/ and solutions/ Markdown files
CREATE TABLE IF NOT EXISTS knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    category TEXT,
    file_path TEXT UNIQUE NOT NULL,
    title TEXT,
    summary TEXT,
    tags TEXT,
    root_cause TEXT,
    solution_summary TEXT,
    content TEXT,
    file_mtime REAL,
    ref_count INTEGER DEFAULT 0,
    created_at REAL NOT NULL,
    updated_at REAL,
    last_accessed REAL,
    embedding BLOB
);

CREATE INDEX IF NOT EXISTS idx_knowledge_type ON knowledge(type);
CREATE INDEX IF NOT EXISTS idx_knowledge_file_path ON knowledge(file_path);

-- FTS5 full-text search index for knowledge
CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
    title,
    summary,
    tags,
    root_cause,
    content,
    content=knowledge,
    content_rowid=id,
    tokenize='trigram'
);

-- Auto-sync triggers for knowledge_fts
CREATE TRIGGER IF NOT EXISTS knowledge_ai AFTER INSERT ON knowledge BEGIN
    INSERT INTO knowledge_fts(rowid, title, summary, tags, root_cause, content)
    VALUES (new.id, new.title, new.summary, new.tags, new.root_cause, new.content);
END;
CREATE TRIGGER IF NOT EXISTS knowledge_ad AFTER DELETE ON knowledge BEGIN
    INSERT INTO knowledge_fts(knowledge_fts, rowid, title, summary, tags, root_cause, content)
    VALUES ('delete', old.id, old.title, old.summary, old.tags, old.root_cause, old.content);
END;
CREATE TRIGGER IF NOT EXISTS knowledge_au AFTER UPDATE ON knowledge BEGIN
    INSERT INTO knowledge_fts(knowledge_fts, rowid, title, summary, tags, root_cause, content)
    VALUES ('delete', old.id, old.title, old.summary, old.tags, old.root_cause, old.content);
    INSERT INTO knowledge_fts(rowid, title, summary, tags, root_cause, content)
    VALUES (new.id, new.title, new.summary, new.tags, new.root_cause, new.content);
END;
"""


def get_connection(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Create a SQLite connection with sqlite-vec loaded and WAL mode enabled."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")

    # Set restrictive file permissions (owner read/write only)
    import os
    try:
        os.chmod(str(db_path), 0o600)
    except OSError:
        pass

    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)

    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Initialize the database schema if needed."""
    version = _get_schema_version(conn)
    if version < SCHEMA_VERSION:
        conn.executescript(_SCHEMA_SQL)
        conn.execute(
            "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
            (SCHEMA_VERSION,),
        )
        conn.commit()


def _get_schema_version(conn: sqlite3.Connection) -> int:
    """Get current schema version, 0 if table doesn't exist."""
    try:
        row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        return row[0] or 0
    except sqlite3.OperationalError:
        return 0


# --- Session CRUD ---


def upsert_session(
    conn: sqlite3.Connection,
    session_id: str,
    *,
    project: str | None = None,
    cwd: str | None = None,
    branch: str | None = None,
    started_at: str | None = None,
    ended_at: str | None = None,
    message_count: int = 0,
) -> None:
    """Insert or update a session record."""
    conn.execute(
        """
        INSERT INTO sessions (session_id, project, cwd, branch, started_at, ended_at, message_count, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET
            project = COALESCE(excluded.project, sessions.project),
            cwd = COALESCE(excluded.cwd, sessions.cwd),
            branch = COALESCE(excluded.branch, sessions.branch),
            started_at = COALESCE(excluded.started_at, sessions.started_at),
            ended_at = COALESCE(excluded.ended_at, sessions.ended_at),
            message_count = excluded.message_count
        """,
        (session_id, project, cwd, branch, started_at, ended_at, message_count, time.time()),
    )
    conn.commit()


def get_session_chunk_count(conn: sqlite3.Connection, session_id: str) -> int:
    """Get the number of chunks for a session."""
    row = conn.execute(
        "SELECT COUNT(*) FROM chunks WHERE session_id = ?", (session_id,)
    ).fetchone()
    return row[0]


# --- Chunk CRUD ---


def insert_chunks(
    conn: sqlite3.Connection,
    chunks: list[dict],
) -> list[int]:
    """Insert multiple chunks and return their IDs."""
    ids = []
    for chunk in chunks:
        cursor = conn.execute(
            """
            INSERT INTO chunks (session_id, project, user_text, assistant_text, timestamp, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                chunk["session_id"],
                chunk.get("project"),
                chunk["user_text"],
                chunk["assistant_text"],
                chunk["timestamp"],
                time.time(),
            ),
        )
        ids.append(cursor.lastrowid)
    conn.commit()
    return ids


def update_chunk_embedding(conn: sqlite3.Connection, chunk_id: int, embedding: bytes) -> None:
    """Update the embedding for a chunk."""
    conn.execute(
        "UPDATE chunks SET embedding = ? WHERE id = ?",
        (embedding, chunk_id),
    )
    conn.commit()


def update_chunk_embeddings_batch(
    conn: sqlite3.Connection, id_embedding_pairs: list[tuple[int, bytes]]
) -> None:
    """Batch update embeddings for multiple chunks."""
    conn.executemany(
        "UPDATE chunks SET embedding = ? WHERE id = ?",
        [(emb, cid) for cid, emb in id_embedding_pairs],
    )
    conn.commit()


# --- Knowledge CRUD ---


def upsert_knowledge(
    conn: sqlite3.Connection,
    *,
    type_: str,
    file_path: str,
    category: str | None = None,
    title: str | None = None,
    summary: str | None = None,
    tags: str | None = None,
    root_cause: str | None = None,
    solution_summary: str | None = None,
    content: str | None = None,
    file_mtime: float | None = None,
) -> int:
    """Insert or update a knowledge record. Returns the row ID."""
    now = time.time()
    cursor = conn.execute(
        """
        INSERT INTO knowledge (type, category, file_path, title, summary, tags,
                               root_cause, solution_summary, content, file_mtime,
                               created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(file_path) DO UPDATE SET
            type = excluded.type,
            category = excluded.category,
            title = excluded.title,
            summary = excluded.summary,
            tags = excluded.tags,
            root_cause = excluded.root_cause,
            solution_summary = excluded.solution_summary,
            content = excluded.content,
            file_mtime = excluded.file_mtime,
            updated_at = excluded.updated_at
        """,
        (type_, category, file_path, title, summary, tags,
         root_cause, solution_summary, content, file_mtime,
         now, now),
    )
    conn.commit()
    return cursor.lastrowid


def update_knowledge_embedding(conn: sqlite3.Connection, knowledge_id: int, embedding: bytes) -> None:
    """Update the embedding for a knowledge record."""
    conn.execute(
        "UPDATE knowledge SET embedding = ? WHERE id = ?",
        (embedding, knowledge_id),
    )
    conn.commit()


def get_knowledge_by_path(conn: sqlite3.Connection, file_path: str) -> sqlite3.Row | None:
    """Get a knowledge record by file path."""
    return conn.execute(
        "SELECT * FROM knowledge WHERE file_path = ?", (file_path,)
    ).fetchone()


def delete_knowledge_by_path(conn: sqlite3.Connection, file_path: str) -> None:
    """Delete a knowledge record by file path."""
    conn.execute("DELETE FROM knowledge WHERE file_path = ?", (file_path,))
    conn.commit()


def increment_knowledge_ref(conn: sqlite3.Connection, knowledge_id: int) -> None:
    """Increment ref_count and update last_accessed."""
    conn.execute(
        "UPDATE knowledge SET ref_count = ref_count + 1, last_accessed = ? WHERE id = ?",
        (time.time(), knowledge_id),
    )
    conn.commit()
