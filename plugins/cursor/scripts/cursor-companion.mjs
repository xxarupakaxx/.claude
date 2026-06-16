#!/usr/bin/env node
// cursor-companion — a thin, dependency-free runtime that lets Claude Code
// delegate coding/diagnosis tasks to the Cursor Agent CLI (`cursor-agent`),
// in the same spirit as the OpenAI Codex companion plugin.
//
// Subcommands:
//   task        Run a Cursor agent turn (foreground or --background), optionally resuming.
//   task-worker (internal) Detached worker that executes a queued background task.
//   status      Show one job, or list recent jobs for this workspace.
//   result      Print the full result text of a finished job.
//   cancel      Cancel a running/queued job.
//   doctor      Check that cursor-agent is installed and authenticated.
//
// State lives under ~/.cursor-companion (override with CURSOR_COMPANION_HOME).

import { spawn, spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const SCRIPT_PATH = fileURLToPath(import.meta.url);
const HOME = process.env.CURSOR_COMPANION_HOME || path.join(os.homedir(), ".cursor-companion");
const JOBS_DIR = path.join(HOME, "jobs");
const LOGS_DIR = path.join(HOME, "logs");
const DEFAULT_MODEL = process.env.CURSOR_COMPANION_MODEL || "gpt-5.5-high";
const CURSOR_BIN = process.env.CURSOR_AGENT_BIN || "cursor-agent";
const PROGRESS_LIMIT = 160;

const MODEL_ALIASES = new Map([
  ["gpt5.5", "gpt-5.5-high"],
  ["gpt-5.5", "gpt-5.5-high"],
  ["gpt55", "gpt-5.5-high"],
  ["opus", "claude-opus-4-8-thinking-high"],
  ["opus-4.8", "claude-opus-4-8-thinking-high"],
  ["claude-opus", "claude-opus-4-8-thinking-high"],
  ["fable", "claude-fable-5-thinking-high"],
  ["sonnet", "claude-4.6-sonnet-medium-thinking"],
  ["auto", "auto"]
]);

// ---------------------------------------------------------------------------
// small helpers
// ---------------------------------------------------------------------------

function ensureDirs() {
  fs.mkdirSync(JOBS_DIR, { recursive: true });
  fs.mkdirSync(LOGS_DIR, { recursive: true });
}

function nowIso() {
  return new Date().toISOString();
}

function generateJobId() {
  const stamp = new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14);
  const rand = Math.floor(Math.random() * 1e6).toString(36);
  return `cur_${stamp}_${rand}`;
}

function jobFile(id) {
  return path.join(JOBS_DIR, `${id}.json`);
}

function logFile(id) {
  return path.join(LOGS_DIR, `${id}.log`);
}

function readJob(id) {
  try {
    return JSON.parse(fs.readFileSync(jobFile(id), "utf8"));
  } catch {
    return null;
  }
}

function writeJob(record) {
  ensureDirs();
  fs.writeFileSync(jobFile(record.id), JSON.stringify(record, null, 2));
  return record;
}

function patchJob(id, patch) {
  const current = readJob(id) ?? { id };
  const next = { ...current, ...patch, updatedAt: nowIso() };
  return writeJob(next);
}

function listJobs() {
  ensureDirs();
  return fs
    .readdirSync(JOBS_DIR)
    .filter((name) => name.endsWith(".json"))
    .map((name) => readJob(name.slice(0, -5)))
    .filter(Boolean)
    .sort((a, b) => String(b.createdAt ?? "").localeCompare(String(a.createdAt ?? "")));
}

function appendLog(id, line) {
  try {
    ensureDirs();
    fs.appendFileSync(logFile(id), `${nowIso()} ${line}\n`);
  } catch {
    /* logging must never throw */
  }
}

function shorten(text, limit = 96) {
  const normalized = String(text ?? "").replace(/\s+/g, " ").trim();
  if (normalized.length <= limit) return normalized;
  return `${normalized.slice(0, limit - 1)}…`;
}

function firstLine(text, fallback = "") {
  const line = String(text ?? "")
    .split(/\r?\n/)
    .map((l) => l.trim())
    .find(Boolean);
  return line ?? fallback;
}

function normalizeModel(model) {
  if (!model) return DEFAULT_MODEL;
  const key = String(model).trim().toLowerCase();
  return MODEL_ALIASES.get(key) ?? String(model).trim();
}

function isActive(status) {
  return status === "queued" || status === "running";
}

function killTree(pid) {
  if (!pid || Number.isNaN(pid)) return;
  for (const target of [-pid, pid]) {
    try {
      process.kill(target, "SIGTERM");
    } catch {
      /* already gone */
    }
  }
}

// ---------------------------------------------------------------------------
// arg parsing
// ---------------------------------------------------------------------------

function parseArgs(argv, { booleans = [], values = [] } = {}) {
  const options = {};
  const positionals = [];
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--") {
      positionals.push(...argv.slice(i + 1));
      break;
    }
    if (arg.startsWith("--")) {
      const eq = arg.indexOf("=");
      const key = (eq === -1 ? arg.slice(2) : arg.slice(2, eq));
      if (booleans.includes(key)) {
        options[key] = true;
      } else if (values.includes(key)) {
        options[key] = eq === -1 ? argv[++i] : arg.slice(eq + 1);
      } else {
        // unknown flag: treat valueless as boolean to be forgiving
        options[key] = eq === -1 ? true : arg.slice(eq + 1);
      }
    } else {
      positionals.push(arg);
    }
  }
  return { options, positionals };
}

// ---------------------------------------------------------------------------
// cursor-agent invocation
// ---------------------------------------------------------------------------

function cursorAvailable() {
  const probe = spawnSync(CURSOR_BIN, ["--version"], { encoding: "utf8" });
  return { available: probe.status === 0, version: (probe.stdout || "").trim() };
}

function cursorLoggedIn() {
  const probe = spawnSync(CURSOR_BIN, ["status"], { encoding: "utf8" });
  const out = `${probe.stdout || ""}${probe.stderr || ""}`;
  return { loggedIn: /Logged in|Login successful/i.test(out), raw: out.trim() };
}

// Runs cursor-agent with stream-json, surfacing progress and capturing the
// final result + session id. Returns a promise of a normalized outcome.
function runCursorTurn({ prompt, model, resumeSessionId, write, cwd, onProgress }) {
  const args = [];
  if (resumeSessionId) args.push("--resume", resumeSessionId);
  args.push("-p", prompt);
  args.push("--output-format", "stream-json");
  // --force grants directory trust + command execution; required for any
  // non-interactive run. Write-capability is the default per project policy.
  args.push("--force");
  if (model) args.push("--model", model);

  return new Promise((resolve) => {
    const child = spawn(CURSOR_BIN, args, {
      cwd,
      env: process.env,
      stdio: ["ignore", "pipe", "pipe"]
    });

    const outcome = {
      pid: child.pid ?? null,
      sessionId: null,
      resolvedModel: null,
      result: "",
      isError: false,
      durationMs: null,
      usage: null,
      stderr: "",
      exitStatus: null,
      assistantTexts: []
    };

    let stdoutBuf = "";

    const handleEvent = (evt) => {
      if (!evt || typeof evt !== "object") return;
      switch (evt.type) {
        case "system":
          if (evt.session_id) outcome.sessionId = evt.session_id;
          if (evt.model) {
            outcome.resolvedModel = evt.model;
            onProgress?.(`▸ model ${evt.model}`);
          }
          break;
        case "assistant": {
          const content = evt.message?.content ?? [];
          for (const part of content) {
            if (part?.type === "text" && part.text?.trim()) {
              outcome.assistantTexts.push(part.text);
              onProgress?.(`💬 ${shorten(part.text, PROGRESS_LIMIT)}`);
            } else if (part?.type && part.type !== "text") {
              const label = part.name || part.tool || part.type;
              onProgress?.(`🔧 ${shorten(label, PROGRESS_LIMIT)}`);
            }
          }
          break;
        }
        case "result":
          if (typeof evt.result === "string") outcome.result = evt.result;
          if (evt.session_id) outcome.sessionId = evt.session_id;
          outcome.isError = Boolean(evt.is_error);
          outcome.durationMs = evt.duration_ms ?? null;
          outcome.usage = evt.usage ?? null;
          break;
        default:
          break;
      }
    };

    const drain = (flush = false) => {
      let idx;
      while ((idx = stdoutBuf.indexOf("\n")) !== -1) {
        const line = stdoutBuf.slice(0, idx).trim();
        stdoutBuf = stdoutBuf.slice(idx + 1);
        if (line) {
          try {
            handleEvent(JSON.parse(line));
          } catch {
            /* ignore non-JSON noise */
          }
        }
      }
      if (flush && stdoutBuf.trim()) {
        try {
          handleEvent(JSON.parse(stdoutBuf.trim()));
        } catch {
          /* ignore */
        }
        stdoutBuf = "";
      }
    };

    child.stdout.on("data", (chunk) => {
      stdoutBuf += chunk.toString();
      drain(false);
    });
    child.stderr.on("data", (chunk) => {
      outcome.stderr += chunk.toString();
    });
    child.on("error", (err) => {
      outcome.stderr += `\n${err.message}`;
      outcome.exitStatus = 127;
      resolve(outcome);
    });
    child.on("close", (code) => {
      drain(true);
      outcome.exitStatus = code ?? 0;
      // If cursor-agent had no explicit final result text, fall back to the
      // last assistant message so the caller always gets something usable.
      if (!outcome.result && outcome.assistantTexts.length) {
        outcome.result = outcome.assistantTexts[outcome.assistantTexts.length - 1];
      }
      resolve(outcome);
    });
  });
}

// ---------------------------------------------------------------------------
// rendering
// ---------------------------------------------------------------------------

function fmtDuration(ms) {
  if (ms == null) return "?";
  return `${(ms / 1000).toFixed(1)}s`;
}

function renderTaskResult(job, outcome) {
  const lines = [];
  const title = job.title || "Cursor Task";
  const model = outcome.resolvedModel || job.model || "?";
  const status = outcome.isError || outcome.exitStatus !== 0 ? "FAILED" : "OK";
  lines.push(`## 🅒 Cursor · ${title} · ${status}`);
  lines.push("");
  const body = (outcome.result || "").trim();
  lines.push(body || outcome.stderr.trim() || "(no output)");
  lines.push("");
  lines.push("---");
  const meta = [
    `model: ${model}`,
    `session: ${outcome.sessionId ?? "?"}`,
    `time: ${fmtDuration(outcome.durationMs)}`
  ];
  if (outcome.usage) {
    meta.push(`tokens: ${outcome.usage.inputTokens ?? "?"}→${outcome.usage.outputTokens ?? "?"}`);
  }
  lines.push(meta.join(" · "));
  lines.push(`resume: \`cursor-companion task --resume-last "<follow-up>"\``);
  return `${lines.join("\n")}\n`;
}

function renderJobLine(job) {
  const icon =
    job.status === "succeeded" ? "✓" :
    job.status === "failed" ? "✗" :
    job.status === "cancelled" ? "⊘" :
    job.status === "running" ? "▶" : "·";
  return `${icon} ${job.id}  [${job.status}]  ${job.model ?? "?"}  ${shorten(job.summary ?? job.title ?? "", 60)}`;
}

function renderJobDetail(job) {
  const lines = [];
  lines.push(`Job ${job.id} — ${job.status}`);
  lines.push(`  title:     ${job.title ?? "?"}`);
  lines.push(`  model:     ${job.model ?? "?"}`);
  lines.push(`  workspace: ${job.workspaceRoot ?? "?"}`);
  lines.push(`  created:   ${job.createdAt ?? "?"}`);
  if (job.completedAt) lines.push(`  completed: ${job.completedAt}`);
  if (job.sessionId) lines.push(`  session:   ${job.sessionId}`);
  if (job.error) lines.push(`  error:     ${job.error}`);
  if (isActive(job.status)) {
    lines.push(`  → still running. Re-check with: cursor-companion status ${job.id}`);
  } else if (job.status === "succeeded") {
    lines.push(`  → see result: cursor-companion result ${job.id}`);
  }
  return `${lines.join("\n")}\n`;
}

function output(value, rendered, asJson) {
  if (asJson) {
    process.stdout.write(`${JSON.stringify(value, null, 2)}\n`);
  } else {
    process.stdout.write(rendered);
  }
}

// ---------------------------------------------------------------------------
// resume resolution
// ---------------------------------------------------------------------------

function resolveResumeSession(workspaceRoot, excludeJobId) {
  const active = listJobs().find(
    (job) => job.workspaceRoot === workspaceRoot && job.jobClass === "task" && isActive(job.status) && job.id !== excludeJobId
  );
  if (active) {
    throw new Error(`Task ${active.id} is still running for this workspace. Wait for it (cursor-companion status ${active.id}) before resuming.`);
  }
  const latest = listJobs().find(
    (job) =>
      job.workspaceRoot === workspaceRoot &&
      job.jobClass === "task" &&
      job.sessionId &&
      job.id !== excludeJobId
  );
  if (!latest) {
    throw new Error("No previous Cursor task with a session id was found for this workspace.");
  }
  return latest.sessionId;
}

// ---------------------------------------------------------------------------
// task execution (shared by foreground + worker)
// ---------------------------------------------------------------------------

async function executeTask(job, { stderrProgress }) {
  patchJob(job.id, { status: "running", pid: process.pid, startedAt: nowIso() });
  const onProgress = (line) => {
    appendLog(job.id, line);
    if (stderrProgress) process.stderr.write(`  ${line}\n`);
  };
  appendLog(job.id, `Running cursor-agent (model=${job.model}, resume=${job.resumeSessionId ?? "none"})`);

  const outcome = await runCursorTurn({
    prompt: job.prompt,
    model: job.model,
    resumeSessionId: job.resumeSessionId,
    write: job.write,
    cwd: job.workspaceRoot,
    onProgress
  });

  const failed = outcome.isError || outcome.exitStatus !== 0;
  patchJob(job.id, {
    status: failed ? "failed" : "succeeded",
    pid: null,
    completedAt: nowIso(),
    sessionId: outcome.sessionId ?? job.sessionId ?? null,
    resolvedModel: outcome.resolvedModel ?? null,
    result: outcome.result ?? "",
    error: failed ? firstLine(outcome.stderr, "cursor-agent reported an error") : null,
    durationMs: outcome.durationMs ?? null,
    usage: outcome.usage ?? null,
    exitStatus: outcome.exitStatus
  });
  appendLog(job.id, `Done: ${failed ? "FAILED" : "OK"} (exit ${outcome.exitStatus})`);

  return { outcome, failed, job: readJob(job.id) };
}

// ---------------------------------------------------------------------------
// commands
// ---------------------------------------------------------------------------

function readPrompt(options, positionals) {
  if (options["prompt-file"]) {
    return fs.readFileSync(path.resolve(process.cwd(), options["prompt-file"]), "utf8").trim();
  }
  const joined = positionals.join(" ").trim();
  if (joined) return joined;
  // piped stdin
  if (!process.stdin.isTTY) {
    try {
      return fs.readFileSync(0, "utf8").trim();
    } catch {
      return "";
    }
  }
  return "";
}

async function handleTask(argv) {
  const { options, positionals } = parseArgs(argv, {
    booleans: ["background", "json", "read-only", "resume-last", "resume", "fresh"],
    values: ["model", "cwd", "prompt-file"]
  });

  const workspaceRoot = options.cwd ? path.resolve(process.cwd(), options.cwd) : process.cwd();
  const model = normalizeModel(options.model);
  const resumeLast = Boolean(options["resume-last"] || options.resume);
  if (resumeLast && options.fresh) {
    throw new Error("Choose either --resume/--resume-last or --fresh, not both.");
  }
  const write = !options["read-only"];
  let prompt = readPrompt(options, positionals);
  if (options["read-only"] && prompt) {
    prompt = `[READ-ONLY MODE: investigate and report only. Do NOT modify files or run mutating commands.]\n\n${prompt}`;
  }
  if (!prompt && !resumeLast) {
    throw new Error("Provide a prompt (positional, --prompt-file, or piped stdin), or use --resume-last.");
  }

  const id = generateJobId();
  let resumeSessionId = null;
  if (resumeLast) {
    resumeSessionId = resolveResumeSession(workspaceRoot, id);
    if (!prompt) prompt = "Continue the previous task.";
  }

  const job = writeJob({
    id,
    jobClass: "task",
    status: "queued",
    title: resumeLast ? "Cursor Resume" : "Cursor Task",
    summary: shorten(prompt),
    prompt,
    model,
    write,
    resumeSessionId,
    workspaceRoot,
    createdAt: nowIso(),
    pid: null
  });

  if (options.background) {
    const child = spawn(process.execPath, [SCRIPT_PATH, "task-worker", "--job-id", id], {
      cwd: workspaceRoot,
      env: process.env,
      detached: true,
      stdio: "ignore"
    });
    child.unref();
    patchJob(id, { pid: child.pid ?? null });
    appendLog(id, "Queued for background execution.");
    const payload = { jobId: id, status: "queued", title: job.title, model };
    output(
      payload,
      `🅒 Cursor task started in background as ${id} (model ${model}).\n` +
        `   Progress: cursor-companion status ${id}\n` +
        `   Result:   cursor-companion result ${id}\n`,
      options.json
    );
    return;
  }

  const { outcome, failed, job: finalJob } = await executeTask(job, { stderrProgress: !options.json });
  output(finalJob, renderTaskResult(finalJob, outcome), options.json);
  if (failed) process.exitCode = 1;
}

async function handleTaskWorker(argv) {
  const { options } = parseArgs(argv, { values: ["job-id"] });
  if (!options["job-id"]) throw new Error("task-worker requires --job-id.");
  const job = readJob(options["job-id"]);
  if (!job) throw new Error(`No stored job for ${options["job-id"]}.`);
  await executeTask(job, { stderrProgress: false });
}

function resolveJobReference(reference, { activeOnly = false } = {}) {
  if (reference) {
    const job = readJob(reference);
    if (!job) throw new Error(`No job found for ${reference}.`);
    return job;
  }
  const workspaceRoot = process.cwd();
  const candidates = listJobs().filter((job) => job.workspaceRoot === workspaceRoot);
  const job = activeOnly
    ? candidates.find((j) => isActive(j.status))
    : candidates[0];
  if (!job) throw new Error("No matching job found for this workspace.");
  return job;
}

function handleStatus(argv) {
  const { options, positionals } = parseArgs(argv, {
    booleans: ["json", "all"],
    values: ["cwd"]
  });
  const reference = positionals[0];
  if (reference) {
    const job = readJob(reference);
    if (!job) throw new Error(`No job found for ${reference}.`);
    output(job, renderJobDetail(job), options.json);
    return;
  }
  const workspaceRoot = options.cwd ? path.resolve(process.cwd(), options.cwd) : process.cwd();
  let jobs = listJobs();
  if (!options.all) jobs = jobs.filter((job) => job.workspaceRoot === workspaceRoot);
  jobs = jobs.slice(0, 15);
  const rendered = jobs.length
    ? `${jobs.map(renderJobLine).join("\n")}\n`
    : "No Cursor jobs recorded for this workspace.\n";
  output({ jobs }, rendered, options.json);
}

function handleResult(argv) {
  const { options, positionals } = parseArgs(argv, { booleans: ["json"] });
  const job = resolveJobReference(positionals[0]);
  if (isActive(job.status)) {
    output(job, `Job ${job.id} is still ${job.status}. Check: cursor-companion status ${job.id}\n`, options.json);
    return;
  }
  const rendered =
    `## 🅒 Cursor · ${job.title ?? "Task"} · ${job.status === "succeeded" ? "OK" : job.status.toUpperCase()}\n\n` +
    `${(job.result || job.error || "(no output)").trim()}\n\n---\n` +
    `model: ${job.resolvedModel ?? job.model ?? "?"} · session: ${job.sessionId ?? "?"} · ${fmtDuration(job.durationMs)}\n`;
  output(job, rendered, options.json);
}

async function handleCancel(argv) {
  const { options, positionals } = parseArgs(argv, { booleans: ["json"] });
  const job = resolveJobReference(positionals[0], { activeOnly: !positionals[0] });
  killTree(job.pid);
  const cancelled = patchJob(job.id, {
    status: "cancelled",
    pid: null,
    completedAt: nowIso(),
    error: "Cancelled by user."
  });
  appendLog(job.id, "Cancelled by user.");
  output(cancelled, `⊘ Cancelled ${job.id}.\n`, options.json);
}

function handleDoctor(argv) {
  const { options } = parseArgs(argv, { booleans: ["json"] });
  const avail = cursorAvailable();
  const auth = avail.available ? cursorLoggedIn() : { loggedIn: false, raw: "cursor-agent not found" };
  const report = {
    cursorAgent: avail,
    auth,
    defaultModel: DEFAULT_MODEL,
    stateHome: HOME,
    ready: avail.available && auth.loggedIn
  };
  const rendered =
    `cursor-agent: ${avail.available ? `✓ ${avail.version}` : "✗ not found"}\n` +
    `auth:         ${auth.loggedIn ? "✓ logged in" : "✗ not logged in (run `cursor-agent login`)"}\n` +
    `default model:${" "}${DEFAULT_MODEL}\n` +
    `state:        ${HOME}\n` +
    `ready:        ${report.ready ? "yes" : "no"}\n`;
  output(report, rendered, options.json);
}

function printUsage() {
  process.stdout.write(
    [
      "cursor-companion — delegate tasks to the Cursor Agent CLI",
      "",
      "Usage:",
      "  cursor-companion task [--background] [--read-only] [--resume-last|--fresh]",
      "                        [--model <opus|gpt-5.5|...>] [--cwd <dir>] [--json] <prompt>",
      "  cursor-companion status [job-id] [--all] [--json]",
      "  cursor-companion result [job-id] [--json]",
      "  cursor-companion cancel [job-id] [--json]",
      "  cursor-companion doctor [--json]",
      ""
    ].join("\n")
  );
}

async function main() {
  const [subcommand, ...argv] = process.argv.slice(2);
  switch (subcommand) {
    case undefined:
    case "help":
    case "--help":
    case "-h":
      printUsage();
      break;
    case "task":
      await handleTask(argv);
      break;
    case "task-worker":
      await handleTaskWorker(argv);
      break;
    case "status":
      handleStatus(argv);
      break;
    case "result":
      handleResult(argv);
      break;
    case "cancel":
      await handleCancel(argv);
      break;
    case "doctor":
      handleDoctor(argv);
      break;
    default:
      throw new Error(`Unknown subcommand: ${subcommand}. Run with --help.`);
  }
}

main().catch((error) => {
  process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
  process.exitCode = 1;
});
