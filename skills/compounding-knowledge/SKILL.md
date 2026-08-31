---
name: compounding-knowledge
description: |
  解決済み問題・知見を構造化ドキュメントとして自動キャプチャし、
  solutions/に保存するCompound Engineeringスキル。
  タスク完了後（Phase 5後）に使用。
  「知見を保存して」「解決策を記録して」「compoundして」等の依頼に対応。
  memories/のインデックスより詳細な、再利用可能なソリューションドキュメントを生成。
  **技術調査で得た知見（SDK API発見、ライブラリ挙動、設計パターン等）も
  solutions/technical-learnings/ に保存する。**
---

# Compounding Knowledge

解決済み問題**および技術調査で得た知見**を構造化ドキュメントとして保存し、将来の開発を加速させる。

## トリガー

### 自動トリガー（プロアクティブに実行を提案）
- **Phase 5.5**: `@context/workflow-rules.md` Phase 5.5の条件を満たす場合
- **デバッグ成功時**: エラーを調査・解決した後（「直った」「解決した」「原因がわかった」等）
- **ADR作成後**: `creating-adr`スキルでアーキテクチャ決定を記録した場合（ADRの内容をsolutions/architecture-decisions/にも変換）
- **レビューで再発パターン検出時**: auto-reviewing-pre-prで過去と同じ指摘が繰り返された場合

### 手動トリガー
- ユーザーが明示的に実行（`/compounding-knowledge`）
- 「知見を保存して」「解決策を記録して」「compoundして」等の発言

## 実行フロー

### Step 1: 情報収集 & 知見タイプ判別

05_log.mdと関連ファイルを読み取り、以下の**2種類の知見**を特定:

#### タイプA: Solution（問題解決パターン）
- 何が問題だったか → どう解決したか → なぜその解決策を選んだか
- 保存先: `solutions/<category>/`

#### タイプB: Technical Learning（技術調査知見）
- Phase 1-2でSDK/ライブラリ/APIを調査して得た発見
- 計画・実装に影響を与えた技術的な知見
- 例: 「AI SDK onStepFinishでツール呼び出しをフックできる」「AsyncLocalStorageでリクエストスコープを伝播できる」
- 保存先: `solutions/technical-learnings/`

**判別基準**: 「問題→原因→修正」の流れがあるか（→Solution）、「調査→発見→活用」の流れか（→Technical Learning）。1つのセッションで両方存在することが多い。

### Step 2: 根拠と状態の確認

固定人数の並列起動や特定のAgent APIは前提にしない。次の観点を、`context/agent-team-routing.md` のGateを満たし独立確認の利益がある場合だけAgent()へ分担し、そうでなければ一つの担当が順に確認する。新しい横断監査の責務をこのSkillへ追加しない。

#### 2-1: Solutionの確認
```
05_log.mdとdiffを分析し、以下を抽出:
- root_cause: 根本原因（1-2文）
- solution: 実際に適用した解決策の具体的手順
- code_changes: 主要なコード変更のサマリー
```

問題、原因、修正、直接検証がそろわない場合は、Solutionとして解決済みと保存しない。mock、静的検査、単発の通知や構文成功を実運用の成功に広げない。

#### 2-2: 再発条件の確認
```
この問題の再発を防ぐための戦略を提案:
- prevention: 予防策のリスト
- detection: 早期発見方法
- related_patterns: 類似問題のパターン
```

#### 2-3: 保存先の確認
```
solutions/の既存カテゴリを確認し、最適なカテゴリとファイル名を決定:
- category: solutions/下のサブディレクトリ名
- filename: kebab-caseのファイル名（.md）
既存カテゴリ: performance-issues, security-issues, runtime-errors,
build-issues, architecture-decisions, database-issues, integration-issues
新カテゴリの作成も可。
```

保存先の決定は既存Skillの責務比較を含める。個別の採用・更新・runtime反映は `skill-governance` へ送り、ここで代行しない。

#### 2-4: 関連根拠の確認
```
関連する外部ドキュメント・GitHub Issue・Stack Overflowの記事を検索:
- references: 関連URLのリスト
- related_solutions: solutions/内の関連ドキュメント
```

外部資料を使う場合は、主張ごとに一次資料のidentity、取得日、版、適用範囲を記録する。二次資料や検索結果だけで現行仕様を確定しない。必要な資料を全文確認できない場合は `unverified` として残す。

#### 2-5: 技術知見の昇格ゲート

コード例、SQL、設定、性能・安全性の主張を保存する前に、少なくとも次を主張ごとに分けて記録する。

- 一次根拠（公式仕様、公式source、または再現可能な実験）と、対応する引用・検証範囲
- 版、取得日、適用範囲、前提条件
- 反例・限界（確認できたもの。なければ「確認済み範囲に反例未確認」と記載）、既知のconsumer/runtime差分
- 実装・本番runtimeでの確認状態、未確認事項、再検証条件

一次根拠、版、適用範囲、または反例・限界の確認状態のいずれかが記録されていない技術主張は、調査中のTechnical Learningとしてのみ保持する。反例が見つからないことを反例がない証明とせず、存在しない反例を創作しない。`confidence: experimental` または `theoretical`、未検証の実装例は、Skill、policy、現行runbookへ昇格させず、根拠がそろうまで保留する。保存済みKnowledgeと採用済み手順を同一視しない。

### Step 3: ドキュメント生成

確認結果を統合し、知見タイプに応じたテンプレートでドキュメントを生成:

#### タイプA: Solution テンプレート

```markdown
---
title: "問題のタイトル"
problem_type: "bug|performance|security|architecture|integration|build|database"
component: "影響を受けたコンポーネント"
tags: [tag1, tag2, tag3]
phases: [planning, implementation, quality-check]  # REQUIRED: この知見が活きるPhase群
root_cause: "根本原因の1行サマリー"
solution_summary: "解決策の1行サマリー"
created: YYYY-MM-DD
severity: "critical|major|minor"
effort: "small|medium|large"
evidence_status: "verified|partial|unverified"
source_refs: ["一次根拠または実行記録"]
source_version: "版、commit、または取得日時"
applicability: "適用範囲と前提"
counterexamples: ["反例または限界。なければ確認済み範囲に反例未確認と記載"]
unknowns: ["未確認のruntime・consumer条件"]
promotion_status: "hold|candidate|approved"
---

# [タイトル]

## 問題
[問題の詳細な説明]

### 症状
- 具体的な症状1

### 根本原因
[root_causeの詳細説明]

## 解決策

### 手順
1. ステップ1

### コード変更
[主要な変更のハイライト]

## 予防策
- 予防策1

## 参考情報
- 関連ソリューション: [solutions/内のパス]
```

#### タイプB: Technical Learning テンプレート

```markdown
---
title: "発見・知見のタイトル"
learning_type: "api-discovery|library-behavior|design-pattern|integration-technique|performance-insight"
source: "調査元（Context7/deepwiki/公式ドキュメント/実験等）"
source_version: "版または取得日時"
component: "適用先コンポーネント"
tags: [tag1, tag2, tag3]
phases: [investigation, planning]  # REQUIRED: この知見が活きるPhase群
discovery_summary: "発見の1行サマリー"
applied_in: "この知見を適用したコミットやファイル"
created: YYYY-MM-DD
confidence: "verified|experimental|theoretical"
applicability: "適用範囲と前提"
counterexamples: ["反例または限界。なければ確認済み範囲に反例未確認と記載"]
unknowns: ["未確認のruntime・consumer条件"]
promotion_status: "hold|candidate|approved"
---

# [タイトル]

## 発見

[何を調べて何がわかったか]

### 背景・動機
- なぜこれを調べたか（どんな課題を解決しようとしていたか）

### 調査結果
[具体的な発見内容。コード例を含む]

## 活用パターン

### 適用方法
[この知見をどう実装に活かしたか]

### コード例
[実際のコードまたは最小限の例]

## 注意点・制約
- 既知の制限やエッジケース

## 参考情報
- [公式ドキュメントURL等]
```

### Step 4: 提案 & ユーザー承認（IMPORTANT）

Technical Learningの保存、Solutionの保存、Skillやruntimeへの採用は別状態で記録する。既存の承認が対象と影響を含む同じ範囲の可逆なローカル保存について、段階ごとの一律な再承認を追加しない。対象・影響を広げる外部write、不可逆操作、runtime反映は別の具体的な承認ゲートへ戻す。

**承認前のEdit禁止ポリシー**: 承認前にknowledge管理ファイルへ直接書き込まない。対象と影響を含む既存承認または新しい承認を確認した後は、宣言済みscope内のWriteを許可する。外部write、不可逆操作、runtime反映は別の具体的な承認ゲートへ戻す。

1. 既存の承認が対象・操作・差分を含む場合は、そのdecision IDとscopeを記録して提案をその承認へ結び付ける。それ以外は**生成したドキュメントを提案として表示**する。
   ```markdown
   ## 保存提案

   **保存先**: `${MEMORY_DIR}/solutions/<category>/<filename>.md`

   ---
   [生成したドキュメント全文]
   ---
   ```

2. 承認が不足している場合だけ、**AskUserQuestionで承認を取得**する。
   - 「このまま保存」
   - 「修正して保存」（修正点を入力）
   - 「保存しない」

3. 新しい承認または既存承認の範囲を確認した後、**Writeツールで保存**する。
   - 保存後、`index.json`に新規エントリを追加（ref_count: 0）

4. 必要に応じて `memories/` にもインデックスを作成する。既存承認または新規承認のscopeを記録し、同じ対象・影響への一律な再承認は追加しない。

## solutions/ ディレクトリ構造

```
${MEMORY_DIR}/
├── solutions/                    # 構造化ソリューション & 知見DB
│   ├── performance-issues/
│   ├── security-issues/
│   ├── runtime-errors/
│   ├── build-issues/
│   ├── architecture-decisions/
│   ├── database-issues/
│   ├── integration-issues/
│   └── technical-learnings/      # 技術調査知見（API発見、ライブラリ挙動等）
├── memories/                     # インデックス層（既存）
└── memory/                       # タスクログ（既存）
```

## 検索との連携

保存されたソリューション・技術知見は `learnings-researcher` エージェントが検索可能。
YAML frontmatterの各フィールド（title, tags, root_cause/discovery_summary, component, problem_type/learning_type）が
grep対象となるため、フィールドは正確に記入すること。
