# Component contract

## Componentは見た目ではなく契約で定義する

各componentについて、次を定義する。

- purposeと利用条件
- anatomy
- content constraints
- variants
- states
- input methods
- accessible semantics
- responsive behavior
- errorとrecovery

見た目が似ていても、意味とinteractionが異なるものを一つのcomponentへ押し込まない。

## Component budgetを先に決める

component libraryの部品を使えることと、その画面に必要なことは別である。
初期画面の既定予算は、compactなorientation一つ、主要surface一つ、primary action一つとする。
二つ目以降のpanel、navigation、summary、status表現には、異なる利用者の問いが必要になる。

各componentを次のいずれかへ分類する。

- **always**：現在地、判断対象、primary actionに必要。
- **selection**：利用者が対象を選んだ後に必要。
- **on-demand**：根拠、全文、履歴、設定など、確認を求めたときだけ必要。

alwaysが増えたら、文字や余白を縮める前にselectionまたはon-demandへ移す。
同じ状態を複数のcomponentで表している場合は、正本となる一つを残して統合する。

全体の順序、範囲、現在位置が主要タスクに必要な画面では、compact overviewをalwaysにできる。
Overviewには詳細、指標、primary actionを持たせず、主要surfaceと視覚的に競合させない。

## Native-firstでcontrolを選ぶ

button、link、input、select、textarea、details、dialog、tableなど、必要な意味と挙動を持つnative elementを優先する。
custom componentは、visual stylingのためではなく、既存要素で表せないinteraction contractがある場合だけ作る。

custom widgetにはkeyboard、focus、name、role、value、pointer、touch、screen readerの実装と検証が必要になる。

## State matrixを持つ

| State | Visual | Content | Interaction | Accessibility |
|---|---|---|---|---|
| default |  |  |  |  |
| hover |  |  |  |  |
| focus |  |  |  |  |
| pressed |  |  |  |  |
| selected |  |  |  |  |
| disabled |  |  |  |  |
| loading |  |  |  |  |
| error |  |  |  |  |

発生しないstateは省略してよい。
`disabled`と`loading`、`selected`と`pressed`は意味が異なるため、同じ見た目で代用しない。

## Formは入力より復旧を設計する

- label、description、format、requiredを入力前に理解できる。
- validation timingをfieldの性質に合わせる。
- errorはfieldと関連付き、修正後に解消される。
- submit中の重複実行を防ぎ、入力値を保つ。
- password manager、autofill、pasteを妨げない。
- 必要なkeyboard typeとautocomplete tokenを指定する。

placeholderをlabelの代わりにしない。

## Navigationは現在地とscopeを示す

navigationは、移動先の一覧だけでは足りない。
現在地、workspaceやaccountのscope、戻り先、深い階層でのorientationを扱う。

mobileではdesktop sidebarを隠すだけでなく、頻度と重要度からprimary navigationを再配置する。

## Data surfaceはtaskに合わせる

metric card、table、chart、timelineを、データがあるという理由だけで並べない。

- 比較には共通scaleと基準線を使う。
- 正確な値の参照にはtableを残す。
- 時系列には欠損、期間、粒度を示す。
- statusにはcolor以外のlabelまたはshapeを使う。
- chart typeは問いに合わせ、3Dや装飾で読み取りを妨げない。
- loading、no data、filtered empty、errorを区別する。

数値は必要に応じて`font-variant-numeric: tabular-nums`を使う。
monospace fontは、製品のtype systemと可読性に合う場合だけ選ぶ。

## Cardを既定のcontainerにしない

cardは、独立したobject、選択単位、異なるsurfaceが必要なgroupに使う。
同じpage contextの情報をすべてcardへ入れると、階層が平坦になる。

section、list、table、split pane、inline groupなど、内容とtaskに合う構造を選ぶ。
