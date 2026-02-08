---
name: techdebt
description: 重複コードの発見・削除。セッション終了時または技術的負債の整理依頼時に使用。コードベース内の重複・類似コードを検出し、リファクタリング提案を行う。
context: fork
---

# Tech Debt - 重複コード検出・削除

セッション中に追加・変更したコードを中心に、重複・類似コードを検出し、リファクタリング提案を行う。

## トリガー条件

- ユーザーが `/techdebt` を実行した場合
- セッション終了前に重複コードの確認を依頼された場合
- 「技術的負債を整理して」と依頼された場合
- コードレビューで重複が指摘された場合

## ワークフロー

### Phase 1: スコープ特定

```bash
# セッション中の変更ファイルを特定
git diff --name-only HEAD~10  # 直近の変更

# または特定のコミット範囲
git diff --name-only <base-branch>...HEAD
```

**スコープ選択肢:**
1. **session**: セッション中の変更ファイルのみ（デフォルト）
2. **directory**: 指定ディレクトリ内
3. **all**: コードベース全体

### Phase 2: 重複検出

#### 2.1 完全重複の検出

同一または酷似したコードブロックを検出:

```bash
# 関数・メソッドの重複検出
# TypeScript/JavaScript
rg -l "function\s+\w+|const\s+\w+\s*=" --type ts --type tsx --type js

# 類似パターンの検出
rg "<pattern>" --type ts -C 5
```

#### 2.2 類似パターンの検出

以下のパターンを重点的にチェック:

| パターン | 説明 | 検出方法 |
|---------|------|---------|
| **Copy-Paste** | 微修正のみの重複 | 関数名・変数名を除いたコード比較 |
| **Similar Logic** | 同じロジックの異なる実装 | 制御フロー分析 |
| **Parallel Implementations** | 同機能の別実装 | 同名関数の複数存在 |
| **Hardcoded Values** | 重複するマジックナンバー | 定数の重複検出 |
| **Boilerplate** | 繰り返しの定型コード | 構造の類似性 |

#### 2.3 検出ツール活用

```bash
# jscpd（JavaScript/TypeScript向け重複検出）
npx jscpd --min-lines 5 --min-tokens 50 <target-dir>

# または手動パターンマッチング
rg -n "<suspected-pattern>" --type ts
```

### Phase 3: 分析・分類

検出した重複を以下の基準で分類:

| 優先度 | 基準 | 例 |
|--------|------|-----|
| **high** | 5箇所以上で重複、保守性に重大な影響 | 同一バリデーションロジックが複数API |
| **medium** | 2-4箇所で重複、改善推奨 | 類似のエラーハンドリング |
| **low** | 軽微な重複、リファクタリングのオーバーヘッドが大きい | 2行程度のユーティリティ |

### Phase 4: リファクタリング提案

各重複に対して具体的な改善案を提示:

```markdown
## 重複 #1: [タイトル]

**優先度:** high/medium/low
**検出箇所:**
- `path/to/file1.ts:10-25`
- `path/to/file2.ts:30-45`
- `path/to/file3.ts:5-20`

**現状のコード（例）:**
```typescript
// file1.ts:10-25
const validateEmail = (email: string) => {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
};
```

**リファクタリング案:**
```typescript
// shared/validators.ts
export const validateEmail = (email: string): boolean => {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
};
```

**影響範囲:** 3ファイル
**工数見積:** 小（30分以内）
```

### Phase 5: 実行（オプション）

ユーザー承認後、リファクタリングを実行:

1. 共通化するコードを適切な場所に移動
2. 重複箇所を共通コードへの参照に置換
3. テスト実行で動作確認
4. コミット

## 出力形式

```markdown
# Tech Debt Report

## サマリー
- 検出日: YYYY-MM-DD
- スコープ: session/directory/all
- 検出重複数: X件（high: X, medium: X, low: X）

## High Priority

### 重複 #1: [タイトル]
...

## Medium Priority

### 重複 #2: [タイトル]
...

## Low Priority（参考）

### 重複 #3: [タイトル]
...

## 推奨アクション
1. [具体的なアクション]
2. [具体的なアクション]
```

## オプション引数

```
/techdebt [options]

--scope <session|directory|all>   検出スコープ（デフォルト: session）
--dir <path>                      対象ディレクトリ（--scope directory時）
--fix                             検出後に自動リファクタリング実行
--min-lines <N>                   最小重複行数（デフォルト: 5）
--priority <high|medium|low>      指定優先度以上のみ報告
```

## 既存設定との関係

- **codebase-review**: 包括的レビュー（6観点）、techdebtは重複コード特化
- **Phase 4品質確認（@context/workflow-rules.md）**: techdebtはPhase 4の補完として使用可能

## 注意事項

- 重複検出は「削除すべき」ではなく「統合検討」の提案
- 意図的な重複（パフォーマンス最適化等）は除外判断が必要
- リファクタリングは必ずテストで動作確認
- 大規模リファクタリングは別タスクとして計画
