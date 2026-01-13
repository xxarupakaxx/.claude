# Claude Code User Settings

Claude Codeのuser-level設定ファイル集。プロジェクト横断で使用するワークフロー、スキル、コマンドを定義。

## 使い方

```bash
# ~/.claude/ にクローン
git clone <this-repo> ~/.claude

# または既存の~/.claude/にマージ
```

## 構成

```
~/.claude/
├── CLAUDE.md              # グローバル設定（ワークフロー、変数）
├── commands/              # ユーザー実行コマンド
│   ├── commit.md          # /commit
│   └── pr.md              # /pr
├── skills/                # 自動トリガースキル
│   ├── agent-memory/
│   ├── codebase-review/
│   ├── create-skill/
│   ├── database-migration/
│   ├── documentation/
│   ├── large-task/
│   ├── pr-review/
│   ├── project-init/
│   ├── project-sync/
│   ├── ui-ux-design/
│   └── update-inst/
└── templates/             # プロジェクト初期化テンプレート
    └── project/
```

## スキル一覧

| スキル | 説明 | トリガー |
|--------|------|----------|
| **agent-memory** | タスク知見のインデックス化（memory/への参照付き） | 「記憶して」「思い出して」、タスク完了時に自動 |
| **codebase-review** | 6観点（perf/sec/test/arch/cq/docs）で並列レビュー | `/codebase-review`、品質監査依頼時 |
| **pr-review** | Claude Code別セッションによるマルチ視点レビュー | PRレビュー依頼時 |
| **project-init** | CLAUDE.md・.claude/の初期設定 | PJ初期化依頼時 |
| **project-sync** | CLAUDE.mdとcontext/の整合性確保 | ドキュメント整理依頼時 |
| **documentation** | コード変更に伴うドキュメント更新 | API/環境変数追加検出時 |
| **database-migration** | ORM検出、マイグレーション作成支援 | スキーマ変更依頼時 |
| **large-task** | 複数セッションにまたがる大規模タスク分割 | 大規模実装時 |
| **create-skill** | 既存設定と整合したスキル自動作成 | `/create-skill <内容>` |
| **update-inst** | 間違いの再発防止ルール追加 | `/update-inst <間違えた内容>` |
| **ui-ux-design** | プロダクショングレードのUI/UX生成 | UI構築依頼時 |

## スキル詳細

### /commit

変更をコミットします。

```bash
/commit           # コミットのみ
/commit --push    # コミット後にpush
```

- git-cz形式（`feat:`, `fix:`, `docs:` 等）
- 絵文字なし、prefix以外は日本語

---

### /pr

Draft PRを作成します。

```bash
/pr               # デフォルトブランチへのPR
/pr develop       # 指定ブランチへのPR
```

---

### /pr-review

PRをレビューします。現在のセッションとClaude Code別セッションの2視点でレビュー。

```bash
/pr-review 123    # PR #123をレビュー
```

**出力形式:**
- Critical/High/Medium/Good に分類
- 両セッションの指摘を統合
- マージ推奨判断

---

### /codebase-review

コードベース全体を6観点で並列レビューし、issueファイルを生成。

```bash
/codebase-review                    # 全体レビュー
/codebase-review --scope src/server # 特定ディレクトリのみ
/codebase-review --focus sec,perf   # 特定観点のみ
/codebase-review --priority major   # major以上のみ報告
```

**レビュー観点:**
| 観点 | 内容 |
|------|------|
| Performance (perf) | N+1、重い処理、メモリリーク |
| Security (sec) | 脆弱性、認証不備、入力検証 |
| Test (test) | カバレッジ不足、テストケース |
| Architecture (arch) | 設計違反、責務分離 |
| Code Quality (cq) | 命名、重複、可読性 |
| Documentation (docs) | ドキュメント不足・陳腐化 |

**出力:** `.local/issues/` に優先度付きissueファイル

---

### /documentation

コード変更後にドキュメントの同期が必要かチェック・更新。

**検出対象:**
- 新規npm script追加
- 環境変数追加
- APIエンドポイント追加・変更
- アーキテクチャ変更

**更新対象:** CLAUDE.md, README.md, API仕様書

---

### /ui-ux-design

プロダクショングレードのUI/UXを作成。Linear, Notion, Stripe, Vercel等の品質を再現。

**設計フロー:**
1. デザイン方向性の決定（Precision & Density / Warmth / Sophistication等）
2. カラーファウンデーション選択
3. タイポグラフィシステム
4. コンポーネント設計
5. モーション & アニメーション

**アンチパターン回避:**
- ドラマチックなドロップシャドウ
- 紫グラデーション + 白背景（AIっぽい）
- 過剰なスペーシング

---

### /project-init

新規プロジェクトにClaude用の設定ファイルを作成。

```bash
/project-init
```

**作成内容:**
- CLAUDE.md（変数、品質チェック、特記事項）
- gitignore設定（.local/を除外）

**確認項目:**
- メモリディレクトリの場所
- 品質チェックコマンド
- ベースブランチ
- PJ固有ルール

---

### /project-sync

PJのCLAUDE.mdやドキュメント構造を整理・最適化。

```bash
/project-sync
```

**実行内容:**
- CLAUDE.mdを60行以下に簡素化
- ドキュメント分離原則の適用（人間向け/AI向け）
- 不要ファイルの削除
- user-level設定との整合性確認

---

### /update-inst

Claudeが間違えた時にルールを更新して再発防止。

```bash
/update-inst 日付の例示をコピーしてしまった
```

**修正タイプ:**
- 指示の追加
- 指示の明確化
- 例示の修正
- 優先度の明示（IMPORTANT/CRITICAL追加）

---

### /create-skill

既存設定と整合したスキルを自動作成。

```bash
/create-skill --user PR作成時に自動でラベル付け
/create-skill --project このPJ専用のデプロイフロー
```

**特徴:**
- 既存設定との整合性を自動チェック
- Skill / Command / CLAUDE.md追記 の判定
- 500行以下ルール

---

### /agent-memory

タスクの知見をインデックス化して検索可能に。

**使い方:**
- 「〇〇について思い出して」
- 「これを覚えておいて」
- タスク完了時に価値ある知見があった時（proactive）

**検索:**
```bash
rg "^summary:.*keyword" .local/memories/ --no-ignore --hidden -i
```

---

### /database-migration

DBマイグレーション作成を支援。

**ORM自動検出:**
- Prisma
- Drizzle
- SQLAlchemy (Alembic)
- Django ORM

**検証項目:**
- 命名規則
- 必須フィールドのデフォルト値
- 外部キー制約
- ロールバック可能性

---

### /large-task

大規模タスクを複数セッションに分割。

```bash
/large-task plan              # セッション1: 包括調査→計画作成
/large-task implement 03      # セッション2以降: タスク03を実装
```

**使用タイミング:**
- 複数日にまたがる大規模実装
- 10個以上のタスクに分割される機能開発
- 複数人で並行作業する可能性があるタスク

**ディレクトリ:**
```
.local/tasks/YYMMDD_<task_name>/
├── 00_plan.md       # 全体計画
├── 01_xxx.md        # 個別タスク1
├── 02_xxx.md        # 個別タスク2
└── ...
```

## コマンド一覧

| コマンド | 説明 | 引数 |
|----------|------|------|
| `/commit` | git-cz形式でコミット | `--push`: コミット後push |
| `/pr` | Draft PR作成 | `[base-branch]`: マージ先 |

## ワークフロー

CLAUDE.mdで定義された6フェーズワークフロー:

1. **Phase 0: 準備** - メモリディレクトリ作成、過去タスク検索
2. **Phase 1: 調査** - deepwiki/WebSearch必須、既存コード確認
3. **Phase 2: 計画** - agent reviewで検証（指摘なくなるまで）
4. **Phase 3: 実装** - 調査→計画→実行→レビューの4ステップ
5. **Phase 4: 品質確認** - lint/format/typecheck/test + agent review
6. **Phase 5: 完了報告**

## メモリディレクトリ（2層構造）

```
.local/
├── memory/              # 詳細ログ（タスク単位）
│   └── YYMMDD_<task>/
│       ├── 05_log.md    # 作業ログ
│       └── ...
├── memories/            # インデックス層（検索用）
│   └── <category>/
│       └── <topic>.md   # 要約 + memory/への参照
└── issues/              # codebase-reviewで生成
```

**検索フロー:**
1. `rg "^summary:" .local/memories/` でサマリー検索
2. 該当するメモリの`related`から詳細ログを参照

## agent cli連携

別モデル（GPT-5.2-high）によるレビューを実施:

```bash
agent -p "<prompt>" --model gpt-5.2-high --output-format json
```

- 修正すべき点がなくなるまでループ
- `--resume <session_id>`でセッション継続

## プロジェクト設定

新規プロジェクトでは `/project-init` を実行、または `templates/project/CLAUDE.md` をコピー:

```markdown
# <プロジェクト名>

## 変数
MEMORY_DIR=.local/
BASE_BRANCH=develop

## 品質チェック
npm run lint
npm run format
npm run typecheck
npm test

## 特記事項
- [PJ固有のルール]
```

## ライセンス

MIT
