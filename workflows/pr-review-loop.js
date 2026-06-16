export const meta = {
  name: 'pr-review-loop',
  description: 'PR/差分をレビュー→修正→再レビューを合格まで自動ループ（最大3ラウンド）',
  whenToUse: 'PRに指摘が来た時 / PR前の自動レビュー対応。args: {pr?, baseBranch?, maxRounds?, autoFix?}',
  phases: [
    { title: 'Review', detail: '専門reviewerを並列起動して差分をレビュー' },
    { title: 'Fix', detail: 'CRITICAL/IMPORTANT指摘を修正してcommit' },
    { title: 'Report', detail: '合格/エスカレーションを報告' },
  ],
}

// レビュー指摘のスキーマ（severity 3階級・CLAUDE.md準拠）
const FINDINGS_SCHEMA = {
  type: 'object',
  properties: {
    dimension: { type: 'string' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          severity: { type: 'string', enum: ['CRITICAL', 'IMPORTANT', 'MINOR'] },
          title: { type: 'string' },
          file: { type: 'string' },
          line: { type: 'string' },
          detail: { type: 'string' },
          fix_hint: { type: 'string' },
        },
        required: ['severity', 'title', 'detail'],
      },
    },
    good_things: { type: 'array', items: { type: 'string' } },
  },
  required: ['dimension', 'findings'],
}

const pr = args?.pr ?? null
const baseBranch = args?.baseBranch ?? ''
const maxRounds = args?.maxRounds ?? 3
const autoFix = args?.autoFix ?? true

// 差分取得方針（reviewer/fixer 各agentが自分で実行する）
const diffSpec = pr
  ? `gh pr diff ${pr}`
  : baseBranch
    ? `git diff ${baseBranch}...HEAD`
    : 'git diff HEAD~1...HEAD（直近コミット）または git diff（作業ツリー）'

// 変更規模に応じた reviewer セット（常に必須3観点 + 標準でquality/test）
const REVIEW_DIMS = [
  { key: 'arch', agentType: 'arch-reviewer', focus: 'アーキテクチャ・責務分離・依存方向・循環参照・過度な結合' },
  { key: 'security', agentType: 'security-reviewer', focus: 'SQLi/XSS/CSRF・認証認可の不備・入力検証・機密情報のハードコード' },
  { key: 'perf', agentType: 'perf-reviewer', focus: 'N+1クエリ・不要な再レンダリング・メモリリーク・非効率アルゴリズム' },
  { key: 'quality', agentType: 'code-quality-reviewer', focus: '命名の不統一・重複・過度に長い関数・深いネスト・不要コード' },
  { key: 'test', agentType: 'test-reviewer', focus: '単体/統合/E2Eの不足・エッジケース/異常系のカバレッジ' },
]

const reviewPrompt = (focus) => `
あなたはコードレビュー担当。まず対象差分を取得する:
- 推奨コマンド: ${diffSpec}
- 取得できない場合は \`git status\` と \`git diff\` で変更を把握する

## 重点観点
${focus}

## ルール（CLAUDE.md準拠）
- severity は CRITICAL / IMPORTANT / MINOR の3階級
- 各findingに file / line / detail / fix_hint を付ける
- 推測で指摘しない。差分の全行に目を通す
- 良い点(good_things)も1-3個（本当に良い箇所のみ）
`

let round = 0
let lastFindings = []

while (round < maxRounds) {
  round++
  phase('Review')
  log(`Round ${round}/${maxRounds}: 並列レビュー実行`)

  const reviews = await parallel(
    REVIEW_DIMS.map((d) => () =>
      agent(reviewPrompt(d.focus), {
        label: `review:${d.key}:r${round}`,
        phase: 'Review',
        agentType: d.agentType,
        schema: FINDINGS_SCHEMA,
      })
    )
  )

  const findings = reviews
    .filter(Boolean)
    .flatMap((r) => (r.findings || []).map((f) => ({ ...f, dimension: r.dimension })))
  const high = findings.filter((f) => f.severity === 'CRITICAL' || f.severity === 'IMPORTANT')
  lastFindings = findings

  log(`Round ${round}: CRITICAL/IMPORTANT ${high.length}件 / MINOR ${findings.length - high.length}件`)

  // 合格判定: 高位指摘ゼロ
  if (high.length === 0) {
    phase('Report')
    log(`合格（Round ${round}）: CRITICAL/IMPORTANT なし`)
    return { result: 'SHIP', rounds: round, findings, minors: findings.filter((f) => f.severity === 'MINOR') }
  }

  // 自動修正しない設定なら指摘を返して終了
  if (!autoFix) {
    phase('Report')
    return { result: 'NEEDS_WORK', rounds: round, high }
  }

  // 修正フェーズ
  phase('Fix')
  log(`Round ${round}: CRITICAL/IMPORTANT ${high.length}件を修正`)
  const fix = await agent(
    `次のレビュー指摘を修正せよ。対象差分: ${diffSpec}

## 修正対象（CRITICAL/IMPORTANT のみ）
${JSON.stringify(high, null, 2)}

## ルール
- 指摘箇所のみ surgical に修正する（依頼外の改変をしない）
- 修正後はプロジェクトのテスト/lint/typecheckを実行して通す
- 重い実装は codex に委任してよい: Agent(subagent_type: "codex:codex-rescue")
- 修正できたら git commit する（fix: で始まる日本語メッセージ）
- 修正不能な指摘があれば理由を明記して返す`,
    { label: `fix:r${round}`, phase: 'Fix' }
  )

  if (!fix) {
    phase('Report')
    return { result: 'BLOCKED', rounds: round, reason: '修正フェーズが失敗', high }
  }
}

// 最大ラウンド超過 → エスカレーション
phase('Report')
const remaining = lastFindings.filter((f) => f.severity === 'CRITICAL' || f.severity === 'IMPORTANT')
log(`最大${maxRounds}ラウンド到達。未解決 ${remaining.length}件をエスカレーション`)
return { result: 'ESCALATE', rounds: maxRounds, remaining }
