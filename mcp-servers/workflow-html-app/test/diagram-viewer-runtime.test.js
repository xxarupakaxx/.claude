import { resolve } from "node:path";
import test from "node:test";
import assert from "node:assert/strict";
import { chromium } from "playwright";

const htmlPath = resolve("ui/diagram-viewer.html");

const mermaidCode = `stateDiagram-v2
    [*] --> Request
    Request --> API : Submit
    API --> Domain : Validate
    Domain --> DB : Save
    DB --> [*] : Persisted`;

const legacyGraph = {
  nodes: [
    { id: "ui", label: "Submit form", layer: "UI", why: "User intent starts the workflow.", order: 0 },
    { id: "api", label: "Server action", layer: "API", why: "The API boundary validates input.", order: 1 },
  ],
  edges: [
    { id: "ui_api", from: "ui", to: "api", label: "submit", type: "sync" },
  ],
};

const timelineGraph = {
  ...legacyGraph,
  timeline: {
    unit: "phase",
    steps: [
      {
        id: "step_0",
        at: 10,
        label: "Submit",
        timestamp: "phase 1",
        summary: "The UI starts the workflow.",
        eventType: "trigger",
        activeNodes: ["ui"],
        changedNodes: ["ui"],
      },
      {
        id: "step_1",
        at: 30,
        label: "Validate",
        timestamp: "phase 2",
        summary: "The API validates the request.",
        eventType: "review",
        activeNodes: ["api"],
        activeEdges: ["ui_api"],
        changedNodes: ["api"],
        changedEdges: ["ui_api"],
      },
    ],
  },
};

async function withPage(t, callback) {
  let browser;
  try {
    browser = await chromium.launch({ channel: "chrome", headless: true });
  } catch (error) {
    t.diagnostic(`System Chrome launch failed; trying bundled Chromium. ${error.message}`);
    browser = await chromium.launch({ headless: true });
  }
  try {
    const page = await browser.newPage({ viewport: { width: 960, height: 720 } });
    await page.goto(`file://${htmlPath}`);
    await page.waitForFunction(() => document.querySelector("#title")?.textContent === "Demo 2.5D State Diagram");
    await callback(page);
    await page.close();
  } finally {
    await browser.close();
  }
}

async function sendPayload(page, payload) {
  await page.evaluate((payloadText) => {
    window.dispatchEvent(new MessageEvent("message", {
      origin: "file://",
      data: {
        type: "tool-result",
        content: [{ type: "text", text: payloadText }],
      },
    }));
  }, JSON.stringify(payload));
  await page.waitForFunction((title) => document.querySelector("#title")?.textContent === title, payload.title);
}

test("legacy graph payload keeps timeline controls hidden", async (t) => {
  await withPage(t, async (page) => {
    await sendPayload(page, {
      mermaidCode,
      title: "Legacy Graph",
      graphJson: JSON.stringify(legacyGraph),
    });

    await page.waitForSelector("#view-graph:not([hidden])");
    await page.waitForFunction(() => document.querySelector("#view-timeline")?.hidden === true);
    const state = await page.evaluate(() => ({
      timelineHidden: document.querySelector("#view-timeline")?.hidden,
      graphNodes: document.querySelectorAll(".graph-node").length,
      graphVisible: document.querySelector("#view-graph")?.classList.contains("active"),
    }));

    assert.equal(state.timelineHidden, true);
    assert.equal(state.graphNodes, 2);
    assert.equal(state.graphVisible, true);
  });
});

test("timeline payload exposes replay controls and step-driven graph state", async (t) => {
  await withPage(t, async (page) => {
    await sendPayload(page, {
      mermaidCode,
      title: "Timeline Graph",
      graphJson: JSON.stringify(timelineGraph),
    });

    await page.waitForSelector("#view-timeline:not([hidden])");
    await page.click("#view-timeline");
    await page.click("#timeline-next");

    const state = await page.evaluate(() => ({
      caption: document.querySelector("#timeline-caption")?.textContent,
      ariaValue: document.querySelector("#timeline-slider")?.getAttribute("aria-valuetext"),
      activeNodes: [...document.querySelectorAll(".graph-node.timeline-active")].map((node) => node.dataset.id),
      changedEdges: document.querySelectorAll("[data-edge-id].timeline-changed").length,
      timelineLive: document.querySelector("#timeline-live")?.textContent,
    }));

    assert.match(state.caption, /2\/2/);
    assert.match(state.ariaValue, /Validate/);
    assert.deepEqual(state.activeNodes, ["api"]);
    assert.ok(state.changedEdges > 0);
    assert.match(state.timelineLive, /API validates/);
  });
});

test("invalid timeline falls back to static graph without hiding Mermaid", async (t) => {
  await withPage(t, async (page) => {
    await sendPayload(page, {
      mermaidCode,
      title: "Invalid Timeline",
      graphJson: JSON.stringify({ ...legacyGraph, timeline: { steps: "bad" } }),
    });

    await page.waitForSelector("#view-graph:not([hidden])");
    await page.waitForFunction(() => /Timeline invalid/.test(document.querySelector("#status")?.textContent || ""));
    await page.waitForSelector("#diagram svg", { state: "attached" });
    const state = await page.evaluate(() => ({
      status: document.querySelector("#status")?.textContent,
      timelineHidden: document.querySelector("#view-timeline")?.hidden,
      mermaidSvg: document.querySelectorAll("#diagram svg").length,
      graphNodes: document.querySelectorAll(".graph-node").length,
    }));

    assert.match(state.status, /Timeline invalid/);
    assert.equal(state.timelineHidden, true);
    assert.equal(state.mermaidSvg, 1);
    assert.equal(state.graphNodes, 2);
  });
});
