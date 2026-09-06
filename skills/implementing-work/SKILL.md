---
name: implementing-work
description: 合意した仕様・ticket・直接の変更依頼を実装し、必要な動作確認まで完了する。
disable-model-invocation: true
---

# 実装を完了する

`context/workflow-rules.md`で作業規模を選び、目的、対象、完了条件、既存の制約を確認する。直接の変更依頼では、必要な実装と検証まで進める。

Work Packetを使うrouteでは、scope、acceptance、constraints、capability class、side effects、承認証跡を確認する。Approved PRDが必要なrouteに限り`review_status: pass`を要求する。通常作業にこれらのartifactを新しく要求しない。

## 実装と確認

既存の構成と関連する実装・testを根拠に、要求を満たす最小の変更を行う。TDDが変更の振る舞いを確かめるのに適していれば、その境界で使う。

変更の影響に合うtypecheck、lint、test、動作確認を選ぶ。全suiteはprojectの必須条件や影響範囲に応じて実行する。失敗を修正したら影響する検証を再実行し、新しい懸念がなければ終了へ進む。

起動や結果の確認を含む依頼では、最初の実装で止まらず、動作確認と必要な修正まで行う。検証だけを依頼された場合は、修正の権限を推測しない。

## 終了

通常作業では変更、検証、残課題を報告する。管理する作業では`context/workflow-rules.md`から該当する工程へ進み、review・Evidence・completion targetまで満たす。code変更量は`rules/complexity-budget.md`に従う。

commitとpushはproject policyと承認範囲に従い、自分の変更だけを対象にする。権限・外部write・不可逆操作の境界は共通ルールを使う。
