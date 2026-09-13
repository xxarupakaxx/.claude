---
name: designing-codebases
description: Module の interface、seam、testability を設計・比較するときに、deep-module の共通語彙で read-only の設計案を作る。別 skill がこの語彙を必要とするときにも使う。
---

# コードベース設計

小さな interface の裏へ複雑さを隠す **deep module** を設計する。成果は設計案と比較であり、実装・ADR作成・リポジトリ変更は行わない。対象は依頼範囲の module（通常1〜3個）に絞る。

## 用語

以下の表記を変えずに使う。`component`、`service`、`API`、`boundary` へ言い換えない。

- **Module**：interface と implementation を持つもの。function、class、package、tier をまたぐ slice を含む。
- **Interface**：caller が正しく使うために知る全事実。型 signature、invariant、順序制約、error mode、設定、性能特性を含む。
- **Implementation**：module 内部のコード本体。**Adapter**（seam で interface を満たす役割）とは分ける。
- **Depth**：interface の leverage。学ぶ interface の量に対して使える振る舞いが多いほど deep、implementation と同程度に複雑なら shallow。
- **Seam**（Michael Feathers）：その場所自体を編集せず振る舞いを変えられる場所、つまり module の interface の位置。DDD の意味を持つ `boundary` とは呼ばない。
- **Leverage**：一つの implementation が複数の call site と test に返す価値。
- **Locality**：変更、バグ、知識、検証を一か所に集める保守上の価値。

## 設計の基準

deep module は「小さな interface + 大きな implementation」、shallow module は「大きな interface + 小さな implementation」。interface を次で検討する。

- method 数と parameter を減らせないか。
- 複雑さを interface の内側へ隠せるか。
- module を消したとき、複雑さが一か所から消えるか、caller 全体へ再出現するか（**deletion test**）。
- caller と test が同じ external seam をまたぎ、internal seam は implementation 内の test にだけ見えるか。
- variation のない adapter 一つだけの seam を、仮説のまま増やしていないか。実際に二つ以上の adapter が必要なときに導入する。

## Testability

- dependency は受け取り、内部で `new` しない。
- 副作用を直接起こすより、計算結果を返す。
- surface area（method と parameter）を小さくし、test setup を単純にする。
- Interface は caller と test の test surface である。interface の先まで test したくなるなら module の shape を見直す。

## 出力

対象、現状の interface/implementation、候補案、seam と adapter、depth・leverage・locality、test 方針、採用理由と未確定事項を、根拠のある file:line とともに示す。実装やADRが必要になった場合は、上位 workflow の write scope と user gate へ引き渡す。

依存を踏まえた shallow module の deepening は [DEEPENING.md](DEEPENING.md)、別案の interface 比較は [DESIGN-IT-TWICE.md](DESIGN-IT-TWICE.md) を、該当する場合だけ読む。別案比較での parallel sub-agent は上位オーケストレーターの Delegation Gate を通す。
