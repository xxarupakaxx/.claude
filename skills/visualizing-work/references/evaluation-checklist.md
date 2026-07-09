# Evaluation Checklist

Use this before calling a visual explanation complete.

## One-Minute Test

The reader should be able to answer the main question in under one minute.

Check:

- The title names the subject, not the format.
- The first visible region contains the main artifact.
- The 3-7 most important facts are visible without opening details.
- The artifact does not require reading a long instruction block first.

## Cognitive Load Test

Check:

- Only necessary concepts are visible in the overview.
- Detail is available on demand or in a later section.
- Jargon is defined or replaced with plain labels.
- The artifact avoids split attention between distant labels and marks.
- It introduces sequence, hierarchy, or causality one layer at a time.

## Evidence Test

Check:

- Every important claim has a source path, URL, command output, or explicit user-provided basis.
- Low-confidence claims are labeled as low confidence.
- Missing evidence is reported as missing, not smoothed over.
- The artifact distinguishes observed facts from interpretation.

## Visual Grammar Test

Check:

- Color, size, line, position, grouping, and motion have explicit meanings.
- Color is never the only way to understand a status or change.
- Arrows indicate the right relationship: time, causality, dependency, ownership, or data movement.
- Reused visual marks always mean the same thing.

## Motion Test

Run this only when the artifact uses animation or replay.

Check:

- Playback can be paused and replayed.
- A scrubber or step controls exist when sequence matters.
- The current step is readable as text.
- Important changes are signaled with labels or summaries, not only motion.
- Reduced-motion or static reading still explains the sequence.

## Format Independence Test

Check:

- If Mermaid fails, the explanation still has text, table, or HTML fallback.
- If HTML cannot be opened, Markdown still explains the artifact.
- If generated imagery is unavailable, the source description is enough to recreate it.
- If an MCP viewer is unavailable, saved files remain useful.

## Final Report Requirements

Report:

- chosen representation
- artifact paths
- source confidence
- verification performed
- known limits
- whether an interactive viewer actually opened
