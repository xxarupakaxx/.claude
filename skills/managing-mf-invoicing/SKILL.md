---
name: managing-mf-invoicing
description: MFクラウド請求書・経費のMCPツールを使った操作を自動化する。認証、取引先管理、勤怠データからの請求書自動生成、見積書・納品書作成、PDF取得、入金管理、経費管理に対応。「請求書を作って」「勤怠から請求書」「請求書一覧」「見積書作成」「経費登録」「入金確認」等の依頼時に使用。
---

# MFクラウド請求書・経費 操作スキル

MFクラウド請求書MCPツール（`mcp__mf-invoice__*`）を使い、請求書・見積書・経費の操作を自動化する。

## 前提

- MCPサーバー `mf-invoice` が接続済みであること
- 未接続の場合はユーザーに `/mcp` での再接続を案内

## ワークフロー

### 1. 認証確認（常に最初に実行）

```
mf_auth_status → 認証済み？
  YES → 続行
  NO → mf_auth_start(wait: false) → ブラウザ認証を案内
```

- トークン期限切れ時は `mf_refresh_token` を試行
- それでもダメなら再認証

### 2. 勤怠→請求書 自動生成フロー

**CRITICAL**: ユーザーが勤怠データを貼り付けた場合に自動トリガー

1. **勤怠データ解析**: Read `references/attendance-parsing.md`
2. **取引先確認**: `mf_list_partners` で既存取引先を検索
   - 未登録の場合 → Web画面での登録を案内（API未対応）
3. **請求書作成**: `mf_create_billing` で日ごと明細を生成
   - 品目名: `開発業務 M/DD` 形式
   - 単価: 勤怠シートの時給
   - 数量: 各日の稼働時間（小数2桁）
   - 単位: `時間`
   - 消費税: `ten_percent`
4. **PDF案内**: MF Web画面からのダウンロードを案内
   - ファイル名規則: `YYYYMM_氏名_業務委託費用.pdf`

### 3. 請求書管理

| 操作 | ツール |
|------|--------|
| 一覧取得 | `mf_list_billings`（期間・取引先・入金状態で絞込） |
| 詳細確認 | `mf_get_billing` |
| 更新 | `mf_update_billing` |
| 入金状態変更 | `mf_update_payment_status`（unsettled/settled） |
| PDF URL取得 | `mf_download_billing_pdf` |

### 4. 見積書管理

| 操作 | ツール |
|------|--------|
| 一覧取得 | `mf_list_quotes` |
| 詳細確認 | `mf_get_quote` |
| 作成 | `mf_create_quote` |
| 更新 | `mf_update_quote` |
| PDF URL取得 | `mf_download_quote_pdf` |
| 請求書に変換 | `mf_convert_quote_to_billing` / `mf_create_billing_from_quote` |

### 5. その他

- **納品書作成**: `mf_create_delivery_slip`
- **品目マスタ**: `mf_list_items` / `mf_get_item`

### 6. 経費管理

認証は請求書と別。`mf_expense_auth_start` → `mf_expense_auth_status` で確認。

| 操作 | ツール |
|------|--------|
| 経費一覧 | `mf_expense_list_transactions` |
| 経費登録 | `mf_expense_create_transaction` |
| 経費更新 | `mf_expense_update_transaction` |
| 経費削除 | `mf_expense_delete_transaction` |
| レシート添付 | `mf_expense_upload_receipt` |
| 経費レポート | `mf_expense_list_reports` / `mf_expense_get_report` |
| レポート承認 | `mf_expense_approve_report` / `mf_expense_disapprove_report` |
| マスタ参照 | `mf_expense_list_depts` / `mf_expense_list_projects` / `mf_expense_list_ex_items` / `mf_expense_list_offices` |

## 請求書作成時の注意事項

- **支払条件**: 改行は実際の改行文字を使用（`\n`リテラルにしない）
- **時間の丸め**: 分→時間変換時は小数2桁（例: 1:08 → 1.13）
- **取引先作成**: MCPでは未対応。Web画面での登録を案内
- **PDF取得**: `mf_download_billing_pdf` はAPI認証付きURL。Web画面からのダウンロードを案内

## 既知の制限

- 取引先の新規作成/更新/削除はAPI未対応
- PDF URLはAPI認証必要（ブラウザ直接アクセス不可）
- レート制限: 3req/sec
