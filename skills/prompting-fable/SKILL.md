---
name: prompting-fable
description: "Claude Fable 5 に渡す長時間・自律・subagent前提の追補プロンプトを設計する。使用タイミング: 「fableに渡すプロンプト作って」「Fable 5に長時間タスクを投げる前に整えて」「Fable用のagent指示を作って」など。"
---

# Prompting Fable

この skill は汎用プロンプト設計を置き換えない。

既存のプロンプト骨格に、Anthropic 公式ガイド「Prompting Claude Fable 5」に基づく Fable 5 / Mythos 5 固有の追補を足す。

## 使う場面

- Fable 5 に長時間の実装、調査、レビュー、運用作業を任せる。
- subagent、非同期進捗、memory、長い context が関わる。
- 旧モデル向けの細かい手順を減らし、Fable 5 固有の詰まり方だけを補う。
- 難度レンジの上限のタスクを渡す（簡単な作業だけで試すと能力レンジを過小評価する。単純なタスクも安定してこなす）。
- Opus 4.8 比の向上点（long-horizon autonomy、first-shot correctness、vision、enterprise workflow、code review / debugging、曖昧なリクエストのナビゲート、並列 subagent の委任・協調）を活かすタスクを選ぶ。

単純な質問、短い翻訳、軽い要約では使わない。

## 責務境界

- 汎用の目的整理、文脈設計、XML構造化、few-shot は `prompt-engineering` 側に任せる。
- この skill は Fable 5 に足す差分だけを作る。
- 完成品は、既存プロンプト全体ではなく `Fable 5向け追補` として出す。

## Fable 5 差分（公式ガイド全項目）

推奨プロンプト文言の原文（コピペ用・英語）は `references/fable5-prompt-snippets.md` を Read で参照する。[S番号] は同ファイルの snippet 番号。snippet を持たない差分があるため差分番号と S 番号は一致しない。各差分末尾の [S番号] を正とする。

1. **長い turn 前提**: hard task では 1 リクエストが数分単位、自律実行は数時間に及ぶ。移行前に client timeout・streaming・進捗表示を調整し、ブロックして待たず scheduled job 等で非同期に様子を見る harness に組み替える。曖昧なタスクでの overplanning は「十分な情報が揃ったら行動する」指示で抑える。[S1]
2. **effort 選択**: effort が知能・レイテンシ・コストの主制御。ほとんどのタスクは `high` をデフォルトに、能力最優先の workload は `xhigh`、定型作業は `medium` / `low`。低 effort でも旧モデルの `xhigh` を上回ることが多い。完了はするが不必要に時間がかかる場合や、より速く対話的に使いたい場合は effort を下げる。Fable 5 の effort は、他スキルの旧モデル向け記述と食い違う場合も本項（公式ガイド準拠）を正とする。
3. **過剰作業抑止**: 高 effort では依頼外の機能追加・refactor・抽象化、仮定の将来要件の設計、起こり得ないシナリオへのエラーハンドリングが出やすい（一方で検証行動・推論は最も厳密になる）。「タスクが要求する以上のことをしない」と明記して抑える。[S2]
4. **短い指示で操舵**: instruction following が強く、挙動を 1 つずつ列挙しなくても短い指示で操舵できる。無操舵だと必要以上に詳述する（選ばない選択肢の列挙、長い根本原因説明、過剰構造の PR 説明、次の行を語るコメント）が、短い brevity 指示 1 つで各パターンの列挙と同等に効く。[S3]
5. **停止条件**: 止まるのは本当にユーザーが必要な場合だけ — 破壊的・不可逆な操作、実質的なスコープ変更、本人しか知らない入力。該当したら promise で終えず、質問して turn を終える。ケースの列挙は不要。[S4]
6. **証拠つき進捗**: 長い自律実行では、進捗報告の各主張をそのセッションの tool result と突き合わせて監査させる。未検証は未検証と明示、テスト失敗は出力ごと報告。Anthropic のテストでは捏造された進捗報告をほぼ排除できた。[S5]
7. **作業境界**: 依頼されていない行動（頼まれていないメールの下書き、防御的な git ブランチのバックアップ等）を稀に取る。してよいこと・しないことの制約を明示する — 問題の説明や質問のときは評価が成果物で、修正は頼まれるまでしない。システム状態を変えるコマンドの前に根拠を確認させる。[S6]
8. **並列 subagent**: 旧モデルより subagent を積極的に使う。頻繁に使わせ、委任が適切な場面のガイダンスを明示し、各 subagent の完了をブロックして待つより orchestrator–subagent 間の非同期通信を優先する。subtask を跨いで context を保つ長寿命 subagent は cache read で時間とコストを節約し、最遅 subagent のボトルネックを避ける。[S7]
9. **memory 設計**: 過去 run の教訓を記録・参照できると特に良く働く。書く場所は Markdown ファイル程度で十分。1 教訓 1 ファイル + 先頭に 1 行要約、repo や会話履歴が既に記録していることは保存しない、重複は既存ノートを更新、誤りは削除。過去セッションのレビューによる bootstrap も可能。[S8]
10. **早期停止防止**: 長いセッションの深部で、tool call を出さずに意図表明だけで turn を終える、または十分な情報があるのに許可を求めることが稀にある。「continue」で再開できる。停止条件（差分5）とペアにし、autonomous パイプラインには system reminder を足す。[S9]
11. **context不安防止**: 非常に長いセッションで、新セッション提案・要約と handoff の申し出・作業の自己短縮が稀に出る。主因は harness が残り token カウントを見せること。可能なら context 残量の明示を避け、見せる必要があるなら「context は十分残っている」と伝える。[S10]
12. **理由を渡す**: 依頼の背後にある意図が分かると性能が上がる（意図を自力推定させず、関連情報とタスクを繋げられる）。特に複数 workstream を扱う長時間 agent には、大きい目的・誰のためか・成果物が何を可能にするかを渡す。[S11]
13. **最終報告の読みやすさ**: 長い agentic 会話では、矢印略記・深すぎる実装詳細・ユーザーが見ていない thinking への参照・過度に技術的な表現が出やすい。途中を見ていない読者向けに、結果を先頭に、作業中の略語や内輪ラベルを捨てて書かせる communication 追補を足す。[S12]
14. **send-to-user ツール**: 長い非同期 agent には、turn を終えずに「そのまま読ませるべき内容」（成果物・数値入り進捗・質問への直接回答）を届ける client 側ツールを用意する（UI 側は input をそのまま描画し、tool result には単純な acknowledgement を返す）。tool input は要約されないため内容が無傷で届く。定義だけでは滅多に呼ばれないので、呼び出しを促す指示とペアにする。narration や推論には使わせない。[S13]
15. **検証の scaffolding**: 長時間タスクには自己検証の方法と実行インターバルを明示する。別 context の fresh な verifier subagent は self-critique を上回る傾向がある。[S14]
16. **旧プロンプト/スキルの見直し**: 旧モデル向けに作った skill は Fable 5 には過剰指示になりやすく、出力品質を下げ得る。デフォルト性能の方が良ければ古い指示の削除を検討する。Fable 5 はタスクから学んだことに基づく skill のその場更新も得意。
17. **reasoning抽出回避**: 内部推論を応答本文へ echo・転記・説明させる指示は `reasoning_extraction` refusal を誘発し、Opus 4.8 への fallback が増える。移行時に既存の skill / system prompt から reflection・show-your-thinking 系の指示を監査する。推論の可視性が必要なら adaptive thinking の structured `thinking` blocks を読み、長い実行中の進捗表示には send-to-user ツールを使う。

## 注意

- Fable 5 は safety classifier を実行する。対象は offensive cybersecurity（exploit・malware・攻撃ツールの構築）、生物・生命科学（実験手法・分子機構）、要約 thinking の抽出（差分17 の `reasoning_extraction`）。良性の cybersecurity・生命科学タスクでも発火し得る。拒否されたリクエストを自動で再ルーティングするには Opus 4.8 への server-side / client-side fallback を構成する。
- API パラメータ差分（adaptive thinking のみ、summarized thinking 出力、extended thinking budget 廃止、`refusal` stop reason と fallback）は「Introducing Claude Fable 5 and Claude Mythos 5」を参照。

## 出力

ユーザーには短い追補プロンプトだけを返す。

```text
Fable 5向け追補:
- 進捗を報告する前に、各主張をこのセッションの tool result と突き合わせる。未検証は未検証と明示する。
- 止まるのは破壊的・不可逆な操作、実質的なスコープ変更、本人しか知らない入力が必要な場合だけ。計画や宣言だけで turn を終えず、実行まで進める。
- context 残量を理由に停止・要約・新セッション提案をしない。
- 最後の報告は、途中を見ていない読者向けに結果を先頭にして書く。
```

必要なら、対象タスクに合わせて effort・作業境界・subagent 委任・memory 置き場・verifier subagent・send-to-user の各項目について、`references/fable5-prompt-snippets.md` の snippet から必要なものを選んで足す。

## チェックリスト

- [ ] 追補が Fable 5 固有差分だけになっている（汎用設計は `prompt-engineering` へ）。
- [ ] 長い turn の受け皿（timeout / streaming / 進捗表示 / 非同期確認）を決めた。
- [ ] effort の方針がある（`high` デフォルト、能力最優先 `xhigh`、定型 `medium`/`low`）。
- [ ] 進捗報告が tool result の証拠に紐づく。
- [ ] 停止条件が「破壊的・不可逆 / スコープ変更 / 本人しか知らない入力」に限られている。
- [ ] 早期停止と context 不安への対策がある。
- [ ] 長時間・非同期の作業なら、subagent 委任 / memory / verifier subagent / send-to-user を検討した。
- [ ] 内部推論を本文へ再現させる指示がない。
- [ ] 旧モデル向けの過剰な指示・禁止リストを持ち込んでいない。

## 参照

- `references/fable5-prompt-snippets.md` — 公式ガイド推奨プロンプトの原文集（コピペ用）
- `~/Documents/obsidian-vault/Inbox/knowledge/Claude Fable 5 プロンプト作成メモ.md`（著者の個人メモ・環境依存）
- Anthropic: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5
- Anthropic: https://platform.claude.com/docs/en/about-claude/models/introducing-claude-fable-5-and-claude-mythos-5
