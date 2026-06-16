export const meta = {
  name: 'tournament-ab',
  description: 'A/B並列実装 → 3ジャッジ評価 → 勝者選定',
  whenToUse: 'A/B比較で最良の実装を選びたいとき。args: {task, spec, testCmd?, baseFile?}',
  phases: [
    { title: 'Implement', detail: '2案を worktree で並列実装' },
    { title: 'Test', detail: '両案をテスト・lint' },
    { title: 'Judge', detail: '3独立ジャッジが匿名評価' },
    { title: 'Decide', detail: '多数決 + 加重スコアで勝者決定' },
  ],
}

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    winner: { type: 'string', enum: ['X', 'Y', 'tie'] },
    confidence: { type: 'number', minimum: 0, maximum: 1 },
    scores: {
      type: 'object',
      properties: {
        X: {
          type: 'object',
          properties: {
            correctness: { type: 'number' },
            maintainability: { type: 'number' },
            performance: { type: 'number' },
            security: { type: 'number' },
            brevity: { type: 'number' },
          },
          required: ['correctness', 'maintainability', 'performance', 'security', 'brevity'],
        },
        Y: {
          type: 'object',
          properties: {
            correctness: { type: 'number' },
            maintainability: { type: 'number' },
            performance: { type: 'number' },
            security: { type: 'number' },
            brevity: { type: 'number' },
          },
          required: ['correctness', 'maintainability', 'performance', 'security', 'brevity'],
        },
      },
      required: ['X', 'Y'],
    },
    reasoning: { type: 'string' },
    notable_differences: { type: 'array', items: { type: 'string' } },
  },
  required: ['winner', 'confidence', 'scores', 'reasoning'],
}

const task = args?.task ?? 'No task specified'
const spec = args?.spec ?? ''
const testCmd = args?.testCmd ?? 'npm test'
const baseFile = args?.baseFile ?? ''

// コスト暴走ガード: A/B並列実装+3ジャッジは高コスト。予算(+Nk)指定時、残量不足なら開始しない
if (budget.total && budget.remaining() < 80_000) {
  log(`予算残量不足(${Math.round(budget.remaining() / 1000)}k)でトーナメントを中止`)
  return { winner: null, reason: 'budget exhausted before tournament' }
}

// --- Phase 1: Implement ---
phase('Implement')
log(`A/Bトーナメント開始: ${task}`)

const implPrompt = (plan) => `
あなたはコード実装エージェントです。以下のタスクを実装してください。

## タスク
${task}

## 仕様
${spec}

## 実装方針
${plan}

${baseFile ? `## 対象ファイル\n${baseFile}` : ''}

## ルール
- テストが通るコードを書く
- YAGNI: 依頼にない機能を追加しない
- 実装が完了したら、変更したファイル一覧と変更概要を返す
`

const [implA, implB] = await parallel([
  () => agent(implPrompt('アプローチA: シンプルさ重視。最小限のコードで要件を満たす。'), {
    label: 'plan-a',
    phase: 'Implement',
    isolation: 'worktree',
  }),
  () => agent(implPrompt('アプローチB: 堅牢性重視。拡張性とエラー処理を充実させる。'), {
    label: 'plan-b',
    phase: 'Implement',
    isolation: 'worktree',
  }),
])

if (!implA && !implB) {
  log('両方の実装が失敗しました')
  return { winner: null, reason: 'both implementations failed' }
}
if (!implA) return { winner: 'B', reason: 'Implementation A failed', implB }
if (!implB) return { winner: 'A', reason: 'Implementation B failed', implA }

// --- Phase 2: Test ---
phase('Test')

const testPrompt = (label, implResult) => `
以下の実装をテスト・検証してください。

## 実装結果
${typeof implResult === 'string' ? implResult : JSON.stringify(implResult)}

## テストコマンド
${testCmd}

## 検証項目
1. テスト実行: \`${testCmd}\` を実行し結果を報告
2. lint: プロジェクトのlintコマンドがあれば実行
3. typecheck: TypeScriptなら tsc --noEmit
4. 変更ファイルの差分を出力

結果をJSON形式で返してください:
{
  "test_passed": true/false,
  "test_output": "...",
  "lint_passed": true/false,
  "lint_output": "...",
  "type_passed": true/false,
  "diff_summary": "..."
}
`

const [testA, testB] = await parallel([
  () => agent(testPrompt('A', implA), { label: 'test-a', phase: 'Test' }),
  () => agent(testPrompt('B', implB), { label: 'test-b', phase: 'Test' }),
])

// --- Phase 3: Judge ---
phase('Judge')
log('3人のジャッジによる匿名評価を開始')

// バイアス軽減: タスク文字列からプレゼンテーション順序を決定（Math.random不可のため）
const swapOrder = task.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0) % 2 === 1
const [first, second] = swapOrder ? [implB, implA] : [implA, implB]
const [testFirst, testSecond] = swapOrder ? [testB, testA] : [testA, testB]

const judgePrompt = (focusAxis, focusDescription) => `
あなたはコードレビューのジャッジです。2つの匿名実装を比較評価してください。

## タスク仕様
${task}
${spec}

## Implementation X の結果
${typeof first === 'string' ? first : JSON.stringify(first)}

テスト結果: ${typeof testFirst === 'string' ? testFirst : JSON.stringify(testFirst)}

## Implementation Y の結果
${typeof second === 'string' ? second : JSON.stringify(second)}

テスト結果: ${typeof testSecond === 'string' ? testSecond : JSON.stringify(testSecond)}

## あなたの重点評価軸: ${focusAxis}
${focusDescription}

## 評価基準（各1-5点）
- correctness (重み3x): テスト通過率、エッジケース
- maintainability (重み2x): 可読性、構造、命名
- performance (重み2x): 計算量、メモリ効率
- security (重み2x): OWASP Top 10
- brevity (重み1x): コード量の少なさ

## ルール
- X/Yどちらかに偏らず公平に評価
- セキュリティスコア2以下の実装は勝者にしない
- 僅差（加重平均0.3以内）ならtie + confidence低め
`

const verdicts = await parallel([
  () => agent(
    judgePrompt('正確性', 'テスト通過率、エッジケース処理、仕様との整合性を重点的に評価'),
    { label: 'judge-correctness', phase: 'Judge', model: 'opus', schema: VERDICT_SCHEMA }
  ),
  () => agent(
    judgePrompt('保守性', '可読性、拡張性、コード構造、命名品質を重点的に評価'),
    { label: 'judge-maintainability', phase: 'Judge', model: 'opus', schema: VERDICT_SCHEMA }
  ),
  () => agent(
    judgePrompt('パフォーマンス', '計算量、メモリ使用量、応答速度を重点的に評価'),
    { label: 'judge-performance', phase: 'Judge', model: 'opus', schema: VERDICT_SCHEMA }
  ),
])

// --- Phase 4: Decide ---
phase('Decide')

const valid = verdicts.filter(Boolean)
if (valid.length === 0) {
  log('全ジャッジが失敗')
  return { winner: null, reason: 'all judges failed' }
}

const weightedScore = (scores) => {
  const w = { correctness: 3, maintainability: 2, performance: 2, security: 2, brevity: 1 }
  let sum = 0
  let wSum = 0
  for (const [k, v] of Object.entries(scores)) {
    if (w[k] !== undefined) {
      sum += v * w[k]
      wSum += w[k]
    }
  }
  return wSum > 0 ? sum / wSum : 0
}

// X/Y は提示順（swapOrderで入替済み）。集計・レポートは必ず実A/Bへ写像してから扱う。
const xIsA = !swapOrder // false: X=A,Y=B / true: X=B,Y=A
const mapAB = (xVal, yVal) => (xIsA ? [xVal, yVal] : [yVal, xVal])

const xWins = valid.filter(v => v.winner === 'X').length
const yWins = valid.filter(v => v.winner === 'Y').length
const ties = valid.filter(v => v.winner === 'tie').length
const [aWins, bWins] = mapAB(xWins, yWins)

const avgScoreX = valid.reduce((s, v) => s + weightedScore(v.scores.X), 0) / valid.length
const avgScoreY = valid.reduce((s, v) => s + weightedScore(v.scores.Y), 0) / valid.length
const [scoreA, scoreB] = mapAB(avgScoreX, avgScoreY)

// セキュリティ下限ハードガード: security平均が閾値以下の案は勝者にしない
// （ab-judge.md / loop-engineering.md が約束する安全保証をコードで強制する）
const avgSecX = valid.reduce((s, v) => s + (v.scores.X.security ?? 0), 0) / valid.length
const avgSecY = valid.reduce((s, v) => s + (v.scores.Y.security ?? 0), 0) / valid.length
const [secA, secB] = mapAB(avgSecX, avgSecY)
const SEC_FLOOR = 2
const aBlocked = secA <= SEC_FLOOR
const bBlocked = secB <= SEC_FLOOR

let winner
let reason
if (aBlocked && bBlocked) {
  winner = null
  reason = `security floor violated (A:${secA.toFixed(1)}, B:${secB.toFixed(1)} <= ${SEC_FLOOR})`
} else if (aBlocked) {
  winner = 'B'
  reason = `A excluded by security floor (sec ${secA.toFixed(1)})`
} else if (bBlocked) {
  winner = 'A'
  reason = `B excluded by security floor (sec ${secB.toFixed(1)})`
} else if (aWins > bWins) { winner = 'A'; reason = `A won by votes (${aWins}-${bWins})` }
else if (bWins > aWins) { winner = 'B'; reason = `B won by votes (${bWins}-${aWins})` }
else if (scoreA > scoreB + 0.3) { winner = 'A'; reason = 'A won by weighted score' }
else if (scoreB > scoreA + 0.3) { winner = 'B'; reason = 'B won by weighted score' }
else { winner = 'tie'; reason = 'too close to call' }

const result = {
  winner,
  reason,
  votes: { A: aWins, B: bWins, tie: ties },
  avgScores: { A: Math.round(scoreA * 100) / 100, B: Math.round(scoreB * 100) / 100 },
  security: { A: Math.round(secA * 100) / 100, B: Math.round(secB * 100) / 100 },
  verdicts: valid,
  implA,
  implB,
}

log(`結果: ${winner === null ? 'セキュリティ下限割れで勝者なし' : winner === 'tie' ? '引き分け' : winner + '案が勝利'} (A:${scoreA.toFixed(2)} vs B:${scoreB.toFixed(2)}, sec A:${secA.toFixed(1)}/B:${secB.toFixed(1)})`)

return result
