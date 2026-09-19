# analyzing-session-tokens

Claude CodeとCodexの現在セッションについて、トークン消費の内訳、原因の根拠と推測、改善の実行、効果確認を行うスキル。

## 呼び出し

- Codex: `$analyzing-session-tokens このセッションの消費原因を調べて改善して`
- Claude Code: `/analyzing-session-tokens このセッションの消費原因を調べて改善して`
- 調査だけなら「調査のみ」と付ける。

既定でセッション内の進め方だけを改善する。共通設定・既存skill・hook等は具体的なdiffへの承認後に変更する。

## 配置

編集元は `~/.codex/skills/analyzing-session-tokens/`。同じbundleを `~/.claude/skills/analyzing-session-tokens/` に配布する。両方とも他方に依存せず、Python 3だけで動く。

Codexのuser skill探索用に `~/.agents/skills/analyzing-session-tokens` からCodex側bundleへのsymlinkを置く。既存の同名entryがある場合は上書きせず確認する。共通設定ファイルの変更は不要。更新が一覧に出なければアプリを再起動する。[Codexの探索仕様](https://developers.openai.com/codex/skills)

Claudeはpersonal skillsから読み込む。IDはスキルの置換変数から渡す。通常のshell環境に同名環境変数があることは前提にしない。[Claudeのスキル仕様](https://code.claude.com/docs/en/skills)

## 集計だけを実行する

```sh
python3 ~/.codex/skills/analyzing-session-tokens/scripts/analyze.py --provider codex
```

両providerとも `--session-id` と `--log` で対象を明示できる。親子合計は `--include-children`。比較は新規の `--save-snapshot` と、後の `--baseline` を使う。全オプションは `--help`、計算方法は [計測仕様](references/measurement.md) を参照。

## 検証と更新

```sh
python3 ~/.codex/scripts/quiet-run.py -- python3 -m unittest discover -s ~/.codex/skills/analyzing-session-tokens/tests -v
```

テストは人工ログだけを使う。更新後は両配置の `SKILL.md`、`README.md`、`references/*.md`、`scripts/analyze.py`、`tests/test_analyze.py` のbyte一致を確認する。`__pycache__` は配布・commitしない。実ログやsnapshotはfixtureへコピーしない。

collectorは記録上の数値を集計する。請求額の確定、取得できない利用枠の推計、ログから分からないファイル別token割合の算出は行わない。改善の効果は、同等作業での比較と品質の確認後に判断する。
