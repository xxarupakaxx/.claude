---
name: viewing-plans
description: 計画・ログ・Roadmapを通常のブラウザで確認する。Roadmap適格性に応じ、短い保守は05_log.mdだけで追跡する。
allowed-tools: Read
---

# Viewing Plans

このSkillは保存済み計画を安全に表示する補助である。`30_plan.html`が人とLLMの共有する計画の正本、`roadmap.html`と`roadmap-snapshot.json`は共通parser/generatorによる派生表示である。新しい計画で`30_plan.md`を作らない。本文をHTMLで直接管理し、派生表示のCSS/JavaScriptやJSONを手で補正しない。

本文、変更前後、実装内容、source根拠、検証、依存図を初期表示する。重要情報をdrawerやtabに隠さず、本文にない完了・担当・期限・因果を補わない。

## Routeと実行者

| route | 条件 | 成果物 |
|---|---|---|
| explicit-roadmap | 計画書またはRoadmap表示の明示要求 | 30_plan.html → sync → roadmap.html |
| roadmap | 設計判断、複数工程、依存、継続共有がある | 同上 |
| log-only | 既知手順を一回の実行・検証で閉じる | 05_log.mdのみ |

routeはfile数で選ばない。詳細はcontext/workflow-rules.mdを使う。このSkillの権限はReadだけであり、計画の保存・sync・ブラウザ起動は呼出元のleadが既存権限で行う。

<!-- viewer-codemap-preflight:start -->
コード変更では最初のedit前にCodemap preflightを実行する。missing / stale / mismatch / insufficientならcontext/codemap.mdに従ってrefreshする。log-onlyでもsource freshnessは確認する。
<!-- viewer-codemap-preflight:end -->

## Workflow

1. taskをsession/thread IDの完全一致で特定する。更新時刻や似たtitleだけで選ばない。
2. 共通source resolverで正本を選ぶ。HTMLがあれば唯一の入力とし、不正・symlink等を旧MDで隠さない。HTMLがない既存taskだけ30_plan.mdをlegacyとして読める。
3. 必要な計画本文・Task・根拠だけをtask-contextから読む。会話全文、HTMLの装飾・runtime code全文、不要なartifactをcontextへ投入しない。
4. Phase artifactとDelegation Decisionを保存して、trusted local executorから同期する。

    python3 ~/.codex/scripts/sync-roadmap.py TASK --workspace-root WORKSPACE --memory-root MEMORY/memory --run-id RUN --phase 2

phaseは2/3/4/5。同じtask/root/run-idを継続して使い、主経路失敗を旧generatorで隠さない。Claudeもこの共通CLIを使う。

5. 検査済みroadmap.htmlを通常ブラウザで一度開く。以後は同じfileを更新し、tabやViewerを自動追加しない。workflow-html-app MCPは使わない。

watchと複数taskのHubは横断確認を明示した場合だけ使う。ログと検証は同じページで確認し、必要な正本へのリンクを渡す。

## HTML正本の契約

具体的なHTML形式はcontext/memory-file-formats.mdと共通parserを参照する。背景・目的・到達点・全体の進め方を先に示し、Taskは成果物や判断のまとまりにする。fileごとの細分化をしない。

見える本文を正本とし、steps・status・blockedBy・acceptance・sourceを同じTaskへ結ぶ。同fileのJSONはUI preview/diagramの機械用情報に限定し、本文を重複させない。新HTMLの進捗はHTML自身が所有し、40_progress.mdで上書きしない。raw UTF-8 bytesからsource hashを計算する。

UI変更のBeforeは実sourceと40桁commit SHA、Afterは計画、unknownは未確認事項として分離する。ユーザーにmetadata入力を求めず、LLM自身が対象sourceから記録する。詳細は~/.codex/skills/viewing-plans/references/ui-change-preview.md。実コードは明示repo参照だけから取得し、変更対象名から推測しない。

Code Mapはfreshなcodemap.json / codemap.lockだけを本文で表示する。roadmapのmtimeでfreshnessを代用しない。invalid v2や不正なHTML本文をlegacy Task抽出で隠さない。旧MD-only taskと古いsnapshotの互換読込だけは残す。

## 表示完了の確認

表示の完了判定は次の層を分ける。

- **機械判定**: parser、schema、source hash、link、sync、static gateの結果。
- **内容確認**: 目的、Task、acceptance、依存、未完了、正本へ戻れる根拠を読める形で確認した結果。
- **利用可能性**: 生成されたHTMLのpath、ブラウザ起動、表示、リンク到達を実際に確認した結果。
- **確認導線**: 利用者が次に判断・操作する場所と、未確認事項。機械判定だけで理解済み・実行可能・完了とは扱わない。

HTMLの生成、ローカルでの表示、外部公開、TaskやIssueのCloseは別の状態である。表示しただけで公開・Close・ユーザー確認済みへ進めず、未確認のsourceやリンクは未確認として残す。既存承認の対象と影響を変えない表示確認に、段階ごとの一律な再承認を追加しない。公開、状態変更、対象拡大が必要な場合だけ、その具体的な操作を別の承認境界へ戻す。

## Security

source previewはallowlist内の相対pathに限定し、secret・個人ノート・symlink・binary・非UTF-8・過大fileを表示しない。HTML本文も未信頼データとして許可要素・属性だけを表示し、script、event handler、外部loadを拒否する。ローカルHTMLはMCP接続や親windowとの通信なしで開き、CSPで外部loadを禁止する。新しい図の正本はSVG。外部writeや追加権限をこのSkillでは承認しない。

関連: context/workflow-rules.md、context/memory-file-formats.md、context/codemap.md、context/html-artifact-contract.md、config/html-surfaces.json、~/.codex/skills/viewing-plans/references/ui-change-preview.md。
