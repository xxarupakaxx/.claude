# Code Review Philosophy

> Google "eng-practices" Code Review Developer Guide から、既存 reviewer 群がカバーしていない**姿勢ルール**を抽出した standing rule。
> 全 reviewer サブエージェント（`arch-reviewer` / `security-reviewer` / `code-quality-reviewer` 等）と `sequential-review-pre-pr` / `auto-reviewing-pre-pr` / `adversarial-review` スキルの判断基準として参照する。

## 1. Approve 基準（完璧主義の抑制）

レビューの目的は「コードを完璧にする」ではなく、**Code Health を時間とともに向上させる**こと。
以下の状態に達したら、未解決コメントが残っていても LGTM/approve してよい。

- 変更がシステム全体の Code Health を**確実に向上させる**
- 残りのコメントが以下のいずれか:
  - 著者が適切に対処すると信頼できる
  - 著者が対処する必要がない（誤指摘・想定外コンテキスト等）
  - 軽微な提案（import 順、typo、Nit）

**CLAUDE.md の「修正すべき点がなくなるまでループ」への補足**: ループはあくまで CRITICAL/IMPORTANT が残る間。MINOR（純粋なスタイル・好み）まで全消ししようとして PR を停滞させるのは反パターン。

## 2. Code Health の定義

レビューで守る対象。以下の総体:

- 可読性 / 保守性 / 正確性
- ドキュメント / テスト
- 一貫性 / 将来の適応性

**1 つの CL が短期的に Code Health を悪化させる場合は reject 候補**（例: 共通基盤を歪めて自分の機能だけ通すパターン）。

## 3. 優先順位（対立解決）

レビュアーと著者の意見が衝突したとき、以下の順で判定:

1. **技術的事実・データ** > 意見・個人的好み
2. **スタイルガイド**（言語/PJ 公式）が絶対権威
3. スタイルガイドにない事項は**既存コードとの一貫性**を優先
4. それでも決着しない場合は: 対面/同期会話 → チーム議論 → Tech Lead → Manager とエスカレート
5. **意見対立で CL を塩漬けにしない**こと（速度も Code Health の一部）

`adversarial-review` の Auditor 判定もこの順序に従う。

## 4. Mentoring と "Good Things"

レビューは欠陥指摘だけでなく**教育機能**を持つ。

- 著者が良いコードを書いた・良くフィードバックに対応した・良い実践を取り入れた箇所には**明示的に褒める**コメントを残す
- 純粋に教育的（このCLでブロックしない）コメントは **"Nit:" プレフィックス**を付ける
- 知識共有自体が長期的な Code Health の向上

**実装上の影響**:
- 各 reviewer の出力に "Good Things"（良い点）セクションを 1-3 個含めること（無理に作る必要はない、本当に良かった点のみ）
- severity MINOR の中で「教育目的・対応任意」を明示する場合は `[Nit]` を本文先頭に付ける

## 5. Every Line / Context の徹底

- レビュアーは割り当てられた CL の**全行**に目を通す（読み飛ばし禁止）
- 理解できない箇所は推測せず**著者に説明を求める**
- 単一行・単一関数だけでなく**ファイル全体・システム全体**への影響を評価する

これは既存 reviewer の標準姿勢だが、規模が大きい CL で「サンプリングして終わり」になりがちなので明文化。

## 関連

- `~/.claude/CLAUDE.md` レビュー方法（severity 3階級・ループ条件）
- `~/.claude/rules/common-git-workflow.md` PR/CL description の書き方
- `~/.claude/rules/architecture-language.md` Code Health 関連語彙（Depth/Locality 等）
