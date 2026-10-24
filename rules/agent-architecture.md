# Agent Architecture（Fold-First）

Agent()/Workflow/spawn_agent/custom agent/reviewerを足す・使う・新しいagentやcommandのchainを設計するときに適用する。`context/agent-team-routing.md` のDelegation Gateを置き換えず、その「分け方」の判断基準を補う。

## 既定

既定は1つのmain loopが計画を書いて自分で実行することである。手順・領域知識はSkill（必要時に全文を読む）へ置き、守るべき上限（検証・承認gate）はtool/hook/script側へ置く。

> Default to a single agent loop; use subagents only when they add real value.

## subagentを使ってよい条件

次のどれか1つを根拠つきで満たすときだけsubagentを使う。

1. **並列の独立作業**: 独立した調査経路を新しい文脈で並べ、終われば捨てる。
2. **独立検証**: maker ≠ checker、review、black-box検証。
3. **文脈隔離**: 数万token級のlog・文書・検索結果を読み、mainには短い結果だけ返す。toolが出力を絞れるならまずそちらを使う。
4. **1つのloopでtool選択が乱れる・指示が衝突する**、または権限を分けたい。

## 問い

そのsubagentは本当に独自の文脈とloopが要るか。要らなければfoldする。迷ったら残す。

## 分け方

問題種別・組織図で分けない。分けると伝言ゲームになり文脈が欠ける。文脈で分け、他から少ししか要らない仕事を渡し、決めた形の短い結果を返させる。ユーザーと直接話す必要がある仕事はsubagentにしない（subagentはユーザーに質問できない）。

## foldの手順（チェックリスト）

1. 1回に1つだけfoldする。
2. 旧agentの手順を1行ずつ仕分ける: Skill本文に書く／tool・hookで強制する／参照資料にする／削除する（口調・古いモデル向けの念押し等）。
3. 旧手順→新しい置き場所の対応表を作り、全ステップに行き先があることを確認する。
4. 一緒に動くchain（A→B）ごとに確認taskを用意し、chainの最後の成果物で判定する。
5. 同じtaskを2回以上走らせる。
6. 総合点だけでなく、前に通っていて落ちたtaskを見る。隣のagentの仕事をmainが手元のtoolで勝手に済ませていないかも見る。
7. 旧agent定義は確認が済むまで残す（routeだけ外す）。
8. 悪化したら戻してsubagentのままにし、負けたtaskを記録する。

## 正式なevalがない環境での代わり

既存のvalidator・canary（例: `scripts/validate-agent-harness.py`、`scripts/run-claude-md-canary.py` / `scripts/run-agents-md-canary.py`）の変更前後比較 + 対応表 + 2回以上のsmoke testで代替する。

## 参考実装

API上で自作するagent製品（例: 業務アプリのmulti-agent）に使う道具として、Anthropicの single-agent-loop-kit がある（https://github.com/anthropics/single-agent-loop-kit 、調査時点commit `c43796287b83bec847db923f07131d1cc8de750d`、Apache-2.0）。手順はaudit→baseline→merge→fold→as-tool→upkeepで、`chain_coverage.py`・`compare.py`を使う。このhomeへSkillとして導入はしていない。第三者Skillの導入は `skill-governance` を通す。

## 出典

- https://claude.com/resources/articles/building-agents-when-to-fold-subagents-into-your-main-agent-loop
- https://x.com/xudong07452910/status/2113800139005460534
- https://github.com/anthropics/single-agent-loop-kit
