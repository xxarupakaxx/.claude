# MCP Server Template Reference

`create-mcp-server` スキルから参照される MCP 最小サーバ雛形集。

## TypeScript Template

### package.json
```json
{
  "name": "my-mcp-server",
  "version": "0.1.0",
  "type": "module",
  "main": "dist/index.js",
  "bin": {
    "my-mcp": "dist/index.js"
  },
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0"
  },
  "devDependencies": {
    "@types/node": "^20",
    "typescript": "^5.4"
  }
}
```

### tsconfig.json
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "outDir": "dist",
    "esModuleInterop": true,
    "strict": true
  },
  "include": ["src/**/*"]
}
```

### src/index.ts (最小ツール定義)
```typescript
#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

const server = new Server(
  { name: "my-mcp-server", version: "0.1.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "echo",
      description: "Echo back the provided text",
      inputSchema: {
        type: "object",
        properties: { text: { type: "string" } },
        required: ["text"],
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "echo") {
    const text = request.params.arguments?.text ?? "";
    return { content: [{ type: "text", text: `Echo: ${text}` }] };
  }
  throw new Error(`Unknown tool: ${request.params.name}`);
});

await server.connect(new StdioServerTransport());
```

## Python Template

### pyproject.toml
```toml
[project]
name = "my-mcp-server"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["mcp>=0.9.0"]

[project.scripts]
my-mcp = "my_mcp_server:main"
```

### my_mcp_server.py (最小ツール定義)
```python
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

app = Server("my-mcp-server")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="echo",
            description="Echo back the provided text",
            inputSchema={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "echo":
        return [TextContent(type="text", text=f"Echo: {arguments.get('text', '')}")]
    raise ValueError(f"Unknown tool: {name}")

def main():
    asyncio.run(stdio_server(app))

if __name__ == "__main__":
    main()
```

## 登録方法

### ~/.claude.json (推奨, user scope)
```json
{
  "mcpServers": {
    "my-mcp": {
      "command": "node",
      "args": ["/absolute/path/to/dist/index.js"]
    }
  }
}
```

または Python:
```json
{
  "mcpServers": {
    "my-mcp": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/project", "my-mcp"]
    }
  }
}
```

### project scope (.mcp.json)
プロジェクトルートに `.mcp.json` を置く形式。チーム共有可能。

## 動作確認

```bash
# MCP server が登録されたか確認
claude mcp list

# 出力例:
# my-mcp: node /path/to/dist/index.js - ✓ Connected
```

接続失敗時:
1. `claude mcp list` で server 名が表示されるか確認
2. 表示されない → ~/.claude.json or .mcp.json の path/args 確認
3. 表示されるが "Failed" → server 単体起動して確認: `node dist/index.js < /dev/null`
4. stderr に出力していないか確認 (stdio transport は stdout を JSON-RPC で占有するため、debug ログは stderr のみ)

## Anti-Patterns

- ❌ console.log / print を多用 (stdio transport が壊れる、stderr を使う)
- ❌ ツール定義の inputSchema を省略 (Claude が引数を渡せない)
- ❌ HTTP transport を local 開発時に使う (stdio が標準)
- ❌ 起動時の重い初期化 (Claude Code のセッション開始が遅くなる)
- ❌ 同期 I/O (Python なら asyncio、Node なら async/await を徹底)
