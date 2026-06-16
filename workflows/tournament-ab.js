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

const xWins = valid.filter(v => v.winner === 'X').length
const yWins = valid.filter(v => v.winner === 'Y').length
const ties = valid.filter(v => v.winner === 'tie').length

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

const avgScoreX = valid.reduce((s, v) => s + weightedScore(v.scores.X), 0) / valid.length
const avgScoreY = valid.reduce((s, v) => s + weightedScore(v.scores.Y), 0) / valid.length

// X/Yの勝者を実際のA/Bにマッピング（swapOrderを考慮）
const xIsA = !swapOrder // swapOrder=false: X=A, Y=B / swapOrder=true: X=B, Y=A
let winner
if (xWins > yWins) winner = xIsA ? 'A' : 'B'
else if (yWins > xWins) winner = xIsA ? 'B' : 'A'
else if (avgScoreX > avgScoreY + 0.3) winner = xIsA ? 'A' : 'B'
else if (avgScoreY > avgScoreX + 0.3) winner = xIsA ? 'B' : 'A'
else winner = 'tie'

const result = {
  winner,
  votes: { A: xWins, B: yWins, tie: ties },
  avgScores: { A: Math.round(avgScoreX * 100) / 100, B: Math.round(avgScoreY * 100) / 100 },
  verdicts: valid,
  implA,
  implB,
}

log(`結果: ${winner === 'tie' ? '引き分け' : winner + '案が勝利'} (A:${avgScoreX.toFixed(2)} vs B:${avgScoreY.toFixed(2)})`)

return result
