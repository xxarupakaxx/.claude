# 深掘り設計

dependency を踏まえながら、shallow module の塊を安全に deepening する方法をまとめます。
[SKILL.md](SKILL.md) にある **Module**、**Interface**、**Seam**、**Adapter** の語彙を前提にします。

## 依存関係の分類

deepening 候補を評価するときは、まず dependency を分類します。
どの分類に入るかで、deepened module をどの seam 越しに test するかが決まります。

### 1. プロセス内

純粋計算、in-memory state、I/O なしの dependency です。
これは常に deepening できます。
module をまとめて、新しい interface 越しにそのまま test します。
adapter は不要です。

### 2. ローカルで差し替え可能

local の test stand-in を持てる dependency です。
たとえば Postgres に対する PGLite や、in-memory filesystem です。
stand-in があるなら deepening できます。
deepened module は、その stand-in を test suite 上で動かしたまま test します。
seam は内部にあり、module の external interface に port は出しません。

### 3. リモートだが自分たちが管理するもの（Ports & Adapters）

network boundary の向こう側にある、自分たちの service です。
microservice や internal API がこれに当たります。
seam の位置に **port**（interface）を定義します。
deep module が logic を持ち、transport は **adapter** として injection します。
test では in-memory adapter を使います。
production では HTTP、gRPC、queue などの adapter を使います。

推奨の形は次のようになります。
*「seam に port を定義し、production 用に HTTP adapter、testing 用に in-memory adapter を実装する。 そうすることで、network 越しに展開されていても、logic 自体は一つの deep module に置ける。」*

### 4. 真の外部依存（Mock）

Stripe や Twilio のような third-party service です。
こちらで制御できません。
deepened module は external dependency を injected port として受け取ります。
test では mock adapter を渡します。

## seam の規律

- **adapter が一つなら仮説上の seam で、二つあって初めて本物です。**
  少なくとも二つの adapter が正当化されないなら、port を導入してはいけません。
  典型例は production と test の二つです。
  adapter が一つしかない seam は、ただの indirection です。
- **internal seam と external seam を混同しません。**
  deep module は、自分の test のために implementation 内に internal seam を持てます。
  しかし test が使うからといって、それを interface へ露出させてはいけません。

## テスト方針: 重ねずに置き換える

- shallow module に対する旧 unit test は、deepened module の interface 上に test がそろった時点で不要です。
  消します。
- 新しい test は deepened module の interface に書きます。
  **interface が test surface** です。
- test は interface 越しに観測できる結果だけを確認し、internal state を直接見ません。
- test は internal refactor をまたいでも生き残る必要があります。
  test が implementation 変更のたびに直るなら、それは interface の先を test しています。
