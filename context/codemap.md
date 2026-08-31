# Codemap preflight

Codemapは、コード変更へ着手する前に読むtask単位の根拠付き地図である。workspaceのコードを検証対象とし、taskの調査範囲と証跡としてtask memory directoryへ保存する。Roadmapと同じTask Workspaceに表示するが、source freshnessはCodemap lockで独立検証する。

## 正本と生成物

`${MEMORY_DIR}/memory/YYMMDD_<task_name>/` に次の3 fileを置く。workspace rootやgit管理対象には置かない。

- `codemap.json`: AIが読む正本。scope、lane、node、edge、evidenceを保持する。
- `codemap.lock`: source/map fingerprintと展開済みsource manifestを保持するcommit marker。

二点は `scripts/generate-codemap.py refresh` だけで更新する。個別手編集しない。JSONをatomic replaceし、lockを最後に置く。途中失敗後はold lockとnew outputが一致せず、次のcheckが失敗する。人向け表示は`roadmap.html`の計画本文にあるCode Mapが担い、別の`codemap.html`は生成しない。

authoring sourceは同じtask memory directoryの `codemap.source.json` とする。これは生成二点に含めず、lockへbytes fingerprintを記録する。source定義を変えたままrefreshしなければstaleである。

## 着手前preflight

コードを変更するtaskでは、最初の編集前に次を順番に行う。

1. 対象fileのGit/workspace rootと現在taskのmemory directoryを確定し、task memory directoryの `codemap.lock` と `codemap.json` を探す。
2. `codemap.json`と`codemap.lock`があれば次を実行する。

   ```bash
   python3 ~/.claude/scripts/generate-codemap.py check \
     --root <workspace-root> \
     --artifact-dir <task-memory-directory>
   ```

3. freshなら `codemap.json` を読み、対象nodeのincoming caller、outgoing impact、`guards` / `tests` relation、各edgeのevidenceを確認する。
4. 次のどれかなら、通常のコード編集を始める前に調査をmap更新へ限定し、`codemap.source.json` を補完してrefreshする。
   - 生成二点またはauthoring sourceがない。
   - checkがmissing / mismatch / staleを返す。
   - 対象nodeがない。
   - caller、impact、guarding testの質問にmapが答えない。
   - evidenceのpath/lineが現在のsourceと対応しない。
5. refresh後にcheckを再実行し、freshになってから実装へ進む。
6. code変更後はscope内のnode/edge/evidenceを更新してrefreshし、もう一度freshを確認する。

地図を作るためのread-only調査は許可する。missing/stale/insufficientな状態でproduction codeを編集してはならない。Markdown、画像、議事録などコードを変更しないtaskはpreflight対象外である。

## CLI

```bash
# codemap.source.jsonを検証し、mapとlockを同期生成
python3 ~/.claude/scripts/generate-codemap.py refresh \
  --root <workspace-root> \
  --artifact-dir <task-memory-directory> \
  --input <task-memory-directory>/codemap.source.json

# map、lock、authoring source、現在sourceを再照合
python3 ~/.claude/scripts/generate-codemap.py check \
  --root <workspace-root> \
  --artifact-dir <task-memory-directory>
```

exit code 0だけをfreshとする。check失敗をwarningへ格下げしない。

`--artifact-dir` はworkspace root配下の論理pathを指定する。worktreeの`.local/memory`がメインworktreeへsymlinkされる構成は許可し、検証対象のrepo-relative pathは引き続き`--root`から解決する。task memory directory外のsource specや、workspace外を直接指定するartifact pathは拒否する。

## Schema v1

`codemap.source.json` は次を必須とする。

- `schemaVersion: 1`
- `title`
- `scope.include`: 1件以上のrepo-relative glob
- `scope.exclude`: repo-relative globのlist
- `lanes[]`: unique `id`、`title`、任意の`order`
- `nodes[]`: unique `id`、`title`、`kind`、既知の`lane`、任意の`path` / `summary`
- `edges[]`: unique `id`、既知nodeの`from` / `to`、`relation`、`status`、`evidence`

scopeはlexicographicに展開する。literal file patternは変更・削除、directory/glob patternは追加・変更・削除を検出する。refresh時に0 fileへ展開されるpatternは拒否する。Codemap生成物と生成中のtemporary fileはscopeにmatchしても常に除外する。

## Evidenceとunknown

edge statusは次の2値だけである。

- `verified`: 1件以上のevidenceが必要。evidenceはworkspace内に存在するrepo-relative `path`、positive `line`、その行に実在する非空`contains`を必須とし、任意で短い`note`を持つ。行移動や内容変更で`contains`が一致しなければrefresh/checkを失敗させる。
- `unknown`: 空でない`reason`が必要。根拠未取得、動的dispatch、外部host依存など、現在のrepositoryから確証できない関係に使う。

AIは「ありそう」という理由でverified edgeを作らない。推測した線を消すのではなく、問いとして残す価値がある場合だけunknown edgeとして明示する。unknownを作業完了の証拠として扱わない。

## UI契約

Codemap UIは`roadmap.html`の計画本文に埋め込まれた`kind: codemap` adapterを使う。Roadmap snapshotは表示用にCodemap payloadを含むが、freshnessの正本は`codemap.lock`である。図と根拠の一覧を最初から表示し、実装説明の近くで読めるようにする。表示のためのdrawerやtab操作を要求しない。

- laneとnodeの関係をSVGで示し、狭い画面では読める配置へ組み替える。
- incoming/outgoingの関係は図とテキスト一覧から確認できる。任意の選択操作だけに根拠を隠さない。
- verified evidenceを `path:line` で表示する。
- unknownは破線と `UNKNOWN — reason` の両方で表示する。
- relationがないnodeへartifact CTAを補作しない。
- SVGにtitle/descを付ける。本文と根拠はkeyboardでたどれ、狭い画面で文字を極端に縮めない。

## Roadmapとの統合境界

- `roadmap.html`: 計画、変更前後、実装内容、検証、Code Mapを初期表示する人向け入口。
- `roadmap-snapshot.json`: live表示用にRoadmapと検証済みCodemap payloadを保持する。
- `codemap.json` / `codemap.lock`: caller、impact、test、dependency、evidenceとsource freshnessの機械判定。

Task Workspaceへの表示統合はpreflightの統合ではない。task logの更新でCodemapをfresh扱わず、code/source変更をRoadmapの時刻freshnessで代用しない。Roadmap generatorは既存Codemap checkerがfreshと判定したpayloadだけを埋め込む。
