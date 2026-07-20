#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


SOURCE_ID = "mattpocock-skills"
SOURCE_REVISION = "9603c1cc8118d08bc1b3bf34cf714f62178dea3b"
SOURCE_SKILL_COUNT = 41
DECISION_COUNTS = {
    "keep": 10,
    "adapt": 24,
    "replace": 1,
    "adopt": 2,
    "retire": 4,
}
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


def default_claude_root(script_root: Path) -> Path:
    if script_root.name in {".claude", ".claude-global"}:
        return script_root
    sibling = script_root.parent / ".claude-global"
    return sibling if sibling.is_dir() else Path.home() / ".claude"


def default_codex_root(script_root: Path) -> Path:
    if script_root.name not in {".claude", ".claude-global"}:
        return script_root
    sibling = script_root.parent / ".codex"
    return sibling if sibling.is_dir() else Path.home() / ".codex"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    script_root = Path(__file__).resolve().parents[1]
    parser.add_argument("--codex-root", type=Path, default=default_codex_root(script_root))
    parser.add_argument(
        "--claude-root",
        type=Path,
        default=default_claude_root(script_root),
    )
    parser.add_argument(
        "--require-governance-audit",
        action="store_true",
        help="also require the complete governance estate audit to be clean",
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


def check_catalog(root: Path, label: str) -> list[str]:
    failures: list[str] = []
    catalog = root / "skills" / "skill-governance" / "catalog.lock.json"
    try:
        data = json.loads(catalog.read_text(encoding="utf-8"))
        source = data["sources"][SOURCE_ID]
    except (OSError, KeyError, json.JSONDecodeError) as error:
        return [f"{label}: cannot read Matt Skill catalog source: {error}"]

    if source.get("revision") != SOURCE_REVISION:
        failures.append(f"{label}: Matt Skill catalog revision differs")
    skills = source.get("skills")
    if not isinstance(skills, list) or len(skills) != SOURCE_SKILL_COUNT:
        count = len(skills) if isinstance(skills, list) else "invalid"
        failures.append(
            f"{label}: Matt Skill catalog must contain {SOURCE_SKILL_COUNT} skills, got {count}"
        )
    elif any(not isinstance(skill, dict) for skill in skills):
        failures.append(f"{label}: Matt Skill catalog contains an invalid entry")
    elif len({skill.get("name") for skill in skills}) != SOURCE_SKILL_COUNT:
        failures.append(f"{label}: Matt Skill catalog contains duplicate names")
    return failures


def numbered_table_rows(text: str) -> list[list[str]]:
    return [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in text.splitlines()
        if re.match(r"^\|\s*\d+\s*\|", line)
    ]


def check_decision_map(root: Path, label: str) -> list[str]:
    failures: list[str] = []
    catalog_path = root / "skills" / "skill-governance" / "catalog.lock.json"
    decision_path = root / "context" / "matt-skill-adoption-map.md"
    try:
        source = json.loads(catalog_path.read_text(encoding="utf-8"))["sources"][SOURCE_ID]
        decision_text = decision_path.read_text(encoding="utf-8")
    except (OSError, KeyError, json.JSONDecodeError) as error:
        return [f"{label}: cannot read Matt Skill decision coverage: {error}"]

    rows = numbered_table_rows(decision_text)
    if len(rows) != SOURCE_SKILL_COUNT:
        failures.append(
            f"{label}: decision map must contain {SOURCE_SKILL_COUNT} rows, got {len(rows)}"
        )
        return failures
    if any(len(row) < 6 for row in rows):
        return [f"{label}: decision map contains a malformed row"]

    skills = source.get("skills")
    if not isinstance(skills, list) or any(not isinstance(skill, dict) for skill in skills):
        return [f"{label}: Matt Skill catalog contains an invalid entry"]
    catalog_names = {skill.get("name") for skill in skills}
    decision_names = [row[1].strip("`") for row in rows]
    if len(decision_names) != len(set(decision_names)):
        failures.append(f"{label}: decision map contains duplicate upstream names")
    if set(decision_names) != catalog_names:
        failures.append(f"{label}: decision map does not cover the pinned catalog exactly")

    observed_counts = {
        decision: sum(row[3] == decision for row in rows)
        for decision in DECISION_COUNTS
    }
    if observed_counts != DECISION_COUNTS:
        failures.append(
            f"{label}: decision counts differ: expected {DECISION_COUNTS}, got {observed_counts}"
        )
    if SOURCE_REVISION not in decision_text:
        failures.append(f"{label}: decision map does not name the pinned revision")
    return failures


def check_governance_audit(root: Path) -> list[str]:
    script = root / "skills" / "skill-governance" / "scripts" / "governance.py"
    completed = subprocess.run(
        [sys.executable, "-B", str(script), "audit", "--json"],
        check=False,
        capture_output=True,
        text=True,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        return [f"governance audit did not return JSON: {error}"]
    blocking = [
        finding.get("code", "unknown")
        for finding in payload.get("findings", [])
        if finding.get("severity") == "BLOCKING"
    ]
    if completed.returncode != 0 or payload.get("status") != "ok":
        return [f"governance audit is not clean: {', '.join(blocking) or payload.get('status')}"]
    return []


def compare_scoped_files(codex: Path, claude: Path) -> list[str]:
    failures: list[str] = []
    relative_files: set[Path] = set()
    paired_directories = [
        Path("skills") / name
        for name in sorted(set(ENTRY_SKILLS) | IN_PROGRESS_SKILLS)
    ]
    for relative_dir in paired_directories:
        directory = codex / relative_dir
        relative_files.update(
            path.relative_to(codex)
            for path in directory.rglob("*")
            if path.is_file()
        )
    relative_files.update({
        Path("context/matt-skill-adoption-map.md"),
        Path("context/matt-skill-user-scope-promotion-plan.md"),
        Path("scripts/validate-matt-skill-integration.py"),
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
        *check_catalog(codex, "codex"),
        *check_catalog(claude, "claude"),
        *check_decision_map(codex, "codex"),
        *check_decision_map(claude, "claude"),
        *compare_scoped_files(codex, claude),
    ]
    if args.require_governance_audit:
        failures.extend(check_governance_audit(codex))
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    audit = ", governance audit=clean" if args.require_governance_audit else ""
    print(
        "PASS: Matt Skill decisions=41, entries=5, in-progress=2, "
        f"retired=4, paired surfaces match{audit}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
