---
name: designing-ui-ux
description: |
  利用者の主要タスク、情報構造、状態、視覚システムを一つの設計へまとめ、Web・モバイル・デスクトップのUIを設計、実装、監査する。
  「UIを作って」「画面をリデザインして」「もっと洗練して」「UXを改善して」「ダッシュボードを設計して」「アクセシビリティやレスポンシブを直して」など、UI source（.tsx、.jsx、.html、.vue、.svelte、.swift等）、styles、design tokens、prototypeを扱う依頼で使用する。
  新規画面、既存UIの改善、デザイン監査、デザインシステム策定に対応し、専門デザインSkillと実画面の品質確認を必要な範囲だけ組み合わせる。
---

# UI/UXを設計する

UIを、利用者が目的を達成するための操作系として設計する。
視覚的な個性は、主要タスク、情報、状態、ブランドの判断を固定した後に与える。

## 既存workflowとの関係

- Phase 0-5.5、承認、記録、レビュー、commitとpushは `@context/workflow-rules.md` に従う。
- このSkillはUI/UXの設計規律を追加する。write scopeや外部操作の権限は広げない。
- 既存のdesign system、component library、brand guideline、platform conventionを、このSkillの既定値より優先する。
- 既存UIの改善では機能範囲を拡張しない。確認済みの課題と受入基準だけを対象にする。

## 最初に依頼を分類する

| Mode | 依頼 | 完了条件 |
|---|---|---|
| `advise` | UX相談、方向性、比較 | 根拠、推奨案、リスク、次の判断を提示 |
| `audit` | 既存画面の評価 | 証拠付きfindingと優先順位を提示。依頼がなければ変更しない |
| `design` | 新規画面、flow、design system | design briefと実装可能な仕様を作成 |
| `implement` | UI作成、改善、リデザイン | 実装し、実画面または代替証拠で検証 |

監査依頼を実装依頼へ読み替えない。
実装依頼では、設計だけで終了しない。

## Design routeを選ぶ

依頼の目的を「誰の、どの仕事を、どの条件で成功させるか」の一文にする。
次に主レンズを1つ、補助レンズを最大2つ選び、選んだSkillだけを全文読む。

| 必要な判断 | Skill |
|---|---|
| UI全体のクラフト、状態、知覚品質 | `../emil-design-eng/SKILL.md` |
| gesture、drag、sheet、連続操作、interrupt可能なtransition | `../apple-design/SKILL.md` |
| 動きを加える候補の探索 | `../find-animation-opportunities/SKILL.md` |
| 既存motionの監査 | `../improve-animations/SKILL.md` |
| 実装済みmotionの最終確認 | `../review-animations/SKILL.md` |
| motion用語の回答 | `../animation-vocabulary/SKILL.md` |

一般的な新規UIと洗練依頼では `emil-design-eng` を主レンズにする。
motionに関係しない依頼ではApple系とanimation系Skillを起動しない。

記録形式は次のとおり。

```md
Design route:
- Primary: <skill>
- Supporting: <skill or none>
- Mode: advise / audit / design / implement
- Why: <今回必要な判断>
```

競合は `project ruleとplatform semantics > accessibility > ユーザー要件 > 既存挙動とdesign system > design brief > 専門Skillのheuristics` の順で解決する。

## 設計を進める

### 1. 現状を観察する

新規UIでは、利用者、主要タスク、利用状況、成功、失敗コスト、必要な情報を確認する。
既存UIでは、画面、主要経路、実データの形、design tokens、component、breakpoint、既知の問題を先に読む。
実画面を起動できる場合は、コードだけで外観を推測しない。

不足情報が結果を大きく変えないなら仮定を明示して進める。
主要タスク、対象platform、ブランド制約のいずれかが不明で、選択により成果物が別物になる場合だけ確認する。
未確認のplatform仕様、component API、適合基準を推測で補わない。
一次情報を確認できなければ、安全な共通原則へ範囲を狭め、未確認事項を明示する。

### 2. Design briefを固定する

`references/design-brief.md` を読み、次を短く記録する。

- primary userとjob
- successとfailure
- primary pathとcritical edge cases
- information priority
- emotional quality
- existing constraints
- signatureとanti-signature

style名、色、fontを先に決めない。

### 3. Task flowと状態を設計する

happy pathだけでなく、empty、loading、partial、error、permission、offline、long content、destructive action、successを必要な範囲で定義する。
各画面について、利用者が「現在地」「可能な操作」「結果」「復旧方法」を理解できるか確認する。

不可逆操作は、警告の強さを操作の損失と復旧可能性に合わせる。
入力エラーは問題の位置、原因、直し方を同じ場所で伝える。

### 4. 情報とcontentを設計する

主要タスクに必要な情報を上位へ置き、補助情報は段階的に開示する。
画面の階層は、size、weight、contrast、space、positionの組合せで作る。
色だけ、iconだけ、hoverだけで意味を伝えない。

ラベルは利用者の語彙で書く。
CTAは動作と結果を表し、曖昧な「続ける」「OK」を避ける。

#### 情報量とcomponent数を制限する

情報を整理するためにcomponentを増やし続けない。
初期画面では、利用者が最初に答える問いを一つに決め、その問いへ関係しない情報を閉じる。

既定の構成は次の範囲に収める。

- 常時表示する主要surfaceは一つ。
- orientationは一つのcompact barへまとめる。
- primary actionは一つ。secondary actionは二つまで。
- 補助情報、provenance、filter、全文、設定は選択時のdrawer、popover、detailsへ送る。
- 同じ状態をcard、badge、graph、summaryで重複表示しない。
- 同じ軸のnavigationに、tabs、sidebar、stepper、breadcrumbを重ねない。

componentを追加する前に「このcomponentだけが答える利用者の問い」を一文で書く。
既存componentと同じ問いへ答えるなら、追加せず統合する。

情報量が多い画面は、重要情報を小さくするのではなく、表示の深さを分ける。

1. **Focus**：今判断する対象とprimary action。
2. **Context**：判断に必要な差、制約、状態。
3. **Evidence**：根拠、履歴、全文。要求されたときだけ開く。

熟練者向け画面でも、情報密度と同時表示量を混同しない。
高密度とは、必要な情報へ短く到達できることであり、すべてを常時表示することではない。

### 5. Visual directionを比較して収束させる

既存design systemが方向性を決めていない場合だけ、briefを満たす異なる2案を作る。
各案について、layout logic、type、color、depth、shape、motion、signature、riskを比較し、一案へ収束する。

流行のstyle catalogは候補探索にだけ使う。
業界名や「高級」「モダン」だけを根拠にpaletteやfontを決めない。

### 6. Design system contractを作る

実装前に次を固定する。

- semantic colorsとcontrast
- type rolesとnumeric treatment
- spacing rhythmとlayout constraints
- radius、border、surface、elevation
- component anatomyとstate matrix
- motion purposeとreduced-motion behavior
- responsive transformation
- icon、illustration、chartの規則

具体的な判断は、必要な参照文書だけを読む。

### 7. 実装する

既存componentとtokenを再利用し、意味のない新variantを増やさない。
native semanticsとplatform componentを優先する。
custom controlは、必要な意味や挙動を既存要素で表せず、keyboard、focus、screen reader、pointerの契約を実装、検証できる場合だけ作る。

視覚変更と同時に、loading、empty、error、disabled、focus、selected、pressedを実装する。
interactionを伴う装飾は、操作可能に見えるなら実際に操作可能にする。

## 品質ゲート

`references/quality-gates.md` を読み、変更リスクに合う証拠を集める。

1. **Task**：主要タスクを開始、理解、完了、復旧できる。
2. **Structure**：階層、現在地、主要action、状態が一目で区別できる。
3. **System**：token、component、content、motionが一貫する。
4. **Accessibility**：WCAG 2.2 AA、keyboard、focus、semantics、contrast、zoom、reduced motionを確認する。
5. **Responsive**：contentが縮小されるだけでなく、優先度に応じてreflowする。
6. **Evidence**：可能なら実ブラウザで主要flowと375、768、1440pxを確認する。

materialなUI変更は `ui-ux-reviewer` と `a11y-reviewer` の対象になる。
project ruleが専門Agentレビューを明示時だけに制限する場合は、freshな直接検証を優先する。
motion差分がある場合だけ `review-animations` を追加する。

## 失敗を避ける

- style名、palette、component libraryから設計を始める
- 機能をcardへ均等に並べて情報設計を済ませる
- placeholder copy、似た長さの架空データ、happy pathだけで完成扱いにする
- generic gradient、glass、bento、巨大heroを文脈なしで選ぶ
- contrast不足をfont weight、shadow、brand colorで正当化する
- desktopを縮めただけのmobile layoutを作る
- animationで遅さや状態不明を隠す
- screenshotの美しさをtask successの代替にする
- brand名を交換しても成立する画面を、署名のあるデザインとみなす
- 情報を失いたくないという理由で、card、panel、badge、tabを初期画面へ足し続ける
- 同じ事実をsummary、route、status card、inspectorで重複表示する

## デザインメモリ

projectに `.interface-design/system.md` があれば、確立済みのDirection、Tokens、Patterns、Decisionsを読む。
なければmaterialな設計判断が確定した後に作成を提案する。
現在の仕様はprojectのdesign systemを正本とし、このSkillへ個別projectの値を埋め込まない。

## 必要時に読む参照

| 判断 | 参照 |
|---|---|
| brief、flow、state、情報優先度 | `references/design-brief.md` |
| color | `references/color-palettes.md` |
| typography | `references/typography-detail.md` |
| layout、density、surface | `references/craft-principles.md`、`references/style-catalog.md` |
| component、form、navigation、chart | `references/components.md` |
| responsive | `references/responsive.md` |
| motion | `references/animation.md` |
| accessibility | `references/accessibility.md` |
| 検証とfinding | `references/quality-gates.md` |
| 外部知見と採用境界 | `references/provenance.md` |

参照は今回の判断に必要なものだけ読む。
参照文書から別の参照文書へ連鎖させない。
