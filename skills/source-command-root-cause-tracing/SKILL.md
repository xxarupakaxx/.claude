---
name: "source-command-root-cause-tracing"
description: "深い実行箇所で発現したエラーや無効データを、コールチェーンと値の流れを逆方向にたどって元のトリガーまで特定する `/root-cause-tracing` の互換 entry。"
---

# source-command-root-cause-tracing

ユーザーが `/root-cause-tracing [症状]` を求めたときに使う。エラーの発生箇所だけを直さず、元の入力・呼び出し・初期化まで追跡して、根拠のある修正候補を示す。深い call chain、長い stack trace、無効値の発生源が不明な場合に向く。逆追跡できない場合は、症状への暫定防御と不足する観測を分けて報告する。

## トレース

1. 症状、発生位置、再現条件を記録する。
2. 症状を直接起こす関数・操作と、その引数・環境を特定する。
3. caller を一段ずつ逆方向へたどり、渡された値がどこで生成・変換されたかを確認する。
4. 元の trigger（誤った入力、初期化順序、設定、test fixture など）を、path:line と観測結果で示す。
5. source での修正案と、各 layer の入力検証・境界防御が必要かを提案する。症状だけの patch を根本修正と扱わない。

## 計装が必要な場合

手動でたどれないときだけ、危険な操作の**前**に一時ログを置く。テストでは抑制されにくい `console.error()` を使い、directory、`process.cwd()`、必要な環境、timestamp、`new Error().stack` を含める。secret、token、個人情報、全 payload は出さない。例:

```typescript
const stack = new Error().stack;
console.error('TRACE-DIAGNOSE', { directory, cwd: process.cwd(), stack });
```

既存の test command で実行し、stderr を捕捉する。

```bash
npm test 2>&1 | grep 'TRACE-DIAGNOSE'
```

原因を確認したら一時計装を削除する。再発防止の永続ログは、必要性とデータ範囲を明記する。

## 完了条件

- 症状から trigger までの call chain と、各値の根拠が追える。
- 修正は trigger の位置に対応し、影響を受ける test を再実行できる。
- 必要なら入力 validation を層ごとに提案し、再現できない点と未確認事項を明示する。
