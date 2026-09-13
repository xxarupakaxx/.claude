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
