---
name: improving-codebase-architecture
description: コードベースを読み取り専用で調査し、shallow module・seam leakage・locality不足からdeepening候補を1〜3件提示する。architectureのhotspotをsurveyしたいときに使い、実装・ADR・CONTEXT更新は別依頼へ渡す。
disable-model-invocation: true
---

# コードベースアーキテクチャ改善 survey

architectural frictionを根拠付きの候補へ整理するread-onlyの設計規律。目的はtestabilityとAI navigabilityを上げる選択肢を示すことにあり、survey中にrepository、`CONTEXT.md`、ADR、source codeを変更しない。実装、test、ADR作成、用語追加、commitはこのSkillの完了後に別のuser gateで扱う。

## 読む範囲

`/designing-codebases` の語彙（`Module`、`Interface`、`Depth`、`Seam`、`Adapter`、`Leverage`、`Locality`）を使い、PJの `CLAUDE.md`、関係する `CONTEXT.md`、`docs/adr/` の既存判断を先に読む。用語が未定義なら、断定せず候補名と根拠を提示する。`component`、`service`、`API`、`boundary`など別語へ不用意に置き換えない。

現行のsession capabilityがあればexplorer相当の読み取り役を使える。固定APIや `multi_agent_v1` を仮定せず、leadが単独で確認できる場合は委譲しない。各候補は次の問いと証拠で絞る。

- 一つのconceptを理解するために、多数の小さなmoduleを往復していないか。
- Interfaceがimplementationと同じ複雑さのshallow moduleになっていないか。
- pure functionの切り出しがcallerの組み合わせへbugを隠し、Localityを失わせていないか。
- Seamをまたぐ依存や漏出がないか。
- Interface越しにtestしにくい理由が何か。

shallowを疑う対象にはdeletion test（消したときcomplexityが一か所へ集まるか、単に移るだけか）を思考実験として行う。コードを削除・編集して試さない。

## 候補の提示

候補は1〜3件に絞り、同じ問題を複数候補に重ねない。各候補に次を付ける。

- Filesとmodule、`path:line`またはsymbolの根拠
- Problem: どのfrictionがどのseamで起きるか
- Solution: どのmoduleをdeepにするか。実装手順ではなく形を示す
- Benefits: Locality、Leverage、testabilityへの影響
- Before / After: node/edgeまたは浅いmoduleを畳み込む簡素なSVG/テキスト図
- Recommendation: `Strong` / `Worth exploring` / `Speculative`
- ADR conflict: 既存ADRを再検討するだけの根拠があるときだけ、該当番号と理由

sourceで確認できない依存や効果を事実として書かない。候補の利得は保証ではなく、前提と不確実性を添える。最初に着手するTop recommendationと、その判断根拠も一つ示す。

## 可視化（条件付き）

ユーザーが視覚的なreportを求めた場合だけ、repository外のtemp directoryへself-contained HTMLを作る。候補カード、before/afterのinline SVG、Files、Problem、Solution、短いWins、Top recommendationを含める。外部script、network依存、独自interactivityを既定で追加せず、HTML正本の詳細は `HTML-REPORT.md` を参照する。図の正本はSVGとする。

HTMLを作らない場合は、同じ情報を短いMarkdownで返す。図は関係の理解に寄与する候補だけにし、文章を重複させない。ユーザーが開かないよう指定していなければ、検証済みのlocal artifactを安全なviewerで開く選択肢とabsolute pathを案内する。

## 選択後のhandoff

ユーザーが候補を選んだら、`/grilling` に次の判断材料を渡す。ここでもside effectを実行しない。

```text
candidate: <選択したcandidate>
evidence: <files:symbol / source anchor>
decision: <制約、依存、deepened moduleのshape>
seam: <何を内側へ置き、何をinterfaceへ残すか>
tests: <生き残るtestと追加検証の候補>
open_questions: <未決定事項>
next_gate: <実装 / ADR / CONTEXT更新を別依頼で判断>
```

`CONTEXT.md` やADRを更新する、sourceを実装する、testを追加する、commitする、既存ADRを再オープンする、といった選択を自動で進めない。ユーザーが別途依頼した場合は、`implementing-work`、`creating-adr`、`modeling-domains`、`designing-codebases`など該当skillへhandoffする。

## 完了条件

- 読み取り対象と根拠が具体的で、候補は1〜3件に収まる。
- shallow/deep、Seam、Interface、Locality、Leverageの関係がsourceに戻れる。
- 変更を実施したように報告せず、実装やADRの選択肢と次のgateで止まる。
- 視覚化を作った場合もrepository変更、外部通信、未検証HTMLを残さない。
