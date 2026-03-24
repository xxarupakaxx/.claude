# Common Git Workflow Rules

全プロジェクトに適用されるGitワークフロー規約。

## コミット

- git-cz形式: `<type>: <日本語の説明>`
- type: feat, fix, refactor, docs, test, chore, perf, ci
- 1コミット = 1つの論理的な変更
- こまめにコミット（大きな変更を1コミットにまとめない）

## ブランチ

- 命名: `feature/<issue_num>-<title>` or `fix/<issue_num>-<title>`
- ベースブランチ: PJ CLAUDE.mdの`BASE_BRANCH`（未定義時: develop → main → master）
- 長期ブランチは定期的にベースからリベース

## PR

- PRタイトルは70文字以内
- 説明にはSummary（箇条書き）とTest plan（チェックリスト）
- 自明でない変更にはWhy（変更の動機）を記載
- 大きなPRは分割を検討

## 禁止事項

- main/masterへの直接push
- `--force` push（`--force-with-lease`は許容）
- `--no-verify`でフックをスキップ
- 機密情報（.env, credentials）のコミット
- バイナリファイルの大量コミット
