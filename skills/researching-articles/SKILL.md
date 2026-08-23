---
name: researching-articles
description: URLや記事・ドキュメントを受け取り、周辺コンテキスト（関連リポジトリ・仕様書・比較技術）まで調査して、10年後の新人でも理解できる詳細なknowledgeノートをInbox/knowledge/に作成し、検証後にone-page-concept-sketchを生成する。「詳しく調べて」「ノートにして」「周辺コンテキストも拾って」「深掘りして」「わかりやすくまとめて」等のフレーズで使用。captureの深掘りモードとして機能する。
---

# URL深掘り調査 → Knowledgeノート作成

URLを受け取り、記事本文だけでなく周辺コンテキストまで調査して、「10年後の新人でも理解できる」knowledgeノートを作成する。

captureスキルの軽量URL処理（3行要約 + 箇条書き）とは異なり、**原理・背景・比較・落とし穴**まで掘り下げることが目的。

## トリガー条件

以下がともに揃っているとき：
- URL（1つ以上）が提示されている
- 「詳しく」「深掘り」「ノートにしておいて」「周辺コンテキストも」「わかりやすく」「まとめておいて」のフレーズ

単なる「読んだ」「要約して」は captureスキルに任せる。

## フロー

### Step 1: japanese-tech-writing 規範の確認

書き始める前に `/japanese-tech-writing` スキルを参照し、文章規範を頭に入れる（CLAUDE.mdの必須ルール）。

### Step 2: 記事本文の取得（並列）

URLが複数あれば WebFetch で並列取得する。

- 通常のWebページ：そのままWebFetchへ
- GitHubのblobURL（`github.com/.../blob/...`）：`raw.githubusercontent.com` に変換してから取得
- 認証必須ページ：`[!] 取得不可 — ログイン必要` としてbacklogに記録し、スキップ

### Step 3: 周辺コンテキストの調査（research）

`research` スキルを使い、URLの性質に応じて調査対象を選ぶ。
一次情報、公式ドキュメント、仕様、ソースコードを優先し、重要な主張ごとに出典URLを残す。

| URLの種類 | 調査対象 |
|----------|---------|
| GitHubリポジトリ | README・仕様書（SPEC.md等）・コアとなるソースファイル |
| 技術記事・ブログ | 公式ドキュメント・関連リポジトリ・比較技術の記事 |
| 仕様書・RFCクラス | 参照実装・既知の問題（GitHub Issues）・類似仕様との比較 |

**research に渡す調査プロンプトの骨格：**

```
このドキュメントの内容を全文できるだけ詳細に抽出してください。
概要、技術的な仕組み、設計思想、使い方、制限・落とし穴、
他技術との比較など、10年後の新人でも理解できるよう詳しく。
```

周辺コンテキストの具体的な調査先を判断する指針は `references/research-targets.md` を参照。

### Step 4: ノートの作成（並列）

トピックが複数あれば並列で書く。`Inbox/knowledge/<タイトルベースのファイル名>.md` に新規作成。

**frontmatter：**

```yaml
---
title: <技術名・概念名>
date_created: <YYYY-MM-DD>
type: knowledge
tags: [関連タグ（英小文字）]
summary: "<何がわかるノートかを1行で。: を含みやすいので必ず引用符で囲む>"
depth: overview
url: <元URL>
as_of: <時間で変わる情報（料金・仕様・モデル名等）を含む場合のみ、確認日 YYYY-MM-DD>
related: ["[[関連ノートやMOC]]"]
---
```

本文の構成は `references/note-structure.md` を参照。
フィールド定義は CLAUDE.md「セカンドブレイン拡張フィールド」に従う。AI/エージェント系のノートは [[AI-Agent-MOC]] の該当クラスタに1行追記して双方向にする。

**図の活用（SVG）**：技術的な仕組み、処理flow、architecture、比較は、図にした方が理解しやすい場合に自己完結したSVGで図示する。SVGは `attachments/` に保存し、Obsidianの本文から埋め込む。Mermaidは新規生成しない。

| 用途 | SVG表現 |
|------|-----------|
| 処理flow、pipeline | label付きnodeと有向edge |
| component間のやり取り | 左から右へ進むsequence |
| 状態遷移 | 状態node、開始と終了、条件付きedge |
| architecture、構成要素の関係 | system groupと関係edge |

### Step 5: デイリーへのリンク追記

今日のデイリーノート `Daily/YYYY-MM-DD.md` を確認し：
- `## 💭 メモ` 配下に元URLがあれば、その行直下に `    - → 整理済み [[ノート名]]` を追記
- `## 🔗 今日のノート` がある場合はそこにも `[[ノート名]]` を追記

### Step 6: Knowledgeノートの検証

Vaultルートで `ruby _shared-ai/scripts/validate-vault-knowledge.rb` を実行する。
FAILがあれば同じ作業内で修正して再実行し、PASSするまで次へ進まない。

### Step 7: one-page-concept-sketch（直列）

Knowledgeノートの保存、Dailyリンク、Step 6の検証が完了した後に `$one-page-concept-sketch` を実行する。

1. `.codex/skills/one-page-concept-sketch/SKILL.md` を正本として全文読み、最新のVault Output ContractとQuality Checkに従う。
2. 完成したKnowledgeノートを入力にし、複数ノートを作成した場合は1ノートにつき1件のスケッチを作る。
3. source-based summaryとしてExact Board modeを既定にし、lane名は `researching-articles` とする。ImagegenまたはDualはユーザーが明示した場合だけ使う。
4. Source Coverageには元URL、周辺調査の根拠、中心主張、仕組み、制限を引き継ぐ。スケッチ段階で新しい事実を推測して追加しない。
5. 保存先、版管理、source noteとDailyへのリンクは`one-page-concept-sketch`の正本に委譲する。
6. Markdownノート、Exact Board PNG、全wikilinkの実在確認が終わるまで調査タスク全体を完了扱いにしない。生成できない場合は、壊れたリンクを残さず未完了理由を報告する。

## 品質チェック

ノートを書き終えたら以下を自問する：

- [ ] 「なぜこれが存在するか」が読んでわかるか
- [ ] 技術的な仕組みを原理から説明しているか（「こうなっている」だけでなく「なぜこうなっているか」）
- [ ] 他技術と何が違うかを書いているか
- [ ] 既知の制限・落とし穴を書いているか
- [ ] LLMっぽい空虚な表現（「重要なのは」「掘り下げる」）を使っていないか（japanese-tech-writing規範）
- [ ] flow、architecture、比較など図にした方が分かりやすい箇所にSVGを使っているか
- [ ] 作成したKnowledgeノートごとにconcept sketchが1件あり、source noteとDailyから辿れるか
- [ ] Exact Boardだけで主題、中心主張、仕組み、次の判断、望ましい終点、重要な制限を説明できるか
- [ ] 埋め込んだ画像wikilinkが実在するPNGへ解決するか

## ガード

CLAUDE.mdの絶対ルールに従う：
- ファイル名は変えない
- 新規ノートは `Inbox/` 配下に作成
- 既存ノートへの大幅な書き換えは禁止（追記のみ）
- frontmatterを壊さない（値に `: ` を含む場合は `"..."` で囲む）
