---
name: designing-codebases
description: 深い module を設計するための共通語彙です。 module の interface を設計したいとき、改善したいとき、どこに seam を置くか決めたいとき、コードを test しやすくしたいとき、AI がたどりやすくしたいとき、または別 skill が deep-module 語彙を必要とするときに使います。
---

# コードベース設計

**深い module** を設計します。
これは、小さな interface の裏に多くの振る舞いを置き、きれいな seam に載せ、その interface を通して test できる module のことです。
コードを設計したり組み替えたりするときは、ここで示す言葉と原則を使います。
狙いは、caller には leverage を、保守者には locality を、全員には testability をもたらすことです。

## 用語集

ここにある語はそのまま使います。
`component`、`service`、`API`、`boundary` などへ言い換えてはいけません。
言葉をそろえること自体が目的の一つです。

**Module** — interface と implementation を持つもの全般です。
function、class、package、tier をまたぐ slice まで含みます。
大きさには依存しません。
_Avoid_: unit、component、service。

**Interface** — caller が module を正しく使うために知っていなければならない事実すべてです。
型 signature だけではなく、invariant、順序制約、error mode、必要な設定、性能特性も含みます。
_Avoid_: API、signature。
それらは型レベルの表面しか指せず、狭すぎます。

**Implementation** — module の内側にあるコード本体です。
これは **Adapter** と区別します。
小さな adapter でも implementation は大きいことがあります。
逆に大きな adapter でも implementation は小さいことがあります。
seam が主題なら「adapter」を使い、それ以外なら「implementation」を使います。

**Depth** — interface における leverage のことです。
caller や test が、学ぶ interface の量に対してどれだけ多くの振る舞いを使えるかを表します。
大量の振る舞いが小さな interface の裏に収まっているなら module は **deep** です。
interface が implementation に近い複雑さを持っているなら **shallow** です。

**Seam**（Michael Feathers）— その場所自体を編集せずに振る舞いを変えられる場所です。
言い換えると、module の interface が置かれている *場所* です。
seam をどこに置くかは、それ自体が設計判断です。
その奥に何を置くかとは別の話です。
_Avoid_: boundary。
DDD の bounded context と意味が重なり過ぎます。

**Adapter** — seam に置かれ、interface を満たす具体物です。
これは中身の話ではなく、*役割* の名前です。

**Leverage** — deep さによって caller が得るものです。
一つの implementation が、N 個の call site と M 個の test に返済してくれます。

**Locality** — deep さによって保守者が得るものです。
変更、バグ、知識、検証が caller 全体へ拡散せず、一か所に集まります。
一度直せば、どこでも直ります。

## 深いものと浅いもの

**Deep module** = 小さな interface + 大きな implementation。

```
┌─────────────────────┐
│   Small Interface   │  ← Few methods, simple params
├─────────────────────┤
│                     │
│  Deep Implementation│  ← Complex logic hidden
│                     │
└─────────────────────┘
```

**Shallow module** = 大きな interface + 小さな implementation。
これは避けます。

```
┌─────────────────────────────────┐
│       Large Interface           │  ← Many methods, complex params
├─────────────────────────────────┤
│  Thin Implementation            │  ← Just passes through
└─────────────────────────────────┘
```

interface を設計するときは、次を自問します。

- method 数を減らせないか。
- parameter をもっと単純にできないか。
- さらに多くの複雑さを内側へ隠せないか。

## 原則

- **Depth は implementation ではなく interface の性質です。**
  deep module の内部は、小さく mock 可能で差し替え可能な部品で構成されていて構いません。
  ただし、それらは interface には出しません。
  module には **internal seam** があり得ます。
  それは implementation の中にあり、自分の test が使います。
  一方で caller と test がまたぐ **external seam** は interface の位置にあります。
- **deletion test。**
  その module を消したと想像します。
  複雑さが消えるなら、それは単なる pass-through でした。
  複雑さが N 人の caller に再出現するなら、その module は役に立っていました。
- **interface が test surface です。**
  caller も test も同じ seam をまたぎます。
  interface の先を test したくなるなら、その module の shape が違っている可能性が高いです。
- **adapter が一つなら仮説上の seam で、二つあって初めて本物です。**
  実際に variation がないのに seam を導入してはいけません。

## テストしやすさのための設計

良い interface は test を自然にします。

1. **dependency は受け取り、内部で new しません。**

   ```typescript
   // Testable
   function processOrder(order, paymentGateway) {}

   // Hard to test
   function processOrder(order) {
     const gateway = new StripeGateway();
   }
   ```

2. **副作用を起こすより、結果を返します。**

   ```typescript
   // Testable
   function calculateDiscount(cart): Discount {}

   // Hard to test
   function applyDiscount(cart): void {
     cart.total -= discount;
   }
   ```

3. **surface area を小さく保ちます。**
   method が少ないほど必要な test は減ります。
   parameter が少ないほど test setup は単純になります。

## 関係

- **Module** は caller と test に見せる一つの **Interface** を持ちます。
- **Depth** は **Module** の性質であり、**Interface** に対して測られます。
- **Seam** は **Module** の **Interface** が置かれる場所です。
- **Adapter** は **Seam** に座り、**Interface** を満たします。
- **Depth** は caller に **Leverage** を、保守者に **Locality** を生みます。

## 採用しなかった考え方

- **implementation 行数 ÷ interface 行数として depth を測る考え方**。
  これは implementation を水増しするほど有利になるので採りません。
  ここでは leverage としての depth を使います。
- **TypeScript の `interface` keyword や public method だけを Interface とみなす考え方**。
  それでは狭すぎます。
  ここでの interface には、caller が知る必要のある事実をすべて含めます。
- **Boundary**。
  DDD の bounded context と重なり過ぎるので使いません。
  必要なときは **seam** か **interface** と言います。

## さらに掘る

- **dependency を踏まえて shallow module 群を deepening する方法** は [DEEPENING.md](DEEPENING.md) を見ます。
- **別案の interface を並べて比較する方法** は [DESIGN-IT-TWICE.md](DESIGN-IT-TWICE.md) を見ます。
  parallel sub-agent を起動し、radically different な interface を複数案作ってから、depth、locality、seam placement で比べます。
