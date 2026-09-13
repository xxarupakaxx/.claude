---
name: "source-command-orchestrate"
description: "migrated source command orchestrateの互換入口。実行契約はcanonical orchestrate Skillへ委譲する。"
---

# source-command-orchestrate

Use this skill when the user asks to run the migrated source command `orchestrate`.

## Compatibility contract

Read `../orchestrate/SKILL.md` and follow it as the canonical execution contract.

This adapter does not own agent chains, artifact fields, capability routing, reviewer selection, or retry limits.
