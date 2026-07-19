#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ENTRY_SKILLS = {
    "wayfinder": "mapping-large-projects",
    "to-spec": "writing-specifications",
    "to-tickets": "creating-tracer-tickets",
    "implement": "implementing-work",
    "teach": "teaching-concepts",
}
IN_PROGRESS_SKILLS = {"batch-grill-me", "to-questionnaire"}
RETIRED_SKILLS = {
    "conducting-quality-assurance",
    "design-an-interface",
    "planning-refactors",
    "ubiquitous-language",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    script_root = Path(__file__).resolve().parents[1]
    parser.add_argument("--codex-root", type=Path, default=script_root)
    parser.add_argument(
        "--claude-root",
        type=Path,
        default=script_root.parent / ".claude-global",
    )
    return parser.parse_args()


def skill_name(text: str) -> str | None:
    match = re.search(r"(?m)^name:\s*([a-z0-9-]+)\s*$", text)
    return match.group(1) if match else None


def check_root(root: Path, label: str) -> list[str]:
    failures: list[str] = []
    for name, implementation in ENTRY_SKILLS.items():
        path = root / "skills" / name / "SKILL.md"
        if not path.is_file():
            failures.append(f"{label}: missing {path}")
            continue
        text = path.read_text(encoding="utf-8")
        if skill_name(text) != name:
            failures.append(f"{label}: wrong frontmatter name for {name}")
        if "disable-model-invocation: true" not in text:
            failures.append(f"{label}: {name} must be user-invoked")
        if implementation not in text:
            failures.append(f"{label}: {name} does not point to {implementation}")

    for name in IN_PROGRESS_SKILLS:
        path = root / "skills" / name / "SKILL.md"
        if not path.is_file():
            failures.append(f"{label}: missing {path}")
            continue
        text = path.read_text(encoding="utf-8")
        if skill_name(text) != name:
            failures.append(f"{label}: wrong frontmatter name for {name}")
        if "disable-model-invocation: true" not in text:
            failures.append(f"{label}: {name} must be user-invoked")
        if "Status: in-progress" not in text:
            failures.append(f"{label}: {name} must disclose in-progress status")

    questionnaire = root / "skills" / "to-questionnaire" / "SKILL.md"
    if questionnaire.is_file():
        text = questionnaire.read_text(encoding="utf-8")
        for phrase in ("local file", "送信、共有、tracker投稿は行いません"):
            if phrase not in text:
                failures.append(f"{label}: to-questionnaire missing boundary: {phrase}")

    for name in RETIRED_SKILLS:
        if (root / "skills" / name / "SKILL.md").exists():
            failures.append(f"{label}: retired skill still exists: {name}")

    routing = (root / "context" / "agent-team-routing.md").read_text(encoding="utf-8")
    for name in (*ENTRY_SKILLS, *IN_PROGRESS_SKILLS):
        if f"`{name}`" not in routing:
            failures.append(f"{label}: routing does not expose {name}")
    if "`modeling-domains`" not in routing:
        failures.append(f"{label}: routing does not expose ubiquitous-language replacement")

    architecture = (root / "skills" / "software-architecture" / "SKILL.md").read_text(encoding="utf-8")
    if "ubiquitous-language" in architecture or "modeling-domains" not in architecture:
        failures.append(f"{label}: software-architecture still points to retired ubiquitous-language")

    for relative in (
        "rules/adr-criteria.md",
        "skills/improving-architecture/SKILL.md",
        "skills/software-architecture/SKILL.md",
        "skills/tdd/SKILL.md",
        "skills/tdd/references/interface-design.md",
    ):
        if "design-an-interface" in (root / relative).read_text(encoding="utf-8"):
            failures.append(f"{label}: active reference still points to retired design-an-interface: {relative}")

    return failures


def numbered_table_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        if not re.match(r"^\|\s*\d+\s*\|", line):
            continue
        rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
    return rows


def check_project(root: Path) -> list[str]:
    failures: list[str] = []
    project = root / "projects" / "matt-skill-harness"
    inventory = project / "matt-skill-inventory.md"
    if not inventory.is_file():
        return [f"missing {inventory}"]

    rows = numbered_table_rows(inventory.read_text(encoding="utf-8"))
    if len(rows) != 41:
        failures.append(f"inventory must have 41 rows, got {len(rows)}")
    names = [row[1].strip("`") for row in rows]
    if len(names) != len(set(names)):
        failures.append("inventory contains duplicate upstream names")

    journal = (project / "team-journal.md").read_text(encoding="utf-8")
    outcome_rows = [
        line for line in journal.splitlines()
        if re.match(r"^\|\s*O-\d+\b", line)
    ]
    if len(outcome_rows) != 8:
        failures.append(f"Outcome Trace must have 8 outcomes, got {len(outcome_rows)}")
    for column in ("Human Review", "Objection", "State"):
        if column not in journal:
            failures.append(f"Outcome Trace missing column: {column}")
    if "## Revision Log" not in journal:
        failures.append("Revision Log missing")

    checkpoints = (project / "checkpoint.md").read_text(encoding="utf-8")
    acceptance_ids = set(re.findall(r"\bAC-\d+\b", checkpoints))
    if len(acceptance_ids) != 10:
        failures.append(f"Sprint Contract must have 10 acceptance ids, got {len(acceptance_ids)}")

    evals = project / "evals" / "skill-routing-cases.md"
    if not evals.is_file() or len(numbered_table_rows(evals.read_text(encoding="utf-8"))) < 10:
        failures.append("at least 10 routing eval cases are required")
    for relative in (
        "lessons/0001-reading-the-harness-roadmap.html",
        "reference/roadmap-reading-guide.html",
        "assets/lesson.css",
        "assets/lesson.js",
    ):
        if not (project / relative).is_file():
            failures.append(f"teaching workspace missing: {relative}")
    return failures


def compare_scoped_files(codex: Path, claude: Path) -> list[str]:
    failures: list[str] = []
    relative_files: set[Path] = set()
    paired_directories = [
        Path("projects/matt-skill-harness"),
        *(Path("skills") / name for name in sorted(set(ENTRY_SKILLS) | IN_PROGRESS_SKILLS)),
    ]
    for relative_dir in paired_directories:
        directory = codex / relative_dir
        relative_files.update(
            path.relative_to(codex)
            for path in directory.rglob("*")
            if path.is_file()
        )
    relative_files.update({
        Path("context/matt-skill-user-scope-promotion-plan.md"),
        Path("scripts/validate-matt-skill-harness.py"),
        Path("skills/skill-governance/catalog.lock.json"),
        Path("skills/skill-governance/estate.lock.json"),
        Path("skills/skill-governance/registry.lock.json"),
        Path("skills/skill-governance/registry.toml"),
        Path("skills/skill-governance/scripts/governance.py"),
        Path("skills/skill-governance/scripts/test_governance.py"),
        Path("tests/roadmap-viewer.test.mjs"),
        Path("tools/roadmap_viewer.html"),
    })
    for relative in sorted(relative_files):
        left = codex / relative
        right = claude / relative
        if not right.is_file():
            failures.append(f"claude missing paired file: {relative}")
        elif left.read_bytes() != right.read_bytes():
            failures.append(f"paired file differs: {relative}")
    return failures


def main() -> int:
    args = parse_args()
    codex = args.codex_root.resolve()
    claude = args.claude_root.resolve()
    failures = [
        *check_root(codex, "codex"),
        *check_root(claude, "claude"),
        *check_project(codex),
        *check_project(claude),
        *compare_scoped_files(codex, claude),
    ]
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("PASS: Matt Skill inventory=41, entries=5, in-progress=2, retired=4, paired surfaces match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
