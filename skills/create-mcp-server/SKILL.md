---
name: create-mcp-server
description: MCPサーバーの最小雛形をTypeScriptまたはPythonで作り、stdioツール、登録例、`claude mcp list`による確認まで案内する。独自MCPや「MCPの雛形を作って」という依頼に使う。
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion, Bash
---

# Create MCP Server

独自MCPサーバーの最小構成を生成する。言語・配置先・最初のツール仕様が不明なときだけ質問し、既存の設定やファイルを調べてから書き込む。

## 要件とテンプレート

次を確定する。

- **言語**: TypeScript（`@modelcontextprotocol/sdk`）またはPython（`mcp`）。Web APIラッパーや既存JavaScriptにはTypeScript、データ処理や既存PythonにはPythonを選ぶ。
- **scope**: user（既定の `~/mcp/<name>/`）または project（`./mcp/<name>/`）。
- **tool**: 名前、入力schema、1行の振る舞い。

選んだ言語の完全な雛形は [references/mcp-templates.md](references/mcp-templates.md) の該当セクションだけを読む。TypeScriptは`package.json`、`tsconfig.json`、stdioの`src/index.ts`、Pythonは`pyproject.toml`とstdioのserverを含め、最低1つの`inputSchema`付きtoolを作る。

## 生成時の不変条件

- stdio transportを使う。stdoutはJSON-RPC専用とし、ログはstderrへ出す。
- tool定義に`inputSchema`を含める。同期的な長時間処理や不要に重い依存は避ける。
- packageの実runtime entrypointと`main`/`start`を一致させ、`command`と`args`には絶対pathを使う。
- user設定（環境に応じた`~/.claude/settings.json`または`~/.claude.json`）またはprojectの`.mcp.json`へ登録例を示す。Codexで使う場合は`~/.codex/config.toml`の`[mcp_servers.<name>]`に`command`、`args`、必要なら`startup_timeout_sec`を示す。
- 既存設定を上書きしない。既存MCPとの名前衝突を確認する。
- `~/.codex/config.toml`などのsecretを含み得る設定をそのまま表示・転記しない。

## 確認と引き渡し

生成後、ユーザーが実行できる次の確認手順を提示する。

```bash
# TypeScript
npm install && npm run build

# Python（プロジェクトの管理方法に合わせる）
uv sync   # または pip install -e .

# 登録確認
claude mcp list

# stdio起動確認（サーバーが入力待ちになればよい）
node dist/index.js < /dev/null
```

プロジェクトのpackage managerや既存testに合わせてコマンドを置き換える。設定変更後はClaude Codeまたは対象セッションの再起動が必要である。`npm test`、`npm run build`、またはPythonの既存checkを、依頼範囲で実行できる場合に実行し、未実行は未実行と報告する。

## 禁止

- stdioのstdoutへdebug出力する。
- `inputSchema`を省略する。
- 未確認のSDK APIやUI経路を捏造する。
- `scripts/`や既存設定を無断で書き換える。
- 新しいMCPの登録を、ユーザーが意図したscopeや承認を越えて行う。
