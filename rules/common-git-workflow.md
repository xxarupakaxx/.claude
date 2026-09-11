# Common Git Workflow Rules

全プロジェクトに適用されるGitワークフロー規約。

## コミット

- git-cz形式: `<type>: <日本語の説明>`
- type: feat, fix, refactor, docs, test, chore, perf, ci
- 絵文字は使わない。prefix 以外は日本語で書く
- 1コミット = 1つの論理的な変更
- こまめにコミット（大きな変更を1コミットにまとめない）

### コミットメッセージ構造（CL description）

Google eng-practices 準拠。**First Line** + 空行 + **Body** の 2 部構成。

**First Line**:
- 命令形・現在形（"ユーザー認証を追加" / "FizzBuzz RPC を削除"）
- それ単体で何が変わったかが分かる（履歴一覧で意味が通る）
- 70 文字以内

**Body**（自明な変更を除き必須）:
- **What**: First Line の詳細展開
- **Why**: 解決したい問題・背景
- **Trade-off**: 採用したアプローチの欠点・他案を捨てた理由
- 参考リンク（Issue 番号、ベンチ結果、ADR、設計ドキュメント等）

**避ける First Line 例**: "Fix bug", "Update", "Add patch", "コード移動"

## ブランチ

- 命名: `feature/<issue_num>-<title>` or `fix/<issue_num>-<title>`
- ベースブランチ: PJ CLAUDE.mdの`BASE_BRANCH`（未定義時: develop → main → master）
- 長期ブランチは定期的にベースからリベース

## 変更完了時のpush

変更依頼では、必要な検証を終え、自分の変更だけをコミットした後、現在のブランチに対応する既存のリモートブランチへ通常pushする。条件が揃う場合は再確認を求めず、pushと到達確認までを完了条件に含める。

- 送信先は設定済みupstreamを優先する。upstreamがなければ、設定済みremote上の同名ブランチが一意に存在する場合に使う。無関係なブランチの存在を根拠に送信先を選ばない。
- fetchで最新状態を確認し、remote・送信先branch・送信するcommitを照合する。リモート側が進んでいれば既存変更を保全して統合し、必要な検証後に通常pushする。競合の解決が目的や仕様を変える場合だけ確認する。
- ユーザーがpush不要・ローカル作業のみと指定した場合は従う。送信先不明、新規remote・新規remote branch、履歴書換え、branch protectionや認証の変更は、この自動pushの範囲に含めない。project固有の送信先制約を守る。
- 他の未送信commitが含まれる場合は内容と依頼範囲を確認し、無関係な変更を混ぜて送らない。未コミット変更をまとめてstageしない。
- 成功後はリモートのcommitを照合し、push先とcommit hashを報告する。失敗した場合は原因を示し、未実施を成功として扱わない。

## PR

- PRタイトルは70文字以内（コミット First Line と同じ規約）
- 説明にはSummary（箇条書き）とTest plan（チェックリスト）
- 自明でない変更にはWhy（変更の動機）+ Trade-off（採用したアプローチの欠点・他案を捨てた理由）を記載
- 大きなPRは分割を検討

### PR サイズの目安と分割パターン

Google eng-practices 準拠。**「自己完結した 1 つの変更」**が単位。

| サイズ | 目安 | 判定 |
|--------|------|------|
| 小 | ~100 行 | 推奨 |
| 中 | 100-500 行 | 許容（理由があれば） |
| 大 | 1000 行超 | 原則 reject、分割を要求 |

**分割パターン**:
- **Stacking**: 先行 PR の上に積み増し（依存関係を明示）
- **水平分割**: レイヤー間（API/Domain/Infra 等）で分離
- **垂直分割**: 全レイヤーを貫く小さな機能単位に分離
- **Refactor 分離**: 機能追加・バグ修正と Refactor を別 PR にする（必須）
- **テスト同梱**: 新規ロジックのテストは同じ PR に入れる（Refactor 分離の例外）

## 禁止事項

- `--force` push（`--force-with-lease`は許容）
- `--no-verify`でフックをスキップ
- 機密情報（.env, credentials）のコミット
- バイナリファイルの大量コミット
