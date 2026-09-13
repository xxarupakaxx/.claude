---
name: exploring-codebase
description: 関心事に必要な範囲だけ、コードベースの構造・データフロー・依存関係を調査する。新規リポジトリの理解、変更前の影響範囲確認、アーキテクチャ把握に使う。
---

# コードベース探索

理解することが目的のread-only調査であり、レビューや修正は行わない。まずユーザーの関心事と判断に必要な未知を一つに絞り、必要な観点だけを調べる。

## 入力と深さ

- 対象path（未指定ならrepository root）
- 関心事・keyword（未指定なら入口と主要なflow）
- 深さ `quick` / `medium` / `thorough`（既定は`medium`）

入口と境界を次の順で確認する。README、CONTRIBUTING、spec、ADR、domain glossary、manifest/lockfile/CI、public API・route・schema、core type・state・persistence・外部連携、必要なtest・fixture・history。全ファイルを最初から読み込まず、`rg`やGlobで候補を絞る。設定や自動化では設定ファイルだけでなく、commands/contextなどの正典も確認する。

## 観点の選択

ローカル調査で未確認点を絞った後、独立調査の利益がコストを上回る場合だけ、`../../context/agent-team-routing.md` のDelegation Gateに従って必要な担当を委譲する。人数や並列数は固定しない。Claude Code では `Agent(subagent_type: ...)` で `architecture-explorer`、`data-flow-tracer`、`dependency-mapper`、`learnings-researcher` を利用可能な場合に使う。

- **Architecture**: module、境界、責務、layer。
- **Data flow**: 入力から出力、状態、外部副作用まで。
- **Dependencies**: import、package、runtime・設定依存。
- **Past learnings**: `MEMORY_DIR`に`memories/`や`solutions/`がある場合だけ、関連する過去知見を検索する。

委譲時は対象の絶対path、関心事、深さ、返す形式（事実、根拠path:line、未確認点。変更禁止）だけを渡す。利用可能な担当がなければ親sessionで調べるか、未実施と報告する。複数sessionの状態共有が必要な場合だけ`team-run`のTeam Journalを使う。

## 出力

```markdown
# コードベース探索結果

## サマリー
<確認できた全体像を1〜3行>

## 調べた観点
### Architecture / Data Flow / Dependencies / Past Learnings
<実際に調べた観点だけ。各事実にpath:lineまたはsymbolの根拠>

## 注目ポイント
- <依頼の判断に影響する発見>

## 未確認・追加調査
- <残るunknownと、解消に必要な証拠>
```

未調査の章を推測で埋めない。一般論よりschema、resolver、設定、実際のcall siteを優先し、想定と実装の差は事実として記録する。

メモリディレクトリがプロジェクト規則で定義され、記録が必要なtaskなら統合結果を`05_log.md`へ追記する。通常の一回限りの探索では不要なartifactや全体計画を作らない。
