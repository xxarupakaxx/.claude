---
name: viewing-plans
description: 計画・ログをMCP Apps HTMLビューアで自動表示するスキル。Phase 2完了後（30_plan.md作成後）、Phase 5完了後（05_log.md確定後）に自動発動。「計画を見せて」「HTMLで確認」等の依頼にも対応。
allowed-tools: Read, mcp__workflow-html-app__view-plan
---

# Viewing Plans (MCP Apps版)

計画ファイル・ログをMCP Apps経由でHTMLビューアに自動表示する。

## 自動発動条件

以下のタイミングで**自動的に**発動（ユーザー確認不要）：

1. **Phase 2完了時**: 30_plan.mdをplan_viewerで表示
2. **Phase 5完了時**: 05_log.mdをlog_viewerで表示

## 手動トリガー

- 「計画をビューアで見たい」「HTMLで確認したい」
- 「ログをタイムラインで見たい」
- `/viewing-plans` 実行時

## ワークフロー

### 1. ファイル読み込み

```
対象ファイル:
  ├── ${MEMORY_DIR}/memory/<task>/30_plan.md → plan viewer
  └── ${MEMORY_DIR}/memory/<task>/05_log.md → log viewer
```

1. Read ツールで対象ファイルを読み込む
2. Markdownコンテンツを取得

### 2. MCP Apps view-plan 呼び出し

`mcp__workflow-html-app__view-plan` ツールを呼び出し:

```
引数:
  content: <読み込んだMarkdownコンテンツ>
```

ツールは自動的にHTML UIリソースを返し、クライアントがビューアを表示する。

### 3. HTMLビューア表示

- MCP Apps が自動的にHTML UIを開く
- ユーザーはインタラクティブに計画を閲覧・コメント追加可能
- コメントはpostMessage経由でCodexに送信される

## 機能概要

### Plan Viewer（計画ビューア）
- Markdownレンダリング（見出し、リスト、コードブロック）
- DOMPurifyによるXSS対策
- コメント追加・Codexへのフィードバック送信

### Log Viewer（ログビューア）※予定
- Phase自動検出・タイムライン表示
- サマリー統計（完了Phase数、所要時間等）

## セキュリティ

- **DOMPurify**: HTMLサニタイズでXSS防止
- **CSP**: Content Security Policyヘッダー
- **オリジン検証**: 信頼済みオリジンのみpostMessage許可

## 使用例

```
# 自動発動（Phase 2完了後）
1. Codexが30_plan.mdの作成を完了
2. Read で30_plan.mdを読み込み
3. mcp__workflow-html-app__view-plan に content を渡す
4. HTML UI が自動表示される（ユーザー操作不要）
```

```
# 手動トリガー
ユーザー: 計画をビューアで見たい
Codex:
1. メモリディレクトリから30_plan.mdを特定
2. Read で読み込み
3. view-plan MCPツールを呼び出し
4. HTML UIが表示される
```

## 関連ドキュメント

- @context/workflow-rules.md（HTML Viewer Toolsセクション）
- @context/memory-file-formats.md
