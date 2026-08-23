# Graph JSON Schema for workflow-html-app 2.5D Diagrams

Use this schema for `91_state_diagram_3d.json`.

## Shape

```json
{
  "nodes": [
    {
      "id": "ui_submit",
      "label": "送信ボタン",
      "layer": "UI",
      "kind": "trigger",
      "why": "ユーザー操作が処理開始点になるため",
      "files": ["app/page.tsx"],
      "order": 0
    }
  ],
  "edges": [
    {
      "id": "ui_submit_to_action",
      "from": "ui_submit",
      "to": "api_action",
      "label": "フォーム送信",
      "type": "sync"
    }
  ],
  "timeline": {
    "unit": "phase",
    "steps": [
      {
        "id": "step_0",
        "at": 0,
        "label": "入力を送信",
        "timestamp": "phase 1",
        "summary": "ユーザー操作が処理の開始点になる。",
        "eventType": "trigger",
        "activeNodes": ["ui_submit"],
        "activeEdges": [],
        "changedNodes": ["ui_submit"],
        "counters": { "errors": 0, "fixes": 0 },
        "annotations": ["まだ永続化は行われていない。"]
      }
    ]
  }
}
```

## Node Fields

| field | required | description |
|-------|----------|-------------|
| `id` | yes | Stable ASCII ID. Prefer lower snake case or lower camel case. |
| `label` | yes | Short visible node label. |
| `layer` | yes | One of `UI`, `API`, `Domain`, `DB`, `External`, `Queue`, `Ops`, `Test`, `Unknown`. |
| `kind` | no | Role such as `trigger`, `command`, `decision`, `read`, `write`, `integration`, `retry`, `error`. |
| `why` | yes | Why the step exists. Avoid only restating the label. |
| `files` | no | Repository-relative file paths. |
| `order` | no | Numeric process order on the X axis. |

## Edge Fields

Use `edges[].id` when timeline steps need to reference a specific transition.

| field | required | description |
|-------|----------|-------------|
| `id` | no | Stable ASCII edge ID for timeline references. If omitted, the viewer derives one from `from`, `to`, and `label`. |
| `from` | yes | Source node ID. |
| `to` | yes | Target node ID. |
| `label` | no | Short transition label. |
| `type` | no | `sync`, `async`, or `error`. Defaults to `sync` in the viewer. |

## Timeline Fields

`timeline` is optional. Omit it for static 2.5D diagrams. When present, it drives the replay/scrubber view in `workflow-html-app`.

| field | required | description |
|-------|----------|-------------|
| `unit` | no | Display unit such as `phase`, `commit`, `second`, or `step`. |
| `steps` | yes | Ordered timeline steps. Keep this compact, usually 5-20 steps. |

## Timeline Step Fields

| field | required | description |
|-------|----------|-------------|
| `id` | yes | Stable ASCII step ID. |
| `at` | yes | Numeric position used for ordering and display. Playback advances step by step, not by elapsed time gaps between `at` values. |
| `label` | yes | Short visible step label. |
| `timestamp` | no | Human-readable timestamp, phase, or commit label. |
| `summary` | yes | What changed at this point and why it matters. |
| `eventType` | no | One of `normal`, `trigger`, `decision`, `error`, `fix`, `review`, or `apply`. |
| `activeNodes` | no | Node IDs that should be emphasized at this step. Unknown IDs are ignored by the viewer. |
| `activeEdges` | no | Edge IDs that should be emphasized at this step. Unknown IDs are ignored by the viewer. |
| `changedNodes` | no | Node IDs that changed compared with the previous step. |
| `changedEdges` | no | Edge IDs that changed compared with the previous step. |
| `counters` | no | Small numeric counters such as errors, fixes, reviews, commits. |
| `annotations` | no | Short notes shown in the timeline details pane. |

Timeline design rules:

- Keep SVG as the static overview. Do not force temporal detail into one SVG if it makes the chart unreadable.
- Use timeline steps for meaningful phase changes, failures, fixes, reviews, retries, commits, or user-visible transitions.
- Do not turn every commit or log line into a step unless each one changes the reader's understanding.
- Make `summary` useful when read alone; it is the fallback when animation is disabled.
- Use `eventType` and labels together. Do not rely on color alone.
- The viewer infers step-specific emphasis from `activeNodes`, `changedNodes`, `activeEdges`, and `changedEdges`.

## Validation Checklist

- `nodes` is a non-empty array.
- Every node ID is unique.
- Every edge references existing node IDs.
- Every `timeline.steps[].activeNodes` and `changedNodes` entry either references an existing node or is intentionally ignored by the viewer.
- Every `timeline.steps[].activeEdges` and `changedEdges` entry either references an existing edge ID or is intentionally ignored by the viewer.
- Layer names are exact; unknown layers should be `Unknown`.
- JSON has no comments or trailing commas.
- Labels are short enough to fit in node cards.
- `why` is useful when shown alone in the details pane.
- `timeline.steps` are sorted by numeric `at`; equal spacing is not required because playback is step-based.
- Timeline payloads are additive: removing `timeline` should still leave a valid static 2.5D graph.
