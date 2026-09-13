---
name: prompt-engineering
description: エージェント用のコマンド、hook、skill、sub-agent prompt、LLM用テンプレートを作成・改善するときに使う。目的に必要な context、制約、構造化出力、検証を設計する。
---

# Prompt & Context Engineering

プロンプトを単独で長くするのではなく、モデルがまだ持っていない情報だけを、目的・制約・入力・出力・検証に分けて設計する。利用者の依頼に必要な範囲だけを対象にし、既存の指示や workflow と重複させない。

## 設計手順

1. 目的、利用者、入力、許可された tool、成功条件を明記する。
2. 実行時に必要な dynamic context（日時、query、検索結果、状態）だけを選ぶ。
3. 必須制約、失敗時の扱い、structured output（schema、JSON、必要な XML）を定める。
4. 必要な場合だけ few-shot、条件分岐、tool orchestration、memory の扱いを加える。
5. 正常系だけでなく、欠損・境界・敵対的な入力で期待出力と停止条件を確認する。

context window は system prompt、会話履歴、tool 定義と共有する。高性能な Claude Code に一般論を教え込まず、未取得の根拠や対象固有の例だけを追加する。

## Claude 4.x を対象にする場合

- 旧モデル向けの `CRITICAL: MUST` などの強い文言を、必要な制約を保った通常の直接指示へ置き換える。
- Claude 4.6 で assistant turn の prefill が使えない環境では、structured output、XML、直接指示で代替する。
- effort parameter または一つの方針を選ぶ指示で、不要な overthinking を抑える。
- 明示された範囲の最小変更を指示し、依存しない tool は並列、依存する tool は逐次にする。

モデルや API の現行仕様を前提にする場合は、公式ドキュメントを確認し、未確認の数値や効果を断定しない。

## 参照先（必要時だけ）

- 手法の選択（few-shot、schema、段階的開示など）：[references/core-techniques.md](references/core-techniques.md)
- agent の委任、自由度、状態管理：[references/agent-prompting.md](references/agent-prompting.md)
- `CLAUDE.md`、skill、hook の構造：[references/claude-code-patterns.md](references/claude-code-patterns.md)

参照先を丸ごと読む必要はない。目的に該当する section だけを読む。
