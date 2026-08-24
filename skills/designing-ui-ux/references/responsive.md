# Responsive contract

## Breakpointより変化の条件を決める

breakpointはdevice名ではなく、contentとinteractionが破綻する幅に置く。
projectの既存breakpointがある場合は、それを優先する。

component内部の変化はcontainer query、page全体のnavigationやshellはviewport queryを使い分ける。

## 各領域の変換規則を記録する

| Region | Wide | Medium | Narrow | 優先して残すもの |
|---|---|---|---|---|
| Navigation |  |  |  |  |
| Header actions |  |  |  |  |
| Main content |  |  |  |  |
| Secondary panel |  |  |  |  |
| Data surface |  |  |  |  |

hide、stack、wrap、collapse、scroll、summarize、moveのどれを使うか明示する。
「mobileでは非表示」だけでは、機能が失われていないか判断できない。

## Contentを縮めずreflowする

- primary actionとcritical statusを先に残す。
- secondary actionはoverflow menuへ移せるが、発見可能性を確認する。
- two-pane layoutは、masterとdetailの戻り方を定義する。
- toolbarはwrap、priority overflow、mode切替を使い分ける。
- long labelをtruncationする場合はfull valueへ到達できるようにする。

## Tableとchartを問いに合わせて変換する

tableを一律にcardへ変換しない。
column比較が仕事なら横scroll、column priority、sticky key column、detail viewを使う。
行単位の閲覧が仕事ならstacked listへ変換できる。

chartはaxis、legend、tooltip、annotationが狭幅で読めるか確認する。
情報を減らす場合は、失われる問いを明示する。

## Input methodを幅と分けて扱う

狭い画面が必ずtouchとは限らず、広い画面が必ずmouseとも限らない。
`hover`、`pointer`、keyboard、touchをviewportとは別に確認する。

hoverにだけactionや説明を置かない。
touch targetを視覚的なicon sizeだけで判断せず、実際のhit areaを確認する。

## 証拠viewportを選ぶ

既定は375px、768px、1440pxとする。
次を追加する価値がある場合は、境界幅も確認する。

- navigationが切り替わる直前と直後
- tableがoverflowを始める幅
- dialogがsheetへ変わる幅
- long contentでwrapが変わる幅

横overflow、content clipping、focus visibility、safe area、on-screen keyboardを主要flowで確認する。
