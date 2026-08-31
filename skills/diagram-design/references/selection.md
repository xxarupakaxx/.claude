# 選択ルール

図は、文章・表よりも関係を速く読めるときだけ使う。最初に「読者が何を判断するか」を一文で書き、次に semantic pattern、最後に visual type を決める。

## JIT routing

| 問い | pattern | type | 必要な参照 |
|---|---|---|---|
| 複数の入口が同じ module / service に集まり、共有依存や cycle を見たい | fan-in / dependency | dependency | `type-dependency.md` |
| 誰がどの順で入力を処理し、何を次へ渡すか | stage / handoff | process または data flow | `type-process.md` |
| component がどの zone にあり、どの境界を越えるか | secure route / boundary | architecture | `type-architecture.md` |
| 二つの状態、二つの判断、Before / After の対応を読みたい | paired trace / state comparison | table、必要なら comparison | `type-comparison.md` |

## 代表 pattern

- fan-in: source、queue、capacity、bottleneck、admitted / deferred を書く。箱の大きさだけで容量を表さない。
- stage: 同じ slot の意味を全 stage で保ち、空欄は `—` または `Not applicable` と書く。
- paired trace: 同じ順序の rule を2本に並べ、`PASS`、`FAIL`、`SKIPPED`、`NOT REACHED` を区別する。
- boundary: 許可された経路と遮断される経路を、線種と停止記号と文章で示す。

## 表へ戻る条件

3列程度の対応表で、順序・境界・共有依存を失わずに読めるなら図を作らない。単純な Before / After は「項目 / Before / After / 根拠」の表にする。図を作った場合でも、HTML に短いテキスト要約を残す。

## 分割と未知

一枚の overview は原則9 nodes、12 edges以内にする。詳細を削ると意味が変わるときは overview と detail に分け、どの node を統合・除外したかを fidelity ledger に残す。source にない名称・数値・状態は `unknown` とし、位置や色から推測しない。

Source basis: fixed upstream `SKILL.md` の semantic selection / visual type table と `references/semantic-patterns.md`。
