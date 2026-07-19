---
name: software-architecture
description: Clean Architecture + DDD 観点での重要アーキテクチャ判断スキル。新システム設計、ドメインモデリング、レイヤー境界の決定、ライブラリファースト判断時に使用。「アーキテクチャを設計して」「ドメイン分離して」「Clean Arch で」等の依頼時に起動。日常的なコード品質チェックは rules/architecture-language.md / common-patterns.md / common-coding-style.md を参照（本スキルとは別経路）。
---

# Software Architecture — Clean Architecture + DDD

重要なアーキテクチャ判断時の参照スキル。
**日常的なコーディング規約** ではなく、**新システム設計** / **ドメインモデリング** / **境界決定** に使う。

## 使用シーン

| シーン | 本スキル | rules/ |
|--------|---------|--------|
| 新システムのアーキ選定 | ✅ | - |
| 既存システムの大規模リファクタ方針 | ✅ | improving-architecture と併用 |
| ドメイン分離 / 集約境界の決定 | ✅ | modeling-domains と併用 |
| ライブラリ vs カスタム実装の判断 | ✅ | search-first と併用 |
| 日常的なネスト深さ・命名・型付け | - | rules/common-coding-style.md |
| パターン適用 (DIP/Repository等) | - | rules/common-patterns.md |
| 設計語彙 (Module/Depth/Seam等) | - | rules/architecture-language.md |

## 中核原則

### 1. ライブラリファースト
カスタムコードを書く前に必ず既存ソリューションを検索:
- Context7 で最新ライブラリ docs 確認
- npm / PyPI で既存ライブラリ評価
- 既存 SaaS / API を検討

カスタムが正当化されるケース:
- ドメイン固有のビジネスロジック
- 既存ライブラリが要件を満たさない (要評価)
- 外部依存が過剰になる場合

### 2. Clean Architecture + DDD
- ドメインエンティティをインフラから分離
- ビジネスロジックをフレームワークから独立
- ユースケース境界を明確に
- 共有されたドメイン言語に従う（詳細: `modeling-domains` skill）

### 3. ドメイン固有の命名
- ❌ 汎用: `utils`, `helpers`, `common`, `shared`
- ✅ 具体: `OrderCalculator`, `UserAuthenticator`, `InvoiceGenerator`

### 4. 関心の分離
- ビジネスロジック ≠ UI コンポーネント
- DB クエリ ≠ コントローラ
- 境界づけられたコンテキストの分離

## アンチパターン

- **NIH (Not Invented Here)**: Auth0/Supabase があるのに自前認証 / Redux/Zustand があるのに自前状態管理
- **God Module**: 50個の無関係関数を含む `utils.js`
- **Layer Mixing**: ビジネスロジックと UI の混在 / コントローラ内 DB 直接アクセス

## 関連スキル

- `improving-architecture`: 既存コードのアーキテクチャ改善 (Ousterhout Deep Module)
- `brainstorming`、`designing-codebases`: インターフェース案の比較と境界設計
- `modeling-domains`: ドメイン用語と境界の整理
- `creating-adr`: 重要判断の記録

## 関連ルール

- `~/.claude/rules/architecture-language.md`: 設計語彙 (Module/Depth/Information Hiding/Seam/Leverage)
- `~/.claude/rules/common-patterns.md`: 推奨パターン / アンチパターン
- `~/.claude/rules/common-coding-style.md`: コーディング規約
