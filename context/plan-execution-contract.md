# 計画から実装への判断契約

正本は[Codex共通契約](../../.codex/context/plan-execution-contract.md)。Claudeもこの契約を読み、目的・前提→計画→成果物→内部品質の順に審査する。

HTML本文の実装契約、plan-review.json、task-context.pyの`--execution`、sync-roadmap.pyのPhase 3–5は`~/.codex/scripts/`の共通実装を使う。ローカルコピーや別schemaを作らない。helper不在・非zero・未審査を別のCLIで迂回せず停止する。既存のWork Packet、Evidence Bundle、外部writeの承認gateは維持する。
