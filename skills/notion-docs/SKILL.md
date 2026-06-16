---
name: notion-docs
description: Notion MCP（mcp__claude_ai_Notion__*）を使い、ページ・データベース・コメント・ビューを操作するスキル。Notion 検索・ページ作成・ページ更新・ページ複製・ページ移動・データベース作成・データソース更新・コメント追加/取得・ビュー作成/更新・ユーザー/チーム確認を扱う。「Notion ページ作って」「Notion ページ更新」「Notion 検索して」「Notion でドキュメント作って」「Notion のデータソース更新」「Notion にコメント追加」「Notion ページ移動」「Notion DB 作って」「Notion で議事録」等の依頼が来たら必ず使うこと。
---

# Notion ドキュメント操作スキル

Notion MCPツール（`mcp__claude_ai_Notion__*`）を使い、ページ・データベース・コメント・ビュー操作を自動化する。

## トリガー条件

以下の依頼が来たら自動適用する:
- 「Notion ページ作って」「Notion でドキュメント書いて」「Notion に議事録」
- 「Notion ページ更新」「Notion の◯◯を直して」
- 「Notion 検索」「Notion で◯◯を探して」
- 「Notion DB 作って」「データベース更新」「データソース更新」
- 「Notion にコメント」「Notion のコメント確認」
- 「Notion ページ移動」「ページを複製」

## 前提

- MCPサーバー `claude.ai Notion` が接続済みであること
- 未接続の場合は `/mcp` での再接続を案内

## 基本パターン: search → fetch → update

Notion 操作は **「ID を確定させる」** ことが最重要。次のパターンを徹底する。

```
search（自然言語で対象探索）
  → fetch（ページ/DB の現在内容と構造を取得）
  → create-pages / update-page / update-data-source（変更を適用）
```

ID を推測で書かない。必ず `notion-search` または `notion-fetch` で取得する。

## ワークフロー

### Step 1. コンテキスト確認（任意・必要時）

| 目的 | ツール |
|---|---|
| チーム/ワークスペース一覧 | `mcp__claude_ai_Notion__notion-get-teams` |
| ユーザー一覧（メンション/担当者用） | `mcp__claude_ai_Notion__notion-get-users` |

### Step 2. 対象を探す（search）

`mcp__claude_ai_Notion__notion-search` でキーワード検索。

- フィルタ可: ページ / データベース、所属チーム、更新日範囲
- ヒット 0 件 → AskUserQuestion で別キーワード確認 or 新規作成提案
- ヒット複数 → 一覧提示してユーザーに対象選択

### Step 3. 内容と構造を取得（fetch）

`mcp__claude_ai_Notion__notion-fetch` でページ ID から本文・プロパティを取得。

- ページ階層・データベーススキーマ・既存コンテンツを把握
- 更新時は **必ず fetch してから差分を作る**（上書き事故を防ぐ）

### Step 4. ページ操作

| 目的 | ツール |
|---|---|
| ページ作成 | `mcp__claude_ai_Notion__notion-create-pages` |
| ページ更新 | `mcp__claude_ai_Notion__notion-update-page` |
| ページ複製 | `mcp__claude_ai_Notion__notion-duplicate-page` |
| ページ移動 | `mcp__claude_ai_Notion__notion-move-pages` |

**作成時の必須項目**:
- `parent`（親ページ ID or データベース ID）: Step 2/3 で確定
- `title`: 明確かつ検索しやすい名前
- `content`: Markdown ベースで本文を構成（見出し階層を意識）

**更新時の注意**:
- 既存ブロックを全消し&全書き換えにならないよう、追記/部分更新を優先
- 「ついで修正」をしない（依頼スコープ外のセクションは触らない）

### Step 5. データベース操作

| 目的 | ツール |
|---|---|
| データベース作成 | `mcp__claude_ai_Notion__notion-create-database` |
| データソース更新（スキーマ/プロパティ変更） | `mcp__claude_ai_Notion__notion-update-data-source` |
| ビュー作成 | `mcp__claude_ai_Notion__notion-create-view` |
| ビュー更新 | `mcp__claude_ai_Notion__notion-update-view` |

- プロパティ名・型は事前に fetch で確認
- 既存プロパティのリネーム/削除は破壊的なので AskUserQuestion で確認

### Step 6. コメント

| 目的 | ツール |
|---|---|
| コメント追加 | `mcp__claude_ai_Notion__notion-create-comment` |
| コメント一覧取得 | `mcp__claude_ai_Notion__notion-get-comments` |

- ページ全体 or 特定ブロックへのコメントを区別
- メンションは `notion-get-users` で取得した user_id を使う

## 実行前チェックリスト

1. 対象ページ/DB の ID は search/fetch で確定したか？
2. parent（親）は意図した場所か？（ワークスペース直下 vs 既存ページ配下）
3. 更新時、上書きする範囲は依頼スコープ内か？
4. 機密情報（API キー・トークン・社外秘）を含めていないか？
5. 大量ページ移動・大量更新は事前にユーザー確認したか？

## Anti-Patterns（禁止事項）

- ページ ID を推測で渡す（必ず `notion-search` / `notion-fetch`）
- 既存ページを fetch せずに `update-page` で本文を上書きする
- 依頼にないセクションを「ついでに」整形・改善する
- データベースの既存プロパティを無断でリネーム・削除する
- 重複検索せずに同名ページを量産する（先に search で確認）
- 親（parent）未指定でページ作成（漂流ページ化を防ぐ）
- 機密情報を Notion に貼る（社外秘・個人情報・トークン類）

## 既知の制限

- Notion MCP の利用可能ツールは環境により異なる。未接続なら `/mcp` 案内
- 大量バルク更新はレート制限の対象。分割実行を推奨
- Notion 側の権限不足（ページ非公開等）の場合はユーザーに権限付与を依頼
