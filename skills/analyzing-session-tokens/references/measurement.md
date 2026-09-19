# 計測仕様と制約

## 数えるもの

`scripts/analyze.py` はPython標準ライブラリだけを使う。ネットワーク、モデル呼び出し、設定変更は行わない。JSONの数値と識別子から集計し、会話本文・tool引数・tool結果本文・認証情報を出力しない。ログ内の文字列は実行しない。

| 出力 | 意味 |
|---|---|
| `tokens` | 今回読み取れたAPI使用量の合計。全請求額ではない |
| `sources` | 親と発見した各子の内訳、使用した形式、警告 |
| `by_model` | Codexはturn_context、Claudeはmessageのモデル別使用量。不明はunknown。サーバー側の未記録rerouteは分からない |
| `latest_main_request` | 最後に観測した親の使用量。legacy形式では累計差分 |
| `largest_requests` | 観測したリクエストの上位5件。sourceとログ行番号が根拠 |
| `activity` | ツール回数、結果のbyte数、同一結果、明示されたエラー、圧縮イベント |
| `findings` | 機械的な特徴からの原因候補。確定診断ではない |
| `measurement_status` | `recorded` は警告なし、`qualified` は欠損などの条件付き |

`recorded` でも取得範囲はローカルで観測できた記録だけ。保留中・保存されなかった要求、別端末、リンクできない子、アカウントの他タスクは含まれない。

## プロバイダごとの計算

Codex:

- `input_tokens` はキャッシュ読み取りを含む。
- `uncached_input_tokens = input_tokens - cached_input_tokens`。
- `cache_write_input_tokens` は記録がある場合だけ表示する。入力へ再加算しない。非キャッシュ入力はcache write分を含み得る。
- `reasoning_output_tokens` は出力の内訳。総量は入力＋出力で、推論を再加算しない。
- `token_usage_record` があれば同じthreadの `response_id` 単位で集計する。重複は最後の記録を選び、数値が変わっていれば警告する。
- 同じ履歴にある `token_count` は別途加算しない。thread累計とリクエスト合計の不一致は警告する。
- 旧形式しかない場合は `total_token_usage` の差分を使う。同じ累計は重複として除外する。累計低下はresetとして区切り、その境界の消費を推測して足さない。最初の累計が以前の履歴を含み得るため、旧形式は常に条件付きとする。

Claude Code:

- 総入力＝`input_tokens + cache_creation_input_tokens + cache_read_input_tokens`。
- `input_tokens` は非キャッシュ入力としても保持する。
- `output_tokens_details.thinking_tokens` は出力の内訳。欠けていれば不明。
- `(message.id, requestId)` が同じusage行を重複除去する。`requestId` がない場合はmessage IDだけを使い、警告する。message IDもなければそのusageを除外し、警告する。
- usage行の `sessionId` が欠けている場合も、対象への帰属を推測せず除外して警告する。
- 同じ識別子の数値が更新された場合は最後を採用し、警告する。message単位の最終値の保証が取れないため、無条件に正確とは扱わない。
- JSONLは内部形式であり、この識別規則はバージョン付きの経験則。公式の安定した請求schemaとは見なさない。

負の数、文字列、欠損は不明にする。合計に必要な値が一つでも不明なら該当合計も `null`。キャッシュや推論を含めて不明な内訳があれば、条件付きの計測として前後比較を止める。推論が出力を超えるなど、包含関係が崩れた記録にも警告を付ける。

## 親子・再開・分岐

Codexは `session_meta.id` で対象を照合する。子は `source.subagent.thread_spawn.parent_thread_id` をたどる。別threadに帰属するusageは除外し、分岐の継承分と新たな消費を二重計上しない。継承を区別できない旧形式は条件付きのまま示す。

Claudeは各行の `sessionId` を照合し、親transcriptと同名のdirectory内の `subagents/*.jsonl` を子として扱う。親子でsession IDを共有するため、sourceも重複除去キーに含める。別の配置・remote・agent teamの独立sessionは自動で混ぜない。子から実行する場合はそのtranscriptを明示する。

探索は対象IDを使い、同じIDの候補が複数あれば停止する。Codexの子でも同じIDの複数候補を合算しない。アーカイブは `--root` または `--log` で明示する。再開・分岐の解釈に疑いがある場合は親、継承、今回の実行を分け、正確な合算を保留する。

## 比較と保存

`--save-snapshot` は指定された新規ファイルだけをmode 0600で作成する。directoryの作成、既存ファイルやsymlinkの上書きはしない。Gitや外部同期の対象外に保存する。

保存内容はprovider、session ID、scope、時刻、計測状態、対象pathのハッシュと、識別子をハッシュ化したリクエスト別の数値。本文、tool名、生のpath、引数は保存しない。ハッシュは匿名化の保証ではないため、snapshotも個人の作業情報として扱う。

`--baseline` は同じsession・対象path・scope・schemaの記録を比較する。同じIDを共有するClaudeの親子も、対象pathで区別する。以前のリクエストが消えたり値が変わった場合、または両時点のいずれかに警告がある場合は停止する。新しいリクエストだけの使用量を返す。診断と通常作業が同時に進んだ区間は区別できない。

差分は「追加で消費した量」であり、削減した量ではない。削減効果には同等の作業のbaselineと品質の確認が別に必要。

## 容量と失敗

- 一回の入力は合計64 MiBまで、1行8 MiBまで。大きすぎる場合は停止し、scopeを狭める。黙って切り捨てない。
- 探索候補は10,000ファイル、集計対象は親子合計128ファイルまで。上限超過時は停止する。
- 各ファイルは開始時のbyte境界まで読む。最後の書きかけ行は除外して `incomplete_tail` を付ける。
- 不正行、usage欠損、形式の違いを警告する。ファイル未発見・ID不一致・比較不能は終了コード2。集計成功は0だが、警告の確認は必要。
- bodyのbyte数はJSON表現の大きさ。token数や請求費用へ換算しない。wrapper内のツール名は分解できない場合がある。Codexの一般的なtool失敗はエラーfieldがないと検出できない。

## 根拠

2026-09-20に公式資料とローカル記録を照合。ログ形式変更時はsynthetic fixtureと公式表示を再照合し、未知の形式を既存仕様に押し込めない。

- [Codex token表示の実装](https://github.com/openai/codex/blob/main/codex-rs/tui/src/token_usage.rs): キャッシュ・累計・直近量の区別。
- [Codex App Server](https://developers.openai.com/codex/app-server): thread単位の使用量通知。
- [Claude prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching): 通常入力、cache creation、cache readの包含関係。
- [Claude statusline](https://code.claude.com/docs/en/statusline): session ID、transcript、直近使用量。
- [Claude costs](https://code.claude.com/docs/en/costs): `/usage`、プランとAPI費用の違い、原因別の補助情報。
- [Claude sessions](https://code.claude.com/docs/en/sessions): transcriptとsessionの扱い。
