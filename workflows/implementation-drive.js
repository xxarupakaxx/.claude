export const meta = {
  name: 'implementation-drive',
  description: 'Jiraチケット分析 → 実装方針決定 → 実装・テスト・レビュー',
  whenToUse: 'Jiraチケットの実装を自動化したいとき。args: {ticketKey, useTournament?}',
  phases: [
    { title: 'Analyze', detail: 'チケット分析 + コードベース調査' },
    { title: 'Spec', detail: '仕様書ドラフト生成' },
    { title: 'Implement', detail: '実装（直接 or A/Bトーナメント）' },
    { title: 'Verify', detail: 'テスト + レビュー' },
    { title: 'Report', detail: 'Jiraに結果記録' },
  ],
}

const TASK_ANALYSIS_SCHEMA = {
  type: 'object',
  properties: {
    ticketKey: { type: 'string' },
    title: { type: 'string' },
    complexity: { type: 'string', enum: ['simple', 'medium', 'complex'] },
    estimatedFiles: { type: 'number' },
    estimatedLines: { type: 'number' },
    affectedModules: { type: 'array', items: { type: 'string' } },
    risks: { type: 'array', items: { type: 'string' } },
    subtasks: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          title: { type: 'string' },
          description: { type: 'string' },
          estimatedLines: { type: 'number' },
        },
        required: ['title'],
      },
    },
    useTournament: { type: 'boolean' },
  },
  required: ['ticketKey', 'title', 'complexity', 'subtasks', 'useTournament'],
}

const ticketKey = args?.ticketKey
if (!ticketKey) {
  log('ticketKey が指定されていません')
  return { success: false, reason: 'ticketKey required in args' }
}
const forceTournament = args?.useTournament ?? false

// --- Phase 1: Analyze ---
phase('Analyze')
log(`チケット ${ticketKey} の分析を開始`)

const analysis = await agent(`
Jiraチケット ${ticketKey} を分析してください。

## 手順
1. Jira MCPでチケット詳細を取得（説明、受入基準、コメント、関連チケット）
2. チケット内容からコードベースの関連箇所をGrep/Globで調査
3. 影響範囲を特定

## 判定基準
- simple: 1-5ファイル、100行以下、既存パターン踏襲
- medium: 5-15ファイル、100-500行、一部新規パターン
- complex: 15ファイル超 or 500行超 or 新規アーキテクチャ

## トーナメント推奨条件
以下のいずれかに該当する場合、useTournament=trueを設定:
- 複数の実装アプローチが考えられる
- パフォーマンスが重要
- complexityがcomplex
${forceTournament ? '\n**注意: ユーザーがトーナメント使用を明示的に指定しています。useTournament=trueにしてください。**' : ''}
`, {
  label: 'analyze',
  phase: 'Analyze',
  model: 'opus',
  schema: TASK_ANALYSIS_SCHEMA,
})

if (!analysis) {
  return { success: false, reason: 'analysis failed' }
}

log(`分析完了: ${analysis.complexity} (${analysis.estimatedFiles}ファイル, ~${analysis.estimatedLines}行, tournament=${analysis.useTournament})`)

// --- Phase 2: Spec ---
phase('Spec')

const spec = await agent(`
Jiraチケット ${ticketKey} の仕様書ドラフトを生成してください。

## チケット分析結果
${JSON.stringify(analysis)}

## 仕様書テンプレート
- 概要: 何を、なぜ変更するか
- 要件: 機能要件 + 非機能要件
- 技術設計: 変更対象ファイル、API変更、DB変更
- テスト計画: ユニット/統合/E2E
- リスク・注意点
- サブタスク一覧

仕様書をMarkdown形式で作成し、${ticketKey}のコメントとしてJiraに追加してください。
追加できない場合はMarkdownテキストをそのまま返してください。
`, {
  label: 'spec',
  phase: 'Spec',
  model: 'opus',
  agentType: 'jira-spec-writer',
})

// --- Phase 3: Implement ---
phase('Implement')

let implResult

if (analysis.useTournament) {
  log('A/Bトーナメントモードで実装')
  implResult = await workflow('tournament-ab', {
    task: `${ticketKey}: ${analysis.title}`,
    spec: typeof spec === 'string' ? spec : JSON.stringify(spec),
  })
  // セキュリティ下限割れ等で勝者なしなら、下流に流さず失敗扱い
  if (implResult && implResult.winner === null) {
    log(`トーナメント勝者なし: ${implResult.reason ?? 'no winner'}`)
    return { success: false, reason: implResult.reason ?? 'tournament: no winner', tournament: implResult }
  }
} else if (analysis.complexity === 'simple' || !analysis.subtasks?.length) {
  log('シンプル実装モード')
  implResult = await agent(`
以下の仕様に基づいてコードを実装してください。

## チケット: ${ticketKey} — ${analysis.title}

## 仕様
${typeof spec === 'string' ? spec : JSON.stringify(spec)}

## サブタスク
${analysis.subtasks.map((s, i) => `${i + 1}. ${s.title}: ${s.description ?? ''}`).join('\n')}

## ルール
- テストも一緒に書く
- 既存パターンに合わせる
- YAGNI: 依頼にない機能は追加しない
- こまめにgit commit
`, { label: 'implement-simple', phase: 'Implement' })
} else {
  log('パイプライン実装モード')
  implResult = await pipeline(
    analysis.subtasks,
    (subtask, _, idx) => agent(`
サブタスク ${idx + 1}/${analysis.subtasks.length} を実装してください。

## 親チケット: ${ticketKey} — ${analysis.title}
## サブタスク: ${subtask.title}
${subtask.description ? `## 説明\n${subtask.description}` : ''}

## 仕様コンテキスト
${typeof spec === 'string' ? spec : JSON.stringify(spec)}

## ルール
- このサブタスクの範囲のみ実装
- 直前のサブタスクの変更の上に積み増す（同一ブランチ/作業ツリー）
- テストも書く
- git commit する
`, {
      label: `impl-${idx}`,
      phase: 'Implement',
      // 逐次サブタスクは互いの変更を前提に積み増すため worktree 隔離しない
      // （隔離すると後続サブタスクが前の成果を見られず、かつメイン未統合になる）
    }),
  )
}

// --- Phase 4: Verify（review→fix→re-review 自律ループ）---
phase('Verify')
log('検証＋自動修正ループ実行中（CRITICAL/IMPORTANTが0になるまで最大3ラウンド）')

const VERIFY_SCHEMA = {
  type: 'object',
  properties: {
    passed: { type: 'boolean' },
    rounds: { type: 'number' },
    remaining: {
      type: 'array',
      items: {
        type: 'object',
        properties: { severity: { type: 'string' }, title: { type: 'string' } },
        required: ['severity', 'title'],
      },
    },
    summary: { type: 'string' },
  },
  required: ['passed', 'summary'],
}

const verifyResult = await agent(`
実装結果を検証し、CRITICAL/IMPORTANT指摘が無くなるまで「レビュー→修正→再レビュー」を最大3ラウンド繰り返してください（信頼タスク全自律: 確認不要で修正してよい）。

## 実装結果
${typeof implResult === 'string' ? implResult : JSON.stringify(implResult)}

## 各ラウンドの手順
1. テスト実行（プロジェクトのテストコマンドを探して実行） / lint・format / TypeScriptなら型チェック
2. 変更ファイルをコードレビュー（セキュリティ・パフォーマンス・可読性・テスト網羅）。指摘を severity (CRITICAL/IMPORTANT/MINOR) で分類
3. CRITICAL/IMPORTANT が残っていれば surgical に修正して git commit → 次ラウンドで再検証
4. CRITICAL/IMPORTANT が 0 になったら合格として終了（MINORは残してよい）

## 出力
- passed: 最終的に CRITICAL/IMPORTANT が 0 なら true
- rounds: 実施ラウンド数
- remaining: 3ラウンドでも残った CRITICAL/IMPORTANT のリスト
- summary: テスト結果と対応内容の要約
`, { label: 'verify', phase: 'Verify', schema: VERIFY_SCHEMA })

// --- Phase 5: Report ---
phase('Report')

await agent(`
実装完了をJiraチケット ${ticketKey} に記録してください。

## 分析結果
${JSON.stringify({ complexity: analysis.complexity, files: analysis.estimatedFiles, tournament: analysis.useTournament })}

## 検証結果
${typeof verifyResult === 'string' ? verifyResult : JSON.stringify(verifyResult)}

以下をJiraコメントとして追加してください:
1. 実装完了の報告
2. 変更ファイル一覧
3. テスト結果サマリー
4. レビュー指摘事項（あれば）

追加できない場合はテキストをそのまま返してください。
`, { label: 'report', phase: 'Report' })

log(`${ticketKey} の実装フローが完了`)

return {
  success: true,
  ticketKey,
  complexity: analysis.complexity,
  tournament: analysis.useTournament,
  subtasks: analysis.subtasks.length,
}
