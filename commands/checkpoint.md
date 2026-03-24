---
name: checkpoint
description: "検証状態を保存する。合格基準の定義と現在のステータスをcheckpoint.mdに記録。/verifyと組み合わせて使用。"
---

# Checkpoint — 検証状態の保存

`verification-loop`スキルのStep 1として使用する。
現在の合格基準と各基準の状態をcheckpoint.mdに保存する。

## 手順

1. PJ CLAUDE.mdから品質チェックコマンドを取得
2. プロジェクトの技術スタックに合わせた合格基準を自動生成
3. 各基準の現在の状態を実行して確認
4. `${MEMORY_DIR}/memory/YYMMDD_<task>/checkpoint.md` に保存
5. 結果をユーザーに報告

## ユーザーがカスタム基準を指定した場合

`/checkpoint "coverage 80%以上" "バンドルサイズ5MB以下"` のように引数で追加基準を受け付ける。
