---
name: ask-skill-router
description: "skill / plugin / agent route を選ぶ canonical entrypoint。user-invoked と model-invoked を分け、「どのskill」「ask-matt相当」「flow選んで」「このタスクの進め方を選んで」等に、最小の規律と必要な承認を返す。"
---

# Ask Skill Router

この skill は、作業前に使う **canonical routing entrypoint** である。
`choosing-skills` は互換入口であり、独立した lifecycle の正本ではない。

## 正本と読込順

1. project の `AGENTS.md` / `CLAUDE.md` / `README.md` を先に読む。
2. no skill で足りるか、user-invoked か model-invoked かをこの skill で決める。
3. 具体的な plugin / skill / agent / orchestration tool の選択と Delegation Gate は `../../context/agent-team-routing.md` を読む。
4. engineering skill を選んだ場合、接続先 Phase と境界は `../../context/workflow-rules.md` の Phase adapter を読む。

## 判断原則

1. **No skill を先に検討する。** 自明な一行修正、単純な検索、短い説明には通常の作業を使う。
2. **実際のボトルネックを分類する。** 要求の不一致、共有語彙、feedback loop 不足、route の不確実性、設計劣化、外部調査不足のどれかを特定する。
3. **起動権を分ける。** 作業の進路や外部状態を変える flow は user-invoked、小さく可逆な品質規律は model-invoked とする。
4. **重い flow を既定にしない。** Superpowers、`team-run`、`orchestrate`、`blueprint` は、明示依頼またはその共有状態が本当に必要な場合だけ選ぶ。
5. **route 選択と副作用の承認を分ける。** skill を選んだだけでは、外部投稿、tracker 更新、commit / push、secret 書き込みを許可しない。

## 基本ルーティング

| 症状 | 推奨 route | 起動権 |
|---|---|---|
| 何を作るべきか曖昧で codebase / 状態付き docs がない | `grill-me`、必要なら `brainstorming` | user-invoked |
| codebase / 状態付き docs を読みながら設計の合意を作る | `grilling-with-docs` | user-invoked |
| 目的地はあるが、複数 session にまたがる route 自体が霧に包まれている | `mapping-large-projects` | user-invoked |
| route と acceptance が明確で、小さく閉じる | direct lane / focused discipline | model-invoked または no skill |
| route と acceptance が明確で、Goal・Team Journal・独立検証を持つ協調が価値を生む | `team-run` または `blueprint` | user-invoked |
| engineering lifecycle の分岐が必要 | `../../context/agent-team-routing.md` の Engineering Lanes | route ごとに判定 |
| 独立タスクを複数担当へ割りたい | `team-run`、`orchestrate` | user-invoked |
| 原因不明の不具合で再現器がない | `diagnosing-bugs` | model-invoked |
| test seam があり新規ロジックやバグ修正を進める | `tdd` | model-invoked |
| 外部事実や最新仕様が必要 | `research`、Context7、WebSearch、deepwiki | model-invoked |
| 外部 Skill の発見、評判、導入、更新、廃止、provenance / collision 確認 | `skill-governance`。棚卸しだけなら `skill-stocktake` | mutation は user-invoked、read-only audit は model-invoked可 |
| 完了前の証拠が弱い | `verification-loop`、`verify`、適切な review skill | model-invoked |
| plugin が所有する source / deliverable を扱う | `../../context/agent-team-routing.md` の plugin route | route ごとに判定 |

## 選択手順

1. user intent と期待成果物を一文にする。
2. no skill で閉じられなければ、上表で bottleneck を一つ選ぶ。
3. `../../context/agent-team-routing.md` で具体 route、起動権、Delegation Gate、外部書き込み gate を確認する。
4. project rule と矛盾する route は採用せず、より小さい route または user confirmation へ戻す。

## Router の保守

shared skill の追加、改名、削除、source pin 更新を行ったら、`skill-governance` の registry / lock / parity を先に確認し、この表と `../../context/agent-team-routing.md` の入口を再点検する。
upstream の別名をそのまま増やさず、既存の canonical route と責務境界に収まるかを先に確認する。

## 出力形式

```md
推奨route: <skill / plugin / no skill>
起動権: user-invoked / model-invoked / no skill
理由: <ボトルネックを1文で>
Phase/adapter: <接続する global Phase または none>
次の一手: <今すぐ行う最小手順>
読むcontext: <必要な正本 path、なければ none>
外部承認: <required: 対象と操作 / none>
```

## 禁止

- 単に「非自明」だからという理由だけで重い flow や sub-agent fan-out へ送らない。
- user-invoked skill を、別の model-invoked skill から暗黙に起動しない。
- in-progress、deprecated、promotion 状態不明の upstream skill を shared engineering lane として推奨しない。
- project rule、Phase 0-5.5、review、commit / push policy をこの router で上書きしない。
