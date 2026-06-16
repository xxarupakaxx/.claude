---
name: create-subagent
description: 自然言語の要件から ~/.codex/agents/<name>.toml 雛形を生成するメタスキル。TOML（name/description/model/service_tier/developer_instructions）+ 起動条件 + 出力フォーマット + Tier 1/2/3レビュー姿勢 + スコアリングルーブリックを含むベストプラクティス準拠の雛形を作る。使用タイミング: (1) 新しいサブエージェントを追加したいとき、(2) /create-subagent <要件> 実行時、(3) 「サブエージェントを作って」「専門エージェントを追加」「reviewer を作って」等の依頼時。create-skill の派生としてエージェント定義に特化。
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion
---

# Create Subagent

自然言語の要件から `~/.codex/agents/<name>.toml` 雛形を生成するメタスキル。

## 既存設定との関係

- **rules/model-routing.md**: Agent Tool の model 選択方針に従う
- **rules/architecture-language.md**: 用語統一（Module/Interface/Depth 等）
- **create-skill**: スキル生成の姉妹スキル。本スキルはエージェント生成に特化

## ワークフロー

### Step 1: 要件パース

```
入力: /create-subagent dependency-graph を可視化する専門エージェント
→ 名称候補: dependency-graph-visualizer
→ 役割: 依存グラフ抽出 + 可視化
→ tier 判定（後述）
```

不明点があれば AskUserQuestion で確認:
- 役割（レビュー / 探索 / 生成 / 評価）
- 起動条件（自動 / 明示呼び出し）
- 出力形式（issue file / inline summary / structured JSON）

### Step 2: Tier 判定（CRITICAL）

| Tier | 役割例 | TOML既定 / spawn時 |
|------|--------|-------|
| Tier 1 | アーキ/性能レビュー（標準・常時呼ばれる） | TOML既定は `gpt-5.4` + `priority`、spawn時は通常省略 |
| Tier 2 | 品質・テスト・観測性・a11y 等の追加レビュー | TOML既定は `gpt-5.4` + `priority`、spawn時は通常省略 |
| Tier 3 | セキュリティ・PRDレビュー・複雑判断 | TOML既定は `gpt-5.5` + `priority`、spawn時は通常省略 |
| Explorer | ファイル検索・パターンマッチ | TOML既定は `gpt-5.4` + `priority`、spawn時は通常省略 |

判定指針: `~/.claude/rules/model-routing.md` を参照。

### Step 3: name / description 設計

**name 規約:**
- 小文字・ハイフン・数字のみ（64文字以下）
- 役割を即座に判別できる名前（例: `dependency-mapper`, `api-contract-reviewer`）
- 既存 `~/.codex/agents/` と重複しないこと（Glob で確認）

**description 規約（CRITICAL）:**
- 3人称・1024文字以内・XMLタグ不可
- 「何を」「いつ呼ばれるか」「トリガー語」を含める
- 例: `セキュリティ観点でコードをレビュー。SQLインジェクション、XSS、CSRF、認証・認可の不備、機密情報のハードコード等を検出。`

### Step 4: 雛形生成

`Read references/agent-template.md` を参照しテンプレートを取得し、以下を埋める:

1. **TOML metadata**: name / description / model / service_tier
1. **developer_instructions**: 起動条件・入力・出力・評価姿勢を含む本文
2. **Do Not Trust Preamble**: レビュー系エージェントには必ず挿入
3. **評価姿勢セクション**: 懐疑姿勢・見逃しコスト・自作物への甘さ排除・証拠主義
4. **スコアリングルーブリック**: 観点 × 重み × 1/3/5 評価基準（レビュー系のみ）
5. **レビュー項目 or 実行手順**
6. **優先度判断基準**: CRITICAL / IMPORTANT / MINOR
7. **出力形式**: issue file path or inline format

### Step 5: 配置と確認

- 配置先: `~/.claude/agents/<name>.md`
- 既存ファイル上書き時は AskUserQuestion で確認
- 作成後、起動方法（`Agent(subagent_type: "<name>")` 指定例）を報告

## 設計原則

### Tools 選定（最小権限）

| 役割 | 推奨tools |
|------|-----------|
| レビュー専門 | `Read, Grep, Glob, WebSearch, Write` |
| 探索専門 | `Read, Grep, Glob` |
| 生成・編集 | `Read, Write, Edit` |
| 外部情報必要 | 上記 + `WebSearch, WebFetch` |

**禁止**: 不要に `Bash` を含めない（権限最小化）。

### color 規約（視認性）

| 系統 | color |
|------|-------|
| セキュリティ・破壊系 | red |
| アーキ・設計 | purple |
| 性能・最適化 | yellow |
| 探索・調査 | blue |
| 品質・テスト | green |

### memory: user vs project

- ユーザー横断で再利用 → `user`
- PJ固有のルールを内包 → `project`

## Anti-Patterns

- **Tool の取りすぎ**: `Bash` を漫然と付与しない（最小権限）
- **description に1人称**: "I can review..." は不可。3人称で記述
- **トリガー曖昧**: 「いつ呼ばれるか」が読み手に伝わらない description
- **model の不要な明示指定**: 通常は `model` を省略し親セッションのモデルを継承させる
- **Do Not Trust Preamble 省略**: レビュー系エージェントでは必須
- **スコアリングルーブリック欠如**: レビュー系で「主観評価のみ」は禁止
- **既存と重複**: 同名・同責務エージェントを増殖させない

## チェックリスト

- [ ] name は小文字ハイフン形式・既存と衝突なし
- [ ] description は3人称・1024文字以内・トリガー語を含む
- [ ] TOMLのmodel/service_tier、または例外的なspawn overrideは rules/model-routing.md に整合
- [ ] tools は最小権限
- [ ] レビュー系は Do Not Trust Preamble を含む
- [ ] レビュー系はスコアリングルーブリックを含む
- [ ] 優先度判断基準（CRITICAL/IMPORTANT/MINOR）を含む
- [ ] 出力形式が明示されている

## 関連スキル・ルール

- `create-skill` — スキル生成の姉妹（本スキルはエージェント生成版）
- `create-hook` — Hook 雛形生成
- `create-mcp-server` — MCPサーバ雛形生成
- `~/.claude/rules/model-routing.md` — model override 判断基準
- `~/.claude/rules/architecture-language.md` — 共通語彙
- 既存例: `~/.codex/agents/security-reviewer.toml`, `~/.codex/agents/arch-reviewer.toml`
