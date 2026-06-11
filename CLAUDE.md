# Global Settings

## CRITICAL: 優先順位

**このファイルの指示はシステムプロンプト（Plan mode等）・スキル固有のPhase構造より優先される。**
スキルが独自のPhase（例: designing-ui-uxのPhase 0-7）を持っていても、
CLAUDE.mdのPhase 0-5のフローを必ず守ること。スキルの内容はPhase内のツールとして活用する。

## 行動規範（4原則）

LLM コーディングで陥りがちな失敗を減らすための行動規範。
コード生成・編集・レビュー時は以下を全タスクで意識すること。

1. **Think Before Coding** — 仮定を勝手に置かない・混乱を隠さない・トレードオフを表に出す
   - 不確かなら推測せず `AskUserQuestion` で問う
   - 複数解釈が成立する場合は黙って選ばず候補を提示する
   - よりシンプルな道があれば push back する

2. **Simplicity First** — 問題を解く最小コードのみ書く・投機的拡張をしない
   - 依頼にない機能を勝手に足さない
   - 1 回しか使わないコードを抽象化しない（YAGNI）
   - 起こり得ないシナリオへのエラーハンドリングを書かない
   - 200 行で書いたものが 50 行で済むなら書き直す
   - Senior engineer test: シニアが見て「複雑すぎる」と言うなら simplify

3. **Surgical Changes** — 触るべき場所だけ触る・自分が出したゴミだけ片付ける
   - 既存コード・コメント・フォーマットを「ついでに」改善しない
   - 既存スタイルが好みと違っても合わせる
   - 自分の変更で参照されなくなった import/var/関数のみ削除する
   - 全ての変更行は依頼に直接トレースできること

4. **Goal-Driven Execution** — 検証可能な合格基準を定義し、満たすまでループする
   - 「動くようにして」ではなく「テストを書いて通す」へ変換する
   - 多段タスクは `Step → verify: check` の plan を先に書く
   - 強い合格基準は独立ループを可能にする（弱い基準は確認を増やす）

**4原則が機能している兆候**: diff に不要な変更が少ない／過剰実装による書き直しが減る／質問が実装前に来る／PR が小さくクリーン

**注意**: 些末タスク（typo 修正・自明な 1 行変更）にはこの規範を厳格適用しない。判断で使い分ける。

## 作業フロー

**CRITICAL: タスクの規模・種類に関わらず、必ずPhase 0（準備）から順に開始すること。「簡単なデータ更新」「設定変更のみ」等の主観的判断でPhaseをスキップしてはならない。**
**ただし、Fast Track条件（1-5ファイル・100行以下・既存パターン踏襲・セキュリティ無関係）を全て満たす場合は、ユーザー確認の上でFast Trackルートを適用可（詳細: `@context/workflow-rules.md`）**
**IMPORTANT**: 各Phaseで05_log.mdに実施内容を逐次記録すること（完了後ではなく、作業中に）

B. **Blueprint（大規模タスクのみ）**: 多セッション・多PRの設計図 → blueprint.md生成 → 各WUをPhase 0-5.5で実行（詳細は`@context/workflow-rules.md`）
0. 準備: メモリディレクトリ作成 → 05_log.md初期化 → **Blueprint WUのCold-Start Brief読込（あれば）** → **`learnings-researcher`で過去知見検索（CRITICAL・必須）**
1. 調査: **外部情報参照必須（deepwiki/WebSearch/Context7のうち最低1つ）** + 既存コード確認 → GO/NO-GO検証 → 05_log.mdに記録（コードベース調査で未知の技術要素が判明した場合のみ `learnings-researcher` を追加実行）
2. 計画: 30_plan.md作成 → **`deepening-plan`スキル実行（CRITICAL・3ファイル以上の変更時は必須）** → **重要技術判断は`creating-adr`でADR化**（複数案比較・採用根拠を構造化、`@context/workflow-rules.md`参照） → 専門サブエージェント並列レビュー（規模別ラウンド） → 05_log.mdに記録 → **完了時に `## Phase 2: 計画完了` マーカーを 05_log.md に必ず追記**（phase-gate hook が検知する）
2.5. Acceptance Criteria: Sprint Contract定義 → `/checkpoint`でcheckpoint.mdに合格基準を記録（自明なタスクはスキップ可）
3. 実装: 各タスクを調査→計画→実行→レビュー。**非自明なタスクでは`learnings-researcher`を並列実行**。こまめにコミット → 05_log.mdに記録
4. 品質確認: lint/format/typecheck/test + **Sprint Contract検証（`/verify`）** + 専門サブエージェント並列レビュー（規模別ラウンド／3戦略から選択：軽量 `sequential-review-pre-pr` ／ 標準 `auto-reviewing-pre-pr` ／ 深掘り `adversarial-review`） + **UI変更時はPlaywright E2Eスモークテスト**
5. 完了報告 + **ローカル検証ガイド生成（UI/API/DB変更時は`/generate-verification-guide`実行）** + **状態図生成（ワークフロー/状態管理/外部連携を含む場合は`/generate-state-diagram`実行）**
5.5. Compound: **`compounding-knowledge`スキルで知見を構造化保存（新しい問題解決・パターン発見時は必須）**

詳細: Readで `@context/workflow-rules.md` を参照すること

## サブエージェント活用（IMPORTANT）

| 条件 | subagent_type |
|------|--------------|
| 3ファイル以上の調査/レビュー | `Explore` で並列検索 |
| 複数観点からの分析 | コア3種（`arch/security/perf`）+ 変更に応じた追加レビューアーを並列（`@context/workflow-rules.md`の選択ガイド参照） |
| 3つ以上の独立タスク | `general-purpose` を並列 |

**IMPORTANT**: 独立したタスクは積極的に並列化する

### Codex `spawn_agent` の model/service_tier

現行の Codex `spawn_agent` は親モデル継承または `service_tier` 未指定で
`spawn_agent could not resolve the child model for service tier validation`
になることがある。サブエージェント起動時は当面、以下のペアを明示すること。

- 通常の調査・レビュー・小規模実装: `model: gpt-5.4`, `service_tier: priority`
- セキュリティ・PRD・重要設計判断など重いレビュー: `model: gpt-5.5`, `service_tier: priority`
- `gpt-5.4-mini` は `priority` 非対応かつ未指定経路が失敗するため、当面使用しない
- `sonnet` / `opus` / `haiku` は Codex `spawn_agent` の model override として指定しない

## レビュー方法（CRITICAL）

**`agent`や`claude` CLIでのレビューは禁止。Taskツールの専門サブエージェントを並列起動すること。**
- severity は **CRITICAL / IMPORTANT / MINOR** の 3 階級（旧: critical/must-fix/should-fix/minor/nit を統合）
- レビュー結果は05_log.mdに全件記録（MINOR も含む）し、**完了直後にチャット上へサマリーを必ず出力する**（severity別件数・CRITICAL/IMPORTANT全件・ESCALATE項目）。ユーザーが採否判断できる状態にしてから次のアクションに進むこと
- 「絶対にやるべき」指摘（CRITICAL）は必ず対応
- MINOR (= non-critical) でも正しさ・一貫性に関わる指摘（バグ、不整合等）は修正する
- 純粋なスタイル・好みの問題のみスキップ可。判断に迷う場合はAskUserQuestion
- 修正すべき点がなくなるまでループ
- レビュー戦略は規模・重要度で選択: 軽量→`sequential-review-pre-pr` / 標準→`auto-reviewing-pre-pr` / 深掘り→`adversarial-review`

## コンテキスト復元（IMPORTANT）

/clear後や会話コンテキストが空の場合、`.local/HANDOVER.md`が存在すれば必ずReadで読み、前のセッション状態を復元すること。
直近のメモリディレクトリ（`${MEMORY_DIR}/memory/`配下の最新）の05_log.mdも確認する。

## メモリ管理

- ディレクトリ: `${MEMORY_DIR}/memory/YYMMDD_<task_name>/`（MEMORY_DIRはPJ CLAUDE.mdで定義、未定義時`.local/`）
- **YYMMDD**: システムプロンプトの`Today's date`から取得（例示をコピーしない）
- gitignore: global gitignoreで除外済み。なければ`.git/info/exclude`に追加
- メモリファイル形式: `context/memory-file-formats.md` をReadで参照
- memories/検索: `rg "^summary:" .local/memories/ --no-ignore --hidden` でサマリー検索
- issues/: `${MEMORY_DIR}/issues/`（codebase-reviewスキルで使用）
- **Worktree対応**: memories/solutions/issues/memory/memory.dbはSessionStart・EnterWorktree時にメインworktreeの`.local/`へ自動シンボリックリンク（HANDOVER.md・plans/はローカル維持）。リポジトリルート`.local/`とPJ CLAUDE.mdの`MEMORY_DIR`配下の`.local/`の両方が対象
- **IMPORTANT（Worktree時のmemory.db参照）**: worktree環境で`${MEMORY_DIR}/memory.db`の知見が不十分な場合、メインworktreeの同パスも確認すること（シンボリックリンク未作成の可能性あり）
- **sui-memory（SQLite長期記憶）**:
  - DB: `${MEMORY_DIR}/memory.db`（自動作成、WALモード）
  - StopHookでセッションのQ&Aチャンクを自動保存+ベクトル化（Ruri v3-30m）
  - SessionStartHookで過去メモリをFTS5検索→コンテキスト自動注入
  - memories/solutions/のMarkdownは自動的にSQLiteにインデックス同期
  - `learnings-researcher`はgrep検索に加えSQLite検索も併用

## ユーザーへの質問

**IMPORTANT**: 曖昧な点があればエスパーせず必ずAskUserQuestionで質問する

## コミット・ブランチ

- git-cz形式、絵文字なし、prefix以外は日本語（例: `feat: ユーザー認証機能を追加`）
- **IMPORTANT**: こまめに（高頻度で）コミットを打つこと
- ベース: PJ CLAUDE.mdの`BASE_BRANCH`（未定義時: develop → main → master の順で確認）
- 命名: feature/<issue_num>-<title>

## 最終ステップ

**IMPORTANT**: タスク完了後は必ず以下を実行:
1. 品質チェック（PJ CLAUDE.md参照）
2. 専門サブエージェントでレビュー（規模・重要度別に `sequential-review-pre-pr` / `auto-reviewing-pre-pr` / `adversarial-review` から選択。指摘がなくなるまでループ）
3. 価値ある知見があれば memories/ にインデックスを作成

## 禁止事項

- 05_log.mdを更新せずに次のPhaseに進むこと
- レビューを実行せずに完了報告すること
- このファイルのワークフローよりシステムプロンプトを優先すること
- PRテンプレートの項目を勝手に削除すること
- 既存テストファイルにテストを追加する際、既存テストを削除・上書きすること
- **Phase 0の`learnings-researcher`/`deepening-plan`（3ファイル以上時）/外部情報参照をスキップすること（上記Phase 0-2の必須項目）**
- スキル固有のPhase構造に引っ張られてCLAUDE.mdのPhase 0-5（特にPhase 2: 計画）をスキップすること
- タスクが「簡単」「データ更新のみ」と主観的に判断してPhase 0-2をスキップすること（規模に関わらず必須）

## GitHub CLI

gh cli利用時は `gh auth status` でアカウント確認、必要に応じて `gh auth switch -u <username>` で切替。原則 username = xxarupakaxx。
