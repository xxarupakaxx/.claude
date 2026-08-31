# 狭幅とレスポンシブ

幅を縮めたときに情報を隠すのではなく、読み順を保ったまま形を変える。

## 検査幅

計画書と自己完結HTMLは少なくとも375、640、768、1024、1440pxで確認する。ユーザーが別の幅を指定したら追加する。各幅でbodyと主要wrapperに意図しない横overflow、clip、重なり、クリックlabelの改行がないことを確認する。

## 変形

- desktopのBefore / Afterは二列、375pxでは一列へ移す。
- 依存SVGはdesktopの横flowとmobileの縦flowを別viewBoxで用意し、ラベルを縮小して読めなくしない。
- tableと長いcodeは内部wrapへ置き、bodyを横スクロールさせない。
- navigationやanchorは狭幅でも常に本文から到達できる。
- 余白を0にして密度を上げるのではなく、見出し・本文・図の順序とmeasureを保つ。

overflow-x: hiddenで壊れたレイアウトを隠さない。原因を直し、必要な局所wrapだけへoverflowを許可する。
