# ADR Criteria

> ADR (Architecture Decision Record) を**いつ書くべきか/書くべきでないか**の判断基準。

ADRは**コストのある成果物**。書きすぎると陳腐化し、書かなさすぎると判断が失われる。
**3条件すべて**を満たす判断のみADR化する。

## ADR を書くべき判断: 3条件

以下の **全て** を満たすときADR化する。

### 1. Hard to reverse（後戻りが困難）

変更コストが高い判断:
- DB スキーマの根本的な選択（RDB vs DocumentDB, 正規化方針）
- 公開API の仕様（後方互換性の制約を生む）
- 言語/フレームワーク選定
- 認証方式の根本選択（IdP委譲 vs 自前）
- データ保持・暗号化方針
- 通信プロトコル（REST vs gRPC vs GraphQL）

**判定**: 「後で変えるなら数日〜数週かかる？」 → YES なら hard to reverse

### 2. Surprising without context（背景なしには驚かれる選択）

「なぜこれを選んだか」を新メンバーに口頭で説明する必要がある判断:
- 一般的な選択肢を**敢えて避けた**判断
- 業界標準に**反する**選択
- 過去の失敗・組織制約・取引先要求などの**外部要因**による判断

**判定**: 「ドキュメントなしで読んだ人が『なぜ？』と思う？」 → YES なら surprising

例:
- ✅ 「Reactを使わずSvelte選定」: 一般的にはReactが安全牌、surprising
- ❌ 「TypeScriptでReactアプリ作る」: 自明、surprisingではない

### 3. Result of real trade-off（複数案の比較が実質的に行われた）

複数案を比較した上での判断:
- A案/B案/C案の3案以上を実際に検討した
- 各案のメリット・デメリットが明確
- 採用した1案の理由が **他案ではダメな理由** で説明できる

**判定**: 「捨てた案を3つ以上、その理由付きで挙げられる？」 → YES なら real trade-off

「他に選択肢を考えていない」=ADR化しても薄っぺらいので不要。

## ADR を書かないべきケース

### 1. 既知のベストプラクティスをそのまま採用

- 「パスワードはbcryptでハッシュ化する」
- 「APIキーは環境変数で管理する」
- 「N+1クエリを避ける」

→ ADRではなく `~/.claude/rules/` などのルール集に記録。

### 2. 戻せる判断

- ライブラリのマイナー選定（lodash vs ramda 程度）
- ファイル配置の慣習
- linter ルール

→ コードコメントやREADMEで十分。

### 3. 検討した形跡がない判断

- 「とりあえずこれにした」
- 「他の選択肢を知らない」

→ まず `grill-me`、`brainstorming`、`designing-codebases` で**実質的な検討**をしてからADR化を判断。

### 4. 議論中・暫定の判断

- 「次のスプリントで再評価予定」
- 「PoC段階」

→ memory ディレクトリの作業ノートで十分。Promote 時にADR化。

## 判定フロー

```
重要判断が確定？
  ↓
Hard to reverse？
  NO → コメント or rules/ に記録
  YES ↓
Surprising without context？
  NO → コメント or rules/ に記録
  YES ↓
Result of real trade-off？
  NO → grill-me / brainstorming / designing-codebases で検討してから再判定
  YES ↓
ADR化（creating-adr スキル）
```

## ADRの保存場所

`creating-adr` スキルのルールに従う:
- 作業中: `${MEMORY_DIR}/memory/<task>/adr/`
- Promote 時: PJ の `docs/adr/` または同等の永続的場所

## 関連

- `creating-adr` スキル: ADR作成のテンプレートと手順
- `grill-me` スキル: 重要判断の前にtrade-offを洗い出す
- `brainstorming`、`designing-codebases` スキル: 複数案の比較と境界設計
