import { readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";
import assert from "node:assert/strict";

const root = new URL("..", import.meta.url).pathname;

function read(relativePath) {
  return readFileSync(join(root, relativePath), "utf8");
}

function readFirst(relativePaths) {
  const errors = [];
  for (const relativePath of relativePaths) {
    try {
      return read(relativePath);
    } catch (error) {
      errors.push(`${relativePath}: ${error.code}`);
    }
  }
  throw new Error(`none of the candidate files could be read: ${errors.join(", ")}`);
}

test("view-diagram accepts optional graphJson and forwards it to the UI payload", () => {
  const server = read("server.ts");

  assert.match(server, /graphJson:\s*z\.string\(\)\.optional\(\)/);
  assert.match(server, /async\s*\(\{\s*mermaidCode,\s*title,\s*graphJson\s*\}\)/);
  assert.match(server, /JSON\.stringify\(\{\s*mermaidCode,\s*title:[^}]+graphJson/s);
});

test("diagram viewer exposes the 2.5D graph UI contract", () => {
  const html = read("ui/diagram-viewer.html");

  assert.match(html, /id="view-mermaid"/);
  assert.match(html, /id="view-graph"/);
  assert.match(html, /id="view-timeline"/);
  assert.match(html, /id="layer-filters"/);
  assert.match(html, /id="node-details"/);
  assert.match(html, /id="timeline-panel"/);
  assert.match(html, /id="timeline-slider"/);
  assert.match(html, /id="timeline-play"/);
  assert.match(html, /id="timeline-prev-event"/);
  assert.match(html, /id="timeline-next-event"/);
  assert.match(html, /function renderGraph3d/);
  assert.match(html, /function normalizeTimeline/);
  assert.match(html, /function applyTimelineStep/);
  assert.match(html, /function copyGraphJson/);
  assert.match(html, /setPointerCapture/);
});

test("diagram viewer keeps Mermaid rendering independent from optional graph parsing", () => {
  const html = read("ui/diagram-viewer.html");
  const mermaidIndex = html.indexOf("renderDiagram(data.mermaidCode)");
  const graphIndex = html.indexOf("normalizeGraph(data.graphJson)");

  assert.notEqual(mermaidIndex, -1);
  assert.notEqual(graphIndex, -1);
  assert.ok(mermaidIndex < graphIndex, "Mermaid must render before optional graph parsing");
  assert.match(html, /currentGraph\s*=\s*null/);
});

test("diagram viewer keeps timeline replay optional and step based", () => {
  const html = read("ui/diagram-viewer.html");

  assert.match(html, /viewTimelineEl\.hidden\s*=\s*!graph\.timeline/);
  assert.match(html, /timelinePanelEl\.hidden\s*=\s*!isTimeline/);
  assert.match(html, /requestAnimationFrame\(tickTimeline\)/);
  assert.match(html, /prefers-reduced-motion: reduce/);
  assert.match(html, /changedNodes/);
  assert.match(html, /changedEdges/);
  assert.match(html, /activeNodes/);
  assert.match(html, /activeEdges/);
});

test("build step emits the static diagram viewer used by the dist server", () => {
  const packageJson = JSON.parse(read("package.json"));
  const copyScript = read("scripts/copy-static-ui.mjs");

  assert.match(packageJson.scripts["build:ui"], /copy-static-ui\.mjs/);
  assert.match(copyScript, /diagram-viewer\.html/);
  assert.match(copyScript, /verification-viewer\.html/);
});

test("generate-state-diagram-3d documents graph JSON and requires workflow-html-app MCP", () => {
  const skill = readFirst([
    "../../../skills/generate-state-diagram-3d/SKILL.md",
    "../../skills/generate-state-diagram-3d/SKILL.md",
  ]);

  assert.match(skill, /91_state_diagram_graph\.json/);
  assert.match(skill, /91_state_diagram_3d\.html/);
  assert.match(skill, /graphJson/);
  assert.match(skill, /2\.5D/);
  assert.match(skill, /UI \/ API \/ Domain \/ DB \/ External/);
  assert.match(skill, /workflow-html-app MCP/);
  assert.match(skill, /mcp__workflow-html-app__view-diagram/);
  assert.match(skill, /timeline/);
  assert.match(skill, /replay/);
});

test("base generate-state-diagram stays Mermaid-focused and does not own graphJson output", () => {
  const skill = readFirst([
    "../../../skills/generate-state-diagram/SKILL.md",
    "../../skills/generate-state-diagram/SKILL.md",
  ]);

  assert.doesNotMatch(skill, /91_state_diagram_graph\.json/);
  assert.doesNotMatch(skill, /graphJson/);
  assert.match(skill, /generate-state-diagram-3d/);
});

test("graph JSON schema documents additive timeline replay fields", () => {
  const schema = readFirst([
    "../../../skills/generate-state-diagram-3d/references/graph-json-schema.md",
    "../../skills/generate-state-diagram-3d/references/graph-json-schema.md",
  ]);

  assert.match(schema, /Timeline Fields/);
  assert.match(schema, /Timeline Step Fields/);
  assert.match(schema, /edges\[\]\.id/);
  assert.match(schema, /step-based/);
  assert.match(schema, /activeNodes/);
  assert.match(schema, /changedEdges/);
  assert.doesNotMatch(schema, /startStep/);
  assert.doesNotMatch(schema, /focusStep/);
  assert.doesNotMatch(schema, /endStep/);
});
