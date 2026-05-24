# Common Git Workflow Rules

全プロジェクトに適用されるGitワークフロー規約。

## コミット

- git-cz形式: `<type>: <日本語の説明>`
- type: feat, fix, refactor, docs, test, chore, perf, ci
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

- main/masterへの直接push
- `--force` push（`--force-with-lease`は許容）
- `--no-verify`でフックをスキップ
- 機密情報（.env, credentials）のコミット
- バイナリファイルの大量コミット
