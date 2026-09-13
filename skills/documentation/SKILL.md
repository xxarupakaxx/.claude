---
name: documentation
description: ドキュメント更新。コード変更後にnpm script/環境変数/API追加を検出した場合に使用。CLAUDE.md/README.md/API仕様の同期を支援。
allowed-tools: Read, Write, Bash, Glob, Grep
---

# ドキュメント更新

## トリガー条件

- コード変更後にドキュメント更新が必要な場合
- 以下の変更を検出した場合:
  - 新規npm script追加
  - 環境変数追加
  - APIエンドポイント追加・変更
  - アーキテクチャ変更

## 実行手順

### 1. 変更内容の確認

`<base-branch>` は PJ 設定（CLAUDE.md / CLAUDE.md）の `BASE_BRANCH` に従う。未定義時は develop → main → master の順で存在するものを使う。

```bash
git diff <base-branch> --name-only
git diff <base-branch>
```

### 2. 更新が必要なドキュメントの特定

| カテゴリ | 例 | 更新対象 |
|---------|-----|---------|
| コマンド変更 | npm script追加 | CLAUDE.md, README.md |
| API変更 | エンドポイント追加 | API仕様書 |
| 設定変更 | 環境変数追加 | README.md |
| アーキテクチャ変更 | 新規レイヤー | CLAUDE.md |

### 3. 更新提案の作成

```markdown
## ドキュメント更新提案

### CLAUDE.md
**現在:**
```
npm run lint
```

**提案:**
```
npm run lint
npm run new-command  # 新しいコマンド
```

### README.md
**追加:**
```
## 環境変数
- NEW_VAR: 説明
```
```

### 4. 更新不要の判断

以下は更新不要:
- 内部実装の変更のみ
- テストコードの変更のみ
- リファクタリング（機能変更なし）

## 実績由来の知見

- canonical な記録先が外部（Confluence等）だとユーザーが明示した場合、リポジトリ側ドキュメントは長文複製ではなく参照リンクへ縮小する（出典: memories/rollout_summaries/2026-06-16T07-44-40-S8ow-jira_ai_workflow_shared_dev_state_confluence_integration.md「Task 2, Failures and how to do differently」）
- リポジトリ内ドキュメントは明示指定がなくても日本語プローズを既定とし、固有名詞は原語のまま保持する（出典: memories/rollout_summaries/2026-06-16T07-44-40-S8ow-jira_ai_workflow_shared_dev_state_confluence_integration.md「Task 1, Preference signals」）
- 用語・導線の置換を伴うドキュメント更新は、主要ファイルの修正だけで完了と判断しない。置換対象語彙で `rg` 横断検索を行い、ヒットゼロになったことを完了条件とする（部分置換で旧記述が残存しレビュー指摘を受けた実失敗より。出典: memories/23_evidence_summary.md「S-004, S-009」）
- 図・表に実スキーマ未確認の項目を書かない。schema定義と突合してから記載する（ER図に実在しないカラムを書き、reviewer指摘で削除した実例。出典: memories/rollout_summaries/2026-06-26T02-46-53-Dw5K-check_in_lottery_wiki_migration_and_review_fix.md「Task 2 Key steps / Reusable knowledge」）
- 内部仕様と設計docが矛盾したら現実装をsource of truthにする。既存docs/wikiの命名規約（flattened `features-{name}-interface.md` 等）を先に確認してから書く（出典: memories/rollout_summaries/2026-06-26T02-46-53-Dw5K-check_in_lottery_wiki_migration_and_review_fix.md「Task 1 Preference signals / Key steps」）
