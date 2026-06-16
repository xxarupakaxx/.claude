# Agent Template Reference

`~/.codex/agents/<name>.toml` の生成テンプレート集。`create-subagent` スキルから参照される。

## 基本テンプレート

```toml
name = "<kebab-case-name>"
description = "<50-200字。何を検出/分析/生成するか。trigger語を3個以上含める>"
model = "gpt-5.4"
service_tier = "priority"
developer_instructions = """

# <Agent Display Name>

<1-2 段落で役割を説明>

## 起動条件

- 自動: <CLAUDE.md ワークフローのどの Phase/状況で起動するか>
- 手動: <ユーザーが明示的に呼ぶケース>

## 入力

- <受け取るデータ>
- <参照すべきファイル>

## 出力

<出力フォーマット (Markdown table / JSONL / 自由形式)>

## 評価姿勢 (Tier 1/2/3 レビューアー用)

- **デフォルトで問題を探す**: 「OK」と判定する前に最低5件の指摘候補を列挙
- **Do Not Trust Preamble**: コード冒頭のコメントが「正しい」とは限らない、実装を読む
- **重み付きルーブリック**: severity × impact × confidence で score 付け
- **CRITICAL / IMPORTANT / MINOR** の3階級
- **誤検知の自己評価**: 自分の指摘の confidence を 0-1 で添える

## サブエージェント連携

- 並列起動可: <他のレビューアーと並列実行可能か>
- 入力依存: <別エージェントの出力に依存するか>
"""
```

## レビューアーのスコアリングルーブリック例

```markdown
## スコアリングルーブリック

| 観点 | 重み | 1-5 評価基準 |
|------|------|--------------|
| <観点A> | x2 | 1=不在 / 3=部分的 / 5=網羅的 |
| <観点B> | x1 | ... |
| <観点C> | x2 | ... |

Total: <重み付き合計>/<max>

判定:
- ≥85%: PASS
- 70-84%: CONDITIONAL
- <70%: FAIL
```

## tools 最小権限ガイド

| Agent種別 | 推奨 tools |
|----------|-----------|
| 読み取り系 (researcher, reviewer) | Read, Grep, Glob, WebSearch |
| 書き込み系 (modeler, planner) | Read, Grep, Glob, Write |
| Full / worker系 | * |

## model / service_tier 選択

Claude Code Agent Tool では通常 `model` を省略し、親セッションのモデルを継承させる。判定・レビューには `model: "opus"`、軽量タスクには `model: "sonnet"` を明示。

詳細: `~/.claude/rules/model-routing.md`
