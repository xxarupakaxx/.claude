---
name: one-page-concept-sketch
description: Create a single hand-drawn, black-and-white concept sketch that makes an idea understandable at a glance. Use when the user asks for an image, diagram, infographic, explainer sheet, one-page summary, whiteboard-style visual, handwritten Japanese style, sketchnote, or "one image that shows what this is about"; also use when turning a concept, article, decision rule, product idea, architecture principle, or meeting insight into a compact visual artifact.
---

# One Page Concept Sketch

## Goal

Turn an idea into one readable image that explains the concept, not a decorative poster.

Optimize for three outcomes:

- A reader can say what the topic is within 3 seconds.
- A reader can explain the core mechanism within 30 seconds.
- The visual still works when viewed as a screenshot on a phone.

## Output Mode

Choose the production mode before drafting.

- Use SVG or HTML/CSS when exact Japanese text, labels, or long explanations must be readable.
- Use image generation when the user mainly wants a bitmap illustration, mood, or rough visual direction.
- Use a prompt plus layout spec when the user asks for guidance rather than an actual file.

If using an image generation tool, keep text short and expect to manually revise or rebuild text-heavy areas as SVG/HTML if legibility fails.

## Structure

Use this layout grammar by default:

1. Title at top center.
2. One-line subtitle that states the claim.
3. Two or three numbered sections separated by thin horizontal rules.
4. Each section contains a left-to-right causal flow, comparison, or timeline.
5. Put one boxed "Point" note on the right side of each main section.
6. End with a bottom summary band that names the takeaway and action.

Prefer a single argument over a catalog.
If the source has many ideas, select the one tension that explains the rest.

## Visual Language

Use a restrained hand-drawn style:

- White or warm-white background.
- Black ink only, with gray allowed for secondary guide lines.
- Thin, slightly imperfect strokes.
- Rounded rectangles, speech bubbles, arrows, timelines, simple stick figures, and small charts.
- Handwritten-looking Japanese and Latin text, monoline, rounded, with generous spacing.
- No gradients, glossy effects, stock illustration, heavy shadows, or dense color palettes.

The reference feel is a clear sketchnote or whiteboard explainer: structured, calm, and legible.
Do not copy a supplied reference image; borrow only the layout logic and visual constraints.

## Content Compression

Before drawing, reduce the idea to:

- **Title**: concrete subject name.
- **Claim**: one sentence that changes how the reader thinks.
- **Mechanism**: two or three steps that explain why the claim is true.
- **Contrast**: wrong intuition versus better framing.
- **Takeaway**: what to preserve, avoid, decide, or do next.

Delete supporting details that do not help the mechanism.
If a sentence cannot fit in a small label, turn it into a shorter noun phrase or move it to a point box.

## Text Rules

Keep labels short.

- Title: 6 to 14 Japanese characters, or 2 to 5 English words.
- Subtitle: one line.
- Box labels: 3 to 12 characters where possible.
- Point boxes: up to 5 short lines.
- Body captions: one idea per line.

Avoid long prose inside the image.
If a concept needs long prose, make the image simpler and provide the prose outside the image.

## Common Patterns

Use one of these patterns:

- **Cost of early commitment**: show "decide now" losing options versus "wait for information" preserving choices.
- **Before/after**: show the old model on the left and the better model on the right.
- **Trade-off map**: show two axes, the risky zone, and the recommended zone.
- **Lifecycle**: show how a thing moves through states over time.
- **System loop**: show inputs, process, feedback, and failure point.
- **Decision rule**: show a branch and the criterion that chooses the branch.

Do not mix more than two patterns in one image.

## Workflow

1. Extract the concept and write the compression bullets.
2. Choose one common pattern.
3. Draft the layout as text first: title, subtitle, sections, point boxes, summary band.
4. Produce the artifact in the chosen output mode.
5. Check legibility at small size.
6. Remove any decorative element that does not explain the idea.

## Image Generation Prompt Template

Use this template when generating a bitmap:

```text
A single-page black-and-white hand-drawn concept sketch on a clean white background.
Topic: [topic].
Title at top center: [short title].
Subtitle: [one-line claim].
Layout: [two or three numbered sections], separated by thin horizontal rules, with simple arrows, rounded boxes, tiny stick figures, speech bubbles, timelines, and one boxed "Point" note on the right of each section.
Style: Japanese sketchnote, neat handwritten monoline lettering, thin imperfect black ink, generous spacing, readable labels, calm whiteboard explainer.
Content:
1. [section 1 labels and flow]
2. [section 2 labels and flow]
Bottom summary band: [takeaway].
Avoid color, gradients, shadows, dense text, photorealism, and decorative clutter.
```

For Japanese-heavy images, shorten the text further or create SVG/HTML instead.

## Quality Check

Pass the artifact only if all checks are true:

- The title and subtitle are readable at phone width.
- The main claim is visible without reading every caption.
- Arrows show cause, time, or choice clearly.
- Right-side point boxes add judgment, not repetition.
- The bottom summary band contains the practical takeaway.
- No section has more than one main message.
- The visual style is hand-drawn and monochrome, not a slide deck or marketing hero.
