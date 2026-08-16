---
name: payment-domain-scan
description: LayerX入社準備として、Payment、B2B決済、法人カード、請求書、Peppol、金融規制、LayerX/Bakuraku周辺を毎朝横断し、用語解説と業務フローつきの日誌ノートをObsidianに生成する。
---

# /payment-domain-scan — 毎朝のPaymentドメイン学習

> **スコープ**: このスキルは Obsidian Vault（`~/Notes/Vault`）でのみ有効。Vault 外のプロジェクトでは起動しない（`Daily/`、`Inbox/`、`Claude-note/` が存在せず、参照する絶対ルールと拡張フィールドの定義も Vault の `CLAUDE.md` にしかないため）。Vault 内には project scope の同名スキルがあり、そちらが優先される。

`.claude/commands/payment-domain-scan.md` と [[10_payment-domain-scan]] に従う。

このスキルの目的は、Payment領域のニュースを拾うことではなく、LayerX入社前に業務フロー、用語、法制度、顧客課題、仮説検証、プロダクト含意を毎日少しずつ理解すること。

出力先は `Inbox/automation/payment-trends/payment-trend-YYYY-MM-DD.md`。
`evidence_urls` には、根拠に使った重要URLだけを入れる。
frontmatterには `summary` / `depth: flash` / `related` も設定し、本文には「基礎ノートへの接続」節を含める（テンプレートは [[10_payment-domain-scan]]、定義は `CLAUDE.md` と互換 `CLAUDE.md` の「セカンドブレイン拡張フィールド」）。
外部調査は `research` スキルのルールで行い、一次情報、公式情報、規制当局、業界団体、企業公式発表を優先する。
最低1つは「顧客仮説」または「検証案」まで落とす。
scheduled/無人実行は通常30分以内にpayment trendノートとDailyリンクを残す。
45分を超えそうな場合は、追加ソース調査、画像生成、PNG化を止め、1テーマ、一次情報1〜3件、顧客仮説1件の最小ノートに切り替える。
未確認ソースは本文の「未処理/次回」かbacklogに残す。

日次の完了条件は payment trend ノートと Daily リンクである。
`one-page-concept-sketch` スキル は既定では実行しない。
ユーザーが明示した場合、または別タスクとして十分な時間がある場合だけ実行する。

調査、画像生成、HTML/PNG化などで長時間化しそうな処理は、本体ノートをブロックしない。
代替として、ノート内の `## 明日の候補` または `Inbox/automation/backlog.md` に後続候補を残す。
