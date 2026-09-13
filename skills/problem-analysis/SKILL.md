---
name: problem-analysis
description: 本番障害、繰り返す問題、Kaizen の起点を、A3 で定式化し、Fishbone の6カテゴリと Iterative 5 Whys で根本原因候補と検証可能な action plan に整理する。「問題を分析して」「課題を整理して」「根本原因を探って」「problem-analysisして」で使う。単純なバグには使わない。
---

# Problem Analysis

問題を **定式化 → 原因仮説 → 根本原因の収束 → 行動計画** の順で整理する。これは built-in の `analyse-problem`、`cause-and-effect`、`why` を統合した上位スキルで、コード変更や単純な不具合の局所修正は行わない。

## 1. A3：観察可能な問題にする

`${MEMORY_DIR}/memory/<task>/problem_analysis.md` に、事実を中心に次を記す。

```markdown
# Problem: <タイトル>
## Background
## Current State
## Target State
## Gap
```

発生時期、範囲、頻度、影響、関連メトリクス、成功基準を、分かっている範囲だけ書く。`Current` と `Target` の差を短く表し、「動かない」「重い」などは観測方法や値で具体化する。

## 2. Fishbone：仮説を広げる

Gap に対して、関係するカテゴリだけを使い、無理に数を揃えない。

| Category | 観点 |
| --- | --- |
| Method | 手順・プロセス・workflow |
| Machine | tool・インフラ・hardware |
| Material | data・入力・依存 |
| Measurement | 計測・monitoring・log |
| Environment | 外部条件・タイミング・network |
| People | skill・communication・組織 |

この段階では仮説を事実と混同せず、根拠の有無と確認方法を添える。複雑な場合だけ SVG 図を添付する。

## 3. Iterative 5 Whys：収束する

Fishbone の候補から、影響、尤もらしさ、検証コストを見て最有力の1〜3候補を選ぶ。各回答が次の問いの根拠になる形で掘り、5回に満たなくても根拠が尽きたら止める。個人の責任で止めず、仕組み・環境要因まで確認する。根拠が薄い候補は別枝へ切り替え、根本原因を断定しない。

## 4. Action plan

分析結果に次を追記する。

```markdown
## Root Cause
<根拠と不確実性>
## Actions
| # | アクション | オーナー | 期日 | 検証方法 |
|---|---|---|---|---|
## Follow-up
```

各 action を原因に対応づけ、完了条件と再点検時期を含める。重要な設計判断は `creating-adr` へ渡す。

## 使い分け

- バグの再現・局所追跡：`diagnosing-bugs`
- 深いコールスタックの遡及：`root-cause-tracing`
- アーキテクチャ改善：`improving-architecture`
- Kaizen の問題定義・振り返り：この skill
