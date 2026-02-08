# MCP Server セットアップガイド

## 設定済みMCP Servers（user-level）

settings.jsonで設定済み:

| Server | 用途 |
|--------|------|
| deepwiki | GitHubリポジトリのドキュメント参照 |
| context7 | 最新のライブラリドキュメント取得 |
| mcp-atlassian | Confluence/Jira操作（別設定で有効） |

## プロジェクトごとに設定するMCP Servers

### Serena（コードベースセマンティック検索）

プロジェクトルートで以下を実行:

```bash
claude mcp add serena -- uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context claude-code --project "$(pwd)"
```

**特徴:**
- LSPベースで30以上の言語をサポート
- シンボルレベルのコード理解
- コードベースのセマンティック検索・編集
- トークン節約と応答品質向上

**参考:** [Serena GitHub](https://github.com/oraios/serena)

## 使用方法

### context7の使用

プロンプトに `use context7` を追加:

```
Create a Next.js middleware that checks for a valid JWT. use context7
```

または、ライブラリを指定:

```
Implement basic authentication with Supabase. use library /supabase/supabase for API and docs.
```

### deepwikiの使用

```
mcp__deepwiki__ask_question でリポジトリについて質問
mcp__deepwiki__read_wiki_contents でドキュメント取得
```

### Serenaの使用（プロジェクトで設定済みの場合）

- `find_symbol`: シンボル検索
- `get_definition`: 定義取得
- `get_references`: 参照取得
- `semantic_search`: セマンティック検索

## 追加可能なMCP Servers

| Server | 用途 | 設定コマンド |
|--------|------|------------|
| Slack | チャンネル参照、メッセージ投稿 | `claude mcp add slack -- npx -y @anthropic-ai/mcp-server-slack` |
| GitHub | リポジトリ管理（gh cli代替） | `claude mcp add github -- npx -y @anthropic-ai/mcp-server-github` |
| Notion | ページ読み書き | `claude mcp add notion -- npx -y @notionhq/mcp-server-notion` |
| PostgreSQL | データベース操作 | `claude mcp add postgres -- npx -y @anthropic-ai/mcp-server-postgres` |
