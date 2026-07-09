---
name: visualizing-work
description: Transforms complex work, code behavior, plans, incidents, research findings, or agent activity into a human-readable visual explanation. Use when the user asks to make processing easier to understand, visualize what is happening, show progress or causality visually, create an explainer, make an HTML view, or choose a better representation without assuming a fixed format.
allowed-tools: Read, Bash, Glob, Grep, Write, mcp__workflow-html-app__view-plan, mcp__workflow-html-app__view-diagram
---

# Visualizing Work

Create a visual explanation that helps a human understand what is happening.
The output format is chosen after understanding the reader's question, not before.

This skill is separate from `generate-state-diagram`.
Use `generate-state-diagram` only after deciding that a state or flow diagram is the right representation.

## Trigger

Use this skill when the user asks for:

- "処理内容をわかりやすく見たい"
- "何が起きているかを視覚化して"
- "進捗や因果を見えるようにして"
- "人間が簡単に理解できる形にして"
- "もっと理解しやすい見せ方を考えて"
- "HTMLで見たい", "replay", "timeline", "map", "dashboard", "storyboard"

Do not use this skill for decorative graphics, marketing visuals, or a diagram requested only as a fixed deliverable.

## Core Rule

Start from the human comprehension task.
Do not start from Mermaid, graph JSON, HTML, a timeline, or any other output format.

The first decision is:

```text
What must the reader understand faster after seeing this?
```

## Workflow

### 1. Define the Reader and Question

Identify:

- reader: developer, reviewer, PM, operator, future maintainer, or nontechnical stakeholder
- question: sequence, causality, ownership, risk, status, comparison, architecture, data movement, decision, or learning
- evidence: code, logs, commits, plan files, notes, screenshots, external sources, or user-provided context
- time pressure: quick glance, review meeting, handoff, debugging, onboarding, or decision

If the target reader or question is unclear and cannot be inferred from context, ask one concise question before producing the artifact.

### 2. Choose the Representation

Read `references/representation-catalog.md`.
Choose one primary representation and, when useful, one supporting representation.

Examples:

- sequence or progress -> timeline, replay, storyboard
- causality or root cause -> causal chain, fault tree, evidence ladder
- ownership or handoff -> swimlane, responsibility map
- architecture or dependency -> layered map, boundary map
- tradeoff or decision -> option matrix, decision tree
- risk or confidence -> heatmap, uncertainty map
- onboarding or learning -> progressive explanation, glossary map

Do not choose more than two visual metaphors unless the user explicitly asks for a dashboard.

### 3. Design the Artifact Contract

Read `references/artifact-contract.md`.

Every artifact must state:

- title
- reader and question
- visual grammar: what position, color, line, size, motion, or grouping means
- data source and confidence
- what changed or what matters
- how to inspect details
- what is intentionally omitted

Choose the delivery surface:

- Markdown with a compact visual block
- static HTML
- interactive HTML
- workflow-html-app viewer
- image or canvas
- table plus small multiples
- existing specialized skill such as `generate-state-diagram`, `generate-state-diagram-3d`, `viewing-plans`, or `generate-verification-guide`

### 4. Build the Smallest Useful Artifact

Prefer a stable overview plus inspectable details.
Use animation only when temporal change is the concept the reader must understand.

If using HTML, make the first screen useful without instructions.
If using motion, provide pause, replay, scrub, and a static fallback.
If using color, add labels or shapes so color is not the only carrier of meaning.
If using generated imagery, ground it in the real process and avoid abstract decoration.

### 5. Verify Comprehension

Read `references/evaluation-checklist.md`.

Before claiming completion, check:

- Can the reader answer the original question in under one minute?
- Is the visual grammar explained by the artifact itself?
- Are source and confidence visible?
- Are details available without cluttering the overview?
- Does the artifact avoid decorative motion or format-driven complexity?
- Does it degrade to text or static view when viewer features fail?

If a viewer, browser, or image generator was required but unavailable, save the source artifact and report the missing display step separately.

## Relationship to Other Skills

- Use `viewing-plans` when the task is workflow progress visibility.
- Use `generate-state-diagram` when the chosen representation is a static state or flow diagram.
- Use `generate-state-diagram-3d` when the chosen representation is a layered technical map or timeline replay.
- Use `generate-verification-guide` when the artifact is a checkable manual verification path.
- Use `research` or deep-research style investigation when the visual explanation depends on external facts, unfamiliar domains, or design precedents.

## Outputs

Save outputs in the active task memory directory when one exists:

- `92_visual_explanation.md`: explanation, visual grammar, sources, and reading guide
- `92_visual_explanation.html`: optional standalone or interactive artifact
- `92_visual_data.json`: optional structured data for replay, dashboard, map, or generated view

Use different filenames only when the surrounding workflow already has a stronger convention.

## Quality Bar

- The artifact answers a human question, not a tool's preferred format.
- The overview is understandable before opening details.
- The reader can trace claims back to evidence.
- The representation reduces cognitive load rather than adding spectacle.
- The result is usable even when Mermaid, graph rendering, animation, or MCP display is unavailable.
