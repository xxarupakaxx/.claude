---
name: diagram-design
description: Creates a task-local static editorial visual after visualizing-work has selected that representation. Use for an evidence-backed explainer, comparison, timeline, causal view, or ownership view when spatial grouping reduces cognitive load; never for Roadmap, canonical state, or 3D graph artifacts.
allowed-tools: Read, Write
---

# Diagram Design Adapter

Create the smallest static visual explanation that helps the named reader answer the named question.

This is a locally authored, static-only adapter informed by the recorded upstream revision. Do not execute or import upstream files.

## Entry Conditions

Use this skill only when all conditions hold:

- `visualizing-work` selected a static editorial SVG sidecar after choosing the representation.
- The reader, question, evidence, confidence, and omitted scope are known.
- Spatial grouping materially helps explain a small comparison, timeline, causal, ownership, or concept view.
- The output is not a workflow Roadmap, canonical state or flow diagram, layered technical map, timeline replay, or viewer integration.
- When `generate-state-diagram` calls this adapter, `91_state_diagram.*` is complete and the sidecar answers a distinct reader question.
- When `viewing-plans` calls this adapter, `roadmap.html` is complete and the sidecar answers a distinct reader question.

Otherwise return to `visualizing-work` or use the specialized owner skill.

## Required Output

Always create or update the active task's `92_visual_explanation.md` first. Follow the `visualizing-work` artifact contract: explain the visual grammar, sources, confidence, and omissions in readable Markdown.

When a distinct companion already occupies that path, use the next available numbered visual explanation paths instead of overwriting it.

Create `92_visual_explanation.svg` as the visual source of truth.
Create `92_visual_explanation.html` beside it only when inline SVG and surrounding text make the answer faster to understand. Put the answer in the first visible region, never an onboarding page or style guide.

## Static-Safety Boundary

- Use only local evidence supplied to the task and a system font stack with inline CSS.
- Do not use JavaScript, event attributes, iframes, `foreignObject`, external stylesheets, external images or icons, web fonts, URL onboarding, browser automation, Playwright export, or upstream scripts.
- Keep SVG self-contained with `viewBox`, `title`, `desc`, and XML-escaped evidence text.
- Do not create or modify shared style guides, global configuration, plugin caches, or viewer servers.
- Write only the selected task-local visual explanation paths above.
- Escape evidence-derived text for its exact HTML context. Keep anything unsafe in the Markdown explanation.
- Use labels, shape, and text in addition to color. Include a visible text summary or link to the Markdown fallback in every HTML artifact.

## Build Order

1. Read the `visualizing-work` artifact contract.
2. Write the Markdown artifact contract and evidence summary.
3. Produce one stable SVG overview and at most one supporting SVG view.
4. Add static HTML with the same inline SVG only when it reduces comprehension time.
5. Check the first viewport, text fallback, visual grammar, and source traceability before completion.

## Ownership Boundary

- `viewing-plans` owns workflow progress visibility and Roadmap artifacts.
- `generate-state-diagram` owns canonical static state and flow artifacts.
- `generate-state-diagram-3d` owns layered technical maps and timeline replay artifacts.
- This adapter owns only an optional task-local editorial sidecar.
- After `generate-state-diagram`, this adapter never redraws canonical states, transitions, or SVG flows.
- After `viewing-plans`, this adapter never redraws canonical Roadmap task order, progress, or Concept Map.
