---
name: prompt-engineering
description: エージェント向けのコマンド、フック、スキル、サブエージェント向けプロンプト、その他LLMインタラクションを作成する際に使用。プロンプト最適化、LLM出力改善、本番用プロンプトテンプレート設計を含む。
---

# プロンプト & コンテキストエンジニアリング

LLMのパフォーマンス、信頼性、制御性を最大化するための技術。
2025年以降、単一プロンプトの最適化（Prompt Engineering）から、情報エコシステム全体の設計（Context Engineering）へパラダイムシフトが進行中。

## コンテキストエンジニアリングの原則

Prompt Engineeringはコンテキストウィンドウ「内」の最適化。Context Engineeringはウィンドウに「何を入れるか」の設計。

### 5つの構成要素

1. **システムプロンプト & 指示** — 安定した動作定義（ロール、制約、出力形式）
2. **動的コンテキスト** — 実行時に注入される情報（日時、ユーザークエリ、検索結果）
3. **構造化入出力** — スキーマ定義、XMLタグ（Claude固有）、JSON構造
4. **ツール統合** — 利用可能な能力とそのパラメータ定義
5. **メモリシステム** — 短期（会話履歴）+ 長期（キャッシュ、ベクトルストア、ファイルシステム）

### コンテキストウィンドウは公共財

プロンプト・コマンド・スキルは他のすべて（システムプロンプト、会話履歴、ツール定義等）とウィンドウを共有する。
**デフォルト前提**: Claudeはすでに非常に賢い。Claudeが「まだ持っていない」コンテキストのみを追加する。

## コアテクニック

1. **Few-Shot Learning** — 2-5個の入出力ペアで動作を教示
2. **Chain-of-Thought** — ステップバイステップ推論で精度30-50%向上
3. **Adaptive/Extended Thinking** — Claude 4.x: effortパラメータで思考深度を制御
4. **テンプレートシステム** — 変数・条件付きセクションの再利用可能構造
5. **XMLタグ構造化（Claude固有）** — Claude訓練データに含まれるXMLタグで曖昧さを排除。他LLMでは効果が異なる

詳細: `Read references/core-techniques.md`

## Claude 4.x固有の注意点

- **Overtrigger対策**: 以前のモデル向けの積極的指示（「CRITICAL: MUST use...」）は緩和する。通常の言語で十分
- **Prefill廃止**: Claude 4.6でassistant turnのprefillは非対応。structured outputs/XML/直接指示で代替
- **Overthinking制御**: effortパラメータまたは「1つのアプローチを選んでコミットせよ」で制御
- **過剰エンジニアリング抑止**: 明示的に「最小限の変更のみ」と指示
- **並列ツール実行**: 依存関係がなければ並列、依存があれば逐次。明示的指示で精度〜100%

## エージェントプロンプティング

Anthropic公式ベストプラクティスに基づく原則集。説得の7原則（権威・コミットメント・希少性・社会的証明・一体感・互恵性・好意）、自由度設計、subagent orchestration、multi-window workflow、state management。

詳細: `Read references/agent-prompting.md`

## Claude Code固有のパターン

CLAUDE.md設計、skills/hooks設計、サブエージェントプロンプトの実践パターン。

詳細: `Read references/claude-code-patterns.md`

## 段階的開示（設計原則）

1. **レベル1**: 直接的な指示
2. **レベル2**: 制約を追加
3. **レベル3**: 推論ステップを追加
4. **レベル4**: 例を追加

## 一般的な落とし穴

- **過剰エンジニアリング**: シンプルなものを試す前に複雑なプロンプトから始める
- **Overtrigger**: 以前のモデル向けの強い言語がClaude 4.xで過剰反応を招く
- **コンテキスト汚染**: 不要な情報でウィンドウを浪費
- **曖昧な指示**: 「何をしないか」ではなく「何をするか」で指示する
- **エッジケース無視**: 異常/境界入力でテストしない

## ソース

- [Anthropic公式: Prompting best practices (Claude 4.x)](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices)
- [Context Engineering Guide](https://www.promptingguide.ai/guides/context-engineering-guide)
- [Anthropic Cookbook](https://github.com/anthropics/anthropic-cookbook)
