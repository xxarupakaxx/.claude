# Reviewer Eval Harness

reviewer サブエージェントの **品質を pass@k / precision / recall / Cohen's κ** で定量評価するためのデータセット + 実行ランナー。

## ディレクトリ構造（MVP・フラット）

```
evals/reviewer/
├── README.md                       # 本ファイル
├── _runner/
│   ├── run_reviewer_eval.py        # 評価スクリプト雛形（pseudo-callable）
│   └── metrics.py                  # precision/recall/kappa/pass@k
├── sec-001-sql-injection/          # 各ケースは個別ディレクトリ
│   ├── input.ts                    # レビュー対象コード
│   ├── input.meta.json             # 言語・FW・前提
│   ├── expected.json               # 期待される指摘（JSON Schema 準拠）
│   └── README.md                   # ケース説明
├── arch-001-shotgun-surgery/
├── perf-001-n-plus-one/
└── results/
    └── YYYY-MM-DD/
        ├── summary.md
        └── raw/
            └── sec-001-run1.json
```

> **R10（2026-05-02）**: MVP はフラット構造（カテゴリ別サブディレクトリなし）。ケースが 10 件を超えたら category 別ディレクトリへの再編を検討する。

## ケース命名規約

`<category>-<seq>-<short-desc>` 形式。

| category | 含むテスト例 |
|---------|-------------|
| `sec-` | SQL injection / XSS / IDOR / 認証バイパス |
| `arch-` | Shotgun Surgery / 循環参照 / God Object |
| `perf-` | N+1 / O(n²) / メモリリーク / 不要再レンダ |
| `test-` | テスト不足 / アサーション欠落 |
| `cq-` | 命名 / 重複 / マジックナンバー |

## 実行方法（雛形）

```bash
cd ~/.claude/evals/reviewer
python3 _runner/run_reviewer_eval.py --test-id sec-001-sql-injection --k 5
python3 _runner/run_reviewer_eval.py --category sec --k 3
python3 _runner/run_reviewer_eval.py --all --k 3
```

> 現状 `run_reviewer_eval.py` の `run_reviewer()` は **pseudo-callable**（実装は Claude Code SDK の subagent invocation 経由を想定）。`raise NotImplementedError` を返す。実際に実行する際は、Task tool 経由で reviewer を起動するロジックを差し込む必要がある。

## 評価メトリクス

- **pass@1**: 単発実行 PASS 率（信頼性指標）
- **pass@k**: k 回試行中 1 回でも PASS したケース率（カバレッジ指標）
- **precision** = TP / (TP + FP) — 誤検出耐性
- **recall** = TP / (TP + FN) — 見逃し耐性
- **Cohen's κ** = (po - pe) / (1 - pe) — 人間ラベルとの一致度

> **κ閾値**: McHugh 2012 の正しい解釈に従い `κ ≥ 0.6` を実用最低ライン とする（一般的に使われる 0.4 は too lenient と批判されている）。

## 退化検出

reviewer prompt に変更を加えた場合、変更前 baseline と変更後の precision/recall を比較。

| 状況 | 判定 |
|------|------|
| precision/recall 共に baseline 以上 | OK |
| precision/recall いずれかが baseline -2pt 以内 | 注意（許容範囲） |
| precision/recall いずれかが baseline -2pt 超 | **退化** → ロールバック検討 |

## 関連

- `~/.claude/.local/memory/260502_claude_config_research/30_plan.md` — 設計計画
- `~/.claude/.local/memory/260502_claude_config_research/40_templates.md` #6 — 詳細テンプレ
- `~/.claude/skills/eval-harness/` — Eval-Driven Development 全体スキル
