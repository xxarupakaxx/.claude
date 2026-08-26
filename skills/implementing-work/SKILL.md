---
name: implementing-work
description: spec や ticket に基づいて作業を実装します。
disable-model-invocation: true
---

ユーザーがApproved PRD、ticket、またはfast-trackのdirect requirementで示した作業を実装します。

実装前にWork Packetの`artifact_id / source_hash / Objective / Scope / Acceptance / Constraints / capability_class / safety_decision_id / side effects / approval evidence / dry-run`を確認します。

Approved PRDが必要なrouteで`review_status: pass`がない場合、または必要な承認証跡がない場合は実装せず停止します。

可能なところでは、事前に合意した seam で `/tdd` を使います。

コード変更では、実装前に `rules/complexity-budget.md` の要素別 production / test / config・migration target、除外、超過時の再計画条件を確認します。要素完了ごとに actual と variance を記録し、targetを守るためにテスト・安全性・必要なエラー処理を削りません。

typecheck は定期的に回します。
単体 test file もこまめに回します。
full test suite は最後に一度通します。

終わったらEvidence Bundle draftへacceptance evidence、test、finding、residual risk、実行済みwriteを記録し、`/reviewing-code` で独立レビューします。レビューへ target / actual / variance / reason を渡します。

作業内容は current branch に commit します。
