---
name: search-first
description: "コード実装前にnpm/PyPI/GitHub/MCP/既存スキルを検索し、既存ツールがあれば利用を推奨する「車輪の再発明防止」スキル。brainstormingやPhase 1の調査で併用。"
---

# Search First — 既存ツール優先ワークフロー

## 概要

新しいコードを書く前に、既存のライブラリ・ツール・パターンを徹底的に検索する。
「自分で書く」は最後の選択肢。

## トリガー

- 新しいユーティリティ関数の実装を開始しようとした時
- 「〇〇する機能を作って」と依頼された時
- Phase 1（調査）で技術選定を行う時
- `/search-first <実装したいこと>`

## 検索パイプライン

### Step 1: ローカル検索（並列）

以下を**同時に**検索:

| 検索先 | 方法 |
|--------|------|
| **プロジェクト内** | Grep/Globで既存実装を検索 |
| **既存スキル** | `~/.claude/skills/`で類似スキルを確認 |
| **既存エージェント** | `~/.claude/agents/`で関連エージェントを確認 |

### Step 2: 外部検索（並列）

| 検索先 | 方法 | 対象 |
|--------|------|------|
| **パッケージレジストリ** | WebSearch | npm, PyPI, crates.io, pkg.go.dev |
| **GitHub** | WebSearch | 類似のOSSライブラリ・ツール |
| **公式ドキュメント** | Context7/deepwiki | フレームワーク組み込み機能 |

### Step 3: 評価マトリクス

見つかった候補を以下で評価:

```markdown
## 候補比較

| 候補 | メンテ状態 | 人気度 | サイズ | 適合度 | 判定 |
|------|-----------|--------|--------|--------|------|
| libraryA | ✅ active | ⭐ 5k | 50KB | 90% | **ADOPT** |
| libraryB | ⚠️ 6mo ago | ⭐ 1k | 200KB | 70% | CONSIDER |
| 自作 | - | - | ~20行 | 100% | LAST RESORT |
```

### Step 4: 判定

| 判定 | 基準 | アクション |
|------|------|-----------|
| **ADOPT** | 適合度80%+、メンテナンス活発 | そのまま導入 |
| **EXTEND** | 適合度60%+、カスタマイズ可能 | フォーク/ラッパーで拡張 |
| **BUILD** | 適合候補なし、または全て不適合 | 自作（ただし理由を記録） |

## 検索すべきタイミング

### 必ず検索
- 日付/時刻操作（date-fns, dayjs, luxon）
- バリデーション（zod, yup, joi）
- HTTP通信（ky, got, ofetch）
- 状態管理（zustand, jotai, valtio）
- テストユーティリティ（testing-library, msw）
- CLI解析（commander, yargs, citty）

### 検索不要（自作OK）
- プロジェクト固有のビジネスロジック
- 10行以下の単純なヘルパー
- 既存ライブラリの薄いラッパー

## `brainstorming`との関係

- `brainstorming`: **何を作るか**の設計探索
- `search-first`: **既にあるか**の存在確認
- 推奨フロー: search-first → brainstorming（既存がなければ設計へ）
