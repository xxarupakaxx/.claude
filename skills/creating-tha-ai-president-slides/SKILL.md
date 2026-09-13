---
name: creating-tha-ai-president-slides
description: >
  THA「AI社長」資料の青・黄・白を基調とした視覚文法で、JSONから
  16:9の編集可能PPTXを生成する。AI社長テンプレート、THAらしい提案資料、
  青いグラデーションの章扉、課題カード、Before/After、事例、引用、
  階層図を使ったGoogle Slides向け資料を作りたいときに使用する。
---

# Creating THA AI President Slides

## 目的

元デッキの内容を複製せず、再利用可能なデザイン規則だけを使って、
Google Slidesへの取り込みを想定した編集可能PPTXを生成する。

## 先に読むもの

1. `references/style-guide.md`
2. `references/input-schema.md`
3. デザイン根拠の確認が必要な場合だけ `references/source-manifest.md`

以下の例では、この `SKILL.md` があるdirectoryのabsolute pathを
`SKILL_DIR` として設定する。generatorへ渡した相対pathは実行時の
current directoryから解決されるため、input/outputはabsolute pathで渡す。

## ワークフロー

### 1. 内容を設計する

- 読み手、目的、1枚ごとの主張を決める。
- 1枚1メッセージにする。
- 事実、引用、数値には出典を付け、`sources` と各slideの `sourceIds` で
  speaker notesへ残す。
- 元デッキの顧客名、数値、文章、事例をコピーしない。
- 外部事実が必要なら、生成前に一次情報を調査する。

### 2. JSONを作る

`examples/sample-deck.json` を複製し、`references/input-schema.md` に従って
内容を置き換える。利用できるlayoutは次のとおり。

- `cover`
- `section`
- `stats`
- `issue-cards`
- `cards`
- `comparison`
- `case-study`
- `quotes`
- `layers`

収まりを守るため、指定された項目数と文字数上限を超えない。

### 3. PPTXを生成する

PptxGenJS `4.0.1` を使う。Codex Desktopではworkspace dependenciesを読み、
返されたNodeとnode_modulesを使う。

```bash
SKILL_DIR="<absolute-path-to-creating-tha-ai-president-slides>"
NODE_PATH="<workspace-node-modules>" "<workspace-node>" \
  "$SKILL_DIR/scripts/generate-tha-deck.cjs" \
  --input "$SKILL_DIR/examples/sample-deck.json" \
  --output /absolute/path/to/output.pptx
```

通常のNode環境では、`pptxgenjs@4.0.1` を利用可能にして次を実行する。

```bash
SKILL_DIR="<absolute-path-to-creating-tha-ai-president-slides>"
node "$SKILL_DIR/scripts/generate-tha-deck.cjs" \
  --input /absolute/path/to/deck.json \
  --output /absolute/path/to/output.pptx
```

generatorは呼出元directoryから明示したinput/outputを解決する。
PptxGenJSを解決できない場合は、代替versionで続けず、案内付きで停止する。

### 4. 検証する

必要なtoolchainは Python 3 + Pillow、LibreOffice、Poppler
（`pdftotext`, `pdftoppm`）、`unzip`、`xmllint`、`grep`。次の2コマンドで
再圧縮と検証artifact生成を行う。

```bash
python3 "$SKILL_DIR/scripts/rezip-pptx.py" /absolute/path/to/output.pptx
bash "$SKILL_DIR/scripts/validate-tha-deck.sh" \
  /absolute/path/to/output.pptx \
  /absolute/path/to/validation-output
```

指定したvalidation outputの下に、実行ごとに `validation.XXXXXX` という
重複しないrun directoryが作られる。そこへ `extracted-text.txt`、PDF、
全ページPNG、`overview.png`、`validation-summary.txt` が生成される。
実際のrun directoryはコマンド終了時にも表示される。overviewと各ページを
目視し、overflow、切断、重なり、低コントラストがあればJSONまたはgeneratorを
修正して、もう一度2コマンドを実行する。

Google Slidesへの実インポートは外部書き込みになる。ユーザーの明示承認が
ある場合だけ行い、ローカル検証と混同しない。

## 出力原則

- テキスト、カード、線、図はPowerPointネイティブ要素で作る。
- SVGは章扉のgradient背景だけに使う。
- 画像生成AIは、ユーザーが明示的に求めた場合だけ使う。
- footerは通常ページに付け、表紙と章扉では省略する。
- フォント置換が起こり得るため、文字枠には10%以上の余裕を持たせる。

## 完了条件

- PPTXとPDFが開ける。
- 抽出テキストに主要本文が残る。
- 事実、引用、数値のsourceがspeaker notesに残る。
- 全スライドを画像で確認している。
- placeholderと意図しないsource内容がない。
- `.codex` / `.claude` の両方を更新する作業では、対応ファイルが一致する。
