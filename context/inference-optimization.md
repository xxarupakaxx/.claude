# 推論量とキャッシュを使い分ける

軽い作業では推論量を選び、同じ資料の重複読込を減らす。重要な判断と最終レビューには既存の品質設定を使う。固定した架空3課題で時間と検出品質を測定した。実際の請求額の差と実務での品質同等性は未確認である。

## Codexの起動

| 作業 | 新規セッションの起動 | 推論量 |
|---|---|---|
| 短い整形・既知の局所作業 | `codex -p fast` | medium |
| 低リスクで検証方法が明確な通常実装 | `codex -p balanced` | high |
| 設計判断・セキュリティ・承認・最終レビュー | `codex` | 既存のmax |

profileはモデルや権限を変えず、`model_reasoning_effort`だけを上書きする。専門roleの設定と既存のroutingは維持する。軽量profileで始めた作業に重要判断が加わったら、要件・根拠・未完了gateを通常設定の新しいセッションへ引き継ぐ。

Codex CLI 0.163.0の`--help`で、`-p`が`$CODEX_HOME/<name>.config.toml`をbase configへ重ねる方式であることを確認した。`fast.config.toml`と`balanced.config.toml`はこの方式を使う。手元のモデルmetadataでもmediumとhighの対応を確認した。将来のCLI更新時は受理される方式を再確認する。

## Claude Codeの起動

```sh
~/.claude/bin/claude-optimized
```

この起動fileは、通常の`claude`に`--exclude-dynamic-system-prompt-sections`を付けて実行する。cwd・環境情報・memory path・git statusをsystem promptから最初のuser messageへ移す、CLIのネイティブ機能である。共通prefixの再利用を助ける構成だが、今回の測定範囲とcache率は[実測比較](inference-benchmark-2026-10-23.md)を参照する。費用の確定比較は保留している。

Claude Code 2.1.251の`--help`で対応を確認した。`--system-prompt`を指定するとこのflagは無視される。モデル・effort・hook・Skill・権限は既存設定を使い、追加の引数と終了値はそのまま渡す。軽い作業だけ新規起動時に`--effort medium`を選べる。重要判断・専門レビューは既存のroutingを使う。

通常の`claude`や既存セッションへ、この起動fileのflagが自動で適用されるわけではない。

## 各作業で減らすもの

1. 共通指示とtool定義を固定し、可変情報は作業入力へ分ける。CLIが管理するcache breakpointを設定できるとは扱わない。
2. 必要な参照先を先に示し、独立した検索・読込をまとめる。保存済み原典や同じ版の資料は再取得しない。
3. 再レビューでは対象版と依存を照合し、変更も影響もない担当だけ省く。変更fileの全行、必要な依存、安全性、未完了gateは確認する。
4. 完了処理の後に目的のない追加turnを作らない。timeout・provider失敗・cancelを区別する。

詳細は[model routing](../rules/model-routing.md)と[review方針](../rules/code-review-philosophy.md)を参照する。

## 効果の確認と戻し方

同程度の作業で、完了までの時間、モデル呼出し数、入力・出力・cache読込token、再作業、テスト失敗、重要な見落としを比較する。cache hit率だけで採否を決めず、使える実測値だけを記録する。API換算額とサブスクリプションの請求額は区別する。品質が落ちる作業では軽量profileを使わない。

2026-10-23に架空3課題を各条件2回ずつ比較した。平均時間はCodex fastで55.2%、balancedで56.0%、Claude最適化起動で12.5%短縮し、全条件で6件中6件が固定採点に合格した。[測定範囲・費用の参考値・全対の結果](inference-benchmark-2026-10-23.md)を参照する。Codexは同じ更新版CLIとモデルで推論量を比較し、profile値をCLIにも明示した。設定受理と性能の実測は区別し、現在進行中のセッションの推論量やprefixが変わったとは扱わない。

軽量profileを使わず`codex`を起動し、Claudeでは通常の`claude`を起動すれば、それぞれ既存の起動方法に戻る。運用規則の追加を戻す場合は、今回追加した節だけを戻す。

## 根拠と確認できた範囲

- [Cloudflareの記事](https://blog.cloudflare.com/obsessive-inference-optimization/)：共有prefix、読込と呼出しの削減、モデル・effortと検出品質の比較。保存済み原典`cloudflare-optimization.md`の1608–1622、1628–1686、1694–1738行。
- [Anthropicのprompt caching仕様](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)：安定した内容を先頭へ置くことと、tool定義・effort変更による無効化。保存済み原典`anthropic-prompt-cache.md`の489–491、623–637行。
- 原典の保存先：`~/.local/share/imozuru/topics/cloudflare-inference-optimization-20261022/sources/`。取得済みの同じ原典を再利用する。
- ローカル仕様の確認：Codex CLI 0.163.0は2026-10-23、Claude Code 2.1.251は2026-10-22のhelp。

記事の68%削減はCloudflareのレビュー処理での結果であり、この環境の削減予測には使わない。記事の「Codex standards reviewer」は同社の処理名であり、OpenAI Codex CLIの設定例として転用しない。

その後、専用runnerの内部エラーを修復し、Codex公式仕様とClaude公式仕様の追加取得、保存、引用9件の照合、report生成が成功した。今回の実測では、取得済みの原典とローカルの記録を再利用した。
