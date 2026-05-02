"""Reviewer Eval Runner (MVP 雛形)

reviewer サブエージェントを N 回起動し、pass@k / precision / recall / Cohen's kappa を計測する。

Usage:
  python run_reviewer_eval.py --test-id sec-001-sql-injection --k 3
  python run_reviewer_eval.py --category sec --k 3
  python run_reviewer_eval.py --all --k 3

Note:
  `run_reviewer()` は pseudo-callable。実際の reviewer 起動は Claude Code SDK の subagent invocation
  を経由する想定。MVP では `raise NotImplementedError` を返す。
"""
import argparse
import json
import re
from pathlib import Path
from typing import Any

EVAL_ROOT = Path(__file__).parent.parent

SEVERITY_ORDER = ["MINOR", "IMPORTANT", "CRITICAL"]


def run_reviewer(reviewer_name: str, input_code: str, meta: dict) -> list[dict]:
    """指定 reviewer を起動し、検出した指摘リストを返す。

    実装は Claude Code SDK の subagent invocation を用いる想定。
    MVP 段階では未実装のため NotImplementedError を投げる。
    実装する場合は以下のフォーマットで戻り値を返すこと:

        [{"file": str, "line": int, "severity": str, "message": str}, ...]
    """
    raise NotImplementedError(
        "subagent invocation を実装してください。"
        "evals/reviewer/_runner/run_reviewer_eval.py の run_reviewer() を参照。"
    )


def match_finding(actual: list[dict], expected_item: dict) -> bool:
    """期待される指摘が、実際の指摘リストの中で検出されているか判定。

    line_range 内に含まれ、severity が min_severity 以上で、
    patterns のいずれかが message にマッチすれば一致とする。
    """
    min_severity = expected_item.get("min_severity", expected_item["severity"])
    if min_severity not in SEVERITY_ORDER:
        raise ValueError(f"Unknown severity: {min_severity}")
    min_idx = SEVERITY_ORDER.index(min_severity)

    line_lo, line_hi = expected_item["line_range"]
    fuzzy_tol = expected_item.get("fuzzy_line_tolerance", 5)

    for f in actual:
        if not (line_lo - fuzzy_tol <= f["line"] <= line_hi + fuzzy_tol):
            continue
        if SEVERITY_ORDER.index(f["severity"]) < min_idx:
            continue
        text = f.get("message", "")
        if any(re.search(p, text, re.IGNORECASE) for p in expected_item["patterns"]):
            return True
    return False


def is_expected(finding: dict, expected: dict) -> bool:
    """ある検出が期待された範囲（must_detect or may_detect）に含まれるか。"""
    for m in expected.get("must_detect", []) + expected.get("may_detect", []):
        if match_finding([finding], m):
            return True
    return False


def evaluate_case(case_dir: Path, k: int) -> dict:
    """1 ケースを k 回実行し、メトリクスを集計する。"""
    expected = json.loads((case_dir / "expected.json").read_text())
    input_file = next(case_dir.glob("input.*"))
    input_code = input_file.read_text()
    meta_file = case_dir / "input.meta.json"
    meta = json.loads(meta_file.read_text()) if meta_file.exists() else {}
    reviewer = expected["target_reviewer"]

    runs: list[list[dict]] = []
    for _ in range(k):
        actual = run_reviewer(reviewer, input_code, meta)
        runs.append(actual)

    pass_per_run = []
    for actual in runs:
        all_must_hit = all(match_finding(actual, m) for m in expected.get("must_detect", []))
        no_must_not = not any(
            match_finding(actual, mn) for mn in expected.get("must_not_detect", [])
        )
        pass_per_run.append(all_must_hit and no_must_not)
    pass_at_1 = pass_per_run[0] if pass_per_run else False
    pass_at_k = any(pass_per_run)

    tp = sum(
        sum(1 for m in expected.get("must_detect", []) if match_finding(actual, m))
        for actual in runs
    )
    fp = sum(
        sum(1 for f in actual if not is_expected(f, expected))
        for actual in runs
    )
    fn = sum(
        sum(1 for m in expected.get("must_detect", []) if not match_finding(actual, m))
        for actual in runs
    )
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0

    kappa = compute_cohen_kappa(
        human=expected.get("human_label", {}).get("labels", []),
        machine=[infer_severity(actual, expected) for actual in runs],
    )

    return {
        "test_id": expected["test_id"],
        "k": k,
        "pass@1": pass_at_1,
        "pass@k": pass_at_k,
        "pass_per_run": pass_per_run,
        "precision": precision,
        "recall": recall,
        "kappa": kappa,
    }


def infer_severity(actual: list[dict], expected: dict) -> str:
    """actual の中で must_detect にマッチする severity を 1 つ返す（kappa 用）。"""
    for m in expected.get("must_detect", []):
        for f in actual:
            if match_finding([f], m):
                return f["severity"]
    return "MINOR"


def compute_cohen_kappa(human: list[str], machine: list[str]) -> float:
    """severity ラベル間の Cohen's kappa を素朴実装で計算。

    len(human) と len(machine) は同じである必要はない（どちらも空でなければ良い）。
    実装簡略化のため平均一致率ベースで近似する。MVP のため厳密 kappa は別途。
    """
    if not human or not machine:
        return 0.0
    if len(human) != len(machine):
        # len 不一致のときは短い方に合わせる
        n = min(len(human), len(machine))
        human, machine = human[:n], machine[:n]
    n = len(human)

    po = sum(1 for h, m in zip(human, machine) if h == m) / n
    cats = list(set(human) | set(machine))
    pe = sum(
        (human.count(c) / n) * (machine.count(c) / n)
        for c in cats
    )
    if pe == 1:
        return 1.0
    return (po - pe) / (1 - pe)


def collect_cases(root: Path, category: str | None, test_id: str | None) -> list[Path]:
    """評価対象ケース一覧を取得。"""
    cases = []
    for case_dir in sorted(root.iterdir()):
        if not case_dir.is_dir():
            continue
        if case_dir.name.startswith("_") or case_dir.name == "results":
            continue
        if test_id and case_dir.name != test_id:
            continue
        if category and not case_dir.name.startswith(f"{category}-"):
            continue
        cases.append(case_dir)
    return cases


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", default=None, help="例: sec / arch / perf")
    ap.add_argument("--test-id", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--k", type=int, default=3)
    args = ap.parse_args()

    cases = collect_cases(EVAL_ROOT, category=args.category, test_id=args.test_id)
    if not cases:
        print("No matching cases found.")
        return

    results = []
    for c in cases:
        try:
            results.append(evaluate_case(c, args.k))
        except NotImplementedError as e:
            print(f"[SKIP] {c.name}: run_reviewer() 未実装 ({e})")
        except Exception as e:  # noqa: BLE001
            print(f"[ERROR] {c.name}: {e}")

    if not results:
        return

    summary = {
        "total": len(results),
        "pass@1_rate": sum(r["pass@1"] for r in results) / len(results),
        f"pass@{args.k}_rate": sum(r["pass@k"] for r in results) / len(results),
        "precision_avg": sum(r["precision"] for r in results) / len(results),
        "recall_avg": sum(r["recall"] for r in results) / len(results),
        "kappa_avg": sum(r["kappa"] for r in results) / len(results),
    }
    print(json.dumps({"summary": summary, "results": results}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
