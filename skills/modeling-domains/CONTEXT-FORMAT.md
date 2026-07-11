# `CONTEXT.md` の形式

## 構成

```md
# {コンテキスト名}

{この context が何で、なぜ存在するのかを 1〜2 文で書く。}

## 言語

**注文**:
{その用語を 1〜2 文で説明する}
_Avoid_: 購買、取引

**請求書**:
納品後に customer へ送る支払い依頼。
_Avoid_: bill、payment request

**顧客**:
注文を行う個人または組織。
_Avoid_: client、buyer、account
```

## ルール

- **意見を持って決める。**
  同じ概念を指す言葉が複数あるなら、最善の一語を選び、他は `_Avoid_` に並べます。
- **定義は短く保つ。**
  1〜2 文までに抑えます。
  その概念が *何であるか* を定義し、*何をするか* の説明には寄りません。
- **その project の context に固有の用語だけを入れる。**
  一般的な programming concept は入れません。
  timeout、error type、utility pattern のような語は、いくら多用していても対象外です。
  用語を追加する前に、それがこの context 固有の概念なのか、一般的な programming concept なのかを自問します。
  入れてよいのは前者だけです。
- **自然なまとまりが見えたら subheading で group 化する。**
  すべてが一つの cohesive な領域に属しているなら、flat list のままで構いません。

## 単一コンテキストのリポジトリと複数コンテキストのリポジトリ

**Single context（ほとんどの repo）** は、repo root に一つの `CONTEXT.md` を置きます。

**Multiple contexts** の場合は、repo root の `CONTEXT-MAP.md` に、各 context の場所と関係を列挙します。

```md
# コンテキストマップ

## コンテキスト一覧

- [受注](./src/ordering/CONTEXT.md) — customer の注文を受け付け、追跡する
- [請求](./src/billing/CONTEXT.md) — 請求書を生成し、支払いを処理する
- [出荷](./src/fulfillment/CONTEXT.md) — 倉庫での picking と shipping を管理する

## 関係

- **受注 → 出荷**: 受注は `OrderPlaced` event を出し、出荷はそれを受けて picking を開始する
- **出荷 → 請求**: 出荷は `ShipmentDispatched` event を出し、請求はそれを受けて invoice を生成する
- **受注 ↔ 請求**: `CustomerId` と `Money` は共有 type として使う
```

この skill は、どの構造が適用されるかを次のように判断します。

- `CONTEXT-MAP.md` があれば、それを読んで context を見つけます。
- root の `CONTEXT.md` しかなければ single context とみなします。
- どちらもなければ、最初の用語が解決した時点で root の `CONTEXT.md` を lazy に作ります。

複数 context がある場合は、現在の話題がどの context に属するかを推測します。
曖昧なら聞きます。
