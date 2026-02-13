# カスタムエージェント定義リファレンス

## ファイル配置

```
~/.claude/agents/<name>.md
```

## Frontmatter仕様

```yaml
---
name: agent-name          # 必須: エージェント名
description: 説明文        # 必須: 用途説明（日本語可）
tools: Read, Grep, Glob   # 必須: 使用可能ツール（カンマ区切り）
model: opus               # 任意: 使用モデル（sonnet/opus/haiku）
color: purple             # 任意: 表示色
---

# システムプロンプト

ここにエージェントへの指示を記述
```

## 有効なカラー値

| 値 | 説明 |
|----|------|
| `red` | 赤 |
| `blue` | 青 |
| `green` | 緑 |
| `yellow` | 黄 |
| `purple` | 紫（magentaの代替） |
| `orange` | オレンジ |
| `pink` | ピンク |
| `cyan` | シアン |
| `gray` | グレー |

**注意**: `magenta`はサポートされていない。`purple`を使用すること。

## 使用可能ツール

| ツール | 用途 |
|--------|------|
| `Read` | ファイル読み取り |
| `Write` | ファイル書き込み |
| `Edit` | ファイル編集 |
| `Grep` | テキスト検索 |
| `Glob` | ファイルパターン検索 |
| `Bash` | コマンド実行 |
| `WebSearch` | Web検索 |
| `WebFetch` | Webページ取得 |
| `Task` | サブエージェント起動 |
| `AskUserQuestion` | ユーザーへの質問 |

## 呼び出し方法

Taskツールで`subagent_type`に指定:

```
Task(subagent_type="arch-reviewer", prompt="...")
```

## 例: レビュワーエージェント

```yaml
---
name: security-reviewer
description: セキュリティ観点でコードをレビュー。SQLインジェクション、XSS等を検出。
tools: Read, Grep, Glob, WebSearch, Write
model: opus
color: red
---

# Security Reviewer

セキュリティ観点でコードベースをレビューする専門エージェント。

## レビュー項目

- SQLインジェクション
- XSS（クロスサイトスクリプティング）
- 認証・認可の不備
...
```
