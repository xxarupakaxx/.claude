export const meta = {
  name: 'evening-review',
  description: '夕方レビュー: コスト集計 → 失敗パターン分析 → 改善提案 → Slack報告',
  whenToUse: '毎夕18:00のスケジュールタスクから実行、または手動で /evening-review',
  phases: [
    { title: 'Cost', detail: '本日のトークン・コスト集計' },
    { title: 'Failures', detail: '失敗パターン分析' },
    { title: 'Improve', detail: '改善提案の生成' },
    { title: 'Summary', detail: 'Slack日次サマリー投稿' },
  ],
}

const COST_REPORT_SCHEMA = {
  type: 'object',
  properties: {
    date: { type: 'string' },
    total_cost_usd: { type: 'number' },
    sessions: { type: 'number' },
    breakdown: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          model: { type: 'string' },
          input_tokens: { type: 'number' },
          output_tokens: { type: 'number' },
          cost_usd: { type: 'number' },
        },
        required: ['model', 'cost_usd'],
      },
    },
    alert_level: { type: 'string', enum: ['ok', 'info', 'warning', 'critical'] },
    recommendations: { type: 'array', items: { type: 'string' } },
  },
  required: ['date', 'total_cost_usd', 'alert_level'],
}

const FAILURE_SCHEMA = {
  type: 'object',
  properties: {
    patterns: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          type: { type: 'string', enum: ['repeated_error', 'inefficiency', 'quality_issue'] },
          description: { type: 'string' },
          occurrences: { type: 'number' },
          impact: { type: 'string', enum: ['high', 'medium', 'low'] },
          suggested_rule: { type: 'string' },
        },
        required: ['type', 'description', 'occurrences', 'impact'],
      },
    },
    total_errors: { type: 'number' },
    total_retries: { type: 'number' },
  },
  required: ['patterns', 'total_errors'],
}

// --- Phase 1: Cost ---
phase('Cost')
log('本日のコスト集計を開始')

const costReport = await agent(`
本日のClaude Code使用コストを集計してください。

## データソース（優先順位順）
1. ccusage コマンド: \`ccusage --today\` または \`ccusage\`（インストール済みなら）
2. コスト追跡ログ: ~/.claude/.local/cost-track/ 配下の本日分
3. セッションレポート: ~/.claude/projects/ 配下のJSONLから推計

## アラート閾値
- ok: $0-5
- info: $5-15
- warning: $15-30
- critical: $30+

## モデル別推奨
- critical時: opus → sonnet へのダウングレードを提案
- warning時: 並列agent数の削減を提案
- info以下: 現状維持

コマンドが見つからない場合はログファイルから推計してください。
`, {
  label: 'cost-report',
  phase: 'Cost',
  agentType: 'cost-monitor',
  schema: COST_REPORT_SCHEMA,
})

// --- Phase 2: Failures ---
phase('Failures')
log('失敗パターンを分析中')

const failures = await agent(`
本日のClaude Codeセッションから失敗パターンを分析してください。

## データソース
1. ~/.claude/.local/harness-suggestions/ 配下の本日分（stop hookが生成）
2. ~/.claude/projects/ 配下の本日のセッションJSONL

## 検出対象
1. **繰り返しエラー**: 同じエラーメッセージが3回以上
2. **非効率パターン**: 同じファイルの5回以上のRead、10回以上のgrep
3. **品質問題**: レビュー指摘の再発パターン

## 注意
- セッションファイルが大きい場合はgrep/headで効率的に検索
- パターンが見つからなければ空リストを返す（無理に見つけない）
`, {
  label: 'failure-analysis',
  phase: 'Failures',
  agentType: 'harness-improver',
  schema: FAILURE_SCHEMA,
})

// --- Phase 3: Improve ---
phase('Improve')

const improvements = []

if (costReport?.alert_level === 'critical' || costReport?.alert_level === 'warning') {
  log(`コストアラート: ${costReport.alert_level} ($${costReport.total_cost_usd})`)
  const costImprovement = await agent(`
コスト削減の改善提案を生成してください。

## 現在のコスト状況
${JSON.stringify(costReport)}

## 提案の形式
- 具体的なルール変更（CLAUDE.md or rules/ への追記内容）
- 期待されるコスト削減効果
- トレードオフ（品質への影響）

最大2件の提案に絞ってください。
`, { label: 'cost-improvement', phase: 'Improve', model: 'opus' })
  if (costImprovement) improvements.push({ type: 'cost', content: costImprovement })
}

const significantFailures = (failures?.patterns ?? []).filter(p => p.impact === 'high' || p.occurrences >= 3)
if (significantFailures.length > 0) {
  log(`重要な失敗パターン: ${significantFailures.length}件`)
  const failureImprovement = await agent(`
以下の失敗パターンに対する改善提案を生成してください。

## 失敗パターン
${JSON.stringify(significantFailures)}

## 提案ルール
- 既存の ~/.claude/CLAUDE.md や ~/.claude/rules/*.md と矛盾しないこと
- 過度に制限的でないこと（生産性を著しく下げない）
- 最大3件

## 出力形式（各提案）
- パターン: [検出された問題]
- 提案ルール: [追加すべきルール文]
- 適用先: [ファイルパス]
- 根拠: [発生回数、影響]
`, { label: 'failure-improvement', phase: 'Improve', model: 'opus', agentType: 'harness-improver' })
  if (failureImprovement) improvements.push({ type: 'failure', content: failureImprovement })
}

if (improvements.length === 0) {
  log('改善提案なし（問題なし）')
}

// --- Phase 4: Summary ---
phase('Summary')
log('日次サマリーを作成中')

const summaryLines = [
  `*夕方レビュー*`,
  '',
  `*コスト*: $${costReport?.total_cost_usd?.toFixed(2) ?? '?'} (${costReport?.alert_level ?? 'unknown'}) / ${costReport?.sessions ?? '?'}セッション`,
]

if (costReport?.breakdown?.length) {
  summaryLines.push('')
  costReport.breakdown.forEach(b => {
    summaryLines.push(`  - ${b.model}: $${b.cost_usd?.toFixed(2) ?? '?'}`)
  })
}

summaryLines.push('')
summaryLines.push(`*失敗パターン*: ${failures?.total_errors ?? 0}エラー / ${failures?.patterns?.length ?? 0}パターン検出`)

if (significantFailures.length > 0) {
  significantFailures.forEach(p => {
    summaryLines.push(`  - [${p.impact}] ${p.description} (${p.occurrences}回)`)
  })
}

if (improvements.length > 0) {
  summaryLines.push('')
  summaryLines.push(`*改善提案*: ${improvements.length}件（要確認）`)
}

if (costReport?.recommendations?.length) {
  summaryLines.push('')
  summaryLines.push('*推奨アクション*')
  costReport.recommendations.forEach(r => summaryLines.push(`  - ${r}`))
}

const summaryText = summaryLines.join('\n')

await agent(`
以下のサマリーをSlackに投稿してください。投稿先は自分のDMまたはtimes-yoshikiチャンネル。
投稿できない場合はテキストをそのまま返してください。

---
${summaryText}
---
`, { label: 'slack-summary', phase: 'Summary' })

log('夕方レビュー完了')

return {
  success: true,
  cost: costReport,
  failures,
  improvements: improvements.length,
}
