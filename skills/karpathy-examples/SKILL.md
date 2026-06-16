---
name: karpathy-examples
description: "Karpathy 4原則違反のTypeScript Before/After実例集。code-simplicity-reviewer・brainstorming等から明示参照される教材データ。自動起動しない参照専用スキル。「karpathy的観点で見せて」「4原則違反の実例を見せて」など明示依頼があった場合のみ起動。"
---

# Karpathy Examples（参照専用）

[Andrej Karpathy のLLMコーディング指摘](https://x.com/karpathy/status/2015883857489522876) に基づく4原則の違反パターンと、TypeScript版のBefore/After実例集。

## 用途

このスキルは**自動起動しない**。以下の場合のみ参照される:

- `code-simplicity-reviewer` がレビュー時にアンチパターン例を提示する場合
- `brainstorming` でユーザーの要求がKarpathy原則違反になりそうな兆候を検出した場合
- ユーザーが明示的に「Karpathy的観点で実例を見せて」と依頼した場合

## 構成

- **EXAMPLES.md**: 4原則×TypeScript Before/After実例（4例厳選）+ アンチパターン早見表

## 関連

主原則本体は `~/.claude/CLAUDE.md` の「行動規範（4原則）」セクション（SSoT）。

参照規約:
- `rules/common-patterns.md`（Speculative Features アンチパターン）
- `rules/common-coding-style.md`（Style Drift 防止）
- `agents/code-simplicity-reviewer.md`（Karpathy式アンチパターン検出）
