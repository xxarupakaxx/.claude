---
name: viewing-plans
description: 計画・ログ・Roadmapを既存HTMLと補助Viewerで確認する。Roadmap適格性に応じ、短い保守は05_log.mdだけで追跡する。
allowed-tools: Read, mcp__workflow-html-app__view-plan, mcp__workflow-html-app__view-log, mcp__workflow-html-app__view-verification
---

# Viewing Plans

このSkillは計画を作るSkillではなく、保存済みartifactを安全に表示する補助である。roadmap.htmlは人向けの既定入口、30_plan.mdは人とLLMが読む正本、roadmap-snapshot.jsonは既存parserから作る派生viewである。LLMにHTML全文を書かせず、JSONやHTMLを手で補正しない。

RoadmapのProject Map + Focusは全体像、Current Task、primary action、NextまたはBlocker、Evidenceをsource-backedに表示する。Detail drawerはDocument、Change、Impact、Test、Sourcesを持ち、ImpactからCode Mapを開く。正本へ戻れない関係、本文にない完了・担当・期限・因果を表示側で補作しない。

## Roadmap適格性ゲート

Phase 0で表を上から順に評価し、最初に一致した結果を05_log.mdへ roadmap_route: <結果>：<理由> の形で記録する。

| route | 条件 | 動作 |
|---|---|---|
| `explicit-roadmap` | ユーザーがRoadmapまたは計画書Viewを明示 | 30_plan.md、sync、roadmap.htmlを作り表示 |
| `roadmap` | 設計判断、複数案、依存する複数Task、継続共有、引継ぎがある | 30_plan.md、sync、roadmap.htmlを作り表示 |
| `log-only` | 手順と完了条件が既知で一回の実行・検証に閉じる | 05_log.mdだけ。30_plan.mdとroadmap.htmlを作らない |

競合解消、単発再実行、形式修正、誤字修正、設定同期はlog-onlyを既定とする。ファイル数だけを理由にRoadmapへ昇格させない。仕様や振る舞いの選択、複数の解消案、依存する複数Taskが現れた場合はroadmapへ昇格する。ゲートは表示の要否だけを決め、Phase記録、検証、安全条件、承認、コード変更時のCodemap preflightは省略しない。

<!-- viewer-codemap-preflight:start -->
コード変更では、最初のedit前にCodemap preflightを実行する。missing / stale / mismatch / insufficientなら context/codemap.md に従いtask-local artifactをrefreshしてから編集する。log-onlyでもfreshnessだけは確認し、Roadmapを生成しない。
<!-- viewer-codemap-preflight:end -->

## Workflow

1. MEMORY_DIR/memory/<task>を、session IDまたはthread IDの完全一致で特定する。最新時刻だけでtaskを選ばない。
2. routeに応じて、00_spec.md、20_survey.md、30_plan.md、40_progress.md、80_review.md、90_verification.md、05_log.mdを読む。不要なfileを生成して読み込み量を増やさない。
3. roadmap / explicit-roadmapでは、Phase 2 artifactとDelegation Decisionを保存した後、trusted local executorでsyncする。Phase 3/4/5も同じ入口を使う。ログ専用ではsyncの検査・skip結果だけを記録する。
4. syncが検査・生成・atomic publishしたroadmap.htmlの返却pathを、成功後に利用者の入口として開く。invalid renderで既存HTMLを上書きしない。別generatorを二重起動しない。
5. 必要なときだけPlan / Log / VerificationのMCP Viewerを使う。MCP unavailableやtext fallbackをHTML UI表示済みと扱わず、05_log.mdへ記録する。

Syncの共通形は次のとおりである。

    python3 ~/.codex/scripts/sync-roadmap.py TASK --workspace-root WORKSPACE --memory-root MEMORY/memory --run-id RUN --phase 2

phaseは2、3、4、5のいずれかで、--dry-runはread-onlyである。主経路のsyncが失敗したとき、旧generatorや別CLIへ黙ってfallbackしない。Claudeは ~/.codex/scripts/sync-roadmap.py を明示入口として使い、詳細はClaudeのcommands/lfg.mdを参照する。

## Roadmap data contract

30_plan.mdの各Taskは、仕様、目的、変更対象、実装根拠、実装、成果物、検証、acceptance ID、blockedBy、write scopeを持つ。実装根拠の書式は repo:<relative-path>#<anchor-or-Lx-Ly> とし、生成時点の実sourceを最大限必要な範囲だけ取得する。bare pathや `変更対象` からsource参照を推測しない。

Plan解釈は scripts/roadmap_plan_contract.py に一本化する。schemaVersion 2のtasks / edges / progress / diagnostics / source lineと、05_log.md等から明示されたtimelineを別々に表示する。v2が存在するのに壊れているsnapshotはlegacy表示で隠さず、errorまたは同期停止にする。v1 fallbackはplanを持たない古いsnapshotだけに限る。

各Taskの `実装` を計画、生成元から解決したsource抜粋を生成時点の実sourceとして表示する。実装図がある場合は、planに明示されたnodeとedgeだけをinline SVGで描く。図の正本はSVGで、MarkdownへMermaidを生成しない。UI変更Taskは `UI変更: yes` と `ui-preview-json` 1ブロックを同じTaskへ置き、Before（固定source）・After（計画案）・uncertaintyを分離する。詳細schemaとpreview authoringは `~/.codex/skills/viewing-plans/references/ui-change-preview.md` と context/memory-file-formats.md を参照する。

UI変更Taskでは、計画を作るLLM自身が対象sourceを確認し、計画開始時点の `HEAD` を40桁commit SHAへ固定してBefore / Afterを記録する。ユーザーへmetadata入力やfile importを求めない。sourceを確認できないBeforeは補作せず `unverified` とし、previewを作れない計画は同期を通さない。

Code Mapはfreshなcodemap.json / codemap.lockだけをDetail drawerのImpactから開く。roadmapのmtimeでfreshnessを代用しない。source previewはallowlist内の相対pathに限定し、hidden / secret / 個人ノート / symlink / binary / 非UTF-8 / oversized fileを表示しない。Markdownとuser contentはescape / sanitizeする。

## 自動・手動の起動

`explicit-roadmap`または`roadmap`では、Phase 2完了後にsyncが生成・検査したRoadmapを表示し、30_plan.mdをPlan Viewerで開く。Phase 3/4更新後は同じsyncで再生成し、Phase 5では05_log.mdをLog Viewer、90_verification.mdがあればVerification Viewerで開く。watchは必要な場合だけ使う。

手動トリガーは「計画をビューアで見たい」「HTMLで確認したい」「ロードマップを見たい」「ログをビューアで見たい」、または /viewing-plans である。log-onlyで手動表示を明示された場合はexplicit-roadmapへ昇格する。

roadmap Task Hubを横断確認するときは既存syncへ明示rootを渡す。選択は完全一致のsession / thread IDを優先し、path・title・更新時刻だけで自動確定しない。command引数、tool output全文、古い会話context、secretを表示用modelへ渡さない。

## Security

MCP Appsは対応hostでtext/html;profile=mcp-app、宣言済みresource URI、standard transportを使い、非対応hostではtextへ退化する。CSPで外部loadを禁止し、Markdownとuser contentをsanitizeする。コメント送信など外部writeはこのSkillでは承認しない。

関連:
- context/workflow-rules.md
- context/memory-file-formats.md
- context/agent-team-routing.md
- context/codemap.md
- context/html-artifact-contract.md と config/html-surfaces.json
- ~/.codex/skills/viewing-plans/references/ui-change-preview.md
