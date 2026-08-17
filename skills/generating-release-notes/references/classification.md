# 分類ルール

## ラベル → カテゴリのマッピング

GitHubのラベル文字列を正規化（小文字化、記号除去）し、次の優先順位で照合する。複数該当する場合は上から優先する。

| カテゴリ | 一致させるラベル例 | 備考 |
|---|---|---|
| `Breaking Change` | `breaking`, `breaking-change`, `major` | 対象範囲に関わらず最優先で分類 |
| `Bug Fix` | `bug`, `fix`, `bugfix`, `hotfix` | |
| `New Feature` | `feature`, `feat`, `enhancement`（新規機能の場合） | `enhancement`は既存機能改善と紛れやすいので本文タイトルも確認する |
| `Improvement` | `improvement`, `refactor`（ユーザー影響がある場合のみ）, `performance` | 内部リファクタで外部影響が無いものは`Internal`へ |
| `Internal（非公開）` | `internal`, `chore`, `ci`, `docs-internal`, `wontfix`, `duplicate` | リリースノート対象外。Notion/Slackに出さない |

## ラベルが無い/曖昧な場合

推測で確定しない。次の手順で扱う。

1. Issueタイトルが Conventional Commits 風のprefix（`feat:`, `fix:`, `chore:`, `docs:`）を持つ場合は参考情報として提示するが、確定には使わない
2. 「要確認」リストとしてユーザーに一覧提示し、カテゴリを選んでもらう
3. ユーザー確認が取れるまで、そのIssueをNotion/Slackへの公開候補に含めない

## Kubernetes方式との対応（参考）

Kubernetesの`release-note`ラベル運用は、PR本文の`release-note`ブロックに`NONE`と書くことで明示的に除外する方式を取る。このスキルでは、GitHubラベルに`release-note-none`または`skip-release-note`があればコードを検索せずそのまま`Internal`扱いとする。

## 対象範囲（テナント/プラン）の抽出

1. ラベルに`tenant:xxx`や`plan:xxx`のようなプレフィックス付きラベルがあればそこから抽出する
2. 無ければIssue本文中の「対象」「Scope」等の記載を探す
3. どちらも無ければユーザーに確認する（推測で「全テナント対象」と書かない）
