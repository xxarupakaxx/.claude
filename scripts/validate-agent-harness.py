#!/usr/bin/env python3
"""Validate the stable entrypoint and knowledge artifact contracts of ~/.claude.

.codex/scripts/validate-agent-harness.py の user-scope Claude Code 版。
codex 固有の TOML role、config.toml、global mirror、delivery lifecycle
（gpt-5.6 roster / Work Packet / PRD）契約は .claude に対応物がないため移していない。
移したのは runtime に依存しない4つの契約である。

1. entrypoint: CLAUDE.md が薄い入口のままか
2. SSoT reachability: 正本mapが指す先が実在するか
3. role definition: agents/*.md の frontmatter が最低限を満たすか
4. knowledge artifact: memories/ と solutions/ の frontmatter 契約
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date, datetime
from pathlib import Path

# CLAUDE.md は 2026-08-28 時点で 129 行 / 12.4KB。
# 現状を追認せず、かつ肥大化を検出できる幅としてソフト目標を置く。
ENTRYPOINT_MAX_LINES = 150
ENTRYPOINT_MAX_BYTES = 24 * 1024

ENTRYPOINT = "CLAUDE.md"

# CLAUDE.md の「正本map」が指す先。CLAUDE.md 内に言及があり、かつ実在すること。
REQUIRED_REFERENCES = (
    "context/workflow-rules.md",
    "context/agent-team-routing.md",
    "context/memory-file-formats.md",
    "context/codemap.md",
    "context/team-run.md",
    "context/graph-engineering.md",
    "rules/model-routing.md",
    "rules/complexity-budget.md",
    "rules/adr-criteria.md",
    "rules/security.md",
    "rules/common-git-workflow.md",
    "rules/code-review-philosophy.md",
    "skills/viewing-plans/SKILL.md",
)

PROJECT_TEMPLATE = "templates/project/CLAUDE.md"
PROJECT_TEMPLATE_MARKERS = ("MEMORY_DIR=", "BASE_BRANCH=", "## 品質チェック")

# memories/ と solutions/ の frontmatter 契約（context/memory-file-formats.md）。
# 両者はスキーマが違う。memories は索引層、solutions は構造化ソリューションDB。
MEMORIES_REQUIRED_KEYS = ("summary", "created")
SOLUTIONS_REQUIRED_KEYS = ("title", "created")
# solutions は問題解決型と技術知見型の2変種を持つ（compounding-knowledge SKILL.md）。
SOLUTIONS_SUMMARY_VARIANTS = (
    ("root_cause", "solution_summary"),
    ("learning_type", "discovery_summary"),
)
KNOWLEDGE_PHASES = {
    "preparation",
    "investigation",
    "planning",
    "implementation",
    "quality-check",
    "reporting",
    "compound",
}

FRONTMATTER_LINE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$")


def parse_frontmatter(path: Path) -> dict[str, str]:
    """先頭の YAML frontmatter を単純な key: value として読む。

    ネストした値（related のリスト等）は key のみ記録し、値は空文字にする。
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    values: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return values
        match = FRONTMATTER_LINE.match(line)
        if match:
            values[match.group(1)] = match.group(2).strip().strip("\"'")
    return {}


def valid_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return False
    return True


def validate_entrypoint(repo_root: Path) -> list[str]:
    errors: list[str] = []
    entry = repo_root / ENTRYPOINT
    if not entry.is_file():
        return [f"missing entrypoint: {ENTRYPOINT}"]

    text = entry.read_text(encoding="utf-8")
    line_count = len(text.splitlines())
    if line_count > ENTRYPOINT_MAX_LINES:
        errors.append(f"{ENTRYPOINT} exceeds {ENTRYPOINT_MAX_LINES} lines: {line_count}")
    byte_count = len(text.encode("utf-8"))
    if byte_count > ENTRYPOINT_MAX_BYTES:
        errors.append(f"{ENTRYPOINT} exceeds {ENTRYPOINT_MAX_BYTES} bytes: {byte_count}")

    for reference in REQUIRED_REFERENCES:
        if reference not in text:
            errors.append(f"{ENTRYPOINT} missing SSoT reference: {reference}")
        if not (repo_root / reference).is_file():
            errors.append(f"missing SSoT target: {reference}")

    template = repo_root / PROJECT_TEMPLATE
    if not template.is_file():
        errors.append(f"missing project entrypoint template: {PROJECT_TEMPLATE}")
    else:
        template_text = template.read_text(encoding="utf-8")
        for marker in PROJECT_TEMPLATE_MARKERS:
            if marker not in template_text:
                errors.append(f"project template missing {marker}: {PROJECT_TEMPLATE}")

    return errors


def validate_roles(repo_root: Path) -> list[str]:
    """agents/*.md の frontmatter 契約。name はファイル名と一致させる。"""
    errors: list[str] = []
    agents_dir = repo_root / "agents"
    if not agents_dir.is_dir():
        return ["missing agents directory"]

    definitions = sorted(agents_dir.glob("*.md"))
    if not definitions:
        return ["agents directory has no role definition"]

    for path in definitions:
        relative = path.relative_to(repo_root).as_posix()
        values = parse_frontmatter(path)
        if not values:
            errors.append(f"{relative}: missing YAML frontmatter")
            continue
        for key in ("name", "description"):
            if not values.get(key):
                errors.append(f"{relative}: missing frontmatter key: {key}")
        name = values.get("name")
        if name and name != path.stem:
            errors.append(f"{relative}: frontmatter name '{name}' does not match filename")
    return errors


def knowledge_schema(path: Path) -> str:
    """パスから memories / solutions のどちらのスキーマかを決める。"""
    for part in reversed(path.parts):
        if part == "solutions":
            return "solutions"
        if part == "memories":
            return "memories"
    return "memories"


def validate_knowledge_artifact(path: Path, relative: str) -> list[str]:
    errors: list[str] = []
    values = parse_frontmatter(path)
    if not values:
        return [f"{relative}: missing YAML frontmatter"]

    schema = knowledge_schema(path)
    required = SOLUTIONS_REQUIRED_KEYS if schema == "solutions" else MEMORIES_REQUIRED_KEYS
    for key in required:
        if not values.get(key):
            errors.append(f"{relative}: missing frontmatter key: {key} ({schema} schema)")
    if schema == "solutions" and not any(
        all(values.get(key) for key in variant) for variant in SOLUTIONS_SUMMARY_VARIANTS
    ):
        expected = " または ".join(" + ".join(variant) for variant in SOLUTIONS_SUMMARY_VARIANTS)
        errors.append(f"{relative}: solutions frontmatter needs {expected}")

    created = values.get("created")
    if created and not valid_date(created):
        errors.append(f"{relative}: invalid created: {created}")
    phases = values.get("phases")
    if phases:
        listed = [item.strip() for item in phases.strip("[]").split(",") if item.strip()]
        unknown = [item for item in listed if item not in KNOWLEDGE_PHASES]
        if unknown:
            errors.append(f"{relative}: unknown phases: {', '.join(unknown)}")
    return errors


def validate_knowledge_dir(path: Path, repo_root: Path) -> list[str]:
    if not path.is_dir():
        return [f"knowledge directory not found: {path}"]
    errors: list[str] = []
    for artifact in sorted(path.rglob("*.md")):
        if artifact.name.upper() in {"README.MD", "INDEX.MD"}:
            continue
        try:
            relative = artifact.relative_to(repo_root).as_posix()
        except ValueError:
            relative = str(artifact)
        errors.extend(validate_knowledge_artifact(artifact, relative))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--knowledge-dir",
        type=Path,
        action="append",
        default=[],
        help="memories/ または solutions/ の実ディレクトリ（複数指定可）",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    errors = validate_entrypoint(repo_root)
    errors.extend(validate_roles(repo_root))
    for knowledge_dir in args.knowledge_dir:
        errors.extend(validate_knowledge_dir(knowledge_dir.resolve(), repo_root))

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    print("PASS: agent harness contracts are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
