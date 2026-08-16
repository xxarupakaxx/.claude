---
name: adversarial-review
description: 重要判断（アーキテクチャ・セキュリティ・性能クリティカル変更）に対し、Redのfindingを同じBlueへ逐次渡し、全件照合後にAuditorが審判する3エージェントレビュー。通知とdurable queueを分離し、protocol failure時はbatch直列へ戻る。auto-reviewing-pre-pr より高コストなので、ユーザーが明示的に呼び出すか auto-reviewing が ESCALATE した場合のみ起動。「アドバーサリアルレビューして」「Red/Blueで検証」「敵対的レビュー」等の依頼に対応。
context: current
---

# Adversarial Review — 三者敵対的レビュー

## 概要

通常レビューでは検出しづらい「reviewer のバイアス」を相互チェックする。
Red（悲観派）がfindingを確定するたびに同じBlue（楽観派）へ渡し、BlueがRed完了前から独立検証する。
Red EOFとBlue全応答を照合して固定snapshotを作った後、Auditor（審判）が最終判定する。

streamingは待ち時間を減らす最適化であり、正しさの前提ではない。
`SendMessage` による同一 agent への follow-up や agent thread が部分故障した場合は、保存済みfindingから従来のbatch直列へ降格する。

## モデル選択（コスト最適化）

Agent Tool では通常 `model` を省略し、親セッションのモデルを継承させる:

| エージェント | subagent_type / model | 役割 |
|------------|-------|------|
| `red-reviewer` | `Agent(subagent_type: "red-reviewer")` — model省略（親継承） | 攻撃側（広く速く懸念列挙） |
| `blue-reviewer` | `Agent(subagent_type: "blue-reviewer")` — model省略（親継承） | 防御側（Red の反論検証） |
| `auditor-reviewer` | `Agent(subagent_type: "auditor-reviewer", model: "opus")` | 審判（最終判定・Read で独立検証） |

> model 指定は審判（Auditor）の `model: "opus"` のみ。Red/Blue は省略して親セッション継承。

## アンチ多数決原則（CRITICAL）

- **多数決は confabulation consensus を生む**: 全員同じ嘘に収束するリスクあり
- Auditor は Red と Blue の **不一致点** を優先的に分析する（一致点は独立 Read でスポット検証）
- Red:AGREE + Blue:AGREE のケースでも、Auditor は独立に Read で最低限の確認を行ってから採用する（詳細検証ではなくスポットチェックでよい）

## トリガー条件

- `/adversarial-review` で明示的に呼ばれた場合
- `auto-reviewing-pre-pr` が ESCALATE を返し、ユーザーがこのスキルを選択した場合
- 重要判断（DB スキーマ変更、認証フロー変更、外部 API 契約変更等）の前に

## ワークフロー

### Phase 1: コンテキスト準備

```bash
git diff $BASE_BRANCH > /tmp/adv_diff.patch
git diff $BASE_BRANCH --name-only > /tmp/adv_files.txt
mkdir -p ${MEMORY_DIR}/memory/<task>/adv
touch ${MEMORY_DIR}/memory/<task>/adv/queue.jsonl
```

CLAUDE.md と PJ ルールを読み込んで、Phase 2 のプロンプトに含める。
leadを`queue.jsonl`、`red.jsonl`、`blue.jsonl`の唯一のwriterにする。
RedとBlueはfinding/responseをleadへ返し、共有queueを直接編集しない。
レビューcycleごとに`cycle_id`（例: `C01`）を発行し、RedとBlueの起動promptへ渡す。

### Event contract

`adv/queue.jsonl`はappend-onlyのprotocol logであり、1行を1 JSON objectにする。

| event | 必須key | 用途 |
|---|---|---|
| `finding` | `cycle_id`, `finding_id`, `payload` | Red findingを保存する |
| `blue_response` | `cycle_id`, `red_finding_id`, `payload` | Blue responseを保存する |
| `ack` | `cycle_id`, `red_finding_id`, `stage` | leadがresponseを保存したことを示す |
| `red_eof` | `cycle_id`, `finding_ids`, `count` | Redの全finding IDを固定する |
| `reconcile` | `cycle_id`, `red_ids`, `blue_ids`, `missing_blue_ids`, `duplicate_ids`, `status`, `mode` | Auditor前の完全性を証明する |

例:

```jsonl
{"event":"finding","cycle_id":"C01","finding_id":"R001","payload":{"role":"red","finding_id":"R001","file":"src/api/users.ts","line":42,"severity":"CRITICAL","claim":"IDOR可能性","attack_vector":"他人のuserIdを送信","confidence":0.85}}
{"event":"blue_response","cycle_id":"C01","red_finding_id":"R001","payload":{"role":"blue","red_finding_id":"R001","red_claim_ref":"src/api/users.ts:42","verdict":"AGREE","reason":"スコープ検証なし","counter_evidence":null,"adjusted_severity":"CRITICAL","confidence":0.9}}
{"event":"ack","cycle_id":"C01","red_finding_id":"R001","stage":"blue_response_persisted"}
{"event":"red_eof","cycle_id":"C01","finding_ids":["R001"],"count":1}
{"event":"reconcile","cycle_id":"C01","red_ids":["R001"],"blue_ids":["R001"],"missing_blue_ids":[],"duplicate_ids":[],"status":"pass","mode":"streaming"}
```

`cycle_id + finding_id`と`cycle_id + red_finding_id`を重複排除keyにする。
完全に同じeventの再送は無視してよい。
内容が異なる同一IDは`duplicate_ids`へ記録し、protocol failureとしてbatchへ降格する。
agentからの返答は通知専用であり、queueへ保存されていないfinding/responseを処理済みとみなさない。
`queue.jsonl`をtruncateせず、再開時は対象`cycle_id`の最終eventから未処理IDを復元する。

### Phase 2: Red起動

`Agent(subagent_type: "red-reviewer")` を起動する。
Redには`cycle_id`、findingごとに返す形式、最後に`red_eof` manifestを返す契約を渡す。
leadは受信したfindingを検証し、`finding` eventとしてqueueへ保存してからBlueへ渡す。

### Phase 3: Blue逐次検証

最初のfindingをqueueへ保存した時点で `Agent(subagent_type: "blue-reviewer")` を1件だけ起動する。
後続findingは `SendMessage` で同じBlueへfollow-upとして渡す。
findingごとにBlueを新規起動しない。

Blue responseを受信したleadは、`blue_response`をqueueへ保存した後に`ack`を追記する。
Blueがturnを完了していても、`SendMessage` で同じagentを継続できる間はfollow-upで続ける。
同じagentを継続できない場合はprotocol failureとしてPhase 3.5へ進む。

Redがno-findingで終了した場合はBlueを起動せず、空の`red.jsonl`と`blue.jsonl`、`red_eof`、`reconcile status: pass`を作成してAuditorへ進む。

### Phase 3.5: protocol healthとbatch fallback

次のいずれかをprotocol failureとする。

- RedまたはBlueの起動失敗。
- finding/responseが進まず、leadがtaskごとに定めて05_log.mdへ記録したwait budgetを超える。
- queueを読み直せない、またはJSONLとしてparseできない。
- 同一IDで内容が衝突する。
- Red EOFのID集合とBlue responseのID集合が一致しない。
- Blueが`status: incomplete`を返す。

protocol failure時は、保存済みの一意なRed findingから`red.jsonl`を固定し、完成済み`red.jsonl`を入力としてBlueをbatch modeで実行する。
既存Blueが健全なら `SendMessage` で同じagentを使い、停止している場合だけreplacement Blueを1件起動して理由を05_log.mdへ記録する。
fallbackはfinding数に応じたfan-outを増やさない。

`SendMessage` による follow-up が最初から使えない場合は、streamingを試さず従来のbatch直列を使う。

### Phase 4: EOF reconciliationとsnapshot固定

Redの`red_eof.finding_ids`と、queueへ保存した全`blue_response.red_finding_id`を集合比較する。
重複、欠落、余分なIDが0件の場合だけ`reconcile status: pass`をqueueへ追記する。
queueの一意なfinding/responseから`red.jsonl`と`blue.jsonl`を固定する。

streamingまたはbatch fallbackのどちらでも、Auditor起動前にID集合が一致しなければならない。
照合に失敗したままAuditorへ進めない。

### Phase 4.5: Auditor起動

固定済み`red.jsonl`と`blue.jsonl`を結合したJSONを入力として `Agent(subagent_type: "auditor-reviewer", model: "opus")` を起動する。
streaming中のagent応答履歴はAuditor入力に含めない。
出力を`${MEMORY_DIR}/memory/<task>/adv/audit.jsonl`に保存する。

入力 JSON の組み立て例:

```json
{
  "red_findings": [/* red.jsonl を配列化 */],
  "blue_responses": [/* blue.jsonl を配列化 */],
  "context": {
    "files": ["..."],
    "diff": "...",
    "pj_rules": "...",
    "reconcile": {
      "cycle_id": "C01",
      "status": "pass",
      "mode": "streaming",
      "red_ids": ["R001"],
      "blue_ids": ["R001"]
    }
  }
}
```

### Phase 5: 結果集約とユーザー報告（CRITICAL）

`audit.jsonl` を読み、verdict 別に集計し、**チャット上に以下のサマリーを必ず出力する**（ファイル保存だけで終わらせない）。ユーザーが ADOPT/UPGRADE の対応可否、ESCALATE の判断、REJECT の妥当性を確認できる状態にしてから Phase 6 に進む:

```markdown
## Adversarial Review Result

### サマリー
- ADOPT: N件 (severity別: CRITICAL=X, IMPORTANT=Y, MINOR=Z)
- DOWNGRADE: N件
- UPGRADE: N件
- REJECT: N件
- ESCALATE: N件

### ADOPT/UPGRADE 詳細（必須対応）
（一覧）

### ESCALATE 詳細（人間判断要）
（一覧）AskUserQuestion で判断を求める

### 統計（バイアス指標）
- Red の指摘数: R
- Blue の AGREE 率: A%
- Blue の REJECT 率: B%
- Auditor の ADOPT 率: P%
- Red 過剰指摘指数: (R - ADOPT数) / R
- Blue 過剰却下指数: REJECT中ADOPTになった数 / REJECT総数
```

### Phase 6: ADOPT/UPGRADE の修正 → Phase 2 へ戻る or 完了

ADOPT の全件修正後、再度 Adversarial Review を回す（最大 2 サイクル）か、`auto-reviewing-pre-pr` で軽量再検証する。

## 並列化の方針

- Redのfinding生成とBlueの検証だけをpipeline化する。
- Blueは1 agentだけを使い、findingごとのfan-outを行わない。
- AuditorはRed EOFとBlue全応答のbarrier後に単独で起動する。
- streamingが不健全ならbatch直列へ戻す。
- ファイル単位で並列化したい場合は、各サイクルで別ファイル群を扱う

## コスト試算（参考）

- Red: `Agent(subagent_type: "red-reviewer")` — model省略（親継承）
- Blue: `Agent(subagent_type: "blue-reviewer")` — model省略（親継承）
- Auditor: `Agent(subagent_type: "auditor-reviewer", model: "opus")`
- **方針**: model 指定は Auditor のみ。Red/Blue は省略して親セッション継承

## 禁止事項

- Red をスキップして Blue から始めること
- agent応答履歴だけを監査の正本にすること
- queueへ保存する前にfinding/responseを処理済みとみなすこと
- Red EOFとBlue response IDの照合前にAuditorを起動すること
- findingごとにBlue agentを新規起動すること
- protocol failureを無視して不完全なstreaming結果をAuditorへ渡すこと
- Auditor の verdict を主観で書き換えること
- ESCALATE をユーザーに見せずに勝手に判定すること
- **Phase 5 のサマリーをチャット出力せずに Phase 6（修正）や完了報告へ進むこと**
- Auditor が Read で直接コードを確認せず Red/Blue の rationale だけで判定すること
- 多数決（Red+Blue 一致なら自動採用）を使うこと
