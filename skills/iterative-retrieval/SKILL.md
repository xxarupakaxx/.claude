---
name: iterative-retrieval
description: 初回検索の不足を評価し、未解決の問いに合わせた追加検索で調査コンテキストを段階的に精製する。learnings-researcher、exploring-codebase、サブエージェントへ渡す情報が足りないときに使う。
---

# Iterative Retrieval

一度に全情報を集めようとせず、検索結果から残る問いを明示し、その問いに必要な範囲だけ追加調査する。十分な根拠が揃ったら止める。調査対象・時間・round 数の上限が必要な場合は先に決め、既定では最大3 round を目安にする。

## ループ

各 round で次を記録する。

1. 見つかった事実と根拠
2. まだ不明な点
3. 次に確認するキーワード、path、または別の手法
4. その調査で不確実性が減るか

### Round 1：広く把握

`Grep` で関連語を探し、`Glob` で構造を確認する。必要なら `memories/solutions/` を横断する。

### Round 2：対象を深く読む

Round 1 で特定した file/module の関数定義、型、test、import/require 先を読む。意図の確認に必要な場合だけ `git log` / `git blame` を見る。

### Round 3：不足が残るとき

不足の種類に応じて WebSearch、deepwiki、Context7、AskUserQuestion、または仮説を立てたコード検証を選ぶ。外部検索や質問を必須にせず、不要ならそこで終了する。

## 出力

各 round の発見、根拠、残る不明点、採用した次の検索と、十分と判断した理由を短く返す。推測は仮説として明記する。

サブエージェントへ渡す場合は、対象と目的、検索語、調べる順序、結果・残課題だけを返す形式を指定する。`explorer` には「広く検索 → 関連 file を深読 → 不足時だけ追加検索」の順序を渡す。

`learnings-researcher` の関連度が低いときは、タグ・カテゴリ、`root_cause` / `component`、同じ framework など、残った問いに対応する軸だけを追加する。
