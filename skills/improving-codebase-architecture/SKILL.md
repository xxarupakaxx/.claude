---
name: improving-codebase-architecture
description: コードベースを走査して deepening opportunity を見つけ、視覚的な HTML report として提示し、その中から選んだ候補を grilling で掘り下げます。
disable-model-invocation: true
---

# コードベースアーキテクチャ改善

architectural friction を表に出し、**deepening opportunity** を提案します。
これは shallow module を deep module へ変えるための refactor 候補です。
狙いは testability と AI-navigability です。

この command は project の domain model に支えられ、共有設計語彙の上に成り立ちます。

- architecture の語彙と原則のために `/designing-codebases` skill を使います。
  そこにある **Module**、**Interface**、**Depth**、**Seam**、**Adapter**、**Leverage**、**Locality** の語を、すべての suggestion でそのまま使います。
  `component`、`service`、`API`、`boundary` へ drift してはいけません。
- `CONTEXT.md` の domain language は、良い seam に名前を与えます。
  `docs/adr/` の ADR は、この command がむやみに蒸し返してはいけない decision を記録しています。

## 手順

### 1. 探索する

まず project の domain glossary である `CONTEXT.md` を読みます。
触ろうとしている領域に関係する ADR が `docs/adr/` にあれば、それも先に読みます。

その後、探索 sub-agent に codebase を歩き回らせます。
Claude Code では Agent tool を `subagent_type=Explore` で使います。
Codex では `multi_agent_v1.spawn_agent` または現在利用できる agent orchestration で explorer 相当の role を使います。
硬直した heuristic には従いません。
自然に探索しながら、自分が friction を感じる場所を記録します。

- 一つの concept を理解するのに、多数の小さな module を行き来しなければならない場所はどこか。
- interface が implementation とほぼ同じ複雑さを持つ **shallow** な module はどこか。
- testability のためだけに pure function を切り出した結果、実際の bug が caller 側の組み合わせに隠れ、**Locality** を失っている場所はどこか。
- 強く結合した module が seam をまたいで leak している場所はどこか。
- 現在の interface 越しには test できない、または test しづらい場所はどこか。

shallow だと疑った対象には **deletion test** を当てます。
それを消したときに複雑さが一か所へ集まるのか、それとも単に移るだけなのかを見ます。
「消すと complexity が集中する」が欲しい signal です。

### 2. 候補を HTML レポートで提示する

repo には何も落とさず、OS の temp directory に self-contained な HTML file を書きます。
temp dir は `$TMPDIR` から解決し、なければ `/tmp` を使います。
Windows では `%TEMP%` を使います。
出力先は `<tmpdir>/architecture-review-<timestamp>.html` とし、毎回 fresh な file にします。
その file をユーザー向けに開きます。
Linux では `xdg-open <path>`、macOS では `open <path>`、Windows では `start <path>` を使います。
absolute path も伝えます。

report では layout と styling に **Tailwind via CDN** を使います。
diagram には **Mermaid via CDN** を使います。
graph、flow、sequence のように構造が graph-shaped なときは Mermaid が向いています。
一方で、mass diagram、cross-section、collapse animation のような editorial な visual には hand-crafted な CSS や SVG を混ぜます。
Mermaid だけに頼らず、手で描いた visual も併用します。
各 candidate には **before / after visualisation** を必ず付けます。
とにかく visual にします。

各 candidate について、card には次を載せます。

- **Files**。
  関係する file と module。
- **Problem**。
  現在の architecture がなぜ friction を生んでいるか。
- **Solution**。
  何を変えるかを平易な言葉で書いた説明。
- **Benefits**。
  Locality と Leverage の観点で見た利点と、test がどう良くなるか。
- **Before / After diagram**。
  shallow さと deepening の形を左右比較で描いた custom visual。
- **Recommendation strength**。
  `Strong`、`Worth exploring`、`Speculative` のいずれか。
  badge として描画します。

report の最後には **Top recommendation** section を置きます。
最初に着手するならどの candidate か、その理由は何かを書きます。

domain には `CONTEXT.md` の語彙を使います。
architecture には `/designing-codebases` の語彙を使います。
もし `CONTEXT.md` で「Order」が定義されているなら、「FooBarHandler」でも「Order service」でもなく、「Order intake module」と話します。

**ADR conflict** は、本当に摩擦が強く、ADR を再検討する価値があるときだけ表に出します。
card の中で、それと分かるように明示します。
たとえば「ADR-0007 と矛盾するが、次の理由で再オープンする価値がある」のような warning callout にします。
理論上禁止されるすべての refactor を列挙してはいけません。

完全な HTML scaffold、diagram pattern、styling guidance は [HTML-REPORT.md](HTML-REPORT.md) を見ます。

この段階では interface そのものはまだ提案しません。
file を書き終えたら、「どれを掘り下げたいですか」とユーザーに聞きます。

### 3. grilling の反復

ユーザーが candidate を一つ選んだら、`/grilling` skill で design tree を一緒に歩きます。
制約、dependency、deepened module の shape、seam の奥に置くもの、どの test が生き残るかを詰めます。

decision が固まるたびに side effect をその場で反映します。
domain model を最新に保つために `/modeling-domains` skill を併用します。

- **deepened module に、`CONTEXT.md` にない concept 名を付けるなら**、その term を `CONTEXT.md` に追加します。
  file がなければ lazy に作ります。
- **会話の中で曖昧な term が sharpen されたなら**、その場で `CONTEXT.md` を更新します。
- **ユーザーが load-bearing な理由で candidate を却下したなら**、ADR を提案してよいかを聞きます。
  未来の explorer が同じ候補を再提案しないために、その理由を残す価値が本当にあるときだけ勧めます。
  「今はそこまでの価値がない」や「見れば自明」といった一過性の理由なら提案しません。
- **deepened module の別 interface 案も見たいなら**、`/designing-codebases` skill を起動し、その design-it-twice pattern を使います。
