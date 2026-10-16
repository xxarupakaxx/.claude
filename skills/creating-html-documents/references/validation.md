# HTML検証gate

## Static

- `python3 ~/.claude/scripts/lint-html-document.py <file>` の誤りが0である。下の項目のうち、機械で数えられるものを調べる。残りは読んで確かめる。
- doctype、`lang`、charset、viewport、title、CSPがある。
- `h1`は一つ。heading levelを飛ばさない。
- `main`、`aside`、`figure`、`table`などsemantic要素を用途どおり使う。
- id重複がない。anchor targetが存在する。
- 意味を持つ各SVGを囲む`figure`に、`role="img"`付きSVG、`title`、`desc`、`figcaption`がある。装飾のSVGは親に `aria-hidden="true"` があり、意味を伝えていない。
- `<table` が0である。例外で使う場合は `table-exception` のmetaに理由があり、table headerに`scope`がある。
- `script` が0である。例外で使う場合は `script-exception` のmetaに理由がある。
- 意味を持つラベル（追加、消える、変わる、旧、新、番号）が実要素で、CSSの `::before` / `::after` の `content` に文字がない。
- outline、border、背景で強調した要素の内側に文字ラベルがある。
- `overflow:hidden` の箱の中で外側へ出る `outline` を使っていない。数値・日付のセルに `overflow-wrap:anywhere` や `text-overflow:ellipsis` を使っていない。
- SVGの `text` の色がCSSクラスで指定され、`fill` 属性がCSSに上書きされていない。
- 外部navigation linkに `rel="noopener noreferrer"` がある。
- codeをHTMLとして解釈させずescapeする。
- remote `src`、stylesheet、font、scriptを列挙し、許可根拠のないものを0にする。
- Mermaid、remote resource、runtime scriptをoverviewやdetail図の表示要件にしていない。
- overview SVGの長い説明はcaptionまたは本文へ逃がし、図中文字は短いlabelまたは明示的な折返しで読める設計にしている。

## Browser（既定はdesktopのみ）

既定viewportは1440x900。mobile、tablet、print、PDFは明示依頼時だけ追加する。

browser toolが `file:` URLを開けない場合は、生成fileの親directoryを `python3 -m http.server --bind 127.0.0.1` で一時的に配信し、検査後に停止する。

SVGを含む文書では、page上で次を機械検査し、いずれも0にしてから目視する。

- 同じSVG内の `text` のbbox同士の重なり。
- `text` のbboxが、触れている `rect` の内側に収まっていない（はみ出し）。
- `text` のbboxがviewBoxの外に出ている。
- `marker-end` が参照するidが文書内に存在する。
- 表示倍率（描画幅÷viewBox幅）と、図中の最小文字の実寸（font-size×表示倍率）。実寸12px未満の文字を0にする。

検査後、各図をscreenshotで目視し、矢印とラベルの対応、線と文字の衝突を確認する。

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
- 冒頭の要約は、太字の長い段落や狭い補助列の長文で読ませていない。並列する要点は項目に分かれて本文の節へリンクし、要約の条件と推論の表示が本文と一致している。
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
- screen-diffでは、冒頭の件数、地図の枠、場面のラベル、末尾のカードの分類が一致し、旧が「変わる」で新が「追加」のような不揃いな対がない。設計で消したものと未作成のものを分けている。構造の地図を省いたのは、差分が一つの画面に閉じ、メニューが変わらず、別の画面へ移る要素も無い場合だけである。
- 初学者向けexplainerでは、場面の絵、登場人物の地図（地図が場面の絵の繰り返しになる場合は場面の絵の直後の箇条書き）、主要章の「たとえるなら」と「比喩の限界」、歴史の章、仮設の代表ケース、章ごとの絵、自己テストが揃っている。章を読む順はdecision bandの外にある。型を埋めるために、対象に無い段、主体、規制・制度の章を作っていない。
- 既定を重ねた文書とファイルの索引を持つ文書は、`document-system.md` のTechnical explainer（change-reviewならChange review）の順に沿っている。索引の後の図や仕組みの地図で、overviewと同じ図を描き直していない。
- `<meta name="reader">` に読者と目的が一文で残り、初学者向けの既定と理解の確認の既定を重ねるかが読める。読者が実務者の文書に、初学者向けの既定が入っていない。
- 理解のための解説では、読み終えたらできること、仕組みの地図と中心の問い、読む前の予想とその回収、根拠の強さのラベルと確かめた範囲、わかったつもりの罠、答えを折りたたんだ自己テスト、最後の説明チェックが揃っている。予想の問いが示す答えの位置が実在し、自己テストの各答えと各誤解から戻る章へリンクがある。「読み終えたらできること」の各項目に、対応する問いがある。確認済みの欄に推測が混ざっていない。
- 同じ情報を複数componentで繰り返さない。
- 事実、推論、提案、未確定が区別できる。
- 制作指示、会話、prompt、placeholderが残っていない。

## ファイル・関数を追う索引

複数fileの変更レビュー・技術解説、またはfile指定の処理説明に適用する。

- 読む順に並ぶ索引から全対象のfile・symbolの詳細へ移動し、索引へ戻れる。全anchorが存在し、番号と名称が図・詳細で一致する。索引の見出しは、チームが差分を確かめて判断するレビュー記録では「レビューする順番」、それ以外では「ファイルを読む順番」である。
- 索引の順の理由、依存矢印の意味、runtime Level（SKILL.mdの「ファイル・関数を追う索引」で定義した、入口をLevel 0とする実行時の呼び出しの深さ）の定義が別々に読める。runtime Levelを索引の番号やzoom levelと混ぜていない。cycle、並行、handoffを誤った直列順にしていない。
- 各関係に種別とsourceがあり、runtime callには呼出箇所の根拠がある。手順参照、予定、unknownを実行済みの関数呼び出しとして表示していない。
- 指定fileが索引に含まれ、展開範囲は説明に必要な関係に限定される。完全なpath、symbol、source行・版、根拠抜粋を読める。
- script無効でも索引・主要関係・根拠が読め、keyboardでリンクを往復できる。長いpathが本文からはみ出さない。
- SVG採用時はdiagram-designの型別上限を守り、責務nodeとfile・symbolの対応を辿れる。単純なcall treeや文言修正に不要な図を強制しない。

## Independent review

配布前に、実装した文脈と別の、まっさらな文脈のレビュー担当へfileのpathと文書の目的だけを渡し、重要度順の指摘を受ける。指摘の根拠（file:line、観察した幅と場所）を確認してから反映し、反証された指摘は理由を残して除外する。見た目や構造が大きく変わる修正をしたときは、もう一度依頼する。理解のための解説では、`mastery-explainer.md` の確認観点（事実の誤りと言い過ぎ、根拠ラベルの強さの不一致、確かめた範囲の過大評価、説明の無い語、時点や用語の揺れ、理解の断絶）も渡す。

## Evidence report

完了報告には次を含める。

- fileの絶対path。
- 選んだ文書型。
- 1440x900とoverflow結果。
- external resourceとscriptの件数。
- heading、table、idの結果。
- mobile、print、PDFを実行したか。未依頼なら `not requested` とする。
- Overview gateの判定、overview SVGの有無、detail sliceとの接続結果。
- 表の件数（0が既定）と、例外時の理由。
- lintの誤りと要確認の件数、要確認をどう判断したか。
- 独立レビューの実施回数、反映した指摘、除外した指摘と理由。
- 未検証項目と残るrisk。
