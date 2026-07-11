---
name: writing-fragments
description: 文章の explore を行い、まだ構成を決めずに素材となる fragment を集める。
disable-model-invocation: true
---

<what-to-do>

ここでは純粋な **explore** を行う。
構成を確定せず、書ける内容の範囲を広げる。
確定は別の skill が行う _exploit_ の仕事である。
ユーザーが書きたい topic について容赦なく問い続け、fragment を生み出す grilling session を進める。
phase、outline、article structure を押し付けることは対象外である。

会話のどちら側から fragment が生まれた場合も、一つの markdown file に追記する。

ユーザーが path を渡していない場合は、文書の保存先を一度だけ確認し、session の残りではその path を覚えておく。

最初の prompt を含め、ユーザーの最初の発言から fragment を記録する。

最初の書き込みでは、仮 title の H1 を一つだけ先頭に置く。
title はあとで変更してよい。
metadata、TOC、date は追加しない。

</what-to-do>

<supporting-info>

## Fragment とは

fragment は、最終的な article に残る可能性のある任意の文章片である。
_author が読める_必要があり、author 自身が意味を理解できなければならない。
ただし、用語を定義したり、初めて読む人が理解できたりする必要はない。
基準は「自己完結した argument か」ではなく、「良い文章の一部か」である。

fragment は意図的に異なる種類を混在させる。
fragment の例：

- どこで使うかは未定だが、どこかに置きたい鋭い一文。
- 一行の根拠を伴う claim。
- 出来事、code snippet、scenario、analogy などの vignette。
- 「X が Y のように感じられることについて、あとで考える」のような考えかけの文。
- quote、dialogue、耳にした一言。
- 感覚的につながっている関連 observation の list。
- complaint、confession、punchline。
- **leading word**。
文章全体を支えられる簡潔な metaphor または coinage であり、_tracer bullets_ や _fog of war_ のように pattern 全体へ名前を付ける一つの用語を指す。

この中で、leading word は見つける価値が最も高い fragment である。
文章を支える役割があり、explore 中に適切な語を付けると、その後の structure、transition、title が形作られ、exploit phase 全体に効果が続く。
会話が同じ idea の周りを巡り始めたら、それを表す語を作るよう促す。

小説家の日記を手本にする。
何年分もの構造化されていない気付きが、あとで素材として採掘される。
fragment は気付きである。

## ファイル形式

```markdown
# 仮 title

最初の fragment をここに置く。

複数の段落でもよい。
list、code、quote など、fragment に自然な形を使える。

---

二つ目の fragment。

---

> ユーザーが残しておきたい quote。

それに対する反応。

---

- 感覚的につながった observation のまとまり
- 一緒に置くことが自然な項目
- 互いに近くに置きたい項目
```

fragment は水平線（`\n---\n`）で区切る。
body 内に heading を置かない。
tag は付けない。
追加された順序以外の並び順は設けない。

## 書き進める rhythm

黙って追記する。
fragment ごとに許可を求めない。
追加したことは「それも追加します」のように会話の流れで伝えるが、保存 dialog で会話を中断しない。

書き込む前には毎回、disk からファイルを読み直す。
turn の間にユーザーが fragment を編集、並べ替え、削除している可能性があるため、その変更を保持する。
ファイルを上書きしてはならない。
追記だけを行い、ユーザーが依頼した場合に限り、指定された fragment をその場で編集する。

ユーザーはいつでも「最後のものを削除して」「もっと鋭く書き直して」「この二つを統合して」と指示できる。
それらを正式な指示として扱う。

</supporting-info>
