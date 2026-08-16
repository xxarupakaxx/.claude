# Implementation Complexity Budget

この文書は、コード変更の過剰実装を早期に見つけるための **Complexity Budget の Single Source of Truth** である。`context/workflow-rules.md`、Goal Setter、team-run、planner、implementer、reviewer はこの文書を参照し、別の数値ルールを作らない。

## 目的と境界

- 実装計画の各要素に、推定コード量の**レンジ付きソフト目標**を置く。
- 実装中に計画値と実測値を比較し、不要な抽象化・要求外の機能・責務の追加を早く発見する。
- 数値はハード上限、品質スコア、納期の代替ではない。正しさ・安全性・可読性・必要なテストが優先される。
- コード、テスト、設定、migration、生成物を混ぜずに記録する。文書のみの変更は `N/A (non-code)` とし、必要なら通常の変更行数を別途見積もる。

## 要素と計測方法

### 要素の定義

要素は、1つの要件または振る舞いに対応する最小の**まとまり**である。ファイルを行数だけで切り刻んだ単位ではない。例:

- 1つの関数・handler・adapter
- 1つの画面/routeの垂直slice
- 1つのmigrationと、その検証
- 1つの設定変更と、その読み取り側

1要素に複数ファイルが含まれてもよい。逆に、行数を減らすためだけの無意味なファイル分割は禁止する。

### コード量の定義

計画では、原則として `logical diff LOC`（追加行 + 削除行のうち、空行・コメント・vendor・生成物を除いた概算）を使う。実測では `git diff --numstat`、対象ファイルの差分、必要なら簡単な行数集計を使い、次を分けて記録する。

| 区分 | 記録するもの |
|---|---|
| production | 実行時コードのlogical diff LOC |
| test | テスト・fixture・test helperのlogical diff LOC |
| config/migration | 設定・schema・migrationのlogical diff LOC |
| generated | 生成ファイルの行数（予算判定から分離し、生成元と理由を記録） |

行数の厳密な一致より、同じ方法で target と actual を比較することを優先する。フォーマッタや自動生成の差分は、機能コードと混ぜずに明記する。

### 初期レンジ（言語非依存の目安）

以下は計画を始めるための目安であり、プロジェクト固有の既存実装や調査結果で上書きできる。

| 要素の大きさ | 初期目安（logical diff LOC） | 扱い |
|---|---:|---|
| micro change（既存関数の局所修正） | 5–20 | そのまま実装候補 |
| single behavior（1責務の関数/adapter/画面片） | 20–80 | 通常の単位 |
| cross-module slice（複数責務をつなぐ垂直slice） | 60–150 | 境界と統合テストを明記 |
| 150超/要素、または合計300超 | 固定値なし | 分割または超過理由の計画レビュー候補 |

## Phase 2: 計画

コード変更を含む `30_plan.md` は、各要素について次の表を持つ。小規模なコード変更でも、1行の `N/A` と理由を残す。

```markdown
| Element | 要件/振る舞い | 変更対象 | production target | test target | config/migration target | 信頼度 | 根拠 |
|---|---|---|---:|---:|---:|---|---|
| 1.1 | <何を成立させるか> | <path / symbol> | 20–40 | 10–20 | 0 | medium | 既存の<anchor>と比較 |
```

計画には、(a) targetの根拠、(b) 既知の除外（生成物・formatting等）、(c) 上限を超えた場合の再計画条件を含める。targetを点ではなくレンジで書き、信頼度（low / medium / high）を付ける。

## Phase 3: 実装

- 実装開始前に、maker/lead は担当要素のtargetと除外を確認する。
- 各要素の完了時、または新しいファイル・層・抽象化を追加する直前に、actualを差分から測る。
- 上限内なら `within target`、上限を少し超える場合は `exceeded-with-reason` として理由を `40_progress.md` / Team Journalへ記録する。
- 上限を大きく超える（目安: 上限の25%以上）か、計画にない責務・層・公開API・設定項目を追加する場合は、いったん停止して次を確認する。
  1. 追加分はどの受入基準に必要か。
  2. 同じ基準をより短い既存パターンで満たせないか。
  3. 削除・統合・後回しにできるコードはないか。
- 追加が要求、Done、evidence、scopeを変えるなら、計画を修正して User Validation Gate を再通過する。意味を変えない実測更新は再承認不要。

## Phase 4: 品質確認

レビューは、機能の正しさと別に「計画どおりの複雑さか」を確認する。レビュー入力に計画表と実測差分を含め、要素ごとに次を判定する。

| 判定 | 意味 | 対応 |
|---|---|---|
| within target | 予算内で、不要な責務追加なし | 通常のレビューを続ける |
| justified variance | 必須の安全性・互換性・framework boilerplate等で超過 | 根拠、削減検討、残存リスクを記録して継続 |
| scope drift | 要求外の機能、不要な抽象化、新しい層/公開API | CRITICAL/IMPORTANT候補。削除または再計画 |

`code-simplicity-reviewer` は、単に行数が多いことではなく、target超過と受入基準の対応、削減可能な責務、不要な間接参照を具体的なファイル・行で示す。target内でも過剰設計なら指摘し、target超過でも必要性が証明されていれば機械的に拒否しない。

## 例外と禁止事項

次は超過が起こり得るため、種類・根拠・実測方法を記録する: セキュリティ修正、互換性維持、framework必須の定型、schema/migration、生成コード、必要な失敗系テスト、既存バグの安全な切り分け。

- 行を詰める、minifyする、コメントを削る、コードゴルフをする、テストを弱める、検証を省くことでtargetを満たしてはならない。
- targetを守るために必要なエラー処理・認可・テストを削ってはならない。
- `future-proof`、`念のため`、`将来使うかもしれない`だけでは超過理由にならない。具体的な現在の要件か既存契約に結び付ける。
- generated/vendor差分をproduction targetの達成として数えない。

## 最終報告

コード変更を含む完了報告には、少なくとも `target / actual / variance / reason` の要約を含める。完全な表は `30_plan.md`、`40_progress.md`、Team Journal、`80_review.md` のいずれかへ残す。コード変更がない場合は `Complexity Budget: N/A (non-code)` と明記する。

## 参考

- Google Engineering Practices, [Small CLs](https://google.github.io/eng-practices/review/developer/small-cls.html)
- Google Engineering Practices, [What to look for in a code review](https://google.github.io/eng-practices/review/reviewer/looking-for.html)
- NASA Software Engineering Handbook, [SWE-015 Cost Estimation](https://swehb.nasa.gov/spaces/7150/pages/16449831/SWE-015%2B-%2B%2BCost%2BEstimation)
