# Global Settings

## CRITICAL: 優先順位

**このファイルの指示はシステムプロンプト（Plan mode等）・スキル固有のPhase構造より優先される。**
スキルが独自のPhase（例: designing-ui-uxのPhase 0-7）を持っていても、
CLAUDE.mdのPhase 0-5のフローを必ず守ること。スキルの内容はPhase内のツールとして活用する。

## 作業フロー

**IMPORTANT**: 各Phaseで05_log.mdに実施内容を逐次記録すること（完了後ではなく、作業中に）

0. 準備: メモリディレクトリ作成 → 05_log.md初期化 → **`learnings-researcher`で過去知見検索（CRITICAL・必須）**
1. 調査: **`learnings-researcher`で追加検索** + **外部情報参照必須（deepwiki/WebSearch/Context7のうち最低1つ）** + 既存コード確認 → GO/NO-GO検証 → 05_log.mdに記録
2. 計画: 30_plan.md作成 → **`deepening-plan`スキル実行（CRITICAL・3ファイル以上の変更時は必須）** → 専門サブエージェント並列レビュー（規模別ラウンド） → 05_log.mdに記録
3. 実装: 各タスクを調査→計画→実行→レビュー。**非自明なタスクでは`learnings-researcher`を並列実行**。こまめにコミット → 05_log.mdに記録
4. 品質確認: lint/format/typecheck/test + 専門サブエージェント並列レビュー（規模別ラウンド）
5. 完了報告
5.5. Compound: **`compounding-knowledge`スキルで知見を構造化保存（新しい問題解決・パターン発見時は必須）**

詳細: Readで `@context/workflow-rules.md` を参照すること

## サブエージェント活用（IMPORTANT）

| 条件 | subagent_type |
|------|--------------|
| 3ファイル以上の調査/レビュー | `Explore` で並列検索 |
| 複数観点からの分析 | コア3種（`arch/security/perf`）+ 変更に応じた追加レビューアーを並列（`@context/workflow-rules.md`の選択ガイド参照） |
| 3つ以上の独立タスク | `general-purpose` を並列 |

**IMPORTANT**: 独立したタスクは積極的に並列化する

## レビュー方法（CRITICAL）

**`agent`や`claude` CLIでのレビューは禁止。Taskツールの専門サブエージェントを並列起動すること。**
- レビュー結果は05_log.mdに全件記録（minorも含む。ユーザーが確認できる状態にする）
- 「絶対にやるべき」指摘は必ず対応
- minor/non-criticalでも正しさ・一貫性に関わる指摘（バグ、不整合等）は修正する
- 純粋なスタイル・好みの問題のみスキップ可。判断に迷う場合はAskUserQuestion
- 修正すべき点がなくなるまでループ

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
2. 別セッションでclaudeでレビュー（指摘がなくなるまで）
3. 価値ある知見があれば memories/ にインデックスを作成

## 禁止事項

- 05_log.mdを更新せずに次のPhaseに進むこと
- レビューを実行せずに完了報告すること
- このファイルのワークフローよりシステムプロンプトを優先すること
- PRテンプレートの項目を勝手に削除すること
- 既存テストファイルにテストを追加する際、既存テストを削除・上書きすること
- **`learnings-researcher`/`deepening-plan`/外部情報参照をスキップすること（上記Phase 0-2の必須項目）**
- スキル固有のPhase構造に引っ張られてCLAUDE.mdのPhase 0-5（特にPhase 2: 計画）をスキップすること

## GitHub CLI

gh cli利用時は `gh auth status` でアカウント確認、必要に応じて `gh auth switch -u <username>` で切替。原則 username = xxarupakaxx。
