# Source reputation snapshot — 2026-07-15

このスナップショットは候補ソースの優先順位と追加審査の必要性を判断するための補助情報である。star、fork、issue 数、公式性は安全性や採用承認を意味しない。採用判断では固定 revision、完全な package tree、license、静的検査、人間 review、価値 eval を別々に確認する。

調査時点では11ソースすべてが非 archived で、registry の固定 revision は default branch の HEAD と一致していた。数値は2026-07-15時点の GitHub 表示値であり、将来変化する。

| Source | Signal | License / security | Governance judgment |
|---|---:|---|---|
| [Agent Skills specification](https://github.com/agentskills/agentskills) | 23,064 stars / 1,629 forks / 29 open issues | Apache-2.0 / repository security policy 未検出 | 一次仕様の trust anchor。Skill 実装の一括承認には使わない。 |
| [OpenAI plugins](https://github.com/openai/plugins) | 4,583 / 664 / issues disabled | root license なし | 公式 curated examples だが一括再利用不可。608件中403件に近傍 license evidence がない。 |
| [Anthropic skills](https://github.com/anthropics/skills) | 161,210 / 19,045 / 292 | per-skill license 混在 | 公式でも skill 単位で審査する。README は一部 office skills を source-available・非OSSと説明し、critical use 前の test を求める。18件中2件に license gap がある。 |
| [Vercel Skills CLI](https://github.com/vercel-labs/skills) | 26,158 / 2,193 / 600 | README は MIT、root license file なし | distribution reference。install と network surface を trust anchor にしない。 |
| [Matt Pocock skills](https://github.com/mattpocock/skills) | 170,770 / 14,694 / 164 | MIT | 活発で40件すべてに license evidence がある。ただし人気は approval ではなく、script・write・global workflow は個別 review が必要。 |
| [Superpowers](https://github.com/obra/superpowers) | 254,846 / 22,780 / 154 | MIT | Skill 集より methodology / harness に近い。hooks、global config、process gate を伴い得るため standard approval path では L2 とする。 |
| [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills) | 29,077 / 2,605 / 59 | README は MIT、root license file なし | 公式 collection でも deploy、network、credential 系を含む。9件すべてに license-file gap がある。 |
| [Microsoft Azure Skills](https://github.com/microsoft/azure-skills) | 1,283 / 207 / 2 | MIT / [security policy](https://github.com/microsoft/azure-skills/security/policy) | 保守と security signal は良い。credential、network、MCP 能力が主なので standard path では L2。 |
| [Hugging Face Skills](https://github.com/huggingface/skills) | 10,814 / 717 / 7 | Apache-2.0 | 公式で license と活動は明確。Hub token、model、dataset 操作は L2 として隔離する。 |
| [Addy Osmani Agent Skills](https://github.com/addyosmani/agent-skills) | 78,381 / 8,420 / 48 | MIT | 活発で24件すべてに license evidence がある。自己記述の「production-grade」と人気を approval にしない。 |
| [Cisco Skill Scanner](https://github.com/cisco-ai-defense/skill-scanner) | 2,354 / 290 / 9 | Apache-2.0 / [security policy](https://github.com/cisco-ai-defense/skill-scanner/security/policy) | best-effort の補助 signal。scanner 自身が false positive / false negative と human review の必要性を明記しており、approval oracle にはしない。 |

役割は次のように分離する。

- 仕様: Agent Skills specification。
- vendor reference / candidate: OpenAI、Anthropic、Microsoft、Hugging Face、Vercel。
- community candidate: Matt Pocock、Obra、Addy Osmani。
- distribution reference: Vercel Skills CLI。
- optional security signal: Cisco Skill Scanner。

この区分は trust の短絡を防ぐためのもので、候補ごとの approval lifecycle を省略しない。

## Refresh boundary

評判signalを更新するときは `reputation.lock.json` の `generated_at`、各snapshotの `observed_at`、数値、assessment、evidence URLだけを更新する。source ID、GitHub identity、固定revisionはregistryと一致させる。評判の更新日だけを理由にregistryのsource観測日やcatalog / estate lockを変更しない。upstream revisionを更新する場合は別のsource updateとして、catalogと候補を再審査する。
