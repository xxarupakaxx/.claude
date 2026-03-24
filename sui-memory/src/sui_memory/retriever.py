"""Hybrid search: FTS5 + vector search with RRF fusion and time decay."""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass

from .embedder import encode_query, to_blob


@dataclass
class SearchResult:
    id: int
    source: str  # "chunk" or "knowledge"
    user_text: str
    assistant_text: str
    session_id: str | None
    timestamp: str | None
    score: float
    # knowledge-specific fields
    title: str | None = None
    summary: str | None = None
    file_path: str | None = None
    type_: str | None = None


def search(
    conn: sqlite3.Connection,
    query: str,
    *,
    limit: int = 5,
    fts_limit: int = 20,
    vec_limit: int = 20,
    half_life_days: int = 30,
    include_chunks: bool = True,
    include_knowledge: bool = True,
) -> list[SearchResult]:
    """Unified search across chunks and knowledge with RRF + time decay."""
    results: dict[str, SearchResult] = {}
    scores: dict[str, float] = {}

    if include_chunks:
        fts_chunks = _fts_search_chunks(conn, query, limit=fts_limit)
        vec_chunks = _vec_search_chunks(conn, query, limit=vec_limit)
        _merge_rrf(results, scores, fts_chunks, "chunk")
        _merge_rrf(results, scores, vec_chunks, "chunk")

    if include_knowledge:
        fts_knowledge = _fts_search_knowledge(conn, query, limit=fts_limit)
        vec_knowledge = _vec_search_knowledge(conn, query, limit=vec_limit)
        _merge_rrf(results, scores, fts_knowledge, "knowledge")
        _merge_rrf(results, scores, vec_knowledge, "knowledge")

    # Apply time decay
    now = time.time()
    for key, result in results.items():
        created_at = _parse_timestamp(result.timestamp) if result.timestamp else now
        decay = _time_decay(created_at, now, half_life_days)
        scores[key] *= decay

    # Sort by score and return top results with score set
    sorted_keys = sorted(scores, key=lambda k: scores[k], reverse=True)
    final = []
    for k in sorted_keys[:limit]:
        result = results[k]
        result.score = scores[k]
        final.append(result)
    return final


def _fts_search_chunks(
    conn: sqlite3.Connection, query: str, *, limit: int = 20
) -> list[tuple[SearchResult, int]]:
    """FTS5 trigram search on chunks."""
    # Escape special FTS5 characters
    escaped = query.replace('"', '""')
    try:
        rows = conn.execute(
            """
            SELECT c.id, c.session_id, c.user_text, c.assistant_text,
                   c.timestamp, c.project
            FROM chunks_fts fts
            JOIN chunks c ON c.id = fts.rowid
            WHERE chunks_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (f'"{escaped}"', limit),
        ).fetchall()
    except sqlite3.OperationalError:
        return []

    return [
        (
            SearchResult(
                id=row["id"],
                source="chunk",
                user_text=row["user_text"],
                assistant_text=row["assistant_text"],
                session_id=row["session_id"],
                timestamp=row["timestamp"],
                score=0,
            ),
            rank,
        )
        for rank, row in enumerate(rows)
    ]


def _vec_search_chunks(
    conn: sqlite3.Connection, query: str, *, limit: int = 20
) -> list[tuple[SearchResult, int]]:
    """Vector similarity search on chunks using vec_distance_cosine."""
    query_emb = encode_query(query)
    query_blob = to_blob(query_emb)

    rows = conn.execute(
        """
        SELECT id, session_id, user_text, assistant_text, timestamp, project,
               vec_distance_cosine(embedding, ?) AS distance
        FROM chunks
        WHERE embedding IS NOT NULL
        ORDER BY distance ASC
        LIMIT ?
        """,
        (query_blob, limit),
    ).fetchall()

    return [
        (
            SearchResult(
                id=row["id"],
                source="chunk",
                user_text=row["user_text"],
                assistant_text=row["assistant_text"],
                session_id=row["session_id"],
                timestamp=row["timestamp"],
                score=0,
            ),
            rank,
        )
        for rank, row in enumerate(rows)
    ]


def _fts_search_knowledge(
    conn: sqlite3.Connection, query: str, *, limit: int = 20
) -> list[tuple[SearchResult, int]]:
    """FTS5 trigram search on knowledge."""
    escaped = query.replace('"', '""')
    try:
        rows = conn.execute(
            """
            SELECT k.id, k.type, k.file_path, k.title, k.summary,
                   k.content, k.created_at
            FROM knowledge_fts fts
            JOIN knowledge k ON k.id = fts.rowid
            WHERE knowledge_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (f'"{escaped}"', limit),
        ).fetchall()
    except sqlite3.OperationalError:
        return []

    return [
        (
            SearchResult(
                id=row["id"],
                source="knowledge",
                user_text=row["summary"] or "",
                assistant_text=row["content"] or "",
                session_id=None,
                timestamp=None,
                score=0,
                title=row["title"],
                summary=row["summary"],
                file_path=row["file_path"],
                type_=row["type"],
            ),
            rank,
        )
        for rank, row in enumerate(rows)
    ]


def _vec_search_knowledge(
    conn: sqlite3.Connection, query: str, *, limit: int = 20
) -> list[tuple[SearchResult, int]]:
    """Vector similarity search on knowledge."""
    query_emb = encode_query(query)
    query_blob = to_blob(query_emb)

    rows = conn.execute(
        """
        SELECT id, type, file_path, title, summary, content, created_at,
               vec_distance_cosine(embedding, ?) AS distance
        FROM knowledge
        WHERE embedding IS NOT NULL
        ORDER BY distance ASC
        LIMIT ?
        """,
        (query_blob, limit),
    ).fetchall()

    return [
        (
            SearchResult(
                id=row["id"],
                source="knowledge",
                user_text=row["summary"] or "",
                assistant_text=row["content"] or "",
                session_id=None,
                timestamp=None,
                score=0,
                title=row["title"],
                summary=row["summary"],
                file_path=row["file_path"],
                type_=row["type"],
            ),
            rank,
        )
        for rank, row in enumerate(rows)
    ]


def _merge_rrf(
    results: dict[str, SearchResult],
    scores: dict[str, float],
    ranked_items: list[tuple[SearchResult, int]],
    source: str,
    k: int = 60,
) -> None:
    """Merge results using Reciprocal Rank Fusion."""
    for result, rank in ranked_items:
        key = f"{source}:{result.id}"
        rrf_score = 1.0 / (k + rank)
        if key in scores:
            scores[key] += rrf_score
        else:
            results[key] = result
            scores[key] = rrf_score


def _time_decay(created_at: float, now: float, half_life_days: int = 30) -> float:
    """Exponential time decay with configurable half-life."""
    elapsed = now - created_at
    half_life_seconds = half_life_days * 86400
    if half_life_seconds <= 0:
        return 1.0
    return 0.5 ** (elapsed / half_life_seconds)


def _parse_timestamp(ts: str) -> float:
    """Parse ISO timestamp to Unix timestamp."""
    try:
        from datetime import datetime, timezone

        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.timestamp()
    except (ValueError, AttributeError):
        return time.time()
