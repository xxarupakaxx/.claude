---
name: viewing-plans
description: 計画・ログ・Roadmapを通常のブラウザで確認する。Roadmap適格性に応じ、短い保守は05_log.mdだけで追跡する。
allowed-tools: Read
---

# Viewing Plans

このSkillは、保存済みの計画を安全に表示する補助である。新しい計画の正本は、head・style・bodyを備えた完成済みの`30_plan.html`である。`roadmap.html`はそのDOMとCSSを保ったまま同期した表示で、末尾に機械用の不活性な`embedded-snapshot`を持つ。`roadmap-snapshot.json`はTaskを索引する機械用viewであり、本文の章立てや表示内容を作り直す入力ではない。

新しい計画は、なぜ行うか、到達点、実装するコードと構造、根拠、検証を目に見える本文へ書く。Taskは成果物や判断のまとまりで置き、本文にない担当・期限・完了・因果を表示側で補わない。計画のsource生成、UI mock、architecture図の作成はauthoring中に終え、ブラウザはsourceや図を生成しない。

## Route

| route | 条件 | 成果物 |
|---|---|---|
| `explicit-roadmap` | 計画書またはRoadmap表示を明示された | `30_plan.html` → sync → `roadmap.html` |
| `roadmap` | 設計判断、複数工程、依存、継続共有または引継ぎがある | 同上 |
| `log-only` | 既知手順を一回の実行・検証で閉じる | `05_log.md`のみ |

routeはfile数で選ばない。詳細は`context/workflow-rules.md`を使う。このSkillの権限はReadだけであり、保存・sync・ブラウザ起動は呼出元のleadが既存権限で行う。

## Authoringと同期

1. taskをsession/thread IDの完全一致で特定する。更新時刻や似たtitleだけで選ばない。
2. HTMLがある場合は唯一の入力とし、不正なHTMLを旧MDで隠さない。既存taskでHTMLがない場合だけ`30_plan.md`をlegacy入力として読める。
3. `30_plan.html`の本文に背景・目的・outcome、変更対象、実装コードとarchitecture/data flow、成果物、evidence、verificationを置く。Taskの進捗・依存・acceptance・source根拠も同じ本文へ結ぶ。
4. UI変更は`ui-change-preview.md`に従い、確認済みsourceに基づく実DOM mockをTask内へ置く。architecture図は明示した`diagramData`を`plan_architecture.py`へ渡し、authoring中に対応するfigureへ検証済みSVGを書き込む。`--check`は現在のfragmentとSVGをread-onlyで確認する。
5. `~/.claude/scripts/sync-roadmap.py`を同じTASK、workspace root、run-idで実行する。syncは完成済みHTMLとarchitecture図を検証してから、HTMLをDOM/CSSごとコピーする。snapshotはTask索引を保存するだけである。
6. 検査済みの`roadmap.html`を通常ブラウザで一度開く。以後は同じfileを更新し、tabやViewerを自動追加しない。

新しい`30_plan.html`をブラウザやgeneratorがTask cardへ再構成してはならない。生成された`embedded-snapshot`は表示の正本ではなく、source hash・Task・検証結果を同期する不活性JSONである。

## UI変更とarchitecture

計画本文のUI/UXは[creating-html-documents](../creating-html-documents/SKILL.md)のeditorialな文書設計と、同Skillが指定するテンプレートを参考にしてよい。結論と現在地を冒頭へ置き、関係が複数にまたがる場合は短いorientationと既存のArchify overviewから、実UI比較・コード・検証根拠へ進める。本文を主役にし、余白・見出し・罫線で階層を作る。system font、15–17pxの本文、1.75–1.95の行間、控えめなaccent、必要な場合だけ250–310pxの補助railを起点にする。本文をKPI card群へ分解せず、重要情報をrailや折り畳みに隔離しない。

取り入れるのは計画書の読みやすさと情報の順序である。比較対象のBeforeまでreferenceの配色へ着せ替えず、対象componentのDOM・styleと固定source根拠を維持する。別の完成HTMLや第二のviewerは作らず、構成図は検証済みArchify SVGを同じ正本へ置く。`html-plan`の既存static / browser gateを、reference Skillのdesktop-only既定で緩和しない。

UI変更のBefore / Afterは同じTask内の実際のHTML mockを表示する。UI mockはLLM自身が対象sourceを読んでauthoringし、ユーザーへmetadata入力を求めない。Beforeは40桁commit SHAで確認したcomponent、直接import、局所styleを根拠にし、Afterは計画に書いた未実装案だけを表す。Before/Afterのcaption、anchor、unknownの扱いは[UI Change Preview Runbook](references/ui-change-preview.md)へ集約する。sourceを確認できない箇所は補作せず、未確認理由を残す。

計画のarchitecture図はTask順や旧Codemapから自動生成しない。実際のcomponentとdata flowを表す明示fragmentだけをArchifyへ渡す。入力、固定runtime、cache、失敗時の表示は[Archify overview contract](references/archify-overview.md)に従う。旧`codemap.*`は履歴互換用であり、新しい計画の入力・preflight・図には使わない。

## 実装へ渡す前の確認

表示成功は実装開始条件を満たした意味ではない。[計画から実装への判断契約](../../context/plan-execution-contract.md)の本文fieldと独立審査を用意し、task-context.pyの`--execution`で確認する。未審査でもPhase 2で表示して計画をレビューできる。

## 表示完了の確認

- **機械判定**: parser、schema、raw source hash、UI anchor、architecture `--check`、sync、static gate。
- **内容確認**: why、outcome、実装コード、根拠、検証、未確認事項を本文で読めること。
- **利用可能性**: 生成されたHTMLのpath、ブラウザ起動、表示、source/図へのリンク到達。
- **確認導線**: 次に判断・操作する場所と残るunknown。

HTML生成、ローカル表示、外部公開、TaskやIssueのCloseは別の状態である。表示しただけで公開・Close・ユーザー確認済みへ進めない。

## Security

planのsource previewはallowlist内の相対pathに限定し、secret・個人ノート・symlink・binary・非UTF-8・過大fileを表示しない。本文のHTMLは許可されたsemantic要素・属性だけを使い、scriptの実行、event handler、外部load、外部resourceを許可しない。UI mockのstyleはhead内に置き、確認できたcomponentと直接importのstyleから再現する。実行時data、未知のpixel値、外部URLは推測しない。

ローカルHTMLはMCP接続や親windowとの通信なしで開く。新しい図の正本はSVGである。外部writeや追加権限をこのSkillで承認しない。

関連: `context/workflow-rules.md`、`context/memory-file-formats.md`、`context/html-artifact-contract.md`、`config/html-surfaces.json`、`references/ui-change-preview.md`、`references/archify-overview.md`。
