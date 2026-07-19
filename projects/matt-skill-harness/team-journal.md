# Team Journal: matt-skill-harness

## 定位置

- Goal Gate：PASS
- Lane：user-scope governance と harness implementation
- Outcome Trace：実装接続済み8、evidence収集中、holistic pending
- Review Heat：標準。governance、UI、accessibility を直接検証する。
- 現在の周：1

## Outcome Trace

| Outcome | Requirement | Implementation | Acceptance | Evidence | Human Review | Objection | State |
| --- | --- | --- | --- | --- | --- | --- | --- |
| O-1 41 Skill の判断を残す | 00_spec.md O-1 | Task 1 / matt-skill-inventory.md | AC-01 | validator PASS、human review待ち | 分類理由を一覧で読めるか | 「既存対応を導入済みと数えていないか」 | missing-evidence |
| O-2 in-progress 2件を隔離導入する | 00_spec.md O-2 | Task 3 / skills 2件 | AC-02 | static test PASS、prompt review待ち | 起動時に状態と境界が分かるか | 「実験的Skillが勝手に起動しないか」 | missing-evidence |
| O-3 正式名を発見可能にする | 00_spec.md O-3 | Task 2 / entry 5件 | AC-03 | discovery validator PASS、fresh session待ち | Skill一覧から期待名を見つけられるか | 「別名が二重起動を起こさないか」 | missing-evidence |
| O-4 deprecatedを削除する | 00_spec.md O-4 | Task 4 / retired 4件 | AC-04 | validator PASS、live audit待ち | 置換先が明記されているか | 「削除で既存参照が壊れないか」 | missing-evidence |
| O-5 一画面で漏れを判断する | 00_spec.md O-5 | Task 5 / roadmap viewer | AC-05, AC-06 | parser test PASS、browser review待ち | 一分以内に次の確認先を言えるか | 「情報を隠しているだけではないか」 | missing-evidence |
| O-6 観察後の修正を履歴化する | 00_spec.md O-6 | Task 5 / Revision Log | AC-07 | parser test PASS、browser review待ち | 元計画と変更理由を追えるか | 「後付けで合格基準を変えられないか」 | missing-evidence |
| O-7 teachで理解可能にする | 00_spec.md O-7 | Task 6 / lesson、reference | AC-08 | content作成済み、browser review待ち | 図と小テストだけで読めるか | 「教材が本体とずれないか」 | missing-evidence |
| O-8 両surfaceとlive homeを揃える | 00_spec.md O-8 | Task 7, Task 8 | AC-09, AC-10 | paired validator PASS、live sync待ち | live discoveryを再起動後に確認できるか | 「runtime-only fileが消えないか」 | missing-evidence |

## Revision Log

| ID | Observed | Plan change | Revalidate | Status |
| --- | --- | --- | --- | --- |
| REV-01 | upstream正式名が local discovery に出ていない | 正式名の薄い user-invoked entryを追加した | AC-03, AC-09 | implemented |
| REV-02 | catalog live の人間向け表示が欠損fieldで例外になる | 欠損時に安全な表示へfallbackした | AC-09 | verified |
| REV-03 | 7列のOutcome Traceは横に重く、Revisionまで視線が届きにくい | SpecからEvidenceまでを一つのchainへまとめ、4列へ減らした | AC-05, AC-06 | implemented |
| REV-04 | モバイル表示で未指定のflex orderがObservation / Revisionを先頭へ押し上げた | Now / Next、Outcome Trace、Revision、詳細の順序を明示した | AC-05, AC-06 | implemented |
| REV-05 | hidden file inputにアクセシブルネームがなかった | ファイル選択inputへ用途を示すaria-labelを追加した | AC-05 | implemented |
| REV-06 | upstreamでdeprecatedの`design-an-interface`と同名の旧local Skillが残っていた | Skillを削除し、`brainstorming`と`designing-codebases`へ参照を分離した | AC-01, AC-04 | implemented |

## Decision Log

| 時刻 | 決定 | 理由 |
| --- | --- | --- |
| 2026-07-19 11:33 JST | in-progress 2件を再評価する | reject理由は自動起動時の負荷であり、明示起動なら隔離できる |
| 2026-07-19 11:33 JST | deprecated 4件を削除対象にする | 置換先があり、ユーザーが実削除を承認した |
| 2026-07-19 11:33 JST | `handing-off-to-claude` は保持する | in-progressだがdeprecatedではなく、今回の削除承認の範囲外である |
