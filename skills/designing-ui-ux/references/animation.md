# Motion contract

## Motionに仕事を与える

motionは次のいずれかを担う場合だけ使う。

- actionへのfeedback
- objectの連続性と移動先の説明
- hierarchyまたはstate changeの説明
- gestureと結果の直接的な接続
- attentionの短い誘導

装飾、遅さの隠蔽、操作可能に見せるためだけのmotionは追加しない。

## 時間より知覚を設計する

小さなfeedbackは短く、大きなspatial transitionは距離が理解できる長さにする。
固定の150ms、200ms、300msをすべてへ当てはめない。

次を一つのmotion token setとして定義する。

```css
:root {
  --motion-instant: 100ms;
  --motion-fast: 160ms;
  --motion-base: 220ms;
  --ease-enter: cubic-bezier(.2, .8, .2, 1);
  --ease-exit: cubic-bezier(.4, 0, 1, 1);
}
```

値は開始点にすぎない。
距離、頻度、入力方法、platform conventionを実画面で確認して調整する。

## Interactionをinterrupt可能にする

- repeated actionをanimation完了まで待たせない。
- gestureで動かすobjectは指やpointerに追従させる。
- openとcloseでspatial logicを一致させる。
- exitはenterより短くして、次の操作を待たせない。
- layout animationでcontentのreading positionを不用意に動かさない。

`transition: all` は、意図しないpropertyまで補間するため使わない。
transformとopacityは有用だが、semantics、focus、hit targetの変化を代替しない。

## Reduced motionを別の体験として設計する

```css
@media (prefers-reduced-motion: reduce) {
  .spatial-transition {
    transform: none;
    transition-property: opacity;
  }

  .ambient-loop {
    animation: none;
  }
}
```

parallax、zoom、large translation、animated blur、反復motionを減らす。
状態変化は即時表示、fade、静的なhighlightなどで残す。

## 実画面で確認する

- 連打、途中取消、戻る操作でstateが壊れない。
- low-end deviceでinput responseを遅らせない。
- loading animationが実際のprogressと誤認されない。
- focusがanimation後の意味のある位置にある。
- reduced motionでも同じtaskを完了できる。

AppleのHuman Interface Guidelinesは、motionを目的に結び付け、任意にし、短く正確にし、取消可能にすることを勧めている。

- Motion: https://developer.apple.com/design/human-interface-guidelines/motion
- Accessibility: https://developer.apple.com/design/human-interface-guidelines/accessibility
