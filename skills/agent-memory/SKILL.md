---
name: agent-memory
description: "メモリの保存・想起・整理を依頼された場合に使用。トリガー: '覚えて'、'保存して'、'メモして'、'〜について何を話した？'、'ノートを確認'、'メモリを整理'。価値ある発見を保存すべき場合はプロアクティブに使用。"
allowed-tools: Read, Write, Grep, Glob
---

# Agent Memory

タスクの知見をインデックス化し、後から検索・参照可能にする。

**Location:** `.local/memories/`（PJ単位）

## 2層構造

```
.local/
├── memory/          # 詳細ログ（既存）
│   └── YYMMDD_<task>/
│       ├── 05_log.md
│       └── ...
└── memories/        # インデックス（本スキル）
    └── <category>/
        └── <topic>.md
```

- **memory/**: タスクの全記録（生ログ）
- **memories/**: 要約・インデックス（検索用）

## 使い方

**検索フロー:**
1. 「〇〇について思い出して」
2. memories/のsummaryを検索
3. 該当するmemory/ディレクトリの詳細を参照

## Proactive Usage

**Save memories when:**
- タスク完了時に価値ある知見があった
- 調査で重要な発見があった
- トリッキーな問題を解決した
- アーキテクチャの決定をした

本人の選好や作業上の指示を保存する場合は、本人が明示した現在の選好だけを `current` として扱い、対象・時点・根拠を添える。汎用Skillへ本人の役割、私的事実、関係者、案件固有の許可を複写しない。

**Check memories when:**
- 関連する作業を開始する前
- 過去に触った機能を再度作業する時
- 会話の途中で過去の文脈が必要な時

## 文脈の状態を分ける

保存・想起時は、次の状態を一つずつ区別する。frontmatterへ置く場合の値は例であり、既存のsummaryやcreatedを置き換えない。

- `current_preference`: 本人が現在も有効だと明示した選好。対象範囲と確認日を記録し、本人の訂正・撤回があるまでそのscope内で保持する。毎回の再確認を既定にしない。
- `historical_instruction`: 過去の指示や当時の前提。現在の既定値として自動適用しない。
- `correction`: 後続の訂正。訂正元を `supersedes` または `related` で参照し、古い記録を同時に現行扱いしない。
- `current_unknown`: 現在の状態・許可・実行結果を確認できていない事項。推測で `resolved` や `current` に変えない。

検索で見つかった履歴は、本文と状態を確認してから現在の判断へ使う。後続訂正がない古い指示も、時点を越えた許可や設定として継承しない。AIの推測や要約を本人の明示した選好へ昇格しない。状態を確認できない記録は、想起結果に「未確認」と残す。

secretの実値、認証済みsession、token、secret reference、不要な個人識別情報は保存・関連付け・再掲をしない。必要な場合も、値を含まない種別、原本の識別子、確認状態だけを既存の安全な履歴へ渡す。

## 値を含まない除去台帳

機微値の除去や一致候補の確認を行う場合だけ、値を含まない台帳を先に作る。台帳には `target_id`、`storage_layer`、`field`、`derived_index`（FTS / embedding等）、`before_hash`、確認時点、処置状態を記録し、本文・値・認証情報は記録しない。除去後は同じ対象ID・保存層・field・派生索引を照合し、after hashと未確認範囲を別に残す。

一致が未確定、派生層を確認できない、または除去範囲を証明できない場合は `current_unknown` として保持する。単一層の除去や検索結果から全層完全除去を主張しない。DB操作が必要な場合は既存の対応手順と権限へ引き継ぎ、このSkillに新しいtool権限を足さない。

## Frontmatter

**Required:**
```yaml
---
summary: "1-2行の説明（検索の判断材料）"
created: 2026-01-14
---
```

**Optional:**
```yaml
---
summary: "N+1クエリ問題の解決 - eagerロードの適用"
created: 2026-01-14
updated: 2026-01-20
status: resolved  # in-progress | resolved | blocked | abandoned
tags: [performance, database]
related:          # 詳細ログへの参照
  - .local/memory/260114_n-plus-one-fix/
context_kind: knowledge  # current_preference | historical_instruction | correction | knowledge
state: current             # current | historical | superseded | unknown
supersedes: []             # 訂正元のmemory path（ある場合のみ）
---
```

## Search Workflow

```bash
# 1. カテゴリ一覧
ls .local/memories/

# 2. サマリー一覧
rg "^summary:" .local/memories/ --no-ignore --hidden

# 3. キーワードでサマリー検索
rg "^summary:.*keyword" .local/memories/ --no-ignore --hidden -i

# 4. タグ検索
rg "^tags:.*keyword" .local/memories/ --no-ignore --hidden -i

# 5. 全文検索（サマリーで見つからない場合）
rg "keyword" .local/memories/ --no-ignore --hidden -i

# 6. relatedから詳細ログを参照
```

## Operations

### Save

タスク完了時に価値ある知見をインデックス化:

```bash
mkdir -p .local/memories/category-name/
cat > .local/memories/category-name/topic.md << 'EOF'
---
summary: "簡潔な説明"
created: 2026-01-14
tags: [tag1, tag2]
related:
  - .local/memory/260114_task-name/
---

# タイトル

## 要点
- ポイント1
- ポイント2

## 詳細
→ related参照
EOF
```

### Maintain

- **Update**: 情報が変わったら`updated`フィールドを追加して更新
- **Delete**: 不要になってもファイルを削除せず、`superseded` / `abandoned` と理由を残す。原本の削除はこのSkillの責務外で、別の明示承認が必要
- **Consolidate**: 関連するメモリをマージする前に、同一経験か、別の経験を同じ原則で記録したものかを確認する。後者は履歴を潰さず関連付ける
- **Reorganize**: カテゴリを整理

## Guidelines

1. **要点のみ記載**: 詳細はrelatedで参照させる
2. **summaryは検索の判断材料**: 読むべきか判断できる内容に
3. **relatedを活用**: memory/の詳細ログへのリンクを必ず含める
4. **実用的に**: 本当に価値のある知見のみ保存
5. **状態を保持**: 現在の選好、過去の指示、後続訂正、current unknownを一つの現行指示へ混ぜない
6. **再利用範囲を限定**: 履歴の保存・想起は、現在の承認、runtimeの成功、外部状態の確認を代替しない
