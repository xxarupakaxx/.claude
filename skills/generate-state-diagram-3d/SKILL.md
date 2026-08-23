---
name: generate-state-diagram-3d
description: branch変更からlayer付きSVG状態図とtime-aware Graph JSONを生成する。2.5Dまたはtimeline表示が必要な図に使う。
allowed-tools: Read, Bash, Glob, Grep, Write
---

# 2.5D状態図とtimelineの生成

## 境界

このSkillは、layer、ownership、retry、queue、commit列、段階的なfailure recoveryを平面図だけでは追いにくい場合に使う。

静的なoverviewもlayer図もSVGを正本とし、Mermaidを生成しない。
Mermaid入力を必須にするviewer経路は使わない。

小さな変更や静的SVGだけで十分な変更では `generate-state-diagram` を使う。

## 成果物

- `91_state_diagram_3d.svg`：layer付きoverviewの正本。
- `91_state_diagram_3d.json`：node、edge、layer、timeline eventの機械可読データ。
- `91_state_diagram_3d.md`：説明、SVG参照、用語集、file map。
- `91_state_diagram_3d.html`：inline SVGとtimeline操作を含む自己完結HTML。

既存の `91_state_diagram.svg` を明示的な依頼なしに上書きしない。

## Graph JSON

JSONは最低限次を持つ。

```json
{
  "schemaVersion": 1,
  "title": "Diagram title",
  "nodes": [],
  "edges": [],
  "layers": [],
  "timeline": {
    "events": []
  }
}
```

nodeは安定した `id`、短い `label`、`layer`、状態または種別を持つ。
edgeは既知nodeだけを結び、関係labelを持つ。
timeline eventは時刻または順序、対象node、変化、根拠を持つ。
repositoryから確定できない関係を事実として補作しない。

## 手順

1. branch差分、commit列、関連sourceを読む。
2. 読者が追うべき時間軸とlayerを決める。
3. Graph JSONを作る。
4. 同じnodeとedgeからlayer付きSVGを生成する。
5. HTMLへSVGをinlineで埋め込み、timeline eventの選択で対象nodeをhighlightする。
6. MarkdownへSVG参照、関係一覧、用語集、file map、再生方法を書く。
7. JSON、SVG、Markdown、HTMLのnode IDとedge IDが一致することを検証する。

## SVG表現

- layerは背景bandまたはgroupで分離する。
- depthは位置、scale、opacityのうち必要最小限で表す。
- edgeは前後関係が読めるarrowとlabelを持つ。
- `role="img"`、`title`、`desc`、`viewBox`を必須にする。
- 外部resource、外部script、`foreignObject`、event handler属性を入れない。
- static SVGだけを開いても全体像が理解できるようにする。

## Timeline HTML

HTMLは自己完結させる。
Graph JSONをscript dataとして埋め込む場合は `application/json` を使い、`</script` をescapeする。
timeline controlはstep移動、reset、現在eventの説明を持つ。
JavaScriptはSVGのclassまたは属性だけを切り替え、nodeやedgeを推測で追加しない。

## 検証

- JSON schema、node参照、edge参照、timeline参照が整合する。
- SVGをXML parserでparseできる。
- HTML内の図はinline SVGであり、Mermaid sourceとruntimeを含まない。
- static SVGとtimeline初期状態の内容が一致する。
- timeline parseに失敗した場合もstatic SVGを残し、失敗を別に報告する。
