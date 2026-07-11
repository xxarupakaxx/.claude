---
name: mapping-large-projects
description: 一つの agent session には収まらない巨大な作業を、issue tracker 上で共有する調査 ticket の map として計画する。目的地までの道筋が明確になるまで、ticket を一つずつ解決する。
disable-model-invocation: true
---

一つの agent session では扱えず、ここから**目的地**までの道がまだ見えない、霧に包まれた大まかな idea が届いたとする。
Wayfinding の目的は、目的地へ突進することではなく、そこへ至る道を見つけることである。
この skill は、repo の issue tracker に道筋を**共有 map**として描き、route が明確になるまで ticket を一つずつ進める。

目的地は effort ごとに異なり、名前を付けることが作図の最初の行為になる。
目的地がすべての ticket の形を決める。
目的地は、引き渡して反復する仕様書、計画前に確定すべき決定、data-structure migration のようにその場で行う変更などである。
map は domain を問わず、engineering work、course content など、この形に合うものに使える。

## 実行せず、計画する

Wayfinder は既定では**計画**を行う。
各 ticket で一つの決定を解決し、誰かが実行へ移る前に決めるべきことがなくなり、道筋が明確になった時点で map は完了する。
作業を実行したくなったら、通常は map の端まで到達し、引き渡す時期が来たことを示す。
effort の **Notes** で override し、実行自体を map に含めることもできる。
その指定がなければ deliverable ではなく decision を作る。

## 名前で参照する

map と ticket はすべて issue であるため、title という**名前**を持つ。
人間が読むすべての場所（説明、map の Decisions-so-far）では、id、number、slug だけで参照せず、必ず名前で参照する。
`#42, #43, #44` が並ぶだけでは読めないが、名前なら一目で分かる。
id と URL は消さず、名前を link にすることで、その*内側*に含める。
名前の代わりに単独で置かない。

## Map

map はこの repo の issue tracker にある一つの issue であり、`wayfinder:map` label を付ける。
これが正式な artifact になる。
ticket は map の child issue とする。

map は**索引**であり、情報の保存場所ではない。
決定事項を列挙し、詳細を持つ ticket を指す。
一つの decision は一つの ticket だけに置くため、map では再説明せず gist と link だけを記す。

**map、child ticket、blocking、frontier query を実際に置く場所と表現方法は tracker ごとに異なる。**
issue tracker の情報は事前に提供されている必要がある。
提供されていない場合は `/setting-up-engineering-skills` を実行する。
この repo での表現方法は、tracker 文書の「Wayfinding 操作」section を参照する。
tracker が提供されていない場合は local-markdown tracker を使う。

### map の body

map 全体を低い解像度で表し、session ごとに一度だけ読み込む。
open ticket は列挙しない。
open child issue として query で見つける。

```markdown
## Destination

<この map の終点に到達した状態を書く。この effort が道筋を探している仕様書、決定、変更などを一、二行で示す。各 session は ticket を選ぶ前に、これを読んで方向を確認する。>

## Notes

<domain、各 session で参照する skill、この effort で常に守る設定を書く。>

## Decisions so far

<!-- 索引。close 済み ticket ごとに一行を書く。関連性を判断できる gist を示し、詳細を持つ ticket へ link する。 -->

- [<close 済み ticket の title>](link)：<回答の一行 gist>

## Not yet specified

<!-- 「Fog of war」を参照。まだ ticket にできない scope 内の霧を記す。frontier が進むと ticket になる。 -->

## Out of scope

<!-- 「Out of scope」を参照。目的地の先にあると判断した作業を記す。close 済みであり、ticket にはならない。 -->
```

### Ticket

各 ticket は map の **child issue** であり、tracker の issue id が identity になる。
body には、一つの 100K token agent session で扱える大きさの question を書く。

```markdown
## Question

<この ticket で解決する決定または調査>
```

各 ticket に `wayfinder:<type>` label を付ける。
type は `research`、`prototype`、`grilling`、`task` のいずれかである（[Ticket type](#ticket-type) を参照）。

session は作業を始める**前に**、map を進める developer を ticket の assignee に設定して **claim** する。
これにより、並行する session はその ticket を避ける。
assignee が claim そのものである。
open かつ unassigned の ticket は unclaimed である。

blocking には tracker の **native** dependency relationship を使う。
tracker 自身の UI に frontier が*視覚的に*表示され、人間が map を開かずに着手可能な ticket を確認できるため、この表現が必要である。
native blocking のない tracker だけが body の規約へ fallback する。
block しているすべての ticket が close されると ticket は **unblocked** になる。
open、unblocked、unclaimed の child が **frontier** であり、既知の領域の端を表す。

回答は body に含めない。
解決時に記録する（[map を進める](#map-を進める) を参照）。
ticket の解決中に作成した asset は issue に link し、貼り付けない。

## Ticket type

すべての ticket は **HITL** または **AFK** である。
HITL は human in the loop を表し、自分の意見を話す人間と*一緒に*進める。
AFK は agent が単独で進める。
HITL ticket は live な対話を通じてのみ解決する。
agent が人間側を代行してはならない。
問いを出す agent が自分で回答した場合、この規則に違反している。

- **Research**（AFK）：documentation、third-party API、knowledge base などの local resource を読む。
markdown の要約を linked asset として作る。
現在の working directory 外の知識が必要な場合に使う。
- **Prototype**（HITL）：反応を得られる安価で粗い具体物を作り、議論の fidelity を高める。
outline、rough take、stub、`/prototyping-solutions` skill で作る UI または logic code などを使う。
prototype を asset として link する。
「どのように見えるべきか」「どのように振る舞うべきか」が主な question の場合に使う。
- **Grilling**（HITL）：`/grilling` と `/modeling-domains` skill を使い、一度に一問ずつ会話する。
これが既定である。
- **Task**（HITL または AFK）：*decision* を下す前に必要な手作業を行う。
決めること、prototype、research はないが、完了するまで議論が block される作業である。
API を評価するために service へ登録する、access を provision する、形を確認できるよう data を移動する、などが該当する。
これは decision ではなく*実行*を行う唯一の type である。
目的地を deliver するためではなく、decision を unblock するために使う。
agent が単独で進められる場合は AFK とし、進められない場合は人間へ正確な checklist を渡す HITL とする。
作業の完了時に resolve する。
回答には、実施内容と、後続 ticket が依存する事実（credential の場所、新しい URL、row count など）を記録する。

## 戦場の霧

map は意図的に不完全にする。
まだ見えないものを描いてはならない。
live ticket の先には **fog of war** がある。
これは、先にあることは分かるが、まだ open の question に依存しているため具体化できない decision や investigation のぼんやりした姿である。
ticket を解決すると前方の霧が晴れ、具体化できるようになったものが新しい ticket になる。
目的地までの道が明確になり、ticket がなくなるまで一つずつ進める。

map の **Not yet specified** section に、そのぼんやりした姿を書く。
あとで確認する疑わしい question や領域を記す。
目的地へ向かう未発見の frontier であり、ここにあるものはすべて scope 内だが、ticket にするにはまだ曖昧である。
見えている範囲に合わせて粗くも詳しくも書いてよい。
effort の進行方向を読む collaborator に示す signpost にもなる。

**霧か ticket か。**
判断基準は、今すぐ正確な question として表現できるかどうかである。
今すぐ回答できるかどうかではない。

- question がすでに明確なら **Ticket** にする。
block されていて、まだ行動できなくても ticket にする。
- まだ同じ精度で表現できないなら **Not yet specified** にする。
霧を先に ticket size へ分割してはならない。
霧は ticket より粗く、一つの領域から frontier 到達時に複数の ticket が生まれることも、一つも生まれないこともある。

**Not yet specified** には、決定済みの内容（Decisions so far）、live ticket、対象外の内容（次の section）は含めない。

## 対象外

霧が集まるのは目的地へ*向かう*方向だけである。
目的地が scope を固定するため、その先にある作業は **out of scope** になる。
それは霧ではなく、**Not yet specified** にも置かない。
map の **Out of scope** section に、この effort では意識して対象外とした作業を記す。
scope に含まれるかどうかでこの section が決まり、明確さは関係しない。

対象外の作業は ticket にならない。
frontier は目的地で止まる。
目的地を引き直した場合に限り、新しい effort として戻る。
以前の effort の再開にはしない。

対象外にする判断は scope を定める行為であり、route 上の step ではない。
すでに存在する ticket が目的地の先にあると判明した場合（作図時に誤って scope へ入れた場合、解決結果によって判明した場合）は、その ticket を **close する**。
close 済み ticket は frontier から明確に外れる。
**Out of scope** section に、gist と対象外の理由を一行で記し、close 済み ticket へ link する。
その項目は **Decisions so far** には置かない。
そこには実際に歩いた route を記録し、scope の境界は route 上の step ではないためである。

## 呼び出し方

二つの mode がある。
どちらでも、一つの session で複数の ticket を解決してはならない。

### map を描く

ユーザーが大まかな idea とともに呼び出す。

1. **目的地に名前を付ける。**
`/grilling` と `/modeling-domains` の session を実行し、この map が道を探す先（仕様書、決定、変更）を確定する。
目的地が scope を固定するため、最初に決める。
2. **frontier を描く。**
もう一度問いを重ねる。
今回は **breadth-first** で進め、一つの thread を深く追うのではなく全体へ広げ、open decision と現在着手できる最初の step を明らかにする。
**霧がまったく見つからない場合**、目的地への道はすでに明確で、journey 全体が一つの session に収まる。
map は不要なので停止し、どのように続けるかユーザーに確認する。
3. **map を作る**（label は `wayfinder:map`）。
Destination と Notes を埋め、Decisions-so-far は空にし、霧を **Not yet specified** に描く。
4. **現在具体化できる ticket を作る。**
map の child issue として作成した後、**二回目の pass** で blocking edge を接続する。
相互参照には issue id が必要なためである。
edge によって frontier と blocked に分類する。
まだ具体化できないものはすべて霧として **Not yet specified** section に残す。
5. 停止する。
map の作図が一つの session の作業であり、同じ session で ticket まで解決しない。

### map を進める

ユーザーが map（URL または number）とともに呼び出す。
ticket の指定は任意である。
指定がなければユーザーではなく agent が次の decision を選ぶ。

1. **map** を読み込む。
すべての ticket body ではなく、低い解像度の view だけを読む。
2. ticket を選ぶ。
ユーザーが指定した場合はそれを使う。
指定がない場合は frontier の先頭を選ぶ。
作業前に自分を assignee にして **claim** する。
3. ticket を解決する。
必要に応じて**拡大する**。
関連する ticket や close 済み ticket の全文は必要なときだけ取得し、`## Notes` block に挙げられた skill を呼び出す。
迷った場合は `/grilling` と `/modeling-domains` を使う。
4. 解決結果を記録する。
回答を **resolution comment** として投稿し、issue を **close** し、context pointer を map の Decisions-so-far に追記する。
5. 新しく明らかになった ticket を追加する（作成後に edge を接続する）。
回答によって具体化できるようになった霧を ticket にし、**Not yet specified** から該当部分を削除する。
情報は新しい ticket だけに置く。
この ticket または別の ticket が目的地の先にあると判明した場合は、route 上で解決せず**対象外にする**。
decision によって map の別部分が無効になった場合は、該当 ticket を更新または削除する。

ユーザーは unblocked ticket を並行して進めることがある。
他の session も同時に tracker を編集すると想定する。
