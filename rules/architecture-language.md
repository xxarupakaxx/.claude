# Architecture Language

> John Ousterhout「A Philosophy of Software Design」の語彙を、CLAUDE設定全体で統一して使うための共通辞書。

設計に関する議論・レビュー・ADR・スキル間で**この用語を使う**ことで、認識のズレを減らす。

## 基本語彙

### Module（モジュール）

**定義**: 一定の責務を持つコードの単位。
- 言語によって粒度は異なる（クラス、関数、パッケージ、ファイル）
- 「外から見える形」と「中の仕組み」を持つ

### Interface（インターフェース）

**定義**: モジュールの利用者から見える形。**公開API**。
- メソッドシグネチャ、型、エラー仕様、不変条件
- 利用者が「知らなければならない情報」の総量
- **小さいほど良い**

### Implementation（実装）

**定義**: モジュールの内部の振る舞い。Interface の **実現方法**。
- 利用者は知らなくてよい情報
- 自由に変更できる領域（Interface が同じなら）

### Depth（深さ）

**定義**: `Implementation の量 ÷ Interface の量`。
- **多いほど良い**
- 小さなInterface で大きな機能を提供 = Deep
- 大きなInterface で小さな機能しか提供しない = Shallow

```
Deep:    [小さいInterface] ─── [厚いImplementation]
Shallow: [大きいInterface] ─── [薄いImplementation]
```

### Information Hiding（情報隠蔽）

**定義**: モジュール内部の決定を **外から見えなくする** 設計原則。
- データ構造の選択、アルゴリズム、外部ライブラリの選定など
- Information Hiding が強い = Depth が大きい
- 失敗すると **Information Leakage（情報漏れ）** となり、複数モジュールが同じ前提知識を持つことになる

### Seam（縫い目）

**定義**: 振る舞いを **差し替え可能** にする境界。
- テスト時に Fake/Mock に差し替えるための接合点
- DI（Constructor Injection）で作るのが一般的
- System Boundary（DB/API/時刻/乱数）には必ず Seam を入れる

### Adapter（アダプタ）

**定義**: 外部依存を **Seam で抽象化** する層。
- ライブラリ直接依存を散在させない
- ライブラリ更新時の影響範囲を限定
- Adapter Layer は薄く（Pass-through Wrapper にならないよう注意）

### Leverage（てこ）

**定義**: 1箇所の変更が **複数の改善** を生む構造。
- Leverage の高い変更を優先する（10ファイル直る変更 > 1ファイル直る変更）
- 共通基盤の改善は Leverage が大きい
- 局所最適化（特定ファイルのみ）は Leverage が小さい

### Locality（局所性）

**定義**: 関連する変更が **近い場所** に集まること。
- 「この変更を入れるためにどれだけのファイルを触る？」
- 多い = Locality 低 = Shotgun Surgery 兆候
- 少ない = Locality 高 = 良い設計

## 派生語彙

### Pull Complexity Downward

> 利用者の負担を減らすために、複雑性をモジュール内へ押し込む。

- 利用者からは「シンプル」に見えること優先
- 内部が複雑になっても OK
- 例: デフォルト値の埋め込み、Configuration Push-Down

### Configuration Push-Down

> 設定パラメータをデフォルト化し、公開Interfaceから外す。

- 利用者の99%は気にしない設定を表に出さない
- 残り1%向けには「上書き手段」を別途用意
- API表面の肥大化を防ぐ

### System Boundary

> 自分のコードと外部世界の境界。
- DB, 外部API, ファイルシステム, 時刻, 乱数, プロセス, ユーザー入力
- バリデーションが必要な唯一の場所（内部信頼）
- Mock すべき唯一の場所（テストにおいて）

### Tracer Bullet（垂直スライス）

> エンドツーエンドで動く最小実装を先に通し、その後肉付けする手法。

- 横方向（レイヤー全層実装）より縦方向（一機能を全レイヤー貫通）を優先
- 早期に統合リスクを発見
- TDD の Phase 1 と相性が良い

## 使用シーン

| シーン | この語彙を使う場面 |
|-------|-----------------|
| 設計議論 | 「Depth が浅いから Pull Complexity Downward しよう」 |
| コードレビュー | 「ここに Information Leakage があるので Seam を切ろう」 |
| ADR | 「Trade-off: Locality vs Configuration Push-Down」 |
| Refactor 計画 | 「対象モジュールのDepth評価 → Shallow なので統合候補」 |
| TDD 振り返り | 「Refactor フェーズで Deep Module へ昇華した」 |

## 関連

- `improving-architecture` スキル: この語彙を使った改善手順
- `tdd/references/deep-modules.md`: TDD文脈でのDeep Module
- `~/.claude/rules/common-patterns.md`: 推奨/アンチパターンとの対応
