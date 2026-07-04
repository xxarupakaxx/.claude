---
name: ask-skill-router
description: "Matt Pocockのask-matt型の軽量ルーター。どのskill/flowを使うべきか、user-invokedとmodel-invokedを分けて判断する。「どのskill」「ask-matt相当」「flow選んで」「このタスクの進め方を選んで」等で使用。重いSuperpowers/Team flowを起動する前の小さな判断層。"
---

# Ask Skill Router

このskillは、作業を始める前に「どのskillを使うか」を小さく決めるためのルーターである。
目的は、重いharnessに早く乗せすぎず、実際のボトルネックに合う最小の規律を選ぶことにある。

## 判断原則

1. **No skill** で済むなら使わない。
   自明な1行修正、単純な検索、短い説明では通常の作業で進める。
2. **User-invoked** と **model-invoked** を分ける。
   作業の進路や外部状態を変えるflowは、ユーザーの明示または短い確認を待つ。
   小さな品質規律は、タスクに合うときだけモデルが使ってよい。
3. Superpowers や長いteam flowは既定にしない。
   明示依頼、複数ターンの高価値実装、既存計画が前提にしている場合だけ使う。
4. 迷ったら「要求の不一致」「共有語彙」「feedback loop不足」「設計劣化」「外部調査不足」のどれかに分類する。

## ルーティング表

| 症状 | 推奨route | 起動権 |
|---|---|---|
| 何を作るべきか曖昧 | `grill-me`、必要なら `brainstorming` | user-invoked |
| 会話が冗長、用語が揺れる | `ubiquitous-language`、CONTEXT/ADR更新 | model-invoked |
| 仕様を残したい | PRD化、`creating-adr`、issue tracker またはローカルMarkdown | user-invoked |
| 独立タスクに割りたい | `team-run`、`orchestrate`、issue分解 | user-invoked |
| コードが動かない | `diagnosing-bugs` | model-invoked |
| 新規ロジックやバグ修正 | `tdd` | model-invoked |
| 設計が泥団子化している | `improving-architecture`、`software-architecture`、`codebase-review` | user-invoked for broad refactor |
| 外部事実や最新仕様が必要 | `research`、Context7、WebSearch、DeepWiki | model-invoked |
| 完了前の証拠が弱い | `verification-loop`、`verify`、review skill | model-invoked |
| 別agentや別threadへ渡す | handoff tool/skill、作業ログ、Daily/issueリンク | user-invoked |

## 出力形式

迷っているユーザーに返すときは、次の形で短く出す。

```md
推奨route: <skill or no skill>
起動権: user-invoked / model-invoked / no skill
理由: <ボトルネックを1文で>
次の一手: <今すぐやる最小手順>
```

## 禁止

- 単に「非自明」だからという理由だけでSuperpowersやteam flowへ送らない。
- ユーザーが求めていない外部投稿、PR作成、issue作成、スケジュール変更を始めない。
- 既存のproject `AGENTS.md` / `CLAUDE.md` / `README.md` のルールを、このskillで上書きしない。
