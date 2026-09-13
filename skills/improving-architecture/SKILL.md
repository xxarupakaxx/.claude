---
name: improving-architecture
description: 既存コードのアーキテクチャを read-only で調査し、Deep Module・Deletion Test・Seam・Localityに基づく改善案と実装引継ぎを作るスキル。「アーキテクチャを改善して」「設計が複雑」「リファクタ方針を決めたい」など、設計判断が必要な依頼で使う。実装、ADR作成、commitは別の明示された作業へ引き継ぐ。
allowed-tools: Read, Grep, Glob, Bash, Edit, Write, Task
---

# Improving Architecture

> "The best modules are deep: they have powerful functionality yet simple interfaces." — John Ousterhout

## CRITICAL: 用語の統一

このスキルでは `~/.claude/rules/architecture-language.md` の語彙を使う。
全ての分析・提案で以下の用語を一貫して使用すること:

- **Module（モジュール）**: 一定の責務を持つコード単位
- **Interface（インターフェース）**: 利用者から見える形（公開API）
- **Implementation（実装）**: モジュール内部の振る舞い
- **Depth（深さ）**: `Implementation の量 / Interface の量`。多いほど良い
- **Seam（縫い目）**: 振る舞いを差し替え可能にする境界
- **Adapter（アダプタ）**: 外部依存を Seam で抽象化する層
- **Leverage（てこ）**: 1箇所の変更が複数の改善を生む構造
- **Locality（局所性）**: 関連する変更が近い場所に集まること

## Phase 1: スコープの限定

### 1.1 対象モジュールの選定

「コードベース全体を改善」は禁止。1回のセッションでは:
- 1〜3モジュール、または
- 1つの貫通する関心事（例: エラーハンドリング、認証フロー）

ユーザーに対象を確認する（曖昧なら `AskUserQuestion`）。

### 1.2 現状の把握

`exploring-codebase` スキルまたは `explorer` サブエージェントで:
- 対象モジュールの公開API（=Interface）を列挙
- 呼び出し箇所を全て洗い出し（Leverageの規模を把握）
- 内部の依存関係を確認

## Phase 2: Shallow / Deep の判定

### 2.1 Depth の評価

各モジュールについて:

| 観点 | Shallow（浅い） | Deep（深い） |
|------|---------------|------------|
| Interface | 大きい（多メソッド・多パラメータ） | 小さい（少数の入口） |
| Implementation | 薄い（パススルー、薄いラッパー） | 厚い（複雑な内部処理を隠蔽） |
| 利用者の負担 | 高い（多くを知る必要） | 低い（数行で使える） |
| Information Hiding | 弱い | 強い |

**典型的なShallow Moduleのサイン**:
- `getX / setX` が並ぶだけのDTO相当
- 関数本体が1-2行のラッパー
- 引数を増やすたびに利用箇所も全て修正必要
- 複数モジュールが同じ実装詳細を知っている

### 2.2 Information Leakage の検出

```sh
# 同じimport群が複数ファイルで繰り返される=情報漏れの兆候
rg "^import.*from '@/foo/internals'" --count-matches
```

複数モジュールに **共通の前提知識** が必要なら、その知識を1箇所に集約する候補。

## Phase 3: Deletion Test

### 3.1 削除テスト

各モジュールについて自問:

> **「このモジュールを削除し、呼び出し側に直接書き戻したら、どうなるか？」**

| 結果 | 判定 |
|------|-----|
| 呼び出し側でほぼ同じコードを書き直すことになる | **Shallow** → 統合候補 |
| 呼び出し側が爆発的に複雑化する | **Deep** → 維持 |
| 呼び出し側が単純化される | **Premature Abstraction** → 統合候補 |

### 3.2 統合 vs 分割の判断

- Shallowが連続している → **統合**（隣接Shallow Moduleをまとめる）
- 1つのDeep Moduleが多責務 → **分割**（Information Hidingの軸で切る）

## Phase 4: 改善案の提示

### 4.1 改善パターン

| パターン | 内容 | 適用条件 |
|---------|------|---------|
| **Pull Complexity Downward** | 利用者の負担を減らすため複雑性をモジュール内へ | Shallow検出時 |
| **Extract Seam** | 外部依存（DB/API/時刻）を差し替え可能に | テスタビリティ低い時 |
| **Adapter Layer** | 外部ライブラリを薄いラッパーで包む | ライブラリ直接依存が散在 |
| **Locality Restoration** | 関連する変更を1箇所に集める | Shotgun Surgery発生時 |
| **Configuration Push-Down** | 設定パラメータをデフォルト化し公開Interfaceから外す | API表面が肥大化時 |

### 4.2 提案フォーマット

各改善案は以下を明示:

```markdown
### 提案 N: [パターン名] - [対象モジュール]

**現状**: [Shallow/Information Leakage/etc]
**Depth評価**: Interface行数 X / Implementation行数 Y → 比 Y/X = Z（目標: >5）

**変更**:
- Before: [現在のInterface]
- After: [変更後のInterface]

**Leverage**: この変更により改善される箇所 N 個（[ファイル列挙]）

**Trade-off**:
- メリット: [Locality/Depth向上等]
- デメリット: [移行コスト等]
- リスク: [後方互換性等]
```

### 4.3 必要な場合だけ複数案を比較

非自明な改善だけ、`brainstorming` で案を比較し、`designing-codebases` で境界とinterfaceを評価する。各Skillが使えない場合は、その欠落を記録して自分の証拠と推論を分ける。

## Phase 5: ADR化（重要判断時のみ）

`~/.claude/rules/adr-criteria.md` の3条件を確認:
1. **Hard to reverse**（後戻りが困難）
2. **Surprising without context**（背景なしには驚かれる選択）
3. **Result of real trade-off**（複数案の比較が実質的に行われた）

3つ全てを満たすなら `creating-adr` スキルでADR化。

## Phase 6: 段階的適用

### 6.1 実装への引継ぎ

- 大きなリファクタは小さな論理単位へ分ける案として提示する。
- 変更対象、移行順、互換性、必要な検証を明記し、実装者へ渡せる状態にする。
- コード、設定、ADR、issue、commitはこのSkillの実行中に変更しない。

### 6.2 検証

現状の証拠を取得する範囲で、既存のlint/format/typecheck/test結果や再現手順を確認する。未実行の検証を実行済みと扱わず、必要な検証を引継ぎに列挙する。専門reviewerは設計判断の不確実性と影響に応じて選ぶ。

## アンチパターン

- **抽象化のための抽象化**: Depth評価せず層を増やす
- **Premature Generalization**: 「将来使うかも」で柔軟性追加（YAGNI違反）
- **Pattern-First Design**: 「Strategyパターンを使いたい」が先に立つ
- **Big Bang Refactor**: 一気に全体書き換え→テスト失敗→巻き戻し
- **Information Leakage の放置**: 共通前提を複数モジュールに分散させたまま

## 関連スキル

- `brainstorming`、`designing-codebases`: 複数案の比較と境界設計
- `creating-adr`: 重要判断のADR化
- `refactoring-advisor`（agent）: 局所的なリファクタ提案
- `software-architecture`: アーキテクチャ全般のガイド
- `techdebt`: 重複・負債の検出
