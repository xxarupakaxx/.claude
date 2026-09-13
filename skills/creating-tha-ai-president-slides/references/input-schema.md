# Input Schema

## Top level

```json
{
  "meta": {
    "title": "Deck title",
    "subject": "Deck subject",
    "author": "Author",
    "company": "Company",
    "label": "Footer label",
    "language": "ja-JP"
  },
  "theme": {
    "fontBody": "BIZ UDGothic",
    "fontDisplay": "Arial"
  },
  "sources": [
    {
      "id": "source-1",
      "kind": "web",
      "title": "出典名",
      "url": "https://example.com/",
      "accessed": "2026-07-25"
    }
  ],
  "slides": []
}
```

`theme` は省略できる。配色はブランド整合を守るためoverrideできない。
local-safe defaultは `BIZ UDGothic` / `Arial`。検証環境にfontがある場合は
`Noto Sans JP` / `Outfit` を指定する。

## 出典

- `sources[].id`: deck内で一意、40文字以内
- `kind`: `web`、`internal`、`fictional`
- `title`: 120文字以内
- `url`: webでは必須、internal/fictionalでは省略可
- `accessed`: 確認日。webでは `YYYY-MM-DD`
- `note`: 任意、160文字以内

事実、引用、数値を含むslideは `sourceIds` で出典を指定する。
generatorはspeaker notesへ出典情報を追記する。slide上の可読性を保ちつつ、
PPTX内で根拠を失わないための正規の保存場所はspeaker notesとする。

## 共通フィールド

すべてのslideは次を持てる。

```json
{
  "type": "cards",
  "kicker": "SECTION LABEL",
  "title": "ページタイトル",
  "speakerNotes": "発表者向けメモ",
  "sourceIds": ["source-1"]
}
```

- kicker 40文字以内
- 通常page title 44文字以内
- speakerNotes 600文字以内
- sourceIdsは重複なし

文字数は日本語・英数字を同じ1文字として数える。

## Layouts

### cover

```json
{
  "type": "cover",
  "eyebrow": "AI × MANAGEMENT",
  "titleLines": [
    {"text": "経営の知識を、"},
    {"text": "組織の力へ", "highlight": true}
  ],
  "subtitle": "補足説明",
  "date": "2026.07"
}
```

- `titleLines`: 2–3件、各24文字以内
- highlightは1件まで

### section

```json
{
  "type": "section",
  "number": "01",
  "title": "章タイトル",
  "subtitle": "章の問い"
}
```

- title 28文字以内
- subtitle 50文字以内

### stats

```json
{
  "type": "stats",
  "kicker": "WHY",
  "title": "選ばれる理由",
  "metrics": [{"value": "3×", "label": "指標"}],
  "reasons": [{"title": "理由", "body": "説明"}]
}
```

- metrics: 4件
- reasons: 3件
- metric value 14文字、label 28文字以内
- reason title 20文字、body 48文字以内

### issue-cards

```json
{
  "type": "issue-cards",
  "kicker": "ISSUES",
  "title": "見えている課題",
  "cards": [{"label": "分類", "value": "72%", "body": "説明"}],
  "takeaway": "最下部の結論"
}
```

- cards: 6件
- label 18文字、value 14文字以内
- body 42文字以内
- takeaway 42文字以内

### cards

```json
{
  "type": "cards",
  "kicker": "SCENES",
  "title": "6つの場面",
  "cards": [{"title": "カード名", "body": "説明"}]
}
```

- cards: 6件
- title 18文字、body 58文字以内

### comparison

```json
{
  "type": "comparison",
  "kicker": "BEFORE / AFTER",
  "title": "変化",
  "left": {"label": "BEFORE", "title": "以前", "points": ["項目"]},
  "right": {"label": "AFTER", "title": "以後", "points": ["項目"]},
  "takeaway": "変化の要約"
}
```

- points: 左右各3件
- label 16文字、title 24文字以内
- point 36文字以内
- takeaway 48文字以内

### case-study

```json
{
  "type": "case-study",
  "kicker": "CASE",
  "title": "導入事例",
  "context": {"title": "背景", "body": "説明"},
  "episode": {"title": "起きたこと", "body": "説明"},
  "outcomes": [{"value": "1/2", "label": "成果"}]
}
```

- outcomes: 3件
- context/episode title 24文字、body 110文字以内
- outcome value 16文字、label 28文字以内

### quotes

```json
{
  "type": "quotes",
  "kicker": "VOICES",
  "title": "利用者の声",
  "quotes": [{"quote": "引用", "name": "話者", "role": "役割"}],
  "takeaway": "共通する結論"
}
```

- quotes: 3件
- quote 100文字以内
- name 24文字、role 30文字以内
- takeaway 48文字以内

### layers

```json
{
  "type": "layers",
  "kicker": "LAYERS",
  "title": "5つの層",
  "layers": [{"label": "01", "title": "層名", "body": "説明"}]
}
```

- layers: 5件
- label 8文字、title 18文字、body 40文字以内

## Validation behavior

generatorは未知のlayout、項目数違反、文字数超過、必須値欠落を
エラーとして停止する。内容を黙って切り捨てない。
