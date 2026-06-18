# team-run PJ設定 — <プロジェクト名>

> `/team-run` 実行時に team-lead が最初に読む、このPJ固有の設定。
> グローバルの「動かし方」（`~/.claude/commands/team-run.md`）に対し、
> ここは「このPJで**何を見て・どう実装し・誰がレビューするか**」を定義する。
> 不要なセクションは削ってよい。空欄ならグローバル既定で動く。

## 通知・監視チャンネル

- Slack通知先: [C0XXXXXXX]      <!-- channel ID推奨。完了報告・エスカレ先 -->
- 監視チャンネル: [なし / C0YYYYYYY]  <!-- 仕様変更・障害を拾うチャンネルがあれば -->
- Jiraプロジェクト: [PROJ]       <!-- チケット連携する場合 -->

## チーム編成デフォルト

- teammate構成: planner(Plan) / implementer(general-purpose) / reviewer(専門)
- 人数目安: [4]
- 重い実装の委任先: codex:codex-rescue   <!-- このPJで使わないなら明記 -->
- このPJ特有の役割: [例: FE/BE分割が多いので implementer を2枚]

## 実装方針

- コーディング規約: [`.claude/CLAUDE.md` / `docs/xxx` を参照]
- 必須テスト: [例: 新規ロジックは vitest 必須 / E2E は playwright]
- 触ってはいけない領域: [例: `legacy/` 配下 / 生成コード]
- ライブラリ選定: [例: 状態管理は zustand 固定]

## レビュー観点（teammateとして起動する専門reviewer）

- 必須: arch-reviewer / security-reviewer
- このPJで重視: [例: perf-reviewer（性能要件あり） / domain-reviewer]
- severity基準: CLAUDE.md準拠（CRITICAL / IMPORTANT は必ず対応）

## PJ固有の制約・注意

- [例: 外部API呼び出しは必ずタイムアウト付き]
- [例: PR は 100 行以下を推奨、垂直分割]
