# Representation Catalog

Choose the visual representation from the reader's question.
Do not begin with a rendering format.

## Sequence and Progress

Use when the reader asks "what happened when?" or "where are we now?"

Good forms:

- timeline
- replay
- storyboard
- progress rail
- commit or phase strip

Best for:

- agent workflows
- migrations
- incident response
- debugging history
- UI state over time
- phased delivery

Avoid:

- animating every log line
- moving the camera while also changing state
- hiding the final state behind playback

## Causality

Use when the reader asks "why did this happen?" or "what caused what?"

Good forms:

- causal chain
- fault tree
- fishbone
- evidence ladder
- before and after contrast

Best for:

- root-cause analysis
- performance regressions
- failure recovery
- bug investigations
- policy or process consequences

Avoid:

- implying certainty when evidence is weak
- flattening multiple causes into one arrow
- showing correlation as causation

## Ownership and Handoff

Use when the reader asks "who or what owns each step?"

Good forms:

- swimlane
- responsibility map
- queue or handoff board
- role-to-artifact matrix

Best for:

- multi-agent work
- team processes
- review loops
- customer support escalation
- operations handoff

Avoid:

- making technical layers look like owners
- hiding ambiguous ownership

## Structure and Boundaries

Use when the reader asks "what are the parts and boundaries?"

Good forms:

- layered map
- boundary map
- system context map
- dependency map
- concept map

Best for:

- architecture explanation
- module boundaries
- domain models
- integration surfaces
- onboarding

Avoid:

- showing every file as a node
- using depth or 3D only as decoration

## Decisions and Tradeoffs

Use when the reader asks "which option should we choose?"

Good forms:

- option matrix
- decision tree
- weighted tradeoff table
- constraint map
- go or no-go board

Best for:

- design alternatives
- vendor or tool selection
- scope decisions
- product tradeoffs

Avoid:

- fake precision
- hiding the decision criterion

## Risk, Confidence, and Attention

Use when the reader asks "what should I look at first?"

Good forms:

- risk heatmap
- confidence map
- review heat
- uncertainty ribbon
- attention queue

Best for:

- reviews
- planning
- status reporting
- research synthesis
- operational monitoring

Avoid:

- color-only encoding
- mixing severity, likelihood, and confidence without labels

## Learning and Onboarding

Use when the reader asks "how do I understand this from scratch?"

Good forms:

- progressive explanation
- ladder of abstraction
- glossary map
- annotated walkthrough
- worked example

Best for:

- new joiner docs
- complex domain notes
- unfamiliar codebases
- research notes

Avoid:

- jumping from overview directly to implementation details
- using unexplained jargon in labels

## Delivery Surface Selection

Use Markdown when:

- the artifact must live well in GitHub, Obsidian, or a PR
- static reading is enough
- the most important value is durable explanation

Use static HTML when:

- layout, filtering, or visual hierarchy matters
- the user should open a single file
- no live tool surface is guaranteed

Use interactive HTML when:

- the reader needs zoom, filtering, hover details, replay, or step selection
- the artifact is dense but should stay explorable

Use workflow-html-app when:

- the current Codex/Cowork environment can render it
- existing plan, verification, or diagram viewers match the chosen representation

Use generated imagery when:

- the concept is spatial, physical, or memorable
- precision is less important than first-glance comprehension

Use a specialized skill when:

- an existing skill already owns the chosen artifact contract
- reuse gives better verification than a bespoke artifact

## Research Notes

- Cognitive load theory suggests that working memory is limited, so visual explanations should reduce extraneous load and introduce complexity gradually.
- Instructional visualization research distinguishes static and dynamic visualizations; motion can engage, but engagement alone does not guarantee learning.
- Change blindness research warns that users can miss large changes when attention is elsewhere, so changed items need explicit signaling.
- Dashboard guidance emphasizes preattentive visual processing for fast scanning.
- Bret Victor style explorable explanations suggest linking concrete examples with higher-level abstractions instead of forcing a single level.

Useful source families:

- NASA TLX for subjective workload framing.
- Nielsen Norman Group for attention, change blindness, dashboards, and animation cautions.
- Bret Victor's explorable explanations for linked representations and ladder-of-abstraction thinking.
- Instructional visualization and cognitive load literature for managing complexity.

Source URLs checked during skill creation:

- https://www.nasa.gov/human-systems-integration-division/nasa-task-load-index-tlx/
- https://www.nngroup.com/articles/change-blindness/
- https://www.nngroup.com/videos/data-visualizations-dashboards/
- https://worrydream.com/
- https://research.birmingham.ac.uk/en/publications/instructional-visualizations-cognitive-load-theory-and-visuospati/
