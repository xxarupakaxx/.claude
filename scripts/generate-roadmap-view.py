#!/usr/bin/env python3
from __future__ import annotations

import argparse
import functools
import hashlib
import http.server
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
]

OUTPUT_NAMES = {"roadmap.html", "roadmap-snapshot.json"}
EMBEDDED_SNAPSHOT_RE = re.compile(
    r'<script\b(?=[^>]*\bid=["\']embedded-snapshot["\'])[^>]*>(.*?)</script\s*>',
    re.IGNORECASE | re.DOTALL,
)


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


def build_fingerprint(files: dict[str, str], artifacts: list[dict[str, object]]) -> str:
    payload = {
        "files": files,
        "artifacts": artifacts,
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def infer_title(files: dict[str, str], task_dir: Path) -> str:
    for name in ("30_plan.md", "00_spec.md", "05_log.md"):
        text = files.get(name, "")
        for line in text.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                if title:
                    return title
    return task_dir.name.replace("_", " ")


def build_snapshot(task_dir: Path, output: Path | None = None) -> dict[str, object]:
    files, sources = read_files(task_dir)
    if not files:
        raise ValueError(f"no roadmap source files found in {task_dir}")
    artifacts = collect_artifacts(task_dir, output)
    return {
        "version": 1,
        "title": infer_title(files, task_dir),
        "taskDir": str(task_dir),
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "fingerprint": build_fingerprint(files, artifacts),
        "files": files,
        "sources": sources,
        "artifacts": artifacts,
    }


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


def write_outputs(task_dir: Path, output: Path, write_json: bool) -> dict[str, object]:
    json_path = output.with_name("roadmap-snapshot.json")
    snapshot = build_snapshot(task_dir, output=output)
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


def watch_outputs(task_dir: Path, output: Path, interval: float, stop: threading.Event) -> None:
    while not stop.is_set():
        try:
            write_outputs(task_dir, output, write_json=True)
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
        description="Generate a browser-readable roadmap.html from a Codex task memory directory."
    )
    parser.add_argument("task_dir", help="Path to .local/memory/<task>")
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
        "--open",
        action="store_true",
        help="Open the generated file or local server URL in the default browser.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    task_dir = Path(args.task_dir).expanduser().resolve()
    if not task_dir.is_dir():
        print(f"task_dir is not a directory: {task_dir}", file=sys.stderr)
        return 2

    output = Path(args.output).expanduser().resolve() if args.output else task_dir / "roadmap.html"
    write_json = args.json or args.serve or args.watch
    write_outputs(task_dir, output, write_json=write_json)

    print(output)
    if args.serve:
        stop = threading.Event()
        thread = None
        if args.watch:
            thread = threading.Thread(
                target=watch_outputs,
                args=(task_dir, output, args.interval, stop),
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
            watch_outputs(task_dir, output, args.interval, stop)
        except KeyboardInterrupt:
            print("\nstopping roadmap watch", file=sys.stderr)
        return 0

    if args.open:
        webbrowser.open(output.as_uri())

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
