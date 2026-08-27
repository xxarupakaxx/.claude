---
name: viewing-plans
description: 計画・ログ・ロードマップをHTMLビューアで表示するスキル。Roadmap適格性ゲートを通過したタスクでは、Phase 2完了後（30_plan.md作成後）にRoadmap Viewerを優先表示する。短い保守作業は05_log.mdだけで追跡する。「計画を見せて」「HTMLで確認」等の依頼にも対応。
allowed-tools: Read, mcp__workflow-html-app__view-plan, mcp__workflow-html-app__view-log, mcp__workflow-html-app__view-verification
---

# Viewing Plans (HTML Viewer版)

計画ファイル・ログ・レビュー結果をHTMLビューアに自動表示する。

Roadmap Viewer は `html-plan` route のcanonical outputとして、task directoryに揃っている記録からProject Map + Focusを生成する。
第一画面では、全体像、Current Task、唯一のprimary action、NextまたはBlocker、Evidenceをsource-backedに表示する。`graph-map.md` がある場合も補助のConcept Mapであり、Project Map + Focusの一次情報を置き換えない。
Markdown全文、手動ファイル読込、JSON操作、KPIカードは第一画面へ並べず、要約から正本を直接開けるようにする。
`--serve --watch` で起動すると、Codex app の横に置いたブラウザが自動更新される。
Plan Viewer / Log Viewer / Verification Viewer は個別本文を確認する補助画面であり、Roadmap適格taskでは所定の節目に自動表示する。

task memory directoryにCodemapがある場合は、`roadmap.html`のDetail drawerにあるImpactからCode Mapを開けるようにする。Roadmap generatorはCodemap checkerがfreshと判定したpayloadだけを埋め込む。Code Mapを別HTMLや常時toggleへ戻さず、Plan / Log / Verificationの個別本文は各MCP Viewerで開く。コード変更taskでは`context/codemap.md`のpreflightを先に成立させ、Roadmapの更新時刻をCodemap freshnessとして扱わない。

HTML route、lifecycle、static/browser gateは `context/html-artifact-contract.md` と `config/html-surfaces.json` を正本にする。`roadmap.html`は配布前にstatic gateと該当browser profileを通す対象であり、invalid renderで既存成果物を上書きしない。

## Roadmap適格性ゲート

Phase 0で、Roadmapを生成する前に表を上から順に評価し、最初に一致した結果へ分類する。判定結果は`05_log.md`へ`roadmap_route: <結果>：<理由>`を一行で記録する。

| 結果 | 条件 | 表示 |
|---|---|---|
| `explicit-roadmap` | ユーザーがRoadmapまたは計画書Viewを明示した | Roadmapを生成する |
| `roadmap` | 設計判断、複数案の比較、依存する複数Task、継続的な進捗共有、引き継ぎのいずれかが必要 | `30_plan.md`を作成してRoadmapを生成する |
| `log-only` | 手順と完了条件が既知で、一つの実行と検証で閉じ、設計判断と複数案比較がない | `05_log.md`だけで追跡し、`30_plan.md`と`roadmap.html`を作らない |

競合解消、失敗コマンドの単発再実行、形式修正、誤字修正、既知手順による設定同期は、`log-only`を既定とする。ファイル数だけを理由にRoadmapへ昇格させない。

ただし、競合が仕様や振る舞いの選択を含む場合、複数の解消案を比較する場合、解消後の作業が依存する複数Taskへ分かれる場合は`roadmap`へ昇格する。作業中にこの条件が判明した場合も、判定を`05_log.md`へ追記してから`30_plan.md`とRoadmapを作る。

このゲートは表示の要否だけを決める。Phase記録、検証、安全条件、承認、コード変更時のCodemap preflightは省略しない。

<!-- viewer-codemap-preflight:start -->
コード変更taskでは編集前に `scripts/generate-codemap.py check --root <workspace-root> --artifact-dir ${MEMORY_DIR}/memory/<task>` を実行する。freshでなければ `context/codemap.md` に従ってtask-localな`codemap.source.json`を更新し、refresh → checkを行う。`explicit-roadmap`または`roadmap`ならTask Workspaceを再生成して同じ`roadmap.html`を実際に開く。`log-only`ならCodemapのfreshness確認だけを行い、Roadmapは生成しない。
<!-- viewer-codemap-preflight:end -->

複数 task を横断して見る場合は Roadmap Task Hub を使う:

```bash
python3 scripts/generate-roadmap-view.py --hub --memory-root "$MEMORY_DIR/memory" --open
```

`--memory-root` は複数回指定できる。current thread ID を取得できた場合は `task-meta.json` の `thread_id` に保存し、完全一致だけを確定済み対応として扱う。path・title・更新時刻による一致は候補として表示するだけで自動確定せず、採用の承認は Codex 会話を正本とする。

Hub は loopback 上の OS 割当 port で起動し、URL fragment の session key でローカル API を保護する。Codex app-server と memory task を定期再取得し、provider の一時障害中は直近の成功結果を保持して degraded 状態を表示する。ブラウザ heartbeat が途絶えると Hub は終了する。

Hubの主表示は計画書ではなくLive Sessionとする。Codex app-serverが返すsession pathからJSONL末尾最大1MBだけを読み、直近24時間・最大100イベントへ制限する。turn状態、user待ち、未完了tool call、直近のsub-agent観測、最終イベント、経過時間、明示blockerを先に表示し、その下に設計Plan、承認、実装計画、成果物、検証結果を置く。command引数、tool出力全文、古い会話contextは表示用modelへ入れない。

## 自動発動条件

Roadmap適格性ゲートが`explicit-roadmap`または`roadmap`を返した場合だけ、以下のタイミングで**自動的に**発動する（ユーザー確認不要）：

1. **Phase 2完了時**: `${MEMORY_DIR}/memory/<task>/roadmap.html` を生成・表示し、`30_plan.md`を`mcp__workflow-html-app__view-plan`でPlan Viewerへ表示
2. **横で見たい場合**: `scripts/generate-roadmap-view.py ${MEMORY_DIR}/memory/<task> --serve --watch` を起動し、表示URLを案内
3. **Phase 3/4の節目**: `40_progress.md` / `80_review.md` / `05_log.md` 更新後、watch中ならブラウザが自動更新
4. **Phase 5完了時**: Roadmap Viewerで最終状態を表示し、`05_log.md`を`mcp__workflow-html-app__view-log`でLog Viewerへ表示
5. **コード変更task**: task memory directoryのCodemapをcheckし、freshならDetail drawerのImpact Code Mapで確認する。stale / insufficientならコード編集より先にrefreshする
6. **検証ガイドがある場合**: `90_verification.md`を`mcp__workflow-html-app__view-verification`でVerification Viewerへ表示する

Plan / Log / VerificationのMCP toolが利用できない場合は個別Viewerを表示済みと扱わず、runtime登録またはsession再起動が必要なblockerとして`05_log.md`と完了報告へ記録する。MCP Apps非対応hostではtext resultをfallbackとして扱い、HTML UI表示済みとは区別する。

## 手動トリガー

- 「計画をビューアで見たい」「HTMLで確認したい」
- 「ログをビューアで見たい」
- 「ロードマップを見たい」「roadmap.htmlを出して」
- `/viewing-plans` 実行時

## ワークフロー

最初にRoadmap適格性ゲートを実行する。`log-only`なら`05_log.md`へ判定を記録し、Phase 2でDelegation Decision保存後に`scripts/sync-roadmap.py`の検査・skip証跡を取得して、このスキルのRoadmap生成手順を終了する。

### 1. ファイル読み込み

```
対象ファイル:
  ├── ${MEMORY_DIR}/memory/<task>/00_spec.md → roadmap viewer
  ├── ${MEMORY_DIR}/memory/<task>/30_plan.md → plan viewer
  ├── ${MEMORY_DIR}/memory/<task>/40_progress.md → roadmap viewer
  ├── ${MEMORY_DIR}/memory/<task>/80_review.md → roadmap viewer
  ├── ${MEMORY_DIR}/memory/<task>/90_verification.md → roadmap viewer + verification viewer（任意）
  ├── ${MEMORY_DIR}/memory/<task>/team-journal.md → roadmap viewer（任意）
  └── ${MEMORY_DIR}/memory/<task>/05_log.md → log viewer
```

1. 対象メモリディレクトリを特定
2. `scripts/generate-roadmap-view.py <memory_dir>` を実行してProject Map + Focusの `roadmap.html` を生成
3. コード変更taskでは `scripts/generate-codemap.py check --root <workspace-root> --artifact-dir ${MEMORY_DIR}/memory/<task>` を実行し、Detail drawerのImpactで使う`codemap.json`からcaller / impact / guarding test / evidenceを確認
4. 必要に応じて Read ツールで個別Markdownコンテンツを取得

### 2. Roadmap Viewer生成

```bash
python3 scripts/generate-roadmap-view.py ${MEMORY_DIR}/memory/<task>
```

出力:

```
${MEMORY_DIR}/memory/<task>/roadmap.html
```

ユーザーには生成されたHTMLパスを案内する。
ブラウザで開けば、taskの全体像、Current Task、primary action、NextまたはBlocker、Evidenceを一画面で追える。関係を深掘りするときだけDetail drawerとConcept Mapを開く。

コード変更taskでは、CodemapをcheckしてからTask Workspaceを再生成し、同じ`roadmap.html`を実際にopenする。

```bash
python3 scripts/generate-codemap.py check \
  --root <workspace-root> \
  --artifact-dir ${MEMORY_DIR}/memory/<task>
python3 scripts/generate-roadmap-view.py ${MEMORY_DIR}/memory/<task>
open ${MEMORY_DIR}/memory/<task>/roadmap.html
```

Codemapがmissing / stale / mismatch / insufficientなら、`context/codemap.md` に従って同task memory directoryの`codemap.source.json`を更新し、refresh → checkを終えてからTask Workspaceを開く。パスだけを案内して完了しない。

ライブ更新:

```bash
python3 scripts/generate-roadmap-view.py ${MEMORY_DIR}/memory/<task> --serve --watch
```

`--serve` は既定で `127.0.0.1` にbindし、port `0` で空きポートを自動割当する。複数セッションで同時に使う場合は、各セッションの `${MEMORY_DIR}/memory/<task>` を分ける。固定portが必要な時だけ `--port <port>` を指定する。

<!-- roadmap-editorial-companion:start -->
### 2.5 補助説明図を選ぶ（条件付き）

`roadmap.html` を先に完成させる。

すべての実行で、Roadmap だけでは答えられない別の読者の問いが残るかを評価する。

責務、判断、リスク、引き継ぎなどを空間的なグループで短く説明できる場合だけ、`visualizing-work` を経て `diagram-design` を呼び、`92_visual_explanation.svg` と読解用の `92_visual_explanation.md` を作る。

別の canonical owner が `92_visual_explanation.*` を使用済みなら、`visualizing-work` の命名規則に従い、次に空いている番号の visual explanation path を使う。

静的 HTML が理解時間を短くする場合だけ、正本SVGをinlineで埋め込んだ、同じ番号の visual explanation HTML も作る。

補助図では Roadmap の task 順序、進捗、Concept Map を描き直さない。

不要なら visual explanation を作らず、判断理由を `05_log.md` に残す。
<!-- roadmap-editorial-companion:end -->

### 3. MCP Apps Plan / Log Viewer呼び出し

`mcp__workflow-html-app__view-plan` ツールを呼び出し:

```
引数:
  content: <読み込んだMarkdownコンテンツ>
```

ツールは自動的にHTML UIリソースを返し、クライアントがビューアを表示する。

Phase 5では同じ入力形式で`mcp__workflow-html-app__view-log`へ`05_log.md`本文を渡す。`90_verification.md`がある場合は`mcp__workflow-html-app__view-verification`へ渡す。Plan、Log、Verificationは別resource URIで開き、安全なMarkdown描画実装を共有する。

### 4. HTMLビューア表示

- Roadmap Viewer は生成済みHTMLをブラウザで開く
- MCP Apps が利用可能な場合は個別Plan/Log/Verification UIを開く
- ユーザーはインタラクティブに計画を閲覧・コメント追加可能
- コメントはMCP Apps protocol経由でhostへ送信される。非対応hostではtext fallbackを表示する

## 機能概要

### Task Workspace（Project Map + Focus）
- `00_spec.md` / `20_survey.md` / `30_plan.md` / `40_progress.md` / `checkpoint.md` / `80_review.md` / `90_verification.md` とfreshなCodemapだけをsourceにする
- 初期画面はProject Map、Current Task、primary action、NextまたはBlocker、Evidenceを同時に示す
- Project Mapは企画、設計、実装、検証をsource-backed nodeだけで表示し、Outcome Trace、実装根拠、明示Task参照、明示`blockedBy`以外からedgeを補作しない
- Currentはfreshなin-progress、なければ最初の未完了Taskとして一意に決める。選択操作でCurrentを変えない
- unresolved `blockedBy`があればBlockerを優先し、解除条件がなければ「Blocker未記録」と表示する
- primary actionは対象Taskの`実装`sectionにある最初の未完了checkboxだけを使う。欠落時は「未記録」と表示する
- Detail drawerはDocument、Change、Impact、Test、Sourcesを持つ。Code MapはImpactから開き、閉じたら起点へfocusを戻す
- blocked、stale、missing、completedは色だけでなく、文言、記号、線種、状態labelでも区別する
- `30_plan.md` の各Taskは `目的`、`変更対象`、`実装`、`成果物`、`検証`を持つ。欠落時はViewerが補作せず、`未記録`と表示する
- 任意の `実装図` に `diagram-json` を記録すると、planに明示されたnodeとedgeだけを自己完結inline SVGで表示する
- 任意の `実装根拠` に `repo:<relative-path>#<anchor-or-Lx-Ly>` を1件記録すると、generatorが生成時点の実sourceを最大12行だけ取得する。bare pathや `変更対象` からsource参照を推測しない
- source previewはcode/automation prefix allowlist内だけを対象とし、個人ノート領域、hidden state、secret file/content、`automation_read: false`、symlink、binary、非UTF-8、1MiB超のfileを拒否する
- source previewの色付けは自己完結lexerで行い、tokenごとにescapeしてからclassを付ける。未対応言語は色なしのescape済み本文へ戻し、コードを欠落させない
- 固定Phaseと固定Taskだけを算定可能な進捗として扱い、推測の百分率を表示しない
- task directory配下の通常ファイルを成果物metadataとして再帰収集する。symlinkは追跡せず、Viewer出力と一時ファイルは除外する
- 生成済みHTMLにsnapshotを埋め込むため、追加サーバーなしで `file://` 表示できる
- `--serve --watch` では `roadmap-snapshot.json` をpollingし、source内容または表示対象artifact metadataが変化したときだけ自動更新する
- 単一task表示では手動のMarkdown/JSON読込やJSON出力を提供しない
- Markdown全文は第一画面へ表示しない。source-boundの要約と正本への導線は隠さない

### Impact Code Map（taskコード地図）
- freshな`codemap.json` payloadを同じ`roadmap.html`のDetail drawer内Impactから開く
- lane別column、node filter、inspectorでcaller / impact / guarding testを1-hopずつ辿る
- verified relationは `path:line` evidenceを表示し、unknown relationは破線とreasonを併記する
- Project Map + Focusや `graph-map.md` routeを置き換えない
- desktopはgraph + inspector、狭幅はinspectorを下段、mobileはcolumn canvasをhorizontal scrollで保持する

### Plan Viewer（計画ビューア）
- Markdownレンダリング（見出し、リスト、コードブロック）
- DOMPurifyによるXSS対策
- コメント追加・対応hostへのフィードバック送信

### Log Viewer（ログビューア）
- `view-log`専用toolと`ui://log-viewer/` resourceでPlanとは別画面として開く
- 05_log.mdの見出しをoutlineへ表示し、チェック項目の進捗を集計する
- 安全なMarkdown描画、CSP、コメント送信経路はPlan Viewerと共有する

### Verification Viewer（検証ビューア）
- `view-verification`専用toolと`ui://verification-viewer/` resourceで開く
- 90_verification.mdのchecklistを表示し、検証結果の確認に使う
- Plan / Logと同じdocument bundleから生成されるaliasとして扱い、独立してhand-maintainしない

## セキュリティ

- **CSP**: self-contained HTML resourceとして外部loadを禁止する
- **Sanitization**: Markdown本文とuser contentをDOMへ入れる前にescape / sanitizeする
- **MCP Apps protocol**: 対応hostでは `text/html;profile=mcp-app` とstandard transportを使い、非対応hostではtext resultへ退化する

## 使用例

```
# 自動発動（Phase 2完了後）
1. Roadmap適格性ゲートが`explicit-roadmap`または`roadmap`を返す
2. Codexが30_plan.mdの作成を完了
3. `scripts/generate-roadmap-view.py <memory_dir>` を実行
4. `roadmap.html` のパスをユーザーに提示
5. mcp__workflow-html-app__view-plan に30_plan.md content を渡す
6. 90_verification.md があれば mcp__workflow-html-app__view-verification に渡す
```

```
# 手動トリガー
ユーザー: 計画をビューアで見たい
Codex:
1. メモリディレクトリを特定
2. Roadmap Viewerを生成
3. 個別に深掘りしたい場合は30_plan.md / 05_log.md / 90_verification.mdを既存viewerで表示
```

## 関連ドキュメント

- @context/workflow-rules.md（HTML Viewer Toolsセクション）
- @context/memory-file-formats.md
- @context/codemap.md
