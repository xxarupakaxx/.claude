# 避ける問題と修正

| 観測 | 問題 | 具体的な修正 |
| --- | --- | --- |
| h1と抽象的な説明が最初の画面を占有 | 何を見るべきか遅い | decision、現在地、次に読むanchorを先頭へ |
| すべてが同じカード | 情報の関係が見えない | 本文、表、縦stage、SVG、横比較に役割分担する |
| Before / Afterが縦並び | 変更の差が視線で比較できない | desktop二列・gap32px以上・padding24px以上、狭幅だけ縦積み |
| クリックしないと根拠が見えない | 初期表示で判断できない | 主要本文・根拠・限界・検証を常時表示 |
| 別画面の模型を実画面として提示 | 観測と案が混ざる | captionへ「模式図」「移行案・未実装」を明記 |
| 依存図の矢印が空白を指す | 図と本文の因果が不一致 | 入力→計画モデル→HTML→文書、出力→検証、失敗→公開停止へ整理 |
| 375pxでSVG labelが読めない | 情報を縮小しすぎ | mobile viewBoxを縦にし、同じ名称・固有idを保つ |
| 未実装が合格表示 | 完了状態を誤認 | 状態、根拠、未確認を別labelで出す |
| fake browser/IDE chrome、意味のないgradient | 実装理解を装飾へ置換 | 実際のDOM、token、diff、SVGを描く |
| external font/CDN/analytics | self-contained契約違反 | local/system font、inline SVG、外部load0 |
| hoverにのみ説明がある | keyboard・touchで欠落 | 本文・captionへ移す |
| 3列の均一feature card | 構造が汎用templateに見える | 主要内容を広く、補助内容を狭く、または本文へ戻す |
