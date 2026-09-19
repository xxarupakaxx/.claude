#!/usr/bin/env python3
"""Read local usage counters, never print transcript text or execute log contents."""

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

FIELDS = ("input_tokens", "uncached_input_tokens", "cached_input_tokens",
          "cache_write_input_tokens", "output_tokens", "reasoning_output_tokens", "total_tokens")
MAX_BYTES = 64 * 1024 * 1024
MAX_LINE = 8 * 1024 * 1024
MAX_FILES = 128
MAX_CANDIDATES = 10000
ID = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")
LABEL = re.compile(r"[A-Za-z0-9_.:/-]{1,128}\Z")


class AnalysisError(Exception):
    pass


def number(value):
    return value if type(value) is int and value >= 0 else None


def total(values):
    values = list(values)
    return sum(values) if values and all(v is not None for v in values) else None


def subtract(a, b):
    return a - b if a is not None and b is not None and a >= b else None


def label(value):
    return value if isinstance(value, str) and LABEL.fullmatch(value) else "unknown"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def normalize(usage, provider):
    usage = usage if isinstance(usage, dict) else {}
    inp = number(usage.get("input_tokens"))
    out = number(usage.get("output_tokens"))
    if provider == "claude":
        cache = number(usage.get("cache_read_input_tokens"))
        write = number(usage.get("cache_creation_input_tokens"))
        uncached, inp = inp, total([inp, cache, write])
        details = usage.get("output_tokens_details") or {}
        reasoning = number(details.get("thinking_tokens")) if isinstance(details, dict) else None
    else:
        cache = number(usage.get("cached_input_tokens"))
        write = number(usage.get("cache_write_input_tokens"))
        uncached = subtract(inp, cache)
        reasoning = number(usage.get("reasoning_output_tokens"))
    return dict(zip(FIELDS, [inp, uncached, cache, write, out, reasoning, total([inp, out])]))


def summed(rows):
    return {key: total(row["tokens"][key] for row in rows) for key in FIELDS}


def read_rows(path, warnings):
    """Read a fixed byte boundary so a live writer cannot extend this run forever."""
    try:
        limit = path.stat().st_size
        if limit > MAX_BYTES:
            raise AnalysisError("log_too_large: select a smaller explicit transcript")
        with path.open("rb") as stream:
            remaining = limit
            line_no = 0
            while remaining:
                raw = stream.readline(min(remaining, MAX_LINE + 1))
                if not raw:
                    warnings.add("file_changed_during_read")
                    break
                remaining -= len(raw)
                line_no += 1
                if len(raw) > MAX_LINE:
                    raise AnalysisError("log_line_too_large")
                try:
                    row = json.loads(raw)
                    if not isinstance(row, dict):
                        raise ValueError()
                except (ValueError, UnicodeError):
                    warnings.add("incomplete_tail" if remaining == 0 else "malformed_record")
                    continue
                yield line_no, row
    except OSError:
        raise AnalysisError("log_unreadable") from None


def header(path):
    try:
        with path.open("rb") as stream:
            raw = stream.readline(MAX_LINE + 1)
        row = json.loads(raw)
        payload = row.get("payload", {})
        return payload if row.get("type") == "session_meta" and isinstance(payload, dict) else {}
    except (OSError, ValueError, AttributeError):
        return {}


def candidates(root, pattern):
    found = []
    for path in root.rglob(pattern):
        if path.is_file():
            found.append(path)
        if len(found) > MAX_CANDIDATES:
            raise AnalysisError("discovery_limit: supply --log; narrow --root for child discovery")
    return sorted(found)


def resolve_log(provider, session_id, root, explicit):
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if not path.is_file():
            raise AnalysisError("log_not_found")
        return path
    matches = candidates(root, f"*{session_id}*.jsonl" if provider == "codex" else f"{session_id}.jsonl")
    if provider == "codex":
        matches = [p for p in matches if header(p).get("id") == session_id]
    if len(matches) != 1:
        raise AnalysisError("session_not_unique: supply --log for the intended session")
    return matches[0]


def discover_children(provider, root, path, session_id):
    if provider == "claude":
        return [(p, session_id) for p in candidates(path.with_suffix("") / "subagents", "*.jsonl")]
    related, known = [], {session_id}
    links = []
    for p in candidates(root, "*.jsonl"):
        if p.resolve() == path.resolve():
            continue
        meta = header(p)
        source = meta.get("source")
        if not isinstance(source, dict):
            continue
        subagent = source.get("subagent", {})
        spawn = subagent.get("thread_spawn", {}) if isinstance(subagent, dict) else {}
        parent = spawn.get("parent_thread_id") if isinstance(spawn, dict) else None
        if parent and isinstance(meta.get("id"), str):
            links.append((p, meta["id"], parent))
    while True:
        additions = [(p, sid) for p, sid, parent in links if parent in known and sid not in known]
        if not additions:
            break
        if len({sid for _, sid in additions}) != len(additions):
            raise AnalysisError("child_session_not_unique: narrow --root")
        related.extend(additions)
        known.update(sid for _, sid in additions)
        if len(related) >= MAX_FILES:
            raise AnalysisError("child_limit: narrow the requested scope")
    return related


class Activity:
    """Content sizes are proxies; hashes only detect identical local output."""

    def __init__(self):
        self.tools = Counter()
        self.output_bytes = 0
        self.repeated_bytes = 0
        self.results = 0
        self.errors = 0
        self.seen = set()
        self.identities = set()
        self.compactions = 0

    def result(self, content, error=False):
        raw = json.dumps(content, ensure_ascii=False).encode()
        fingerprint = hashlib.sha256(raw).digest()
        self.results += 1
        self.output_bytes += len(raw)
        if fingerprint in self.seen:
            self.repeated_bytes += len(raw)
        self.seen.add(fingerprint)
        self.errors += int(error is True)

    def observe(self, row, provider):
        payload = row.get("payload", {}) if provider == "codex" else row
        if not isinstance(payload, dict):
            return
        kind = row.get("type")
        if kind == "compacted" or row.get("subtype") == "compact_boundary":
            self.compactions += 1
        if provider == "codex":
            if kind != "response_item":
                return
            typ = payload.get("type")
            key = (typ, payload.get("call_id"))
            if key[1] and key in self.identities:
                return
            if key[1]:
                self.identities.add(key)
            if typ in ("function_call", "custom_tool_call"):
                self.tools[label(payload.get("name"))] += 1
            elif typ in ("function_call_output", "custom_tool_call_output"):
                self.result(payload.get("output", ""))
        else:
            message = row.get("message", {})
            blocks = message.get("content", []) if isinstance(message, dict) else []
            if not isinstance(blocks, list):
                return
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                typ = block.get("type")
                key = (typ, block.get("id") or block.get("tool_use_id"))
                if key[1] and key in self.identities:
                    continue
                if key[1]:
                    self.identities.add(key)
                if typ == "tool_use":
                    self.tools[label(block.get("name"))] += 1
                elif typ == "tool_result":
                    self.result(block.get("content", ""), block.get("is_error"))

    def report(self):
        return {"tool_calls": dict(self.tools.most_common(12)), "tool_results": self.results,
                "tool_result_bytes_proxy": self.output_bytes,
                "identical_result_bytes_proxy": self.repeated_bytes,
                "explicit_tool_errors": self.errors, "compactions_observed": self.compactions}


def collect(path, provider, session_id, source_label):
    warnings, records, legacy = set(), {}, []
    activity = Activity()
    identity_seen = False
    model, version = "unknown", "unknown"
    duplicates = 0
    last_thread_total = None
    modern_seen = False
    for line_no, row in read_rows(path, warnings):
        kind = row.get("type")
        payload = row.get("payload", {})
        payload = payload if isinstance(payload, dict) else {}
        if provider == "codex":
            if kind == "session_meta":
                if payload.get("id") != session_id:
                    raise AnalysisError("session_identity_mismatch")
                identity_seen = True
                version = label(payload.get("cli_version"))
                if payload.get("forked_from_id") or payload.get("forked_from"):
                    warnings.add("fork_history_requires_attribution")
            if kind == "turn_context":
                model = label(payload.get("model"))
            if kind == "event_msg" and payload.get("type") == "token_count":
                info = payload.get("info")
                if isinstance(info, dict) and isinstance(info.get("total_token_usage"), dict):
                    legacy.append((line_no, row.get("timestamp"), model, info["total_token_usage"]))
            if kind != "token_usage_record":
                activity.observe(row, provider)
                continue
            if payload.get("thread_id") != session_id:
                warnings.add("foreign_thread_usage_excluded")
                continue
            modern_seen = True
            key = payload.get("response_id")
            usage = payload.get("usage")
            last_thread_total = payload.get("thread_token_usage")
        else:
            sid = row.get("sessionId")
            if sid is not None:
                if sid != session_id:
                    raise AnalysisError("session_identity_mismatch")
                identity_seen = True
            version = label(row.get("version")) if row.get("version") else version
            activity.observe(row, provider)
            message = row.get("message", {})
            if not isinstance(message, dict) or not isinstance(message.get("usage"), dict):
                continue
            if sid is None:
                warnings.add("usage_without_session_id_excluded")
                continue
            usage = message["usage"]
            key = [message.get("id"), row.get("requestId")]
            if not key[0]:
                key = None
            elif not key[1]:
                warnings.add("request_id_missing_message_id_fallback")
            model = label(message.get("model"))
        if not key or not isinstance(usage, dict):
            warnings.add("unidentifiable_usage_excluded")
            continue
        tokens = normalize(usage, provider)
        if tokens["input_tokens"] is None or tokens["output_tokens"] is None:
            warnings.add("required_usage_fields_missing")
        if any(value is None for value in tokens.values()):
            warnings.add("usage_breakdown_incomplete")
        if provider == "codex" and "total_tokens" in usage and number(usage.get("total_tokens")) != tokens["total_tokens"]:
            warnings.add("reported_total_mismatch")
        if (tokens["reasoning_output_tokens"] is not None and tokens["output_tokens"] is not None
                and tokens["reasoning_output_tokens"] > tokens["output_tokens"]):
            warnings.add("reasoning_exceeds_output")
        if provider == "codex" and tokens["cached_input_tokens"] is not None and tokens["uncached_input_tokens"] is None:
            warnings.add("invalid_cache_counters")
        fingerprint = digest([source_label, key])
        if fingerprint in records:
            duplicates += 1
            if records[fingerprint]["tokens"] != tokens:
                warnings.add("usage_revision_latest_selected")
        records[fingerprint] = {"key": fingerprint, "line": line_no, "timestamp": row.get("timestamp"),
                                "model": model, "tokens": tokens, "source": source_label}
    if not identity_seen:
        raise AnalysisError("session_identity_unverified")
    if provider == "codex" and not modern_seen:
        warnings.add("legacy_cumulative_adapter")
        previous = {key: 0 for key in FIELDS}
        for line_no, timestamp, model, usage in legacy:
            current = normalize(usage, provider)
            if current == previous:
                duplicates += 1
                continue
            if any(current[k] is not None and previous[k] is not None and current[k] < previous[k]
                   for k in FIELDS):
                warnings.add("counter_reset_totals_are_partial")
                previous = current
                continue
            tokens = {k: subtract(current[k], previous[k]) for k in FIELDS}
            key = digest([source_label, line_no, current])
            records[key] = {"key": key, "line": line_no, "timestamp": timestamp,
                            "model": model, "tokens": tokens, "source": source_label}
            previous = current
    rows = list(records.values())
    if not rows:
        warnings.add("usage_unavailable")
    if isinstance(last_thread_total, dict):
        reported = normalize(last_thread_total, provider)
        observed = summed(rows)
        if any(reported[k] != observed[k] for k in ("input_tokens", "output_tokens")):
            warnings.add("thread_total_differs_from_attributed_records")
    return {"source": source_label, "transcript_name": label(path.name),
            "version": version, "requests_observed": len(rows),
            "duplicates_removed": duplicates, "tokens": summed(rows),
            "warnings": sorted(warnings), "activity": activity.report()}, rows


def findings(sources, rows):
    result = []
    for source in sources:
        evidence = source["activity"]
        sid = source["source"]
        if evidence["identical_result_bytes_proxy"]:
            result.append({"source": sid, "fact": "identical_tool_output_observed",
                           "evidence_bytes_proxy": evidence["identical_result_bytes_proxy"],
                           "hypothesis": "redundant_reads_or_repeated_checks", "confidence": "medium",
                           "action": "reuse_unchanged_evidence; retain_required_checks"})
        if evidence["tool_result_bytes_proxy"] >= 20000:
            result.append({"source": sid, "fact": "large_tool_output_observed",
                           "evidence_bytes_proxy": evidence["tool_result_bytes_proxy"],
                           "hypothesis": "tool_output_increases_later_input", "confidence": "medium",
                           "action": "filter_locally_and_return_relevant_excerpts"})
        if evidence["explicit_tool_errors"]:
            result.append({"source": sid, "fact": "tool_errors_observed",
                           "count": evidence["explicit_tool_errors"], "hypothesis": "retry_overhead",
                           "confidence": "low", "action": "inspect_failed_step_before_retry"})
    return result[:12]


def build_report(provider, session_id, root, path, include_children=False):
    files = [(path, session_id, "main")]
    if include_children:
        children = discover_children(provider, root, path, session_id)
        if len(children) >= MAX_FILES:
            raise AnalysisError("child_limit")
        files.extend((p, sid, "child-" + digest(str(p.resolve()))[:12]) for p, sid in children)
    if sum(p.stat().st_size for p, _, _ in files) > MAX_BYTES:
        raise AnalysisError("scope_too_large: use main scope or selected transcripts")
    sources, rows = [], []
    for p, sid, source_label in files:
        source, entries = collect(p, provider, sid, source_label)
        sources.append(source)
        rows.extend(entries)
    groups = {}
    for entry in rows:
        groups.setdefault(entry["model"], []).append(entry)
    latest = next((r for r in reversed(rows) if r["source"] == "main"), None)
    report = {"schema_version": 1, "provider": provider, "session_id": session_id,
              "target": digest(str(path.resolve())),
              "snapshot_at": datetime.now(timezone.utc).isoformat(),
              "scope": "local_family" if include_children else "main_only",
              "coverage": "observed_local_records_only", "tokens": summed(rows),
              "measurement_status": "qualified" if any(s["warnings"] for s in sources) else "recorded",
              "sources": sources, "by_model": {m: summed(v) for m, v in groups.items()},
              "latest_main_request": latest,
              "largest_requests": sorted(rows, key=lambda r: r["tokens"]["total_tokens"] or -1,
                                         reverse=True)[:5],
              "findings": findings(sources, rows),
              "limits": ["not_billing_or_plan_limit", "bytes_are_not_tokens",
                         "no_exact_file_or_tool_token_attribution", "pending_requests_not_included",
                         "unlinked_or_remote_agents_not_included"]}
    return report, rows


def compare(baseline, report, rows):
    for key in ("schema_version", "provider", "session_id", "scope", "target"):
        if baseline.get(key) != report.get(key):
            raise AnalysisError("baseline_scope_mismatch")
    if baseline.get("measurement_status") != "recorded" or report.get("measurement_status") != "recorded":
        raise AnalysisError("baseline_or_current_measurement_qualified: inspect warnings before comparison")
    old = baseline.get("ledger")
    if not isinstance(old, dict):
        raise AnalysisError("baseline_ledger_missing")
    now = {row["key"]: row["tokens"] for row in rows}
    if any(key not in now or now[key] != tokens for key, tokens in old.items()):
        raise AnalysisError("baseline_history_changed: no reliable before_after_delta")
    added = [r for r in rows if r["key"] not in old]
    return {"requests_added": len(added),
            "tokens": summed(added) if added else {key: 0 for key in FIELDS},
            "interpretation": "observed_since_baseline_including_diagnostic_overhead; not_proven_savings"}


def save_snapshot(path, report, rows):
    data = {key: report[key] for key in ("schema_version", "provider", "session_id", "scope", "snapshot_at",
                                       "measurement_status", "target")}
    data["ledger"] = {r["key"]: r["tokens"] for r in rows}
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(Path(path).expanduser(), flags, 0o600)
        with os.fdopen(fd, "w") as stream:
            json.dump(data, stream, ensure_ascii=False)
            stream.write("\n")
    except OSError:
        raise AnalysisError("snapshot_not_written: choose a new file in an existing private directory") from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", required=True, choices=("codex", "claude"))
    parser.add_argument("--session-id")
    parser.add_argument("--log", help="explicit transcript; session identity is still verified")
    parser.add_argument("--root", help="sessions/ or projects/ directory")
    parser.add_argument("--include-children", action="store_true")
    parser.add_argument("--baseline", help="compare against a previous --save-snapshot")
    parser.add_argument("--save-snapshot", help="create a new private counters-only snapshot; no overwrite")
    args = parser.parse_args()
    try:
        env_key = "CODEX_THREAD_ID" if args.provider == "codex" else "CLAUDE_SESSION_ID"
        session_id = args.session_id or os.environ.get(env_key)
        if not session_id or not ID.fullmatch(session_id):
            raise AnalysisError("session_id_required: use the current runtime ID, never the latest log")
        home_key = "CODEX_HOME" if args.provider == "codex" else "CLAUDE_CONFIG_DIR"
        home = Path(os.environ.get(home_key, str(Path.home() / ("." + args.provider)))).expanduser()
        root = Path(args.root).expanduser() if args.root else home / ("sessions" if args.provider == "codex" else "projects")
        path = resolve_log(args.provider, session_id, root, args.log)
        report, rows = build_report(args.provider, session_id, root, path, args.include_children)
        if args.baseline:
            baseline_path = Path(args.baseline).expanduser()
            if baseline_path.stat().st_size > MAX_BYTES:
                raise AnalysisError("baseline_too_large")
            baseline = json.loads(baseline_path.read_text())
            if not isinstance(baseline, dict):
                raise AnalysisError("baseline_invalid")
            report["since_baseline"] = compare(baseline, report, rows)
        if args.save_snapshot:
            save_snapshot(args.save_snapshot, report, rows)
        print(json.dumps(report, ensure_ascii=False, separators=(",", ":")))
        return 0
    except (AnalysisError, OSError, ValueError, TypeError) as exc:
        message = str(exc) if isinstance(exc, AnalysisError) else "invalid_or_unreadable_input"
        print(json.dumps({"error": message}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
