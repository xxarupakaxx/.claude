# UI/UX quality gates

## 証拠を先に選ぶ

コードの静的確認だけで判定できる項目と、実画面でしか判定できない項目を分ける。

| Evidence | 確認できること | 確認できないこと |
|---|---|---|
| source diff | semantics、token、state実装 | 視覚階層、overflow、知覚速度 |
| component test | state transition、event | 実際のlayoutとcontrast |
| screenshot | hierarchy、density、visual consistency | keyboard、focus order、dynamic flow |
| browser interaction | task flow、focus、responsive、motion | screen readerの読み上げ品質すべて |
| accessibility scan | 機械判定可能な違反 | task理解、copy、全ARIA挙動 |
| screen reader | name、role、value、reading order | 視覚品質 |

dev serverを起動できるUI変更では、source diffだけで完了判定しない。

## 主要タスクを検証する

各主要タスクについて、次を確認する。

1. 開始点が見つかる。
2. 現在地と対象が分かる。
3. 次のactionと結果を予測できる。
4. 処理中と完了を区別できる。
5. 入力ミスやsystem errorから復旧できる。
6. destructive actionを誤って確定しにくい。

findingは「見た目が悪い」で終えない。

```md
- Severity: critical / important / minor
- Evidence: <screen、state、viewport、操作>
- User impact: <理解、成功、誤操作、復旧への影響>
- Cause: <情報、content、component、token、implementation>
- Fix: <変更対象と期待する結果>
- Validation: <修正を確認する方法>
```

## 視覚品質を確認する

- 3秒見たとき、page purpose、primary information、primary actionが区別できる。
- ぼかして見ても、見出し、group、actionの階層が残る。
- 同じ意味の要素が、同じvisual treatmentを持つ。
- surface、border、shadow、radiusが階層を説明し、装飾の種類を増やすために使われていない。
- 実データの最小、最大、空、長文でも階層が崩れない。
- brand名を交換しても同じに見える場合、Briefに接続したsignatureを再検討する。

## Attention budgetを確認する

- 3秒見たとき、最初に見る場所が一つに定まる。
- 初期画面の主要surfaceとprimary actionが一つに絞られている。
- 常時表示componentごとに、固有の利用者の問いがある。
- 同じ状態をcard、badge、graph、summary、inspectorで重複表示していない。
- tabs、sidebar、stepper、breadcrumbが同じ移動軸で競合していない。
- 補助情報、provenance、全文、filter、設定が段階的に開示される。
- 情報量が多いとき、fontとtargetを縮めず、Focus、Context、Evidenceへ深さを分けている。
- 全体の順序、範囲、現在位置が主要タスクに必要なら、drawerを開かず把握できる。
- Overviewが詳細やactionを持ち、主要surfaceと競合していない。
- 企画書、設計書、判断、成果物が作業を規定する場合、Task一覧だけを全体像と呼んでいない。
- 文書とTaskの関係を、本文を開かず把握できる。

画面をぼかしたときに同じ強さの矩形が多数残る場合は、component数、surface階層、常時表示の必要性を再検討する。

## Responsiveを確認する

既定の証拠viewportは375px、768px、1440pxとする。
製品の利用環境やprojectのbreakpointが異なる場合は、そちらを優先する。

- 横overflowが意図したdata surface以外にない。
- 主要actionがviewport外やhover専用にならない。
- navigation、table、toolbar、dialogが優先度に応じてreflowする。
- 200% zoomとtext enlargementで重要情報やactionが失われない。
- keyboard focusがsticky header、footer、overlayに完全に隠れない。

## Accessibilityを確認する

- semanticsとaccessible nameを確認する。
- keyboardだけで主要flowを完了する。
- focus orderとvisible focusを確認する。
- text、non-text、stateのcontrastを確認する。
- errorを位置、原因、修正方法と関連付ける。
- 色、位置、icon、motionの一つだけに意味を依存させない。
- reduced motion、forced colors、高contrastを変更範囲に応じて確認する。

自動scanが0件でも合格とは限らない。
task理解、focus order、custom widget、dynamic announcementは人が操作して確認する。

## 判定する

次のいずれかが残る場合は完了扱いにしない。

- 主要タスクを完了できない、または誤操作で重大な損失が起きる。
- keyboardまたは支援技術で主要タスクへ到達できない。
- primary contentやactionが対象viewportで失われる。
- loading、error、emptyなど発生可能なcritical stateが未定義である。
- 初期画面に同格の主要surfaceまたはprimary actionが複数あり、開始点を決められない。

minorな視覚的好みは、Brief、design system、受入基準のいずれにも接続しない場合、必須修正にしない。
