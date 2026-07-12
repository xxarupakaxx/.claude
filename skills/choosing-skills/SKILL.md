---
name: choosing-skills
description: 既存の choosing-skills 呼び出しを canonical な ask-skill-router へ渡す compatibility entrypoint。
disable-model-invocation: true
---

# Choosing Skills Compatibility Entrypoint

この skill は upstream 互換の入口であり、独立した lifecycle や routing table の正本ではない。

次の順で route を選ぶ。

1. `../ask-skill-router/SKILL.md` を読み、no skill、起動権、bottleneck を決める。
2. `../../context/agent-team-routing.md` を読み、具体的な plugin / skill / agent / orchestration tool と外部承認を決める。
3. engineering route では `../../context/workflow-rules.md` の Phase adapter に従う。

回答は `ask-skill-router` の `推奨route / 起動権 / 理由 / Phase/adapter / 次の一手 / 読むcontext / 外部承認` 形式をそのまま使う。

この compatibility entrypoint 自体は、user-invoked skill の起動、外部 tracker 更新、commit / push、secret 書き込みを許可しない。
