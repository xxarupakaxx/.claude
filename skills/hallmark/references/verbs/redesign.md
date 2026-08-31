# redesign

同じ情報を、別の構造と視覚リズムで読めるようにする。visual / interaction layerを対象にし、既存のroute、logic、data、auth、form契約を保つ。

## 先に宣言すること

- 対象ファイルと変更しない境界。
- single-pageかmulti-pageか。
- 現行の構造fingerprintと、採用する構造・theme・type。
- Before / Afterで何を観測し、何を提案するか。
- 変更しないための検証と、失敗時の公開停止条件。

## 規則

- ファイル削除、route統合、global設定、package導入を既定にしない。
- 既存CSSのimportとtokenを不用意に置換しない。
- 文書の原文や添付資料は、明示的な逐語指定がない限り理解用のsourceとして扱う。
- full rebuildが指定された単一HTMLでも、視覚層に限定し、実装前後のhashと検証を記録する。
- 新しいthemeを選ぶときは、既存design systemとの整合を優先し、一つのthemeファイルだけを読む。

出力は実装前の案だけでなく、具体的なDOM、token、selector、state、responsive、検証の順序まで追える内容にする。
