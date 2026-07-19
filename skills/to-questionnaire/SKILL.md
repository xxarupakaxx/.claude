---
name: to-questionnaire
description: 利用者だけでは答えられない判断を、知識を持つ相手へ渡すlocal Markdown questionnaireにする実験的Skill。`/to-questionnaire` と明示されたときだけ使う。
disable-model-invocation: true
---

# To Questionnaire

> Status: in-progress
>
> questionnaireをlocal fileへ作るまでがこのSkillの責務です。
> 送信、共有、tracker投稿は行いません。

利用者が単独では答えられない判断を、知識を持つ一人の相手へ渡すquestionnaireにします。

質問するのはsubjectそのものではなく、**誰へ渡し、何を持ち帰るか**です。

1. 一度のexchangeで、相手の役割、専門性、利用者との関係を確認する。
2. 一度のexchangeで、相手から得たい事実または判断を具体的な一覧にする。
3. `to-questionnaire-<slug>.md` を現在のdirectoryへ作る。
4. 必要な項目がすべて一つ以上の質問へ対応しているか確認し、pathを報告して止める。

## Document structure

```markdown
# <Questionnaire title>

**Purpose:** <何を決めるための質問か>

**From:** <利用者>
**To:** <回答者>
**How answers will be used:** <回答の利用先>

## Context

<回答に必要な一段落の背景>

## How to answer

<期限、所要時間の目安、部分回答や不明も有用であること>

## <Theme>

### <一つの論点だけを問う質問>

_Why this matters: <誤解を防ぐ必要がある場合だけ記載>_

>

## Anything else?

<聞けていない重要事項の自由記入>
```

## Safety boundary

- 自動起動しない。
- 一つの質問に複数の論点を混ぜない。
- 本人アカウント、秘密情報、個人情報を回答欄へ要求しない。
- 外部送信は利用者が別に依頼した場合だけ、その送信先の承認規則に従う。
