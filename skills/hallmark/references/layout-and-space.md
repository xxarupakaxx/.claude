# 余白とレイアウト

見た目の密度をカード数で決めず、主軸、measure、節間、比較列の距離で決める。中央揃えを既定の解にせず、本文と図の役割に合う軸を選ぶ。

## token

4pt基準の役割名scaleを使う。

~~~css
:root {
  --space-2xs: 0.25rem;
  --space-xs: 0.5rem;
  --space-sm: 0.75rem;
  --space-md: 1rem;
  --space-lg: 1.5rem;
  --space-xl: 2rem;
  --space-2xl: 2.5rem;
  --space-3xl: 4rem;
  --space-4xl: 6rem;
}
~~~

同じgapだけを繰り返さず、labelと本文の間、節の間、比較列の間に別のtokenを割り当てる。siblingsの間はgapを使い、段落の連続性はline-heightで作る。

## 文書の基準

- 本文measureは55–72字程度。図・表は必要なときだけ本文幅から広げる。
- 計画書のBefore / Afterは repeat(2, minmax(0, 1fr))、gapは32px以上、panel paddingは24px以上を起点にする。
- panelのmin-widthは0にして長い日本語・pathが列を押し広げない。
- 375px前後では一列へ移し、bodyの横overflowを発生させない。
- 1440pxで見出しがfirst viewportを占拠しない。余白はタイトルより本文節と比較列へ使う。
- dl、table、preの既定marginをリセットし、節内のgapをtokenで管理する。

## 見た目の変化

同じ情報を同じカードへ変換し続けない。planは縦stage、Before / Afterは横diptych、依存はSVG、根拠は表または本文、と表現を分ける。装飾のために余白を消費せず、読み手が視線を分けるための空白を残す。
