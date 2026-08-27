# HTML検証gate

## Static

- doctype、`lang`、charset、viewport、title、CSPがある。
- `h1`は一つ。heading levelを飛ばさない。
- `main`、`aside`、`figure`、`table`などsemantic要素を用途どおり使う。
- id重複がない。anchor targetが存在する。
- 各SVGを囲む`figure`に、`role="img"`付きSVG、`title`、`desc`、`figcaption`がある。
- table headerに`scope`がある。
- codeをHTMLとして解釈させずescapeする。
- remote `src`、stylesheet、font、scriptを列挙し、許可根拠のないものを0にする。
- Mermaid、remote resource、runtime scriptをoverviewやdetail図の表示要件にしていない。
- overview SVGの長い説明はcaptionまたは本文へ逃がし、図中文字は短いlabel、明示的な折返し、または狭幅時の局所scrollで読める設計にしている。

## Browser

既定viewportは375px、768px、1440px。

各幅で次を記録する。

- viewport、document、bodyのscroll width。
- layout columnとrailの位置。
- text overlap、clip、意図しない横scroll。
- table、diff、figureの局所overflow。narrow時のoverview SVGは全体を縮小しすぎず、document全体overflow 0のまま局所scrollできる。
- first viewportのpage purpose、中心主張、status。

200% zoom相当でも主要情報と読み順を確認する。

## Accessibility

- keyboardだけでlinkとcontrolへ到達できる。
- visible focusがある。
- hoverだけで開示する主要情報がない。
- text、border、statusのcontrastが十分である。
- 色以外にlabel、記号、位置、形の手がかりがある。
- reduced motion、forced colorsで情報が消えない。
- DOM順がmobileとprintの読み順として成立する。

## Print

- A4 print previewを生成する。
- sticky、navigation、interactive controlをprint向けに解除または非表示にする。
- heading直後の孤立、figure / table / diffの不自然な分断を避ける。
- URL、caption、source、page statusが必要に応じて残る。

## Content

- 冒頭だけで結論と次の判断が分かる。
- workflow、architecture、lifecycle、before / after、dependency、failure pathなど、3つ以上の相互作用する要素関係またはfailure伝播を扱う文書では、中心主張の直後にorientationとoverview SVGがある。単にfileやevidenceが3件あるだけで必須扱いにしていない。
- orientationは背景、without-this failure、対象scope、目標状態、全体内の位置を含む。背景が中心主張より前に出ていない。
- overview SVGはactor / component / stage、主要flow、対象境界、failureの伝播先を示し、captionが読者の問いに答えている。
- detail sliceはoverviewの番号、名称、境界を再利用し、一つのsubflow、before / after、failure path、diffへzoomしている。
- overviewとdetailで同じ情報を再描画していない。重複するsummary、card、diagram、badgeを増やしていない。
- 単一事実、単純な一操作、短い値比較、2要素だけのbefore / afterに不要な図を強制していない。
- 各sectionは一つの問いに答える。
- 同じ情報を複数componentで繰り返さない。
- 事実、推論、提案、未確定が区別できる。
- 制作指示、会話、prompt、placeholderが残っていない。

## Evidence report

完了報告には次を含める。

- fileの絶対path。
- 選んだ文書型。
- viewportとoverflow結果。
- external resourceとscriptの件数。
- print、heading、table、idの結果。
- orientation triggerの判定、overview SVGの有無、detail sliceとの接続結果。
- 未検証項目と残るrisk。
