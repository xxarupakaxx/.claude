# Diagram Design 適合版レビュー

## 状態

`review-stage-draft`。これは公式候補を根拠にしたローカル適合版であり、active runtime への反映や有効化を完了したものではない。レビュー対象は次の2 targetで、内容とbyte列は同一である。

- Codex: `/Users/yoshiki/.local/share/skill-governance/review/diagram-design-html-2026-08/diagram-design/codex`
- Claude: `/Users/yoshiki/.local/share/skill-governance/review/diagram-design-html-2026-08/diagram-design/claude`

各 target は24 files、66,896 bytes、mode `0644`で、stage manifest SHA-256は両方とも `d2f95e1f43c196228bda26ea9af605b9435166ecc1e7c7f3ff68757bab805a70`。static checkerに出る `target_manifest_hashes` は `path:sha256` 連結方式の別digestであり、stage manifestとは定義が異なる。stageの詳細は [`diagram-stage.json`](/Users/yoshiki/Notes/Vault/.local/memory/260831_html-runtime-adoption/diagram-stage.json) に記録している。

## 目的と使い方

計画書の本文から、依存・処理の受け渡し・構造の境界・Before / After の差を追える図を作るための入口である。常時読むのは短い日本語の [`SKILL.md`] と [`references/selection.md`] だけにし、選んだ図種の reference を一つだけ追加で読む。図は本文の代替ではなく、表や短い文章より空間配置が情報を増やす場合だけ埋め込む。

図の選択と作成は次の順に固定した。

1. 読者の問い、source anchor、未知・除外範囲を決める。
2. semantic pattern から一つを選び、visual type を決める。
3. size、detail、audience、fidelity を [`references/output-contract.md`] で決める。
4. 図種 reference と共通の [`references/visual-rules.md`] だけを読む。
5. sourceの事実から同一IDの入力を作る。
6. SVGを正本にし、同じSVG・短い読み方・source anchor・テキストfallbackを自己完結HTMLへ入れる。
7. [`references/quality-gate.md`] と静的検査を通す。

採用する入口は4つに絞った。

| 問い | 図種 | JIT reference |
|---|---|---|
| 共有依存、fan-in、cycle | dependency | `references/type-dependency.md` |
| 担当をまたぐ入力・処理・出力 | process / data flow | `references/type-process.md` |
| zone、component、trust boundary | architecture | `references/type-architecture.md` |
| 二状態の差、ルール差、paired trace | comparison | `references/type-comparison.md` |

3列程度の表、短い箇条書き、単純な差分で足りる場合は図を作らない。Roadmapの進捗・task順・session / Hub選択・canonical stateは `viewing-plans` と共通rendererの責務であり、この適合版はそれらを管理しない。

## 公式候補からの差分

原典は固定した公式 main commit `b52a33bfeef85d43995193ee52c13b485154b7b4`、package tree `1bf319831137412e8ab71df321b510fa561fd262`、package manifest SHA-256 `97a426bfbb45b8c6f7fe22d527c2f9fb25d34f1329a6b7952eed5d090b104aa2`である。原典の全212 filesは不変 quarantineに保存され、参照元とMIT licenseは [`SOURCE.md`](/Users/yoshiki/.local/share/skill-governance/review/diagram-design-html-2026-08/diagram-design/codex/SOURCE.md) と [`UPSTREAM.md`](/Users/yoshiki/.local/share/skill-governance/review/diagram-design-html-2026-08/diagram-design/codex/UPSTREAM.md) に結び付けた。license本文は各targetの `LICENSE` と、元取得記録の `/Users/yoshiki/Notes/Vault/.local/memory/260831_html-skill-additions/license-evidence/diagram-design-LICENSE.txt` で確認できる。

原典から採用した判断は、semantic patternを先に選ぶこと、図より表を優先する削除規則、dependencyのrank / fan-in / cycle、processのlane / step / payload、architectureのzone / boundary / 直交connector、comparisonの同一ID / first divergence / fidelity ledger、SVGのtitle / desc / aria、system font、静的出力である。これらの根拠は quarantine内の `SKILL.md:50-79,139-179`、`references/type-dependency.md:3-28`、`references/type-architecture.md:3-16,52-68`、`references/type-data-flow.md:1-7,163-195,281-349`、`references/semantic-patterns.md:61-73`、`references/type-line.md:46-86`、`references/output-spec.md:3-12,84-112,116-137,168-182` にある。

contextを抑え、実行経路を安全にするため、次を変更または除外した。

| 原典 | 適合版 | 判断理由 |
|---|---|---|
| 39 visual types の大きな選択表 | 4つのJIT入口 | 計画書の実装説明に必要な判断だけを常時参照するため |
| Instrument Serif / Geist / Geist Mono とlive font link | CJKを含むsystem font stack | 外部load 0、オフライン閲覧、表示の再現性を優先するため |
| URL onboarding、profile resolution | 固定local tokenと明示source | URL取得、永続write、global stateを持ち込まないため |
| 多数のexample HTML | 5つの小さなデモ | galleryを常時読む負担を減らし、構図を検査可能にするため |
| export / import / gallery scripts | 参照のみ、実行経路から除外 | 未審査code、browser automation、networkを実行しないため |

公式155 example HTML、gallery iframe、animation controller、`drawio_extract.py`、`mermaid_extract.py`、`self_check.py`、Playwright export、profilesの保存・削除、remote fonts、外部asset、`foreignObject`、global style-guide mutationは含めていない。公式全体を導入したという意味ではない。

## 実装単位とサンプル

各HTMLは外部CSS、画像、font、script、iframe、network requestを持たず、inline CSSと同梱SVGだけで表示する。共通契約として、登録済み `diagram-design-sidecar` producer の `html-diagram` routeに結び、`<meta name="artifact-kind" content="html-diagram">` を `<head>` に置く。`data-artifact-kind` だけでは代替せず、stage固有検査に加えて `html_artifact_contract.py` の `strict-self-contained` profileを各HTMLへ適用する。SVGは `viewBox`、`role="img"`、`aria-labelledby`、title、descを持ち、線を先に描いてからnodeを描く。fontは `Hiragino Sans`、`Yu Gothic`、`Noto Sans JP`、`system-ui` を基本にする。主要な型ごとの上限は dependency 9 nodes / 14 edges / 4 ranks、process 6 lanes / 12 steps、data flow 4 lanes / 6 steps、architecture 3 zones、paired comparison 2 traces / 3–6 rules / 1 divergenceとした。

実例は、正本SVGと同じSVGを含むHTMLをペアで置いている。今回のstage差分は10 HTMLの契約metaと2 targetの `references/output-contract.md` への共通検査規則だけで、SVG 10 fileのbyte列は更新前と一致する。

- `examples/dependency-before.*`: 5つの平坦な関係をBeforeとして示す。
- `examples/dependency-candidate.*`: `plan`、`renderer`、`parser`、`snapshot`、`source`の5 node、5 edge、4 rank、`snapshot`へのfan-in 2を直交線で示す。全node / edgeに `data-source` を付けた。
- `examples/process.*`: 3 lane、4 node、typed input / output、1 focal handoffを示す。
- `examples/architecture.*`: 3 zone、3 component、3 link、trust boundaryを含む主経路を示す。
- `examples/comparison.*`: 同じ3 item IDをBefore / After列で対応させ、表を第一候補にする判断を併記する。

これらは構図のfixtureであり、対象VaultやRoadmapの実装事実を表す証拠ではない。実案件では各node、edge、itemを `path#Lx-Ly` またはtask artifactの該当行へ戻し、削除・統合・未知の値をfidelity ledgerへ残す。

## 確認結果

以下はローカルで実行した確認である。PASSは構造・構文・fixtureの条件を満たしたことを表し、読者の理解度、視認性、model value、production precision / recallを測ったものではない。

| 確認 | 結果 | 記録 |
|---|---|---|
| Codex / Claudeのfile、mode、byte parityとsource binding | PASS | [`diagram-eval-static.json`](/Users/yoshiki/Notes/Vault/.local/memory/260831_html-runtime-adoption/diagram-eval-static.json) |
| 10 HTMLの`html-diagram` metadata、登録済みproducer、共通契約 | PASS | [`diagram-eval-html-contract.json`](/Users/yoshiki/Notes/Vault/.local/memory/260831_html-runtime-adoption/diagram-eval-html-contract.json) |
| dependency Before / candidateのnode、edge、rank、fan-in、source、直交path | PASS | [`diagram-eval-dependency.json`](/Users/yoshiki/Notes/Vault/.local/memory/260831_html-runtime-adoption/diagram-eval-dependency.json) |
| 正しい図種4件と、表・進捗・canonical state・装飾の非採用4件 | PASS | [`diagram-eval-trigger.json`](/Users/yoshiki/Notes/Vault/.local/memory/260831_html-runtime-adoption/diagram-eval-trigger.json) |
| frontmatter（offline uv / PyYAML 6.0.2） | PASS | [`diagram-eval-frontmatter-codex.json`](/Users/yoshiki/Notes/Vault/.local/memory/260831_html-runtime-adoption/diagram-eval-frontmatter-codex.json)、[`diagram-eval-frontmatter-claude.json`](/Users/yoshiki/Notes/Vault/.local/memory/260831_html-runtime-adoption/diagram-eval-frontmatter-claude.json) |
| 10 SVGのXML構文 | PASS | [`diagram-eval-svg-xml.txt`](/Users/yoshiki/Notes/Vault/.local/memory/260831_html-runtime-adoption/diagram-eval-svg-xml.txt) |

candidate codeの実行、外部通信、browser automationは行っていない。modelによる価値評価とhuman approval receiptは未取得である。active runtime、registry、lockは変更していないため、次の判断はleadが安全性・価値・承認・bindingを確認した後に行う。

## 境界と残課題

このstageは `diagram-design-html-2026-08` のreview collectionに固定されている。`~/.codex/skills/diagram-design` と `~/.claude/skills/diagram-design` にある既存adapter、Roadmap / Hubの共通renderer、active registry / lockはこの資料の作成対象ではなく、変更していない。採用する場合も、まずleadがsource、license、parity、safety/value evidence、human approval、runtime bindingを確認し、別のgateでactive runtimeへ反映する。現時点の事実は「適合版のreview-stage構成、静的fixture検査、共通HTML契約検査が完了」であり、「Skillが有効化され、実案件のHTML計画書を自動生成できる」ではない。
