# Graph JSON Schema for workflow-html-app 2.5D Diagrams

Use this schema for `91_state_diagram_graph.json`.

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
      "from": "ui_submit",
      "to": "api_action",
      "label": "フォーム送信",
      "type": "sync"
    }
  ]
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

| field | required | description |
|-------|----------|-------------|
| `from` | yes | Source node ID. |
| `to` | yes | Target node ID. |
| `label` | no | Short transition label. |
| `type` | no | `sync`, `async`, or `error`. Defaults to `sync` in the viewer. |

## Validation Checklist

- `nodes` is a non-empty array.
- Every node ID is unique.
- Every edge references existing node IDs.
- Layer names are exact; unknown layers should be `Unknown`.
- JSON has no comments or trailing commas.
- Labels are short enough to fit in node cards.
- `why` is useful when shown alone in the details pane.
