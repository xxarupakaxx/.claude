---
name: adversarial-review
description: 重要判断（アーキテクチャ・セキュリティ・性能クリティカル変更）に対し、Red(攻撃側) → Blue(防御側) → Auditor(審判) の3エージェントで多角検証する。auto-reviewing-pre-pr より高コストなので、ユーザーが明示的に呼び出すか auto-reviewing が ESCALATE した場合のみ起動。「アドバーサリアルレビューして」「Red/Blueで検証」「敵対的レビュー」等の依頼に対応。
context: current
---

# Adversarial Review — 三者敵対的レビュー

## 概要

通常レビューでは検出しづらい「reviewer のバイアス」を相互チェックするため、
Red（悲観派）→ Blue（楽観派）→ Auditor（審判）の順で 3 段レビューを行う。

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
```

CLAUDE.md と PJ ルールを読み込んで、Phase 2 のプロンプトに含める。

### Phase 2: Red 起動（直列、最初は Red 単独）

Task ツールで `red-reviewer` を起動。出力（JSONL）を `${MEMORY_DIR}/memory/<task>/adv/red.jsonl` に保存。

### Phase 3: Blue 起動

`red.jsonl` を入力として Task ツールで `blue-reviewer` を起動。
出力を `${MEMORY_DIR}/memory/<task>/adv/blue.jsonl` に保存。

### Phase 4: Auditor 起動

`red.jsonl` と `blue.jsonl` を結合した JSON を入力として Task ツールで `auditor-reviewer` を起動。
出力を `${MEMORY_DIR}/memory/<task>/adv/audit.jsonl` に保存。

入力 JSON の組み立て例:

```json
{
  "red_findings": [/* red.jsonl を配列化 */],
  "blue_responses": [/* blue.jsonl を配列化 */],
  "context": {
    "files": ["..."],
    "diff": "...",
    "pj_rules": "..."
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

- **Red 単独 → Blue 単独 → Auditor 単独**（直列）
- 並列化せず、前段の出力を必ず次段に渡す
- ファイル単位で並列化したい場合は、各サイクルで別ファイル群を扱う

## コスト試算（参考）

- Red: `Agent(subagent_type: "red-reviewer")` — model省略（親継承）
- Blue: `Agent(subagent_type: "blue-reviewer")` — model省略（親継承）
- Auditor: `Agent(subagent_type: "auditor-reviewer", model: "opus")`
- **方針**: model 指定は Auditor のみ。Red/Blue は省略して親セッション継承

## 禁止事項

- Red をスキップして Blue から始めること
- Auditor の verdict を主観で書き換えること
- ESCALATE をユーザーに見せずに勝手に判定すること
- **Phase 5 のサマリーをチャット出力せずに Phase 6（修正）や完了報告へ進むこと**
- Auditor が Read で直接コードを確認せず Red/Blue の rationale だけで判定すること
- 多数決（Red+Blue 一致なら自動採用）を使うこと
