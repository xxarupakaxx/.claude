---
name: creating-tracer-tickets
description: 計画・仕様・会話を、検証可能な tracer bullet ticket 群へ分割し、blocking edge を明記して、承認後に設定済みの tracker へ公開する。local は一 ticket 一ファイル、実 tracker は native の blocking link を使う。
disable-model-invocation: true
---

# Ticket を作成する

計画、仕様書、または会話を、各 ticket が end-to-end に検証できる垂直 slice へ分割する。issue tracker と triage label の語彙が未設定なら `/setting-up-engineering-skills` を先に案内する。

## 1. 入力と調査

- 会話にある情報を使い、引数で指定された仕様書、issue、URLは本文とコメントまで読む。
- codebase 未調査なら、関連する構造、domain glossary、ADR、既存の実装を必要な範囲で確認する。
- 変更を容易にする prefactoring が必要なら、先行 ticket として扱う。

## 2. 分割

各 ticket は狭い完全な経路（必要なら schema、API、UI、test の全層）を通り、単独で demo または検証でき、ひとつの context window で完了できる大きさにする。ticket 間の **blocking edge** には、本当に開始を妨げる blocker だけを書く。

広範な機械的変更で一括移行が green にできない場合は、次の順にする。

1. **expand**：新形式を旧形式と並べて追加する。
2. blast radius ごとの migrate batch：各 batch は expand に block され、可能なら個別に green にする。
3. **contract**：全 batch に block され、旧形式を削除する。

各 batch を単独で green にできない場合は、共通の integration branch と最後の integrate-and-verify ticket を置き、最後の ticket だけが green を保証する。

## 3. 承認

公開前に番号付きで次を示し、ユーザーへ確認する。

- **Title**、**Blocked by**、**What it delivers**
- 粒度が粗すぎないか、細かすぎないか
- blocking edge が開始条件を正しく表しているか
- 統合・分割したい ticket があるか

承認されるまで分割案を直す。parent issue は close も変更もしない。

## 4. 公開形式

- **Local**：`.scratch/<feature-slug>/issues/<NN>-<slug>.md` に、一 ticket 一ファイルを blocker 順で作る。「Blocked by」には番号と title を書く。
- **実 tracker（GitHub、Linearなど）**：blocker 順に一 ticket 一 issue を公開し、native の blocking/sub-issue 関係を使う。機能がなければ「Blocked by」へ issue を記載する。指定がなければ `ready-for-agent` triage label を使う。

どちらも次の形式で、ユーザーがそのまま着手できる acceptance criteria を書く。

```markdown
## What to build
ユーザー視点の end-to-end の挙動

## Acceptance criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Blocked by
- 依存 ticket の参照、または None — can start immediately
```

具体的なファイルパスや実装コードは原則書かない。state machine、reducer、schema、type shape が決定を正確に表す場合だけ、必要部分の snippet を埋め込む。

## 5. 引き渡し

公開後は `/implementing-work` で frontier（blocker が完了した ticket）を一つずつ進め、ticket 間で context を clear する。
