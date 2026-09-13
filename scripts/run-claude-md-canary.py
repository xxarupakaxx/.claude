#!/usr/bin/env python3
"""Check that CLAUDE.md still reaches the instructions each representative task needs.

.codex/scripts/run-agents-md-canary.py の user-scope Claude Code 版。
CLAUDE.md を起点に参照グラフを BFS で辿り、到達できた文書の集合に対して
シナリオごとの必須マーカーが残っているかを判定する。

CLAUDE.md は「全 Agent が毎回守る不変条件と正本への導線だけを置く」薄い入口である。
入口を削るリファクタで導線が切れると、マーカーが到達不能になって FAIL する。

baseline revision を渡すと、その時点との比較（入口が痩せて到達性が落ちていない）も行う。
渡さない場合は現在の到達性だけを判定する回帰モードで動く。
"""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import subprocess
from collections import deque
from pathlib import Path

ENTRYPOINTS = ("CLAUDE.md",)
# CLAUDE.md 配下の正本ディレクトリ。ここで始まる参照は root 相対として解決する。
ROOT_RELATIVE_PREFIXES = (
    "agents/",
    "commands/",
    "context/",
    "hooks/",
    "rules/",
    "scripts/",
    "skills/",
    "templates/",
    "tools/",
    "workflows/",
)
REFERENCE_PATTERN = re.compile(r"`([A-Za-z0-9_./-]+\.(?:md|py|js|mjs))`")
MAX_SOURCES = 256

EXECUTION_CHECKS = {
    "harness_contract": ["python3", "scripts/validate-agent-harness.py"],
    "html_surface_contract": ["python3", "scripts/verify-html-surfaces.py"],
    "roadmap_adapter": [
        "python3", "-m", "unittest", "discover", "-s", "tests",
        "-p", "test_sync_roadmap.py",
    ],
}


def git_text(repo: Path, revision: str, relative: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{revision}:{relative}"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout if result.returncode == 0 else ""


def read_source(root: Path, relative: str, revision: str | None) -> str:
    if revision:
        return git_text(root, revision, relative)
    path = root / relative
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def normalize_reference(source: str, reference: str) -> str:
    if reference.startswith(ROOT_RELATIVE_PREFIXES):
        return reference
    # `..` を畳まないと同じ文書が別キーで二重に到達扱いになる。
    return posixpath.normpath(posixpath.join(posixpath.dirname(source), reference))


def reachable_sources(root: Path, revision: str | None) -> dict[str, str]:
    found: dict[str, str] = {}
    queue = deque(ENTRYPOINTS)
    while queue and len(found) < MAX_SOURCES:
        relative = queue.popleft()
        if relative in found:
            continue
        text = read_source(root, relative, revision)
        if not text:
            continue
        found[relative] = text
        for reference in REFERENCE_PATTERN.findall(text):
            normalized = normalize_reference(relative, reference)
            if normalized not in found:
                queue.append(normalized)
    return found


def evaluate(
    variant: str,
    sources: dict[str, str],
    scenarios: list[dict[str, object]],
    repetitions: int,
) -> list[dict[str, object]]:
    text = "\n".join(sources.values())
    trials: list[dict[str, object]] = []
    for scenario in scenarios:
        required = [str(item) for item in scenario["required"]]
        missing = [marker for marker in required if marker not in text]
        for repetition in range(1, repetitions + 1):
            trials.append(
                {
                    "variant": variant,
                    "scenario": scenario["id"],
                    "repetition": repetition,
                    "safety": bool(scenario["safety"]),
                    "status": "pass" if not missing else "fail",
                    "missing": missing,
                }
            )
    return trials


def entry_bytes(root: Path, revision: str | None) -> int:
    return sum(
        len(read_source(root, path, revision).encode("utf-8")) for path in ENTRYPOINTS
    )


def run_execution_checks(root: Path) -> dict[str, dict[str, object]]:
    results: dict[str, dict[str, object]] = {}
    for name, command in EXECUTION_CHECKS.items():
        completed = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        results[name] = {
            "status": "pass" if completed.returncode == 0 else "fail",
            "returncode": completed.returncode,
            "output_tail": (completed.stdout + completed.stderr)[-1000:].strip(),
        }
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--baseline-ref",
        default=None,
        help="比較する過去 revision。省略時は現在の到達性だけを判定する",
    )
    parser.add_argument("--skip-execution-checks", action="store_true")
    parser.add_argument(
        "--list-sources",
        action="store_true",
        help="到達した文書を列挙して終了する（シナリオ設計用）",
    )
    parser.add_argument(
        "--scenarios",
        type=Path,
        default=Path(__file__).parents[1] / "evals" / "claude-md-thin-entry" / "scenarios.json",
    )
    args = parser.parse_args()
    root = args.root.resolve()

    candidate_sources = reachable_sources(root, None)
    if args.list_sources:
        for relative in sorted(candidate_sources):
            print(relative)
        print(f"# reachable={len(candidate_sources)} entry_bytes={entry_bytes(root, None)}")
        return 0

    fixture = json.loads(args.scenarios.read_text(encoding="utf-8"))
    scenarios = fixture["scenarios"]
    repetitions = int(fixture["repetitions"])

    trials = evaluate("candidate", candidate_sources, scenarios, repetitions)
    summary: dict[str, object] = {
        "trial_count": len(trials),
        "candidate_pass": sum(trial["status"] == "pass" for trial in trials),
        "candidate_safety_failures": sum(
            trial["status"] != "pass" and trial["safety"] for trial in trials
        ),
        "candidate_reachable_sources": len(candidate_sources),
        "candidate_entry_bytes": entry_bytes(root, None),
    }

    baseline_ok = True
    if args.baseline_ref:
        baseline_sources = reachable_sources(root, args.baseline_ref)
        trials.extend(evaluate("baseline", baseline_sources, scenarios, repetitions))
        summary["baseline_ref"] = args.baseline_ref
        summary["baseline_pass"] = sum(
            trial["status"] == "pass" and trial["variant"] == "baseline" for trial in trials
        )
        summary["baseline_reachable_sources"] = len(baseline_sources)
        summary["baseline_entry_bytes"] = entry_bytes(root, args.baseline_ref)
        baseline_ok = (
            summary["candidate_entry_bytes"] <= summary["baseline_entry_bytes"]
            and summary["candidate_reachable_sources"] >= summary["baseline_reachable_sources"]
        )
        summary["baseline_comparison_passed"] = baseline_ok

    execution_checks = {} if args.skip_execution_checks else run_execution_checks(root)
    summary["execution_checks_passed"] = all(
        result["status"] == "pass" for result in execution_checks.values()
    )

    print(json.dumps(
        {"summary": summary, "execution_checks": execution_checks, "trials": trials},
        ensure_ascii=False,
        indent=2,
    ))

    candidate_total = len(scenarios) * repetitions
    passed = (
        summary["candidate_pass"] == candidate_total
        and summary["candidate_safety_failures"] == 0
        and summary["execution_checks_passed"]
        and baseline_ok
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
