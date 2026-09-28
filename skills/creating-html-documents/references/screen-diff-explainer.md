# 画面差explainerの型（before / after並置）

旧と新、現行と提案、AとBのように「二つの状態の違い」を伝える文書に適用する。読者は元の状態を知っている実務者で、「どの画面のどこが変わったか」「何が消えたか」を短時間で把握したい。表で軸を並べる形は、読者に行と列を往復させて差分を自分で再構成させるため使わない。差分は、同じ場面の旧と新を左右に並べ、変わった要素にラベルを付けて直接見せる。

## 発火条件

- 依頼に「差分」「何が変わった」「旧と新」「before / after」「現行と提案」「モックの比較」が含まれる。
- 対象が画面、メニュー、フォーム、一覧、モーダルなど、読者が目で見て確かめられる構造を持つ。

数値の増減だけを扱う場合は、この型ではなくbar、ものさし、期間の帯を使う。

## 章立ての既定

1. 一文の中心主張と、凡例（追加、消える、変わる、旧、新のラベル）。
2. 差分の件数。「消えた」「増えた」「変わった」の3つを並べ、それぞれに対象名を列挙する。この件数は以降の全章と一致させる。
3. 構造の地図。旧と新のメニュー（またはサイトマップ）を左右に置き、旧の要素の行き先を矢印で結ぶinline SVG。消える要素は破線枠、追加は実線枠、行き先の矢印は1色。
4. 業務の順に並べた場面。各場面は「旧のミニ画面 → 新のミニ画面」の並置と、1〜3文の説明で閉じる。場面の数は4〜8を目安にする。
5. 消えたものと、その行き先。カードのグリッド。各カードは「消えたもの → 行き先」。行き先がなければ「代替なし」と書く。
6. 追加したもの。カードのグリッド。
7. 変わっていないもの、未作成のもの、どちらにもないもの。設計で消したものと、資料や試作で作っていないだけのものを混ぜない。

## ミニ画面（wireframe）の描き方

- CSSだけで描く。sidebar、title bar、行、ボタン、入力欄、モーダル、パネルの最小部品を用意し、実物の文言をそのまま使う。
- 差分に関係する列と項目だけを載せる。省いた列があることを章の冒頭で一度断る（「ラベルのない違いは省略によるもので、機能の差ではない」）。
- 各ミニ画面のtitle barに「旧」「新」のチップを置く。1カラム化した幅でも、今見ているのが旧か新か分かるようにする。
- 旧と新で同じ場面を同じ順序、同じ粒度で描く。旧にある要素が新で消えたなら旧側に「消える」、新に増えたなら新側に「追加」、同じ位置で中身が変わったなら両側に「変わる」を付ける。旧が「変わる」で新が「追加」のような対にしない。
- 数字と日付は途中で折らない。`overflow-wrap:anywhere` を数値セルに使わず、列を減らすか幅を広げる。省略記号（…）で隠さない。

## ラベルの規則

- 「追加」「消える」「変わる」は実要素（`<em class="lb add">追加</em>` など）として、強調する要素の内側の先頭に置く。CSSの `::before` / `::after` の `content` で出さない。疑似要素のラベルは `overflow:hidden` で切れ、隣の要素に重なり、支援技術とコピーで失われる。
- 色は補助で、ラベル文字が主。凡例をページ先頭に置く。
- 画面全体を強調するときは、外側 `outline` ではなく `border` を使う。ミニ画面の外枠に `overflow:hidden` があると外側のoutlineは3辺が切れる。
- 隣り合うセルを別々に強調するときは、outlineのはみ出しがセル間隔を超えないようにする。

## 地図SVGの規則

- 旧と新の枠を左右に置き、要素の行と矢印の経路を先に決める。矢印は縦横の折れ線にし、ラベルは矢印の水平区間の上に置く。矢印の交差は避けられない1本までにし、ラベルの上を線が通らないようにする。
- SVG内の文字色は、`fill` 属性ではなくCSSクラスで指定する。`svg text { fill: ... }` のようなCSSがあると、要素の `fill` 属性は負けて全部同じ色になる。
- `role="img"`、`title`、`desc`、figcaptionを付け、captionで矢印の色の意味を説明する。

## 整合の規則

- 冒頭の件数、地図の枠、各場面のラベル、末尾のカードで、同じ要素の分類（追加、消える、変わる）が一致する。
- 「置き換え」は旧側を「消える」、新側を「追加」とし、captionと末尾のカードで後継関係を書く。
- 仮の数値は仮と明記し、同じ数値を複数箇所で使うときは計算が合っていることを確かめる。

## 最小のHTML部品

```html
<div class="pair">
  <div class="col">
    <p class="col-h"><span class="chip old">旧</span>旧モック</p>
    <div class="wf old">
      <div class="wf-bar"><span class="chip old">旧</span>与信管理</div>
      <div class="wf-body nosb"><div class="wf-main hl del">
        <em class="lb del block">消える</em>
        <div class="rows">
          <div class="tr th" style="grid-template-columns:1.3fr 1fr 1fr"><span>送付先名</span><span>与信金額</span><span>与信残額</span></div>
          <div class="tr" style="grid-template-columns:1.3fr 1fr 1fr"><span>株式会社青葉物産</span><span>3,000,000</span><span>2,901,000</span></div>
        </div>
      </div></div>
    </div>
  </div>
  <div class="mid" aria-hidden="true"><svg viewBox="0 0 34 34"><path d="M4 17h22M18 8l9 9-9 9" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"></path></svg></div>
  <div class="col">
    <p class="col-h new"><span class="chip new">新</span>新モック</p>
    <div class="wf new">
      <div class="wf-bar"><span class="chip new">新</span>送付先一覧（与信台帳）</div>
      <div class="wf-body nosb"><div class="wf-main">
        <div class="rows">
          <div class="tr th" style="grid-template-columns:1.3fr 1fr 1fr"><span>送付先名</span><span class="hl add"><em class="lb add">追加</em>審査</span><span class="hl add"><em class="lb add">追加</em>与信枠と残枠</span></div>
        </div>
      </div></div>
    </div>
  </div>
</div>
<div class="cap"><p>「与信管理」という画面をなくし、与信枠と残枠を送付先の属性にした。</p></div>
```

```css
.lb{display:inline-block;padding:0 6px;border-radius:3px;color:#fff;font-size:10px;font-weight:700;line-height:16px;font-style:normal;margin-right:5px;white-space:nowrap}
.lb.add{background:#176b34}.lb.del{background:#a3302d}.lb.chg{background:#1769aa}
.hl.add{outline:2px solid #176b34;outline-offset:1px;background:#e9f8ee}
.hl.del{outline:2px dashed #a3302d;outline-offset:1px;background:repeating-linear-gradient(45deg,#fdeceb,#fdeceb 5px,#fff 5px,#fff 10px)}
.hl.chg{outline:2px solid #1769aa;outline-offset:1px;background:#e8f1fa}
.wf-main.hl{outline:none;border:3px solid #176b34}
.wf-main.hl.del{border-style:dashed;border-color:#a3302d}
.pair{display:grid;grid-template-columns:minmax(0,1fr) 44px minmax(0,1fr);gap:14px;align-items:start}
.wf{border:1.5px solid #242522;border-radius:10px;background:#fff;overflow:hidden;font-size:12px}
.tr{display:grid;gap:8px;padding:4px 0;border-bottom:1px dotted #c8c8c8}
.tr > span{min-width:0;overflow-wrap:normal;word-break:normal}
.rows{overflow-x:auto;font-size:11px}
.chip{display:inline-block;padding:0 8px;border-radius:4px;color:#fff;font-size:11px;font-weight:700;line-height:18px}
.chip.old{background:#5a5d58}.chip.new{background:#2E3782}
.cards{list-style:none;padding:0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
@media (max-width:900px){.pair{grid-template-columns:minmax(0,1fr)}.cards{grid-template-columns:minmax(0,1fr)}}
```

## 完了前の点検

- `<table` が0である。
- 強調した要素のすべてに文字ラベルがあり、`::after` / `::before` の `content` に意味を持つ文字がない。
- 冒頭の件数と、末尾のカード数、場面内のラベルが一致する。
- 1280px前後の2カラムで、数字と日付が途中で折れず、省略記号で隠れない。
- SVGの文字色が意図どおりに出ている（CSSクラスで指定）。矢印の線がラベルの上を通らない。
- 実装者と別の文脈のレビュー担当に、上の点を含めて確認を依頼し、指摘を反映してから配布する。
