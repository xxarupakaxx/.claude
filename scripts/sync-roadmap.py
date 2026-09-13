#!/usr/bin/env python3
"""Synchronize a task Roadmap from its recorded workflow route."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path


ELIGIBLE_ROUTES = {"explicit-roadmap", "roadmap"}
ROUTE_PATTERN = re.compile(
    r"roadmap_route:\s*(explicit-roadmap|roadmap|log-only)(?=[：:\s`]|$)"
)
PHASE_STATES = {
    "2": "active",
    "3": "active",
    "4": "verifying",
    "5": "completed",
}
DELEGATION_DECISION_FIELDS = (
    "decision", "role", "gate", "decision_unit",
    "passed_conditions", "failed_conditions", "local_first_evidence", "reason",
    "write_scope", "acceptance", "supersedes", "lead_retains",
)
DELEGATION_DECISION_ENUMS = {
    "decision": {"worker", "lead", "N/A (read-only)"},
    "role": {"worker", "implementer", "N/A"},
    "gate": {"PASS", "FAIL", "N/A"},
}
DELEGATION_DECISION_PATTERN = re.compile(r"(?ms)^## .+ - Delegation Decision[^\n]*\n(.*?)(?=^## |\Z)")
DECISION_FIELD_PATTERN = re.compile(r"^\s*-\s*([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$")


def valid_task_dir(path: Path, memory_root: Path) -> bool:
    try:
        relative = path.resolve().relative_to(memory_root.resolve())
    except ValueError:
        return False
    return bool(relative.parts) and relative.parts[0] not in {".", ".."}


def validate_task_metadata(task_dir: Path, workspace_root: Path) -> str | None:
    metadata_path = task_dir / "task-meta.json"
    if not metadata_path.is_file():
        return None
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "task_metadata_invalid"
    expected = str(workspace_root.resolve())
    for field in ("project_path", "worktree_path"):
        value = metadata.get(field)
        if value is not None and str(Path(str(value)).resolve()) != expected:
            return f"task_metadata_{field}_mismatch"
    return None


def file_fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_fingerprints(task_dir: Path, route: str) -> dict[str, str]:
    names = ["05_log.md"]
    if route in ELIGIBLE_ROUTES:
        names.append("30_plan.md")
    if (task_dir / "task-meta.json").is_file():
        names.append("task-meta.json")
    return {
        name: file_fingerprint(task_dir / name)
        for name in names
        if (task_dir / name).is_file()
    }


def detect_route(log_text: str) -> str | None:
    matches = ROUTE_PATTERN.findall(log_text)
    return matches[-1] if matches else None


def validate_delegation_decision(log_text: str) -> tuple[list[str] | None, list[str]]:
    matches = list(DELEGATION_DECISION_PATTERN.finditer(log_text))
    if not matches:
        return None, []
    fields: dict[str, str] = {}
    for line in matches[-1].group(1).splitlines():
        match = DECISION_FIELD_PATTERN.match(line)
        if match:
            fields[match.group(1)] = match.group(2).strip()
    missing = [field for field in DELEGATION_DECISION_FIELDS if not fields.get(field)]
    invalid = [
        field for field, choices in DELEGATION_DECISION_ENUMS.items()
        if fields.get(field) and fields[field] not in choices
    ]
    return missing, invalid


def roadmap_command(
    task_dir: Path,
    generator: Path,
    phase: str,
    open_requested: bool,
    headless: bool,
) -> list[str]:
    command = [
        sys.executable,
        str(generator),
        str(task_dir),
        "--json",
        "--task-state",
        PHASE_STATES[phase],
    ]
    if open_requested and not headless:
        command.append("--open")
    return command


def synchronize(
    task_dir: Path,
    generator: Path,
    phase: str,
    workspace_root: Path,
    run_id: str,
    memory_root: Path | None = None,
    open_requested: bool = False,
    headless: bool = False,
    dry_run: bool = False,
) -> tuple[int, dict[str, object]]:
    task_dir = task_dir.resolve()
    workspace_root = workspace_root.resolve()
    if not re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", run_id):
        return 2, {"status": "failed", "reason": "run_id_invalid"}
    selected_memory_root = (memory_root or workspace_root / ".local" / "memory").resolve()
    if not valid_task_dir(task_dir, selected_memory_root):
        return 2, {
            "status": "failed",
            "reason": "task_dir_outside_memory",
            "path": str(task_dir),
            "memory_root": str(selected_memory_root),
        }
    metadata_error = validate_task_metadata(task_dir, workspace_root)
    if metadata_error:
        return 2, {"status": "failed", "reason": metadata_error}
    log_path = task_dir / "05_log.md"
    if not log_path.is_file():
        return 2, {"status": "failed", "reason": "log_missing", "path": str(log_path)}
    log_text = log_path.read_text(encoding="utf-8")
    route = detect_route(log_text)
    if route is None:
        return 2, {"status": "failed", "reason": "route_missing"}
    if phase == "2":
        missing_fields, invalid_fields = validate_delegation_decision(log_text)
        if missing_fields is None:
            return 2, {"status": "failed", "route": route, "reason": "delegation_decision_missing"}
        if missing_fields or invalid_fields:
            return 2, {
                "status": "failed",
                "route": route,
                "reason": "delegation_decision_invalid",
                **({"missing_fields": missing_fields} if missing_fields else {}),
                **({"invalid_fields": invalid_fields} if invalid_fields else {}),
            }
    if route == "log-only":
        return 0, {
            "status": "skipped",
            "route": route,
            "phase": phase,
            "task_dir": str(task_dir),
            "workspace_root": str(workspace_root),
            "run_id": run_id,
            "generated_at_unix": time.time(),
            "source_fingerprints": source_fingerprints(task_dir, route),
            "reason": "log_only",
        }
    plan_path = task_dir / "30_plan.md"
    if not plan_path.is_file():
        return 2, {
            "status": "failed",
            "route": route,
            "reason": "plan_missing",
            "path": str(plan_path),
        }
    if not generator.is_file():
        return 2, {
            "status": "failed",
            "route": route,
            "reason": "generator_missing",
            "path": str(generator),
        }

    command = roadmap_command(
        task_dir, generator.resolve(), phase, open_requested, headless
    )
    open_status = "requested" if open_requested and not headless else "not_requested"
    if open_requested and headless:
        open_status = "suppressed_headless"
    if dry_run:
        return 0, {
            "status": "dry_run",
            "route": route,
            "phase": phase,
            "task_dir": str(task_dir),
            "workspace_root": str(workspace_root),
            "run_id": run_id,
            "open_status": open_status,
            "command": command,
        }
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        return completed.returncode, {
            "status": "failed",
            "route": route,
            "reason": "generator_failed",
            "stderr": completed.stderr.strip(),
        }
    artifacts = (task_dir / "roadmap.html", task_dir / "roadmap-snapshot.json")
    missing = [str(path) for path in artifacts if not path.is_file()]
    if missing:
        return 2, {
            "status": "failed",
            "route": route,
            "reason": "roadmap_artifact_missing",
            "missing": missing,
        }
    metadata_error = validate_task_metadata(task_dir, workspace_root)
    if metadata_error:
        return 2, {"status": "failed", "reason": metadata_error}
    return 0, {
        "status": "synchronized",
        "route": route,
        "phase": phase,
        "task_dir": str(task_dir),
        "open_status": open_status,
        "roadmap": str(task_dir / "roadmap.html"),
        "workspace_root": str(workspace_root),
        "run_id": run_id,
        "generated_at_unix": time.time(),
        "source_fingerprints": source_fingerprints(task_dir, route),
        "artifact_fingerprints": {
            path.name: file_fingerprint(path) for path in artifacts
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_dir", type=Path)
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--memory-root", type=Path)
    parser.add_argument("--phase", choices=sorted(PHASE_STATES), required=True)
    parser.add_argument("--open", action="store_true", dest="open_requested")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--generator",
        type=Path,
        default=Path(__file__).with_name("generate-roadmap-view.py"),
    )
    args = parser.parse_args()
    code, result = synchronize(
        args.task_dir,
        args.generator,
        args.phase,
        args.workspace_root,
        args.run_id,
        memory_root=args.memory_root,
        open_requested=args.open_requested,
        headless=args.headless,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
