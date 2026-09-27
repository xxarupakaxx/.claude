# 計画から実装への判断契約

## session-dashboardの計画契約（現行）

新規の作業計画とレビューは[セッションダッシュボード](session-dashboard.md#計画の正本とレビュー)を正本とする。目的・前提→計画→成果物→内部品質の審査順と独立性は維持し、審査・実装は同じダッシュボードの計画全文を参照する。審査対象の版と本文証拠を記録し、実装前・完了前に現行本文と照合する。

以下の30_plan.html、plan-review.json、旧parser、task-context.py --execution、sync-roadmap.pyに関する形式と起動条件は過去taskの互換記録であり、新規session-dashboardへ適用しない。移行前の旧計画・未完了gateは保持し、移行時は新正本への対応を確認する。指示による照合を自動強制済みとは扱わない。

正本は[Codex共通契約](../../.codex/context/plan-execution-contract.md)。Claudeもこの契約を読み、目的・前提→計画→成果物→内部品質の順に審査する。

移行前タスク専用の旧形式では、HTML本文の実装契約、plan-review.json、task-context.pyの`--execution`、sync-roadmap.pyのPhase 3–5は`~/.codex/scripts/`の共通実装を使う。ローカルコピーや別schemaを作らない。helper不在・非zero・未審査を別のCLIで迂回せず停止する。既存のWork Packet、Evidence Bundle、外部writeの承認gateは維持する。
