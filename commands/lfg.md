---
name: lfg
description: "Phase 0-5 + Compoundを自律チェーン実行する自律ワークフロー。/lfg <タスクの説明> で使用。"
---

# LFG - Autonomous Workflow

Phase 0からCompoundまでを自律的にチェーン実行する。
ユーザーの介入を最小限にし、各フェーズのゲートを自動で通過する。

## 使い方

```
/lfg <タスクの説明>
```

## 実行フロー

### Sequential Phase（順次実行）

#### 1. Phase 0: 準備
- メモリディレクトリ作成（`${MEMORY_DIR}/memory/YYMMDD_<task_name>/`）
- 05_log.md初期化
- 関連する過去タスク・issueを`learnings-researcher`で検索

#### 2. Phase 1: 調査
- 過去知見の参照（`learnings-researcher`エージェント）
- コードベース調査（必要に応じて`exploring-codebase`スキル）
- 外部情報参照（Context7 / deepwiki / WebSearch から最低1つ）
- GO/NO-GO判定

**AUTO-GATE**: GO判定の場合は自動で次へ。CONDITIONAL/NO-GO/DEFERの場合はユーザーに確認。

#### 3. Phase 2: 計画
- 30_plan.md作成（4ステップ構造）
- `/deepening-plan` で計画の深掘り
- サブエージェント並列レビュー（5ラウンド制）

**USER-GATE**: 計画をユーザーに提示し承認を得る（これは省略不可）

#### 4. Phase 3: 実装
- 各タスクを「調査→計画→実行→レビュー」で実行
- こまめにコミット
- 10+タスクの場合は中間報告

#### 5. Phase 4: 品質確認
- lint/format/typecheck/test実行
- サブエージェント並列レビュー（5ラウンド制）
- 指摘がなくなるまでループ

#### 6. Phase 5: 完了報告
- 実装サマリー
- 自律決定事項
- ブランチ名
- 残存課題

#### 7. Phase 5.5: Compound（自動提案）
- `/compounding-knowledge` で知見を構造化保存
- 保存すべき知見がない場合はスキップ

## 自律判断ルール

### 自動で進めてよい判断
- ライブラリの選択（既存コードベースと同じもの）
- ファイル配置（既存の規約に従う）
- テストの追加
- リファクタリングの範囲（変更に直接関連するもの）

### ユーザーに確認が必要な判断
- 既存APIの破壊的変更
- 新しいライブラリの導入
- アーキテクチャの変更
- Phase 2の計画承認（必須）
- GO/NO-GOがGO以外の場合

## 注意事項

- Phase 2のUser Validation Gateは**絶対に省略しない**
- 各Phaseで05_log.mdを更新する（通常フローと同じ）
- エラーが発生した場合は自律リトライ（最大3回）→ユーザーに報告
- ワークフロー全体のPhase 0-5ルール（`@context/workflow-rules.md`）に準拠
