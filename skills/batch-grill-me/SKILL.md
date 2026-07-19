---
name: batch-grill-me
description: 設計treeの現在のfrontierにある質問を一問ずつではなくround単位でまとめて聞く実験的interview。`/batch-grill-me` と明示されたときだけ使う。
disable-model-invocation: true
---

# Batch Grill Me

> Status: in-progress
>
> 安定版の既定経路は `grill-me` と `grilling` です。
> 一度に複数の質問へ答えたいと利用者が明示した場合だけ使います。

共有理解に達するまで、設計treeをround単位でたどります。

**Frontier** は、前提がすでに確定し、推測せず今すぐ質問できる判断の集合です。

各roundではfrontier全体を番号付きで提示し、各質問へ推奨回答を添えます。

利用者の回答を待ってからtreeを更新し、次のfrontierを計算します。

同じround内の未回答項目に依存する質問は、次のroundへ送ります。

環境から調べられる事実は利用者へ質問せず、ローカル調査または利用可能なread-only toolで確認します。

判断は利用者へ残し、代理回答しません。

frontierが空になっても、共有理解に達したことを利用者が確認するまで実装へ進みません。

## Safety boundary

- 自動起動しない。
- 質問数に固定上限を置かないが、各roundの冒頭で回答負荷を示す。
- 利用者が疲労または中断を示したら、未決事項を残して停止する。
- `grill-me` の一問ずつの形式へいつでも戻せる。
