---
name: prompting-fable
description: "Claude Fable 5 に渡すプロンプトを、Anthropic 公式ガイド「Prompting Claude Fable 5」の全項目チェック付きで構築する。長時間・自律・subagent 前提のタスクを Fable 5 に投げる前に使う。使用タイミング: 「fableに渡すプロンプト作って」「Fable 5に長時間タスクを投げる前に整えて」「Fable用のagent指示を作って」など。"
---

# Prompting Fable

Fable 5 に投げたいタスクを受け取り、公式ガイド「Prompting Claude Fable 5」の全項目を 1 行ずつ判定しながらプロンプトを構築する。

出力は 3 点セット: **そのまま Fable 5 に渡せる完成プロンプト / harness・API 設定サマリー / 全項目チェック表**。チェック表が全行埋まっていることが「問題なく投げられる」の保証になる。

## 使う場面

- Fable 5 に長時間の実装、調査、レビュー、運用作業を任せる前。
- subagent、非同期進捗、memory、長い context が関わるタスクを投げる前。
- 難度レンジの上限のタスクを渡すとき（簡単な作業だけで試すと能力レンジを過小評価する。単純なタスクも安定してこなす）。
- Opus 4.8 比の向上点（long-horizon autonomy、first-shot correctness、vision、enterprise workflow、code review / debugging、曖昧なリクエストのナビゲート、並列 subagent の委任・協調）を活かすタスクを選ぶ。

単純な質問、短い翻訳、軽い要約では使わない。

## 責務境界

- この skill は Fable 5 向けプロンプトの構築と全項目チェックを担う。
- 汎用テクニック（XML 構造化、few-shot 等）の深掘りが必要な場合のみ `prompt-engineering` を併用する。
- 判定と文言の根拠は公式ガイドに限定する。ガイドにない Fable 5 挙動ルールを足さない。

## Step 1: 入力の収集

プロンプトを組む前に以下を把握する。依頼文・会話から導けるものは導き、本人にしか分からないものだけ AskUserQuestion で質問する（自律実行中は仮定を置き、チェック表に仮定と明記する）。

- タスク選定: 旧モデルに任せるより難しいタスクか（scope 決め・確認質問・実行まで Fable 5 に任せられる）
- タスク内容・成果物・合格基準
- 大きい目的、誰のためか、成果物が何を可能にするか（表 #1 で使う）
- 実行形態（対話 / 半自律 / 自律パイプライン）と想定実行時間
- 権限範囲: 状態変更・外部送信・削除など変更系アクションの有無
- harness の可用性: effort 制御 / subagent / memory 置き場 / send-to-user 相当のツール / timeout・streaming・非同期確認 / 残 token カウント表示の有無
- 流用する既存プロンプト・スキルの有無

## Step 2: 全項目チェック

下表の**全 19 行に判定を出す**。判定は 3 値: `組み込む [S番号]` / `harness側で対応` / `対象外（理由必須）`。行の省略・まとめ判定は禁止。

snippet の英語原文は `references/fable5-prompt-snippets.md` を Read して使う。

| # | 項目 | 組み込むもの | 適用判定（公式ガイドの条件） |
|---|------|------------|--------------------------|
| 1 | 目的と理由 | S11 の型で冒頭に目的・誰のため・何を可能にするかを書く | 常時推奨（意図が分かると性能が上がる傾向）。特に複数 workstream の長時間 agent |
| 2 | effort | harness: `high` デフォルト / 能力最優先は `xhigh` / 定型は `medium`・`low`。完了はするが不必要に長い・対話重視なら下げる（低 effort でも旧モデルの `xhigh` を上回ることが多い） | 常時（API/harness 設定）。他スキルの旧モデル向け記述と食い違う場合も本項（公式ガイド準拠）を正とする |
| 3 | 長い turn の受け皿 | harness: timeout・streaming・進捗表示を調整し、ブロックせず scheduled job 等で非同期に確認 | hard task・自律実行を投げる前（1 リクエスト数分〜、自律実行は数時間に及ぶ） |
| 4 | overplanning 抑止 | S1 | タスクに曖昧さがあり計画過多が起き得るとき |
| 5 | 過剰作業抑止 | S2 | 高 effort で動かすとき（依頼外の機能・refactor・抽象化・将来要件の設計を防ぐ） |
| 6 | brevity | S3 | 無操舵の詳述（選ばない選択肢の列挙、長い根本原因説明等）を避けたい・報告の読みやすさが要るとき。パターンの個別列挙より短い指示 1 つで足りる |
| 7 | 停止条件 | S4 | 長時間ワークフロー全般。止まるのは破壊的・不可逆 / スコープ変更 / 本人しか知らない入力のみ。ケースの列挙は不要 |
| 8 | 証拠つき進捗 | S5 | 長い自律実行（tool result と突き合わせる監査で、捏造された進捗報告をほぼ排除） |
| 9 | 作業境界 | S6 | 依頼されていない行動（頼まれていないメール下書き・防御的 git バックアップ等）を防ぎたいとき。してよいこと・しないことを明示 |
| 10 | 並列 subagent | S7 + 委任が適切な場面の明示 | subagent が使えるとき。完了をブロックして待つより非同期通信を優先し、context を保つ長寿命 subagent を活用（cache read で節約・最遅 subagent のボトルネック回避） |
| 11 | memory | S8 + 置き場 [X] の具体化（初回導入時は bootstrap 用 snippet も） | 複数 run で教訓を持ち越すとき。Markdown ファイル程度で十分 |
| 12 | 早期停止防止 | S9 | 自律パイプライン（対話なら「continue」で再開できるため任意）。#7 の停止条件とペアで使う |
| 13 | context 不安 | harness: 残 token カウントを可能な限り見せない。見せるなら S10 | 非常に長いセッション（新セッション提案・handoff・自己短縮の主因は残量カウント表示） |
| 14 | 最終報告の読みやすさ | S12 | ユーザーが途中を見ない長い agentic 実行（多数の tool call・大きい作業 context） |
| 15 | send-to-user | harness: ツール定義（S13 の JSON）+ 呼び出しを促す指示（定義だけでは滅多に呼ばれない） | 途中成果物・逐語で読ませるべき内容を turn 中に届ける UX が必要なとき。ルーチン進捗の narration だけならモデル自身の要約で足りる |
| 16 | 検証 scaffolding | S14（interval [X] を具体化） | 長時間の構築系タスク。別 context の fresh な verifier subagent は self-critique を上回る傾向 |
| 17 | 旧プロンプト見直し | 流用元から旧モデル向けの細かすぎる手順・長い禁止リストを削る | 既存プロンプト/スキルを流用するとき（旧モデル向けは過剰指示になり品質を下げ得る） |
| 18 | reasoning 抽出回避 | 監査: 内部推論を本文へ echo・転記・説明させる指示を除去。可視性が要るなら adaptive thinking の structured thinking blocks + send-to-user | 常時（Step 4 で確認）。違反は `reasoning_extraction` refusal を誘発し Opus 4.8 への fallback が増える |
| 19 | safety classifier | 該当し得るなら refusal を前提に Opus 4.8 への server-side / client-side fallback を構成 | offensive cybersecurity（exploit・malware・攻撃ツール）/ 生物・生命科学（実験手法・分子機構）/ 要約 thinking の抽出に触れ得るタスク（良性の作業でも発火し得る） |

## Step 3: プロンプト組み立て

判定 `組み込む` の項目を、次の順で 1 本のプロンプトに組む。snippet は英語原文のまま埋め込み、`[X]` 等のプレースホルダは Step 1 の情報で必ず具体化する。

1. 目的と理由（S11 の型）
2. タスク本体・成果物・合格基準
3. 作業境界（S6）と停止条件（S4）
4. 実行時の振る舞い: S1 / S2 / S5 /（自律パイプラインなら S9）
5. 委任と検証: S7 / S8 / S14
6. 報告様式: S3 / S12 /（send-to-user があれば S13 の促進指示）
7. 必要時のみ: S10

組み立ての原則（公式ガイド準拠）: Fable 5 は短い指示で挙動を操舵できるため、同じ趣旨の snippet を重複させない・タスクに関係ない行を残さない・挙動の網羅列挙をしない。

## Step 4: 最終監査と出力

監査（全部満たすまで直してから出力する）:

- [ ] チェック表の 19 行すべてに判定（と対象外の理由 / 置いた仮定）がある
- [ ] 内部推論を本文へ再現させる指示が混入していない（#18）
- [ ] 旧モデル向けの過剰指示・長い禁止リストを持ち込んでいない（#17）
- [ ] プレースホルダ（`[X]` 等）がすべて具体化されている
- [ ] `harness側で対応` と判定した項目がプロンプト文言に化けていない（ツール定義・effort・timeout は prompt では解決しない）

ユーザーへの出力（3 点セット）:

1. **完成プロンプト** — コードブロックで、そのまま Fable 5 に渡せる形
2. **harness・API 設定サマリー** — effort 値、timeout・streaming・非同期確認、send-to-user ツール定義、残 token カウント非表示、（#19 該当時）Opus 4.8 fallback
3. **全項目チェック表** — 19 行の判定結果（組み込む [S番号] / harness側で対応 / 対象外＋理由）

## 参照

- `references/fable5-prompt-snippets.md` — 公式ガイド推奨プロンプトの原文集（S1-S14、コピペ用）
- `~/Documents/obsidian-vault/Inbox/knowledge/Claude Fable 5 プロンプト作成メモ.md`（著者の個人メモ・環境依存）
- Anthropic: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5
- Anthropic: https://platform.claude.com/docs/en/about-claude/models/introducing-claude-fable-5-and-claude-mythos-5
