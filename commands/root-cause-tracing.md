---
name: root-cause-tracing
description: 実行の深い場所で発生したerrorや不正データを、症状からcall chainと入力の生成元へ逆向きにたどる。stack trace、instrumentation、テスト起因の診断を依頼されたときに使う。
---

# ルートコーズトレーシング

エラーが表示された行だけを直さず、直接の原因、呼出元、渡された値、最初の不正入力を確定してsourceで修正する。入口が不明、stackが長い、同じ症状が複数経路から出る場合に適用する。

## トレース

1. **症状を固定**: 完全なerror、実行時点、対象path、入力、環境、再現条件を保存する。
2. **直接の原因**: 失敗した操作を呼ぶfile・symbol・引数を確認する。エラー文だけで根本原因と断定しない。
3. **一段上へ戻る**: caller、さらにcallerへ進み、各段で何を呼び、どのpayload/値を渡したかを記録する。
4. **最初の不正値**: 空値、既定値、変換、fixture、設定、環境のどこで誤った値が生まれたかを特定する。import経路と実行入口をsourceで確定する。
5. **sourceを直す**: 生成元または境界で修正し、必要なら下流の複数層にもvalidation・guard・明確なerrorを置く。
6. **再現と回帰**: 元の再現、原因境界のtest、関連する回帰確認を実行し、instrumentationを不要なら削除する。

トレースが外部権限、環境差、未接続サービスで止まったら、推測で埋めず、最後に確認できた値と外部要因を分けて報告する。

## 計装

静的な追跡で行き止まりになったときだけ、危険な操作の**前**に一時的な計装を置く。テストではloggerが抑制されることがあるため `console.error()` を使う。

```typescript
async function riskyOperation(directory: string) {
  console.error('DEBUG riskyOperation', {
    directory,
    cwd: process.cwd(),
    nodeEnv: process.env.NODE_ENV,
    stack: new Error().stack,
  });
  return runOperation(directory);
}
```

操作後ではなく直前に、path/cwd、必要な環境、timestamp、入力の安全な要約、完全なstackを出す。秘密、token、個人情報、raw requestをログや委譲へ渡さない。取得したログは目的のpatternだけを絞って読む。

```bash
npm test 2>&1 | grep 'DEBUG riskyOperation'
```

計装は原因確認後に削除または最小化し、デバッグ出力を本番へ残さない。`git init`、file write、DB openなどpathを受ける操作は、空値・相対path・許可rootを境界で検証する。

## 多層防御

根本修正に加え、同じ誤りが別経路から入る場合だけ層を追加する。

| 層 | 例 |
| --- | --- |
| input boundary | 必須値、型、許可されたpath/範囲 |
| domain/API | 不正状態を表せない型、前提条件、明確なerror |
| side-effect boundary | root外write、環境、権限、transactionのguard |
| test/observability | 回帰test、失敗時の安全なcontext、監視 |

同じguardを無根拠に各層へ複製せず、どの再発経路を防ぐかを記録する。症状の場所だけにfallbackを置いて誤りを隠さない。

## 完了条件

- 実行入口から失敗点までのcall chainと各payloadがsource anchorへ戻れる。
- 最初に不正値が生まれた場所、または外部要因で未確認の境界が明示されている。
- 根本修正と、必要な多層防御の理由が分かれている。
- 元の再現と回帰確認が通り、未確認の環境や推測をPASS扱いしていない。
