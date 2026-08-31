# 操作状態

interactive elementごとに、発生する状態を意味ごとに設計する。標準の8状態に加え、選択を表すUIでは `selected` を独立して扱う。

| 状態 | 観測 | 設計 |
| --- | --- | --- |
| default | 待機 | 本来のborder、text、背景 |
| hover | pointerが乗る | 小さな色・rule変化。主要情報は増やさない |
| focus | keyboard/programmatic focus | focus-visibleを明確な輪郭で表示 |
| pressed | 押下中 | 位置または色をわずかに変える |
| selected | tab、radio、toggleなどが選択中 | pressedと混同せず、選択中であることを本文・属性・視覚で示す |
| disabled | 操作不可 | labelを読めるまま無効状態を示す |
| loading | 処理中 | labelを消さず、処理中と示す |
| error | 失敗 | 本文、状態属性、borderで原因を示す |
| success | 完了 | 完了内容を本文で伝える |

`selected` は `pressed` の別名ではない。primaryの情報設計、task flow、アクセシビリティ判断は `designing-ui-ux` が担当し、Hallmarkは選択状態の視覚表現と表示確認を補助する。

plan-documentでは、主本文を隠す操作を追加しない。anchorは目次と見出しidで移動し、keyboard focusが移動先で見えるようにする。button・linkのlabelは狭幅でも折返しで欠けない。

motionは短く控えめにし、reduced-motionではanimation・transition・smooth scrollを停止する。外部通信、storage、analytics、認証情報処理を操作状態へ混ぜない。
