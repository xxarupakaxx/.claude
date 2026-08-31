# 視覚設計の契約

## 目的

Hallmarkは、HTMLの見た目と相互作用を改善する。読み手が目的、変更理由、実装の形、根拠、限界を追える状態を出力する。

## 境界

- visual / interaction layerだけを扱う。
- route、business rule、data、auth、状態管理、権限、台帳、運用設定を変更しない。
- 既存global stylesheetはimportと既存tokenを保つ。追加は既存規約の下へ置く。
- 明示された単一HTMLの全体再構築は許可できるが、対象pathと保持境界を出力へ書く。
- 内容のない数値、コピー、出典、実績を作らない。

## self-contained output

- CSSは同じHTMLまたは既存プロジェクトの正規stylesheetへ置く。
- fontはlocal/systemを使う。
- 画像はinline SVG、data URI、または指定されたlocal assetだけを使う。
- 外部font、CDN、analytics、remote image、外部runtime、外部通信を既定にしない。
- static文書のscriptは0を優先する。必要な場合も、anchor移動・表示状態など範囲を明示した小さな処理だけにする。
- 単一HTMLはCSPを持つ。既定例は "default-src 'none'; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'" とし、実際の出力契約に合わせて検証する。
- HTMLからbrowser起動、redirect、shell、profile書込みを行わない。

## 既存画面の変更

まず変更前を読み、視覚差分とロジック差分を分ける。既存の情報・route・操作契約を保ったまま、selector、token、layout、focus、responsiveを変更する。削除や大規模route変更は別の明示範囲として扱う。

## 計画書の扱い

計画書の本文、Before / After、inline SVG、source ledgerは最初から表示する。details、accordion、hover専用表示は主要情報に使わない。未実装の案は必ず「移行案」「未実装」と付け、検証合格と混同させない。
