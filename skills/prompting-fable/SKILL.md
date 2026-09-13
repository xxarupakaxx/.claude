---
name: prompting-fable
description: "Claude Fable 5 に渡す長時間・自律・subagent前提の追補プロンプトを設計する。使用タイミング: 「fableに渡すプロンプト作って」「Fable 5に長時間タスクを投げる前に整えて」「Fable用のagent指示を作って」など。"
---

# Prompting Fable

この skill は汎用プロンプト設計を置き換えない。

既存のプロンプト骨格に、Claude Fable 5 固有の長時間実行、早期停止、context不安、証拠報告、reasoning抽出回避の追補を足す。

## 使う場面

- Fable 5 に長時間の実装、調査、レビュー、運用作業を任せる。
- subagent、非同期進捗、memory、長い context が関わる。
- 旧モデル向けの細かい手順を減らし、Fable 5 固有の詰まり方だけを補う。

単純な質問、短い翻訳、軽い要約では使わない。

## 責務境界

- 汎用の目的整理、文脈設計、XML構造化、few-shot は `prompt-engineering` 側に任せる。
- この skill は Fable 5 に足す差分だけを作る。
- 完成品は、既存プロンプト全体ではなく `Fable 5向け追補` として出す。

## Fable 5 差分

1. **長い turn 前提**: timeout、streaming、進捗表示、非同期確認を prompt または harness 側で決める。
2. **effort**: 難しい仕事は `high`、能力最優先は `xhigh`、対話速度優先は `medium` または `low`。
3. **過剰作業抑止**: 高い effort では、依頼外の機能、抽象化、未来対応を抑える。
4. **証拠つき進捗**: 進捗は tool result、差分、テスト、出典に対応させる。
5. **早期停止防止**: 計画や宣言で終わらず、入力が不要なら実行まで進める。
6. **context不安防止**: context残量だけを理由に新セッションやhandoffを提案させない。
7. **停止条件**: 止まるのは破壊的操作、不可逆操作、スコープ変更、本人しか知らない情報が必要な場合だけ。
8. **reasoning抽出回避**: chain-of-thought の再現を求めず、判断理由、根拠、検証結果、未解決事項を出させる。

## 出力

ユーザーには短い追補プロンプトだけを返す。

```text
Fable 5向け追補:
- 長時間実行を前提に、進捗は証拠と結びつける。
- 入力が本当に必要な場合だけ止まり、計画だけで終わらない。
- context残量や推論表示を理由に作業を止めない。
- 完了時は、結果、検証、残課題だけを読み手向けに報告する。
```

必要なら、対象タスクに合わせて effort、停止条件、検証方法、subagent検証の有無を1行ずつ足す。

## チェックリスト

- [ ] 追補が Fable 5 固有差分だけになっている。
- [ ] 長い turn と非同期確認の扱いがある。
- [ ] 早期停止と context不安への対策がある。
- [ ] 進捗報告が証拠に紐づく。
- [ ] 停止条件が本当にユーザー入力が必要な場面に限られている。
- [ ] chain-of-thought を本文へ出させる指示がない。

## 参照

- `Inbox/knowledge/Claude Fable 5 プロンプト作成メモ.md`
- Anthropic: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5
- Anthropic: https://platform.claude.com/docs/en/about-claude/models/introducing-claude-fable-5-and-claude-mythos-5
