---
name: creating-html-documents
description: 日本語の計画書、技術解説、調査報告、変更レビュー、画面差（before / after）の解説、長文資料を、具体的な根拠・仕組み・境界・含意まで読めるdesktop向け自己完結HTMLとして作成・編集する。ユーザーがHTML、ブラウザで読む報告書、図・差分・コードを含む説明資料を求めたときに使う。表は使わず、比較・差分・対応関係は並置、カード、地図SVG、ラベルで見せる。mobile、印刷、PDFは明示依頼時だけ扱う。
---

# HTML文書を作成する

MarkdownをHTMLで包むのではなく、読者が判断・理解・検証しやすい文書を作る。読者が自分の頭の中で情報を組み立て直さなくても、見た瞬間に差分や関係が分かる形を選ぶ。

## 最初に決める

HTMLを書く前に次を一行ずつ確定する。

1. 読者: 誰が読むか。
2. 目的: 読後に何を理解または判断するか。
3. 文書型: `decision-plan`、`technical-explainer`、`change-review`、`research-report`、`screen-diff` のどれか。
4. 中心主張: 冒頭だけで伝える結論。
5. 根拠: 事実、比較、図、差分、出典のどれが主張を支えるか。
6. 配布条件: local単一file、隣接asset、desktop以外の対応要否。
7. 読者の前提知識: そのドメインの初学者か、実務者か。初学者向けなら、指示がなくても `references/illustrated-explainer.md` の既定を章立てへ組み込む。
8. 理解が目的か: 読者自身がその対象を理解し身につけるための解説か、判断・記録のための文書か。理解が目的なら、指示がなくても `references/mastery-explainer.md` の既定を組み込む。

7と8の判断は、どの文書型でも `<meta name="reader" content="読者と目的を一文で">` に残す。初学者向けの既定と理解の確認の既定を重ねるかも、同じ一文に含める。

作業の計画・進捗・タスクの正本は、`viewing-plans` が作るセッションダッシュボードに置く。このSkillで作るHTMLは、読者が判断し理解するための成果物であり、作業計画の正本にしない。`decision-plan` の実装Wave、受入条件、riskは、読者が採否を判断するための本文として計画書HTMLに書く。計画書HTMLの冒頭で示す現在地とstatusは採否の段階（提案中、承認待ち、採用済みなど）であり、タスクの進捗ではない。タスクの状態、進捗、次の行動はダッシュボードに置き、両者へ同じ本文を複製しない。必要なら互いにリンクする。旧Roadmapは廃止済みのため生成しない。ユーザーがRoadmapを求めたら、廃止済みであることを伝え、セッションダッシュボードで代える。

## 表を使わない

表は既定で使わない。表は読者に行と列を往復させ、差分や関係を自分で再構成させる。比較、差分、対応関係、分類、一覧のどれも、表より速く伝わる形がある。読者の問いごとに次の形へ置き換える。

- 何を採用するか: 案ごとのカード（成立条件、欠点、採否理由）を横に並べ、採用案をdecision bandで先に言い切る。
- 何が変わったか: 同じ場面の旧と新を左右に並置し、変わった要素に「追加」「消える」「変わる」のラベルを付ける。コードならdiff。
- AはどこへBへ移るか: 旧と新の構造を左右に置き、矢印で行き先を結ぶ地図SVG。または「X → Y」のカード。
- 分類や一覧: ラベル付きカードのグリッド。
- 用語と定義: 定義リスト（`dl`）。
- 合格したか: 受入条件ごとのカードに、結果と根拠へのリンクを置く。
- 数値の一覧: barやものさし。数値の照合そのものが読者の目的で、3列以上の数値を突き合わせないと判断できない場合だけ、例外として表を使う。

例外として表を使う場合は、文書の `<meta name="table-exception" content="表を使った理由">` に理由を一文残し、見出しcellに `scope` を付け、5行を超えるなら並べ替えの手がかり（太字、色以外の記号）を置く。この規則は文書だけでなく、このSkillの説明文にも適用する。

## 文書型を選ぶ

詳細は `references/document-system.md` を読む。

- `decision-plan`: 採用判断、Overview-first gate該当時のorientation / overview、現状と目標、比較根拠、実装Wave、受入条件、risk、rollback。
- `technical-explainer`: 結論、Overview-first gate該当時のorientation / overview、用語、処理flow、制約、例、検証方法。
- `change-review`: 変更理由、Overview-first gate該当時のorientation / overview、before / after、重要差分、影響範囲、risk、検証。
- `research-report`: 結論、Overview-first gate該当時のorientation / overview、scope、方法、発見、限界、含意、推奨、source。
- `screen-diff`: 二つの状態（旧と新、現行と提案）の画面差。凡例と件数、行き先の地図、業務順の場面ごとの旧 / 新並置、消えたものと行き先、追加したもの、同じもの。詳細は `references/screen-diff-explainer.md`。

文書型は固定templateではない。各章に一つの問いを与え、その問いに合うvisual patternを一つ選ぶ。

## 初学者向けexplainerの既定

読者が対象ドメインの前提知識を持たず、目的がその読者の理解である解説では、文書型（多くは `technical-explainer`）に次の既定を自動で加える。依頼に「前提知識がない」「まっさらな人向け」「初めて」とある場合や、「〜とは何か」「ドメインを把握したい」のように対象を一から知りたい依頼で、読者が実務者だと分かる手がかりがない場合が当たる。「仕組みを知りたい」「解説して」のような依頼語は、読者の理解が目的であることの合図で、下の「理解の穴に気づける解説の既定」を発火させるが、それだけでは読者を初学者とみなさない。ユーザーがアナロジーや絵を明示していなくても省略しない。詳細な型と描き方は `references/illustrated-explainer.md` に置く。

- 具体と抽象の往復: 主要章ごとに「たとえるなら」の囲みを一つ置き、必ず「比喩の限界」を併記する。身近な例で掴ませてから、専門用語へ戻す。
- なぜ生まれたか: 歴史、以前の方法、何を解いたか、何が難しくなったか、を独立した章にする。
- 絵としてのoverview: 箱と矢印の流れ図で終えず、登場人物と、対象で実際に動くもの（決済ならモノ・書類・お金、認証なら要求・証明・権限）と記録を描いた場面の絵にする。続けて「登場人物の地図」を置き、周辺の主体が中心の当事者のどの番号を手伝うか縛るかを章番号つきで示す。主体は実在する数だけ置き、地図が場面の絵の繰り返しになるなら場面の絵の直後の箇条書きで代える。
- 詳細章ごとに一枚: 各章の問いに合う型（同型並列、両端、昔と今の帯、ものさし、資金の穴、階段、before / afterの帯）を一枚ずつ差し込む。図番号は章番号ベースにする。
- 代表ケース: 仮設と明示した数字で、1件が最後まで流れる時系列を追う。
- 締め: 答えを折りたたんだ自己テストと、用語集railを置く。自己テストの作り方は `references/mastery-explainer.md` に従う。

読者が実務者（そのドメインの用語と基本の流れを知っている人）の文書には適用しない。実務者向けの `technical-explainer` や仕様説明も含み、目的が読者の理解なら、下の「理解の穴に気づける解説の既定」だけを重ねる。`decision-plan`、チームが差分を確かめて判断するためのレビュー記録、`screen-diff`、短い確認用HTML、ダッシュボードにも適用しない。読者が初学者かどうか判断できないときは、読者と目的を一文で決める。判断は「最初に決める」のとおり `<meta name="reader">` に残す。

## 理解の穴に気づける解説の既定

読者自身が対象を理解し、身につけるための解説では、指示がなくても次を本文に組み込む。「解説して」「教えて」「わかるように」「仕組みを知りたい」「マスターしたい」といった依頼や、PR・設計・ドメイン・障害・ライブラリの挙動の解説が当たる。読者の前提知識の有無は問わず、初学者なら上の既定も重ねる。判断のための計画書、チームが差分を確かめて判断するためのレビュー記録、差分の把握だけを求める文書（`screen-diff` や、APIの差分を見やすく示す `change-review` など）、短い確認用HTML、ダッシュボードには適用しない。「差分が視覚的にわかる」のように見やすさを求める「わかる」は、理解が目的であることの合図にしない。PRの解説は `change-review` の要素（before / after、ファイルごとの差分）を持つが、目的が読者の理解ならこの既定を重ねる。読者と目的の判断は `<meta name="reader">` に一文で残す。詳細は `references/mastery-explainer.md` に置く。初学者向けの既定と重ねたときの章順と、ファイルの索引の位置は、`references/document-system.md` のTechnical explainerに一本の順序としてまとめてある。

目的は、読者がわかったつもりで終わらず、自分の理解の穴に気づき、対象を自分の言葉で説明・予測・応用できる状態にすることである。仕組みを組み立てる段を省かず、手間を理由に要素を削らない。同じ内容の言い換えで分量を増やすこともしない。

- 読み終えたらできること: 冒頭の要約（decision band）の直後、orientationの前に、外から確かめられる動詞で3〜5個書き、最後の自己テストと対応させる。
- 仕組みの地図: 要素、役割と持っている情報、因果の連鎖、境界を本文に明示する。可能なら、全詳細を説明し直せる中心の問いを一つ立てる。「メンタルモデル」などの語で済ませない。
- 段を飛ばさない: 具体例 → 一般化 → 適用の順にする。用語は初出で定義し、同じ概念に同じ語を使う。比較の基準時点や多義語は定義する。
- 読む前の予想: 主要章の前に外れやすい問いを置き、答えの位置を正確に示して本文で回収する。
- 根拠の強さ: 主張ごとに「確認済み」「出典の記載」「推測」「未確認」を文字で付け、確かめた環境・版・条件を書く。確認済みの欄に推測を混ぜない。
- わかったつもりの罠: 読者が本当に持ちそうな誤解を5〜8個、「誤解 → 実際 → 戻る章」で並べる。
- 自己テスト: 答えは `details` で折りたたみ、開く前に答えさせる。説明・予測・区別・境界・応用の問いを混ぜて目安8〜12問にし、各答えに戻る章へのリンクを付ける。
- 最後の説明チェック: 何も見ずに3文前後で説明させ、含めるべき要点と、詰まったときに戻る章を示す。
- 独立レビュー: 通常の観点に加え、事実の誤りと言い過ぎ、根拠ラベルの強さ、確かめた範囲の過大評価、説明の無い語、理解の断絶を確かめてもらう。

## 画面差explainer（screen-diff）の既定

次の二つを両方満たすときだけ `screen-diff` を選ぶ。一つは、依頼に「差分」「何が変わった」「旧と新」「before / after」「現行と提案」のような差分の語が含まれること。もう一つは、対象が画面、メニュー、フォームのように、読者が目で見て確かめられる画面の構造を持つこと。API、コード、設定、データの差分は、差分の語があっても `screen-diff` にせず、`change-review` のbefore / afterとdiffで扱う。数値の増減だけならbar、ものさし、期間の帯を使う。この型では、構造の地図を省く条件に当たる場合を除き、次を省略しない。詳細は `references/screen-diff-explainer.md` に置く。

- 冒頭に凡例（追加、消える、変わる、旧、新）と、「消えた」「増えた」「変わった」の件数を対象名つきで置く。
- 旧と新の構造（メニュー、サイトマップ）を左右に置き、旧要素の行き先を矢印で結ぶ地図SVGを置く。差分が一つの画面の中に閉じ、メニューが変わらず、別の画面へ移る要素も無いときだけ地図を省き、件数の行に「画面の構成は変わらない」と書く。
- 業務の順に場面を並べ、各場面は旧のミニ画面と新のミニ画面の並置と、1〜3文の説明で閉じる。ミニ画面はCSSで描き、実物の文言を使い、title barに旧 / 新チップを付ける。
- ラベル「追加」「消える」「変わる」は実要素として要素の内側に置く。CSSの `::before` / `::after` の `content` で出さない。
- 末尾に「消えたものと行き先」「追加したもの」「同じもの、未作成のもの、どちらにもないもの」のカードを置き、冒頭の件数と一致させる。

## show-meをvisual layerとして使う

このSkillが文書全体のownerであり続ける。章立て、source inventory、claim ledger、overview trigger、evidence、HTMLへの配置、CSP、検証、browser表示を`show-me`へ渡さない。

各claimまたはsectionで「何を見せれば最も速く伝わるか」を決めるときだけ`show-me`を使う。入力にはsectionの問い、evidence anchor、欠かせないactor / state / branch / 境界、文書内で再利用する名称を渡す。戻り値は擬似コード、call tree、component / file tree、diff、SVG、または次のvisual briefとする。

```text
visual-question: 読者が視覚表現から理解すべき問い
evidence-anchors: file、symbol、test、sourceなどの根拠
recommended-form: 採用する最小表現
must-show: 欠かせない要素と関係
omit: 今回は見せない周辺情報
fallback: 同じ意味を読めるtext表現
```

呼出しcontextに`document-owner: creating-html-documents`を明示する。このcontextでは`show-me`は局所visual sliceだけを返し、HTML文書全体を作らず、このSkillへ再委譲しない。受け取った表現が本文と同じ内容を繰り返す場合は採用しない。overviewの要否はこのSkillのOverview gateが決め、`show-me`はoverview内の最小構成を選ぶ。

## ファイル・関数を追う索引

複数fileの変更レビュー・技術解説、またはfile指定の処理説明では、`show-me`の「レビュー順と依存関係を表示する」を適用する。source inventoryから対象と必要な呼出元・呼出先を渡し、索引、関係、順序の意味をvisual briefで受け取る。単純な文言修正やコードを扱わない資料では省く。

この節のruntime Levelは、`show-me` の「Levelの定義」と同じく、利用者の操作や外部入力を受ける入口をLevel 0、その直接の受け手をLevel 1とする実行時の呼び出しの深さである。循環、callback、queueでの再開のように単純な深さにならない箇所では、Levelを付けず、handoffの名前か再入点を書く。索引の番号、静的な依存の深さ、下の「Orientationとoverviewは索引にする」のzoom level（Level 0〜4）とは別のものとして書く。Skill・設定のfile参照を明示的に求められた場合は、symbolを見出し・設定キーに置き換え、runtime Levelは適用外とする。

- 中心主張と、該当時のorientation / overviewの後に、読む順に並べた番号付きの索引を初期表示する。初学者向けでは登場人物の地図の後に置く。ほかの章との順は `references/document-system.md` のTechnical explainerとChange reviewに従う。索引の見出しは文書の目的で分ける。チームが差分を確かめて判断するレビュー記録では「レビューする順番」、それ以外（`technical-explainer`、PRの解説、差分の把握だけを求める文書）では「ファイルを読む順番」とする。各項目にfile、symbol、処理の一文、先に読む理由を置き、本文内の詳細へリンクする。
- 詳細は同じidと番号を使い、file path・symbol・source行、入力、具体的な処理、呼出元→呼出先、出力・副作用、関連diff・testを示す。索引へ戻るリンクも置く。既存のdetailへ統合し、別章に同じ説明を複製しない。
- 索引に続くcall treeまたは図は「依存関係」「呼び出し順」のどちらかを明記する。索引の順との違い、矢印の意味、runtime Levelを短く説明する。その図がoverviewと同じ要素と矢印になるなら別に描かず、overviewの各nodeに索引の番号を振る。その場合は、番号が読む順で実行の順ではないこと、矢印の意味、runtime Levelをcaptionに書く。diagram-designのSVGを採用する場合は同じSVG正本を埋め込み、nodeのidからfile・symbolの詳細を辿れる本文リンクを置く。
- file pathは省略表示だけで終えず、完全なpathとsource行を選択・コピーできるtextで示す。確認済みのsource URLがあればリンクする。local fileの行ジャンプがbrowserで使えるとは仮定せず、HTML内の根拠抜粋へ移動できるようにする。sourceの版や取得時点を添え、行番号の陳腐化を判別できるようにする。
- 索引、主要な関係、sourceはhoverやscriptに依存させない。通常のanchorリンクでkeyboardから辿れ、初期表示にtext fallbackがある形にする。長いpathは折り返す。

文書ownerはHTMLへの配置と検証を保持する。`show-me`から`diagram-design`へ渡すのは根拠付きの図の入力だけとし、文書全体や索引の順の決定を再委譲しない。

## 先に中身を抽出する

HTML構造や図を作る前に、source inventoryとclaim ledgerをcompactな作業メモとして作る。

- source inventory: file、section、symbol、差分、test、外部sourceのどこが何を裏付けるか。
- claim ledger: 主要主張、具体的な事実、仕組みまたは因果、境界・反例、読者への含意、source anchor。

各主要主張は、少なくとも具体的な根拠、仕組み、読者への含意へ接続する。境界条件や反例がmaterialなら省略しない。sourceで確認できない内容は、事実として補完せず推論または未確認と表示する。

文書型ごとのdetail unitは次を最低粒度にする。

- `decision-plan`: 選択肢、成立mechanism、採否理由、trade-off、entry / exit、failure、rollback、evidence。
- `technical-explainer`: input、具体的な処理、branch条件、data contract、state / side effect、failure / recovery、source。
- `change-review`: file / symbol、before / after、変更理由、caller / downstream impact、compatibility、test evidence。
- `research-report`: sourceごとの主張、evidence quality、比較軸、代表case、反例・限界、実務上の含意。
- `screen-diff`: 場面ごとの旧 / 新の要素、要素ごとの分類（追加、消える、変わる）、行き先、設計で消したか未作成かの区別、仮の値の明示。

「処理する」「連携する」「最適化する」「対応する」のような抽象語だけでdetailを閉じない。主体、対象、条件、観測可能な結果まで具体化する。長文化やsection数を情報量の代替にせず、同じ内容の言い換えを削る。

## Orientationとoverviewは索引にする

workflow、architecture、lifecycle、before / after、dependency、failure pathなどを説明し、3つ以上の相互作用するactor、component、stage、state、責務、dependencyが関係する文書では、中心主張の直後にorientationとaccessibleなinline SVG overviewを置く。欠如時failureが複数箇所へ伝播する場合も同じ扱いにする。単にfileやevidenceが3件あるだけでは発火しない。

orientationは長い背景説明ではない。次の5点を短く並べ、読者が「なぜ読むか」と「全体のどこを見ているか」を先に掴めるようにする。

1. 背景: この文書が必要になった状況。
2. without-this failure: この理解や変更がない場合に何が壊れるか。
3. 対象scope: どの境界、期間、system、file、機能を扱うか。
4. 目標状態: 読後または変更後に成立しているべき状態。
5. 全体内の位置: 対象が周辺actor、上流、下流、検証、運用のどこに接続するか。

overviewからdetailへ降りるzoom levelを固定する。

- Level 0: headerまたはdecision bandで中心主張を言い切る。
- Level 1: orientationで背景、without-this failure、scope、目標状態、全体内の位置を示す。
- Level 2: overview SVGで全体のactor / component / stage、主要flow、対象境界、failureの伝播先を一枚で示す。
- Level 3: detail sliceでoverview上の番号や名称を再利用し、一つのsubflow、before / after、failure path、diffだけを詳述する。
- Level 4: evidenceでtest、source、制約、残余riskを示す。

detailはoverviewと同じ名称、番号、境界名で接続する。overviewの情報を別図として再描画しない。overviewだけで説明を終えず、claim ledgerの具体的なdetail unit、evidence、含意へ降りる。detailで同じ情報を繰り返すだけなら、図を増やさず、該当番号への文章、diff、evidenceにする。

単一事実、単純な一操作、短い値比較、2要素だけのbefore / afterにはoverview SVGを強制しない。その場合も結論先行、scope、evidenceは保つ。

## Visual patternを選ぶ

読者の問いごとに主な表現を一つ選ぶ。

- 何を採用するか: decision band、案ごとの並置カード。
- 全体のどこを見るか: orientation、overview SVG。
- 何が変わるか: 旧 / 新の並置とラベル、diff。
- どこへ移るか: 行き先の矢印を持つ地図SVG。
- どう動くか: inline SVGのflow、sequence。
- ないと何が壊れるか: failure path、impact map。
- どの順で進めるか: entry / work / exitを持つWave。
- 合格したか: 受入条件ごとのカードと根拠リンク。
- 正確な値は何か: bar、ものさし。照合が目的のときだけ例外の表。
- 用語・出典を確認したい: evidence rail、定義リスト、脚注、source list。
- 全体を一枚の絵で見たい: 場面の絵（scene overview）、登場人物の地図。
- 身近な例と同じ形か: 同型並列図。
- 昔と今で何が変わったか: 期間の帯比較。
- どこまで許すか、いくらまでか: ものさし、bar。
- 悪化するとどうなるか: 下りの階段。

cardを先に並べない。同じ状態をbadge、card、summary、diagramで重複表示しない。文章で十分ならvisualを増やさない。

## 作成手順

1. source inventoryとclaim ledgerを作り、根拠不足と未確認を分離する。
2. 各sectionの問いを定め、文章だけで十分かを先に判断する。視覚化がmaterialなsectionだけ、`document-owner: creating-html-documents`を付けて`show-me`から最小表現またはvisual briefを得る。
3. `assets/editorial-document.html` を基礎にする。`head` に `<meta name="artifact-kind" content="html-document">` を置く（テンプレートには入っていない。lintはこのmetaがないと誤りにする）。既存HTMLの編集ではfilenameを変えない。編集の前に元のfileを `$TMPDIR` へ写しておき、編集の後に `python3 ~/.claude/scripts/html-change-list.py <元> <編集後>` で変更点を列挙する。各行が依頼のどの文に対応するかを確かめ、対応しない行は元へ戻すか、変えた理由を報告に書く。`screen-diff` では `references/screen-diff-explainer.md` の部品CSSを足す。
4. 文書型に応じて章を選び、不要なplaceholderとcomponentを削る。読者が初学者なら、初学者向けexplainerの既定（アナロジー、歴史、場面の絵、登場人物の地図、章ごとの絵、代表ケース、自己テスト）を章立てへ組み込む。読者自身の理解が目的なら、理解の穴に気づける解説の既定（読み終えたらできること、仕組みの地図、予想、根拠ラベル、誤解、折りたたんだ自己テスト、説明チェック）も組み込む。
5. 中心主張と現在地を最初のviewportに置く。背景説明から始めない。
6. orientation triggerに該当する場合だけ、中心主張の直後に短いorientationとoverview SVGを置く。
7. claim ledgerのdetail unitを本文へ展開する。重要な主張は具体例、境界、evidence、含意へ接続する。
8. 本文をprimary surfaceにする。desktopでは約68–76字幅、補助railは250–310pxを目安にする。
9. 図はinline SVGを正本にし、`role="img"`、`title`、`desc`、captionを付ける。SVG内の文字色はCSSクラスで指定する。Mermaid runtimeを新規導入しない。
10. codeはescapeし、言語classまたは明示labelを付ける。変更系文書では、変更理由の直後に関連diffを示す。
11. 表を使わない。例外で使う場合は理由を `table-exception` のmetaに残し、見出しcellへ`scope`を付ける。
12. 出典は主張の近くに置き、末尾のsource listへ接続する。sourceの内容と会話上の推測を混ぜない。
13. `python3 ~/.claude/scripts/lint-html-document.py <file>` を実行し、誤りを0にする。続けて `references/validation.md` のgateを通す。SVGを含む文書では、図中textの重なり、囲みrectからのはみ出し、viewBox外を機械検査し、0にしてから目視する。
14. 実装した文脈と別の、まっさらな文脈のレビュー担当に、fileのpathと画面の目的だけを渡してレビューさせ、根拠を確認した指摘を反映する。1文書につき1回、指摘の反映で見た目や構造が大きく変わったときはもう1回行う。理解のための解説では、pathと目的に加えて `references/mastery-explainer.md` の確認観点（事実の誤りと言い過ぎ、根拠ラベルの強さ、確かめた範囲、説明の無い語、理解の断絶）も渡す。
15. 検証合格後、ユーザーが自動表示を不要と明示していなければ、生成fileの絶対pathをhostのplatform openerで開く。
16. browser表示の成否、生成fileの絶対path、文書型、検証結果、レビューの実施と反映、残る制約を報告する。

## どのモデルでも守る最低水準

判断力に頼らず機械的に確かめられる条件を先に満たす。上の手順を省略した場合でも、次を満たさない文書は配布しない。

このうち機械で数えられる項目は、`python3 ~/.claude/scripts/lint-html-document.py <file>` が調べる。対象は、`<table`、`th` の `scope`、`h1`、`script`、id重複、外部resource、CSP、外部navigation linkの `rel`、`::before` / `::after` の文字、SVG `text` の `fill` 属性である。誤りが0になるまで直す。例外で表やscriptを使うときは、`<meta name="table-exception" content="理由">` または `<meta name="script-exception" content="理由">` を置く。lintは理由を表示し、「要確認」として扱う（終了コードは0のまま）。

lintの判定は、下の項目より弱い箇所がある。SVG `text` の `fill` 属性は、どの図にも当たるCSS（`svg text` など）が `fill` を指定している場合だけ誤りにし、それ以外は「要確認」として件数を出す。`counter()` と `attr()` で出す番号やラベルも「要確認」になる。「要確認」は、下の項目に照らして自分で判断する。

lintが通っても、最低水準をすべて満たしたことにはならない。強調した要素のラベル、はみ出し、SVG図中の文字の実寸、件数の一致、要約の太字、数値の根拠、レビューの記録は、下の項目を読んで確かめる。

- `<table` の出現回数が0である。例外で使うときは `table-exception` のmetaに理由がある。
- 意味を持つラベル（追加、消える、変わる、旧、新、番号）はすべて実要素で、CSSの `::before` / `::after` の `content` に文字がない。
- 強調した要素（outline、border、背景色で目立たせた要素）には、内側に文字ラベルがある。色だけで意味を伝えない。
- `overflow:hidden` を持つ箱の中で、外側へ出る `outline` を使っていない。数値と日付のセルに `overflow-wrap:anywhere` と `text-overflow:ellipsis` を使っていない。
- SVGの `text` の色は `fill` 属性ではなくCSSクラスで指定している。矢印の線がラベルの上を通っていない。
- SVG図中の文字は、表示倍率（描画幅÷viewBox幅）を掛けた実寸で12px以上である。
- 冒頭の件数や要約と、本文のラベル、末尾の一覧の分類が一致している。
- 冒頭の要約（decision band）の本文が、段落ごと `strong`、`b`、`font-weight:700` になっていない。本文幅の40%未満の列に、4行を超える文章を入れていない。用語集もこの規則に従い、各項目を4行以内の短い定義にして、長い説明は本文の初出に置く。
- `h1` は一つ、id重複0、script 0（interactionが不可欠な場合を除く）、外部resource 0、CSPあり、外部navigation linkに `rel="noopener noreferrer"`。
- 数値はすべて根拠か「仮」の明示があり、同じ数値を複数箇所で使うとき計算が合っている。
- 独立したレビュー担当の指摘を、根拠を確認してから反映した記録が報告にある。
- 理解のための解説では、自己テストの答えが `details` で折りたたまれ、各答えと各誤解に戻る章へのリンクがあり、予想の問いが示す答えの位置が実在する。根拠ラベルの無い言い切りが無い。

## 自己完結を既定にする

- system / local fontを使う。
- CSSは単一HTMLへinlineする。
- 画像はinline SVG、data URI、またはユーザーが指定した隣接local assetを使う。
- remote font、CDN、analytics、remote image、外部runtimeを既定では読み込まない。
- scriptは内容に不可欠なinteractionがある場合だけ追加する。static文書はscript 0を優先する。
- CSPを付ける。static単一fileの既定は `default-src 'none'; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'` とする。
- HTML自身へbrowser起動用のscript、redirect、shellを埋め込まない。browserを開く責務は、検証後にhost側のplatform openerが担う。
- clipboard、PDF生成、印刷最適化、公開script、git commit / pushはHTML生成と別能力である。明示依頼と個別gateなしに実行しない。

## 視覚言語

- 長文はeditorial寄りにし、dashboardのKPI card群へ変換しない。
- hierarchyは見出し、余白、rule、位置で作る。radius、shadow、色の種類を増やして作らない。
- accentは1色を基本とし、警告、追加、削除など意味が異なる場合だけ補助色を使う。
- gradient、glass、装飾pill、意味のないicon、過剰なmotionを既定にしない。
- 日本語本文は15–17px、line-height 1.75–1.95を起点に実画面で調整する。
- 既定は1440x900前後のPC閲覧とする。mobile responsive、tablet調整、print stylesheet、PDF exportは明示依頼時だけ追加する。
- hoverだけに主要情報を置かない。
- 冒頭の要約（decision band）は、通常の太さのリード文1〜3文で結論を言う。段落全体を太字や大きい文字にしない。強調は核となる語句2〜3個までにする。
- 要約に並列する要点（当事者ごと、案ごと、効果ごと）が2つ以上あるときは、一文に詰めず、見出し1行と補足1行の項目に分けて並べ、各項目から本文の該当節へリンクする。リンクには下線などの見た目の手がかりを付け、hoverの背景だけに頼らない。
- 状態、照合範囲、出典の注記は、要約の下端の一行に置く。本文より狭い補助列に長文を入れて細切れに折り返させない。
- 要約の各項目は、本文と同じ条件、記号、推論の表示を使う。本文で条件付きの主張を、要約で言い切らない。
- 図のviewBoxの幅は、図枠の実幅に近づける（表示倍率0.9以上）。横に並べると本文欄で縮む図は、縦に積む配置に組み直す。番号や記号は丸いバッジなどの実要素にし、ラベルの文字列に混ぜない。ラベルと補足は箱の内側に余白を残して収め、収まらない説明はcaptionか本文へ移す。

## 完了条件

次を確認できるまで完成と報告しない。

- 3秒でpage purpose、中心主張、現在地を区別できる。
- 1440x900で意図しない横overflow、text overlap、clipがない。
- heading level skip、duplicate id、表が0。例外で表を使った場合は `table-exception` のmetaに理由がある。
- keyboard focusが見え、主要情報がhover専用でない。
- contrastと色以外の意味表示を考慮する。ラベルは実要素で、疑似要素のcontentに文字がない。
- 外部resourceは依頼で許可されたものだけ。既定は0。
- 制作過程やpromptの痕跡が本文に残らない。
- orientation triggerに該当する文書では、中心主張直後のorientation、accessible overview SVG、対応するdetail slice、evidenceが同じ名称や番号で接続している。
- 各主要主張が具体的な根拠、仕組み、読者への含意へ接続し、materialな境界条件または反例が落ちていない。
- technical flowではinput、branch、data / state、side effect、failure / recovery、sourceを追える。
- overview、見出し、一般論だけで本文を埋めていない。
- triggerに該当しない単純文書では、図を省いた理由が文書構造上自然で、結論、scope、根拠が不足していない。
- `show-me`へ渡したsectionは局所visual sliceとして閉じ、文書ownerの循環、章立ての重複、根拠のない要素追加がない。
- 初学者向けexplainerでは、場面の絵と登場人物の地図（地図が場面の絵の繰り返しになる場合は、場面の絵の直後の箇条書き）があり、主要章に「たとえるなら」と「比喩の限界」があり、歴史の章、仮設の代表ケース、章ごとの絵、自己テストが揃っている。
- 理解のための解説では、読み終えたらできること、仕組みの地図と中心の問い、読む前の予想とその回収、根拠の強さのラベルと確かめた範囲、わかったつもりの罠、折りたたんだ自己テスト、最後の説明チェックが揃い、「読み終えたらできること」の各項目に対応する問いがある。
- screen-diffでは、凡例と件数、行き先の地図（差分が一つの画面に閉じる場合は、地図の代わりに件数の行の「画面の構成は変わらない」）、場面ごとの旧 / 新並置、消えたものと行き先、追加したもの、同じもののカードが揃い、分類が全章で一致している。
- SVG図のtext同士の重なり、rect外へのはみ出し、viewBox外が0である。
- 独立したレビュー担当の指摘を確認し、反映した。
- 明示的なopt-outがない限り検証済みfileをbrowserで開き、起動できない環境では失敗理由と絶対pathを報告する。

見た目の好みだけで合格にしない。中心主張、具体的detail、根拠到達、含意、安全性を確認する。mobile、print、PDFは依頼された場合だけ追加rubricを適用する。
