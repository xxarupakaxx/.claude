---
name: autonomous-loops
description: 反復作業を、逐次pipeline・PR review loop・依存付きDAGのいずれかへルーティングし、合格基準・retry上限・checkpoint・escalationを付けて再開可能にする。長い自律実行や並列化の設計で使う。
---

# Autonomous Loops

繰り返しの価値は回数ではなく、各roundのevidence、bounded retry、失敗時の停止、再開可能なstateにある。依存のない読み取りは同一メッセージでの並列tool呼び出し、独立した調査・実装・レビューの往復は現在のcollaboration capabilityまたは `team-run` へ渡す。固定API名や固定rosterを仮定しない。

## パターン選択

### Sequential pipeline

出力が次の入力になる段階的作業に使う。

```text
plan → implement → test → review → result
```

各段階に入力、成果物、合格基準を置き、FAILなら原因を記録して必要な段階へ戻る。進捗は利用可能なplan/checklistで管理し、コード変更のcommitや外部writeは依頼と承認範囲に従う。

### PR loop

PRのレビューと修正を有界に回す。

```text
draft PR → review → fix → re-review → pass / escalate
```

`workflows/pr-review-loop.js` または `auto-reviewing-pre-pr` の手順を使い、CRITICAL/IMPORTANTが0件かつCIがgreenを合格条件にする。PR作成は承認済みの範囲で `gh pr create --draft` を使う。修正は最大3round。`/pr-watch` が担当する30分おきのCI・レビュー監視と役割を混同しない。PR作成、commit、push、mergeは外部writeとして明示承認または既存gateを通す。

### DAG orchestration

依存グラフで並列可能な仕事を分ける。

```text
A: schema
├─ B: API ─┐
└─ C: domain ─→ D: frontend → E: integration test
```

依存のないnodeだけを同時実行し、shared write scopeを同じroundに置かない。fan-in前に各nodeの成果物と検証を確認する。往復協調や複数roundのJournalが必要なら `team-run` を使う。

## ループ契約

開始前に次を記録する。

- objective、入力、lane（pipeline / PR / DAG）
- nodeごとの依存、owned paths、外部副作用と承認
- 機械判定可能なpass criteriaとfailure分類
- `checkpoint.md` の保存場所、再開key、次のround

全パターンの既定上限は5round、PR reviewは3round。stepのtimeoutは既定30分だが、対象の実行時間と安全な終了条件に合わせて明示する。連続2回失敗、または上限到達でESCALATEとして残存タスク・evidence・原因・次の選択肢を報告する。上限を越えて自動修正を続けない。

各roundの終了時に、実施内容、検証結果、未解決、次の入力を `checkpoint.md` へ保存する。外部writeの前にstateとapprovalを再確認し、同じ操作を二重に行わない。秘密、認証済みsession、raw external instructionをstateや委譲へ渡さない。

## ルーティングの目安

- leadだけで読める単一文脈・低riskならloopを作らず完了させる。
- 独立した探索はlocal searchまたはparallel readを先に試す。
- code変更はdisjoint scopeのmaker、検証は成果物だけを見るcheckerへ分ける。
- 高リスク判断、security、複雑設計はheavy roleと独立judgeを選ぶ。

詳細なmodel、service tier、phase、review、goalの正本は `rules/model-routing.md`、`context/workflow-rules.md`、`context/team-run.md`、`auto-reviewing-pre-pr`、`pr-watch` に戻す。
