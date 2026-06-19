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

## ファイル探索は検索ファースト（CRITICAL）

コードベースを調べる時、ファイルを1つずつ `Read` で通読して把握するのは禁止。
必ず **「広く検索 → 候補を絞る → 必要箇所だけ Read」** の順で進める。
これは team-run / exploring-codebase / 単発 Explore / 専門探索 agent すべてに適用される。

1. **まず検索で当たりをつける**: `rg`（ripgrep）/ Grep / Glob でシンボル・文字列・ファイル名を横断検索
   - 定義箇所: `rg -n "func Foo|class Foo|def foo"`
   - 利用箇所: `rg -n "Foo\(" -t go`
   - ファイル列挙: Glob `**/*.tsx` / `rg --files | rg keyword`
2. **Read は絞り込んだ確定箇所のみ**: ヒット行の前後だけ `Read`（offset/limit 活用）。ディレクトリの全ファイル通読は禁止
3. **並列検索**: 独立した検索は1メッセージで複数同時に投げる

### アンチパターン

- ❌ `ls` でディレクトリ一覧 → 1ファイルずつ全部 `Read` して把握しようとする
- ❌ `rg`/`grep` を使わず `Read` だけで目的の関数を探す
- ❌ `rg` でヒット位置が分かっているのにファイル全体を `Read` する
- ✅ `rg -n "keyword"` で位置特定 → 該当行 ±数十行だけ `Read`

コードベース探索のサブエージェントは `Agent(subagent_type: "Explore")` を優先（whole file ではなく excerpt を読む設計）。
