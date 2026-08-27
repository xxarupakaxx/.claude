# workflow-html-app

MCP Appsプロトコルを使用したインタラクティブHTMLワークフローViewer。

## 機能

- `view-plan`: 計画ファイル（30_plan.md）をインタラクティブHTMLで表示
  - Markdownレンダリング
  - コメント入力（Claude Codeへのフィードバック）
  - responsiveな文書・review UI
- `view-log`: 作業ログ（05_log.md）を独立したLog Viewerとして表示
  - sanitized Markdown描画をPlan Viewerと共有
  - コメントprefixを文書種別で切り替え

## ビルド

```bash
npm install
npm run build
```

## Claude Code連携設定

Claude CLIでuser scopeへ登録:

```bash
claude mcp add --scope user workflow-html-app -- \
  bash -c 'exec node "$HOME/.claude/mcp-servers/workflow-html-app/dist/main.js"'
```

## 使用方法

Claude Codeから:
```
# view-plan ツールを呼び出し
mcp__workflow-html-app__view-plan content="# 計画\n\n## タスク\n- [x] 完了"

# view-log ツールを呼び出し
mcp__workflow-html-app__view-log content="# 作業ログ\n\n## Phase 1: 調査\n- 完了"
```

## 技術スタック

- MCP SDK (`@modelcontextprotocol/sdk`)
- Vite + vite-plugin-singlefile（HTMLバンドル）
- Marked.js（Markdownレンダリング）

## 注意事項

MCP Apps UIは現時点でClaude Code公式サポートが限定的。
HTML UIの表示はホスト側のMCP Apps対応が必要。
