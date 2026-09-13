---
name: eval-harness
description: "Eval-Driven Development（EDD）フレームワーク。スキル・ワークフロー・エージェントの品質をpass@kメトリクスで定量評価し、回帰テストを自動化する。"
---

# Eval Harness — 評価駆動開発

## 概要

スキルやワークフローの品質を「感覚」ではなく「数値」で評価する。
pass@kメトリクスで信頼性を測定し、回帰テストで品質劣化を検出する。

## トリガー

- 新しいスキル・コマンドを作成した後
- ワークフローを変更した後
- 「このスキルの品質を評価して」
- `/eval <対象>`

## Eval定義

### 基本構造

```markdown
## Eval: [スキル名]

### Test Cases
| ID | Input | Expected | Criteria |
|----|-------|----------|----------|
| E1 | [入力] | [期待結果] | [判定基準] |
| E2 | [入力] | [期待結果] | [判定基準] |

### Pass Criteria
- pass@k = k回試行して1回以上成功する割合（kが大きいほど成功しやすい標準定義）
- 信頼性評価は pass@1 の実測割合で行う: 90%以上=信頼性高 / 70-90%=許容範囲 / 70%未満=要改善
- pass@3 / pass@5 は「再試行を許した場合に通るか」（フレーク耐性）を見る補助指標として使う。主指標はあくまで pass@1
```

### Eval種別

#### Capability Eval（新機能テスト）
新しいスキル・機能が正しく動作するかを検証:
```
入力: "TypeScriptプロジェクトでbuild-fixを実行"
期待: tsc --noEmitが0エラーになる
判定: exit code 0
```

#### Regression Eval（回帰テスト）
既存機能が壊れていないかを検証:
```
入力: "既存のcommitコマンドを実行"
期待: git-cz形式でコミットが作成される
判定: コミットメッセージが ^(feat|fix|refactor|docs|test|chore): にマッチ
```

## 実行プロセス

### Step 1: Eval定義の作成/読込

対象スキルのSKILL.mdを読み、テストケースを自動生成。
ユーザーが追加ケースを指定可能。

### Step 2: 実行

各テストケースを実行し、結果を記録:

```markdown
## Eval Results — YYYY-MM-DD

| ID | Result | Duration | Notes |
|----|--------|----------|-------|
| E1 | ✅ PASS | 3.2s | |
| E2 | ❌ FAIL | 5.1s | Expected X, got Y |
| E3 | ✅ PASS | 2.8s | |

### Metrics
- pass@1: 2/3 (66.7%)
- Total: 2 PASS, 1 FAIL
```

### Step 3: 分析と改善

FAIL したケースの根本原因を分析し、改善案を提示:
- スキル定義の修正提案
- エッジケースの追加
- ガードレールの強化

### Step 4: 結果保存

`${MEMORY_DIR}/memory/YYMMDD_<task>/eval-results.md` に保存。
過去のeval結果と比較して品質推移を追跡。

## `skill-stocktake`との連携

- `skill-stocktake`: スキルの**存在価値**を評価（keep/retire）
- `eval-harness`: スキルの**動作品質**を評価（pass/fail）
- 定期メンテナンス: stocktake → eval → 改善のサイクル
