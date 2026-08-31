# Hallmark artifact trial review

## 評価範囲

最終candidate `/Users/yoshiki/.local/share/skill-governance/review/hallmark-html-2026-08/hallmark/codex` を明示して、計画書のBefore / After比較HTMLを一度だけ生成した。生成物は `/Users/yoshiki/Notes/Vault/.local/memory/260831_html-runtime-adoption/hallmark-value-generated/candidate.html`、生成attemptは1、retryは0、生成後の修正は行っていない。

candidateの `SKILL.md` は `bf7483992c06f630be9d688694aac3487d7a18780b52c04d492cfad5ccdec5d2`、target treeは `d7c75d8862bb0053d13fc00a040c84fa24cfdbad54ea59b55c2841c07a6f101e` である。Hallmarkのrouteは `plan-document`、配布HTMLのArtifact Contract routeは、Roadmap生成物ではない自己完結文書のため `html`（owner: `creating-html-documents`、artifact kind: `html-document`）へ写像した。

HTML Artifact Contractのstatic gateとbrowser gateは親がfreshに判定する。このreviewでは、生成済みbyteとhash、入力要件の反映、未検証事項を記録し、HTMLの合否を先取りしていない。

## 読んだ資料

Hallmarkの `SKILL.md` 全文に加え、`plan-document` と自己完結HTMLに必要な次の資料だけを読んだ。

- `/Users/yoshiki/.local/share/skill-governance/review/hallmark-html-2026-08/hallmark/codex/references/contract.md`
- `/Users/yoshiki/.local/share/skill-governance/review/hallmark-html-2026-08/hallmark/codex/references/layout-and-space.md`
- `/Users/yoshiki/.local/share/skill-governance/review/hallmark-html-2026-08/hallmark/codex/references/structure.md`
- `/Users/yoshiki/.local/share/skill-governance/review/hallmark-html-2026-08/hallmark/codex/references/components/h2-split-diptych.md`
- `/Users/yoshiki/.local/share/skill-governance/review/hallmark-html-2026-08/hallmark/codex/references/components/f4-step-sequence.md`
- `/Users/yoshiki/.local/share/skill-governance/review/hallmark-html-2026-08/hallmark/codex/references/typography.md`
- `/Users/yoshiki/.local/share/skill-governance/review/hallmark-html-2026-08/hallmark/codex/references/responsive.md`
- `/Users/yoshiki/.local/share/skill-governance/review/hallmark-html-2026-08/hallmark/codex/references/interaction-and-states.md`
- `/Users/yoshiki/.local/share/skill-governance/review/hallmark-html-2026-08/hallmark/codex/references/anti-patterns.md`
- `/Users/yoshiki/.codex/context/html-artifact-contract.md`
- `/Users/yoshiki/.codex/config/html-surfaces.json`
- `/Users/yoshiki/.codex/skills/creating-html-documents/SKILL.md`
- `/Users/yoshiki/.codex/skills/creating-html-documents/references/validation.md`
- `/Users/yoshiki/.codex/skills/sanitizing-artifacts/SKILL.md`

## 生成物

`candidate.html` は10,293 bytes・349行、SHA-256は `26015e94c971ca66c36001fad079d47e9e62ca29f08291a1ef3c18c66db6b6c3` である。HTMLには次を一度の生成で置いた。

- `<!doctype html>`、`lang="ja"`、charset、viewport、title、`data-artifact-kind="html-document"`
- inline CSS、system font stack、4ptのspacing token、semantic color token
- `default-src 'none'`、`script-src 'none'`、`frame-src 'none'`、`connect-src 'none'` を含むCSP
- semanticなh1 / h2 / h3、目次anchor、常時表示の本文
- Beforeの「別々の画面を開く」「依存図を後から開く」
- Afterの「同じ文書を読む」「依存図を本文で見る」
- Beforeを観測事実、Afterを「移行案・未実装」と示す二つの模型
- desktopでは `repeat(2, minmax(0, 1fr))`、gap 32px、panel padding 24px、`min-width: 0`
- 375pxでは比較を一列へreflowし、長い内容を局所wrapするmedia query
- title、desc、caption、`role="img"`を持つinline SVGの依存図
- `script`、`iframe`、外部font、CDN、remote image、外部resourceを含めない構成

HTML本文には `検証状態: 未検証` を表示し、640px以上、375px、自己完結条件を「検証条件」として分けた。これは検証済み表示ではない。

## route判定数（ケース集合限定）

既存の [hallmark-value-final-results.json](/Users/yoshiki/Notes/Vault/.local/memory/260831_html-runtime-adoption/hallmark-value-final-results.json) に保存した7試行を読み、Hallmarkをuseするかどうかを二値化した。positiveは「Hallmark名の明示または明示的なvisual-craft委譲があり、かつin-scopeなのでHallmark use」、negativeは「generic、範囲外、unsafe、または他primaryなのでHallmarkを起動しない」と定義した。databaseとpermissionはHallmark名を含むが、範囲外なのでnegativeである。

元6件だけでは、期待positive 0・期待negative 6、観測positive 0・観測negative 6となった。TP=0、TN=6、FP=0、FN=0、分母6、accuracy=1.0である。positiveの分母がないためprecisionとrecallは未定義であり、値を作っていない。

比較内容を保ったまま「Hallmarkを使って」を付加した派生1件を含めると、期待positive 1・期待negative 6、観測positive 1・観測negative 6となった。TP=1、TN=6、FP=0、FN=0、分母7、accuracy=1.0、precision=TP/(TP+FP)=1/1=1.0、recall=TP/(TP+FN)=1/1=1.0である。

この数値は固定された7ケースのrouteラベル集計だけであり、model pass@1、production trigger precision / recall、一般化性能、baselineの成功率ではない。baselineのケース実行は行っていない。

## 安全境界と未検証事項

candidateのSKILLや原典codeは実行せず、npm、npx、site server、外部通信、runtime、registry、lock、quarantine、他者fileも変更していない。今回のwrite scopeは `candidate.html`、`trial.json`、このreviewだけである。承認receipt、promotion、runtime activationは作成していない。

親が次をfreshに確認するまで、artifactのstatusは `generated_pending_parent_validation` とする。

- strict-self-contained static gate（doctype、lang、charset、viewport、title、artifact kind、CSP、external load 0、duplicate ID 0、禁止element 0、inline handler 0）
- 640px以上の二列、gap 32px以上、panel内側24px以上
- 375pxの一対ずつ縦配置、body横overflow 0、text wrapとclipなし
- semantic heading階層、SVGの表示とaccessible title / desc / caption
- keyboard focus、contrast、1440x900 desktop smoke
- HTML artifact routeとbrowser profileの整合

生成後に修正や再試行を行っていないため、親の検証で失敗が見つかった場合はこのtrialの失敗として記録し、別runで扱う。
