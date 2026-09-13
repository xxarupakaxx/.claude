---
name: design-reviewer
description: "`.kiro/specs/feature/design.md`をrequirements・既存構成・interface・前提・非機能・テストの11観点で検証し、Critical/High/Mediumの根拠付きサマリーを作る。設計レビュー依頼またはSDDのレビューtaskで使う。"
context: fork
---

# Design Reviewer

設計ドキュメントを変更せずにレビューし、人間が採否を判断できる問題一覧と修正方針を返す。対象は通常次のディレクトリにある。

```text
.kiro/specs/<feature>/
├── requirements.md  # レビュー基準
├── design.md        # 必須の対象
└── tasks.md         # あれば参照
```

## 入力と外部仕様

`design.md` を全文読む。`requirements.md` があれば要約で代替せず全文を読み、全ユーザーストーリー、WHEN-THEN受入基準、用語、非機能要件を照合表にする。なければ要件カバレッジをスキップしたことを報告する。`tasks.md` は実装境界との整合を見る必要があるときだけ読む。

外部仕様のConfluence URLは自動推測しない。

- ユーザーからの直接呼び出しはAskUserQuestionでURL（または「なし」）を確認する。
- SDDからのdispatchはプロンプトの `CONFLUENCE_URL` だけを使い、なければ外部仕様なしで進める。
- URLがあれば `mcp-atlassian` の `confluence_get_page`（ページIDはURLの `/pages/<数字>/`）または `confluence_search` で取得する。未接続ならレビューを続け、サマリーに「mcp-atlassian未接続のためスキップ」とURLを残す。

## レビューの流れ

1. PJの `CLAUDE.md` と対象specの制約を確認し、requirementsの受入基準を一覧化する。
2. designと既存コード・構成を照合し、次の優先順で11観点を確認する。

   | 優先 | 観点 |
   | --- | --- |
   | P1 | 要件カバレッジ、アーキテクチャ整合、interface整合、前提の正しさ |
   | P2 | scope/非機能、未決定事項、実現可能性、エラーハンドリング |
   | P3 | テスト戦略、性能/scale、外部仕様整合 |

   詳細な問いは `references/review-perspectives.md`、前提の実在確認と検証順は `references/verification-steps.md` を該当箇所だけ読む。

3. 観点を独立に委譲する場合は、現在利用できるcollaboration capabilityを使い、arch/interface/feasibility、security/error、performanceを分担する。`multi_agent_v1` など固定APIを仮定しない。requirementsとの照合、未決定事項、前提検証、テスト、外部仕様はleadが統合する。
4. 問題を分類する。

   - **Critical**: 要件欠落、重大な矛盾、存在しないcomponentや依存境界を前提にするなど、承認できないもの。
   - **High**: 設計不備、状態・interface・error戦略の欠落、高い実装リスク。
   - **Medium**: 曖昧なscope、未決定事項の未記録、テストや明文化の不足など改善推奨。

5. `templates/review-summary.md` に従い、各指摘へ観点、重要度、根拠（`file:line`）、影響、修正方針、未確認事項を付ける。Criticalがある場合は承認を推奨しない。

## 直接呼び出しの確認

SDD経由ではこの節を省く。直接呼び出しでは、指摘を重要度別にAskUserQuestionで確認する（1回最大4問）。該当指摘がないroundは省く。

- Critical: 「修正する / 対応不要 / 要議論」
- High: 「修正する / 対応不要 / 後で対応」
- Medium: 「修正する / 対応不要 / 後で対応」

回答を最終サマリーへ反映する。設計の再生成や実装を勝手に始めず、指摘ごとに `design.md` の変更箇所と具体的方針を示す。必要なら次の再レビュー手順を案内する。

```text
/kiro:spec-design <feature名>  # 修正方針を反映
/design-reviewer               # 同じ11観点を再確認
/kiro:spec-tasks <feature名>   # Critical/Highが解消した後
```

SDD経由では修正方針を返し、再生成の判断は呼び出し元に任せる。

## 不合格条件

- `design.md`を読まずに判定する。
- `requirements.md`があるのに全文を読まない、受入基準との照合を省く。
- 既存component、interface、外部仕様など前提の実在性を確認しない。
- 未決定事項、テスト戦略、エラーハンドリングの抽出を省く。
- Criticalがあるのに承認を推奨する。
- `templates/review-summary.md` の必須セクションを落とす（Confluence未参照時だけ外部仕様欄を省略可）。
