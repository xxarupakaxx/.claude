---
name: techdebt
description: セッション中の変更、指定ディレクトリ、またはコードベースから重複コードを検出し、統合候補を報告する。`/techdebt`、技術的負債の整理、code review で重複を調べる依頼に使う。
context: fork
---

# Tech Debt：重複コード

重複を「削除すべき」と決めつけず、意図的な重複や性能上の理由を確認したうえで、統合の候補と影響を報告する。既定ではセッション中に追加・変更した範囲を対象にする。

## 1. スコープ

```bash
git diff --name-only HEAD~10
git diff --name-only <base-branch>...HEAD
```

`/techdebt` の引数で次を選ぶ。

- `--scope session`：セッション中の変更（既定）
- `--scope directory --dir <path>`：指定ディレクトリ
- `--scope all`：コードベース全体

対象と比較基準を先に報告し、依頼外の変更範囲を広げない。

## 2. 検出

まず対象言語・構造に合う検索をする。

```bash
rg -l 'function\s+\w+|const\s+\w+\s*=' --type ts --type js
rg -n '<suspected-pattern>' --type ts -C 5
npx jscpd --min-lines 5 --min-tokens 50 <target-dir>
```

次の種類を区別する。

- **Copy-Paste**：変数名などだけが違う同一 block
- **Similar Logic**：制御フローや処理目的が同じ別実装
- **Parallel Implementations**：同じ機能・同名関数の並存
- **Hardcoded Values**：重複する magic number や設定
- **Boilerplate**：繰り返す定型構造

ツールの出力だけで同一性を断定せず、該当箇所を読み、役割と挙動を比較する。

## 3. 分類と提案

目安として high は5箇所以上または保守影響が大きいもの、medium は2〜4箇所、low は軽微な重複とする。件数だけで優先度を固定せず、変更頻度、挙動差、統合コスト、意図を添える。

各候補に次を示す。

- priority と理由
- 全ての検出位置（path:line）
- 現状の共通点と差分
- 統合案、影響範囲、必要な test
- 意図的に残す場合の理由

## 4. 出力と実行

```markdown
# Tech Debt Report
## Summary
- date / scope / duplicate count（high・medium・low）
## Findings
### Duplicate #1
...
## Recommended actions
...
```

`--min-lines <N>`（既定5）、`--priority <high|medium|low>` で検出条件を調整できる。`--fix` は検出後に自動リファクタリングを行う指定だが、ユーザー承認なしに実行しない。実行する場合は共通化、参照置換、test、commit の順にする。

包括的な品質確認は `codebase-review`、Phase 4 の補完は `@context/workflow-rules.md` を参照する。大規模リファクタリングは別タスクへ分ける。
