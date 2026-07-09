# Deep Research Skill 日本語導入版

このディレクトリは、`199-biotechnologies/claude-deep-research-skill` を日本語入口つきで導入したものです。

上流の取得元は次の通りです。

- Repository: `https://github.com/199-biotechnologies/claude-deep-research-skill`
- Commit: `f2f2c0fa4e7617ca84c86b63f4bb40f77a746933`
- 取得日: `2026-07-09`
- Original README: `README.upstream.md`

## 何が日本語化されているか

- `SKILL.md`：日本語化済み。Codex と Claude の道具名の違いも追記しています。
- `README.md`：このファイル。導入状態と使い方を日本語で説明しています。
- `reference/`：上流の英語原典を同梱しています。
- `scripts/`、`schemas/`、`templates/`、`tests/`：上流の実行資産をそのまま保持しています。

長い参照文書まで全面翻訳すると、上流スクリプトや検証条件との対応が崩れやすくなります。
そのため、実行入口は日本語化し、詳細仕様は原典を参照する構成にしています。

## 使い方

次のような依頼で起動します。

```text
deep research: 2026年時点のAIエージェント評価基盤を出典つきで調べて
徹底調査: PostgreSQL と Supabase を今の自社スタック前提で比較して
出典つきで深い調査レポートを作って
```

既定は `standard` モードです。
短く探索する場合は `quick`、重要判断では `deep`、網羅調査では `ultradeep` と明示してください。

## 出力

通常は次のフォルダに成果物を保存します。

```text
~/Documents/[Topic]_Research_[YYYYMMDD]/
```

Vault 内にノートとして残す依頼では、Vault の `AGENTS.md` を優先し、既存の配置と frontmatter に合わせます。

## 任意の検索ツール

上流は `search-cli` を主検索ツールとして想定しています。
未導入でも、Codex では `web` 検索、Claude では WebSearch を使って実行できます。

`search-cli` を使う場合は、上流 README の手順に従ってください。

```bash
brew tap 199-biotechnologies/tap && brew install search-cli
search config set keys.brave YOUR_KEY
```

API キーは Vault に保存しないでください。

## 検証

レポートを生成したら、可能な範囲で次を実行します。

```bash
python scripts/validate_report.py --report [path]
python scripts/verify_citations.py --report [path]
python scripts/md_to_html.py [markdown_path]
```

検証に失敗した場合は、エラーを読んで具体箇所を修正し、再実行します。
3回試しても通らない場合は、残っている問題をユーザーへ報告します。

## 注意

このスキルは調査の品質を上げるための重い手順です。
単純な検索、短い質問、ローカルコードのデバッグには使いません。

医療、法律、金融、安全、採用など高リスク領域では、必ず最新の一次情報を確認し、出典と不確実性を明記します。
