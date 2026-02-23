---
name: lfg
description: "Phase 0-5.5を自律チェーン実行する自律ワークフロー。/lfg <タスクの説明> で使用。"
---

# LFG - Autonomous Workflow Orchestrator

`@context/workflow-rules.md` のPhase 0-5.5を自律的にチェーン実行する**薄いオーケストレータ**。

**IMPORTANT**: 各Phaseの詳細はworkflow-rules.mdに従うこと。このコマンドはPhaseの手順を複製しない。

## 使い方

```
/lfg <タスクの説明>
```

## オーケストレーション

workflow-rules.mdの各Phaseを順次実行し、各Phase間のゲート判定のみを担当する。

| Phase | 参照先 | ゲート |
|-------|--------|--------|
| 0: 準備 | `@context/workflow-rules.md` Phase 0 | AUTO |
| 1: 調査 | `@context/workflow-rules.md` Phase 1 | GO→AUTO / それ以外→USER |
| 2: 計画 | `@context/workflow-rules.md` Phase 2（deepening-plan + レビュー5ラウンド） | **USER（省略不可）** |
| 3: 実装 | `@context/workflow-rules.md` Phase 3 | AUTO（10+タスクは中間報告） |
| 4: 品質 | `@context/workflow-rules.md` Phase 4 | AUTO（指摘0でPASS） |
| 5: 完了 | `@context/workflow-rules.md` Phase 5 | AUTO |
| 5.5: Compound | `@context/workflow-rules.md` Phase 5.5 | AUTO（条件判定で実行/スキップ） |

## ゲート判定ルール

### AUTO-GATE（自動通過）
- Phase 0完了 → Phase 1へ
- GO/NO-GO = GO → Phase 2へ
- Phase 4で全レビューアーPASS → Phase 5へ
- Phase 5.5の自動トリガー条件を満たす → 実行

### USER-GATE（ユーザー確認必須）
- GO/NO-GO = CONDITIONAL / NO-GO / DEFER → ユーザーに報告
- Phase 2のUser Validation Gate → **絶対に省略しない**
- 10+タスクの中間報告

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
- エラーリトライが3回失敗した場合

## エラーハンドリング

- Phase内でエラー発生 → 自律リトライ（最大3回）
- 3回失敗 → ユーザーに報告し判断を仰ぐ
- Phase間では05_log.mdの更新を確認してから次へ進む
