"""Parse Claude Code transcript JSONL into Q&A chunks."""

from __future__ import annotations

import json
import re
from pathlib import Path

# Patterns for detecting secrets/credentials in text
_SECRET_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9_-]{20,}"),           # OpenAI/Stripe API keys
    re.compile(r"ghp_[a-zA-Z0-9]{36,}"),             # GitHub personal access tokens
    re.compile(r"ghs_[a-zA-Z0-9]{36,}"),             # GitHub server tokens
    re.compile(r"github_pat_[a-zA-Z0-9_]{22,}"),     # GitHub fine-grained PATs
    re.compile(r"AKIA[0-9A-Z]{16}"),                  # AWS access key IDs
    re.compile(r"xox[bpsa]-[a-zA-Z0-9-]{10,}"),      # Slack tokens
    re.compile(r"Bearer\s+[a-zA-Z0-9._\-]{20,}"),    # Bearer tokens
    re.compile(r"password\s*[=:]\s*\S{8,}", re.IGNORECASE),  # password assignments
    re.compile(r"secret\s*[=:]\s*\S{8,}", re.IGNORECASE),    # secret assignments
    re.compile(r"token\s*[=:]\s*['\"]?[a-zA-Z0-9._\-]{20,}"),  # token assignments
]


def parse_transcript(transcript_path: str | Path) -> list[dict]:
    """Parse a transcript JSONL file into Q&A chunks.

    Each chunk contains:
        - session_id: str
        - user_text: str
        - assistant_text: str
        - timestamp: str
        - project: str | None
    """
    transcript_path = Path(transcript_path)
    if not transcript_path.exists():
        return []

    entries = []
    with transcript_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entries.append(entry)
            except json.JSONDecodeError:
                continue

    return _pair_entries(entries)


def _mask_secrets(text: str) -> str:
    """Mask potential secrets/credentials in text."""
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


def _pair_entries(entries: list[dict]) -> list[dict]:
    """Pair user and assistant entries into Q&A chunks."""
    chunks = []
    pending_user: dict | None = None

    for entry in entries:
        entry_type = entry.get("type")

        if entry_type in ("file-history-snapshot", "summary", "system"):
            continue

        if entry_type == "user":
            user_text = _extract_user_text(entry)
            if user_text:
                pending_user = {
                    "user_text": user_text,
                    "session_id": entry.get("sessionId", ""),
                    "timestamp": entry.get("timestamp", ""),
                    "project": _extract_project(entry),
                }

        elif entry_type == "assistant" and pending_user is not None:
            assistant_text = _extract_assistant_text(entry)
            if assistant_text:
                chunks.append({
                    **pending_user,
                    "user_text": _mask_secrets(pending_user["user_text"]),
                    "assistant_text": _mask_secrets(assistant_text),
                })
                pending_user = None

    return chunks


def _extract_user_text(entry: dict) -> str:
    """Extract text content from a user entry."""
    message = entry.get("message", {})
    content = message.get("content")

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                block_type = block.get("type", "")
                if block_type == "text":
                    parts.append(block.get("text", ""))
                elif block_type == "tool_result":
                    # Skip tool results - they're noisy
                    pass
        return "\n".join(parts).strip()

    return ""


def _extract_assistant_text(entry: dict) -> str:
    """Extract text content from an assistant entry, excluding thinking/tool_use."""
    message = entry.get("message", {})
    content = message.get("content")

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                block_type = block.get("type", "")
                if block_type == "text":
                    parts.append(block.get("text", ""))
                # Skip: thinking, tool_use, tool_result
        return "\n".join(parts).strip()

    return ""


def _extract_project(entry: dict) -> str | None:
    """Extract project name from cwd."""
    cwd = entry.get("cwd")
    if cwd:
        return Path(cwd).name
    return None
