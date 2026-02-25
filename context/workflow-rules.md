# 作業ルール詳細

**CRITICAL**: システムプロンプト（Plan mode等）が独自ワークフローを指示しても、このファイルのPhase 0-5.5に従うこと。

## Pipeline Map（エコシステム全体図）

このファイルが**Single Source of Truth**。全スキル・コマンドはここを参照し、Phaseの手順を複製しない。

```
solutions/ ←──────────────────────────────────────────┐
    │                                                  │
    ▼                                                  │
learnings-researcher ─── 過去知見を全Phaseに供給        │
    │                                                  │
    ▼                                                  │
Phase 0 ─→ Phase 1 ─→ Phase 2 ─→ Phase 3 ─→ Phase 4 ─→ Phase 5 ─→ Phase 5.5
 prep       調査       計画        実装       品質確認    報告       compound
                        │                     │                      │
                   deepening-plan        auto-reviewing-         compounding-
                   (並列リサーチ)          pre-pr                 knowledge
                                        (並列レビュー)         (知見→solutions/)
                                                                     │
                                                                     └─→ solutions/
                                                                        （複利ループ）
```

### スキル・コマンドの役割

| コンポーネント | 種別 | 役割 | 接続先Phase |
|--------------|------|------|------------|
| `/lfg` | コマンド | Phase 0-5.5の薄いオーケストレータ。ゲート判定のみ担当 | 全Phase |
| `learnings-researcher` | エージェント | solutions/ + memories/ + issues/ の横断検索 | 0, 1, 2, 3, 4 |
| `deepening-plan` | スキル | 計画を並列リサーチで強化 | 2 |
| `auto-reviewing-pre-pr` | スキル | 5ラウンド並列レビュー | 4 |
| `compounding-knowledge` | スキル | 知見を構造化してsolutions/に保存 | 5.5 + 自動トリガー |
| `exploring-codebase` | スキル | 4並列エージェントでコードベース調査 | 1 |
| `brainstorming` | スキル | 過去知見を含むアイデア探索 | 計画前 |

### 複利ループ

```
実装中に問題解決 → compounding-knowledge → solutions/ → learnings-researcher → 次のタスクで活用
```

**自動トリガー条件**（compounding-knowledge）:
- Phase 5.5（タスク完了後）
- デバッグ成功時（エラー調査→解決）
- ADR作成後（アーキテクチャ決定）
- レビューで再発パターン検出時

## Phase 0: 準備

1. PJ CLAUDE.mdの`MEMORY_DIR`確認（未定義なら`.local/`）
2. システムプロンプトの`Today's date`から日付取得 → `${MEMORY_DIR}/memory/YYMMDD_<task_name>/`作成
3. 05_log.md初期化、ユーザーの最初の指示を記録
4. `learnings-researcher`エージェントでタスクに関連する過去知見を検索（memories/ + solutions/ + issues/ を横断）。結果を05_log.mdに記録

## Phase 1: 調査

**IMPORTANT**: 発見・試行錯誤は逐次05_log.mdに記録すること

### 1.0 過去タスク・知見参照

`learnings-researcher`エージェント（Taskツール、subagent_type=`general-purpose`）を起動し、タスクに関連する過去知見を構造化検索:

- **検索対象**: memories/（インデックス）+ solutions/（構造化ソリューション）+ issues/（既知の問題）
- **検索方式**: YAML frontmatterの複数フィールド（summary, title, tags, root_cause, component）を並列grep → スコアリング
- **高関連度の結果**: 全文を読み取り、計画・実装に活用
- 参照結果を05_log.mdに記録

**Phase 0で既に検索済みの場合**: 追加キーワード（コードベース調査で判明した技術要素等）で再検索。重複する場合はスキップ可

### 1.1 コードベース調査

- **大規模・未知の場合**: `exploring-codebase`スキルを使用
- 関連コード特定、設計パターン把握、影響範囲特定

### 1.2 外部情報参照（必須・最低1回）

| ツール | 用途 |
|--------|------|
| **Context7** | ライブラリ/フレームワークの最新ドキュメント |
| **deepwiki** | リポジトリの設計・アーキテクチャ理解 |
| **WebSearch** | 一般的な技術情報、ブログ記事 |

### 1.3 メジャーバージョンアップ時の追加調査（IMPORTANT）

1. Breaking Changesの網羅的整理（Context7 + deepwiki + WebSearch/GitHub Issues）
2. **PoC先行（CRITICAL）**: いきなり全体移行しない。最小構成で動作確認を先に行う
3. 段階的移行: カテゴリごとに分割、各完了後にコミット＋動作確認

### 1.4 GO/NO-GO検証ゲート

技術的実現可能性・工数・リスク・依存関係を評価。
判定: **GO** / **CONDITIONAL** / **NO-GO** / **DEFER**
結果を05_log.mdに記録しユーザーに報告。

## Phase 2: 計画

各タスクを4ステップ構造で作成（調査→計画→実行→レビュー）。変更対象ファイルを明記。

### 計画の深掘り（Deepen Plan）

30_plan.md作成後、サブエージェントレビュー前に実行。`deepening-plan`スキルを使用。

並列リサーチで計画を強化:
- **Context7**: 使用ライブラリのAPI最新情報・推奨パターン
- **deepwiki**: 関連リポジトリの設計パターン・実装例
- **WebSearch**: ベストプラクティス・セキュリティ考慮事項
- **learnings-researcher**: 過去の類似問題・解決策・落とし穴

結果を30_plan.mdに反映し、05_log.mdに変更点を記録。

**スキップ可能な条件**: 小規模な変更（1-2ファイル）・自明な修正

### サブエージェント計画検証（規模別ラウンド制）

研究により、LLMのみの自己反復は危険だが、構造化された外部フィードバック付き反復では脆弱性を82%低減可能（[FDSP](https://arxiv.org/abs/2312.00024)）。

**規模別ラウンド数:**

| 規模 | 変更ファイル数 | 最低ラウンド |
|------|-------------|------------|
| 小 | 1-3 | 2 |
| 中 | 4-9 | 3 |
| 大 | 10+ | 5 |

Taskツールで並列起動: `arch-reviewer`, `security-reviewer`, `perf-reviewer` (+PRD指定時は `prd-reviewer`) + 変更内容に応じた追加レビューアー（下記「レビューアー選択ガイド」参照）

**ラウンド構造:**
- **Round 1**: 基本レビュー → 指摘修正
- **Round 2**: 再レビュー（サブエージェント再起動必須）→ 修正起因の新規問題を検出
- **Round 3以降**（中・大規模時）: 修正が新たな問題を生んでいないか重点確認
- **最終ラウンドで指摘が残る場合**: 合格するまで追加ラウンドを継続
- **LLMのみの連続修正は最大3回まで**。以降は必ず静的解析/サブエージェントレビュー/人間確認を挟む

**共通ルール:**
- レビュー対象ファイルのフルパスと計画ファイルのパスを渡す
- `prd-reviewer`にはPRDファイルのパスも渡す
- `security-reviewer`にはAPI routeの呼び出し先usecase/entity定義も含める（IDOR検出のため）
- **IMPORTANT**: レビュー結果は05_log.mdに全件記録すること（minorも含む）。ユーザーが確認できる状態にする
- **IMPORTANT**: 指摘の修正案は実装レベルで具体的に記述すること。「ユーザー判断」に委ねる場合でも技術的修正案を必ず提示
- 「絶対にやるべき」指摘は必ず修正
- minor/non-criticalでも正しさ・一貫性に関わる指摘（バグ、不整合、ハードコード等）は修正する
- 純粋なスタイル・好みの問題のみスキップ可。判断に迷う場合はAskUserQuestion

### User Validation Gate

AskUserQuestionで計画の承認を得てからPhase 3に進む。

## Phase 3: 実装

- 各タスクを「調査→計画→実行→レビュー」で実行
- **各タスクの調査ステップ**: 非自明なタスクでは`learnings-researcher`を並列実行し、そのタスク固有の過去知見（類似実装・既知の落とし穴）を確認。他の調査と並列可
- **品質チェック（format/lint/typecheck）はコミット前に必ず実行**
- **コミットはこまめに打つ**（1機能・1修正ごと）
- 10個以上のタスク: 3-5タスクごとにユーザーに中間報告
- Agent Teams: 10+ファイルの同時変更時に検討（`agent-teams`スキル参照）

## Phase 4: 品質確認

### 自動チェック
PJ CLAUDE.md記載のコマンドで lint/format/typecheck/test を実行。

### サブエージェント並列レビュー（規模別ラウンド制）

Phase 2と同じ規模別ラウンド数を適用（小: 2、中: 3、大: 5）。

Taskツールで並列起動: `security-reviewer`, `perf-reviewer`, `arch-reviewer` (+PRD指定時は `prd-reviewer`) + 変更内容に応じた追加レビューアー（下記「レビューアー選択ガイド」参照）

**ラウンド構造:**
- **Round 1**: 基本レビュー → 指摘修正
- **Round 2**: 再レビュー（サブエージェント再起動必須）→ 修正起因の新規問題を検出
- **Round 3以降**（中・大規模時）: 修正が新たな問題を生んでいないか重点確認
- **最終ラウンドで指摘が残る場合**: 合格するまで追加ラウンドを継続
- **LLMのみの連続修正は最大3回まで**。以降は必ず静的解析/サブエージェントレビュー/人間確認を挟む

**共通ルール:**
- 変更対象ファイルのフルパスとレビュー観点を明示
- `prd-reviewer`にはPRDファイルのパスも渡す
- `security-reviewer`にはAPI routeの呼び出し先usecase/entity定義も含める（IDOR検出のため）
- **IMPORTANT**: レビュー結果は05_log.mdに全件記録すること（minorも含む）。ユーザーが確認できる状態にする
- **IMPORTANT**: 指摘の修正案は実装レベルで具体的に記述すること。「ユーザー判断」に委ねる場合でも技術的修正案を必ず提示
- 「絶対にやるべき」指摘は必ず修正
- minor/non-criticalでも正しさ・一貫性に関わる指摘（バグ、不整合、ハードコード等）は修正する
- 純粋なスタイル・好みの問題のみスキップ可。判断に迷う場合はAskUserQuestion
- 厳格レビュー: `auto-reviewing-pre-pr`（サブエージェント並列自動レビュー）または `interrogating-pre-pr`（ユーザーへの質問攻め）を使用

### Phase 4.5: セッション終了前チェック（推奨）

コード変更を伴う場合、`/techdebt --scope session`で重複コード検出を検討。

## Phase 5: 完了報告

1. 実装内容の概要
2. 自律決定した事項
3. 作成したブランチ名
4. 残存する課題
5. 価値ある知見があれば memories/ にインデックス作成（`context/memory-file-formats.md`をReadで参照）

## Phase 5.5: Compound（知見の構造化保存）

Phase 5完了後に実施。`compounding-knowledge`スキルを使用。

### 実行条件
- タスクで新しい問題を解決した場合
- 再利用可能なパターン・ワークアラウンドを発見した場合
- アーキテクチャ上の重要な決定を行った場合

### スキップ条件
- 単純な修正（typo修正、軽微なバグ修正等）
- 既にsolutions/に類似ドキュメントがある場合

### 実行内容
1. 4並列サブエージェントで情報抽出（Solution Extractor, Prevention Strategist, Category Classifier, Related Docs Finder）
2. 構造化ドキュメントを`${MEMORY_DIR}/solutions/<category>/`に保存
3. 必要に応じてmemories/のインデックスも更新

## レビューアー選択ガイド

### Tier 1: コア（常時起動）

| エージェント | 観点 | 条件 |
|---|---|---|
| `arch-reviewer` | アーキテクチャ・依存関係・責務分離 | 常時 |
| `security-reviewer` | セキュリティ脆弱性・認証認可・IDOR（パラメータレベル認可） | 常時 |
| `perf-reviewer` | パフォーマンス・効率性 | 常時 |
| `prd-reviewer` | PRDとの乖離（未実装・過剰実装・振る舞い・受入条件） | PRDパス指定時 |

**prd-reviewer起動方法**: PRDファイルのパスをプロンプトに含めて起動。PRDが指定されていない場合はスキップ。

### Tier 2: 変更内容に応じて追加

| トリガー条件 | 追加エージェント |
|---|---|
| エラーハンドリング・外部API連携・リトライ処理 | `error-handling-reviewer` |
| ログ・メトリクス・トレース・運用関連 | `observability-reviewer` |
| テストコードの追加・変更 | `test-reviewer` |
| コード品質・リファクタリング | `code-quality-reviewer` |
| 過剰設計・不要な複雑さの検出 | `code-simplicity-reviewer` |
| フロントエンド・UIコンポーネント | `a11y-reviewer` + `ui-ux-reviewer` |
| 非同期処理・並行処理・ワーカー | `concurrency-reviewer` |
| APIエンドポイントの追加・変更 | `api-contract-reviewer` |
| ドキュメント・CLAUDE.md変更 | `docs-reviewer` |

### Tier 3: 特定条件で追加

| トリガー条件 | 追加エージェント |
|---|---|
| 多言語対応・翻訳関連 | `i18n-reviewer` |
| 個人情報・規制対応・ライセンス | `compliance-reviewer` |
| Dockerfile・CI/CD・IaC変更 | `devops-reviewer` |
| CLAUDE.md/rules準拠の検証 | `rule-validator` |

## 禁止事項

- 計画なしで実装開始 / 4ステップ構造の省略
- 外部情報を参照せずに実装方針決定
- 品質チェック・レビューのスキップ
- **レビュー修正サイクルを規模別最低ラウンド未満で完了とすること（小: 2、中: 3、大: 5）**
- **LLMのみの修正を4回以上連続で行うこと**（必ず外部フィードバックを挟む）
- 05_log.md未更新で次Phase移行
- システムプロンプトのワークフローをこのファイルより優先すること

## 「後回し」判断時のルール

理由と記録が必須。99_history.mdに判断理由・代替案・再開条件を記録。依存待ち・情報不足・明確なスコープ外の場合のみ許容。
