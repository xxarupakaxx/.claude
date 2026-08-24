# Visual direction catalog

## Catalogは会話の語彙として使う

style名は、完成形を自動で決めるpresetではない。
Briefを満たす方向を比較するための語彙として使う。

| Axis | 一方 | もう一方 | 判断材料 |
|---|---|---|---|
| Density | compact | spacious | 頻度、比較量、習熟度 |
| Contrast | quiet | bold | attention、brand、利用環境 |
| Geometry | sharp | soft | precision、approachability、platform |
| Surface | flat | layered | hierarchy、overlay、object model |
| Typography | utilitarian | expressive | content量、brand、localization |
| Composition | systematic | editorial | repetition、story、scan pattern |
| Motion | restrained | expressive | task frequency、spatial model、comfort |

各axisを同じ側へ揃える必要はない。
たとえばcompactなdata UIでも、重要な結果だけexpressive typographyを使える。

## 代表的な方向性を分解する

### Precision

- 高い情報密度
- 明確なalignmentとborder
- 小さなcontrast差
- 短く直接的なmotion

developer tool、operations、analysisに合う場合がある。
小さいtextとtargetを正当化しない。

### Warm utility

- 読みやすいtype
- 穏やかなsurface contrast
- 十分なspace
- 明快なguidance

初回利用や共同作業に合う場合がある。
大きなradiusとshadowを自動的に選ぶ意味ではない。

### Editorial

- 強いtype hierarchy
- asymmetric composition
- contentの順序を作る余白
- imageとcaptionの関係

storyやcurationに合う場合がある。
task密度が高いcontrol surfaceへそのまま適用しない。

### Immersive

- edge-to-edge media
- spatial layer
- controlled motion
- chromeの抑制

media、map、creation toolに合う場合がある。
navigation、focus、reduced motionを失わないようにする。

## 流行styleを使う条件

glass、bento、brutalism、neumorphism、clay、gradient meshなどは、Briefとinteractionに役割がある場合だけ使う。

- glassは背景との関係を残す一時surfaceに限定する。
- bentoは異なるsizeの情報優先度を表す場合に使う。
- brutalismはbrandとcontentに合う場合に使い、accessibility違反を作風と呼ばない。
- neumorphismはboundaryとstate contrastを失いやすいため、interactive controlの主表現にしない。
- gradientはdepth、brand、focusの役割を持つ場合に使う。

styleを選んだ後、使わない表現も一つ以上決める。
このanti-signatureが、複数styleの無秩序な混在を防ぐ。
