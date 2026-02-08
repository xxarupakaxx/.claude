---
name: create-skill
description: 既存設定と完全に整合したスキルを自動作成。~/.claude/CLAUDE.md、context/*.md、既存スキルを自動参照し、重複・競合を避けたスキルを生成。使用タイミング: (1) 新しいスキルを作りたい場合、(2) /create-skill --user または --project 実行時。「スキルを追加して」「新しいスキルを作って」「SKILLを作成したい」等の依頼に対応。SKILL.md（YAML frontmatter付き）を生成。
model: opus
allowed-tools: Read, Write, Glob, Grep
---

# Create Skill

既存のuser-level/project-level設定と整合性が取れたスキルを自動作成する。

## 使い方

```
/create-skill <内容>                 # user scope（デフォルト）
/create-skill --user <内容>          # user scope（明示）
/create-skill --project <内容>       # project scope
```

## ワークフロー

### Step 1: 引数パース

```
入力: /create-skill --project 大規模タスク分割ワークフロー
→ scope: project
→ 内容: 大規模タスク分割ワークフロー
```

### Step 2: 既存設定の読み込み（必須）

**常に読み込む:**
- `~/.claude/CLAUDE.md` - user-level設定
- `~/.claude/context/*.md` - 特に以下が重要:
  - `claude-customization-guide.md` - Skills/Commands/CLAUDE.mdの使い分け
  - `workflow-rules.md` - Phase 0-5ワークフロー
  - `memory-file-formats.md` - メモリディレクトリ構造

**--project時に追加で読み込む:**
- `./CLAUDE.md` - project-level設定
- `./context/*.md` - project-level参照ファイル

**既存スキルの確認:**
- `~/.claude/skills/*/SKILL.md` のfrontmatter（name, description）を取得
- 重複・競合がないか確認

### Step 3: Skill vs Command vs CLAUDE.md 判定

@context/claude-customization-guide.md に従い判定:

| 選択 | 条件 |
|------|------|
| **Skill** | 自動トリガー、ドメイン知識、スクリプト同梱 |
| **Command** | ユーザー制御、引数必須、ショートカット |
| **CLAUDE.md追記** | 常時適用ルール、60行以下に収まる |

### Step 4: 整合性チェック

1. **ワークフローとの整合**: Phase 0-5、4ステップ構造との関係
2. **ディレクトリ構造**: MEMORY_DIR、memory/、tasks/等との整合
3. **既存スキルとの重複**: 同じ機能を持つスキルがないか
4. **スコープ判定**: user vs project（@context/claude-customization-guide.md参照）

問題があればAskUserQuestionで確認。

### Step 5: スキル設計

**設計原則:**
参照: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices

**命名規則（CRITICAL）:**
- **gerund形式**（verb + -ing）を使用
- Good: `implementing-kysely`, `processing-pdfs`, `reviewing-prs`, `managing-databases`
- Bad: ~~`kysely`~~, ~~`pdf`~~, ~~`pr-review`~~, ~~`database`~~
- 小文字・数字・ハイフンのみ（64文字以下）

**description（CRITICAL）:**
- **3人称**で記述（"I can..." や "You can..." は避ける）
- 「**何をするか**」+「**いつ使うか**」を含める
- 最大1024文字
- XMLタグ（`<` や `>`）は含めない
- ユーザーが言うかもしれない**具体的なタスク・フレーズ**を含める
- 関連する場合は**ファイルタイプ**に言及する

**description例:**
```yaml
# Good（3人称 + What + When + 具体的タスク）
description: Reviews pull requests for code quality and security. Use when PR number or branch is specified, or when review is requested. "PRをレビューして" "コードレビューお願い" 等の依頼に対応。

# Bad（1人称、Whenがない、具体的タスクなし）
description: I can review PRs.
```

**その他:**
- SKILL.mdは**500行以下**
- 詳細は別ファイルに分割（参照は**1階層のみ**）
- 既存設定を`@context/xxx.md`形式で参照（重複記載しない）

### Step 6: スキル作成

**配置先:**
- `--user`: `~/.claude/skills/<skill-name>/`
- `--project`: `./.claude/skills/<skill-name>/`

**構造（Progressive Disclosure）:**
```
<skill-name>/
├── SKILL.md              # Level 2: トリガー時ロード（500行以下）
└── references/           # Level 3: 必要時のみロード
    └── detail.md
```

### Step 7: 確認

作成後、以下を報告:
- 作成したファイル一覧
- 既存設定との関係
- 使い方の例

## SKILL.md テンプレート

```yaml
---
name: <skill-name>
description: <何をするか>。<いつ使うか>。使用タイミング: (1) xxx、(2) yyy。
---

# <Skill Name>

[1-2文で概要]

## 既存設定との関係

- **Phase 0-5（@context/workflow-rules.md）**: [補完/拡張/独立]
- **メモリディレクトリ（@context/memory-file-formats.md）**: [既存構造を使用/拡張]

## ワークフロー

[具体的な手順]

## 既存設定への参照

- @context/workflow-rules.md
- @context/memory-file-formats.md
```

## 禁止事項

- 既存設定との整合性確認なしでスキル作成
- 既存スキルと重複する機能の作成
- **名詞形のスキル名**（`kysely`ではなく`implementing-kysely`）
- **1人称のdescription**（"I can..."、"You can..."）
- SKILL.mdに500行以上記載
- references/内で更にファイル参照（1階層まで）
- descriptionに「いつ使うか」がない

## チェックリスト

- [ ] ~/.claude/CLAUDE.md を読んだか
- [ ] ~/.claude/context/claude-customization-guide.md を確認したか
- [ ] 既存スキル一覧を確認したか
- [ ] Skill/Command/CLAUDE.md追記の判定をしたか
- [ ] **スキル名がgerund形式か**（implementing-xxx, processing-xxx）
- [ ] **descriptionは3人称か**（"I can..."は不可）
- [ ] descriptionに「何を」「いつ」が含まれるか
- [ ] descriptionにXMLタグ（`<` `>`）が含まれていないか
- [ ] descriptionにユーザーが言いそうな具体的タスク・フレーズが含まれるか
- [ ] 関連する場合、descriptionにファイルタイプが言及されているか
- [ ] SKILL.mdは500行以下か
- [ ] @context/xxx.md 形式で参照を記載したか
