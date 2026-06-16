---
name: pr-review
description: 毎時、ydb-superapp-serverのPRコメントを監視し、レビュー→修正→再レビューの自動ループを回してSlack報告
---

【目的】毎時実行。監視対象リポジトリのPRに付いたコメントを検知し、review→fix→re-review の自動ループ（pr-review-loop ワークフロー）を回す。

【設定読み込み】
- `~/.claude/config/user.json` を Read。`github.watch_repos`（配列）があればそれを監視対象にする。無ければ既定で `ydb-superapp-server` を対象とする。
- Slack通知先は `slack.notification_channel`（無ければDM）。

【手順】
1. `gh` で監視対象リポジトリの直近1時間に更新があったオープンPRを取得する:
   - 自分がauthorのPR: `gh pr list --author @me --state open`
   - 自分がreviewerのPR: `gh search prs --review-requested=@me --state=open`
2. 各PRについて、直近1時間に新規コメント（レビューコメント含む）が付いたものを対象にする。コメントが無ければスキップ。
3. 対象PRごとに pr-review-loop ワークフローを実行する:
   - Workflow Tool で `~/.claude/workflows/pr-review-loop.js` を実行
   - 自分がauthorのPR → `args: { pr: <PR番号>, autoFix: true, maxRounds: 3 }`（指摘を自動修正してpush。信頼タスク全自律）
   - 自分がreviewerのPR → `args: { pr: <PR番号>, autoFix: false }`（レビューのみ。コードは修正しない）
4. ワークフロー結果(result: SHIP/NEEDS_WORK/ESCALATE/BLOCKED)を判定:
   - author自身のPRで SHIP → 「指摘なし/修正完了」をPRにコメント
   - NEEDS_WORK/ESCALATE → 未解決のCRITICAL/IMPORTANTをPRコメント + Slack通知
5. レビュー結果サマリー（PR番号・result・主要指摘・次のステップ）を必ず Slack に投稿する。
6. 冪等性: 同一コメントに対する二重処理を避ける。直近処理済みPR/コメントは `~/.claude/.local/pr-review-state.json` に記録し、未処理分のみ扱う。

【注意】
- 1回の実行で最大5PRまで（過負荷防止）
- pr-review-loop が ESCALATE を返したら、自動修正をやめて人間に委ねる（Slackで明示）
- reviewer立場のPRには絶対にコードをpushしない（autoFix:false固定）