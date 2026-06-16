export const meta = {
  name: 'morning-kickoff',
  description: '朝の日次キックオフ: データ収集 → 計画作成 → Slack通知',
  whenToUse: '毎朝9:00のスケジュールタスクから実行、または手動で /morning-kickoff',
  phases: [
    { title: 'Gather', detail: 'Jira/Calendar/未完了/PRを並列取得' },
    { title: 'Plan', detail: '優先順位付き日次計画を作成' },
    { title: 'Notify', detail: 'Slackに計画を投稿' },
  ],
}

const DAILY_PLAN_SCHEMA = {
  type: 'object',
  properties: {
    date: { type: 'string' },
    focus: { type: 'string' },
    p0: { type: 'array', items: { type: 'object', properties: { key: { type: 'string' }, title: { type: 'string' }, reason: { type: 'string' } }, required: ['title'] } },
    p1: { type: 'array', items: { type: 'object', properties: { key: { type: 'string' }, title: { type: 'string' } }, required: ['title'] } },
    p2: { type: 'array', items: { type: 'object', properties: { key: { type: 'string' }, title: { type: 'string' } }, required: ['title'] } },
    meetings: { type: 'array', items: { type: 'object', properties: { time: { type: 'string' }, title: { type: 'string' }, prep: { type: 'string' } }, required: ['time', 'title'] } },
    carryover: { type: 'array', items: { type: 'string' } },
    estimated_hours: { type: 'number' },
  },
  required: ['date', 'focus', 'p0', 'p1', 'meetings'],
}

// --- Phase 1: Gather ---
phase('Gather')
log('データ収集開始')

const [jiraData, calendarData, carryoverData, prData] = await parallel([
  () => agent(`
Jiraで自分（yoshiki.morii@dena.com）にアサインされたチケットを取得してください。
ステータス: Open, In Progress, To Do のもの。
各チケットについて以下を返してください:
- チケットキー
- タイトル
- ステータス
- 優先度
- 期限
- Epic（あれば）
JQLを使ってください: assignee = currentUser() AND statusCategory != Done ORDER BY priority DESC, duedate ASC
`, { label: 'jira-tickets', phase: 'Gather' }),

  () => agent(`
Google Calendarから今日の予定を取得してください。
各予定について:
- 開始時刻
- 終了時刻
- タイトル
- 参加者数
- 必須出席かどうか
予定がある時間帯と空き時間帯も計算してください。
`, { label: 'calendar-events', phase: 'Gather' }),

  () => agent(`
昨日のdailyノート（~/.claude/.local/daily/ 配下の最新ファイル）を読み、
未完了のタスク（チェックボックスが未チェック [ ] のもの）を抽出してください。
ファイルが見つからない場合は空リストを返してください。
`, { label: 'carryover-tasks', phase: 'Gather' }),

  () => agent(`
GitHub CLIを使って、自分宛のPRレビューリクエストを取得してください。
コマンド: gh search prs --review-requested=@me --state=open --json number,title,repository,createdAt,author
各PRの緊急度（作成日からの経過日数）も計算してください。
`, { label: 'pr-reviews', phase: 'Gather' }),
])

// --- Phase 2: Plan ---
phase('Plan')
log('日次計画を作成中')

const plan = await agent(`
あなたはdaily-plannerエージェントです。以下の情報から日次計画を作成してください。

## Jiraチケット
${typeof jiraData === 'string' ? jiraData : JSON.stringify(jiraData)}

## カレンダー
${typeof calendarData === 'string' ? calendarData : JSON.stringify(calendarData)}

## 昨日の未完了
${typeof carryoverData === 'string' ? carryoverData : JSON.stringify(carryoverData)}

## PRレビュー待ち
${typeof prData === 'string' ? prData : JSON.stringify(prData)}

## 優先順位ルール
- P0（即対応）: ブロッカー、本番障害、SLA違反リスク
- P1（今日中）: 今日期限、他チームブロック中、48h以上経過PRレビュー
- P2（余裕があれば）: 今週期限、通常PRレビュー
- ミーティング時間を考慮し、実作業可能時間を8時間以内に収める
- P0が3件以上なら警告フラグを立てる

focusには今日最も重要な1つのことを書いてください。
`, {
  label: 'create-plan',
  phase: 'Plan',
  model: 'opus',
  agentType: 'daily-planner',
  schema: DAILY_PLAN_SCHEMA,
})

if (!plan) {
  log('計画作成に失敗')
  return { success: false, reason: 'plan creation failed' }
}

// --- Phase 3: Notify ---
phase('Notify')

const formatPlan = (p) => {
  const lines = [`*日次計画 — ${p.date}*`, '', `> ${p.focus}`, '']
  if (p.p0?.length) {
    lines.push('*P0（即対応）*')
    p.p0.forEach(t => lines.push(`- ${t.key ? `[${t.key}] ` : ''}${t.title}${t.reason ? ` — ${t.reason}` : ''}`))
    lines.push('')
  }
  if (p.p1?.length) {
    lines.push('*P1（今日中）*')
    p.p1.forEach(t => lines.push(`- ${t.key ? `[${t.key}] ` : ''}${t.title}`))
    lines.push('')
  }
  if (p.p2?.length) {
    lines.push('*P2（余裕があれば）*')
    p.p2.forEach(t => lines.push(`- ${t.key ? `[${t.key}] ` : ''}${t.title}`))
    lines.push('')
  }
  if (p.meetings?.length) {
    lines.push('*ミーティング*')
    p.meetings.forEach(m => lines.push(`- ${m.time} ${m.title}${m.prep ? ` (準備: ${m.prep})` : ''}`))
    lines.push('')
  }
  if (p.carryover?.length) {
    lines.push('*昨日の未完了*')
    p.carryover.forEach(c => lines.push(`- ${c}`))
    lines.push('')
  }
  lines.push(`_推定作業時間: ${p.estimated_hours ?? '?'}h_`)
  return lines.join('\n')
}

const slackMsg = formatPlan(plan)
const notifyResult = await agent(`
以下のメッセージをSlackの自分のDM（またはtimes-yoshikiチャンネル）に投稿してください。
投稿できない場合は、メッセージ内容をそのまま返してください。

---
${slackMsg}
---
`, { label: 'slack-notify', phase: 'Notify' })

log('日次計画の作成と通知が完了')

return { success: true, plan, notified: !!notifyResult }
