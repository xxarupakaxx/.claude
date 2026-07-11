---
name: writing-specifications
description: 現在の会話を仕様書にまとめてプロジェクトの issue tracker に公開する。インタビューは行わず、すでに話し合った内容を統合する。
disable-model-invocation: true
---

このスキルは、現在の会話コンテキストと codebase への理解をもとに仕様書を作成する。
この文書は PRD と呼ばれることもある。
ユーザーへのインタビューは行わず、すでに把握している内容を統合する。

issue tracker と triage label の語彙は、事前に提供されている必要がある。
提供されていない場合は `/setting-up-engineering-skills` を実行する。

## 手順

1. まだ調査していない場合は repo を調べ、codebase の現在の状態を理解する。
仕様書全体でプロジェクトの domain glossary にある語彙を使い、変更対象の領域にある ADR を尊重する。

2. 機能をテストする seam の案を作る。
新しい seam より既存の seam を優先する。
新しい seam が必要なら、可能な限り高い位置に設ける案を出す。
codebase 全体の seam は少ないほどよく、理想は一つである。

これらの seam がユーザーの期待に合っているか確認する。

3. 次の template で仕様書を書き、プロジェクトの issue tracker に公開する。
`ready-for-agent` triage label を付ける。
追加の triage は不要である。

<spec-template>

## 問題の説明

ユーザーが直面している問題を、ユーザーの視点から説明する。

## 解決策

問題の解決策を、ユーザーの視点から説明する。

## ユーザーストーリー

ユーザーストーリーを番号付きで**網羅的に**列挙する。
各ユーザーストーリーは次の形式で書く。

1. <actor> として、<benefit> のために <feature> したい

<user-story-example>
1. モバイルバンキングの顧客として、支出についてより適切に判断できるように、口座の残高を確認したい
</user-story-example>

ユーザーストーリーは十分に網羅し、機能のあらゆる側面を扱う。

## 実装上の決定

決定済みの実装事項を列挙する。
次の内容を含めてもよい。

- 構築または変更する module
- 変更する module の interface
- 開発者による技術的な補足
- architecture 上の決定
- schema の変更
- API contract
- 具体的な interaction

具体的なファイルパスやコードスニペットは含めない。
すぐに古くなる可能性があるためである。

例外として、prototype が文章より正確に決定内容を表す snippet（state machine、reducer、schema、type shape）を生成した場合は、該当する決定の中に埋め込んでもよい。
prototype から得たことを簡潔に記す。
動作する demo 全体ではなく、決定に関わる部分だけに絞る。

## テスト上の決定

決定済みのテスト事項を列挙する。
次の内容を含める。

- 良いテストの条件（実装の詳細ではなく、外部から見える挙動だけをテストする）
- テストする module
- テストの参考になる既存例（codebase 内にある同種のテストなど）

## 対象外

この仕様書の対象外となる事項を説明する。

## 補足

機能についての補足事項を書く。

</spec-template>
