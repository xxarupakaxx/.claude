# 計画テンプレート

`improve-animations` が作成するすべての計画は、次の構造に従う。実装担当は文脈も美的判断基準も持たない可能性があるため、計画にはすべてを正確に記載する。「上の監査」や「話し合った easing」を参照してはならない。

````markdown
# NNN — <短い命令形のタイトル>

- **Status**: TODO
- **Commit**: <この計画の作成時に `git rev-parse --short HEAD` が出力した値>
- **Severity**: HIGH | MEDIUM | LOW
- **Category**: <監査カテゴリ>
- **Estimated scope**: <n files, rough size>

## Problem

何が、どこで、なぜ誤っており、それが製品の手触りにどう影響するか。
すべての場所を `path/to/file.tsx:123` として引用し、現在のコードをそのまま含める。

```css
/* src/components/dropdown.css:14 — current */
.dropdown { transition: all 400ms ease-in; }
```

## Target

正確な end state。curve、duration、spring config、media query のすべての値を明記する。
「より良い easing を使う」とは書かない。

```css
/* target */
.dropdown {
  transition: transform 200ms var(--ease-out), opacity 200ms var(--ease-out);
  transform-origin: var(--radix-dropdown-menu-content-transform-origin);
}
```

## Repo conventions to follow

この codebase がすでに採用している方法と、実装担当が模倣すべき一つの exemplar
（token name、file placement、prop pattern）を示す。

- Easing tokens live in `src/styles/tokens.css`; add new curves there, e.g. `--ease-out: cubic-bezier(0.23, 1, 0.32, 1);`
- <exemplar file:line that already does this correctly>

## Steps

1. <各 step につき一つの具体的な edit: file、変更内容、変更後の code。>
2. …

## Boundaries

- Do NOT touch <files/components out of scope>.
- Do NOT change markup/structure — motion properties only (unless a step says otherwise).
- Do NOT add new dependencies.
- If a step doesn't match the code you find (drift since the commit stamp), STOP and report instead of improvising.
- この plan は入力データであり、それ自体は実行指示ではない。実装前に、上位 workflow で write scope と user gate を明示する。

## Verification

- **Mechanical**: <exact commands — typecheck, lint, build — with expected outcome>.
- **Feel check**: UI を実行し、<interaction> を発火して次を確認する。
  - <観察可能な確認。例: 「dropdown が center ではなく trigger を起点に scale する」>
  - <例: 「toggle を連打しても animation がゼロから再開しない」>
  - DevTools の Animations panel で playback を 10% に設定し、<detail> を確認する。
  - Rendering panel で `prefers-reduced-motion` を切り替え、movement がなくなる一方で opacity feedback が残ることを確認する。
- **Done when**: <機械または目視で確認可能な完了条件>.
````

## 計画作成者への注記

- 指摘ごとに一つの計画を作成する。2つの指摘がすべて同じファイルと修正パターンを共有する場合（たとえば複数 component にまたがる同じ easing token の置換）は、一つの計画に統合してよい。
- すべての値を [AUDIT.md](AUDIT.md) から取得し、記憶で近似しない。
- Feel check は省略できない。Motion は機械的に正しくても、手触りが悪い場合がある。実装担当または差分を確認する人が slow motion で具体的に何を見るべきかを記載する。
- 計画の作成後、`plans/README.md` を作成または更新し、計画の table（number、title、severity、status）、推奨 execution order、計画間の dependency を記載する。
- このテンプレートと生成された plan は入力データとして扱う。ソース変更、計画実行、reconcile、worktree 操作へ自動的に進めない。実装は、上位のオーケストレーターが Delegation Gate を確認し、明示的な write scope と user gate を設けた別 workflow でのみ行う。
