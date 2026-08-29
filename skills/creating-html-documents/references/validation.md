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
- overview SVGの長い説明はcaptionまたは本文へ逃がし、図中文字は短いlabelまたは明示的な折返しで読める設計にしている。

## Browser（既定はdesktopのみ）

既定viewportは1440x900。mobile、tablet、print、PDFは明示依頼時だけ追加する。

次を記録する。

- viewport、document、bodyのscroll width。
- layout columnとrailの位置。
- text overlap、clip、意図しない横scroll。
- table、diff、figureのoverflow。
- first viewportのpage purpose、中心主張、status。

## Accessibility

- keyboardだけでlinkとcontrolへ到達できる。
- visible focusがある。
- hoverだけで開示する主要情報がない。
- text、border、statusのcontrastが十分である。
- 色以外にlabel、記号、位置、形の手がかりがある。
- static文書では不要なmotionを追加しない。

## Optional delivery gate

- mobile / tablet: ユーザーが必要としたviewportだけ追加確認する。
- print: ユーザーが印刷を求めた場合だけprint previewとpage breakを確認する。
- PDF: ユーザーがPDF fileを求めた場合だけ別成果物として生成・検証する。HTML生成の副作用として自動生成しない。

## Content

- 冒頭だけで結論と次の判断が分かる。
- workflow、architecture、lifecycle、before / after、dependency、failure pathなど、3つ以上の相互作用する要素関係またはfailure伝播を扱う文書では、中心主張の直後にorientationとoverview SVGがある。単にfileやevidenceが3件あるだけで必須扱いにしていない。
- orientationは背景、without-this failure、対象scope、目標状態、全体内の位置を含む。背景が中心主張より前に出ていない。
- overview SVGはactor / component / stage、主要flow、対象境界、failureの伝播先を示し、captionが読者の問いに答えている。
- detail sliceはoverviewの番号、名称、境界を再利用し、一つのsubflow、before / after、failure path、diffへzoomしている。
- overviewとdetailで同じ情報を再描画していない。重複するsummary、card、diagram、badgeを増やしていない。
- 各主要主張に具体的な事実、mechanismまたは因果、source anchor、読者への含意がある。
- materialな境界条件、反例、failureを一般論で隠していない。
- technical flowはinput、branch条件、data contract、state / side effect、failure / recoveryを追える。
- change reviewはfile / symbol、before / after、caller / downstream impact、test evidenceを追える。
- 「処理する」「連携する」「対応する」だけでdetailを閉じていない。
- 単一事実、単純な一操作、短い値比較、2要素だけのbefore / afterに不要な図を強制していない。
- 各sectionは一つの問いに答える。
- 同じ情報を複数componentで繰り返さない。
- 事実、推論、提案、未確定が区別できる。
- 制作指示、会話、prompt、placeholderが残っていない。

## Evidence report

完了報告には次を含める。

- fileの絶対path。
- 選んだ文書型。
- 1440x900とoverflow結果。
- external resourceとscriptの件数。
- heading、table、idの結果。
- mobile、print、PDFを実行したか。未依頼なら `not requested` とする。
- orientation triggerの判定、overview SVGの有無、detail sliceとの接続結果。
- 未検証項目と残るrisk。
