# HTML文書system

## Content-first gate

最初にsource inventoryとclaim ledgerを作り、本文へ残す具体性を確保する。主要主張は、具体的な事実、成立mechanismまたは因果、source anchor、読者への含意へ接続する。materialな境界条件、反例、failureがある場合は併記する。

overview、見出し、一般論はdetailの代わりにならない。sectionを増やすより、読者が次の判断やsource確認へ進める具体情報を優先する。

## Visual owner contract

文書全体は`creating-html-documents`がownerになる。各sectionの局所visualだけを`show-me`へ渡し、問い、evidence anchor、must-show、omit、text fallbackをvisual briefで固定する。`document-owner: creating-html-documents`のcontextでは、`show-me`は最小表現を返して終了し、HTML文書全体を作成せず再委譲もしない。

Overview gateの判定、章立て、source inventory、claim ledger、evidenceへの接続、HTML composition、accessibility、CSP、validation、browser表示は文書ownerが保持する。`show-me`の提案が本文を言い換えるだけなら採用せず、文章または並置を残す。

## Overview gate

workflow、architecture、lifecycle、before / after、dependency、failure pathなど、3つ以上の相互作用するactor、component、stage、state、責務、dependencyの関係を理解しないと判断できない文書では、中心主張の直後にorientationとaccessibleなinline SVG overviewを置く。欠如時failureが複数の下流へ伝播する場合も必須にする。単にfileやevidenceが3件あるだけでは発火しない。

orientationは背景、without-this failure、対象scope、目標状態、全体内の位置を短く示す。全体像の図は、図の問いを一文で決め、部品表から形を選んで描く（`overview-patterns.md`）。決まった形の図に題材を流し込まない。読者が対象を業界や事業ドメインの中に位置づけないと理解・判断できない文書では、ドメイン俯瞰図にする。failureの伝播先は、図の問いに失敗が含まれるときだけ描く。detail sliceはoverviewの番号、名称、境界を再利用し、claim ledgerの具体的なsubflow、before / after、failure path、diff、evidenceへzoomする。overviewだけで説明を完了せず、再描画や同じ情報の重複表示もしない。

単一事実、単純な一操作、短い値比較、2要素だけのbefore / afterには図を強制しない。図を省く場合も結論、scope、根拠の位置は崩さない。

## Decision plan

最初のviewportで「何を採用するか」「現在どこか」「何が次のgateか」を判断できるようにする。

推奨順序:

1. 中心主張とstatus。
2. Overview gate該当時のorientation: 背景、without-this failure、scope、目標状態、全体内の位置。
3. Overview gate該当時の全体像の図: 図の問いの例は「何を採用すると、どこが変わり、何に頼るか」。形は問いで選び、failureの伝播が判断の争点なら影響マップにする。
4. 現状と目標。
5. 選択肢の比較と採否理由。
6. Overview gate該当時のdetail slice: 目標構造または重要な移行flow。
7. entry / work / exitを持つ実装Wave。
8. acceptanceとevidence。
9. risk、停止条件、rollback。
10. source。用語は本文の初出で定義する。

Task一覧だけを計画書と呼ばない。誰が何をするかだけでなく、なぜ、その順なのか、何をもって次へ進むのかを書く。

## Technical explainer

推奨順序を一本にまとめる。印の無い項目はどの文書にも置き、印のある項目は条件に当たるときだけ置く。【理解】は読者自身の理解が目的の文書（`mastery-explainer.md`）、【初学者】は読者が対象ドメインの前提知識を持たない文書（`illustrated-explainer.md`）、【索引】はSKILL.mdの「ファイル・関数を追う索引」を置く文書（複数fileの解説、file指定の処理説明）に当たる。既定を重ねるときも、この順のまま印の項目を差し込む。【初学者】の条件は目的が読者の理解であることを含むので、【初学者】の文書には【理解】の項目も置く。

1. 一文の結論（decision band）。
2. 【理解】読み終えたらできること。
3. 【初学者】章を読む順。decision bandの外に一行で置く。
4. Overview gate該当時のorientation: 背景、without-this failure、scope、目標状態、全体内の位置。
5. Overview gate該当時の全体像の図: 図の問いに合う形で、全体構造と主要flowを示す。対象をドメインの中に位置づける必要があればドメイン俯瞰図にする。【初学者】では場面の絵にし、直後に登場人物の地図を置く。場面の絵に収まらない主体を見せる必要があるときだけ、場面の絵の前にドメイン俯瞰図を置き、登場人物の地図はドメイン俯瞰図で代える。
6. 【索引】ファイルの索引と、それに続く依存関係または呼び出し順の図。
7. 【初学者】身近な例で掴む章。
8. 読者が先に必要とする最小用語。読者が知らない語が無ければ章を置かない。
9. 【初学者】代表ケースの時系列。
10. 【初学者】なぜ生まれたか。
11. 【理解】仕組みの地図と中心の問い。【初学者】を重ねない文書では、地図の冒頭に短い具体例を一つ置いてから一般化する（`mastery-explainer.md` の「段を飛ばさない説明」）。
12. Overview gate該当時のdetail slice: input、branch条件、data contract、state / side effect、output。【理解】主要章の前に、読む前の予想を置く。【初学者】各章に一枚の絵と「たとえるなら」を置く。
13. failure mode、検知、retryまたはrecovery。【初学者】では失敗の入口から終点までを階段で描く。
14. 具体例とmaterialな境界・反例。【理解】では、別の場面への適用もここで扱う。
15. 【初学者】規制・制度（対象を外から縛るものがあるときだけ）と、似た言葉の整理。
16. 読者への含意、検証方法。
17. 【理解】わかったつもりの罠、答えを折りたたんだ自己テスト、最後の説明チェック。【初学者】の自己テストもここに一つにまとめる。
18. source。

同じ内容を二度描かないよう、次のように統合する。

- overviewと索引の後の図: 索引の後の図がoverviewと同じ要素と矢印になるなら別に描かず、overviewの各nodeに索引の番号を振る。captionには、その番号が読む順で実行の順ではないこと、矢印の意味（依存関係か呼び出し順か）、runtime Levelを書く。
- overviewと仕組みの地図: overviewがある文書では、仕組みの地図で図を描き直さず、overviewの番号と名称を使って、要素、役割と持っている情報、因果の連鎖、境界を本文に書く。overviewが無い文書では、本文の箇条書きか短い図で示す。
- 場面の絵と登場人物の地図: 地図が場面の絵の繰り返しになるなら、場面の絵の直後の箇条書きで、各主体の役割と担当する番号・章番号を示す。

用語は本文の初出で定義する。用語集は既定で作らず、SKILL.mdの「目次と用語集は必要なときに開く」の条件に当たるときだけ、目次の折りたたみに参照用として置く。8の最小用語も、読者が知らない語だけにする。

読者が対象ドメインの前提知識を持たないなら、`illustrated-explainer.md` の既定を上の【初学者】の位置に重ねる。読者が実務者なら【初学者】の項目は置かない。

読者自身の理解が目的なら、前提知識の有無にかかわらず `mastery-explainer.md` の既定を重ねる。change-reviewとresearch-reportでも、目的が読者の理解なら同じにする。

## Change review

推奨順序:

1. 変更の理由と影響。
2. Overview gate該当時のorientation: 背景、without-this failure、scope、目標状態、全体内の位置。
3. Overview gate該当時の全体像の図: 図の問いの例は「この変更はどこにあり、上流と下流の何に波及し、どこで戻せるか」。形は問いで選び、失敗の伝播が変更の争点なら影響マップにする。
4. 複数fileの変更では、ファイルの索引と、それに続く依存関係または呼び出し順の図。
5. before / afterの要約。
6. Overview gate該当時のdetail slice: file / symbol、before / after、変更理由、関連diff。
7. caller、data / API / UI、downstreamへの影響。
8. migration、compatibility、rollback。
9. test evidence。
10. 残るrisk。

diffだけを並べず、読者が先に理由と影響を理解できるようにする。

読者の理解が目的のchange-review（PRの解説など）では、Technical explainerの【理解】の項目（読み終えたらできること、仕組みの地図と読む前の予想、わかったつもりの罠・自己テスト・最後の説明チェック）を、同じ位置関係で差し込む。チームが差分を確かめて判断するためのレビュー記録には差し込まない。

## Research report

推奨順序:

1. 結論と次の一手。
2. Overview gate該当時のorientation: 調査対象が全体のどこにあり、未理解だと何を誤判断するか。
3. Overview gate該当時の全体像の図: 市場、業界、競合の調査では、調査対象を置いたドメイン俯瞰図にする。判断軸の比較が問いなら位置づけの地図、sourceの関係が問いならevidence mapとして描く。
4. scope、母集団、方法。
5. 主要発見。
6. Overview gate該当時のdetail slice: sourceごとの主張、evidence quality、比較（並置カード）、代表case、反例。
7. 限界と誤読しやすい点。
8. 調査結果から直接導ける含意と推奨。
9. source list。

事実、推論、提案を構造で区別する。数字は意味まで翻訳し、読者に再計算させない。

## Screen diff

依頼が差分を求め、かつ対象が画面の構造を持つときだけ選ぶ。API、コード、設定、データの差分はChange reviewで扱う。この型では、凡例と件数がorientationの役を、構造の地図がoverviewの役を担う。Overview gateに当たっても、別のorientationとoverview SVGは足さない。

推奨順序:

1. 一文の中心主張と凡例（追加、消える、変わる、旧、新）。
2. 差分の件数（消えた、増えた、変わった）と対象名。
3. 構造の地図: 旧と新のメニューを左右に置き、行き先を矢印で結ぶSVG。差分が一つの画面の中に閉じ、メニューが変わらず、別の画面へ移る要素も無いときは省き、2の件数の行に「画面の構成は変わらない」と書く。
4. 業務順の場面: 旧 / 新のミニ画面の並置と1〜3文の説明。
5. 消えたものと行き先、追加したもの、同じもの・未作成・どちらにもないもののカード。

件数、地図、場面のラベル、末尾のカードで分類を一致させる。表は使わない。詳細は `screen-diff-explainer.md`。

## 共通component

### Orientation

中心主張の直後に置き、背景、without-this failure、対象scope、目標状態、全体内の位置を短く示す。長い経緯、作業日誌、網羅的な前提列挙へ膨らませない。

### 全体像の図

図の問いを一文で決め、部品表から形を選んで描く。形の一覧、ドメイン俯瞰図の描き方、記号と凡例の規則、骨格は `overview-patterns.md` に置く。`role="img"`、`title`、`desc`、captionを持つinline SVGにする。Mermaid、remote resource、runtime scriptを前提にしない。

本文の欄の全幅に置き、viewBoxの幅を図枠の内側の実幅に合わせ、縮小で文字を小さくしない。番号は丸いバッジの実要素にし、ラベルは箱の内側に余白を残して収める。矢印は箱と箱の間の余白だけを通す。線の種類、枠、番号の意味は図の中の凡例に書き、英字一文字の記号を置かない。

### Scene overview と登場人物の地図

初学者向けexplainerのoverviewは、箱と矢印だけでなく、当事者を建物や人の形で置き、対象で実際に動くもの（決済ならモノ・書類・お金、認証なら要求・証明・権限）と記録の動きを段に分けて描く場面の絵にする。続けて、中央の当事者を周辺の主体が囲む登場人物の地図を置き、各主体が担当する番号と章番号を書く。主体は実在する数だけ置き、地図が場面の絵の繰り返しになるなら、場面の絵の直後の箇条書きで代える。場面の絵と、別に描く登場人物の地図は、`role="img"`、`title`、`desc`、captionを持つinline SVGにする。

### Analogy

「たとえるなら」の囲み。身近な例で仕組みを掴ませ、末尾の「比喩の限界」で比喩が崩れる点と、それを扱う章を示す。主要章に一つ置き、同じ比喩の再利用は許すが、比喩のための数字や人物の創作はしない。

### 読み終えたらできること

冒頭の要約の直後に置く。読後にできることを、外から確かめられる動詞で3〜5個書き、自己テストの問いと対応させる。

### 予想と回収

主要章の前に、答えを読む前に予想させる問いを置く。答えの位置を正確に示し、回収する箇所では、予想が外れた人の見落としを書く。

### 根拠の強さのラベル

「確認済み」「出典の記載」「推測」「未確認」を、文字のラベルで主張に付ける。確かめた範囲（環境、版、条件）を併記し、確認済みの欄に推測を混ぜない。

### わかったつもりの罠

誤解、実際、戻る章の3点を1項目にした一覧。読者が本当に持ちそうな誤解だけを載せる。

### 自己テスト

問いと、`details` で折りたたんだ答え。答えには戻る章へのリンクを付ける。説明、予測、区別、境界、応用の問いを混ぜる。

### Detail slice

overviewの番号、名称、境界を再利用し、一つのsubflow、before / after、failure path、diffを詳述する。具体的な対象、条件、結果、source anchor、読者への含意を持たせ、overviewと同じ全体図を描き直さない。

### Decision band

一つの結論と、その根拠の状態を置く。複数のKPIを並べない。上から次の順にする。

1. kicker：「一言でいうと」「結論」などの短いラベル。
2. リード文：通常の太さの1〜3文。段落全体を太字や大きい文字にしない。強調は核となる語句2〜3個まで。
3. 要点の並置：並列する要点（当事者ごと、案ごと、効果ごと）が2つ以上あるときだけ置く。1項目は見出し1行と補足1行にし、本文の節へリンクする。項目名には下線などリンクと分かる手がかりを付ける。
4. 状態注記：状態、照合範囲、出典を下端の一行に置く。狭い右列に入れない。

要約の各項目は、本文と同じ条件、記号、推論の表示を使う。本文で条件付きの主張を、要約で言い切らない。章を読む順、目次、用語はbandに入れず、bandの外に置く。

### 折りたたみの目次と用語集

本文前の左上に`details` / `summary`を置き、初期状態は閉じる。展開一覧も左揃えとし、右側に目次を配置しない。本文は一列とし、目次用の列を予約しない。章リンクは`nav`に置く。用語集は既定で作らず、SKILL.mdの条件に当たるときだけ`nav`の外へ置く。展開時は通常の文書flowで本文を下へ押し出し、同じsummaryで閉じる。重要な根拠と留保は本文に残す。常設sidebarは明示依頼時だけ使う。

### Comparison cards

選択肢を同じ順序の項目（成立条件、欠点、採否理由）で書いたカードを横に並べる。軸を表にして読者に行と列を往復させない。採用案はdecision bandで先に言い切る。

### Wave route

各Waveにentry、work、exitを持たせる。単なる番号付きTaskと区別する。

### Figure

図、caption、sourceを一体にする。diagram内の色だけに意味を依存させず、labelと形でも区別する。

### Diff

追加、削除、contextを行単位で示す。赤緑だけでなく記号とlabelを併用する。

### Before / after pair

同じ場面の旧と新を左右に並べ、変わった要素に実要素のラベル（追加、消える、変わる）を付ける。画面ならCSSで描いたミニ画面、コードならdiff、期間なら帯。詳細は `screen-diff-explainer.md`。

### Change map

旧と新の構造を左右に置き、旧要素の行き先を1色の矢印で結ぶinline SVG。消える要素は破線枠、追加は実線枠。矢印の線がラベルの上を通らない配置にする。

### 表の例外

表は既定で使わない。数値の照合が読者の目的で、3列以上の数値を突き合わせないと判断できない場合だけ使い、理由をmetaに残す。責務や比較は並置カードにする。
