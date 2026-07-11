---
name: writing-shape
description: 文章の exploit を行い、素材を一段落ずつ article の形に整える。
disable-model-invocation: true
---

<what-to-do>

ユーザーは素材が入った markdown file を渡しているか、これから渡す。
整った fragment の list、構造化されていない prose の塊、transcript など、どのような形式でも input の山として扱う。
形式は問わない。
他の作業を始める前に最初から最後まで読む。

その後、別の article document を作る shaping session を進める。
ここでは **exploit** を行う。
explore は終わり、素材の山は固定されているため、structure を決め、素材を採掘して埋める。
素材ファイルはこの skill では read-only であり、編集してはならない。

article の保存先をユーザーが指定していない場合は一度だけ確認し、その path を覚えておく。

</what-to-do>

<supporting-info>

## Loop

1. **素材の山を読む。**
input file をすべて読み、含まれる内容を把握する。
2. **前提知識を確定する。**
読者が読み始める時点ですでに知っていること、つまり最初から **grounded** になっている concept をユーザーと決める。
それ以外の concept は、後続 block が使う前に別の block で grounded にする必要がある。
[Grounding](#grounding) を参照する。
3. **opening の候補を二、三件作る。**
それぞれの opening が article の異なる thesis または angle を示すようにする。
すべてを提示し、ユーザーに一つを選ぶか、組み合わせてもらう。
選ばれた opening によって、article の残りの役割が決まる。
4. **一段落ずつ育てる。**
opening が確定したら、「この opening を踏まえ、読者が次に聞く必要があることは何か」と問う。
答えになる素材を山から取り出す。
次の block が使えるのは grounded の concept だけであり、配置された block は新しい concept を grounded にする。
次の block の形式をユーザーと議論する。
paragraph、list、table、callout、quote、code block などから選ぶ。
形式の選択には意図があり、理由を説明できなければならない。
5. **進行に合わせて article file へ追記する。**
まとめて書かない。
合意した paragraph または block をすぐに書き、article が形になる様子をユーザーが確認できるようにする。
6. **article が完成するまで step 4 を繰り返す。**
完成の判断はユーザーが行う。

## Grounding

block が **concept** を使う前に、その concept を **grounded** にする。
読者が読み始める前から知っているか、以前の block で出会っていれば grounded である。
grounded になっていない concept を使う block は読者を置き去りにする。
単位は concept であり、それを表す単語ではない。
jargon がなくても、読者が知らない idea を block が使うことはある。
concept に **term** という名前がある場合、grounding では idea と term を一緒に定着させる。

concept を grounded にする方法は二つある。

- **Prerequisite**：opening より前から grounded になっている。
読者が持ち込む知識であり、開始時に固定する。
- **Introduced**：block が concept を確立し、それ以降の article 全体で grounded になる。

grounded になっているものの list を持つ。
「読者が次に聞く必要があることは何か」と問うとき、次の動きに必要な未 grounded の concept が答えになる。
最初にその concept を grounded にする。
現在の位置または以前の block で grounding できなければ、次の動きへ進めない。
これは [素材の山から取り出す](#素材の山から取り出す) で不足を名付ける作業を一段上げたものである。
そちらでは素材の山に内容が不足し、こちらでは article に土台が不足している。

調整点は、何を prerequisite とし、何を article 内で grounded にするかである。
最初に多くを求めすぎると読者を締め出す。
article 内で多くを grounded にしすぎると、opening が定義に埋もれる。
前提知識を確定するときにユーザーと決める。

## 会話として進める

これは grilling session を反転したものである。
ideation では「実際に何へ気付いているのか」と問う。
ここでは「この article は実際に何を主張し、読者はどの順序で聞く必要があるか」と問う。
必要なら反論する。
弱い transition を見逃さない。
paragraph が役割を果たさないなら削る。

繰り返し使う具体的な問い：

- 「この paragraph は、前の paragraph では得られなかった何を読者へ与えますか。」
- 「これを削ると、何が壊れますか。」
- 「これは prose と list のどちらにすべきで、prose を選ぶ理由は何ですか。」
- 「この文は二つの役割を持っているため、分割するか一つを選んでください。」
- 「opening は X を約束しましたが Y へ逸れているため、X へつなぎ直すか opening を変更してください。」

## 素材の山から取り出す

素材は script ではなく quarry として扱う。
fragment を取り出し、周囲の paragraph に合うよう手直しして配置する。
一つの fragment を複数の paragraph に分割し、別の fragment と統合し、または paraphrase してよい。
素材の山は採掘されるためにあり、article は一つの voice として読める必要がある。

article に必要なものが素材の山にない場合は、不足を明示する。
「ここには example が必要ですが素材の山にないため、今ここで一つ挙げるか、この section を削ってください。」

## 実際に議論する形式

block の表現方法を選ぶときは、次の tradeoff を黙って判断せず、ユーザーと声に出して比較する。

- **Prose と list。**
prose は argument を運び、list は並列の項目を運ぶ。
項目が本当に並列でなければ prose がよい。
並列なら list の方が速く読める。
- **Inline と callout。**
tip、warning、aside は callout（`> [!TIP]`、`> [!NOTE]`）へ置く。
ただし、inline に置くと main argument を本当に妨げる場合だけにする。
それ以外は inline のままにする。
- **Table と反復構造。**
同じ field を持つ同じ形が三回以上繰り返されるなら table を使う。
それ以外は太字の導入を伴う prose にする。
- **Quote と paraphrase。**
元の言い回し自体が重要なら quote する。
idea だけが重要なら paraphrase する。
- **Code block と inline code。**
複数行、実行可能、または説明用なら block にする。
単一の token または identifier なら inline にする。

## 書き進める rhythm

各 block への合意が得られたら article file へ追記する。
書き込む前には毎回、disk からファイルを読み直す。
turn の間にユーザーが編集している可能性がある。
内容を確認せずに上書きしてはならない。
ユーザーが paragraph の書き直しを求めた場合は、その paragraph だけをその場で編集し、残りには触れない。

## 対象外

- 素材の山にない新しい fragment の採掘（不足は「素材の山から取り出す」に従って扱う）。
- 素材ファイルの編集。
- 公開、特定 platform 向けの整形、ユーザーが依頼していない frontmatter の追加。

</supporting-info>
