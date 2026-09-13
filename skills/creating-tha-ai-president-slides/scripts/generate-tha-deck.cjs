#!/usr/bin/env node

"use strict";

const fs = require("node:fs");
const path = require("node:path");

const REQUIRED_PPTXGENJS_VERSION = "4.0.1";
const W = 13.333;
const H = 7.5;
const C = Object.freeze({
  primary: "1A5CF0",
  deep: "0053DA",
  navy: "1E2A44",
  highlight: "FFE600",
  cardTint: "F4F8FF",
  border: "DCE6FB",
  body: "46546E",
  muted: "A7B0BE",
  white: "FFFFFF",
  pale: "EEF4FF",
  before: "F1F3F6",
});

function fail(message) {
  console.error(`ERROR: ${message}`);
  process.exit(1);
}

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--help" || arg === "-h") out.help = true;
    else if (arg === "--input") out.input = argv[++i];
    else if (arg === "--output") out.output = argv[++i];
    else fail(`Unknown argument: ${arg}`);
  }
  return out;
}

function packageVersion(resolvedPath) {
  let dir = path.dirname(resolvedPath);
  while (dir !== path.dirname(dir)) {
    const candidate = path.join(dir, "package.json");
    if (fs.existsSync(candidate)) {
      const pkg = JSON.parse(fs.readFileSync(candidate, "utf8"));
      if (pkg.name === "pptxgenjs") return pkg.version;
    }
    dir = path.dirname(dir);
  }
  return null;
}

function loadPptxGenJS() {
  const candidates = ["pptxgenjs"];
  const nodePaths = (process.env.NODE_PATH || "")
    .split(path.delimiter)
    .filter(Boolean);
  for (const nodePath of nodePaths) {
    candidates.push(path.join(nodePath, "pptxgenjs"));
  }
  candidates.push(
    path.join(
      process.env.HOME || "",
      ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/pptxgenjs",
    ),
  );

  const errors = [];
  for (const candidate of candidates) {
    try {
      const resolved = require.resolve(candidate);
      const version = packageVersion(resolved);
      if (version !== REQUIRED_PPTXGENJS_VERSION) {
        errors.push(`${candidate}: found ${version || "unknown version"}`);
        continue;
      }
      return require(candidate);
    } catch (error) {
      errors.push(`${candidate}: ${error.code || error.message}`);
    }
  }
  fail(
    `pptxgenjs@${REQUIRED_PPTXGENJS_VERSION} is required. ` +
      "Set NODE_PATH to a node_modules directory containing that exact version, " +
      "or install the pinned dependency from this skill's package.json.\n" +
      errors.join("\n"),
  );
}

function readJson(filePath) {
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch (error) {
    fail(`Cannot read JSON ${filePath}: ${error.message}`);
  }
}

function requireString(value, name, max) {
  if (typeof value !== "string" || value.trim() === "") {
    fail(`${name} must be a non-empty string`);
  }
  if ([...value].length > max) {
    fail(`${name} exceeds ${max} characters`);
  }
  return value;
}

function optionalString(value, name, max) {
  if (value === undefined || value === null || value === "") return "";
  return requireString(value, name, max);
}

function requireArray(value, name, count) {
  if (!Array.isArray(value) || value.length !== count) {
    fail(`${name} must contain exactly ${count} items`);
  }
  return value;
}

function validateSources(sourcesValue) {
  const sources = sourcesValue === undefined ? [] : sourcesValue;
  if (!Array.isArray(sources)) fail("sources must be an array");
  const byId = new Map();
  sources.forEach((source, index) => {
    const prefix = `sources[${index}]`;
    const id = requireString(source.id, `${prefix}.id`, 40);
    if (byId.has(id)) fail(`${prefix}.id is duplicated: ${id}`);
    if (!["web", "internal", "fictional"].includes(source.kind)) {
      fail(`${prefix}.kind must be web, internal, or fictional`);
    }
    requireString(source.title, `${prefix}.title`, 120);
    if (source.kind === "web") {
      requireString(source.url, `${prefix}.url`, 300);
      requireString(source.accessed, `${prefix}.accessed`, 10);
    } else {
      optionalString(source.url, `${prefix}.url`, 300);
      optionalString(source.accessed, `${prefix}.accessed`, 10);
    }
    optionalString(source.note, `${prefix}.note`, 160);
    byId.set(id, source);
  });
  return byId;
}

function svgData(svg) {
  return `data:image/svg+xml;base64,${Buffer.from(svg).toString("base64")}`;
}

function gradientSvg() {
  return svgData(
    `<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900">` +
      `<defs><linearGradient id="g" x1="0" y1="1" x2="1" y2="0">` +
      `<stop offset="0" stop-color="#0053DA"/>` +
      `<stop offset="1" stop-color="#39A5F3"/>` +
      `</linearGradient></defs><rect width="1600" height="900" fill="url(#g)"/>` +
      `</svg>`,
  );
}

function text(slide, value, x, y, w, h, options = {}) {
  slide.addText(value, {
    x,
    y,
    w,
    h,
    margin: 0,
    valign: "mid",
    breakLine: false,
    fit: "shrink",
    fontFace: options.fontFace,
    fontSize: options.fontSize,
    bold: options.bold,
    color: options.color,
    align: options.align || "left",
    valign: options.valign || "mid",
    isTextBox: true,
    paraSpaceAfterPt: 0,
    ...options,
  });
}

function box(slide, S, x, y, w, h, options = {}) {
  slide.addShape(S.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.14,
    fill: { color: options.fill || C.white },
    line: { color: options.line || C.border, width: options.lineWidth || 1 },
  });
}

function addHeader(slide, theme, data) {
  text(slide, optionalString(data.kicker, "kicker", 40) || "AI PRESIDENT", 0.68, 0.38, 3.7, 0.22, {
    fontFace: theme.fontDisplay,
    fontSize: 11,
    bold: true,
    color: C.primary,
    charSpacing: 1.1,
  });
  text(slide, requireString(data.title, "title", 44), 0.68, 0.7, 11.7, 0.58, {
    fontFace: theme.fontBody,
    fontSize: 29,
    bold: true,
    color: C.navy,
  });
  slide.addShape(theme.S.line, {
    x: 0.68,
    y: 1.4,
    w: 11.98,
    h: 0,
    line: { color: C.border, width: 1 },
  });
}

function addFooter(slide, theme, meta, pageNumber) {
  text(slide, meta.label || meta.title || "AI PRESIDENT", 0.68, 7.12, 5, 0.18, {
    fontFace: theme.fontDisplay,
    fontSize: 9,
    color: C.muted,
  });
  text(slide, String(pageNumber).padStart(2, "0"), 11.98, 7.12, 0.68, 0.18, {
    fontFace: theme.fontDisplay,
    fontSize: 9,
    color: C.muted,
    align: "right",
  });
}

function addNotes(slide, data, sourcesById) {
  const notes = [];
  const speakerNotes = optionalString(data.speakerNotes, "speakerNotes", 600);
  if (speakerNotes) notes.push(speakerNotes);
  const sourceIds = data.sourceIds === undefined ? [] : data.sourceIds;
  if (!Array.isArray(sourceIds)) fail("sourceIds must be an array");
  if (new Set(sourceIds).size !== sourceIds.length) fail("sourceIds must not contain duplicates");
  if (sourceIds.length) {
    notes.push(
      "SOURCES\n" +
        sourceIds
          .map((id) => {
            const source = sourcesById.get(id);
            if (!source) fail(`Unknown sourceId: ${id}`);
            const parts = [`[${id}]`, source.title];
            if (source.url) parts.push(source.url);
            if (source.accessed) parts.push(`accessed ${source.accessed}`);
            if (source.note) parts.push(source.note);
            return `- ${parts.join(" | ")}`;
          })
          .join("\n"),
    );
  }
  if (notes.length) slide.addNotes(notes);
}

function cover(slide, theme, data) {
  slide.background = { color: C.white };
  text(slide, optionalString(data.eyebrow, "eyebrow", 40) || "AI × MANAGEMENT", 0.68, 0.55, 4, 0.28, {
    fontFace: theme.fontDisplay,
    fontSize: 12,
    bold: true,
    color: C.primary,
    charSpacing: 1.2,
  });
  if (!Array.isArray(data.titleLines) || data.titleLines.length < 2 || data.titleLines.length > 3) {
    fail("titleLines must contain 2 or 3 items");
  }
  const lines = data.titleLines;
  if (lines.filter((line) => line.highlight).length > 1) fail("Only one title line may be highlighted");
  lines.forEach((line, index) => {
    const value = requireString(line.text, `titleLines[${index}].text`, 24);
    const y = 1.55 + index * 0.82;
    if (line.highlight) {
      slide.addShape(theme.S.rect, {
        x: 0.63,
        y: y + 0.11,
        w: Math.min(7.9, Math.max(2.2, [...value].length * 0.39)),
        h: 0.57,
        fill: { color: C.highlight },
        line: { color: C.highlight, transparency: 100 },
      });
    }
    text(slide, value, 0.68, y, 10.6, 0.72, {
      fontFace: theme.fontBody,
      fontSize: 35,
      bold: true,
      color: C.navy,
    });
  });
  text(slide, optionalString(data.subtitle, "subtitle", 80), 0.7, 4.55, 8.4, 0.65, {
    fontFace: theme.fontBody,
    fontSize: 17,
    color: C.body,
    breakLine: true,
  });
  slide.addShape(theme.S.roundRect, {
    x: 10.1,
    y: 1.2,
    w: 2.55,
    h: 4.65,
    rectRadius: 0.22,
    fill: { color: C.cardTint },
    line: { color: C.border, width: 1 },
  });
  text(slide, "AI", 10.35, 2.15, 2.05, 1.25, {
    fontFace: theme.fontDisplay,
    fontSize: 58,
    bold: true,
    color: C.primary,
    align: "center",
  });
  text(slide, "PRESIDENT", 10.35, 3.45, 2.05, 0.35, {
    fontFace: theme.fontDisplay,
    fontSize: 13,
    bold: true,
    color: C.navy,
    align: "center",
    charSpacing: 1.1,
  });
  text(slide, optionalString(data.date, "date", 18), 0.68, 6.7, 2.5, 0.25, {
    fontFace: theme.fontDisplay,
    fontSize: 11,
    color: C.muted,
  });
}

function section(slide, theme, data) {
  slide.addImage({ data: gradientSvg(), x: 0, y: 0, w: W, h: H });
  text(slide, optionalString(data.number, "number", 6), 0.72, 0.68, 1.4, 0.42, {
    fontFace: theme.fontDisplay,
    fontSize: 19,
    bold: true,
    color: C.highlight,
  });
  text(slide, requireString(data.title, "title", 28), 0.72, 2.22, 10.8, 0.86, {
    fontFace: theme.fontBody,
    fontSize: 37,
    bold: true,
    color: C.white,
  });
  text(slide, optionalString(data.subtitle, "subtitle", 50), 0.74, 3.25, 9.4, 0.72, {
    fontFace: theme.fontBody,
    fontSize: 18,
    color: C.white,
    transparency: 8,
  });
  slide.addShape(theme.S.line, {
    x: 0.72,
    y: 4.35,
    w: 1.35,
    h: 0,
    line: { color: C.highlight, width: 5 },
  });
  text(slide, "AI", 10.65, 5.72, 1.8, 0.64, {
    fontFace: theme.fontDisplay,
    fontSize: 34,
    bold: true,
    color: C.white,
    transparency: 55,
    align: "center",
  });
}

function stats(slide, theme, data) {
  addHeader(slide, theme, data);
  const metrics = requireArray(data.metrics, "metrics", 4);
  metrics.forEach((metric, i) => {
    const x = 0.68 + i * 3.02;
    box(slide, theme.S, x, 1.67, 2.78, 1.36, { fill: i === 0 ? C.primary : C.cardTint });
    text(slide, requireString(metric.value, `metrics[${i}].value`, 14), x + 0.2, 1.88, 2.38, 0.5, {
      fontFace: theme.fontDisplay,
      fontSize: 26,
      bold: true,
      color: i === 0 ? C.white : C.primary,
      align: "center",
    });
    text(slide, requireString(metric.label, `metrics[${i}].label`, 28), x + 0.2, 2.42, 2.38, 0.3, {
      fontFace: theme.fontBody,
      fontSize: 12,
      bold: true,
      color: i === 0 ? C.white : C.body,
      align: "center",
    });
  });
  const reasons = requireArray(data.reasons, "reasons", 3);
  reasons.forEach((reason, i) => {
    const y = 3.36 + i * 0.92;
    text(slide, String(i + 1).padStart(2, "0"), 0.77, y, 0.5, 0.5, {
      fontFace: theme.fontDisplay,
      fontSize: 14,
      bold: true,
      color: C.primary,
      align: "center",
    });
    text(slide, requireString(reason.title, `reasons[${i}].title`, 20), 1.48, y, 3.2, 0.46, {
      fontFace: theme.fontBody,
      fontSize: 17,
      bold: true,
      color: C.navy,
    });
    text(slide, requireString(reason.body, `reasons[${i}].body`, 48), 4.75, y, 7.65, 0.48, {
      fontFace: theme.fontBody,
      fontSize: 14,
      color: C.body,
    });
    if (i < 2) {
      slide.addShape(theme.S.line, {
        x: 0.75,
        y: y + 0.69,
        w: 11.75,
        h: 0,
        line: { color: C.border, width: 1 },
      });
    }
  });
}

function issueCards(slide, theme, data) {
  addHeader(slide, theme, data);
  const cards = requireArray(data.cards, "cards", 6);
  cards.forEach((card, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.68 + col * 4.02;
    const y = 1.65 + row * 1.75;
    box(slide, theme.S, x, y, 3.76, 1.48, { fill: row === 0 ? C.cardTint : C.white });
    text(slide, requireString(card.label, `cards[${i}].label`, 18), x + 0.2, y + 0.15, 1.2, 0.22, {
      fontFace: theme.fontDisplay,
      fontSize: 10,
      bold: true,
      color: C.primary,
    });
    text(slide, requireString(card.value, `cards[${i}].value`, 14), x + 0.2, y + 0.42, 1.05, 0.46, {
      fontFace: theme.fontDisplay,
      fontSize: 23,
      bold: true,
      color: C.navy,
    });
    text(slide, requireString(card.body, `cards[${i}].body`, 42), x + 1.38, y + 0.36, 2.05, 0.72, {
      fontFace: theme.fontBody,
      fontSize: 13,
      color: C.body,
      breakLine: true,
    });
  });
  const takeaway = requireString(data.takeaway, "takeaway", 42);
  slide.addShape(theme.S.roundRect, {
    x: 2.15,
    y: 5.42,
    w: 9.03,
    h: 0.76,
    rectRadius: 0.12,
    fill: { color: C.highlight },
    line: { color: C.highlight, transparency: 100 },
  });
  text(slide, takeaway, 2.42, 5.57, 8.5, 0.4, {
    fontFace: theme.fontBody,
    fontSize: 17,
    bold: true,
    color: C.navy,
    align: "center",
  });
}

function cards(slide, theme, data) {
  addHeader(slide, theme, data);
  const items = requireArray(data.cards, "cards", 6);
  items.forEach((card, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.68 + col * 4.03;
    const y = 1.65 + row * 2.2;
    box(slide, theme.S, x, y, 3.76, 1.92, { fill: i % 2 === 0 ? C.cardTint : C.white });
    text(slide, String(i + 1).padStart(2, "0"), x + 0.22, y + 0.17, 0.45, 0.25, {
      fontFace: theme.fontDisplay,
      fontSize: 11,
      bold: true,
      color: C.primary,
    });
    text(slide, requireString(card.title, `cards[${i}].title`, 18), x + 0.22, y + 0.51, 3.28, 0.4, {
      fontFace: theme.fontBody,
      fontSize: 17,
      bold: true,
      color: C.navy,
    });
    text(slide, requireString(card.body, `cards[${i}].body`, 58), x + 0.22, y + 1.0, 3.25, 0.62, {
      fontFace: theme.fontBody,
      fontSize: 13,
      color: C.body,
      breakLine: true,
    });
  });
}

function comparison(slide, theme, data) {
  addHeader(slide, theme, data);
  const sides = [
    { data: data.left, x: 0.68, fill: C.before, line: "D8DDE6", label: C.muted },
    { data: data.right, x: 6.85, fill: C.cardTint, line: C.primary, label: C.primary },
  ];
  sides.forEach((side, sideIndex) => {
    box(slide, theme.S, side.x, 1.7, 5.8, 3.85, {
      fill: side.fill,
      line: side.line,
      lineWidth: sideIndex ? 2 : 1,
    });
    text(slide, requireString(side.data.label, `${sideIndex ? "right" : "left"}.label`, 16), side.x + 0.28, 1.95, 1.5, 0.25, {
      fontFace: theme.fontDisplay,
      fontSize: 11,
      bold: true,
      color: side.label,
      charSpacing: 1,
    });
    text(slide, requireString(side.data.title, `${sideIndex ? "right" : "left"}.title`, 24), side.x + 0.28, 2.35, 5.15, 0.5, {
      fontFace: theme.fontBody,
      fontSize: 21,
      bold: true,
      color: C.navy,
    });
    const points = requireArray(side.data.points, `${sideIndex ? "right" : "left"}.points`, 3);
    points.forEach((point, i) => {
      slide.addShape(theme.S.ellipse, {
        x: side.x + 0.3,
        y: 3.14 + i * 0.62,
        w: 0.14,
        h: 0.14,
        fill: { color: sideIndex ? C.primary : C.muted },
        line: { color: sideIndex ? C.primary : C.muted, transparency: 100 },
      });
      text(slide, requireString(point, `points[${i}]`, 36), side.x + 0.58, 3.0 + i * 0.62, 4.8, 0.42, {
        fontFace: theme.fontBody,
        fontSize: 14,
        color: C.body,
      });
    });
  });
  slide.addShape(theme.S.chevron, {
    x: 6.3,
    y: 3.18,
    w: 0.5,
    h: 0.55,
    fill: { color: C.primary },
    line: { color: C.primary, transparency: 100 },
  });
  slide.addShape(theme.S.roundRect, {
    x: 1.8,
    y: 5.88,
    w: 9.74,
    h: 0.58,
    rectRadius: 0.12,
    fill: { color: C.primary },
    line: { color: C.primary, transparency: 100 },
  });
  text(slide, requireString(data.takeaway, "takeaway", 48), 2.05, 5.99, 9.24, 0.32, {
    fontFace: theme.fontBody,
    fontSize: 16,
    bold: true,
    color: C.white,
    align: "center",
  });
}

function caseStudy(slide, theme, data) {
  addHeader(slide, theme, data);
  const panels = [
    { item: data.context, x: 0.68, w: 4.05, fill: C.cardTint, label: "CONTEXT" },
    { item: data.episode, x: 4.98, w: 7.67, fill: C.white, label: "EPISODE" },
  ];
  panels.forEach((panel, i) => {
    box(slide, theme.S, panel.x, 1.67, panel.w, 2.78, {
      fill: panel.fill,
      line: i ? C.primary : C.border,
      lineWidth: i ? 2 : 1,
    });
    text(slide, panel.label, panel.x + 0.25, 1.92, 1.5, 0.22, {
      fontFace: theme.fontDisplay,
      fontSize: 10,
      bold: true,
      color: C.primary,
      charSpacing: 1,
    });
    text(slide, requireString(panel.item.title, `${panel.label}.title`, 24), panel.x + 0.25, 2.25, panel.w - 0.5, 0.42, {
      fontFace: theme.fontBody,
      fontSize: 19,
      bold: true,
      color: C.navy,
    });
    text(slide, requireString(panel.item.body, `${panel.label}.body`, 110), panel.x + 0.25, 2.82, panel.w - 0.5, 1.18, {
      fontFace: theme.fontBody,
      fontSize: 14,
      color: C.body,
      breakLine: true,
      valign: "top",
    });
  });
  const outcomes = requireArray(data.outcomes, "outcomes", 3);
  outcomes.forEach((outcome, i) => {
    const x = 0.68 + i * 4.03;
    box(slide, theme.S, x, 4.75, 3.76, 1.25, { fill: i === 1 ? C.primary : C.white });
    text(slide, requireString(outcome.value, `outcomes[${i}].value`, 16), x + 0.2, 4.92, 3.36, 0.42, {
      fontFace: theme.fontDisplay,
      fontSize: 23,
      bold: true,
      color: i === 1 ? C.white : C.primary,
      align: "center",
    });
    text(slide, requireString(outcome.label, `outcomes[${i}].label`, 28), x + 0.2, 5.42, 3.36, 0.28, {
      fontFace: theme.fontBody,
      fontSize: 12,
      bold: true,
      color: i === 1 ? C.white : C.body,
      align: "center",
    });
  });
}

function quotes(slide, theme, data) {
  addHeader(slide, theme, data);
  const items = requireArray(data.quotes, "quotes", 3);
  items.forEach((item, i) => {
    const x = 0.68 + i * 4.03;
    box(slide, theme.S, x, 1.7, 3.76, 3.62, { fill: i === 1 ? C.cardTint : C.white });
    text(slide, "“", x + 0.22, 1.87, 0.6, 0.55, {
      fontFace: theme.fontDisplay,
      fontSize: 34,
      bold: true,
      color: C.primary,
    });
    text(slide, requireString(item.quote, `quotes[${i}].quote`, 100), x + 0.3, 2.4, 3.16, 1.6, {
      fontFace: theme.fontBody,
      fontSize: 16,
      bold: true,
      color: C.navy,
      breakLine: true,
      valign: "top",
    });
    slide.addShape(theme.S.line, {
      x: x + 0.3,
      y: 4.25,
      w: 3.12,
      h: 0,
      line: { color: C.border, width: 1 },
    });
    text(slide, requireString(item.name, `quotes[${i}].name`, 24), x + 0.3, 4.48, 1.65, 0.26, {
      fontFace: theme.fontBody,
      fontSize: 12,
      bold: true,
      color: C.navy,
    });
    text(slide, requireString(item.role, `quotes[${i}].role`, 30), x + 1.52, 4.48, 1.9, 0.26, {
      fontFace: theme.fontBody,
      fontSize: 10,
      color: C.muted,
      align: "right",
    });
  });
  slide.addShape(theme.S.roundRect, {
    x: 2.22,
    y: 5.72,
    w: 8.9,
    h: 0.62,
    rectRadius: 0.12,
    fill: { color: C.highlight },
    line: { color: C.highlight, transparency: 100 },
  });
  text(slide, requireString(data.takeaway, "takeaway", 48), 2.5, 5.84, 8.34, 0.35, {
    fontFace: theme.fontBody,
    fontSize: 16,
    bold: true,
    color: C.navy,
    align: "center",
  });
}

function layers(slide, theme, data) {
  addHeader(slide, theme, data);
  const items = requireArray(data.layers, "layers", 5);
  const fills = ["A9CAFF", "78A9FA", "4D8AF5", C.primary, C.deep];
  items.forEach((item, i) => {
    const width = 5.15 + i * 0.7;
    const x = 0.68 + (7.95 - width) / 2;
    const y = 1.65 + i * 0.88;
    slide.addShape(theme.S.roundRect, {
      x,
      y,
      w: width,
      h: 0.68,
      rectRadius: 0.12,
      fill: { color: fills[i] },
      line: { color: fills[i], transparency: 100 },
    });
    text(slide, requireString(item.label, `layers[${i}].label`, 8), x + 0.2, y + 0.16, 0.48, 0.25, {
      fontFace: theme.fontDisplay,
      fontSize: 10,
      bold: true,
      color: i < 2 ? C.navy : C.white,
    });
    text(slide, requireString(item.title, `layers[${i}].title`, 18), x + 0.75, y + 0.11, width - 1.05, 0.35, {
      fontFace: theme.fontBody,
      fontSize: 15,
      bold: true,
      color: i < 2 ? C.navy : C.white,
      align: "center",
    });
    text(slide, requireString(item.body, `layers[${i}].body`, 40), 8.95, y + 0.03, 3.55, 0.55, {
      fontFace: theme.fontBody,
      fontSize: 13,
      color: C.body,
    });
  });
  slide.addShape(theme.S.line, {
    x: 8.78,
    y: 1.82,
    w: 0,
    h: 3.82,
    line: { color: C.border, width: 2 },
  });
}

const renderers = {
  cover,
  section,
  stats,
  "issue-cards": issueCards,
  cards,
  comparison,
  "case-study": caseStudy,
  quotes,
  layers,
};

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log(
      "Usage: generate-tha-deck.cjs [--input deck.json] [--output deck.pptx]",
    );
    return;
  }

  const inputPath = args.input
    ? path.resolve(process.cwd(), args.input)
    : path.resolve(__dirname, "../examples/sample-deck.json");
  const outputPath = args.output
    ? path.resolve(process.cwd(), args.output)
    : path.resolve(process.cwd(), "tha-ai-president-sample.pptx");
  const config = readJson(inputPath);
  if (!Array.isArray(config.slides) || config.slides.length === 0) {
    fail("slides must be a non-empty array");
  }

  const PptxGenJS = loadPptxGenJS();
  const sourcesById = validateSources(config.sources);
  const pptx = new PptxGenJS();
  pptx.layout = "LAYOUT_WIDE";
  pptx.author = config.meta?.author || "";
  pptx.company = config.meta?.company || "";
  pptx.subject = config.meta?.subject || "";
  pptx.title = config.meta?.title || "THA AI President deck";
  pptx.lang = config.meta?.language || "ja-JP";
  pptx.theme = {
    headFontFace: config.theme?.fontBody || "BIZ UDGothic",
    bodyFontFace: config.theme?.fontBody || "BIZ UDGothic",
    lang: config.meta?.language || "ja-JP",
  };

  const theme = {
    fontBody: config.theme?.fontBody || "BIZ UDGothic",
    fontDisplay: config.theme?.fontDisplay || "Arial",
    S: pptx.ShapeType,
  };

  config.slides.forEach((data, index) => {
    const renderer = renderers[data.type];
    if (!renderer) fail(`slides[${index}].type is unknown: ${data.type}`);
    const slide = pptx.addSlide();
    renderer(slide, theme, data);
    if (!["cover", "section"].includes(data.type)) {
      addFooter(slide, theme, config.meta || {}, index + 1);
    }
    addNotes(slide, data, sourcesById);
  });

  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  await pptx.writeFile({ fileName: outputPath });
  console.log(`Created ${outputPath}`);
  console.log(`Slides: ${config.slides.length}`);
}

main().catch((error) => fail(error.stack || error.message));
