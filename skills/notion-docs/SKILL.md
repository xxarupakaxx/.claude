---
name: notion-docs
description: Notion MCP（mcp__claude_ai_Notion__*）で、ページ・データベース・データソース・コメント・ビューを検索、作成、更新、移動、複製する依頼に使う。対象 ID と現在内容を確認してから操作する。
---

# Notion ドキュメント操作

Notion MCP（`mcp__claude_ai_Notion__*`）を使う。未接続なら `/mcp` で再接続を案内する。検索・取得は読み取り、作成・更新・移動・コメントなどの外部 write はユーザーの明示依頼の範囲だけで行う。

## 基本経路：search → fetch → operation

対象の ID を推測しない。

1. 必要なら `mcp__claude_ai_Notion__notion-get-teams` と `notion-get-users` で workspace、team、mention、assignee を確認する。
2. `mcp__claude_ai_Notion__notion-search` でキーワード、ページ/データベース、team、更新日を必要な範囲で検索する。0件なら別キーワードまたは新規作成を提案し、複数件ならユーザーに選んでもらう。
3. `mcp__claude_ai_Notion__notion-fetch` で選択した page/database の本文、階層、property、schema を取得する。更新時は必ず現状を読んで差分を作る。

## ページ操作

| 目的 | tool |
| --- | --- |
| 作成 | `notion-create-pages` |
| 更新 | `notion-update-page` |
| 複製 | `notion-duplicate-page` |
| 移動 | `notion-move-pages` |

作成には確定した `parent`（親 page または database ID）、検索しやすい `title`、見出し階層を持つ Markdown ベースの `content` を含める。更新は依頼された範囲の追記・部分更新を優先し、既存 block の全消し・全書き換えや重複作成を避ける。

## データベース、データソース、ビュー

| 目的 | tool |
| --- | --- |
| database 作成 | `notion-create-database` |
| data source の schema/property 更新 | `notion-update-data-source` |
| view 作成 / 更新 | `notion-create-view` / `notion-update-view` |

property 名と型を fetch で確定する。既存 property の rename/delete、大量のページ移動・更新は事前にユーザーの確認を得る。

## コメント

コメント追加は `mcp__claude_ai_Notion__notion-create-comment`、取得は `mcp__claude_ai_Notion__notion-get-comments` を使う。ページ全体か特定 block かを区別し、mention の ID は `notion-get-users` で取得する。

## 禁止と制限

- page/database/parent/property の ID を推測しない。親なしで作成しない。
- fetch なしで update-page を上書きしない。
- 依頼外の整形、property の無断 rename/delete、同名ページの量産をしない。
- API key、token、個人情報、社外秘を Notion に貼らない。
- 使える MCP tool は環境に依存する。権限不足はユーザーへ依頼し、大量 bulk 更新はレート制限を考慮して分割する。
