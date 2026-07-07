---
name: generate-state-diagram-3d
description: Generate a workflow-html-app MCP-backed 2.5D state diagram from branch changes. Use when the user asks for 3D/2.5D state diagrams, layered diagrams, graphJson output, workflow-html-app diagram viewer output, or a more inspectable alternative to flat Mermaid diagrams.
allowed-tools: Read, Bash, Glob, Grep, Write, mcp__workflow-html-app__view-diagram
---

# Generate State Diagram 3D

## Overview

Create a 2.5D layered state diagram for branch changes. This skill is separate from `generate-state-diagram`: the base skill owns Mermaid/Markdown diagrams, while this skill owns Graph JSON and the workflow-html-app 2.5D viewer path.

## Hard Requirement

Use `workflow-html-app MCP` for the interactive 2.5D view.

Call `mcp__workflow-html-app__view-diagram` with all three fields:

```text
mermaidCode: "<main Mermaid diagram>"
title: "<diagram title>"
graphJson: "<91_state_diagram_graph.json as a string>"
```

Do not treat hand-written static 3D HTML as the normal path. If `mcp__workflow-html-app__view-diagram` is unavailable, save the Markdown and Graph JSON artifacts, then report that interactive 2.5D display is blocked by the missing workflow-html-app MCP. Generate a static fallback only when the user explicitly asks for file-only output or fallback HTML.

## Outputs

Save these files in the task memory directory:

- `91_state_diagram_3d.md`: explanation, main Mermaid diagram, usage notes, glossary, and file map
- `91_state_diagram_graph.json`: Graph JSON consumed by workflow-html-app
- `91_state_diagram_3d.html`: optional fallback only when MCP display is unavailable or user asks for a standalone file

Do not overwrite `91_state_diagram.md` unless the user explicitly asks to replace the base Mermaid diagram output.

## Workflow

### Step 1: Inspect Branch Changes

Run:

```bash
git diff <BASE_BRANCH>...HEAD --stat
git log <BASE_BRANCH>..HEAD --oneline
```

Identify:

- workflow or orchestration layers
- stateful entities and status columns
- UI interactions and URL/client state
- API, Server Action, usecase, domain, and persistence boundaries
- external systems, queues, webhooks, cron, retry, and failure paths

### Step 2: Decide Layers

Use these layer names exactly where possible:

```text
UI / API / Domain / DB / External / Queue / Ops / Test / Unknown
```

Map the axes as:

| Axis | Meaning |
|------|---------|
| X | process order from trigger to final result |
| Y | parallel branches or same-step alternatives |
| Z | technical layer boundary |

### Step 3: Create Mermaid Context

Create a compact main Mermaid diagram to act as the 2D reference in the viewer. Use `stateDiagram-v2` for lifecycle/state-heavy flows and `flowchart LR` for data-heavy flows.

Read `references/mermaid-syntax.md` before writing Mermaid if the diagram contains Japanese labels, special characters, nested state blocks, or class/entity relationships.

Validate Mermaid using `references/validator-loop.md` when a Mermaid validator MCP is available. If validation is unavailable, keep syntax conservative and mention that live validation was not available.

### Step 4: Create Graph JSON

Read `references/graph-json-schema.md` before building `91_state_diagram_graph.json`.

Graph JSON rules:

- Every node must have `id`, `label`, `layer`, and `why`.
- `why` must explain why the step exists, not just what it does.
- `files` should use repository-relative paths.
- `order` should be stable and roughly monotonic along the main path.
- Every edge must reference existing node IDs.
- Use `type: "async"` for queue/event/background work and `type: "error"` for failure paths.

### Step 5: Save Files

Save `91_state_diagram_3d.md` with:

- purpose and branch
- main Mermaid diagram
- short explanation of how to read the 2.5D view
- glossary
- file map
- Graph JSON file path
- workflow-html-app MCP invocation summary

Save `91_state_diagram_graph.json` as strict JSON with no comments.

### Step 6: Display With MCP

Call:

```text
mcp__workflow-html-app__view-diagram(
  mermaidCode: "<main Mermaid diagram>",
  title: "<feature name> 2.5D state diagram",
  graphJson: "<contents of 91_state_diagram_graph.json>"
)
```

This call is required for normal completion. The final report must say whether the MCP viewer was displayed.

## Quality Bar

- Mermaid remains readable as a flat fallback.
- Graph JSON opens in workflow-html-app without breaking Mermaid display.
- Layer placement helps comprehension; do not create arbitrary decorative 3D.
- The reader can click a node and understand why it exists, what files implement it, and what it connects to.
- Failure and retry paths are represented when they affect state or user-visible behavior.
- If Graph JSON is invalid or the MCP is unavailable, do not claim the 2.5D view was delivered.
