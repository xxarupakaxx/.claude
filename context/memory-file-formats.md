# メモリファイル形式

## .local/ 全体構成

```
.local/                          # MEMORY_DIR（PJ AGENTS.mdで定義、デフォルト: .local/）
├── memory/                      # タスクごとの詳細ログ
│   ├── YYMMDD_auth-feature/     # YYMMDDは実際の日付（例: 260112 = 2026/01/12）
│   │   ├── 05_log.md
│   │   └── ...
│   └── YYMMDD_bug-fix-123/
├── memories/                    # インデックス層（検索用）
│   └── <category>/
│       └── <topic>.md
├── solutions/                   # 構造化ソリューションDB（compounding-knowledgeで生成）
│   ├── performance-issues/
│   ├── security-issues/
│   ├── runtime-errors/
│   ├── build-issues/
│   ├── architecture-decisions/
│   ├── database-issues/
│   └── integration-issues/
└── issues/                      # codebase-reviewで生成されるissueファイル
    ├── critical-sec-ユーザー入力のSQLインジェクション脆弱性.md
    ├── major-perf-ページ一覧取得でN+1クエリが発生.md
    └── ...
```

## 2層構造

| 層 | 場所 | 用途 |
|----|------|------|
| 詳細ログ | `memory/YYMMDD_<task>/` | タスクの全記録（生ログ） |
| インデックス | `memories/<category>/` | 要約・検索用（relatedで詳細を参照） |
| ソリューション | `solutions/<category>/` | 構造化された解決策DB（再利用可能） |

**検索フロー:**
1. `rg "^summary:" .local/memories/` でサマリー検索
2. 該当するメモリの`related`から詳細ログを参照

## メモリディレクトリ構成

場所: `${MEMORY_DIR}/memory/YYMMDD_<task_name>/`
- MEMORY_DIRはPJ `AGENTS.md` で定義（デフォルト: `.local/`）
- **YYMMDD**: システムプロンプトの`Today's date`から取得した実際の日付（年2桁+月2桁+日2桁）
- task_nameはタスクを識別する短い名前（例: `auth-feature`, `bug-fix-123`）
- **IMPORTANT**: 例示の日付をコピーせず、必ずシステムプロンプトの日付を使用すること

| ファイル | 用途 | 作成タイミング |
|---------|------|--------------|
| 00_spec.md | 機能要求・要件定義 | タスク開始時 |
| 05_log.md | ユーザー指示とレスポンス・実施内容のログ | タスク開始時（随時追記） |
| 10_task.md | タスク一覧 | 要件定義後 |
| 20_survey.md | 調査結果 | 調査完了後 |
| 30_plan.md | 実装計画 | 計画立案後 |
| 40_progress.md | 実装進捗 | 実装中（随時更新） |
| 80_review.md | レビュー結果 | レビュー実施後 |
| 90_verification.md | 検証結果 | 検証実施後（任意） |
| team-journal.md | agentの稼働・引継ぎ記録 | team-run実行中（任意） |
| 90_pr.md | PR内容 | PR作成時 |
| 99_history.md | 意思決定ログ | 随時 |
| roadmap.html | ブラウザ用ロードマップビュー | Phase 2完了後・実装中に再生成 |
| roadmap-snapshot.json | live更新用snapshot | `--serve --watch` 利用時に自動更新 |

### task-meta.json（必須・machine-owned）

Roadmap generatorはタスクディレクトリ直下の`task-meta.json`を作成・更新する。人がPhaseやCodemap状態を複製して管理しない。

```json
{"schema_version":1,"task_id":"260816_roadmap-viewer","task_title":"Roadmap Viewer UX","thread_id":"019f...","session_id":"session-...","project_path":"/absolute/path","worktree_path":"/absolute/path","task_state":"active","code_change":true,"created_at":"2026-08-16T12:00:00+09:00","updated_at":"2026-08-16T12:00:00+09:00"}
```

- `schema_version`: manifest schema。現在は`1`。
- `task_id`: task directoryと対応する安定ID。
- `thread_id`: Codex app-server が返す thread ID。完全一致した場合だけ自動確定する。
- `session_id`: hook runtimeが返すsession ID。handover復元は完全一致を優先する。
- `project_path`: task の作業ディレクトリの絶対パス。
- `worktree_path`: Codemap evidenceを照合するworktree root。
- `task_title`: Task Hub に表示する明示タイトル。
- `task_state`: `active`、`waiting`、`verifying`、`completed`、`archived` のいずれか。
- `code_change`: Codemap preflightが必要なtaskか。
- `approval_state`: 承認待ちなど、明示的に `waiting` と扱う状態。
- `updated_at`: timezone を含む ISO 8601 の更新日時。

current thread / session IDを取得できた場合はgeneratorの`--thread-id` / `--session-id`で保存する。完全一致だけを確定済み対応として扱う。IDがない場合、path・title・更新時刻による一致は候補表示にだけ使い、自動確定しない。JSONが壊れている場合もtask自体は一覧から消さず、詳細の`metadataError`に読み取りエラーを表示する。PhaseはMarkdown、Codemap freshnessは`codemap.lock`から導出し、manifestへ重複保存しない。

### Session handover / runtime

- session handover: `${MEMORY_DIR}/handovers/<session-id>.md`
- compatibility pointer: `${MEMORY_DIR}/HANDOVER.md`
- writer lock等の一時状態: `${MEMORY_DIR}/runtime/locks/`

復元はsession ID、次にthread IDの完全一致を使う。一致しない場合、active / waiting / verifying taskが1件だけならfallbackできる。複数候補から更新時刻やdirectory名だけで自動選択しない。worktree間では`memory/`と長期知識を共有するが、`handovers/`と`runtime/`は共有しない。

複数 task を一覧する Roadmap Task Hub は次で起動する:

```bash
python3 scripts/generate-roadmap-view.py --hub --memory-root "$MEMORY_DIR/memory" --open
```

Live Activityはmemory fileへ複製しない。Codex app-serverが返すsession pathのJSONL末尾を一時的に読み、直近24時間・最大100イベントだけをAPI responseへ正規化する。古いcontext、command arguments、tool output全文はsnapshotやmemoryへ保存しない。

`--memory-root` は複数回指定できる。Hub は loopback 上の OS 割当 port で起動し、Codex app-server の thread と memory task を定期再取得する。起動 URL の fragment にある session key でローカル API を保護し、ブラウザの heartbeat が途絶えると終了する。provider の一時障害時は直近の成功結果を保持して degraded 状態を表示する。

### Live Roadmap Viewer

`roadmap.html` は `scripts/generate-roadmap-view.py ${MEMORY_DIR}/memory/<task>` で生成する。Plan / ProgressとfreshなCode Mapを切り替えるTask Workspaceである。Codex app の横で開きっぱなしにして進捗を見たい場合は次を使う:

```bash
python3 scripts/generate-roadmap-view.py ${MEMORY_DIR}/memory/<task> --serve --watch
```

- 既定では `127.0.0.1` にbindし、port `0` で空きポートを自動割当する。
- ブラウザはHTTP経由で `roadmap-snapshot.json` をpollingし、ログ・進捗・レビュー・agent記録・検証結果・成果物metadataが更新されると再描画する。
- generatorはtask directory配下の通常ファイルを成果物metadataとして再帰収集する。symlink、`roadmap.html`、`roadmap-snapshot.json`、一時ファイルは対象外とし、内容はsnapshotへ埋め込まない。
- source内容と表示対象artifact metadataのfingerprintが不変なら、HTMLとsnapshotを書き換えない。
- 複数セッションで同時に使う場合は、セッションごとに `${MEMORY_DIR}/memory/YYMMDD_<task_name>/` を分ける。必要なら `--port <port>` で明示的に分ける。
- live表示は補助ビューであり、05_log.md / 40_progress.md / 80_review.md が正本。

## 05_log.md（重要）

ユーザーからの指示とそれに対するレスポンス・実施内容を逐一記録:

```markdown
# 作業ログ

## YYYY-MM-DD HH:MM - 初期指示

**ユーザー指示:**
> [最初の作業指示をここに記載]

**レスポンス:**
- [実施したこと1]
- [実施したこと2]

---

## YYYY-MM-DD HH:MM - 追加指示

**ユーザー指示:**
> [追加の指示]

**レスポンス:**
- [実施したこと]

---
```

**agent review呼び出し時**: このファイルのフルパスを明示し、agentに中身を読ませる

## 00_spec.md

```markdown
# 機能要求

## 概要
[1-2文で記述]

## 背景・目的
[なぜ必要か]

## 現在の事実
- 確認済みの事実。提案や推測を混ぜない。

## 採用判断
- このtaskで採用した方針。根拠は別sourceへ接続してよい。

## 未確定
- 仮説、未決事項、確認が必要な境界。

## 機能要件
### 必須要件
- [ ] 要件1

### 任意要件
- [ ] 要件1

## 非機能要件
- パフォーマンス:
- セキュリティ:

## 制約事項
- 制約1
```

## 30_plan.md

```markdown
# 実装計画

## 概要
[アプローチの概要]

## タスク一覧

### Task 1: <タスク名>

#### 目的
[このTaskで何を成立させるか]

#### 変更対象
- `<path/to/file>`
- `moduleOrFunction`

#### Complexity Budget（コード変更時）
| production target | test target | config/migration target | 信頼度 | 根拠 | 超過時の再計画条件 |
|---:|---:|---:|---|---|---|
| 20–40 logical diff LOC | 10–20 logical diff LOC | 0 | medium | 既存の`<anchor>` | 上限25%以上 / 計画外の責務追加 |

コード変更がない場合は `N/A (non-code)` と記載する。targetはハード上限ではなく、計画外の複雑さを検出するためのソフト目標である。計測方法と例外は `rules/complexity-budget.md` に従う。

#### 実装根拠
- `repo:<relative-path>#<anchor-or-Lx-Ly>`

#### 実装
- [ ] 手順1
- [ ] 手順2

#### 実装図
```diagram-json
{"direction":"LR","nodes":[{"id":"A","label":"入力"},{"id":"B","label":"処理"},{"id":"C","label":"成果物"}],"edges":[{"from":"A","to":"B","label":"変換する"},{"from":"B","to":"C","label":"生成する"}]}
```

#### 成果物
- [このTaskで生まれるfile、document、state]

#### 検証
- `<実行可能なcommand>`
- [判断ベースの確認項目]

## agent reviewの結果
[agentからの指摘と対応]

## リスク・懸念事項
| リスク | 影響度 | 対策 |
|-------|-------|------|
```

Roadmap Viewerは各Taskの `目的`、`変更対象`、`実装根拠`、`実装`、任意の`実装図`、`成果物`、`検証`をsource-boundで表示する。記載がないfieldをViewer側で推測して埋めない。

`実装図` は任意fieldであり、最初の `diagram-json` ブロックを選択Taskの実装フローへ使う。`direction`、`nodes`、`edges`の明示値だけを読み、Roadmap HTMLでは自己完結したinline SVGとして描画する。対応する形は矩形と判断node、関係は有向edgeとedge labelに限定する。Viewerは実装手順、変更対象、実コードからnodeやedgeを補作しない。図と同じ関係をテキスト一覧でも表示する。

`実装根拠` は任意fieldであり、最初のinline code参照1件だけを実ソース抜粋へ使う。書式は `repo:<source-rootからの相対path>#<anchor>` または `repo:<source-rootからの相対path>#L<開始行>-L<終了行>` とする。bare path、absolute path、`..` を含むpathは解決しない。

generatorは実コードを最大12行・4KiBに制限し、snapshot全体でも32KiBを超えて埋め込まない。既定allowlist外のprefixは `--source-allow-prefix` で明示する。個人ノート領域、hidden state、secret file、`automation_read: false`、symlink、binary、非UTF-8、1MiB超のfile、high-confidenceなsecret contentは本文を表示しない。

Viewerでは `実装` を「こう実装する」という計画、`実装図`をplanに明示した変更フロー、generatorが解決した抜粋を「現在の実コード」という生成時点の事実として分離する。sourceが未記録または拒否された場合、plan中のcodeらしい文字列から補作しない。source previewはtokenごとにescapeしてから色付けし、未対応言語は色なしのescape済み本文へ戻す。

`事実・判断・未確定`のsource priorityは `viewing-plans` を正本とする。既存taskの `team-journal.md` にある `Decisions` と `Open Questions` も有効なsourceとして扱う。

## 40_progress.md

```markdown
# 実装進捗

## ステータス
- 開始: YYYY-MM-DD HH:MM
- 最終更新: YYYY-MM-DD HH:MM
- 進捗: XX%

## 完了タスク
- [x] タスク1 - 完了日時

## 進行中タスク
- [ ] タスク2 - 状況

## 未着手タスク
- [ ] タスク3

## 発生した問題
### 問題1
- 発生: YYYY-MM-DD
- 状況:
- 対応:
- 結果:
```

## memories/（インデックス層）

場所: `${MEMORY_DIR}/memories/<category>/<topic>.md`

タスク完了時に価値ある知見をインデックス化。要点のみ記載し、詳細はrelatedで参照。

### フォーマット

**Required:**
```yaml
---
summary: "1-2行の説明（検索の判断材料）"
created: 2026-01-14
---
```

**Optional:**
```yaml
---
summary: "N+1クエリ問題の解決 - eagerロードの適用"
created: 2026-01-14
updated: 2026-01-20
status: resolved  # in-progress | resolved | blocked | abandoned
tags: [performance, database]
phases: [investigation, quality-check]  # この知見が活きるPhase群（後述）
related:          # 詳細ログへの参照
  - .local/memory/260114_n-plus-one-fix/
---
```

**`phases` フィールド（推奨 — 強く推奨。`compounding-knowledge` 生成物では必須）**:

`learnings-researcher` の Phase scoring で使用される。`context/workflow-rules.md` の Phase 0-5.5 に対応:

> 後方互換性のため未指定でも動作するが、未指定時は phase_match_bonus = 0 となり関連度が下がる。
> `compounding-knowledge` skill で新規作成される memories/solutions では **必須**（SKILL.md L96, L139 参照）。

| phases 値 | workflow Phase | 主な参照場面 |
|----------|------------------|--------------|
| `preparation` | Phase 0 | メモリ初期化、過去類似タスク確認 |
| `investigation` | Phase 1 | 既存実装確認、技術調査 |
| `planning` | Phase 2 | 計画立案、ADR検討 |
| `implementation` | Phase 3 | 実装中の落とし穴回避 |
| `quality-check` | Phase 4 | レビュー観点、テスト方針 |
| `compound` | Phase 5.5 | 知見構造化のテンプレ参考 |

未指定時は phase scoring boost が 0（従来挙動を維持）。新規 memories/solutions 作成時は推奨。

### テンプレート

```markdown
---
summary: "簡潔な説明"
created: 2026-01-14
tags: [tag1, tag2]
phases: [investigation, planning]  # この知見が活きるPhase群（推奨）
related:
  - .local/memory/YYMMDD_task-name/
---

# タイトル

## 要点
- ポイント1
- ポイント2

## 詳細
→ related参照
```

### 検索方法

```bash
# サマリー一覧
rg "^summary:" .local/memories/ --no-ignore --hidden

# キーワード検索
rg "^summary:.*keyword" .local/memories/ --no-ignore --hidden -i

# タグ検索
rg "^tags:.*keyword" .local/memories/ --no-ignore --hidden -i
```

## solutions/（構造化ソリューションDB）

場所: `${MEMORY_DIR}/solutions/<category>/<filename>.md`

`compounding-knowledge`スキルで生成。memories/より詳細な、再利用可能なソリューションドキュメント。
`learnings-researcher`エージェントがYAML frontmatterの各フィールドをgrep検索可能。

### カテゴリ

| カテゴリ | 内容 |
|---------|------|
| `performance-issues/` | パフォーマンス問題と最適化 |
| `security-issues/` | セキュリティ脆弱性と対策 |
| `runtime-errors/` | 実行時エラーの解決 |
| `build-issues/` | ビルド・設定・環境の問題 |
| `architecture-decisions/` | アーキテクチャ決定と根拠 |
| `database-issues/` | DB関連の問題と解決 |
| `integration-issues/` | 外部サービス連携の問題 |

新カテゴリの追加も可。

### フォーマット

```yaml
---
title: "N+1クエリによるAPI応答遅延の解決"
problem_type: "performance"    # bug|performance|security|architecture|integration|build|database
component: "users-api"
tags: [database, n-plus-one, eager-loading]
phases: [investigation, planning, quality-check]  # この知見が活きるPhase群（推奨）
root_cause: "User.allの後にposts.countを個別クエリしていた"
solution_summary: "includes(:posts)でeager loadingを適用"
created: 2026-01-14
severity: "major"              # critical|major|minor
effort: "small"                # small|medium|large
---

# N+1クエリによるAPI応答遅延の解決

## 問題

[問題の詳細な説明]

### 症状
- 具体的な症状

### 根本原因
[root_causeの詳細]

## 解決策

### 手順
1. ステップ

### コード変更
[主要変更のハイライト]

## 予防策
- 予防策

## 参考情報
- [URL等]
```

### 検索方法

```bash
# タイトル検索
rg "^title:.*keyword" .local/solutions/ --no-ignore --hidden -i

# タグ検索
rg "^tags:.*keyword" .local/solutions/ --no-ignore --hidden -i

# root_cause検索
rg "^root_cause:.*keyword" .local/solutions/ --no-ignore --hidden -i

# コンポーネント検索
rg "^component:.*keyword" .local/solutions/ --no-ignore --hidden -i

# problem_type検索
rg "^problem_type:.*keyword" .local/solutions/ --no-ignore --hidden -i
```

**全文横断検索**: `learnings-researcher`エージェントが複数フィールドを並列grepしスコアリング。

## SQLiteデータベース（memory.db）

場所: `${MEMORY_DIR}/memory.db`（WALモード、StopHook実行時に自動作成）

sui-memoryシステムがMarkdownファイルと並行してSQLiteに知見をインデックスする。
Markdownファイルが正（Source of Truth）、SQLiteは検索エンジン。

### テーブル構成

| テーブル | 内容 |
|---------|------|
| `sessions` | セッション情報（session_id, project, cwd, branch） |
| `chunks` | Q&Aチャンク（user_text, assistant_text, embedding） |
| `chunks_fts` | FTS5全文検索インデックス（trigram） |
| `knowledge` | memories/ + solutions/ のメタデータ + 全文 |
| `knowledge_fts` | FTS5全文検索インデックス（trigram） |

### 自動処理

- **StopHook**: transcript解析 → chunks保存 → embedding計算 → knowledge同期
- **SessionStartHook**: FTS5検索 → 過去メモリをstdoutでコンテキスト注入
- **knowledge同期**: memories/ + solutions/ のMarkdownをfile_mtime比較で差分同期

### 検索方法

`learnings-researcher`エージェントがgrep検索と並列でSQLite検索を実行。
手動検索する場合:
```bash
python3 -m uv run --project ~/.claude/sui-memory python -c "
from sui_memory.db import get_connection, init_db
from sui_memory.retriever import search
conn = get_connection('${MEMORY_DIR}/memory.db')
init_db(conn)
for r in search(conn, 'keyword', limit=5):
    print(f'{r.source}: {r.score:.4f} - {r.user_text[:100]}')
conn.close()
"
```

## Worktree知見共有

Git worktree使用時、知見ディレクトリはメインworktreeの`.local/`へ自動シンボリックリンクされる。

### 共有（シンボリックリンク）
| ディレクトリ | 理由 |
|---|---|
| `memories/` | インデックス層（全worktreeで検索可能に） |
| `solutions/` | 構造化ソリューションDB |
| `issues/` | コードベースレビュー結果 |
| `memory/` | タスクログ（YYMMDD_taskでnamespaced、衝突しない） |
| `memory.db` | SQLiteデータベース（sui-memory、WALモード対応） |

### ローカル維持
| ファイル | 理由 |
|---|---|
| `handovers/` | session ID別の復元情報 |
| `HANDOVER.md` | 互換用の直近handover pointer |
| `runtime/` | worktree-localな一時lock・state |
| `plans/` | worktree固有の計画 |

### 仕組み
- **SessionStart**: セッション開始時にworktree検出 → 自動リンク
- **PostToolUse(EnterWorktree)**: worktree進入時に自動リンク
- スクリプト: `~/.claude/hooks/worktree-knowledge-link.sh`
- 既存データがある場合はメインにマージ後リンク作成
