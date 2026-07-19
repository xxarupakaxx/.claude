---
name: tdd
description: テスト駆動開発（Test-Driven Development）スキル。Red-Green-Refactorサイクルを厳格に運用し、テストを先に書いてから実装する。「TDDで進めて」「先にテスト書いて」「Red-Green-Refactor」「tddして」等の依頼時、または新規ロジック実装・バグ修正・リファクタの安全網が欲しい場合に使用。Phase 1で要件をテスト1個に変換、Phase 2でRed（失敗するテスト）、Phase 3でGreen（最小実装で通す）、Phase 4でRefactor（テストを通したまま設計改善）。詳細はreferences/tests.md・mocking.md・deep-modules.md・interface-design.md・refactoring.md参照。
allowed-tools: Read, Grep, Glob, Bash, Edit, Write
---

# Test-Driven Development

> Red → Green → Refactor を1サイクル30分以内で回す。

## CRITICAL: サイクルの厳守

TDDは「テスト先行」だけではない。次の **3フェーズを順に踏む** ことが本質:

1. **Red**: 失敗するテストを1つ書く（実装はまだない/不完全）
2. **Green**: テストを通す **最小限** のコードを書く（汚くてよい）
3. **Refactor**: テストを通したまま設計を改善する（緑のまま）

各フェーズの詳細ルールは references/ を参照:

| 関心事 | 参照 |
|-------|------|
| テスト粒度・命名・AAA | `references/tests.md` |
| Mock の境界・使いどころ | `references/mocking.md` |
| Deep Module を促す書き方 | `references/deep-modules.md` |
| Interface 設計とTDD | `references/interface-design.md` |
| Refactor フェーズの方針 | `references/refactoring.md` |

## Phase 1: 要件のテスト化

### 1.1 ToDo リスト

実装前に、観測可能な振る舞いを箇条書きで列挙:

```
- [ ] 空配列を渡すと 0 を返す
- [ ] 1要素なら要素自身を返す
- [ ] 負数を含むと InvalidInputError を投げる
- [ ] ...
```

このリストが**テストの設計図**。1項目=1テスト。

### 1.2 順序の選定

依存の少ない・自明なものから:
1. 最も単純な正常系（空入力、null、1件）
2. 主要な正常系
3. エッジケース
4. エラーケース

詳細: `references/tests.md`

## Phase 2: Red

### 2.1 失敗するテストを1つ書く

- 1サイクルで足すテストは **1つだけ**
- 「コンパイルエラー」も Red にカウント
- テスト名は「〜すべき」形式（`testing.md` ルール準拠）

### 2.2 失敗を確認

- 必ずテストランナーで赤を見る（書いただけで満足しない）
- 失敗メッセージが**意図通り**かを確認（別の理由で落ちていたら設計ミス）

## Phase 3: Green

### 3.1 最小実装

- 「最も汚い実装」で構わない（hard-code, if-else連発OK）
- 目的は **緑にすること** であり、設計ではない
- 「テストにないケースは実装しない」原則（YAGNI）

### 3.2 緑の確認

- 全テストを実行（既存テストの破壊回帰がないか確認）
- このタイミングで `git add -A && git commit` 推奨（緑状態を保存）

## Phase 4: Refactor

### 4.1 緑のまま改善

- テストを変更してはいけない（変更が必要なら別サイクル）
- 改善の判断軸は `references/refactoring.md` と `improving-architecture` スキル
- Deep Module を意識した内部整理（`references/deep-modules.md`）

### 4.2 テストの再実行

- リファクタの度にテスト実行（5秒以内が理想）
- 緑→緑を維持しているか毎回確認

## Phase 5: 次サイクルへ

ToDoから次の項目を選び、Phase 2へ戻る。
全項目が完了したら **CLAUDE.mdワークフロー Phase 4** へ合流（lint/typecheck/専門レビュー）。

## アンチパターン

- **Red をスキップ**: テストを書かずに実装→後でテスト追加
- **複数テスト同時追加**: 1サイクル1テストの原則違反
- **Refactor 中の機能追加**: テストを増やしながらリファクタ→赤が混入
- **Mock しすぎ**: 内部詳細をモックして実装変更で全テスト破綻（`references/mocking.md`）
- **System Boundary を Mock し忘れ**: DB/API/時刻/乱数を直叩き→フレーキー
- **テスト命名が手抜き**: `it("test1")` のような無意味な名前

## 関連スキル

- `improving-architecture`: Refactorフェーズの方針提供
- `brainstorming`、`designing-codebases`: 公開Interfaceの案と境界を確認してからTDD
- `diagnosing-bugs`: バグ修正TDD（最小再現テスト→修正）
