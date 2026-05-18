---
allowed-tools: Bash(git:*), Bash(gh:*)
argument-hint: [base-branch]
description: Draft PRを作成
---

# /pr コマンド

Draft PRを作成します。

## 実行手順

### 1. 現在の状態確認

```bash
git branch --show-current
git status
git log $ARGUMENTS..HEAD --oneline
```

### 2. PRテンプレートの確認

```bash
ls .github/PULL_REQUEST_TEMPLATE.md 2>/dev/null
```

### 3. 変更内容の確認

```bash
git diff $ARGUMENTS --name-only
git diff $ARGUMENTS
```

### 3.5. 状態図の取り込み

`/generate-state-diagram` が生成した `91_state_diagram.md` を検出し、PR本文に埋め込む。

```bash
# MEMORY_DIR は PJ CLAUDE.md 定義（未定義時は .local/）
# 最新のメモリディレクトリから 91_state_diagram.md を探す
find "${MEMORY_DIR:-.local}/memory" -maxdepth 3 -name "91_state_diagram.md" 2>/dev/null \
  | xargs -I{} stat -f "%m %N" {} 2>/dev/null \
  | sort -rn | head -1 | awk '{print $2}'
```

判定:

- **ファイルあり** → ファイル内の ` ```mermaid ... ``` ` ブロックを全て抽出し、後述「処理フロー / 状態遷移」セクションに埋め込む（`91_state_diagram.md` は Validator 通過済みなのでそのまま貼ってよい）
- **ファイルなし**:
  - 変更にワークフロー/状態管理/外部連携/ドメインモデル変更を含む → `AskUserQuestion` で `/generate-state-diagram` を先に実行するか確認
  - UIのみ / テストのみ / 設定・ドキュメントのみ → スキップ（CLAUDE.md `generate-state-diagram` のスキップ条件と一致）

### 4. PR本文の作成

テンプレートがあれば使用、なければ以下（状態図セクションはファイル検出時のみ含める）:

```markdown
## 概要
[変更内容の概要]

## やったこと
- 変更1
- 変更2

## やらなかったこと
- スコープ外の内容

## 影響範囲
- 影響を受ける画面・処理

## テスト方法
[動作確認方法]

<!-- 91_state_diagram.md が存在する場合のみ以下を追加 -->
## 処理フロー / 状態遷移

> 自動生成: `/generate-state-diagram` 出力（Mermaid Validator通過済み）
> 詳細・用語集・ファイル構成マップは `91_state_diagram.md` を参照

​```mermaid
<block_1 をそのまま貼り付け>
​```

​```mermaid
<block_2 をそのまま貼り付け>
​```
<!-- ここまで状態図セクション -->

## チェックリスト
- [ ] 型チェック通過
- [ ] Lint通過
- [ ] テスト通過
```

注意:

- PRテンプレート（`.github/PULL_REQUEST_TEMPLATE.md`）が存在する場合、テンプレートの項目を勝手に削除してはならない（CLAUDE.md 禁止事項）。状態図セクションはテンプレート末尾（チェックリスト前など適切な位置）に追記する形で挿入
- GitHubはPR本文のMermaidをネイティブレンダリングするため、画像化や外部リンクは不要
- Validator警告コメント（`<!-- ⚠️ Mermaid Validator FAILED ... -->`）が `91_state_diagram.md` に残っている場合、当該ブロックは貼らずに「※構文エラーのため省略」とだけ記載し、ユーザーに通知

### 5. Draft PR作成

```bash
gh pr create --draft \
  --base $ARGUMENTS \
  --title "<タイトル>" \
  --body "$(cat <<'EOF'
<本文>
EOF
)"
```

### 6. 結果の報告

作成されたPRのURLを報告。
