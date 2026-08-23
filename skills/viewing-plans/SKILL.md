---
name: viewing-plans
description: 計画・ログ・ロードマップをHTMLビューアで自動表示するスキル。Phase 2完了後（30_plan.md作成後）はRoadmap Viewerを優先表示し、実装中は更新されたroadmap.htmlで現在地を見せ、Phase 5完了後は05_log.mdをlog_viewerで確認する。「計画を見せて」「HTMLで確認」等の依頼にも対応。
allowed-tools: Read, mcp__workflow-html-app__view-plan
---

# Viewing Plans (HTML Viewer版)

計画ファイル・ログ・レビュー結果をHTMLビューアに自動表示する。

Roadmap Viewer は、task directory に揃っている記録から、実行計画のbriefと補助のConcept Mapを生成する。
第一画面はbrief-firstとし、`実施Task`、`仕様`、`実装根拠`、`実行順序`、`事実・判断・未確定`、`成果物`を同じ読み順で表示する。`graph-map.md` のConcept Mapは折りたたみ可能な補助表示へ置き、第一画面の一次情報を置き換えない。
Markdown全文、手動ファイル読込、JSON操作、KPIカードは第一画面へ並べず、要約から正本を直接開けるようにする。
`--serve --watch` で起動すると、Codex app の横に置いたブラウザが自動更新される。
Plan Viewer / Log Viewer は、明示的に文書本文を確認するときだけ使う。

task memory directoryにCodemapがある場合は、`roadmap.html`のTask WorkspaceへCode Map viewとして統合する。Roadmap generatorはCodemap checkerがfreshと判定したpayloadだけを埋め込む。表示入口は一つだが、コード変更taskでは`context/codemap.md`のpreflightを先に成立させ、Roadmapの更新時刻をCodemap freshnessとして扱わない。

<!-- viewer-codemap-preflight:start -->
コード変更taskでは編集前に `scripts/generate-codemap.py check --root <workspace-root> --artifact-dir ${MEMORY_DIR}/memory/<task>` を実行する。freshならTask Workspaceを再生成して同じ`roadmap.html`を実際に開く。freshでなければ `context/codemap.md` に従ってtask-localな`codemap.source.json`を更新し、refresh → check の後に開く。
<!-- viewer-codemap-preflight:end -->

複数 task を横断して見る場合は Roadmap Task Hub を使う:

```bash
python3 scripts/generate-roadmap-view.py --hub --memory-root "$MEMORY_DIR/memory" --open
```

`--memory-root` は複数回指定できる。current thread ID を取得できた場合は `task-meta.json` の `thread_id` に保存し、完全一致だけを確定済み対応として扱う。path・title・更新時刻による一致は候補として表示するだけで自動確定せず、採用の承認は Codex 会話を正本とする。

Hub は loopback 上の OS 割当 port で起動し、URL fragment の session key でローカル API を保護する。Codex app-server と memory task を定期再取得し、provider の一時障害中は直近の成功結果を保持して degraded 状態を表示する。ブラウザ heartbeat が途絶えると Hub は終了する。

Hubの主表示は計画書ではなくLive Sessionとする。Codex app-serverが返すsession pathからJSONL末尾最大1MBだけを読み、直近24時間・最大100イベントへ制限する。turn状態、user待ち、未完了tool call、直近のsub-agent観測、最終イベント、経過時間、明示blockerを先に表示し、その下に設計Plan、承認、実装計画、成果物、検証結果を置く。command引数、tool出力全文、古い会話contextは表示用modelへ入れない。

## 自動発動条件

以下のタイミングで**自動的に**発動（ユーザー確認不要）：

1. **Phase 2完了時**: `${MEMORY_DIR}/memory/<task>/roadmap.html` を生成し、Roadmap Viewerで表示
2. **横で見たい場合**: `scripts/generate-roadmap-view.py ${MEMORY_DIR}/memory/<task> --serve --watch` を起動し、表示URLを案内
3. **Phase 3/4の節目**: `40_progress.md` / `80_review.md` / `05_log.md` 更新後、watch中ならブラウザが自動更新
4. **Phase 5完了時**: Roadmap Viewerで最終状態を表示し、必要に応じて05_log.mdをlog_viewerで表示
5. **コード変更task**: task memory directoryのCodemapをcheckし、freshならTask WorkspaceのCode Map viewで確認する。stale / insufficientならコード編集より先にrefreshする

## 手動トリガー

- 「計画をビューアで見たい」「HTMLで確認したい」
- 「ログをタイムラインで見たい」
- 「ロードマップを見たい」「roadmap.htmlを出して」
- `/viewing-plans` 実行時

## ワークフロー

### 1. ファイル読み込み

```
対象ファイル:
  ├── ${MEMORY_DIR}/memory/<task>/00_spec.md → roadmap viewer
  ├── ${MEMORY_DIR}/memory/<task>/30_plan.md → plan viewer
  ├── ${MEMORY_DIR}/memory/<task>/40_progress.md → roadmap viewer
  ├── ${MEMORY_DIR}/memory/<task>/80_review.md → roadmap viewer
  ├── ${MEMORY_DIR}/memory/<task>/90_verification.md → roadmap viewer（任意）
  ├── ${MEMORY_DIR}/memory/<task>/team-journal.md → roadmap viewer（任意）
  └── ${MEMORY_DIR}/memory/<task>/05_log.md → log viewer
```

1. 対象メモリディレクトリを特定
2. `scripts/generate-roadmap-view.py <memory_dir>` を実行して `roadmap.html` を生成
3. コード変更taskでは `scripts/generate-codemap.py check --root <workspace-root> --artifact-dir ${MEMORY_DIR}/memory/<task>` を実行し、同task directoryの`codemap.json`からcaller / impact / guarding test / evidenceを確認
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
ブラウザで開けば、taskの目的、仕様、実コード上の変更対象、実行順序、確認済み事項、成果物を一つのbriefとして追える。関係を深掘りするときだけConcept Mapを開く。

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

### 3. MCP Apps view-plan 呼び出し（詳細確認用）

`mcp__workflow-html-app__view-plan` ツールを呼び出し:

```
引数:
  content: <読み込んだMarkdownコンテンツ>
```

ツールは自動的にHTML UIリソースを返し、クライアントがビューアを表示する。

### 4. HTMLビューア表示

- Roadmap Viewer は生成済みHTMLをブラウザで開く
- MCP Apps が利用可能な場合は個別Plan/Log UIを開く
- ユーザーはインタラクティブに計画を閲覧・コメント追加可能
- コメントはpostMessage経由でClaude Codeに送信される

## 機能概要

### Task Workspace（Roadmap / Code Map）
- `00_spec.md` / `30_plan.md` / `40_progress.md` / `80_review.md` を第一画面の正本とし、task、spec、approach、flow、claims、artifactsをbriefへ割り当てる
- 上段は `Phase / 進捗 / 選択中Task` のcompact status barとし、Task選択に同期させる。固定の全体目的をheroとして重複表示せず、全体仕様は仕様cardと `00_spec.md` quick linkから読む
- `現在` と `次` を明示する。次のTaskがなければ、計画完了か未記録かを区別して表示する
- `00_spec.md` と `30_plan.md` のquick linkを初期viewportに置き、成果物linkからsource drawerで正本本文を開けるようにする
- `graph-map.md` があれば `diagram-json` を補助のConcept Mapとして読み、HTMLではSVGとして描画する。なければ既存sourceからfallback graphを作る
- `30_plan.md` の各Taskは `目的`、`変更対象`、`実装`、`成果物`、`検証`を持つ。欠落時はViewerが補作せず、`未記録`と表示する
- 任意の `実装図` に `diagram-json` を記録すると、選択Task detailの `こう実装する` と `現在の実コード` の間へinline SVGで表示する。対応するのは矩形、判断node、明示的な有向edge、edge labelの限定構文だけとする
- 任意の `実装根拠` に `repo:<relative-path>#<anchor-or-Lx-Ly>` を1件記録すると、generatorが生成時点の実sourceを最大12行だけ取得する。bare pathや `変更対象` からsource参照を推測しない
- 第一画面は全Taskのcompact indexと選択Task detailを同時に表示する。全Taskには短い実装方針、選択Taskには `こう実装する`、任意の `実装図`、色付きの `現在の実コード`、変更対象、成果物、検証を表示する
- Tablet / MobileではTask indexを順序どおりのhorizontal railにし、その直後へ選択Task detailを置く。tablistのorientationと矢印keyも表示方向へ合わせる
- `こう実装する` は `30_plan.md` の計画、`現在の実コード` はgeneratorが解決した事実として区別する。存在しないafter codeを生成しない
- `実装図` はplanに明示されたnodeとedgeだけを表示し、実装手順、変更対象、実コードから関係を推測しない。図と同じ関係をテキスト一覧でも読めるようにする
- source previewの色付けは自己完結lexerで行い、tokenごとにescapeしてからclassを付ける。未対応言語は色なしのescape済み本文へ戻し、コードを欠落させない
- source previewはcode/automation prefix allowlist内だけを対象とし、個人ノート領域、hidden state、secret file/content、`automation_read: false`、symlink、binary、非UTF-8、1MiB超のfileを拒否する。追加prefixは `--source-allow-prefix` で明示する
- `事実・判断・未確定`は明示見出しだけから読む。source priorityは次の通り
  - 事実: `40_progress.md` の実測・検証結果 → `20_survey.md` の現在の事実・確認済み事実 → `00_spec.md` の現在の事実
  - 判断: `team-journal.md` のDecisions・判断 → `30_plan.md` の採用判断・実装方針・Final implementation supersession → `00_spec.md` の採用判断
  - 未確定: `team-journal.md` のOpen Questions → `30_plan.md` の未確定・リスク → `20_survey.md` の仮説・未確定 → `00_spec.md` の未確定
- 同じbucketの項目はsource priority順に統合し、正規化後に完全一致する項目だけを重複排除する。分類を推測しない
- 明示graphは型付きnodeとpredicate edgeで構成し、`node → 関係語 → node` が単独で意味を持つようにする
- node表面は短い名詞句に限定し、要求文、ファイルパス、Markdown本文は選択後の詳細へ移す
- Desktop / Tablet / Mobileのすべてでnodeとedgeを保持する。Mobileはselected pathのpredicateだけを優先表示し、線を消してカード一覧へ戻さない
- 明示graphがないfallbackでは、Goalを起点にOutcome、Task、Artifact / Evidenceの確実な関係だけを配置する
- Outcome は本文を並べず、人が識別できる短い意味ラベルへ変換する。原文は選択時の詳細に残す
- Outcome を省略しない。Desktop は横方向の成果マップ、Mobile は全ノードを保った縦方向のツリーへ変換する
- 明示された Outcome Trace の Task 参照と evidence file、Task の `blockedBy` だけを edge にする
- 推測した関連や fallback edge を表示しない
- node 選択時は要点と1-hopの関連ノードだけを Inspector に表示する。「上流」「下流」を連結した長文として表示しない
- Goal 選択時はマップ自体が詳細を担うため、重複する Inspector を表示しない
- Arrow、Home、End、Enter、Escape で node を移動できる
- 固定Phaseと固定Taskだけを算定可能な進捗として扱い、推測の百分率を表示しない
- task directory配下の通常ファイルを成果物metadataとして再帰収集する。symlinkは追跡せず、Viewer出力と一時ファイルは除外する
- 生成済みHTMLにsnapshotを埋め込むため、追加サーバーなしで `file://` 表示できる
- `--serve --watch` では `roadmap-snapshot.json` をpollingし、source内容または表示対象artifact metadataが変化したときだけ自動更新する
- 単一 task 表示では手動のMarkdown/JSON読込やJSON出力を提供しない
- Markdown全文は第一画面へ表示しない。source-boundの要約と正本への導線は隠さない

### Code Map view（taskコード地図）
- freshな`codemap.json` payloadを同じ`roadmap.html`の専用modeで表示する
- lane別column、node filter、right inspectorでcaller / impact / guarding testを1-hopずつ辿る
- verified relationは `path:line` evidenceを表示し、unknown relationは破線とreasonを併記する
- Plan viewのbrief-first contractや `graph-map.md` routeを置き換えない
- desktopはgraph + right inspector、狭幅はinspectorを下段、mobileはcolumn canvasをhorizontal scrollで保持する

### Plan Viewer（計画ビューア）
- Markdownレンダリング（見出し、リスト、コードブロック）
- DOMPurifyによるXSS対策
- コメント追加・Claude Codeへのフィードバック送信

### Log Viewer（ログビューア）※予定
- Phase自動検出・タイムライン表示
- サマリー統計（完了Phase数、所要時間等）

## セキュリティ

- **DOMPurify**: HTMLサニタイズでXSS防止
- **CSP**: Content Security Policyヘッダー
- **オリジン検証**: 信頼済みオリジンのみpostMessage許可

## 使用例

```
# 自動発動（Phase 2完了後）
1. Claude Codeが30_plan.mdの作成を完了
2. `scripts/generate-roadmap-view.py <memory_dir>` を実行
3. `roadmap.html` のパスをユーザーに提示
4. 必要に応じて mcp__workflow-html-app__view-plan に30_plan.md content を渡す
```

```
# 手動トリガー
ユーザー: 計画をビューアで見たい
Claude Code:
1. メモリディレクトリを特定
2. Roadmap Viewerを生成
3. 個別に深掘りしたい場合は30_plan.md / 05_log.mdを既存viewerで表示
```

## 関連ドキュメント

- @context/workflow-rules.md（HTML Viewer Toolsセクション）
- @context/memory-file-formats.md
- @context/codemap.md
