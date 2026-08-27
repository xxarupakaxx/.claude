import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const serverSource = readFileSync(new URL("../server.ts", import.meta.url), "utf8");
const viewerSource = readFileSync(new URL("../ui/plan-viewer.html", import.meta.url), "utf8");

test("Claude-compatible serverはPlanとLogを別resource URIで公開する", () => {
  assert.match(serverSource, /"view-plan"/);
  assert.match(serverSource, /"view-log"/);
  assert.match(serverSource, /ui:\/\/plan-viewer\/index\.html/);
  assert.match(serverSource, /ui:\/\/log-viewer\/index\.html/);
});

test("Claude-compatible viewerはPlanとLogを識別しsanitizeする", () => {
  assert.match(viewerSource, /function detectDocumentKind\(markdown\)/);
  assert.match(viewerSource, /commentPrefix: 'Plan Comment'/);
  assert.match(viewerSource, /commentPrefix: 'Log Comment'/);
  assert.match(viewerSource, /DOMPurify\.sanitize/);
});
