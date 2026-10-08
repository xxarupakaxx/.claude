# Source and adaptation

- Upstream repository: `https://github.com/mathbullet/skills`
- Upstream path: `plugins/html/skills/html`
- Fixed commit: `fe96c626b39abba47fad2d4a4ef738e8a27602b1`
- Upstream package tree: `2d881a0a611f610d977c1c09892dd27806d118d9`
- Local name: `creating-html-documents`
- Adaptation date: `2026-08-26`

## Relationship

This package is a reviewed local adaptation, not an unchanged mirror. It retains the upstream focus on Japanese long-form HTML documents, figures, tables, code diffs, glossary rails, and print layout.

The adaptation adds document-type selection, decision-first composition, Roadmap responsibility boundaries, offline-by-default delivery, CSP, desktop browser and accessibility gates, and evaluation fixtures.

The default path removes remote fonts, CDN syntax highlighting, MathJax, clipboard JavaScript, and the executable PDF rendering shell. Those capabilities are not included in this reviewed tree.

## Local refinements

- `2026-08-27`: Added the overview-first refinement for complex Japanese HTML documents. Workflow, architecture, lifecycle, before/after, dependency, and failure-propagation documents now require a short orientation after the central claim, an accessible inline SVG overview when 3+ interacting elements are involved, detail slices that reuse the overview labels, and matching validation/template/eval coverage. This is a local candidate refinement only; it does not promote to the active runtime or any replica by itself.
- `2026-08-29`: Made overview an index into concrete detail rather than the deliverable itself. The skill now extracts a source inventory and claim ledger before layout, requires document-type-specific detail units and reader implications, rejects abstract filler, and uses desktop-only validation by default. Mobile, print, and PDF are opt-in delivery requirements.
- `2026-09-07`: Added the illustrated-explainer defaults for novice readers. When the reader has no domain background, the skill now applies, without an explicit request, analogy boxes with stated limits, a "why it was born" history chapter, a scene-style overview plus an actors map, one figure per detail chapter drawn from a fixed pattern catalog, a hypothetical worked case, and a self-test. The template gains `.analogy`, `.caution`, `.step-list`, `.qa`, and `.scene` components, and validation adds an SVG text overlap/spill/viewBox check with a local http.server fallback for browsers that block `file:` URLs.
- `2026-09-06`: Integrated the reviewed local `show-me` skill as a section-level visual decision layer. `creating-html-documents` remains the document owner; visual requests carry an explicit owner context and return a bounded visual brief or smallest representation without recursive handoff. Added routing and non-trigger evaluation coverage.

- `2026-09-14`: Added source-backed review navigation for multi-file code explanations: ordered file/symbol index, linked details and evidence, explicit dependency/call semantics, and diagram-design routing through show-me. The document owner retains placement and validation.
- `2026-09-28`: Tables are no longer a default component. Comparisons, differences, mappings and lists use side-by-side cards, before/after pairs, change-map SVGs and labelled highlights; a table is an explicit exception recorded in the document meta. Added the `screen-diff` document type with `references/screen-diff-explainer.md` (legend and counts, change map, scene pairs with CSS mini-screens, real-element labels, consistency rules, CSS pitfalls), a model-independent minimum bar of machine-checkable conditions, and a mandatory independent fresh review before delivery. Motivated by a payment-mock explainer whose table-heavy first version was judged hard to read.
- `2026-09-29`: Reworked the decision band after user feedback that a fully bold lead paragraph next to a narrow status column was hard to read. The band is now a kicker, a normal-weight lead of one to three sentences, optional parallel points (one title line and one note line each, linked to their sections with a visible link cue), and a one-line status footer instead of a side column. SKILL.md adds the visual-language rules and two machine-checkable minimum-bar conditions (no fully bold summary paragraph; no more than four lines of prose in a column narrower than 40% of the body), document-system.md and validation.md describe the new component, and evals add the feedback case. The template overview SVG was also redrawn after the same user found it hard to read: it is sized to the real figure width (viewBox 680, scale about 1.0), stacks stages vertically, uses real badge elements for 1, 2, 3, S and F, keeps labels inside their boxes and routes arrows only through gaps. A minimum-bar condition now requires figure text to render at 12px or larger after scaling, and validation records the scale and smallest rendered text size. The orientation block now reads as labelled rows instead of five narrow columns, with Japanese row labels.
- `2026-10-08`: Moved the mechanically countable part of the minimum standard into a script. `scripts/lint-html-document.py` runs the existing static contract and adds checks for tables, a single `h1`, scripts, text in `::before` / `::after`, and SVG `text` fill attributes overridden by CSS. Table and script exceptions are now named metas (`table-exception`, `script-exception`). Editing an existing HTML file now ends with `scripts/html-change-list.py`, which lists element-level changes so each one can be traced to the request.
