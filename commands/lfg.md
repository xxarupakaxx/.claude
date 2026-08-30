---
name: lfg
description: Phase 0–5.5を開始・再開する薄いClaude入口
---

# LFG

/lfg <タスクの説明> は context/workflow-rules.md のPhase 0–5.5を開始または再開する。ここにPhase手順、固定reviewer、artifact schemaを複製しない。
正本:
- context/workflow-rules.md
- context/workflow-details.md
- context/memory-file-formats.md
- context/agent-team-routing.md
- rules/model-routing.md
- ~/.codex/scripts/sync-roadmap.py
契約:
1. session / thread完全一致のtaskと05_log.mdを復元し、次actionを一つ選ぶ。
2. Phase 2–5のartifact保存後、同じTASKとRUNで共有syncを実行する。
3. --dry-runはread-only。CLI不存在、sync失敗、stale source、承認不足は停止する。
4. 旧generatorへのfallback、外部write、無承認のpolicy promotionを行わない。
5. WAITING_HUMAN / ROUTING_BLOCKEDは副作用なしで停止し、結果と再開条件を05_log.mdへ残す。
Claudeの共有sync例:
    python3 ~/.codex/scripts/sync-roadmap.py TASK --workspace-root ~/.claude --memory-root ~/.claude/.local/memory --run-id RUN --phase 2
phase 3、4、5も同じ入口でphaseだけを変える。
