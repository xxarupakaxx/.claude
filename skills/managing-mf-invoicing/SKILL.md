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

### 1. 認証確認（外部ツール操作時のみ）

手元の勤怠データを解析・集計するだけの場合は、認証操作を開始せず結果を返す。取引先・既存請求書の照合、請求書・見積書・経費の取得や作成など外部MCPツールを使う操作に進む場合だけ、最初に認証状態を確認する。

```
mf_auth_status → 認証済み？
  YES → 続行
  NO → mf_auth_start(wait: false) → ブラウザ認証を案内
```

- トークン期限切れ時は `mf_refresh_token` を試行
- それでもダメなら再認証

### 2. 勤怠→請求書 自動生成フロー

勤怠データの貼り付けは解析の開始条件になり得るが、**解析依頼と請求書作成依頼を同一視しない**。
「解析して」「合計を確認して」だけの場合は解析・照合結果を返して停止し、`mf_create_billing`、更新、入金状態変更などの書き込みへ進まない。請求書を作成する場合は、現在の依頼が明示的な作成依頼であることと、作成対象が承認範囲に含まれることを確認する。既に承認された同一対象・同一範囲へ一律に再承認を求めず、対象月・取引先・金額・明細などが範囲を変えるときだけ確認する。

1. **勤怠データ解析**: Read `references/attendance-parsing.md`
   - 分単位の原値（出退勤・休憩・日別稼働）を保持して集計し、表示用の小数丸め値と請求計算の原値を分ける。
   - 日別明細の丸め後合計、勤怠の月合計（分）、請求金額を照合する。契約上の丸め規則が不明、または丸め差・空欄・休憩処理の扱いが確認できない場合は差異を示して作成を止める。規則上許容される差は、その根拠と扱いを記録する。
2. **既存状態の照合**: `mf_list_partners` と `mf_list_billings` で取引先および対象期間の既存請求書を検索
   - 未登録の場合 → Web画面での登録を案内（API未対応）
   - 同一対象の請求書、重複候補、未承認行があれば作成を止め、既存請求書の確認・更新・見送りの判断を分けて記録する。
3. **請求書作成**: 明細・合計・差異・承認範囲の照合が済み、明示的な作成依頼がある場合だけ `mf_create_billing` で日ごと明細を生成
   - 品目名: `開発業務 M/DD` 形式
   - 単価: 勤怠シートの時給
   - 数量: 各日の稼働時間（小数2桁）
   - 単位: `時間`
   - 消費税: `ten_percent`
4. **PDF状態確認**: 請求書の生成、PDF URL取得、ファイル取得、内容確認を別状態として記録する。`mf_download_billing_pdf` のURLが返っても取得・表示確認済みとは扱わない。API認証付きURLの取得に失敗した場合はWeb画面からのダウンロードと復旧手順を案内し、請求書作成の状態とPDF失敗を別々に報告する。
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
- **集計照合**: 分単位の原値から日別・月合計を計算し、日別明細の丸め後合計と勤怠シートの月合計の差を作成前に示す。差異の扱いが確認できるまで請求書を作成しない。
- **重複照合**: 対象期間・取引先の既存請求書を先に確認し、同一対象を二重作成しない。更新や再作成は、現在の依頼と承認範囲を照合して別操作として扱う。
- **取引先作成**: MCPでは未対応。Web画面での登録を案内
- **PDF取得**: `mf_download_billing_pdf` はAPI認証付きURL。生成済み・URL取得済み・ファイル取得済み・内容確認済みを分け、未取得や確認失敗を成功扱いにしない。Web画面からのダウンロードを案内する。

## 既知の制限

- 取引先の新規作成/更新/削除はAPI未対応
- PDF URLはAPI認証必要（ブラウザ直接アクセス不可）
- レート制限: 3req/sec
