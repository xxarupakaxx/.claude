---
name: create-mcp-server
description: MCP（Model Context Protocol）最小サーバの雛形を生成するメタスキル。TypeScript（@modelcontextprotocol/sdk + package.json）または Python（mcp パッケージ + pyproject.toml）から言語を選択し、最低1つのツール定義サンプル + ~/.Codex.json または settings.json への登録方法 + 動作確認手順（Codex mcp list）を含む雛形を出力する。使用タイミング: (1) 独自MCPサーバを作りたいとき、(2) /create-mcp-server <名前> <言語> 実行時、(3) 「MCPサーバを作って」「カスタムMCP追加」「mcp 雛形」等の依頼時。create-skill 派生のメタスキル。
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion, Bash
---

# Create MCP Server

MCP（Model Context Protocol）最小サーバの雛形を生成するメタスキル。

## 既存設定との関係

- **~/.Codex.json**: user-level MCP 登録先
- **.mcp.json**: project-level MCP 登録先（リポジトリ共有可）
- **create-skill / create-subagent / create-hook**: 姉妹メタスキル

## ワークフロー

### Step 1: 要件パース

```
入力: /create-mcp-server my-tool typescript
→ name: my-tool
→ lang: typescript
→ scope: user（デフォルト） or project
```

AskUserQuestion で必須項目を確認（不明な場合のみ）:
- 言語（TypeScript / Python）
- 配置先（user `~/mcp/<name>/` or PJ `./mcp/<name>/`）
- 最初のツール仕様（名前 / 入力 schema / 振る舞いの1行説明）

### Step 2: 言語選択ガイド

| 観点 | TypeScript | Python |
|------|-----------|--------|
| エコシステム | npm 豊富・既存JS資産 | データ系 SDK 豊富 |
| 配布 | npx 一発実行可 | uvx / pipx |
| 推奨ケース | Web API ラッパ・既存JSロジック流用 | データ処理・ML・既存Pythonロジック流用 |

### Step 3: TypeScript 雛形

ディレクトリ構造:
```
<name>/
├── package.json
├── tsconfig.json
├── src/
│   └── index.ts
└── README.md
```

**package.json:**
```json
{
  "name": "<name>",
  "version": "0.1.0",
  "type": "module",
  "bin": { "<name>": "dist/index.js" },
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "tsx src/index.ts"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0",
    "zod": "^3.23.0"
  },
  "devDependencies": {
    "typescript": "^5.5.0",
    "tsx": "^4.0.0"
  }
}
```

**src/index.ts（最小例 + 1ツール）:**
```typescript
#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";

const server = new Server(
  { name: "<name>", version: "0.1.0" },
  { capabilities: { tools: {} } }
);

const EchoInput = z.object({ text: z.string() });

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [{
    name: "echo",
    description: "入力テキストをそのまま返すサンプルツール",
    inputSchema: {
      type: "object",
      properties: { text: { type: "string" } },
      required: ["text"]
    }
  }]
}));

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  if (req.params.name === "echo") {
    const { text } = EchoInput.parse(req.params.arguments);
    return { content: [{ type: "text", text }] };
  }
  throw new Error(`Unknown tool: ${req.params.name}`);
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

### Step 4: Python 雛形

ディレクトリ構造:
```
<name>/
├── pyproject.toml
├── src/
│   └── <name>/
│       ├── __init__.py
│       └── server.py
└── README.md
```

**pyproject.toml:**
```toml
[project]
name = "<name>"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["mcp>=1.0.0", "pydantic>=2.0"]

[project.scripts]
<name> = "<name>.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**src/<name>/server.py:**
```python
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from pydantic import BaseModel

server = Server("<name>")

class EchoInput(BaseModel):
    text: str

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [Tool(
        name="echo",
        description="入力テキストをそのまま返すサンプルツール",
        inputSchema={
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
    )]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "echo":
        args = EchoInput(**arguments)
        return [TextContent(type="text", text=args.text)]
    raise ValueError(f"Unknown tool: {name}")

def main():
    async def run():
        async with stdio_server() as (r, w):
            await server.run(r, w, server.create_initialization_options())
    asyncio.run(run())
```

### Step 5: Codex への登録

**ユーザー設定（推奨）— `~/.Codex.json`:**
```json
{
  "mcpServers": {
    "<name>": {
      "command": "node",
      "args": ["/absolute/path/to/<name>/dist/index.js"]
    }
  }
}
```

Python の場合:
```json
{
  "mcpServers": {
    "<name>": {
      "command": "uvx",
      "args": ["--from", "/absolute/path/to/<name>", "<name>"]
    }
  }
}
```

**プロジェクト共有設定 — `.mcp.json`（PJ ルート）:**
リポジトリにコミットしてチーム共有可能。同じ schema を使う。

### Step 6: 動作確認手順を提示

```bash
# 1. ビルド（TypeScript）
cd <name>
npm install && npm run build

# 1. インストール（Python）
cd <name>
uv sync   # または pip install -e .

# 2. 登録確認
Codex mcp list

# 3. Codex 起動後、Skill/Agent から mcp__<name>__<tool> として呼び出し可能

# 4. デバッグ: stderr ログを直接実行で確認
node dist/index.js < /dev/null   # 起動して JSON-RPC 待ち状態になればOK
```

### Step 7: 雛形書き出し

`Read references/mcp-templates.md` から該当言語の完全テンプレを取得し、Write で配置。
書き出し後、Bash で `chmod +x` （TS の bin）と `npm install` or `uv sync` の実行可否をユーザーに確認。

## Anti-Patterns

- **stdout 汚染**: stdio transport は JSON-RPC 専用。`console.log` / `print` で stdout を汚すと通信破綻 → ログは **必ず stderr**
- **schema 省略**: `inputSchema` 未指定だと Codex が呼べない
- **絶対パス未使用**: `command`/`args` が相対パス → どこから起動しても動くよう絶対パス
- **依存重量化**: 最小サーバに 100MB の依存を入れない（起動オーバーヘッド）
- **同期 I/O ブロック**: Python は asyncio、Node は async/await 前提。同期で長時間処理しない
- **再起動忘れ**: ~/.Codex.json 編集後は Codex 再起動が必要
- **既存 MCP との name 衝突**: `Codex mcp list` で確認

## チェックリスト

- [ ] 言語が選択された（TypeScript / Python）
- [ ] 最低1ツールが定義されている（inputSchema 付き）
- [ ] stdio transport を使用（HTTP は別途検討）
- [ ] ログは stderr 出力（stdout は JSON-RPC 専用）
- [ ] ~/.Codex.json or .mcp.json 登録例を提示
- [ ] `Codex mcp list` での確認手順を提示
- [ ] 絶対パスで command/args を記載
- [ ] 既存 MCP サーバ名と衝突なし

## 関連スキル・ルール

- `create-skill` / `create-subagent` / `create-hook` — 姉妹メタスキル
- `update-config` — settings.json 編集
- `~/.Codex/rules/library-research.md` — SDK バージョン確認に Context7 を使用
- 公式: https://modelcontextprotocol.io/
- SDK: `@modelcontextprotocol/sdk` (TS) / `mcp` (Python on PyPI)
