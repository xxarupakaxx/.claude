# Comparison / Before・After

## 第一選択は表

項目、Before、After、根拠の4列で、順序・共有依存・境界を失わず読めるなら表を作る。図は対応関係や最初の差分が空間配置で速く読める場合だけ使う。

## Before / candidate の共通契約

- Before と After は同じ `data-item` id で対応付ける。
- 表示順は同じにし、追加・削除には `added` / `removed` を文字で付ける。
- 変更理由、source anchor、未実装・unknown を各 item の近くに置く。
- Before は実測した現状、candidate は提案または実装済み状態として status を分ける。提案を実装済みと表示しない。
- 二つの dependency / architecture snapshot を並べる場合も、同じ node id と source binding を保つ。

## Paired policy trace

二つの入力が同じ ordered rules を進み、結果が異なる場合に使う。trace は exactly 2 本、rule は3–6個、first divergence は1つ、status cell は12個以内。`SKIPPED`（意図的に飛ばした）と `NOT REACHED`（前段で停止）を混同しない。全状態を初期表示し、色だけで PASS / FAIL を伝えない。

## Numeric slopegraph

二つの状態の同じ単位・同じ尺度の数値を4–10 seriesで比較するときだけ使う。全 endpoint に値を印字し、axis と origin を共有する。3状態以上、単位が違う値、単一 series、順位だけの説明には使わない。

Source basis: fixed upstream `SKILL.md` の table-first rule、`references/semantic-patterns.md` の paired trace、`references/type-line.md` の slopegraph。
