# Style Guide

## デザインの核

青の信頼感、黄色の決断点、白の余白を使い、経営者が短時間で
「何が問題で、何を決めるか」を読める資料にする。

## Canvas

- Ratio: 16:9
- Size: 13.333 × 7.5 inch
- Safe margin: 左右 0.68 inch以上、上 0.42 inch以上
- 通常ページは白背景
- 章扉だけ濃青から明青へのgradientを許可

## Color tokens

| Token | Hex | 用途 |
|---|---|---|
| primary | `#1A5CF0` | 見出し、強調線、主要カード |
| deep | `#0053DA` | 章扉、濃い強調 |
| navy | `#1E2A44` | タイトル、重要本文 |
| highlight | `#FFE600` | 結論、決断点、短い強調 |
| cardTint | `#F4F8FF` | 薄青カード |
| border | `#DCE6FB` | カード境界 |
| body | `#46546E` | 本文 |
| muted | `#A7B0BE` | 補助情報 |
| white | `#FFFFFF` | 背景、反転文字 |

黄色は長文の背景に使わず、1ページにつき1つの短い結論へ使う。

## Typography

- 日本語見出し・本文の推奨: `Noto Sans JP`
- 英字label・数値の推奨: `Outfit`
- local-safe default: `BIZ UDGothic`, `Arial`
- fallback: `Hiragino Sans`, `YuGothic`, sans-serif
- page title: 28–34pt、bold
- section title: 30–38pt、bold
- body: 14–18pt
- label: 10–13pt、bold
- quote: 16–20pt

フォントが置換されても収まるよう、枠の高さと幅に10%以上の余裕を残す。
Noto Sans JPまたはOutfitが検証環境にない場合は、local-safe defaultで
生成・画像確認し、Google Slides上で推奨fontへ置換してもよい。

## Components

### Header

- 左上に小さな青いkicker
- その下にnavyのpage title
- 必要な場合だけ細い青線を置く

### Card

- 角丸 0.12–0.18 inch
- fillは白またはcardTint
- borderは1ptのborder color
- shadowは使わない
- 余白は0.22 inch以上

### Highlight

- yellow rectangleの上にnavyの太字
- 文章全体ではなく、結論の1行だけ

### Footer

- 左にdeck label
- 右に2桁page number
- muted color、9–10pt
- 表紙と章扉には付けない

## Layout mapping

| Layout | 用途 | 採用する規則 |
|---|---|---|
| cover | 表紙 | 大きな左寄せtitle、黄色の一行、白背景 |
| section | 章扉 | gradient、白文字、左寄せ |
| stats | Why/根拠 | 上段の数字カード、下段の理由 |
| issue-cards | 課題の可視化 | 2×3の数字カード、下部に結論 |
| cards | 要素・場面 | 2×3の均等カード |
| comparison | Before/After | 左をmuted、右をprimaryで強調 |
| case-study | 事例 | 文脈、episode、成果3カード |
| quotes | 声・証言 | 3枚の引用カード、下部に共通結論 |
| layers | 階層・変化 | 濃淡の青を積み上げた5層 |

## 禁止事項

- 元デッキの顧客情報、固有名詞、数値、引用の複製
- 3D、heavy shadow、glass effect、過剰なgradient
- 青、黄、白以外を主役にする
- 本文14pt未満
- 1枚に複数の結論を詰め込む
- rasterized text
