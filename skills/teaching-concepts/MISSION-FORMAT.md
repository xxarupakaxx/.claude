# MISSION.md の形式

`MISSION.md` はワークスペースのルートに置く。
ユーザーがこのトピックを学ぶ**理由**を記録する。
次に教える内容、提示する資料、設計する演習など、すべての教育上の判断をこの文書へ結び付ける。

## テンプレート

```md
# Mission: {Topic}

## Why
{1-3 sentences. The concrete real-world goal the user is chasing. What changes in their life or work when they have this skill? Avoid abstract framings like "to understand X" — push for the underlying outcome.}

## Success looks like
- {A specific, observable thing the user will be able to do}
- {Another specific thing}
- {…}

## Constraints
- {Time, budget, prior commitments, learning preferences, anything that bounds the approach}

## Out of scope
- {Adjacent topics the user explicitly does not want to chase right now — protects the zone of proximal development}
```

## ルール

- **ワークスペースごとにミッションを一つだけ置く。**
  ユーザーが無関係な二つのことを学びたい場合は、ワークスペースを二つに分ける。
- **抽象的な目標より具体的な目標を選ぶ。**
  「健康になる」より「10月までにハーフマラソンを走る」、「Rust を学ぶ」より「チーム向けの Rust CLI をリリースする」がよい。
- **曖昧さをそのまま受け入れない。**
  ユーザーが理由を説明できない場合は、何かを書く前に面談する。
  悪いミッションは、ミッションがない状態より有害である。
- **現実が変わったら改訂する。**
  ミッションは変化する。
  ユーザーの目標が移ったら、このファイルを更新し、古いミッションで今後のセッションを導かない。
- **短く保つ。**
  `MISSION.md` が一画面を超えたら、羅針盤ではなく計画書になっている。
