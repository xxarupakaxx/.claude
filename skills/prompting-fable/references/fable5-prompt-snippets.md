# Fable 5 推奨プロンプト snippet 集（原文）

出典: Anthropic "Prompting Claude Fable 5"
https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5

すべて公式ガイド掲載の原文（英語）。プロンプトへはこのままコピペして使う。
[S番号] は SKILL.md の各 Step から参照される snippet 番号（Step 2 の項目番号 # とは一致しない）。
一部の見出し（S8, S13）は関連 snippet を複数含むため、組み込む際は見出し内の全ブロックを確認する。

## S1. Overplanning 抑止（Longer turns by default）

曖昧なタスクで計画過多にさせないための指示。

```text
When you have enough information to act, act. Do not re-derive facts already established in the conversation, re-litigate a decision the user has already made, or narrate options you will not pursue in user-facing messages. If you are weighing a choice, give a recommendation, not an exhaustive survey. This does not apply to thinking blocks.
```

## S2. 過剰作業抑止（Consider all effort levels）

高 effort での依頼外の整理・refactor を防ぐ指示。

```text
Don't add features, refactor, or introduce abstractions beyond what the task requires. A bug fix doesn't need surrounding cleanup and a one-shot operation usually doesn't need a helper. Don't design for hypothetical future requirements: do the simplest thing that works well. Avoid premature abstraction and half-finished implementations. Don't add error handling, fallbacks, or validation for scenarios that cannot happen. Trust internal code and framework guarantees. Only validate at system boundaries (user input, external APIs). Don't use feature flags or backwards-compatibility shims when you can just change the code.
```

## S3. Brevity 指示（Strong instruction following）

冗長化パターンを個別列挙する代わりに効く短い指示。

```text
Lead with the outcome. Your first sentence after finishing should answer "what happened" or "what did you find": the thing the user would ask for if they said "just give me the TLDR." Supporting detail and reasoning come after. Being readable and being concise are different things, and readability matters more.

The way to keep output short is to be selective about what you include (drop details that don't change what the reader would do next), not to compress the writing into fragments, abbreviations, arrow chains like A → B → fails, or jargon.
```

## S4. 停止条件（Strong instruction following — checkpoint）

本当にユーザーが必要な場面だけで止めるための指示。ケースの列挙は不要。

```text
Pause for the user only when the work genuinely requires them: a destructive or irreversible action, a real scope change, or input that only they can provide. If you hit one of these, ask and end the turn, rather than ending on a promise.
```

## S5. 証拠つき進捗（Ground progress claims during long runs）

進捗報告を tool result と突き合わせて監査させる指示。捏造された進捗報告をほぼ排除。

```text
Before reporting progress, audit each claim against a tool result from this session. Only report work you can point to evidence for; if something is not yet verified, say so explicitly. Report outcomes faithfully: if tests fail, say so with the output; if a step was skipped, say that; when something is done and verified, state it plainly without hedging.
```

## S6. 作業境界（State the boundaries）

依頼されていない行動を抑える制約の明示。

```text
When the user is describing a problem, asking a question, or thinking out loud rather than requesting a change, the deliverable is your assessment. Report your findings and stop. Don't apply a fix until they ask for one. Before running a command that changes system state (restarts, deletes, config edits), check that the evidence actually supports that specific action. A signal that pattern-matches to a known failure may have a different cause.
```

## S7. 並列 subagent（Parallel subagents）

委任と非同期並行作業を促す指示。

```text
Delegate independent subtasks to subagents and keep working while they run. Intervene if a subagent goes off track or is missing relevant context.
```

## S8. memory 設計（Construct a memory system）

教訓の記録ルール。

```text
Store one lesson per file with a one-line summary at the top. Record corrections and confirmed approaches alike, including why they mattered. Don't save what the repo or chat history already records; update an existing note rather than creating a duplicate; delete notes that turn out to be wrong.
```

既存履歴から memory を bootstrap する指示。

```text
Reflect on the previous sessions we've had together. Use subagents to identify core themes and lessons, and store them in [X]. Make sure you know to reference [X] for future use.
```

## S9. 早期停止防止（Rare cases of early stopping）

autonomous パイプライン用の system reminder。

```text
You are operating autonomously. The user is not watching in real time and cannot answer questions mid-task, so asking "Want me to…?" or "Shall I…?" will block the work. For reversible actions that follow from the original request, proceed without asking. Offering follow-ups after the task is done is fine; asking permission after already discussing with the user before doing the work is not. Before ending your turn, check your last paragraph. If it is a plan, an analysis, a question, a list of next steps, or a promise about work you have not done ("I'll…", "let me know when…"), do that work now with tool calls. End your turn only when the task is complete or you are blocked on input only the user can provide.
```

## S10. context 不安防止（Rare cases of context-budget concern）

harness が残量カウントを見せざるを得ない場合の安心指示。

```text
You have ample context remaining. Do not stop, summarize, or suggest a new session on account of context limits. Continue the work.
```

## S11. 理由を渡す（Give the reason, not only the request）

依頼の意図・背景を渡すテンプレート。

```text
I'm working on [the larger task] for [who it's for]. They need [what the output enables]. With that in mind: [request].
```

## S12. 最終報告の読みやすさ（Readability when communicating with the user）

長い agentic 会話向けの communication 追補。

```text
Terse shorthand is fine between tool calls (that's you thinking out loud, and brevity there is good). Your final summary is different: it's for a reader who didn't see any of that.

If you've been working for a while without the user watching (overnight, across many tool calls, since they last spoke), your final message is their first look at any of it. Write it as a re-grounding, not a continuation of your working thread: the outcome first, then the one or two things you need from them, each explained as if new. The vocabulary you built up while working is yours, not theirs; leave it behind unless you re-introduce it.

When you write the summary at the end, drop the working shorthand. Write complete sentences. Spell out terms. Don't use arrow chains, hyphen-stacked compounds, or labels you made up earlier. When you mention files, commits, flags, or other identifiers, give each one its own plain-language clause. Open with the outcome: one sentence on what happened or what you found. Then the supporting detail. If you have to choose between short and clear, choose clear.
```

## S13. send-to-user ツール（Create a send-to-user tool）

turn を終えずに逐語でユーザーへ届ける client 側ツール定義。tool input は要約されない。

```json
{
  "name": "send_to_user",
  "description": "Display a message directly to the user. Use this for progress updates, partial results, or content the user must see exactly as written before the task finishes.",
  "input_schema": {
    "type": "object",
    "properties": {
      "message": {
        "type": "string",
        "description": "The content to display to the user."
      }
    },
    "required": ["message"]
  }
}
```

定義だけでは滅多に呼ばれない。system prompt に呼び出しを促す指示をペアで入れる。

```text
Between tool calls, when you have content the user must read verbatim (a partial deliverable, a direct answer to their question), call the send_to_user tool with that content. Use send_to_user only for user-facing content, not for narration or reasoning.
```

narration や内部推論を send_to_user に流さない（非ユーザー向け内容での乱用はツールの目的を損なう）。ルーチン進捗の narration だけの agent なら、モデル自身の要約で通常は足りる。

## S14. 検証の scaffolding（Recommended scaffolding changes）

長時間タスクでの自己検証の明示。別 context の fresh な verifier subagent は self-critique を上回る傾向。

```text
Establish a method for checking your own work at an interval of [X] as you build. Run this every [X interval], verifying your work with subagents against the specification.
```
