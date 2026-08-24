# Layout and craft

## Rhythmをtoken化する

4pxまたは8pxのbase gridは、値を減らして一貫性を作る方法である。
すべての寸法を機械的に倍数へ丸める規則ではない。

```css
:root {
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;
  --space-12: 48px;
}
```

optical alignment、1px border、icon geometry、platform conventionには例外がある。
例外はcomponent内部へ閉じ込め、理由を説明できる値にする。

## Spaceは関係を表す

近いものを関連付け、遠いものを分ける。
paddingの対称性は有用な既定値だが、content hierarchy、baseline、touch target、asymmetric compositionが理由になる場合は崩してよい。

同じlevelのsection間隔を揃え、component内部の間隔より大きくする。
余白を増やす前に、不要なcontainer、label、dividerがないか確認する。

## Densityは利用状況で決める

- 頻繁に比較するpower-user UIは、scan distanceを短くする。
- 初回利用や高リスク操作は、説明とseparationを増やす。
- touch中心のUIは、targetと誤操作防止の余白を優先する。
- large displayでもline lengthとdecision scopeを無制限に広げない。

compact、comfortableなどのdensity modeを作る場合は、情報量だけでなくtarget、row height、truncation、keyboard navigationを一緒に確認する。

## Alignmentで構造を作る

見出し、field label、numbers、actionsに共有anchorを持たせる。
意味のないcenter alignmentはscanを遅くする。

textはbaseline、数値はdecimalまたは右端、formはlabelとinputの関係を優先する。

## Shapeとdepthを限定する

radiusはcomponent familyとnestingでscaleを決める。
すべてを同じradiusにする必要はないが、同じ意味のcomponentで値を変えない。

depthは次の一つまたは組合せで表す。

- surface color
- border
- shadow
- overlap
- blur

同じlevelへ複数の強い手段を重ねない。
shadowは浮いているobjectと一時的なoverlayへ使い、page上のすべてのsectionをcard化するために使わない。

## 実データで磨く

短いplaceholderだけでspacingを決めない。
長いtitle、0件、桁の大きい数値、多言語、画像なし、permissionなしを並べて確認する。

1pxの調整は、alignment、contrast、hit area、reading rhythmのどれを改善するか説明できる場合に行う。
