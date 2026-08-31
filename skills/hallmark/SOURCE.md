# Hallmark source and local adaptation

## Upstream

- Repository: Nutlope/hallmark
- Review collection: hallmark-html-2026-08/hallmark
- Repository URL: https://github.com/Nutlope/hallmark
- Homepage: https://www.usehallmark.com/
- Ref: refs/heads/main
- Fixed commit: 13ac0ec7e148655948100b6396439e481361d690
- Commit tree: 02ebcc67f58295654c073cfb74a20a9a86db1f8f
- Upstream skill tree: 747c924c4767b4d5fa6f1c59985c87a21c918334
- Upstream SKILL.md bytes: 67,460
- Upstream SKILL.md sha256: 59469635bbbd21acddbc664d95e8d97147f454b2d8f4a0a89c7d2c5afbe67577
- Package license: MIT; exact text is retained in LICENSE.
- Source quarantine: /Users/yoshiki/.local/share/skill-governance/quarantine/hallmark/13ac0ec7e148655948100b6396439e481361d690/
- Full source package snapshot: repository-snapshot/ in the quarantine above.

## Source-only retention

source/UPSTREAM-SKILL.md.txt is a byte-for-byte copy of the pinned upstream entry. The txt suffix and the source-only label are deliberate: it is provenance evidence, not a local instruction surface, is never loaded as active context, and is not a replacement for this adapted SKILL.md. The original references remain in the immutable quarantine snapshot. No upstream file was silently truncated.

## Relationship

This review tree is a local adaptation for static, self-contained Japanese HTML documents and explicitly selected visual-craft review. It preserves the upstream ideas of preflight, named structure, spacing scale, typography hierarchy, semantic color, anti-pattern review, responsive checks, interaction states, audit, redesign, study, step sequence, split comparison, and inline headings. For product UI, designing-ui-ux remains the primary owner of information architecture, task flow, usability, and accessibility; Hallmark is not a second UI entry.

The adaptation changes the default behavior in these ways:

1. The entry is Japanese and 5,807 bytes / 52 lines; practical details are split into conditional references. This is measured against the prior adapted entry (12,591 bytes) and the pinned upstream entry (67,460 bytes), while the designing-ui-ux baseline is 12,029 bytes. Byte size is not a context-token or comprehension measurement.
2. A plan-document route is explicit. Full initial display, horizontal Before / After, inline SVG dependency maps, implementation details, evidence, and unimplemented labels are required for this task class.
3. Local/system fonts, inline SVG, CSP, and external-load zero are the default. The upstream site demo, font links, analytics, live fetch, storage, and runtime scripts are not adopted.
4. The upstream preflight/log writes become read-only notes or task-local evidence only. No global/profile/config write is implied.
5. Theme choice is catalog-first and one-detail-at-a-time. All 21 upstream theme documents are not loaded on every request.
6. Hallmark activates only when named by the user or explicitly selected by designing-ui-ux as visual-craft support. Existing route, logic, data, auth, and global stylesheet boundaries are preserved unless a separate explicit scope names them; designing-ui-ux remains primary for product UI flow and accessibility.
7. The three directory-only references and thirteen site/docs/example escapes are handled in adaptation.diff; this target contains only concrete local references.
8. The general interaction states are supplemented with a separate selected state when selection semantics exist; selected is not collapsed into pressed.
9. HTML output is handed to the registered creating-html-documents producer and checked by the shared html_artifact_contract. Both data-artifact-kind and meta name="artifact-kind" content="html-document" are required; Hallmark does not duplicate the producer or checker. The original candidate artifact trial remains unchanged and its first static pass is recorded as artifact-kind-missing.

## 16 upstream reference findings

The pinned candidate had 16 blocking relative references: 7 token links into the upstream site, 6 human/visual example links, and 3 directory-only links. This adaptation does not make those targets implicit runtime dependencies.

- Token links are replaced by local theme tokens and the theme catalog. If a source token is needed later, it must be individually copied with source path, fixed commit, hash, and license evidence.
- Human/visual examples remain source-only material in the quarantine snapshot. Study may use a specified local capture; demo HTML, demo JavaScript, external assets, and credential-shaped examples are excluded from this target.
- Directory-only links become concrete files in this tree (references/components, references/themes, and references/verbs). No synthetic index is introduced to hide a missing file.

## Review boundaries

- This is review work, not an active runtime installation.
- Candidate scripts, package setup, hooks, site server, external loads, and package managers were not executed.
- The upstream package snapshot and immutable quarantine are not modified by this adaptation.
- Runtime roots, registry, lock, and global/profile settings are outside this review.
- governance audit/parity remains the lead's promotion gate; a successful static adaptation check cannot mark this tree approved or active.
