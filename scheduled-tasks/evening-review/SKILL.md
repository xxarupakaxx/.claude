---
name: evening-review
description: 夕方の日次レビュー。コスト集計・失敗パターン分析・改善提案・Slackサマリー投稿。
---

【目的】毎夕18:00に実行。当日のAI利用コスト・品質を振り返り、改善候補を蓄積する。

【手順】
1. `~/.claude/config/user.json` を Read で読み取る（存在しない場合はデフォルト値で続行）
2. `evening-review` ワークフローを実行する:
   - Workflow Tool を使い、`~/.claude/workflows/evening-review.js` を実行
   - 引数: `args: { config: <user.jsonの内容> }`（config渡しでワークフロー内のagent読み込みをスキップ）

3. ワークフローが以下を自動実行する:
   - コスト集計: ccusage / cost-track ログ / セッションレポートからトークン・コスト算出
   - 失敗パターン分析: harness-suggestions/ の本日分 + セッションJSONL から検出
   - 改善提案: コスト超過時はモデルダウングレード提案、失敗パターンにはルール改善提案
   - Slackサマリー: 上記をまとめてSlack投稿

4. 改善提案は `~/.claude/.local/harness-suggestions/` に保存される（自動適用しない）。

【アラート閾値】
- $0-5: ok（通常運用）
- $5-15: info（日報に記載）
- $15-30: warning（モデルダウングレード検討）
- $30+: critical（即時対応推奨）

【注意】
- 改善提案はユーザー承認後にのみ適用
- 休日・祝日には実行しない
