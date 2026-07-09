# Artifact Contract

Every visual explanation must make its own reading contract explicit.

## Required Fields

Include these fields in `92_visual_explanation.md` or in the visible artifact:

```markdown
# <title>

## Reader

<who this is for>

## Question

<what the reader should understand>

## View

<chosen representation and why>

## Visual Grammar

- Position:
- Color:
- Line:
- Size:
- Motion:
- Grouping:

## Sources

- <source or evidence>

## Confidence

<high / medium / low, with reason>

## What Matters

<the 3-7 things the reader should notice>

## Details

<expandable details, table, notes, file map, or references>

## Omitted

<what was intentionally left out and why>
```

Use `not used` for visual grammar fields that do not apply.
Do not leave the meaning of colors, arrows, or motion implicit.

## Data Contract

When the artifact uses structured data, prefer this shape:

```json
{
  "title": "string",
  "reader": "string",
  "question": "string",
  "representation": "timeline | causal-chain | swimlane | map | matrix | dashboard | walkthrough | custom",
  "grammar": {
    "position": "string",
    "color": "string",
    "line": "string",
    "size": "string",
    "motion": "string",
    "grouping": "string"
  },
  "sources": [
    {
      "label": "string",
      "path": "string",
      "confidence": "high | medium | low",
      "note": "string"
    }
  ],
  "items": [],
  "relationships": [],
  "steps": [],
  "annotations": []
}
```

Only include arrays that the chosen representation needs.

## Naming Outputs

Default names:

- `92_visual_explanation.md`
- `92_visual_explanation.html`
- `92_visual_data.json`

If the task already has an artifact sequence, use the next number and keep the prefix stable.

## HTML Requirements

If generating HTML:

- first viewport must show the actual artifact, not a landing page
- controls must be visible when interactivity matters
- text must fit on desktop and mobile
- provide keyboard-accessible controls for replay or filtering
- include a static fallback section or visible summary
- avoid decorative gradients, abstract filler, and motion that does not carry meaning

## Markdown Requirements

If generating Markdown:

- put the core answer before implementation detail
- keep the visual block compact
- include a glossary if labels need domain knowledge
- include source paths or URLs for claims
- avoid unexplained arrows and overloaded icons

## Image Requirements

If generating an image:

- describe the exact process or concept to render
- include labels for the important parts
- avoid fake UI chrome unless the UI itself is the subject
- save the prompt or source description beside the artifact
- do not use generated imagery for claims that require precise numbers or exact topology
