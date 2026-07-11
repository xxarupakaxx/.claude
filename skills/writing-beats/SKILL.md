---
name: writing-beats
description: 文章の exploit を行い、各用語を使う前に理解の土台を作りながら、素材を beat の journey に組み立てる。
disable-model-invocation: true
---

<what-to-do>

ユーザーは素材が入った markdown file を渡しているか、これから渡す。
ここでは **exploit** を行う。
explore は終わり、素材の山は固定されているため、そこを通る path を決め、各 beat を満たす素材を採掘する。

article の保存先をユーザーが指定していない場合は一度だけ確認し、その path を覚えておく。

choose-your-own-adventure のように、beat ごとの journey を進める。

1. **前提知識を確定する。**
beat を書く前に、audience が読み始める時点ですでに知っていること、つまり最初から **grounded** になっている concept をユーザーと決める。
それ以外の concept は、後続 beat が使う前に別の beat で grounded にする必要がある。
[Grounding](#grounding) を参照する。
2. 素材から、**開始 beat** の候補を二、三件書く。
それぞれを article への異なる入口にする。
各候補が使えるのは grounded な concept だけであり、新しく grounded にする concept を併記する。
article file へ書く前に候補をユーザーへ示し、一つ選んでもらう。
選択した beat が次に開く path を、少し先まで見えるように preview する。
3. ユーザーが開始 beat を選んだら、**その beat だけ**を article file に書く。
beat は一文でも複数の段落でもよく、その beat に自然な長さにする。
そこで停止する。
4. disk から article file を読み直す。
続いて、現在地点から journey が進める異なる方向として、**次の beat** の候補を二、三件示す。
各候補は現在の grounded set から到達できなければならず、新しく grounded にする concept を併記する。
5. article が自然な終わりに到達するまで step 3 から 5 を繰り返す。

</what-to-do>

<supporting-info>

## Grounding

beat が **concept** を使う前に、その concept を **grounded** にする。
audience が読み始める前から知っているか、以前の beat で出会っていれば grounded である。
grounded になっていない concept を使う beat は読者を置き去りにするため、journey ではこの一手だけを避ける。
単位は concept であり、それを表す単語ではない。
jargon がなくても、読者が知らない idea を beat が使うことはある。
concept に **term** という名前がある場合、grounding では idea と term を一緒に定着させる。

concept を grounded にする方法は二つある。

- **Prerequisite**：最初の beat より前から grounded になっている。
audience が持ち込む知識であり、開始時に固定する。
- **Introduced**：beat が concept を確立し、それ以降のすべての beat で grounded になる。

各 beat には二つの役割がある。
すでに grounded の concept を**必要とし**、新しい concept を **grounded にする**。
現時点で grounded になっているものの list を持ち、beat が確定するたびに更新する。

これが choose-your-own-adventure の形を決める。
候補 beat に必要なすべての concept が grounded の場合だけ、その beat に到達できる。
concept X を grounded にする beat を選ぶと、X を待っていたすべての beat が選べるようになる。
次の beat の候補は、現在の grounded set から到達できるものだけにする。
各候補が何を grounded にするかも示し、その候補によって開く path をユーザーが確認できるようにする。

大きな調整点は、何を prerequisite とし、何を article 内で grounded にするかである。
最初に多くを求めすぎると、その知識のない読者を締め出す。
article 内で多くを grounded にしすぎると、序盤の beat が定義に埋もれる。
前提知識を確定するときにユーザーと決める。
魅力的な beat に、まだ grounded になっていない concept が必要だと判明した場合も見直す。
その前に grounding beat を置くか、その concept を prerequisite に上げる。

## Beat とは

beat は journey における一つの動きである。
scene を設定する、point を定着させる、question を出す、aside を差し込む、angle を反転させる、など一つのことだけを行う。
そこで止まり、次の beat が方向を変えられる地点に読者を置く。

beat の長さは必要な内容で決める。

- その動きが一文だけなら、一文にする（例：「それから三週間、何も起きなかった」）。
- setup が必要なら、短い段落にする。
- 自己完結した vignette、argument、example なら、複数の段落にする。

一つの「beat」に五つの段落と三つの subheading が必要なら、それは二つの beat をつないだものである。
分割する。

## 素材の山から取り出す

素材の山から各 beat に使う内容を取り出す。
paraphrase、分割、再結合、quote を行ってよい。
素材の山は quarry である。

## Journey を終える

article を終えるのは journey が完了したときであり、素材の山が空になったときではない。
大半の場合、使われない fragment が残る。
それでよい。
必要量を超える素材を用意する目的はそこにある。

## 書き進める rhythm

- 一度に一つの beat を追記し、先の beat まで書かない。
- 書き込む前には毎回、disk から article file を読み直す。
ユーザーの編集を必ず保持する。
- ユーザーが前の beat を大きく編集した場合は、その変更を次の内容に反映する。
- ユーザーが「その beat を書き直して」または「戻って別の beat 3 を試して」と言った場合は、その場所だけを編集し、残りには触れない。

</supporting-info>
