# Accessibility contract

## 適合基準と推奨値を分ける

Web UIはWCAG 2.2 AAを基準にする。
組織、法域、platform、projectがより強い基準を持つ場合は上乗せする。

| 項目 | WCAG 2.2 AAの基準 | 推奨 |
|---|---|---|
| 通常text contrast | 4.5:1 | 小さい文字や細い文字は余裕を持たせる |
| large text contrast | 3:1 | sizeだけで階層を作らない |
| UI component、state、graphic | 3:1 | focusとselectedを形でも区別する |
| target size | 24×24 CSS pxまたは規定の例外 | touch中心なら44×44 CSS px前後を目安にする |
| reflow | 320 CSS px相当で情報と機能を失わない | 横scrollは表やcanvasなど必要なsurfaceに限定 |
| text resize | 200%で情報と機能を失わない | containerとcontrolをcontentに合わせて伸ばす |

44×44をWCAG 2.2 AAの適合条件と記述しない。
小さいtargetを使う場合は、spacing、inline、equivalentなど2.5.8の例外条件を確認する。

WebのCSS px、iOSのpt、Androidのdpを同じ尺度として扱わない。
iOSは44×44pt、Androidは48×48dpを一般的な開始点にできるが、対象versionのplatform guidelineと既存componentを確認する。

## Native semanticsを優先する

必要な意味と挙動を持つnative HTML elementまたはplatform componentがある場合は、それを使う。
`div`へroleを付ける方法は、button、link、input、dialog、tableなどで表せない場合に限る。

ARIAは不足するsemanticsを補う。
native semanticsと重複するrole、誤ったstate、focusableな`aria-hidden`要素を追加しない。

## Name、role、valueを確認する

- icon-only controlに動作を表すaccessible nameがある。
- visible labelとaccessible nameが一致する。
- toggle、tab、accordion、comboboxが現在のstateを伝える。
- validation errorが該当fieldと関連付く。
- loading、result count、非同期errorなど必要な更新だけをlive regionで伝える。

live regionを広いcontainerへ付けない。
更新のたびに大量の内容を読み上げると、必要な変化を見つけにくくなる。

## Keyboardとfocusを設計する

- DOM orderとvisual orderを一致させる。
- `Tab`でcomponent間を移動し、複合widget内は対応するarrow key patternを使う。
- `Enter`と`Space`の挙動をnative patternに合わせる。
- `Escape`はpopup、menu、dialogを閉じ、focusを起点へ戻す。
- modalは背景を操作対象から外し、focusを内部で管理する。
- focus indicatorを消さず、背景とcomponentの両方から識別できる見た目にする。
- sticky elementやoverlayがfocused componentを完全に隠さない。

custom widgetはWAI-ARIA Authoring Practicesのkeyboard interactionを確認する。

## Errorと復旧を設計する

errorは色だけで示さない。
field付近に問題、原因、修正方法を置き、form上部のsummaryから該当fieldへ移動できるようにする。

保存、送信、購入など結果が重要な操作では、処理中、成功、失敗、再試行可能性を区別する。
時間切れや通信失敗で入力を失わない。

## Motion、contrast mode、zoomへ対応する

`prefers-reduced-motion` では、意味を保ちながら移動量、parallax、zoom、反復を減らす。
すべてを0.01msへ一括変更すると、必要なstate transitionまで壊す場合があるため、componentごとに代替を定義する。

`forced-colors` とplatformのhigh contrast modeでは、色指定を解除してもboundary、focus、stateが残るか確認する。

## 人が操作して確認する

自動scanに加えて、主要flowをkeyboard、screen reader、200% zoom、reduced motionで確認する。
自動scanはtask理解、reading orderの自然さ、custom widgetの完全な操作契約を保証しない。

## 一次情報

- WCAG 2.2: https://www.w3.org/TR/WCAG22/
- Target Size Minimum: https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html
- Using ARIA: https://www.w3.org/TR/using-aria/
- ARIA Authoring Practices Guide: https://www.w3.org/WAI/ARIA/apg/
- Apple Accessibility: https://developer.apple.com/design/human-interface-guidelines/accessibility
- Android Accessibility: https://developer.android.com/design/ui/mobile/guides/foundations/accessibility
