---
name: creating-tracer-tickets
description: 計画、仕様書、現在の会話を tracer bullet 形式の ticket 群に分割し、各 ticket の blocking edge を明記して設定済みの tracker に公開する。local では ticket ごとに一つのファイルへ edge を文章で記し、実際の tracker では native の blocking link を使う。
disable-model-invocation: true
---

# Ticket を作成する

計画、仕様書、会話を**ticket**群へ分割する。
各 ticket は tracer bullet 形式の垂直 slice とし、その ticket を**ブロックする**別の ticket を明記する。

issue tracker と triage label の語彙は、事前に提供されている必要がある。
提供されていない場合は `/setting-up-engineering-skills` を実行する。

## 手順

### 1. コンテキストを集める

会話コンテキストにすでに含まれる情報を使う。
ユーザーが引数として参照先（仕様書のパス、issue 番号、URL）を渡した場合は、その情報を取得し、本文とコメントをすべて読む。

### 2. codebase を調査する（任意）

まだ codebase を調べていない場合は、code の現在の状態を理解するために調査する。
ticket の title と description にはプロジェクトの domain glossary にある語彙を使い、変更対象の領域にある ADR を尊重する。

実装を容易にする prefactoring の機会を探す。
「変更を簡単にしてから、簡単になった変更を行う。」

### 3. 垂直 slice の案を作る

作業を **tracer bullet** 形式の ticket に分割する。

<vertical-slice-rules>

- 各 slice はすべての layer（schema、API、UI、test）を通る、狭いが**完全な**経路にする。
一つの layer だけを扱う水平 slice にはしない。
- 完了した各 slice は、単独で demo または検証できるようにする。
- 各 slice は、まっさらな一つの context window で完了できる大きさにする。
- prefactoring が必要な場合は先に行う。

</vertical-slice-rules>

各 ticket に **blocking edge** を付ける。
blocking edge とは、その ticket を開始する前に完了していなければならない別の ticket である。
blocker のない ticket はすぐに開始できる。

**広範な refactor は、垂直 slice の例外である。**
**広範な refactor** とは、column の rename や共有 symbol の retype のように、一つの機械的な変更が codebase 全体へ扇状に広がる作業を指す。
一度の編集で何千もの call site が壊れ、green のまま着地できる垂直 slice を作れない場合が該当する。
この変更を無理に tracer bullet にせず、**expand–contract** の順に並べる。
まず expand として、何も壊さずに新しい形式を古い形式と並べて追加する。
次に blast radius に応じた単位（package 単位や directory 単位）で call site を順次移行し、各 batch を expand に block される個別の ticket にする。
古い形式が残っているため、batch ごとに CI を green に保てる。
最後に contract として、すべての migrate batch に block される ticket で、利用箇所がなくなった古い形式を削除する。
各 batch を単独で green にできない場合も順序は維持するが、共通の integration branch を使い、すべての batch が最後の integrate-and-verify ticket を block する形にする。
green を保証するのは、その最後の ticket だけである。

### 4. ユーザーに確認する

提案する分割案を番号付き list で示す。
各 ticket について次を示す。

- **Title**：短く内容を表す名前
- **Blocked by**：先に完了する必要がある別の ticket（ある場合）
- **What it delivers**：この ticket によって動作するようになる end-to-end の挙動

ユーザーに次を確認する。

- 粒度は適切か（粗すぎるか、細かすぎるか）
- blocking edge は正しいか（各 ticket は、本当に開始を妨げる ticket だけに依存しているか）
- 統合またはさらに分割したい ticket はあるか

ユーザーが分割案を承認するまで改善する。

### 5. 設定済みの tracker に ticket を公開する

承認された ticket を公開する。
公開方法は `/setting-up-engineering-skills` で設定された tracker によって異なる。
ticket の内容は同じであり、blocking edge の表現だけが変わる。

- **Local file**：`.scratch/<feature-slug>/issues/<NN>-<slug>.md` に ticket ごとに一つのファイルを作り、依存順（blocker が先）に `01` から番号を振る。
各ファイルの「Blocked by」には、依存する ticket の番号と title を列挙する。
後述の ticket template を使い、一つのファイルには一つの ticket だけを書く。
複数の ticket を一つのファイルにまとめてはならない。
- **実際の issue tracker（GitHub、Linear など）**：依存順（blocker が先）に、ticket ごとに一つの issue を公開する。
この順序なら、各 ticket の blocking edge から実在する identifier を参照できる。
platform に native の blocking または sub-issue 関係がある場合はそれを使う。
ない場合は、各 ticket の「Blocked by」に blocking issue を記載する。
別の指示がなければ `ready-for-agent` triage label を付ける。
各 ticket は agent がそのまま着手できる形になっている。

**frontier** にある ticket に取り組む。
frontier とは、すべての blocker が完了している ticket を指す。
完全に直線的な chain なら、上から下へ取り組む。

parent issue を close または変更してはならない。

<local-ticket-template>

# <NN>：<Ticket title>

**What to build：**この ticket によって動作するようになる end-to-end の挙動を、ユーザーの視点から書く。
layer ごとの実装 list にはしない。

**Blocked by：**この ticket の開始を妨げる ticket の番号と title を書く。
ない場合は「None — can start immediately」と書く。

**Status：**ready-for-agent

- [ ] Acceptance criterion 1
- [ ] Acceptance criterion 2

</local-ticket-template>

<issue-template>

## Parent

tracker 上の parent issue への参照を書く。
元の情報が既存 issue でない場合は、この section を省略する。

## What to build

この ticket によって動作するようになる end-to-end の挙動を、ユーザーの視点から書く。
layer ごとの実装にはしない。

## Acceptance criteria

- [ ] Criterion 1
- [ ] Criterion 2

## Blocked by

- blocking ticket への参照を一件ずつ書く。
ない場合は「None — can start immediately」と書く。

</issue-template>

どちらの形式でも、具体的なファイルパスやコードスニペットは避ける。
すぐに古くなるためである。
例外として、prototype が文章より正確に決定内容を表す snippet（state machine、reducer、schema、type shape）を生成した場合は、それを埋め込み、prototype から得たことを簡潔に記してよい。
動作する demo 全体ではなく、決定に関わる部分だけに絞る。

`/implementing-work` を使い、frontier にある ticket を一つずつ進める。
ticket と ticket の間では context を clear する。
