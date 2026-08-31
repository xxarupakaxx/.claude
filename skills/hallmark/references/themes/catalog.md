# theme catalog

catalogでは目的・温度・文字・rule・構造だけを比較する。採用後は一つのtheme詳細だけを読む。tokenは既存systemへ写像し、値を無条件に上書きしない。

| theme | 向くbrief | 紙・文字・accent | 構成 |
| --- | --- | --- | --- |
| plain-editorial | 長文、調査、静かな計画 | 暖色paper、serif見出しはlocal/system、赤茶accent | long-document、index-first |
| cobalt | API、docs、技術資料 | cool paper、sans＋mono、青accent | workbench、split-diptych |
| grid | system、archive、依存関係 | near-white paper、太めsans、一本のsignal ink、hairline grid | map-diagram、index-first |
| lumen | apparatus、夜間の視覚研究 | dark paper、明暗差、控えめなemit accent | split-studio、long-document |
| brutal | 変更差分、警告、強い制約 | light paper、太いrule、単色accent | step-sequence、workbench |

## 選択ルール

1. 既存design systemと既存fontを第一候補にする。
2. briefの対象と読者に合う一つを選ぶ。
3. theme詳細を一つだけ読む。残りはcatalogの比較で止める。
4. 実装後に色・文字・構造が選択と一致するか確認する。
5. 人気サイトの見た目をコピーせず、主軸、余白、階層、状態だけを抽出する。
