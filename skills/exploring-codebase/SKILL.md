---
name: exploring-codebase
description: コードベースの構造・パターン・依存関係を3つの並列Exploreサブエージェントで深堀り調査。新しいPJの理解、機能追加前の影響範囲調査、アーキテクチャ把握に使用。「コードベースを調べて」「アーキテクチャを理解したい」「影響範囲を調査して」「構造を把握したい」等の依頼に対応。
---

# コードベース深堀り探索

3つの専門Exploreサブエージェントを並列起動し、コードベースを多角的に調査する。

## 既存設定との関係

- **Phase 0-5（@context/workflow-rules.md）**: Phase 1（調査）の補完。通常のExplore探索より深い多角的調査が必要な場合に使用
- **メモリディレクトリ（@context/memory-file-formats.md）**: 結果を05_log.mdに記録
- **codebase-review**: レビュー（品質問題の検出）ではなく、理解（構造の把握）が目的

## 使用場面

- 新しいコードベースへのオンボーディング
- 機能追加・変更前の影響範囲調査
- 既存アーキテクチャの理解
- リファクタリング対象の全体像把握

## ワークフロー

### Step 1: 探索対象の特定

ユーザーの指示から以下を抽出:
- **探索対象ディレクトリ**: デフォルトはプロジェクトルート
- **関心事・キーワード**: 特定の機能、モジュール、技術要素（あれば）
- **探索の深さ**: quick / medium / thorough（デフォルト: medium）

### Step 2: 3つのExploreサブエージェントを並列起動

**CRITICAL**: Taskツールで以下3つを**同時に**起動する（subagent_type="Explore"）。

各エージェントには以下の情報を渡す:
- 探索対象ディレクトリのフルパス
- 関心事・キーワード（あれば）
- 探索の深さ（thoroughness level）
- エージェント定義ファイルの内容（調査項目・出力形式）

#### Agent 1: Architecture Explorer

**エージェント定義**: `~/.claude/agents/architecture-explorer.md`

**プロンプトテンプレート**:
```
以下のコードベースのアーキテクチャを探索・分析してください。

探索対象: {target_dir}
関心事: {keywords}（なければ全体像把握）
深さ: {depth}

~/.claude/agents/architecture-explorer.md の調査項目・出力形式に従って調査してください。
エージェント定義ファイルを最初に読み込んでから作業を開始すること。
```

#### Agent 2: Data Flow Tracer

**エージェント定義**: `~/.claude/agents/data-flow-tracer.md`

**プロンプトテンプレート**:
```
以下のコードベースのデータフローを追跡・分析してください。

探索対象: {target_dir}
関心事: {keywords}（なければ主要フローを追跡）
深さ: {depth}

~/.claude/agents/data-flow-tracer.md の調査項目・出力形式に従って調査してください。
エージェント定義ファイルを最初に読み込んでから作業を開始すること。
```

#### Agent 3: Dependency Mapper

**エージェント定義**: `~/.claude/agents/dependency-mapper.md`

**プロンプトテンプレート**:
```
以下のコードベースの依存関係を分析・マッピングしてください。

探索対象: {target_dir}
関心事: {keywords}（なければ全体の依存関係を分析）
深さ: {depth}

~/.claude/agents/dependency-mapper.md の調査項目・出力形式に従って調査してください。
エージェント定義ファイルを最初に読み込んでから作業を開始すること。
```

### Step 3: 結果の統合

3つのサブエージェントの結果を以下の形式で統合:

```markdown
# コードベース探索結果

## サマリー
[1-3行で全体像。技術スタック、主要な構成パターン、特筆すべき特徴]

## Architecture
[Agent 1の結果をそのまま記載]

## Data Flow
[Agent 2の結果をそのまま記載]

## Dependencies
[Agent 3の結果をそのまま記載]

## 注目ポイント
- [3つのエージェントの結果を横断して、特に重要な発見を箇条書き]

## 追加調査が必要な箇所
- [深堀りすべき箇所があれば記載]
```

### Step 4: 記録と報告

1. **メモリディレクトリが存在する場合**: 統合結果を05_log.mdに追記
2. **ユーザーへの報告**: サマリーと注目ポイントを中心に簡潔に報告
3. **詳細が必要な場合**: 各セクションの深堀りを提案

## 探索の深さガイド

| 深さ | Explore thoroughness | 所要時間目安 | 用途 |
|------|---------------------|-------------|------|
| quick | quick | 短い | 技術スタックとディレクトリ構成の概要把握 |
| medium | medium | 中程度 | 標準的なコードベース理解 |
| thorough | very thorough | 長い | 詳細なアーキテクチャ分析、移行前の徹底調査 |

## 部分探索モード

特定のモジュール・機能に絞って探索する場合:
- 探索対象ディレクトリを絞る（例: `src/auth/`）
- 関心事を具体的に指定（例: 「認証フロー」「決済処理」）
- 必要なエージェントのみ起動してもよい（例: データフローのみ）

## Agent Teams連携

`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` が有効な場合、`~/.claude/agents/` の定義をTeamメンバーとして直接使用可能。大規模コードベースではAgent Teamsでの並列探索がより効果的。

## 既存設定への参照

- @context/workflow-rules.md（Phase 1との連携）
- @context/memory-file-formats.md（05_log.mdへの記録）
