# UI Change Preview Runbook

このrunbookは、UI変更Taskの計画本文にBefore / After mockをauthoringする契約である。`30_plan.html`を正本とし、RoadmapはそのDOMとhead CSSを保ったまま表示する。HTML route、static gate、browser profileは`context/html-artifact-contract.md`と`config/html-surfaces.json`を正本にする。

## 使う場面

新しいHTML計画では、UI変更Taskに`data-ui-change="true"`と、同じTask内の`script[type="application/json"][data-plan-fragment="ui-preview"]`を置く。fragmentは表示内容を持たず、Task本文に見えるmock DOMのanchorだけを指す。

- 使う: navigation、sidebar、settings、list、form、既存画面の構造変更、新規画面。
- 使わない: behavior-only、copyだけ、APIやjobだけの変更、UI変更か判断できないTask。
- sourceを確認できない既存画面はBeforeを補作しない。Task本文または`uncertainty`に確認不能の理由を残す。

旧`30_plan.md`と既存HTMLは、過去の`UI変更: yes`、`ui-preview-json`、v1 payloadを読む互換入力としてだけ扱う。新しいHTML authoringではv2 fragmentを使い、v1 payloadやMarkdown fenceを作らない。

## LLM Authoring Flow

UI変更Taskでは、`30_plan.html`を完成させる前に次を行う。

1. 計画開始時点のrepository `HEAD`を40桁commit SHAへ解決し、Beforeのbaselineとして固定する。
2. 仕様、変更対象、routeを確認し、対象componentを読む。JSX / TSX / template本体、直接importされるcomponent、局所styleを、表示構造と表示labelが分かる範囲で読む。
3. sourceから確認できるDOMの順序、label、group、action、input、明示stateを抽出する。実行時data、未確認のrole差、responsive差を推測しない。
4. 変更対象の周辺だけを、確認したDOMとstyleに沿う小さなBefore mockとAfter mockとして`30_plan.html`へ書く。BeforeとAfterは別の`data-ui-side`要素にし、同じTaskの中に置く。
5. Afterは計画の目的、実装手順、仕様に明示した未実装案だけから作る。実装済みと読める文言を置かず、Afterには常に`計画案・未実装`を見えるcaptionとして置く。
6. sourceまたは計画で確定できないrole、feature flag、権限、responsive、実データは`uncertainty`へ分離する。
7. v2 fragmentを同じTaskへ一つだけ書き、Before / Afterのanchorを記録する。metadataやsource pathをユーザーへ入力させず、ユーザーへJSONを入力させない。
8. 通常生成後、各anchorが解決され、Before/Afterのcaptionと未確認理由が表示されることを確認する。

## 表示DOM

mockはJSONのitem一覧や固定primitiveではなく、計画本文に見える実際のHTML構造である。既存componentのDOM階層、直接importのcomponent、局所styleを根拠に、変更箇所を読める最小範囲で再現する。

```html
<figure id="before-navigation" data-ui-side="before">
  <figcaption>現状・base refから確認</figcaption>
  <nav aria-label="Primary navigation">
    <a href="#home" aria-current="page">Home</a>
    <button type="button" disabled>Settings</button>
  </nav>
</figure>
<figure id="after-navigation" data-ui-side="after">
  <figcaption>計画案・未実装</figcaption>
  <nav aria-label="Primary navigation">
    <a href="#home" aria-current="page">Home</a>
    <a href="#reports">Reports</a>
    <button type="button" disabled>Settings</button>
  </nav>
</figure>
```

実際のcontrols（link、button、input、labelなど）と表示labelを本文へ置く。各sideはTask内にあり、`id`をfragmentのanchorとして一意にする。styleは`30_plan.html`のhead内CSSで、対象componentと直接importのstyleから確認・再現できた範囲を表す。pixel、computed value、runtime dataを根拠なしに足さず、判断できない部分は`uncertainty`に書く。

mockは変更対象周辺の比較面であり、アプリ全体のcapture、production build、自由配置editorではない。sourceのHTML/CSSを読むことと、source codeを実行・buildすることを混同しない。event handler、実行script、外部load、外部resourceは計画本文へ持ち込まない。

## v2 fragment contract

新しいHTMLでは、次の形をTask内に一つだけ置く。fragmentは本文のlabel、DOM、style、実装説明を複製しない。

```html
<script type="application/json" data-plan-fragment="ui-preview">
{
  "version": 2,
  "taskNumber": "1",
  "previews": [{
    "id": "primary-navigation",
    "title": "Primary navigation",
    "provenance": {
      "before": {
        "source": "repo:src/navigation.tsx#PrimaryNavigation",
        "baseRef": "0123456789abcdef0123456789abcdef01234567",
        "observedLabels": ["Home", "Settings"]
      },
      "after": {"source": "Task 1 / UI変更案"}
    },
    "before": {"anchor": "before-navigation"},
    "after": {"anchor": "after-navigation"},
    "uncertainty": []
  }]
}
</script>
```

rootのkeyは`version`、`taskNumber`、`previews`である。各previewのkeyは`id`、`title`、`provenance`、`before`、`after`、`uncertainty`であり、v2の`before` / `after`はそれぞれ同じTask内のvisible DOM anchorを一つだけ指す。`taskNumber`はTaskの`data-task-id`と一致させる。

`provenance.before.source`は`repo:<relative-path>#<anchor>`、`baseRef`は40桁の固定commit SHA、`observedLabels`はそのrefで実際に読んだlabel配列とする。`provenance.after.source`は計画本文の見出し、section、または仕様への明示参照とする。Afterをrepository sourceとして記録しない。

新規画面は既存画面の空カードを作らない。Before側のDOMとBefore sourceを置かず、After側のmockだけを表示し、`新規画面`と`計画案・未実装`をvisibleにする。fragmentは`before: {"anchor": null}`とし、Before anchorを作ったことにしない。

unknown key、Task外fragment、複数fragment、v2以外の新規HTML payload、Task番号不一致、重複anchor、解決不能anchorはinvalidとする。v1は過去のMarkdownと既存HTMLを読む互換入力にだけ残す。

## Sourceと表示の境界

Beforeは固定したbase refの実装sourceと、そのcomponentが直接読む構造・styleから作る。Afterは計画で明示した未実装案から作る。この二つを混ぜず、推測を「現在の実装」と表示しない。sourceをallowlist内の相対pathとして解決できない、secret-like、symlink、binary、非UTF-8、過大fileの場合はcodeやDOMを表示せず、理由だけを残す。

reference HTMLは比較面の余白、caption、focus、responsiveを読みやすくする指針として使える。既存componentのstyleを確認・再現することは許可するが、reference固有のtoken、font、画像、外部CSSを根拠なしに移植しない。安全な計画本文のCSPとsystem fontを保つ。

## Limitsとverification

- 1 Taskにつき`ui-preview` fragmentは1つ、previewは最大3件。
- 1 previewにつきBefore / After各1 anchor。sideは変更対象周辺に絞り、長い一覧や実データを埋め込まない。
- label、caption、uncertaintyは短くし、本文の説明をfragmentへ複製しない。
- sync前にfragment、DOM anchor、base ref、source provenanceを検査する。
- Roadmap生成はcaption、mock DOM、head CSSをそのまま表示し、Task proseやAfter mockをJSONから再構成しない。
- Browser gateではoverflow、focus、keyboard、console/page errorを先に確認する。画像やLLMによる視覚reviewは、assertion失敗または明示要求がある場合に限る。

Before / AfterはUI変更の理解を助ける計画内の実DOMであり、production UIの承認や実装完了の証拠ではない。未実装案、sourceのbaseline、unknownを表示上も分離する。

## 既存v1の互換境界

既存v1の互換読込では、itemの`parentId`は同じsideのgroupを参照し、rootの`slot`は`header`、`nav`、`main`、`aside`、`actions`、`footer`に限定する。孤立参照、循環、group以外への参照、`parentId`と`slot`の併用を拒否する。構造付きpayloadは親子関係と配置を保持し、構造のないpayloadは従来のflat表示を保つ。sourceを検証できないv1のBeforeは計画記録として保持し、確認済みの観測へ昇格させない。新規HTMLのv2 authoringへこのitem形式を持ち込まない。
