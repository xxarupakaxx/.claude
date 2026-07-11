# 別案を二度設計する

選んだ deepening 候補に対して、別案の interface を見比べたいときに使う parallel sub-agent pattern です。
Ousterhout の「Design It Twice」を踏まえています。
最初に思いついた案が最良である可能性は低い、という前提です。

[SKILL.md](SKILL.md) にある **Module**、**Interface**、**Seam**、**Adapter**、**Leverage** の語彙を使います。

## 手順

### 1. 問題空間を定義する

sub-agent を起動する前に、選んだ候補について、ユーザー向けの問題空間説明を書きます。
そこには次を含めます。

- 新しい interface が満たすべき制約。
- 依存する dependency と、その分類。
- 制約を具体化するための大まかな code sketch。

dependency の分類は [DEEPENING.md](DEEPENING.md) を参照します。
code sketch は proposal ではなく、制約を手触りのあるものにするための補助です。

これをユーザーに見せたら、すぐに手順 2 へ進みます。
ユーザーが読みながら考えている間に、sub-agent を parallel に働かせます。

### 2. 並列エージェントを起動する

3 体以上の sub-agent を parallel に起動します。
Claude Code では Agent tool を使います。
Codex では `multi_agent_v1.spawn_agent` または現在利用できる agent orchestration を使い、互いに独立した planner または architecture reviewer 相当の role を起動します。
それぞれが、deepened module に対して **根本的に異なる** interface を出す必要があります。

各 sub-agent には、別々の technical brief を渡します。
そこには file path、coupling の詳細、[DEEPENING.md](DEEPENING.md) 上の dependency category、seam の奥に何があるかを含めます。
この brief は、手順 1 のユーザー向け説明とは別物です。
さらに agent ごとに設計制約を変えます。

- Agent 1: 「interface を最小化する。 entry point は最大 1〜3 個を目安にし、entry point ごとの leverage を最大化する。」
- Agent 2: 「柔軟性を最大化する。 多様な use case と extension を支えられるようにする。」
- Agent 3: 「もっとも一般的な caller に最適化する。 default case を圧倒的に簡単にする。」
- Agent 4（必要なら）: 「cross-seam dependency を ports & adapters として扱う前提で設計する。」

brief には [SKILL.md](SKILL.md) の語彙と `CONTEXT.md` の語彙の両方を含めます。
そうすることで、各 sub-agent が architecture language と project の domain language をそろえたまま名前を付けられます。

各 sub-agent の出力には次を含めます。

1. interface。
2. usage example。
3. seam の奥に implementation が何を隠すか。
4. dependency strategy と adapter。
5. trade-off。

interface には type、method、parameter だけでなく、invariant、順序制約、error mode も含めます。
dependency strategy と adapter については [DEEPENING.md](DEEPENING.md) を参照します。
trade-off では、どこに leverage があり、どこが薄いかを説明させます。

### 3. 提示して比較する

design は順番に提示します。
ユーザーが一案ずつ消化できるようにするためです。
その後、prose で比較します。
比較軸は **Depth**、**Locality**、**Seam placement** です。

最後に、自分の recommendation を明言します。
どの design が最も強いと思うか、その理由まで言います。
複数案の要素を組み合わせるのが良いなら、hybrid 案を提案します。
遠慮せず意見を出します。
ユーザーが欲しいのは、ただの menu ではなく、強い読みだからです。
