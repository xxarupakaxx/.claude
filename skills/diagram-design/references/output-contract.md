# 出力契約

## 先に決める4項目

| 項目 | 既定値 | 計画書での扱い |
|---|---|---|
| format | `html` + canonical `svg` | HTML は説明と fallback、SVG は図の正本 |
| size | `doc-inline`, `0 0 960 600` 相当 | narrow viewport では縦積み。図内の文字を縮めない |
| detail | `balanced` | 重要な関係を残し、統合・除外を記録 |
| audience | `mixed` | 実装名を保ち、不要な port/version は省く |

## detail の目安

- `simplified`: 7 nodes / 9 edges。能力と主経路だけ。
- `balanced`: 12 nodes / 16 edges。計画書の既定。ただし type 固有上限が厳しければそちらを優先する。
- `faithful`: 24 nodes / 32 edges。zone 必須、24を超えたら overview/detail に分割する。

## fidelity ledger

入力より小さくした図には次を HTML と Markdown fallback に書く。

```text
Detail: balanced · <source count> → <drawn count>
Merged: <source items> → <drawn label>
Collapsed: <group> → <drawn label>
Dropped: <items> · <reason>
Kept: <main relation>
```

## source binding

各 node、edge、comparison item は、可能なら `data-source="repo:path#Lx-Ly"` または `data-source="task:file#Lx-Ly"` を持つ。図の末尾に source list を表示し、生成日や mtime から事実を推測しない。比較の Before / After は同じ `data-item` id を使い、根拠が一方だけの場合はその差を明記する。

Source basis: fixed upstream `references/output-spec.md` の four dials、detail、degrade ladder、audience、fidelity ledger。
## 共通 HTML artifact 契約

- この適合版の HTML は、登録済み `diagram-design-sidecar` producer の `html-diagram` route として扱い、`<head>` に `<meta name="artifact-kind" content="html-diagram">` を一つ置く。`data-artifact-kind` だけでは代替しない。
- stage 固有の検査に加え、共通 `html_artifact_contract.py` の `strict-self-contained` profile を対象 HTML の file path ごとに適用する。
