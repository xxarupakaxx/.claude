# 構成の選び方

構成はthemeの飾りではなく、読者の問いに対応させる。

| 構成 | 読者の問い | HTMLの形 | 計画書での使い方 |
| --- | --- | --- | --- |
| long-document | なぜこの判断か | 55–72字の本文、inline見出し | 背景、根拠、限界 |
| step-sequence | 何をどの順で変えるか | 番号付きol/dl | Wave、entry/work/exit |
| split-diptych | 何がどう変わるか | 7/5または1/1比較grid | Before / After |
| map-diagram | どこが依存するか | inline SVGのnode/edge | 要求、モデル、出力、検証 |
| workbench | 実装の中身は何か | code、table、evidence rail | file/symbol、branch、失敗回復 |
| index-first | 何を読むべきか | anchor付き目次＋本文 | 複数sessionの迷子防止 |

今回の共通計画書では、index-firstを先頭、step-sequenceを実装章、split-diptychを比較章、map-diagramを依存章、long-document/workbenchを詳細章に組み合わせる。構成名をCSSの飾りとして宣言するだけにせず、対応するDOMを実際に描く。
