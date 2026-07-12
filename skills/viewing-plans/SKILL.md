---
name: viewing-plans
description: 計画・ログ・ロードマップをHTMLビューアで自動表示するスキル。Phase 2完了後（30_plan.md作成後）はRoadmap Viewerを優先表示し、実装中は更新されたroadmap.htmlで現在地を見せ、Phase 5完了後は05_log.mdをlog_viewerで確認する。「計画を見せて」「HTMLで確認」等の依頼にも対応。
allowed-tools: Read, mcp__workflow-html-app__view-plan
---

# Viewing Plans (HTML Viewer版)

計画ファイル・ログ・レビュー結果をHTMLビューアに自動表示する。

Roadmap Viewer は「現在地」「稼働中の作業」「成果物」「計画」「更新鮮度」を一つの画面で確認する俯瞰ビューを担当する。`--serve --watch` で起動すると、Claude CodeまたはCoworkの横に置いたブラウザが自動更新される。Plan Viewer / Log Viewer はMarkdownの詳細確認用として使う。

## 自動発動条件

以下のタイミングで**自動的に**発動（ユーザー確認不要）：

1. **Phase 2完了時**: `${MEMORY_DIR}/memory/<task>/roadmap.html` を生成し、Roadmap Viewerで表示
2. **横で見たい場合**: `scripts/generate-roadmap-view.py ${MEMORY_DIR}/memory/<task> --serve --watch` を起動し、表示URLを案内
3. **Phase 3/4の節目**: `40_progress.md` / `80_review.md` / `05_log.md` / `team-journal.md` / `90_verification.md` または成果物metadataの更新後、watch中ならブラウザが自動更新
4. **Phase 5完了時**: Roadmap Viewerで最終状態を表示し、必要に応じて05_log.mdをlog_viewerで表示

## 手動トリガー

- 「計画をビューアで見たい」「HTMLで確認したい」
- 「ログをタイムラインで見たい」
- 「ロードマップを見たい」「roadmap.htmlを出して」
- `/viewing-plans` 実行時

## ワークフロー

### 1. ファイル読み込み

```
対象ファイル:
  ├── ${MEMORY_DIR}/memory/<task>/00_spec.md → roadmap viewer
  ├── ${MEMORY_DIR}/memory/<task>/30_plan.md → plan viewer
  ├── ${MEMORY_DIR}/memory/<task>/40_progress.md → roadmap viewer
  ├── ${MEMORY_DIR}/memory/<task>/80_review.md → roadmap viewer
  ├── ${MEMORY_DIR}/memory/<task>/90_verification.md → roadmap viewer（任意）
  ├── ${MEMORY_DIR}/memory/<task>/team-journal.md → roadmap viewer（任意）
  └── ${MEMORY_DIR}/memory/<task>/05_log.md → log viewer
```

1. 対象メモリディレクトリを特定
2. `scripts/generate-roadmap-view.py <memory_dir>` を実行して `roadmap.html` を生成
3. 必要に応じて Read ツールで個別Markdownコンテンツを取得

### 2. Roadmap Viewer生成

```bash
python3 scripts/generate-roadmap-view.py ${MEMORY_DIR}/memory/<task>
```

出力:

```
${MEMORY_DIR}/memory/<task>/roadmap.html
```

ユーザーには生成されたHTMLパスを案内する。ブラウザで開けば、タスク全体の現在地、実行パルス、計画、成果物、レビュー、リスクが一画面で見える。

ライブ更新:

```bash
python3 scripts/generate-roadmap-view.py ${MEMORY_DIR}/memory/<task> --serve --watch
```

`--serve` は既定で `127.0.0.1` にbindし、port `0` で空きポートを自動割当する。複数セッションで同時に使う場合は、各セッションの `${MEMORY_DIR}/memory/<task>` を分ける。固定portが必要な時だけ `--port <port>` を指定する。

### 3. MCP Apps view-plan 呼び出し（詳細確認用）

`mcp__workflow-html-app__view-plan` ツールを呼び出し:

```
引数:
  content: <読み込んだMarkdownコンテンツ>
```

ツールは自動的にHTML UIリソースを返し、クライアントがビューアを表示する。

### 4. HTMLビューア表示

- Roadmap Viewer は生成済みHTMLをブラウザで開く
- MCP Apps が利用可能な場合は個別Plan/Log UIを開く
- ユーザーはインタラクティブに計画を閲覧・コメント追加可能
- コメントはpostMessage経由でClaude Codeに送信される

## 機能概要

### Roadmap Viewer（ロードマップビューア）
- `00_spec.md` / `30_plan.md` / `40_progress.md` / `80_review.md` / `05_log.md` を統合し、`team-journal.md` / `90_verification.md` も存在すれば読み込む
- 上部の「いま」、計画キャンバス、実行パルス、成果物シェルフを第一画面へ表示する
- 固定Phaseと固定Taskだけを算定可能な進捗として扱い、推測の百分率を表示しない
- task directory配下の通常ファイルを成果物metadataとして再帰収集する。symlinkは追跡せず、Viewer出力と一時ファイルは除外する
- 生成済みHTMLにsnapshotを埋め込むため、追加サーバーなしで `file://` 表示できる
- `--serve --watch` では `roadmap-snapshot.json` をpollingし、source内容または表示対象artifact metadataが変化したときだけ自動更新する
- 手動で複数Markdown/JSONをドラッグ&ドロップして確認可能
- 選択したMarkdownは、HTMLをescapeした自己完結の整形プレビューと原文を切り替えて確認できる

### Plan Viewer（計画ビューア）
- Markdownレンダリング（見出し、リスト、コードブロック）
- DOMPurifyによるXSS対策
- コメント追加・Claude Codeへのフィードバック送信

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
1. Claude Codeが30_plan.mdの作成を完了
2. `scripts/generate-roadmap-view.py <memory_dir>` を実行
3. `roadmap.html` のパスをユーザーに提示
4. 必要に応じて mcp__workflow-html-app__view-plan に30_plan.md content を渡す
```

```
# 手動トリガー
ユーザー: 計画をビューアで見たい
Claude Code:
1. メモリディレクトリを特定
2. Roadmap Viewerを生成
3. 個別に深掘りしたい場合は30_plan.md / 05_log.mdを既存viewerで表示
```

## 関連ドキュメント

- @context/workflow-rules.md（HTML Viewer Toolsセクション）
- @context/memory-file-formats.md
