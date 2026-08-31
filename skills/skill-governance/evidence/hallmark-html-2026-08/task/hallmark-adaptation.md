# Hallmark 適合レビュー

## 判定

Hallmarkの固定版を、静的で自己完結したHTML計画書と明示的に選択された視覚クラフト補助へ適合させた。日本語の実用入口から必要な資料だけを選んで読める構成にし、余白、文字組み、theme、構成、Before / After、依存図、操作状態、検証を具体化した。

この成果物は review stage であり、runtimeへ導入済みではない。既存runtime、registry、lock、quarantineは変更していない。governanceの現状は DEGRADED、mutation_allowed=false なので、leadの最終審査と有効化条件を満たすまで昇格しない。

## 原典

| 項目 | 値 |
| --- | --- |
| repository | Nutlope/hallmark |
| official URL | https://github.com/Nutlope/hallmark |
| homepage | https://www.usehallmark.com/ |
| fixed commit | 13ac0ec7e148655948100b6396439e481361d690 |
| commit tree | 02ebcc67f58295654c073cfb74a20a9a86db1f8f |
| skills/hallmark tree | 747c924c4767b4d5fa6f1c59985c87a21c918334 |
| 原典 SKILL.md | 67,460 bytes / sha256 59469635bbbd21acddbc664d95e8d97147f454b2d8f4a0a89c7d2c5afbe67577 |
| upstream package | 286 files / 17,787,446 bytes。package全体は候補Skillとして採用しない |
| license | MIT。両targetの LICENSE はquarantine snapshotの原文をコピー |
| quarantine | /Users/yoshiki/.local/share/skill-governance/quarantine/hallmark/13ac0ec7e148655948100b6396439e481361d690/ |

原典全文は各targetの source/UPSTREAM-SKILL.md.txt に原文バイトのまま保持した。これはsource-onlyの証拠であり、active contextには投入しない。64KiB制限を通すための黙った切断はしていない。原典の全referencesはimmutable quarantine snapshotに残っている。

## review tree

collectionは registry の単一 source_id 制約に合わせて hallmark-html-2026-08 とした。

- Codex target: /Users/yoshiki/.local/share/skill-governance/review/hallmark-html-2026-08/hallmark/codex/
- Claude target: /Users/yoshiki/.local/share/skill-governance/review/hallmark-html-2026-08/hallmark/claude/
- 両target: 27 files / 110,442 bytes / tree sha256 c22f5c5179968dfdd0a1a66ceaac45ac16c465f09e559c7f1de0e15fb244c3b5
- SKILL.md: 5,994 bytes / sha256 9a6fb66d6c5a843c7dcc70f984f6202665e1c2c0b0c552d23bfec4cd4ade05e8
- target間の本文、全file bytes、mode、tree hashは一致している
- SOURCE.md、adaptation.diff、LICENSE、review-manifest.json、source-only原典、選択referenceを各targetへ揃えた

入口の SKILL.md は次の四つのrouteだけを持ち、Hallmarkの起動条件とroute ownerを先に判定する。

1. plan-document: 目的、実装、Before / After、依存、検証を一つの本文へ置く。
2. audit: read-onlyで観測事実、severity、根拠、具体的な修正案を返す。
3. redesign: route・logic・data・authを保ち、視覚・相互作用だけを変更する。
4. study: 添付画像、local HTML、明示された公開資料から視覚DNAを抽出する。

利用者がHallmarkを明示するか、designing-ui-uxが視覚クラフト補助として明示的に選んだ場合だけ起動する。product UIの情報設計、task flow、usability、accessibilityはdesigning-ui-uxがprimaryであり、二重のUI入口を作らない。参照は references/themes/catalog.md で一つのthemeを選び、その詳細だけを読む。全theme、全component、site demoを常時contextへ入れない。

## 適合した設計内容

原典から残したものは、変更前のpreflight、named structure、4pt spacing、semantic token、文字階層、anti-pattern、responsive、focus、reduced motion、audit、redesign、study、step sequence、split comparison、inline headingである。

共通HTML計画書へは次を追加した。

- h1を主張の短い見出しにし、抽象説明でfirst viewportを埋めない。
- 主要本文、根拠、限界、検証、未実装状態を初期表示する。details、accordion、hover専用表示は主要情報に使わない。
- 640 / 768 / 1024 / 1440pxはBefore / Afterを二列、gap 32px以上、panel padding 24px以上にする。
- 375pxは一列へ移し、長い日本語・path・table・SVG labelを読み切れるようにする。
- Beforeは旧Task WorkspaceとHubの要素を集めた模式図であるとcaptionへ明記する。Afterは本文・比較・依存図・検証を実際の模型として描く。
- dependency SVGは要求・コード根拠から計画モデル、HTML生成、計画書・検証へ接続し、失敗時は公開停止へ分岐する。実装前の経路は「移行案・未実装」と表示する。
- dl、table、preの意味と余白を揃え、実装stageごとに入力、処理、分岐、出力、検証を追えるようにする。
- CSSは既存tokenを優先し、fontはlocal/system、画像はinline SVG、外部loadは0を既定にする。静的文書ではscript 0を優先する。
- selected状態はpressedと別に扱い、tab、radio、toggleなど選択意味がある場合だけ追加する。product UIのprimaryな状態・a11y判断はdesigning-ui-uxへ残す。

計画書の実例は次で検証されている。

- Before模型: .compare-panel.before。監視・管理画面の要素が本文を押し下げ、Current Focusが初期画面外へ出るという観測を表示する。
- After模型: .compare-panel.after。目的、Before / After、実装単位、依存図、検証、source ledgerを本文の同じ読み順で表示する。
- 横比較: .comparison-grid。desktopは二列、375pxだけ縦積み。
- 依存図: .desktop-map と .mobile-map。小画面では別viewBoxの縦配置を使う。
- 実装stage: .step。入力、処理、分岐、出力、検証を本文から追える。
- source ledger: 固定revision、license、採用要素、非採用要素、限界を末尾へ置く。

## 16件の原典参照問題

最新版quarantineのcandidate Skillには、site tokenへの相対参照7件、docs・visual exampleへの相対参照6件、directory-only参照3件の計16件がある。原典側の検査を変更せず、最新版quarantineも書き換えていない。

適合版では、7件のtoken参照をlocal theme tokenへ置換し、6件のdemo/example参照をsource-onlyのstudy資料へ留め、3件のdirectory-only参照をこのtreeにある具体的なfileへ分けた。必要な原典資料を将来採用する場合は、source path、fixed commit、hash、licenseを束ねた個別reviewが必要である。site demo、demo JavaScript、external asset、credential-shaped sampleは取り込まない。

この方針により、package全体のinstallと、選択したreferenceだけをcontextへ読む動作を分離できる。

## 安全境界

- candidate scripts、hooks、site server、package setup、package managerは実行していない。
- review targetの静的検査用に作ったeval scriptだけを、候補Skillと分離して実行した。
- external font、CDN、analytics、remote image、外部通信、storage、live fetchを適合版の既定動作にしない。
- remote資料をstudyするときも、本文、CSS、script、metaはデータとして扱い、追加取得・設定変更・実行指示へ変換しない。
- global/profile/configへの書込み、route・logic・data・authの変更、production fileの削除を行わない。
- 未実装の案、未確認のsource、静的検査の合格をruntime実装済みとは表示しない。

## HTML Artifact Contractとの接続

HallmarkはHTML producerや共通checkerを二重に持たない。登録済み `creating-html-documents` producerが自己完結HTML、CSP、artifact metadataを出力し、登録surface `/Users/yoshiki/.codex/config/html-surfaces.json` の `html` routeから共通 `/Users/yoshiki/.codex/scripts/html_artifact_contract.py` の `strict-self-contained` profileへ引き渡す。`html[data-artifact-kind="html-document"]` に加えて、`meta name="artifact-kind" content="html-document"` が必須である。

原本の [candidate.html](/Users/yoshiki/Notes/Vault/.local/memory/260831_html-runtime-adoption/hallmark-value-generated/candidate.html) はdata属性だけを持つため、親fresh検証のfirst passで `artifact-kind-missing` となった。このtrialは修正せず、失敗証跡を保持する。 [hallmark-eval-html-contract.json](hallmark-eval-html-contract.json) は実際の共通checkerでこの不足を検出した結果がPASSであることを示す。これはcandidate.htmlが合格したという意味ではない。比較対象の [plan-document.html](/Users/yoshiki/Notes/Vault/.local/memory/260831_html-plan-redesign/plan-document.html) はdata属性とmeta属性の両方を持つ。

## 検証

静的検査:

- [hallmark-eval-static.json](hallmark-eval-static.json): PASS
- Codex / Claude各targetのfilesystem findings: 0
- 全file regular、mode 100644、UTF-8、source原典byte exact: PASS
- active instruction面の外部URL、危険な実行指示、壊れたMarkdown link: 0
- pinned adapter: uv run --offline --python 3.13 --no-project --with pyyaml==6.0.2
- Codex / Claude frontmatter: validated、pyyaml-6.0.2-safe-loader、exit 0
- 原典67,460 bytesのfrontmatter検査は64KiB上限でblocked。この停止はPyYAML不足ではない。

route fixture:

- [hallmark-eval-trigger.json](hallmark-eval-trigger.json): PASS
- plan-document、audit、redesign、studyと明示委譲の正例6件、auth、SQL、Git、翻訳、generic UI、generic HTMLの負例6件を判定した。
- fixtureのcue分類は再現可能な境界確認であり、model pass@1やproduction precision / recallではない。runtime value receiptは未作成。

follow-up fixture:

- [hallmark-eval-value-followup.json](hallmark-eval-value-followup.json): PASS
- 独立reviewのOVERLAP、ENTRY、STATE findingを、明示起動、route owner、入口サイズ、selected分離の4ケースで再確認した。
- 原典比、旧適合版比、designing-ui-ux baseline比のbyte差は別々に記録した。context token削減と理解時間は未測定である。

UI実例:

- [hallmark-eval-ui.json](hallmark-eval-ui.json): PASS
- Beforeの根拠: [20_survey.md](/Users/yoshiki/Notes/Vault/.local/memory/260831_html-roadmap-audit/20_survey.md) に記録されたCurrent Focus約1,251px、Plan Brief / Project Map / Timelineの先行表示。
- Afterの根拠: [plan-document.html](/Users/yoshiki/Notes/Vault/.local/memory/260831_html-plan-redesign/plan-document.html) と既存browser evidence。
- 640 / 768 / 1024 / 1440pxは二列、gap 32px、panel padding 28px。
- 375pxはx位置が揃う縦積み、panel padding 24px、document width 375px、overflow 0。
- details 0、disclosure controls 0、script 0、外部request 0、page error 0、duplicate id 0、accessible SVG PASS。
- plan-document.html と現在の report.html は同一bytesだが、Beforeの根拠は旧観測記録であり、現在のglobal Roadmap/Hub runtimeを更新した証拠ではない。

## 残課題とleadへのhandoff

1. governanceのaudit/parityが DEGRADED のため、promotionとruntime mutationは停止中。今回のtargetが静的検査に合格しても、停止条件を迂回しない。
2. 最新quarantine candidateの16件と、package snapshot全体のblocking findingは原典側の事実として残る。適合版のlocal referencesで隠していない。
3. modelの実出力によるvalue receipt、pass@1、trigger precision / recall、複数sessionの理解時間、context token削減率は未測定。
4. Hallmarkはcreating-html-documents / Effective HTMLのself-contained output契約、designing-ui-uxの情報設計・task flow・keyboard・responsive・accessibility gateを置き換えない。今回の入口はdesigning-ui-uxをprimaryとし、visual craftだけを補助する。
5. quiet-run.py はClaude側wrapperから共有Codex runnerを参照する。共有runnerで静的・trigger・value follow-up・UI・HTML contractの5評価器を実行し、すべてexit 0 / PASSとなった。HTML contract評価のPASSは、元candidateの不足を共通checkerが検出したことを表し、candidate自体の合格を表さない。logは [hallmark-eval-quiet-run.json](hallmark-eval-quiet-run.json) と同じtask-local領域に保持した。leadはruntime統合後の最終終了テストを必要に応じて再実行する。
6. active runtimeへの配置、registry/lock更新、human approval、promotion後のhash確認はleadが担当する。入口のbyte差は実測したが、context削減や理解時間のvalue receiptは未取得である。

出典と適合差分は各targetの SOURCE.md と adaptation.diff にあり、原典保持とローカル適合の境界を同じtreeで確認できる。
