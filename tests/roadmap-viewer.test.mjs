import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const html = readFileSync(new URL('../tools/roadmap_viewer.html', import.meta.url), 'utf8');
const sourceMatch = html.match(/\/\* ROADMAP_MODEL_START \*\/([\s\S]*?)\/\* ROADMAP_MODEL_END \*\//);

assert.ok(sourceMatch, 'roadmap_viewer.html must expose the exact browser model source between markers');

const context = vm.createContext({
  console,
  Date,
  Intl,
  JSON,
  Math,
  Map,
  Object,
  RegExp,
  Set,
  String,
  globalThis: {}
});
vm.runInContext(sourceMatch[1], context, { filename: 'roadmap-viewer-model.js' });
const model = context.globalThis.__ROADMAP_MODEL__;

assert.ok(model, 'model API must be exported for the browser and tests');

const plan = `# Roadmap Viewer UX

## Task 0：視覚方向を選ぶ

**変更対象:** design/option-3.png

- [x] 案3を選択

## Task 1.5: Markdown正規化

**blockedBy:** Task 0
**備考:** 表記揺れを同じ意味へまとめる

- [x] 見出しを読む
- [ ] 進捗表を読む

### タスク 2：計画キャンバスを実装

- [ ] 初期画面
- [ ] レスポンシブ

## リスクと懸念

| リスク | 影響度 | 対策 |
| --- | --- | --- |
| 古い更新を稼働中と誤認する | 高 | staleなら待ちにする |

## 比較表

| 候補 | 長所 | 短所 |
| --- | --- | --- |
| 案3 | 計画が見える | 情報量が多い |
`;

const progress = `# 進捗

- [x] Task 0 視覚方向を選ぶ
- [ ] タスク 1.5 Markdown正規化

| タスク | 状態 | 進捗 |
| --- | --- | --- |
| Task 1.5 | 進行中 | 1/2 |
| タスク 2 | 未着手 | 0/2 |
`;

const reviews = `# Review

Severity: CRITICAL 0
IMPORTANT：2件

| Severity | Count |
| --- | ---: |
| MINOR | 1 |
`;

const files = {
  '30_plan.md': plan,
  '40_progress.md': progress,
  '80_review.md': reviews,
  '05_log.md': '## Phase 2: 計画完了\n\n案3を選択した。'
};

const generatedAt = '2026-07-12T02:59:30.000Z';
const nowMs = Date.parse('2026-07-12T03:00:00.000Z');

test('groups tasks into running, waiting and recent completed sections', () => {
  const grouped = model.groupTaskSections([
    { id: '1', section: 'running' },
    { id: '2', section: 'waiting' },
    { id: '3', section: 'recent_completed' },
    { id: '4', section: 'unsupported' }
  ]);

  assert.deepEqual(Array.from(grouped.running, task => task.id), ['1']);
  assert.deepEqual(Array.from(grouped.waiting, task => task.id), ['2']);
  assert.deepEqual(Array.from(grouped.recent_completed, task => task.id), ['3']);
});

test('separates design and implementation plans and normalizes approval', () => {
  const result = model.extractPlanSections({
    files: {
      '00_spec.md': '# Design plan',
      '30_plan.md': '# Implementation plan'
    },
    metadata: { approvalState: 'approved' }
  });

  assert.equal(result.designPlan, '# Design plan');
  assert.equal(result.implementationPlan, '# Implementation plan');
  assert.equal(result.approval, 'approved');
});

test('does not treat candidate memory matches as confirmed plans', () => {
  const result = model.extractPlanSections({
    matchState: 'candidate',
    matchCandidates: [{ detail: { files: { '00_spec.md': '# Candidate design' } } }],
    detail: { files: { '30_plan.md': '# Confirmed implementation' } }
  });

  assert.equal(result.designPlan, '');
  assert.equal(result.implementationPlan, '# Confirmed implementation');
  assert.equal(result.approval, 'unknown');
});

test('clamps task hub settings and defaults invalid stored values', () => {
  assert.deepEqual(
    JSON.parse(JSON.stringify(model.taskHubSettings({ staleMinutes: 'oops', recentCompletedHours: 0, recentCompletedCollapsed: false }))),
    { staleMinutes: 15, recentCompletedHours: 24, recentCompletedCollapsed: false }
  );
  assert.equal(model.taskHubSettings({ staleMinutes: 9999, recentCompletedHours: 48 }).staleMinutes, 1440);
});

test('normalizes heading, colon, decimal task, Japanese checklist and progress table variants', () => {
  const normalized = model.normalizeSnapshot({
    version: 1,
    title: 'Roadmap Viewer UX',
    taskDir: '/tmp/task',
    generatedAt,
    files
  });
  const result = model.buildModel(normalized, { nowMs });

  assert.deepEqual(Array.from(result.tasks, task => task.number), ['0', '1.5', '2']);
  assert.equal(result.tasks[0].status, 'complete');
  assert.equal(result.tasks[1].status, 'in-progress');
  assert.equal(result.tasks[1].blockedBy, 'Task 0');
  assert.equal(result.tasks[1].done, 1);
  assert.equal(result.tasks[1].total, 2);
  assert.equal(result.tasks[2].status, 'planned');
  assert.equal(result.activeTask.number, '1.5');
  assert.deepEqual(Array.from(result.nextSteps, task => task.number), ['1.5', '2']);
});

test('normalizes review spelling variants and limits risks to risk sections', () => {
  const result = model.buildModel(model.normalizeSnapshot({ generatedAt, files }), { nowMs });

  assert.deepEqual(
    { critical: result.reviews.critical, important: result.reviews.important, minor: result.reviews.minor },
    { critical: 0, important: 2, minor: 1 }
  );
  assert.equal(result.reviews.hasReview, true);
  assert.deepEqual(Array.from(result.risks, risk => risk.title), ['古い更新を稼働中と誤認する']);
});

test('legacy, manual JSON and generated v1 snapshots share one semantic model', () => {
  const legacy = model.buildModel(model.normalizeSnapshot({ files, generated_at: generatedAt }), { nowMs });
  const manual = model.buildModel(model.normalizeSnapshot({ title: 'Manual', generatedAt, files }), { nowMs });
  const generated = model.buildModel(model.normalizeSnapshot({
    version: 1,
    title: 'Generated',
    taskDir: '/tmp/task',
    generatedAt,
    fingerprint: 'abc',
    files,
    artifacts: [
      { name: '30_plan.md', path: '30_plan.md', type: '.md', size: 2048, modifiedAt: generatedAt }
    ]
  }), { nowMs });

  const semantic = value => ({
    tasks: Array.from(value.tasks, task => [task.number, task.status, task.done, task.total]),
    reviews: [value.reviews.critical, value.reviews.important, value.reviews.minor],
    risks: Array.from(value.risks, risk => risk.title),
    phases: Array.from(value.phases, phase => [phase.number, phase.status])
  });

  assert.deepEqual(semantic(legacy), semantic(manual));
  assert.deepEqual(semantic(manual), semantic(generated));
  assert.equal(generated.artifacts[0].path, '30_plan.md');
  assert.ok(legacy.artifacts.some(artifact => artifact.path === '30_plan.md'));
  assert.ok(manual.artifacts.some(artifact => artifact.path === '40_progress.md'));
});

test('reads progress status only from the status cell and stops task bodies at the next peer section', () => {
  const scopedFiles = {
    '30_plan.md': `# Scoped parser

## Task 5: 完了報告を作る

- [ ] レポートを書く

## リスク

- [x] 受容済み
`,
    '40_progress.md': `| タスク | 状態 | 進捗 |
|---|---|---|
| Task 5 完了報告を作る | 未着手 | 0/1 |
`
  };
  const result = model.buildModel(model.normalizeSnapshot({ generatedAt, files: scopedFiles }), { nowMs });

  assert.equal(result.tasks[0].status, 'planned');
  assert.equal(result.tasks[0].done, 0);
  assert.equal(result.tasks[0].total, 1);
  assert.deepEqual(Array.from(result.tasks[0].steps, step => step.label), ['レポートを書く']);
});

test('scopes phase signals to status sources and keeps Phase 5 distinct from Phase 5.5', () => {
  const phaseFiles = {
    '30_plan.md': '# Plan\n\nPhase 5 完了という例示',
    '40_progress.md': '# 進捗\n\n- 現在地: Phase 3 実装中',
    '05_log.md': '## Phase 2: 計画完了\n\n- Phase 5完了という誤判定を修正する',
    '20_survey_external.md': 'Phase 0からPhase 5.5まで完了と書かれた外部比較'
  };
  const result = model.buildModel(model.normalizeSnapshot({ generatedAt, files: phaseFiles }), { nowMs });
  const states = Object.fromEntries(Array.from(result.phases, phase => [phase.number, phase.status]));

  assert.equal(states['3'], 'in-progress');
  assert.equal(states['5'], 'planned');
});

test('maps workflow subphases 2.5 and 5.5 onto the six-phase rail without losing the source number', () => {
  for (const [workflowNumber, displayNumber] of [['2.5', '2'], ['5.5', '5']]) {
    const result = model.buildModel(model.normalizeSnapshot({
      generatedAt,
      files: { '40_progress.md': `- 現在地: Phase ${workflowNumber} 進行中` }
    }), { nowMs });
    const active = result.phases.find(phase => phase.status === 'in-progress');

    assert.equal(active.number, displayNumber);
    assert.equal(active.workflowNumber, workflowNumber);
  }
});

test('does not turn review headings about completion criteria into phase completion', () => {
  const result = model.buildModel(model.normalizeSnapshot({
    generatedAt,
    files: {
      '40_progress.md': '- 現在地: Phase 3 実装中',
      '80_review.md': '## Phase 5 完了条件のレビュー\n\nまだPhase 3です'
    }
  }), { nowMs });
  const states = Object.fromEntries(Array.from(result.phases, phase => [phase.number, phase.status]));

  assert.equal(states['3'], 'in-progress');
  assert.equal(states['5'], 'planned');
});

test('later completion events supersede historical phase start events', () => {
  const result = model.buildModel(model.normalizeSnapshot({
    generatedAt,
    files: {
      '05_log.md': [
        '## Phase 0 準備開始',
        '## Phase 0 完了、Phase 1 調査開始',
        '## Phase 1 完了、Phase 2 計画開始',
        '## Phase 2 完了',
        '## Phase 3 実装開始',
        '## Phase 5 完了'
      ].join('\n\n')
    }
  }), { nowMs });

  assert.deepEqual(Array.from(result.phases, phase => phase.status), Array(6).fill('complete'));
});

test('stops parent task bodies before nested task headings', () => {
  const nested = model.buildModel(model.normalizeSnapshot({
    generatedAt,
    files: {
      '30_plan.md': '## Task 1: 親\n\n- [ ] 親作業\n\n### Task 1.1: 子\n\n- [x] 子作業'
    }
  }), { nowMs });

  assert.deepEqual(Array.from(nested.tasks, task => [task.number, task.done, task.total]), [['1', 0, 1], ['1.1', 1, 1]]);
});

test('stale snapshots stop presenting recorded work as actively running', () => {
  const staleNow = Date.parse('2026-07-12T04:00:00.000Z');
  const result = model.buildModel(model.normalizeSnapshot({ generatedAt, files }), { nowMs: staleNow });

  assert.equal(result.freshness.state, 'stale');
  assert.equal(result.activeTask, null);
  assert.equal(result.recordedActiveTask.number, '1.5');
  assert.match(result.waiting.reason, /更新/);
});

test('unknown snapshot freshness does not claim recorded work is active', () => {
  const result = model.buildModel(model.normalizeSnapshot({ files }), { nowMs });

  assert.equal(result.freshness.state, 'unknown');
  assert.equal(result.activeTask, null);
  assert.equal(result.recordedActiveTask.number, '1.5');
});

test('artifact completion labels require phase evidence instead of file existence', () => {
  const planned = model.buildModel(model.normalizeSnapshot({
    generatedAt,
    files: {
      '30_plan.md': '# Plan',
      '20_survey_external.md': '# Survey'
    }
  }), { nowMs });
  const completed = model.buildModel(model.normalizeSnapshot({
    generatedAt,
    files: {
      '30_plan.md': '# Plan',
      '20_survey_external.md': '# Survey',
      '05_log.md': '## Phase 1: 調査完了\n\n## Phase 2: 計画完了'
    }
  }), { nowMs });
  const planArtifact = { path: '30_plan.md' };
  const surveyArtifact = { path: '20_survey_external.md' };

  assert.equal(model.artifactStateFor(planArtifact, planned), '計画');
  assert.equal(model.artifactStateFor(surveyArtifact, planned), '調査記録');
  assert.equal(model.artifactStateFor(planArtifact, completed), '計画確定');
  assert.equal(model.artifactStateFor(surveyArtifact, completed), '調査済み');
});

test('renders workflow markdown safely without an external parser', () => {
  const rendered = model.renderWorkflowMarkdown(`# 見出し

- [x] **完了**した作業
- [ ] 未完了の作業

| 項目 | 状態 |
| --- | --- |
| Parser | ready |

> 補足

\`inline\` and [OpenAI](https://openai.com)

\`\`\`html
<script>alert('xss')</script>
\`\`\`

<img src=x onerror=alert(1)>
[危険](javascript:alert(1))`);

  assert.match(rendered, /<h1>見出し<\/h1>/);
  assert.match(rendered, /type="checkbox" disabled checked/);
  assert.match(rendered, /<table>/);
  assert.match(rendered, /<blockquote>補足<\/blockquote>/);
  assert.match(rendered, /href="https:\/\/openai\.com"/);
  assert.match(rendered, /&lt;script&gt;alert\(&#039;xss&#039;\)&lt;\/script&gt;/);
  assert.match(rendered, /&lt;img src=x onerror=alert\(1\)&gt;/);
  assert.doesNotMatch(rendered, /href="javascript:/);
  assert.doesNotMatch(rendered, /<img src=x/);
});

test('keeps malformed markdown table input visible as escaped source text', () => {
  const rendered = model.renderWorkflowMarkdown('| A | B |\n| -- | broken |\n<script>x</script>');

  assert.match(rendered, /\| A \| B \|/);
  assert.match(rendered, /&lt;script&gt;x&lt;\/script&gt;/);
  assert.doesNotMatch(rendered, /<table>/);
});

test('task hub shell exposes list detail status settings and responsive behavior', () => {
  for (const id of ['task-hub', 'provider-status', 'task-sections', 'task-detail', 'hub-stale-minutes', 'hub-recent-hours']) {
    assert.match(html, new RegExp(`id=["']${id}["']`));
  }
  assert.match(html, /@media \(max-width: 1023px\)/);
  assert.match(html, /setInterval\(refresh, 2000\)/);
  assert.match(html, /setInterval\(heartbeat, 5000\)/);
  assert.match(html, /response\.status === 409/);
  assert.match(html, /renderWorkflowMarkdown\(markdown\)/);
});

test('the selected Plan Canvas information architecture remains in the HTML', () => {
  for (const id of [
    'now-strip',
    'phase-rail',
    'task-tree',
    'next-steps',
    'execution-pulse',
    'artifact-shelf',
    'utility-disclosure'
  ]) {
    assert.match(html, new RegExp(`id=["']${id}["']`), `${id} is required`);
  }
  assert.match(html, /role="progressbar"/);
  assert.match(html, /aria-live="polite"/);
  assert.match(html, /prefers-reduced-motion/);
  assert.match(html, /Tabler Icons/);
  assert.match(html, /id="phase-rail" role="list"/);
  assert.match(html, /id="task-tree" role="table"/);
  assert.match(html, /id="open-files" aria-label="Roadmapファイルを開く"/);
  assert.match(html, /id="export-json" aria-label="Roadmap JSONを書き出す"/);
  assert.match(html, /function stopLivePolling\(/);
  assert.match(html, /generation !== pollGeneration/);
  assert.match(html, /const current = model\.activeTask/);
  assert.match(html, /function refreshFreshness\(/);
  assert.match(html, /id="all-artifact-list"/);
  assert.match(html, /id="preview-rendered"/);
  assert.match(html, /id="preview-raw"/);
  assert.doesNotMatch(html, /id="source-preview"[^>]*aria-live/);
  assert.doesNotMatch(html, /function brandData\(/);
});
