---
name: generate-verification-guide
description: ユーザーが検証ガイド、ローカル動作確認手順、チェックリストの生成を明示的に依頼したとき、変更に対応する再現可能な確認手順を作る。通常の実装完了や UI / API / DB 変更だけでは起動しない。
triggers:
  - "検証ガイド生成"
  - "verification guide"
  - "ローカル検証"
  - "動作確認手順"
invocation: user
allowed-tools: Read, Bash, Glob, Grep, Write
---

# ローカル検証ガイド生成

明示依頼を受けた変更の影響範囲を読み、実際に使う project command、前提、成功・空・失敗ケースを、後から再実行できる Markdown ガイドにする。ガイドを書くことと検証を実行することを分け、実行していない確認を完了扱いにしない。

## 適用と除外

`/generate-verification-guide` または上記の trigger がある場合だけ使う。設定、テスト、ドキュメントだけの変更や、依頼のない Phase 5 の自動実行には使わない。対象が UI、API、DB の複数にまたがる場合は、各影響と依存を一つのガイドにまとめる。

## 手順

### 1. 差分と前提

```bash
git diff <BASE_BRANCH>...HEAD --stat
```

変更ファイルを読み、UI（ページ / component）、API（route）、DB（migration / schema）、logic（lib / usecase / action）など、実際に該当する分類だけを記録する。既存の README、CLAUDE.md、test、fixture、環境変数、seed、migration command を調べる。`pnpm dev`、`npm run dev`、Docker などを推測せず、project が定めた command を使う。

### 2. 影響経路を追う

変更から利用者の URL、画面、主要操作、呼び出す API、関連データ、エラー境界へたどる。独立の explorer が利用可能で、調査量に見合う場合だけ委譲してよい。委譲しない場合も同じ項目をローカル検索で確認し、分からないものは `未確認` と書く。

### 3. ケースを設計する

該当する経路ごとに、次を具体的な操作と期待結果で書く。

- 正常：必要なデータと入力がある状態で主要操作が完了する。
- 空：該当データ、一覧、検索結果が0件のときに説明と次の操作が分かる。
- 失敗：認証切れ、権限不足、validation、外部依存、timeout など、今回の変更に関係する失敗を選ぶ。API key 未設定などを全 project へ機械的に足さない。
- UI：変更した control、focus / keyboard、responsive を必要な viewport で確認する。
- DB：migration の適用、schema、既存データとの互換、必要な seed / rollback を project の定義済み command で確認する。

各ケースに、前提、入力値、操作順、期待する画面・HTTP・データ状態、判定を記す。fixture や代替 service が本番経路を置き換える場合は、補助確認であることを明記する。

### 4. 保存

memory directory が定まっている場合は `90_verification.md` へ保存する。既存ファイルを上書きする必要がある場合は workflow のルールに従い、差分と承認を確認する。

```markdown
# ローカル検証ガイド

## 前提条件
- command、環境変数、外部サービス、データの前提

## 影響ページ一覧
| ページ | URL | 変更内容 | 優先度 |
| --- | --- | --- | --- |

## 検証手順
### 環境セットアップ
<project が定める command>
### ページ別ケース
#### <ページ名>（<URL>）
**画面構成**: <見えるもの>
**正常 / 空 / 失敗**: <操作、入力、期待結果>
### DB / API 確認
<定義済み command と期待状態>

## チェックリスト
- [ ] <具体的な確認>

## 未確認・トラブルシューティング
- <原因、再開条件、次の確認>
```

HTML表示を求められた場合だけ、`viewing-plans` の手順で検査済みガイドを通常ブラウザへ開く。チェック操作や HTML 表示だけで検証結果を更新したとは扱わない。未実行の test、利用できない credential、起動できない service は、理由と最小の再実行条件を報告する。

## 品質基準

「検索する」「動作する」ではなく、実在する画面・入力・期待値・command を示す。変更に関係する成功・空・失敗の各クラスを一つ以上確認し、該当しないクラスは対象外の理由を書く。project の既存基準と security / data boundary を弱める fixture や skip を追加しない。
