---
name: codebase-review
description: コードベース包括的レビュー。6観点（perf/sec/test/arch/cq/docs）を並列サブエージェントで実行し、優先度付きissueファイルをメモリディレクトリに生成。
context: fork
---

# コードベース包括的レビュー

## 概要

コードベース全体を6つの観点から並列でレビューし、発見した問題点を優先度付きのissueファイルとして記録する。

## トリガー条件

- ユーザーが `/codebase-review` を実行した場合
- コードベース全体のチェック・監査を依頼された場合
- リリース前の品質確認を依頼された場合

## レビュー観点

| 観点 | 略語 | 説明 |
|------|------|------|
| Performance | perf | N+1、不要な再レンダリング、重い処理等 |
| Security | sec | 脆弱性、認証・認可、入力検証等 |
| Test | test | テストカバレッジ、テストケース不足 |
| Architecture | arch | 責務分割、依存関係、設計パターン |
| Code Quality | cq | 命名、一貫性、可読性、不要コード |
| Documentation | docs | ドキュメント不足、内容の陳腐化 |

## 優先度定義

| 優先度 | 略称 | 説明 | 対応期限 |
|--------|------|------|---------|
| critical | crit | 即座に対応必須（本番障害、重大脆弱性） | 即時 |
| major | maj | 早期対応推奨（バグ、セキュリティリスク） | 次リリースまで |
| minor | min | 改善推奨（設計改善、技術的負債） | 計画的に対応 |
| trivial | triv | 余裕があれば対応（軽微な改善） | 任意 |

※ アルファベット順でソートすると正しい優先度順になる

## 実行手順

### Phase 0: 準備

1. ディレクトリの確認・作成

```bash
# PJ CLAUDE.mdのMEMORY_DIRを確認（未定義なら.local/）
# システムプロンプトのToday's dateから日付を取得（例示をコピーしない）
mkdir -p ${MEMORY_DIR}/memory/YYMMDD_codebase-review
mkdir -p ${MEMORY_DIR}/issues
```

2. 05_log.mdを初期化

3. PJのCLAUDE.mdとcontext/を確認し、アーキテクチャルールを把握

4. **コードベース構造の把握**

```bash
# ディレクトリ構造を取得
find . -type d -not -path '*/node_modules/*' -not -path '*/.git/*' | head -100

# 主要ファイルタイプの分布を確認
find . -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.py" -o -name "*.md" \) \
  -not -path '*/node_modules/*' | wc -l
```

### Phase 1: 並列サブエージェント実行

---
**親エージェント（Claude Code）への警告**

サブエージェントプロンプト作成時に以下を**絶対に守ること**:

1. `--skip-multimodel` オプションが**明示的に指定されていない限り**、タスク3（agent cliによる並行レビュー）の指示を**削除・省略してはならない**
2. 「時間短縮」「コスト削減」「効率化」を理由にした自己判断でのスキップは**禁止**
3. サブエージェントプロンプトには必ず**タスク1〜4すべて**を含めること

**違反した場合**: レビューは不完全とみなされ、ユーザーに説明責任が発生する

---

**CRITICAL**: 6つのサブエージェントを**同時に**起動する。Taskツールを1つのメッセージで6回呼び出す。

**CRITICAL**: サブエージェントは必ず `subagent_type=general-purpose` を使用すること。
- `Explore`エージェントはファイル探索専用でWriteツールを持たないため、issueファイルを作成できない
- `general-purpose`エージェントは全ツール（Read, Write, Grep, Glob, Bash, WebSearch, deepwiki等）にアクセス可能

各サブエージェントには以下の情報を渡す:
- メモリディレクトリのフルパス
- PJ CLAUDE.mdの内容（アーキテクチャルール等）
- 対象リポジトリのパス
- 担当観点とレビュー基準
- **コードベース構造情報**（Phase 0で取得）

**各サブエージェントのプロンプト構成:**
1. 共通テンプレート: `Read templates/shared-template.md` の内容を使用
   - フルパス: `~/.claude/skills/codebase-review/templates/shared-template.md`
   - タスク1〜4、issueファイル形式、注意事項を含む
2. 観点別詳細指示: `Read templates/perspective-prompts.md` から担当観点の指示を挿入
   - フルパス: `~/.claude/skills/codebase-review/templates/perspective-prompts.md`
   - 共通テンプレートの `## あなたの担当観点` セクションに該当観点の内容を挿入する

### Phase 2: 結果の集約

サブエージェント完了後:

1. issuesディレクトリのファイルを集計

```bash
ls -la ${MEMORY_DIR}/issues/
```

2. マルチモデル検証の統計を集計（各issueファイルから）

3. サマリーファイルを作成

### Phase 3: サマリー作成

```markdown
# コードベースレビュー サマリー

## 実行日時
YYYY-MM-DD HH:MM

## 統計

| 優先度 | 件数 |
|--------|------|
| crit   | X    |
| high   | X    |
| mid    | X    |
| low    | X    |
| **合計** | **X** |

| 観点 | crit | high | mid | low | 計 |
|------|------|------|-----|-----|-----|
| perf | X | X | X | X | X |
| sec  | X | X | X | X | X |
| test | X | X | X | X | X |
| arch | X | X | X | X | X |
| cq   | X | X | X | X | X |
| docs | X | X | X | X | X |

## マルチモデル検証結果
- 両者一致（高信頼度）: X件
- Claude Codeのみ検出: X件
- agent cliのみ検出 → 採用: X件
- 優先度差異あり: X件

## Critical Issues（要即時対応）
...

## High Priority Issues（要早期対応）
...

## 推奨対応順序
...
```

### Phase 4: ユーザーへの報告

サマリーを提示し、以下を確認:
- 優先度の妥当性
- 対応の優先順位
- GitHub issueへの登録要否

## ファイル構成

```
${MEMORY_DIR}/
├── memory/
│   └── YYMMDD_codebase-review/
│       ├── 05_log.md          # 作業ログ
│       └── summary.md         # レビューサマリー
└── issues/                    # issueファイル（マルチモデル検証済み）
    ├── critical-*.md          # 各issueにマルチモデル検証結果を含む
    ├── major-*.md             # アルファベット順で優先度順にソート
    ├── minor-*.md
    └── trivial-*.md
```

## オプション引数

```
/codebase-review [options]

--scope <path>      対象ディレクトリを限定（例: src/server）
--focus <観点>      特定の観点のみ実行（例: sec,perf）
--priority <level>  指定優先度以上のみ報告（例: high）
--github            issueをGitHubに登録
--skip-multimodel   agent cli並行レビューをスキップ（Claude Codeのみ）
```

## 注意事項

- サブエージェントは必ず並列で起動する（順次実行しない）
- 各サブエージェントは独立して動作し、他のエージェントの結果を待たない
- issueファイルのタイトル部分は日本語で具体的に記述
- 同じ問題が複数の観点に該当する場合、最も重要な観点で1つだけ作成
- 優先度critは慎重に使用（本当に即時対応が必要な場合のみ）
- **コードベース全体を網羅的に確認すること（一部だけ見て終わりにしない）**
- **問題発見時はdeepwiki/WebSearchでベストプラクティスを必ず調査**
- **CRITICAL: agent cli呼び出しは `--skip-multimodel` オプションが明示的に指定されない限り必須。自己判断でのスキップは禁止**
- **サブエージェントプロンプトには共通テンプレート全体（タスク1〜4すべて）を含めること。観点別の詳細指示のみでは不十分**
