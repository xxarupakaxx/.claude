# ロジックプロトタイプ

ユーザーが state model を手で動かせる、小さな interactive terminal app を作ります。
問いが **business logic、state transition、data shape** に関するものなら、この形を使います。
紙の上では筋が良く見えても、実際の case に通した瞬間に違和感が出るような種類の問いに向いています。

## これが適した形である場面

- 「この state machine は、X のあとに Y が来る edge case をちゃんと扱えるか分からない。」
- 「この data model で、本当にこの case を表現できるのか確かめたい。」
- 「実装前に API の shape を手触りで確かめたい。」
- ユーザーが **button を押して state が変わる様子を見たい** 場面全般。

問いが「どう見えるべきか」であるなら branch が違います。
[UI.md](UI.md) を使います。

## 手順

### 1. 問いを明文化する

code を書く前に、何の state model を、どんな問いのために prototype するのかを書きます。
場所は prototype の README でも、file 先頭 comment でも構いません。
問いを間違えた logic prototype は完全な無駄です。
ユーザーが今見ていようと、あとで AFK で戻ってこようと、問いを検証できる状態にしておきます。

### 2. 言語を選ぶ

host project が使っている言語を使います。
project に明確な runtime がなければ、ユーザーに聞きます。

tooling も project の既存 convention に合わせます。
prototype のためだけに新しい package manager や runtime を持ち込んではいけません。

### 3. logic を持ち運べる module に隔離する

問いに答える本体の logic は、小さく pure な interface の裏に置きます。
あとで real codebase へ持ち上げられる形にするためです。
TUI は throwaway ですが、logic module はそうではありません。

向いている shape は問いによって変わります。

- **pure reducer**。
  `(state, action) => state` の形です。
  action が離散 event で、state が一つの値としてまとまるときに向きます。
- **state machine**。
  state と transition を明示します。
  「今どの action が legal なのか」自体が問いに含まれるときに向きます。
- **plain data type に対する小さな pure function 群**。
  implicit な current state がなく、transformation だけを見たいときに向きます。
- **clear な method surface を持つ class または module**。
  logic が継続的な internal state を本当に所有するなら、この形でも構いません。

TUI に配線しやすいかどうかではなく、問いに最も合う shape を選びます。
logic は pure に保ちます。
I/O、terminal code、制御フローのための `console.log` は入れません。
TUI がそれを import して呼び出し、逆方向には何も流さないようにします。

この分離があるからこそ、prototype は寿命を超えて役に立ちます。
問いに答えが出たあと、validated な reducer、machine、function set を、そのまま real module に lift できます。

### 4. state を見せる最小 TUI を作る

**lightweight TUI** として作ります。
各 tick ごとに画面を clear し、frame 全体を再描画します。
`console.clear()`、`print("\033[2J\033[H")`、または同等の方法で構いません。
scrollback が伸び続けるのではなく、常に一つの安定した view が見える状態にします。

各 frame は、次の二部構成にします。

1. **Current state**。
   pretty-print し、diff を目で追いやすい形にします。
   一行一 field でも、整形 JSON でも構いません。
   field 名や section header には **bold** を使います。
   timestamp、ID、derived value のような重要度の低い情報には **dim** を使います。
   native ANSI escape code をそのまま使って構いません。
   `\x1b[1m` は bold、`\x1b[2m` は dim、`\x1b[0m` は reset です。
   project にすでにあるのでなければ、styling library を増やす必要はありません。
2. **Keyboard shortcut**。
   frame の下部に並べます。
   たとえば `[a] add user  [d] delete user  [t] tick clock  [q] quit` のようにします。
   key を bold にするか、説明を dim にするかは、読みやすさで決めます。

振る舞いは次のとおりです。

1. **Initialise state**。
   一つの in-memory object か struct を用意し、起動時に最初の frame を描画します。
2. **Read one keystroke（or one line）**。
   一回ごとに読み取り、handler に dispatch して state を変えます。
3. **Re-render**。
   各 action のあとに frame 全体を再描画します。
   append ではなく置き換えです。
4. **Loop until quit**。
   quit するまで繰り返します。

frame 全体は一画面に収まるようにします。

### 5. 一つの command で動くようにする

project の既存 task runner に script を追加します。
`package.json` scripts、`Makefile`、`justfile`、`pyproject.toml` などです。
ユーザーは `pnpm run <prototype-name>` など、一つの command だけ覚えればよい状態にします。
path を思い出させてはいけません。

host project に task runner がなければ、prototype の README 冒頭に command を書きます。

### 6. ユーザーへ渡す

run command をユーザーに渡します。
実際に操作するのはユーザーです。
「それは起きてはいけない」「X になると思っていたのに違う」という瞬間こそ、*アイデア側* の bug が露出する瞬間です。
それがこの prototype の目的です。
必要なら action を追加します。
prototype は学びに応じて育って構いません。

### 7. 答えと prototype を捕捉する

prototype が問いに答えたら、まず答えを残します。
そのあとで、[SKILL](SKILL.md) に書かれた形で prototype 自体も捕捉します。
logic prototype では、validated な reducer、machine、function set が real module に lift されます。
一方で TUI shell は throwaway branch 側へ移し、prototype を primary source として残します。

## アンチパターン

- **test を追加しない。**
  test が必要になった prototype は、もはや prototype ではありません。
- **real database に配線しない。**
  問い自体が persistence についてでない限り、in-memory store を使います。
- **一般化しない。**
  「将来 X をサポートしたくなったら」は考えません。
  prototype は一つの問いだけに答えます。
- **logic と TUI を混ぜない。**
  reducer や state machine が `console.log`、prompt、terminal escape code を参照していたら、もはや持ち運べません。
  TUI は pure module の薄い shell に保ちます。
- **TUI shell を production に出さない。**
  shell は terminal で手で回すために最適化されています。
  残す価値があるのは、その背後にある logic module のほうです。
