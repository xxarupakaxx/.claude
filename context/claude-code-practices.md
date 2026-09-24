# Claude Codeの実装・運用規律

実装、作業用ファイル、エラー処理、Skill起動の詳細を定める。作業規模は `context/workflow-rules.md` で選び、Phase記録やtask-level workflow checkは管理する作業に適用する。

## 実装と検証

- 終了する非対話型テストは `python3 ~/.claude/scripts/quiet-run.py -- <元のコマンド>` で実行し、成功時の出力を節約する。終了コードとテスト範囲を維持し、失敗時は保存ログの必要箇所だけ読む。共通実装・適用外・保存方針は `~/.codex/context/quiet-test-output.md`。元のコマンドに必要な承認や権限は省略しない。
- 実装前に仮定、不明点、複数解釈、重要な trade-off を明示する。永続的な仕様判断は既存実装、test、文書、またはユーザー確認を根拠にする。
- 要求を満たす最小の実装を選び、依頼外の機能、抽象化、設定、将来対応を足さない。シニアが見て「複雑すぎる」と言う実装は書き直す。
- 対象に必要な行だけを変更し、無関係な整形、refactor、削除を行わない。
- 成功条件を検証可能にし、変更に対応する再現、test、差分確認で完了を判定する。管理する作業ではtask-level workflow checkも含める。
- 再現 test は観測済みの失敗と既存契約だけを固定し、未確認の出力形式やerror型を新しい期待値にしない。既存 test file へ追加する際に既存 test を削除・上書きしない。
- Markdown を変更したら全文を再読し、矛盾、重複、rule漏れを同じturnで解消する。
- 文書・仕様書・ガイド・レポート・画面文言などの成果物を作成・修正したら、最終確認で `skills/sanitizing-artifacts/SKILL.md` を必ず適用する。

実装の基本は「仮定を明示する / 最小を選ぶ / 触るべき場所だけ触る / 検証可能な合格基準まで進める」の4原則である。TypeScript の Before/After 実例は `skills/karpathy-examples/EXAMPLES.md` にある。typo 修正や自明な1行変更へ厳格適用しない。

## 指示と知識の配置

- sessionをまたぐ情報はMemoryだけに置かず、git管理された正本へ反映する。
- 現在の仕様はdocs、検証可能な期待はtest、局所例外は隣接comment、判断理由はADR、反復手順はSkill、未完了作業はissue、履歴はGit logに置く。
- `CLAUDE.md`には全Agentが毎回守る不変条件と正本への入口だけを置く。完了済みTODOや手順の複製を残さない。
- 例外には理由、適用範囲、解除条件を付け、条件が満たされたら削除する。
- 一過性の下書きや受け渡しはworktreeの`.local/context/`に置き、`.context/`、`/tmp`、`/private`を標準置き場にしない。task workflowの記録は`${MEMORY_DIR:-.local}/memory/`に置く。複数行や構造化内容は実ファイルで渡し、inline展開とhere-docを避け、pipeは単一commandがstdinを即時に一度だけ読む処理に限る。

## Script とerror

- 長時間実行や外部通信を伴うscriptは、開始、反復、retry、完了、失敗をsecretなしで記録する。
- 主経路の失敗を暗黙fallbackで隠さない。代替経路は目的、発動条件、観測log、再実行時の挙動を明示する。
- errorを一致なし、context不一致、path不存在、conflict、dirty state、検証failureなど意味で分類し、原因を確認してから続行する。

## Skill Invocation Policy

必須の適用条件があるSkillはその条件に従い、それ以外はタスクに応じて選ぶ。 重い harness / Superpowers 風の flow は、ユーザーが明示したとき、または高価値で複数ターンの実装に必要なときだけ使う。

起動権は次の2層に分ける。

- **User-invoked**: `team-run`、`orchestrate`、`grill-me`、`blueprint`、`skill-governance`、`graph-engineering`、PRD化、issue分解、外部Skillの採用・更新・廃止、外部投稿やPR作成など、作業の進路や外部状態を大きく変えるもの。ユーザーの明示、または短い確認を挟んで使う。
- **Model-invoked**: `research`、`tdd`、`diagnosing-bugs`、`reviewing-code`、`modeling-domains`、`verification-loop`、`consult-gpt` など、現在の作業を小さく安全に進める規律。タスクに合う場合だけ使い、結果を短く報告する。

ルーティングに迷うときは `ask-skill-router` を読む。 原則は、巨大な自動flowに載せる前に、要求の不一致、共有語彙、TDD/feedback loop、設計の泥団子化のどれが実際のボトルネックかを切り分けること。
Superpowers は強い道具だが既定の process gate ではない。
