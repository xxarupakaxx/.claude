---
name: cleanup-knowledge
description: |
  知見ファイルのクリーンアップを実行。
  30日未参照のアーカイブ候補、同一タグの統合候補を確認し、
  ユーザー承認のもとで整理を行う。
  SessionEndで提案が表示された場合や、手動で /cleanup-knowledge 実行時に使用。
---

# Cleanup Knowledge

知見ファイル（memories/、solutions/）の整理・統合を行う。

## トリガー

- `/cleanup-knowledge` で明示的に実行
- SessionEndで「Knowledge Cleanup Suggestions」が表示された後

## 実行フロー

### Step 0: 対象と証跡を固定

1. 1回の実行で扱う `TOPLEVEL`、`MEMORY_DIR`、`index.json`、対象のpathまたはprefixを先に固定する。別home、SQLite、派生DB、別プロジェクトは、明示された範囲に含まれない限り読まない。
2. 実行開始時に対象一覧をpath順で保存し、各候補についてindexのentryと原本のSHA-256を記録する。後から追加・更新されたファイルは同じ実行の候補へ黙って足さない。
3. 読了深度を分けて記録する。`metadata-only`（index/frontmatterだけ）、`full-body`（対象本文、含まれるコード例・図を全文）、`reference-read`（判断に必要な特定のリンク先を確認）、`unread`（未確認）を混同しない。アーカイブや統合の判断は対象本文が `full-body` の候補だけで行い、リンク先は必要な範囲を別に記録する。未読を支持済みと扱わない。
4. 候補の主張ごとに、本文の支持箇所、原本hash、未確認範囲を記録する。indexの参照回数やタグの一致は、本文の正しさ・時点・重複を証明しない。
5. `agent-memory`（想起・保存）、`compounding-knowledge`（再利用可能な解決策）、`skill-governance`（Skillの採否）など既存Skillの責務を比較し、cleanupが代替しない範囲と引き継ぎ先を候補ごとに残す。全保管層の横断監査をこのSkillの暗黙の責務にしない。
6. 対象外、未読、hash不一致、支持箇所を確認できない候補は処置せず、理由と再開条件を報告する。

### Step 1: 現状分析

```bash
TOPLEVEL=$(git rev-parse --show-toplevel)
MEMORY_DIR="${TOPLEVEL}/.local"
INDEX_FILE="$MEMORY_DIR/index.json"
THRESHOLD_DATE=$(date -v-30d +%Y-%m-%d)

# index.jsonの内容を確認
cat "$INDEX_FILE" | jq '.files | to_entries | sort_by(.value.ref_count) | reverse'

# 30日未参照のファイルを特定
jq -r --arg threshold "$THRESHOLD_DATE" '.files | to_entries[] | select(.value.last_accessed < $threshold) | .key' "$INDEX_FILE"
```

### Step 2: アーカイブ候補の確認

30日以上参照されていないファイルをリストする。候補表には、最終参照、参照回数、原本hash、`read_depth`、本文支持の有無、関連する既存Skillを併記する。

```markdown
## アーカイブ候補（30日未参照）

| ファイル | 最終参照 | 参照回数 | 原本hash | read_depth | 本文支持 | 引き継ぎ先 |
|---------|---------|---------:|---------|------------|---------|------------|
| solutions/xxx.md | 2026-01-15 | 2 | `<sha256>` | full-body | 確認済み | compounding-knowledge |
| memories/yyy.md | 2026-01-20 | 0 | `<sha256>` | unread | 未確認 | agent-memory |
```

既存の承認が対象と影響を含む同じ範囲の可逆な整理に適用できる場合、その承認を使い、候補ごとの一律な再確認を追加しない。承認がない、または移動・削除で対象や影響を広げる場合だけ、対象と操作を具体化してAskUserQuestionで確認する。

AskUserQuestionで確認する場合:
- 「アーカイブする」→ `${MEMORY_DIR}/archived/` に移動
- 「保持する」→ last_accessedを今日に更新
- 「保留する」→ 未読・支持不足・参照影響を残して次回へ回す

削除はこのSkillの選択肢にしない。削除を要望された場合も、原本path、incoming wikilinkとindex参照、保存目的、復元方法、削除の影響、承認の対象・期限を値なしで記録するだけに留める。Vaultの原本削除は別の明示的な承認・実行境界が必要であり、候補確認や既存の承認を削除許可へ読み替えない。

### Step 3: 統合候補の確認

同一タグが3件以上あるトピックをリスト:

```markdown
## 統合候補（類似トピック）

### タグ: "n+1" (4件)
1. solutions/performance-issues/n-plus-one-query.md
2. solutions/performance-issues/eager-loading.md
3. solutions/database-issues/batch-loading.md
4. memories/performance/query-optimization.md
```

同一タグ、似たsummary、近い本文は統合候補を見つける手がかりに過ぎない。同じ経験を複数のtask logや後続訂正が記録している場合は、重複と断定せず、経験の系列・時点・保存目的を確認してリンクする。異なる経験を一つへ潰す統合と、同じ経験の参照化を別の処置として記録する。

AskUserQuestionで確認:
- 「統合する」→ 新しい統合ドキュメントを提案
- 「そのまま維持」→ スキップ

### Step 4: 統合実行（承認された場合）

1. 統合対象ファイルの内容を読み取り
2. 新しい統合ドキュメントを生成
3. **提案として表示**（Edit禁止ポリシー）
4. ユーザー承認後に保存
5. 元ファイルをアーカイブする場合は、`solutions/<relative path>` または `memories/<relative path>` の相対階層を保った `archived/solutions/<relative path>` / `archived/memories/<relative path>` を移動先にし、元path、目的、復元path、incoming wikilinkとindex参照の確認結果を提示する。ファイル名を変えず、移動先に同名ファイルがないこと、添付本体を移動しないこと、参照が安全に解決することを確認できた場合だけ移動する。既存承認が対象と影響を含む場合は再承認せず、範囲を超える移動・参照変更だけ具体的な承認を得る。いずれかを確認できない場合は移動せず、統合文書だけを提案状態にする。

アーカイブ後も元ファイルを復元できる状態を保つ。アーカイブを削除の代用にせず、原本の削除、改名、参照書換えはこのSkillでは実行しない。

### Step 5: インデックス更新

承認済みのアーカイブ・保存後だけ、既存のindex更新手順がある場合にそれを使う。更新前後の `index.json` hash、原本hash、path、参照数を照合し、候補確認中にindexを手作業で書き換えない。更新手順がない、またはhash・参照が一致しない場合はindex差分を提案状態で残し、更新完了とは報告しない。

## アーカイブディレクトリ構造

```
${MEMORY_DIR}/
├── solutions/          # アクティブな知見
├── memories/           # アクティブなインデックス
├── archived/           # アーカイブされた知見
│   ├── solutions/
│   └── memories/
└── index.json          # 参照回数トラッキング
```

## 禁止事項

- ユーザー承認なしの削除・移動
- アーカイブではなく即削除（復元可能性を維持）
- index.jsonの手動編集
