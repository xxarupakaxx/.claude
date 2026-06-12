---
description: Red→Blue→Auditor の3エージェント敵対的レビューを起動
---

# /adversarial-review コマンド

`adversarial-review` スキルを起動し、Red（攻撃側）→ Blue（防御側）→ Auditor（審判）の3段レビューを実行します。

## 使用場面

- DB スキーマ変更、認証フロー変更、外部 API 契約変更等の重要判断
- `auto-reviewing-pre-pr` が ESCALATE を返したとき
- 単一視点では見逃しがちな盲点を検出したいとき

## 実行手順

1. `adversarial-review` スキルを起動
2. Phase 1-5 を順次実行（Red 単独 → Blue 単独 → Auditor 単独）
3. 集計結果（ADOPT/DOWNGRADE/UPGRADE/REJECT/ESCALATE 件数）をユーザー提示
4. ESCALATE 件は AskUserQuestion で人間判断を求める

## コスト方針

- Red/Blue/Auditor はそれぞれ `agent_type` のみ指定し、`model` / `service_tier` は通常省略
- role既定は Red/Blue が `gpt-5.4` + `priority`、Auditor が `gpt-5.5` + `priority`
- `sonnet` / `opus` / `haiku` は Codex の model override として指定しない

詳細は `~/.claude/skills/adversarial-review/SKILL.md` 参照。
