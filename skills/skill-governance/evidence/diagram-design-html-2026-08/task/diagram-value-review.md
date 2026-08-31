# Diagram Design value review

## 評価範囲

候補 `/Users/yoshiki/.local/share/skill-governance/review/diagram-design-html-2026-08/diagram-design/codex` の `SKILL.md` と、各ケースに必要なJIT referenceだけを使って、6ケースを初回1回で判定した。ケースの根拠は `/Users/yoshiki/Notes/Vault/.local/memory/260831_html-runtime-adoption/diagram-value-cases.json` の各行である。モデル名はこの評価から確定できないため `unknown/inherited` と記録した。

候補の入口は、source-backedな関係を空間で読む必要がある場合に、selection → 図種reference → output contract / visual rules / quality gateへ進む構造を持つ。dependency、process、architectureではこの切り分けがそのままfixtureの問いに対応した。単純なBefore/Afterでは表へ戻り、UIの余白とRoadmap進捗は責務外として止まった。

候補の通常出力契約はHTMLとcanonical SVGの組み合わせだが、今回の明示されたwrite scopeはJSON、review Markdown、SVG、短い回答だけである。そのためHTMLは作らず、SVG生成経路のvalueだけを評価した。HTMLを作らなかったことを候補の完全な出力契約のPASSとは数えていない。

## ケース結果

| case | route | 結果 | 根拠 |
|---|---|---|---|
| dependency | fan-in / dependency | SVG生成 | 4接続、5 node。rendererのfan-inとsnapshotの共有先を保持 |
| process | stage / handoff → process | SVG生成 | 2 lane、4 node、3接続。失敗分岐を表示 |
| small_comparison | table | 図なし | 3列の表が最小で、空間配置の追加情報がない |
| spacing | 除外 | 図なし | UI/UXレイアウト調整であり、Diagram Designの対象外 |
| progress | 除外 | 図なし | Roadmapの進捗・完了状態はviewing-plans側の責務 |
| structure | secure route / boundary → architecture | SVG生成 | 3 component、2接続、browser/API間だけのtrust boundary。API内部はunknown |

各ケースのroute判断、理由、caseごとの読込file、回答、attempt数、出力先は `diagram-value-results.json` に保存した。各SVGの短い回答は `diagram-value-output/*.txt` に置いた。

## 生成物の確認

依存図は与えられた4本の矢印を保ち、nodeをrank 0/1/2へ配置してfan-in 0/2を表示した。処理図は利用者側とサービス側のlaneを分け、受付→検証、検証→保存、検証失敗→エラー表示の3接続だけを描いた。構造図はbrowser→API→保存層の2接続と、browser/API間のtrust boundaryを描き、API内部に子componentを補っていない。

候補のquality gateに沿って3 SVGをXML parseし、`viewBox`、`role="img"`、非空の`title`/`desc`、重複IDなし、source anchor、直交connector、禁止要素と外部loadの不在を確認した。connector数は依存4、処理3、構造2で、確認結果は `diagram-value-results.json` の `validation.svg_static_check` に保存した。

fixture以外の実装事実、効果、採用状態は図に加えていない。構造図のAPI内部は `unknown` と明記した。新規図はSVGだけで、MermaidやHTMLは作成していない。

## baselineの入口比較

baseline `/Users/yoshiki/.codex/skills/diagram-design/SKILL.md` は、`visualizing-work` がstatic editorial SVG sidecarを選び、reader・question・evidence・confidence・omitted scopeが既知で、spatial groupingが小さなcomparison、timeline、causal、ownership、concept viewの理解を助ける場合を入口とする。同文書は、dependencyのようなlayered technical map、process/canonical flow、Roadmap、canonical state、task order、progress、session selection、viewer integrationを入口で除外し、直接実行も許していない。

従ってbaselineについて文書から言える「可能」は、前提が満たされた小さなeditorial comparison等に限られる。今回のbaseline実行は行っておらず、成功率・未実行ケースの成功数は作っていない。candidateが今回直接扱えたdependency/process/architectureの3領域は、baselineでは専門ownerまたは除外境界へ戻る。

## 独立レビュー

候補の価値は、計画書の説明図に必要な4入口へ範囲を絞りつつ、表へ戻す条件、図種別の上限、source binding、unknownの扱いを同じ入口で揃えた点にある。fixtureの3つのpositive caseでは、追加事実を作らずに関係・lane・boundaryを可視化できた。2つのnegative caseでは、進捗やレイアウトへ責務を広げなかった。

残る制約は二つある。第一に、候補の通常契約が要求するHTMLの初期表示、text fallback、source listを今回のwrite scopeでは評価できない。第二に、今回のfixtureは小さく、読者の理解時間やcontext削減を測定していない。したがって、この結果はroute適合と静的SVG契約のvalue評価であり、実プロジェクトでの読解効果やHTMLブラウザ表示の証明ではない。

承認receipt、promotion、runtime変更、registry変更、candidate tree・sourceへの変更は作成していない。
