---
name: config-mirror-sync
description: "`~/.codex`・`~/.claude`の変更をObsidianボルトのMarkdownミラーとgit submoduleの指し先へ同期する。Obsidianの作業ツリーには触れず、一時worktreeでコミットする。『vaultに同期』『obsidianに反映』などの明示依頼、またはhome側を更新した直後に使う。PJ文書整合や一時コピーには使わない。"
---

# Config Mirror Sync — Obsidianボルトへの反映

`~/.codex`・`~/.claude`は正本としてホームディレクトリに残したまま、実行環境で確定したObsidianボルト側の2種類の参照経路を最新化する。固定の旧パスを前提にせず、対象Vault rootの実在とGit repositoryであることを先に確認する。

- **Markdown抜粋ミラー**（`_shared-ai/mirrors/`）: `~/.claude/CLAUDE.md`と、`commands/*.md`、`prompts/*.md`、`context/**/*.md`、`rules/**/*.md`、`skills/*/SKILL.md`だけを人間が読める形でコピーする。Codex用のroot `CLAUDE.md`はruntime入口を複製せず、`~/.claude/published/CLAUDE.md`を正本とする薄いgenerated pointerとして同期する。同期定義は`_shared-ai/sync-manifest.toml`。
- **git submoduleの指し先**（vault直下の`.codex`・`.claude-global`）: 親repoが記録するgitlinkだけを進める。Obsidianで開く作業ツリーではサブモジュールを初期化しないので、設定ファイルやスクリプトの実体はhome側とGitHubのrepoで参照する。

## 前提: Obsidianの作業ツリーではサブモジュールを初期化しない

obsidian-gitの自動バックアップは`git add -A`を実行し、サブモジュールの作業ツリーにあるHEADをそのまま指し先として記録する。pullは`git fetch`と`git merge`で行うので、サブモジュールの作業ツリーは追従しない。そのため、作業ツリーが指し先とずれた端末は、バックアップのたびに指し先を書き換える。Vaultの`.github/workflows/submodule-pointer-guard.yml`は、`vault backup:`コミットによるgitlinkの変更を直前の正当値へ戻す。この往復が1日100件前後起きていた（2026-10-08に確認。経緯はVault内の`Inbox/automation/submodule-pointer-guard.md`）。

初期化されていないサブモジュールには`git add -A`が触れない。そこで、Obsidianで開く作業ツリー（以下「Obsidian側」）では`git submodule deinit`しておく。このSkillはObsidian側を読むだけにし、ミラーの適用とgitlinkの書き換えはすべて一時worktreeで行う。

Obsidian側では次を実行しない。`clone --recurse-submodules`が設定する`submodule.active = .`があると、deinit済みのサブモジュールもactiveと判定される。この状態では、引数なしの`git submodule update`でも初期化し直す（2026-10-08にfixtureで確認）。

- `git submodule update`（`--init`・`--remote`・`--merge`や引数の有無を問わない）、`git submodule init`
- `--recurse-submodules`付きの`clone`・`pull`・`checkout`
- `git add -A`、`git add .codex .claude-global`、Obsidian側にある`sync-ai-dotfiles.py`の`--apply`

次の2つは試験で効かないと確認した。`.gitmodules`の`ignore = all`は、Git 2.54未満では`git add -A`を止めず、表示から隠すだけである。`submodule.recurse true`は`git merge`に効かない。

### Obsidianで開く作業ツリーの一覧

gitlinkを進めてよいのは、次の全端末でdeinitを確認できたときだけである。端末が増えたら行を足し、確認したら状態と日付を書き換える。

- `yoshiki.morii.001`のMac（`/Users/yoshiki.morii.001/ghq/github.com/xxarupakaxx/obsidian-vault`）: 2026-10-08にdeinit済み。
- 個人のMac（`/Users/yoshiki/Notes/Vault`）: 未確認。毎朝07:50の自動化`vault-dotfiles-submodule-update`は、promptで`git submodule update --init --remote --merge`を実行する。deinitしても翌朝に初期化し直すので、このpromptを本手順へ直すまでは未確認として扱う。promptはSKILL.mdをVaultの`.codex`内から読むので、deinit後は`~/.codex`側を読むように直す。

## 対象の決定

明示があればそれに従う。なければ直前にhome側で編集・pushした方（`.codex`または`.claude`）を対象にする。両方編集していれば両方を対象にする。

## 手順

以下の`VAULT`は、Obsidian側のrootとして実行環境で実在確認したpathに置き換える。例はCodexを対象にした場合で、Claudeが対象なら`~/.codex`を`~/.claude`に、`.codex`を`.claude-global`に置き換える。両方が対象なら、手順1の確認と手順4の書き換えを両方に行う。

### 1. 現況確認

```bash
VAULT="<実在確認済みのObsidian Vault root>"
git -C "$VAULT" fetch origin main
git -C "$VAULT" submodule status                       # 全行の先頭が「-」（未初期化）であること
git -C "$VAULT" ls-tree origin/main .codex .claude-global
git -C "$VAULT" status --short -- _shared-ai/mirrors
git -C "$VAULT" log --oneline origin/main..HEAD -- _shared-ai/mirrors
git -C ~/.codex fetch origin
git -C ~/.codex rev-parse HEAD
git -C ~/.codex merge-base --is-ancestor HEAD origin/main && echo pushed
git -C ~/.codex status --short -- '*.md'
```

結果に応じて次のように扱う。

- Obsidian側の`submodule status`に、先頭が空白・`+`・`U`の行があれば、その端末は初期化済みで往復の発生源になる。gitlinkの書き換え（手順4）は行わず、`git -C "$VAULT" submodule deinit <path>`を本人へ提案する。サブモジュール内に未コミットの変更があるとdeinitは失敗するので、`--force`で消さずに本人の判断を待つ。ミラーの同期（手順3）は続けてよい。
- Obsidian側の`_shared-ai/mirrors`に未コミットの変更や未pushのコミットがあれば、全体を止める。Vaultは`*.md merge=union`を指定しているので、同じミラーが両側で変わると、マージで行が混ざったファイルができる。
- home側のHEADが`origin/main`に含まれていなければ（`pushed`が出なければ）、gitlinkをそのHEADへ進めない。home側のpushを済ませてからやり直す。
- home側の対象Markdownに未コミットの変更があると、ミラーはHEADと違う内容になる。home側でコミットとpushを済ませてから同期する。

実行開始時に`run_id`、対象（codex / claude）、manifestのscope、home側のHEAD、origin/mainのgitlink、Obsidian側のsubmodule状態とミラーのdirty状態を記録する。各sourceについて対象window、cursor（home HEADまたは現在のpointer）、`success`、`normal-empty`（manifestを最後まで確認し更新対象がない正常な空結果）、`failed`、`unread`を分ける。`success`または確認済みの`normal-empty`だけcursorを進め、失敗・不完全取得・未読では進めず、未処理sourceと再開条件を残す。同じwindowの再実行はsource pathと既存mirror・pointerを照合し、同じ同期や通知を二重に作らない。

origin/mainのgitlinkがhome側のHEADと一致していなければ、その対象は前進の候補になる。設定、run起動、dry-run、実際の保存、commit/push、完了通知は別状態であり、設定が存在することや起動成功だけで同期完了とは扱わない。

### 2. gitlinkを進めてよいかの確認

gitlinkを書き換える前に、上の一覧の全端末でdeinitを確認する。一覧の全端末が確認日つきでdeinit済みなら、聞かずに手順3へ進む。

- 一覧に未確認の端末があれば、本人に「その端末のVaultでサブモジュールをdeinitしたか。初期化し直す自動化を止めたか」を聞く。この会話で本人が両方を確認済みと答えた場合だけ、gitlinkを進めてよい。回答を受けたら、先に一覧の該当行を確認日つきに書き換え、home側の両runtimeのSKILL.mdへ同じ変更を入れてcommit・pushする。そのあと手順1からやり直し、更新後のHEADを指すようにする。
- 本人に聞けない実行（scheduledや無人のworkflow）では、確認を省略しない。gitlinkは進めずにミラーだけを同期し、「前進を保留」とその理由を報告する。
- 確認が取れない間も、ミラーだけの同期は往復を起こさないので続けてよい。

### 3. 一時worktreeを作り、ミラーを適用する

```bash
WT="$(mktemp -d "${TMPDIR:-/tmp}/vault-mirror-sync.XXXXXX")/wt"
git -C "$VAULT" worktree add --detach "$WT" origin/main
git -C "$WT" submodule status                          # 全行の先頭が「-」であること
```

worktreeはVaultのフォルダの外に作る。Vaultの中に作ると、Obsidianが索引に含める。`worktree add`はサブモジュールを初期化しない。`submodule.recurse true`があっても同じである（2026-10-08にfixtureで確認）。worktreeでもサブモジュールのコマンドは実行しない。

`sync-ai-dotfiles.py`は、スクリプト自身の位置からVaultのrootを決める。必ず`$WT`のスクリプトを実行する。Obsidian側のスクリプトを実行すると、Obsidian側へ書き込む。

スクリプトは`tomllib`を使うのでPython 3.11以上が要る。`python3 --version`が3.11未満なら、`python3.12`などを`PY`に入れる。引数なしのdry-runは選択した全ファイルを「COPY」と表示するので、差分の確認には`--check`を使う。

```bash
PY=python3                                             # 3.11以上の解釈系
"$PY" -I -B "$WT/_shared-ai/scripts/sync-ai-dotfiles.py" --check   # exit 0ならミラーの差分なし
"$PY" -I -B "$WT/_shared-ai/scripts/sync-ai-dotfiles.py" --apply
"$PY" -I -B "$WT/_shared-ai/scripts/sync-ai-dotfiles.py" --check   # apply後はexit 0
git -C "$WT" status --short -- _shared-ai/mirrors
git -C "$WT" diff --check -- _shared-ai/mirrors
rg -i --count-matches --no-heading "access_token|api_key|credential|password|refresh_token|secret" "$WT/_shared-ai/mirrors"
git -C "$WT" add -- _shared-ai/mirrors
```

スクリプトはファイルを削除しないので、`git status --short`には`M`と`??`だけが出る。`D`やリネーム、意図しないpathがあれば止める。

secretパターンの走査結果は、pathと件数だけを確認する。キーワードのヒット数0件は安全性の証明にならないため、実値や認証情報の混入があれば失敗として止め、manifestの除外規則と対象差分も別に確認する。行本文を出力する検索やログへの転記は行わない。

stageは`_shared-ai/mirrors`のように対象pathを指定して行い、`git add -A`や`git add .`は使わない。

### 4. gitlinkを書き換える

手順1と手順2で進めてよいと確認できた対象だけを書き換える。

```bash
SHA=$(git -C ~/.codex rev-parse HEAD)                  # 手順1でorigin/mainに含まれると確認したHEAD
git -C "$WT" update-index --cacheinfo "160000,$SHA,.codex"
git -C "$WT" ls-files -s .codex                        # 160000 <SHA> であること
git -C "$WT" diff --cached --submodule=short -- .codex
```

`git add .codex`は使わない。worktreeのサブモジュールは未初期化なので、`add`ではgitlinkが変わらない。

### 5. コミットとpush

```bash
git -C "$WT" diff --cached --name-status               # _shared-ai/mirrors/ と対象のgitlinkだけ
git -C "$WT" diff --cached --check
git -C "$WT" commit -m "chore: AI dotfilesミラーとsubmoduleの指し先を最新化"
git -C "$WT" push origin HEAD:main
```

コミットメッセージを`vault backup:`で始めない。ガードはこの接頭辞のコミットだけを巻き戻しの対象にするので、`chore:`で記録した値が正当値になる。gitlinkを書き換えなかった回は`chore: AI dotfilesミラーを最新化`にする。ステージに何もなければコミットせず、no-opとして手順6へ進む。

pushが非fast-forwardで拒否されたら（obsidian-gitが先にpushした場合など）、rebaseもmergeもしない。手順6でworktreeを片づけ、`git -C "$VAULT" fetch origin main`のあと手順3からやり直す。ミラーの適用とgitlinkの書き換えは何度実行しても同じ結果になるので、作り直して実行し直せば足りる。2回やり直しても拒否されたら止めて報告する。

pushはhome側の許可を別remoteへ自動的に広げず、対象remote・操作・差分が現在の依頼または既存の承認範囲に含まれるかを確認する。含まれる場合は一律に再確認せず、含まれない場合だけユーザーに確認して停止する（Vaultはhome側とは別のGitHub remoteの独立repoのため）。

### 6. 一時worktreeを片づける

```bash
git -C "$VAULT" worktree remove "$WT"
git -C "$VAULT" worktree prune
rmdir "$(dirname "$WT")"
```

途中で止めた場合も片づける。未コミットの差分が残って`remove`が失敗したら、`git -C "$WT" status --short`で差分が今回適用したミラーとgitlinkだけであることを確かめてから`--force`を付ける。初期化済みのサブモジュールがあると`remove`は失敗する。その場合は手順3の確認漏れとして報告する。

### 7. 反映を確かめる

```bash
git -C "$VAULT" fetch origin main
git -C "$VAULT" ls-tree origin/main .codex .claude-global          # 進めた対象が$SHA
git -C "$VAULT" submodule status                                   # Obsidian側は全行の先頭が「-」のまま
git -C "$VAULT" log --format='%h %an %ad %s' <pushしたコミット>..origin/main -- .codex .claude-global
```

最後のコマンドは空であることを期待する。`vault backup:`のコミットや、ガードの`chore: vault backupによるsubmoduleポインタ巻き戻りを自動修復`が現れたら、往復が再発している。gitlinkを進め直さず、そのコミットのauthorと日時を添えて本人へ報告する。obsidian-gitは定期的にpullとバックアップを繰り返すので、push直後に空でも、次の実行の手順1でもう一度確かめる。

## 良い例

home側（例: `~/.codex`）で編集・commit・push → Obsidian側のdeinitと全端末の確認 → 一時worktreeでミラーの適用とgitlinkの書き換えを1つの`chore:`コミットにしてpush → worktreeを片づける → origin/mainのgitlinkと後続のコミットを確かめる、という順序。`95f4cbcf chore: submoduleポインタを個人のMacの作業ツリーの値へ進める`（2026-10-08）は、gitlinkだけを`chore:`コミットで進めた例である。

## 悪い例

- Obsidian側で`git submodule update`を実行する（旧手順。`--init`がなくても初期化し直し、往復が再発する）
- 一時worktreeで`git add -A`や`git add .`を使う（対象外のpathを拾う）
- pushの拒否をrebaseやmergeで解決する（`*.md merge=union`でミラーの行が混ざる）
- 一覧に未確認の端末が残るのに、gitlinkを最新へ進める
- `_shared-ai/mirrors/`配下を直接編集する（次回同期で上書きされる。編集は必ずhome側の原本に対して行う）

## 完了条件

- [ ] Obsidian側: `submodule status`の全行の先頭が「-」のままで、このSkillによる作業ツリーとindexの変更がない
- [ ] Markdown抜粋ミラー: apply後の`--check`がexit 0。`git diff --check`と`git diff --cached --check`がexit 0。対象差分に削除・リネーム・意図しないpath・実値の機密情報がない
- [ ] gitlink: 進めた対象は、origin/mainのgitlinkがhome側のHEAD（origin/mainに含まれる）と一致する。進めなかった対象は、理由（未確認の端末、未pushなど）を報告に書く
- [ ] Vaultのorigin/mainに上記を記録した`chore:`コミットがあり、その後に`vault backup:`やガードによるgitlinkの変更がない。pushは対象remote・操作・差分が現在の依頼または既存の承認範囲に含まれる場合に続行し、含まれない場合だけユーザー確認を得る
- [ ] 一時worktreeを片づけ、`git -C "$VAULT" worktree list`に残っていない

## 除外されるもの

`_shared-ai/sync-manifest.toml`の`blocked_path_parts`・`blocked_file_names`・`blocked_name_fragments`で定義済み（セッションログ・キャッシュ・worktree・認証情報等）。一覧はマニフェスト側を正とし、このファイルには複製しない。
