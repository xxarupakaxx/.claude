# Tool Invocation Rules

全プロジェクト・全ツールに適用される呼び出し規約。

## MCPツールは完全修飾名で呼ぶ

MCPツールは完全修飾名 `mcp__<server>__<tool>` で呼ぶ。
短縮名は `No such tool available` エラーになる。

例:
- ❌ `mark_chapter`
- ✅ `mcp__ccd_session__mark_chapter`
- ❌ `spawn_task` / ✅ `mcp__ccd_session__spawn_task`
- ❌ `show_widget` / ✅ `mcp__visualize__show_widget`

deferred tool（`<system-reminder>` に名前のみ表示されるツール）は、
呼び出し前に `ToolSearch` で `select:<完全修飾名>` を実行してスキーマを取得すること。
