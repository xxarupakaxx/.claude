# 解説 HTML の構成

`creating-html-documents` の change-review に、初学者向けの既定と理解の確認の既定を重ねた構成です。レイアウト、目次、用語集、全体像の図、章の順と統合、各部品の作法は `creating-html-documents` に従い、ここではレビュー固有の章、その置き場所、部品を決めます。章ごとに一つの問いに答え、対象に無い章（migration の無い PR の migration 節など）は作りません。

## body.html に書くもの

`body.html` には、生成後の `<div class="page">` の中身だけを書きます。doctype、`html`、`head`、`body`、`style` は `render` が付けます。`script` は文書に入れません。どれも書くとエラーになります。テンプレート（`editorial-document.html`）を丸ごと貼らず、骨組みと部品の class だけを使います。

```html
<header class="masthead">…</header>
<details class="document-nav" id="toc"><summary>目次</summary><div class="nav-content"><nav aria-label="目次" id="toc-list">…</nav></div></details>
<div class="reading-layout"><main id="main-content">
  <div class="decision-band wide" role="group" aria-labelledby="decision-label">…</div>
  …各章の section…
</main></div>
<a class="to-toc" href="#toc-list">目次へ</a>
```

- テンプレートの部品: `decision-band` 一式、`goals`、`orientation-grid`、`figure-frame`、`diagram`（図の文字と線の class。`t-strong`、`t-note`、`node`、`l-accent`、`m-ink` など）、`analogy`、`predict`、`answer`、`myths`、`qa`、`tag`、`document-nav`、`to-toc`。テンプレートの `step-list` は番号を CSS の counter で描き、lint の「要確認」になるので使わない（使わなくても CSS は残るので、lint の要確認1件はこれと判断してよい）。
- このSkillの部品（`assets/review-guide.css`）: `legend`、`reading-order`、`defs`、`cases`（1件を追う手順の `ol`）、`ba` / `ba-row` / `ba-tag` / `chip`（旧・新・同じの並び）、`file-index`、`calltree`、`todo`、`finding` / `oneline` / `sev` / `judge`（指摘カード）、`author-qs`、`rec-line` / `alts` / `alt`（代替案）、`checks` / `ok`、`explain-check`、`sources`。抜き書きの class（`quote` など）は `render` が出力する。
- 本文に `[[` と書きたいときは `&#91;&#91;` と書く。`[[` はトークンとして解釈される。

## 章の順

章の順と統合の規則は、`creating-html-documents` の `references/document-system.md` を正本とします。土台は「Change review」の順で、そこへ「Technical explainer」の【理解】【初学者】【索引】の項目を同じ位置関係で差し込みます（読み手は前提知識を持たず、目的は読み手自身の理解と採否の判断なので、三つとも当たる）。たとえば、ファイルの索引は全体像の図の直後、仕組みの地図と中心の問いは代表ケースの後、主要章の前には読む前の予想、各章には一枚の絵とたとえを置きます。ここでは順を書き写さず、レビュー固有の章と、その置き場所だけを決めます。

- **見出し**: 対象（PR、比べた commit の短い SHA）と、「抜き書きは git から機械的に切り出した」旨を書く。
- **結論**（decision band）: 安全性の結論 → 直すべき誤り → マージ前に決めたいこと → 依頼者の問いへの短い答え、の順で3〜4文。下端に、要点のリンク（マージまでにやること、指摘、依頼者の問い）と、現在地（確かめた範囲、していないこと、CI の状態）を置く。
- **根拠ラベルと用語の約束**（読み終えたらできることの直後）: 確認済み・出典の記載・推測・未確認の意味。要件の言葉と実装の判定がずれる語は、ここで呼び方を決める。
- **全体像の図**: PR の変更点と、PR 前に起きていた失敗の流れが図の問いに含まれるなら、それぞれ意味の分かる語で書き、線の種類の意味を図の中の凡例に書く。図の class はテンプレートの `diagram` を使う。
- **1件を追う**（代表ケースの時系列の位置）: 正常なケースと PR の対象ケースを、`ol class="cases"` の番号付きの手順で追う。PR 前の手順には merge-base の抜き書きを使う。数字は「仮設」と明記する。
- **PR の変更**（detail slice の位置）: 旧・新・同じの状態の並び、主要な差分の抜き書き。差分は、同じ箇所の merge-base の抜き書きと head の抜き書きを並べて見せる。diff やコードを手で書き写した `<pre>` は `verify` で照合できないので置かない（関数名の並びを示す呼び出し順の `calltree` は別）。
- **マージまでにやること**（読み手への含意の位置）: 順番どおりの番号付きリスト。各項目に所要時間の目安と、該当する指摘へのリンク。migration があれば、リリースの順番（migration、アプリ、後続の migration）をここに含める。
- **指摘**: 下の指摘カードを重要度順に並べる。
- **作者が判断を求めている点への見解**: PR 本文の「見てほしい観点」をすべて拾う。
- **依頼者の問いごとの節**: 読む前の予想 → 根拠の抜き書き → たとえ → 答え（根拠ラベル付き）。
- **代替案**（設計判断を問われたとき）: 案ごとのカードに、成り立つ条件・よい点・欠点・採否。推奨を先に一文で書く。
- **migration**（Change review の migration・compatibility・rollback の位置）: 条件ごとのチェック、本番での確認手順、リリースの順番とロールバックしたときの読み取り。
- **罠と自己テスト**: 罠と答えには、戻る章へのリンクを付ける。
- **出典**: PR、抜き書き、設計書、先例の PR、公式文書。

## 指摘カード

```html
<article class="finding" id="f1" aria-labelledby="f1-h">
  <h3 id="f1-h"><span class="sev high">重要</span> F1 一文で言い切る見出し</h3>
  <p class="oneline">何が、どこで、どう食い違うかを2〜3文で。</p>
  [[q-…]]
  <h4>初めての人向けの解説</h4>
  <p>なぜ問題になるのか。読み手が知らない仕組みは、ここで1段だけ補う。</p>
  <h4>自分で確かめる手順</h4>
  <ol><li>抜き書きの何行目を見れば反証・確認できるか。必要なら SQL やコマンド。</li></ol>
  <h4>推奨</h4>
  <p>修正方向と、選択肢があれば並べる。[[TAG:fact]]（何を確かめたか）</p>
  <p class="judge">判断: 採用 ／ 見送り ／ 要相談</p>
</article>
```

- 重要度の class: `high`（重要）、`mid`（中）、`low`（低）、`ask`（確認・要判断）。重要度を決めた理由が読み手の判断に要るときは、推奨の中に一文で書く。
- 見出しの番号（F1〜）は、自己テスト・罠・マージまでにやることから参照するので、生成後に振り直さない。

## spec.json

```json
{
  "repo": "/abs/path/to/repo-root",
  "github": "owner/name",
  "title": "PR #123 を初めて読む人のためのレビュー解説",
  "reader": "読者と目的を一文で（初学者向けの既定と理解の確認の既定を重ねる）",
  "revs": {"head": "<head の SHA>", "merge-base": "<merge-base の SHA>"},
  "quotes": [
    {"id": "q-guard", "rev": "head", "path": "path/from/repo-root/file.go", "start": 819, "end": 855, "ctx": 4,
     "title": "抜き書きの題", "focus": [838]},
    {"id": "q-old", "rev": "merge-base", "path": "path/from/repo-root/file.go", "find": "一意に決まる文字列", "before": 2, "after": 6}
  ]
}
```

- 必須: `repo`（`git rev-parse --show-toplevel` の値）、`title`、`reader`、`revs`、`quotes`。各抜き書きは `id`、`rev`、`path` と、`start` と `end`、または `find` のどちらか一方が必須（両方は書かない）。
- `revs` の値は40桁の SHA にする（ref 名は、再生成のたびに指す版が変わるので受け付けない）。`git merge-base <base> <head>` などで求めて書く。PR 前の挙動を見せるときは merge-base を使う。base branch の先端は、分岐後の main の変更を含むことがあるので使わない。
- `path` はリポジトリのルートからの相対パス。
- `id` は `q-` で始まる英小文字・数字・ハイフン。本文では各抜き書きを `[[q-id]]` で一度だけ置き、ほかの箇所からは `<a href="#q-id">` で参照する。未使用・重複・存在しない id は生成時にエラーになる。
- 既定値: `ctx`（前後を読む行数）は8、`before` と `after` は0。`focus` は主張の要の行で、抜き書きの範囲内にする。
- 根拠ラベルは `[[TAG:fact]]`・`[[TAG:cited]]`・`[[TAG:guess]]`・`[[TAG:open]]` と書く。
- 本文中で「何行目」と書くときは、抜き書きの行番号（ファイルの行番号）を使う。
