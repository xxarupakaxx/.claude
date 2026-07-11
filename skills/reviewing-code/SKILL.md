---
name: reviewing-code
description: 固定点（commit、branch、tag、merge-base など）から `HEAD` までの変更を、標準準拠と仕様適合の 2 軸でレビューします。 並列 sub-agent で両方を走らせ、並べて報告します。 branch、PR、作業中差分、または「X から先を review して」と言われたときに使います。
---

ユーザーが指定した固定点と `HEAD` の差分を、次の 2 軸でレビューします。

- **標準準拠**。
  コードがこの repo の文書化された coding standard に沿っているかを見ます。
- **仕様適合**。
  元になった issue、PRD、spec の要求を正しく実装しているかを見ます。

この 2 軸は **並列 sub-agent** で走らせます。
互いの文脈を汚さないようにしたうえで、この skill が最後に結果を集約します。

issue tracker は事前に与えられている前提です。
`docs/agents/issue-tracker.md` がなければ、`/setting-up-engineering-skills` を先に実行します。

## 手順

### 1. 固定点を確定する

ユーザーが指定したものをそのまま固定点として扱います。
それは commit SHA、branch 名、tag、`main`、`HEAD~5` など、何でも構いません。
指定がなければ聞き返します。

差分 command は一度だけ確定します。
`git diff <fixed-point>...HEAD` を使います。
three-dot なので、比較対象は merge-base です。
あわせて `git log <fixed-point>..HEAD --oneline` で commit 一覧も取ります。

その先へ進む前に、固定点が解決できるかを `git rev-parse <fixed-point>` で確認します。
差分が空でないことも確認します。
bad ref や empty diff は、この段階で止めます。
並列 sub-agent の中で初めて失敗させてはいけません。

### 2. spec の出所を特定する

元 spec は次の順番で探します。

1. commit message にある issue 参照。
2. ユーザーが引数で渡した path。
3. `docs/`、`specs/`、`.scratch/` 以下の PRD や spec file。
4. 何も見つからなければユーザーに確認する。

commit message の参照には `#123`、`Closes #45`、GitLab の `!67` などがあります。
これらは `docs/agents/issue-tracker.md` の workflow に従って取得します。

spec が一つも見つからなければ、ユーザーに場所を聞きます。
spec 自体が存在しないと言われた場合、**仕様適合** の sub-agent は skip し、「spec がない」と報告させます。

### 3. standard の出所を特定する

repo 内でコードの書き方を定義している文書を探します。
たとえば `CODING_STANDARDS.md` や `CONTRIBUTING.md` です。

repo に何が書かれていても、それに加えて標準準拠軸では常に **smell baseline** を持ち込みます。
これは Fowler の code smell（_Refactoring_ 第 3 章）を固定の基準として使うものです。
repo に文書が何もなくても適用します。

この baseline を使うときのルールは二つです。

- **repo の記述が優先です。**
  repo の standard が明示的に許容しているものを baseline が嫌う場合、その smell は抑止します。
- **smell は常に judgment call です。**
  各 smell は hard violation ではなく、あくまでラベル付きのヒューリスティックです。
  standard と同様に、tooling が自動で強制しているものは skip します。

各 smell は「何か」→「どう直すか」の形で扱い、diff に照らして確認します。

- **Mysterious Name**。
  関数名、変数名、型名から役割が分からないなら rename します。
  正直な名前が付けられないなら、設計がまだ濁っています。
- **Duplicated Code**。
  同じ論理形が複数 hunk や複数 file に現れるなら、共通形を抽出して両方から呼びます。
- **Feature Envy**。
  ある method が自分より他 object の data を覗いているなら、その data 側へ method を移します。
- **Data Clumps**。
  同じ field や param の組が何度も一緒に移動するなら、一つの type に束ねます。
- **Primitive Obsession**。
  domain concept を primitive や string で代用しているなら、小さな専用 type を与えます。
- **Repeated Switches**。
  同じ type に対する `switch` や `if` の連鎖が繰り返されるなら、polymorphism か共有 map に置き換えます。
- **Shotgun Surgery**。
  一つの論理変更のために多くの file を散発的に触っているなら、変化が同居するように module を寄せます。
- **Divergent Change**。
  一つの file や module が無関係な複数理由で編集されているなら、理由ごとに分けます。
- **Speculative Generality**。
  spec にない将来需要のための abstraction、param、hook が入っているなら、実需が出るまで削って inline へ戻します。
- **Message Chains**。
  `a.b().c().d()` のような長い navigation が caller 側に露出しているなら、最初の object に一段で済む method を置きます。
- **Middle Man**。
  class や関数がひたすら委譲するだけなら、間の層を取り除き、実体へ直接つなぎます。
- **Refused Bequest**。
  subclass や implementer が継承したものの大半を拒否しているなら、inheritance をやめて composition を使います。

### 4. 両方の sub-agent を並列起動する

標準準拠と仕様適合の sub-agent を独立に、並列で起動します。
Claude Code では一つの message の中で `Agent` tool を二回呼び、両方に `general-purpose` を使います。
Codex では `multi_agent_v1.spawn_agent` または現在利用できる agent orchestration を使い、標準準拠 reviewer と仕様適合 reviewer を別々に起動してから両方を待ちます。

**標準準拠 sub-agent への prompt** には次を含めます。

- 完全な diff command と commit 一覧。
- 手順 3 で見つけた standards source file 一覧。
- 手順 3 の smell baseline 全文。
- 次の brief。

`Report — per file/hunk where relevant — (a) every place the diff violates a documented standard: cite the standard (file + the rule); and (b) any baseline smell you spot: name it and quote the hunk. Distinguish hard violations from judgement calls — documented-standard breaches can be hard, but baseline smells are always judgement calls, and a documented repo standard overrides the baseline. Skip anything tooling enforces. Under 400 words.`

sub-agent は smell baseline へ他経路からアクセスできないため、全文をそのまま貼ります。

**仕様適合 sub-agent への prompt** には次を含めます。

- diff command と commit 一覧。
- spec の path、または取得した spec 内容。
- 次の brief。

`Report: (a) requirements the spec asked for that are missing or partial; (b) behaviour in the diff that wasn't asked for (scope creep); (c) requirements that look implemented but where the implementation looks wrong. Quote the spec line for each finding. Under 400 words.`

spec がない場合は、仕様適合 sub-agent は起動せず、その旨を最終報告に明記します。

### 5. 集約する

二つの report は、`## Standards` と `## Spec` の見出しで並べて提示します。
そのまま載せるか、必要最小限に整えるだけにとどめます。
**統合したり、軸をまたいで優先順位を付け直したりしてはいけません。**

最後に 1 行の summary を添えます。
各軸ごとの finding 数と、各軸の中で最悪の問題が何かだけを書きます。
軸をまたいだ「総合 1 位」は決めません。
その再ランク付けを避けるために、2 軸を分けています。

## なぜ 2 軸なのか

変更は、一方を通って他方を落ちることがあります。

- すべての standard を守っていても、実装しているものが間違っていることがあります。
- issue の要求どおりに実装していても、project の約束事を壊していることがあります。

分けて報告することで、片方の合格がもう片方の失敗を覆い隠すのを防ぎます。
