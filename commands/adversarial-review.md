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

- Red/Blue は `Agent(subagent_type: "xxx")` で model 省略（親継承）、Auditor のみ `model: "opus"` 指定
- model 指定は審判（Auditor）のみ。Red/Blue は親セッションのモデルを継承

詳細は `~/.claude/skills/adversarial-review/SKILL.md` 参照。
