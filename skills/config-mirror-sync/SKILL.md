---
name: config-mirror-sync
description: "`~/.codex`・`~/.claude`の変更をObsidianボルト（`~/Notes/Vault`）へ反映する。Markdown抜粋ミラー（`_shared-ai/mirrors/`）とgit submodule（`.codex`/`.claude-global`）の両方が対象。「vaultに同期して」「obsidianに反映して」「ミラー更新して」等の依頼時、またはhome側でコミット・pushした直後にvault側も最新化したい場合に使用。**除外**: PJ内ドキュメント整合はproject-sync、単一ファイルの一時的なコピーは対象外。"
---

# Config Mirror Sync — Obsidianボルトへの反映

`~/.codex`・`~/.claude`は正本としてホームディレクトリに残したまま、Obsidianボルト（`~/Notes/Vault`）側の2種類の参照経路を最新化する。

- **Markdown抜粋ミラー**（`_shared-ai/mirrors/`）: `~/.claude/CLAUDE.md`と、`commands/*.md`、`prompts/*.md`、`context/**/*.md`、`rules/**/*.md`、`skills/*/SKILL.md`だけを人間が読める形でコピーする。Codex用のroot `AGENTS.md`は互換ルールを持つ専用ミラーなので単純コピーしない。同期定義は`_shared-ai/sync-manifest.toml`。
- **git submodule**（vault直下の`.codex`・`.claude-global`）: 設定ファイルやスクリプトも含めた実体を独立repoとして参照する。

## 対象の決定

明示があればそれに従う。なければ直前にhome側で編集・pushした方（`.codex`または`.claude`）を対象にする。両方編集していれば両方を対象にする。

## 手順

### 1. 現況確認

```bash
VAULT=~/Notes/Vault
git -C ~/.codex rev-parse HEAD   # 対象が.codexの場合。.claudeなら ~/.claude で確認
git -C "$VAULT" submodule status
git -C "$VAULT" status --short
```

実行開始時に `run_id`、対象（codex / claude）、manifestのscope、home側のHEAD、submodule pointer、Vaultのdirty状態を記録する。開始時に対象Vaultまたはsubmoduleに既存のdirty差分があれば、対象を分離できるまでapply・stage・commitを行わない。各sourceについて対象window、cursor（home HEADまたは現在のpointer）、`success`、`normal-empty`（manifestを最後まで確認し更新対象がない正常な空結果）、`failed`、`unread` を分ける。`success` または確認済みの `normal-empty` だけcursorを進め、失敗・不完全取得・未読では進めず、未処理sourceと再開条件を残す。同じwindowの再実行はsource pathと既存mirror・pointerを照合し、同じ同期や通知を二重に作らない。

対象submoduleのcommitがhome側の現HEADと一致していなければ、その対象は同期が必要。設定、run起動、dry-run、実際の保存、commit/push、完了通知は別状態であり、設定が存在することや起動成功だけで同期完了とは扱わない。

### 2. Markdown抜粋ミラーの同期

```bash
cd "$VAULT"
python3 _shared-ai/scripts/sync-ai-dotfiles.py          # dry-run
```

差分が意図どおり（削除なし・新規/更新のみ）であることを確認してから適用する。

```bash
python3 _shared-ai/scripts/sync-ai-dotfiles.py --apply
git diff --check
git diff --cached --check
git status --short
rg -i --count-matches --no-heading "access_token|api_key|credential|password|refresh_token|secret" _shared-ai/mirrors
```

`git diff --check` と `git diff --cached --check` がexit 0、`git status --short` に削除・リネーム・意図しないpathがなく、secretパターンの走査結果（pathと件数だけ）を確認する。キーワードのヒット数0件は安全性の証明にならないため、実値や認証情報の混入があれば失敗として止め、manifestの除外規則と対象差分も別に確認する。行本文を出力する検索やログへの転記は行わない。apply後の未staged差分も必ず確認し、dry-runや起動だけを保存成功と報告しない。

### 3. git submoduleの更新

```bash
git -C "$VAULT" submodule update --remote --merge .codex          # 対象が.codexの場合
git -C "$VAULT" submodule update --remote --merge .claude-global  # 対象が.claudeの場合
```

更新後、対象runtimeごとにpointerを照合する。Codex対象は `git -C "$VAULT/.codex" rev-parse HEAD` と `git -C ~/.codex rev-parse HEAD`、Claude対象は `git -C "$VAULT/.claude-global" rev-parse HEAD` と `git -C ~/.claude rev-parse HEAD` を比較する。両方を対象にした場合は両方が一致して初めて同期成功とし、片方の一致をもう片方の完了とは扱わない。

### 4. vault側のポインタ更新をコミット

submoduleを更新しても、親のobsidian-vaultリポジトリは自動では気づかない。ポインタ更新は別途コミットする。

```bash
cd "$VAULT"
git add .codex .claude-global _shared-ai/mirrors   # 実際に更新した対象のみ add
git commit -m "chore: AI dotfilesミラーとsubmoduleポインタを最新化"
```

pushはhome側の許可を別remoteへ自動的に広げず、対象remote・操作・差分が現在の依頼または既存の承認範囲に含まれるかを確認する。含まれる場合は一律に再確認せず、含まれない場合だけユーザーに確認して停止する（Vaultはhome側とは別のGitHub remoteの独立repoのため）。

## 良い例

home側（例: `~/.codex`）で編集・commit・push → vault側で本手順を実行しミラーとsubmoduleポインタを最新化 → vault側でポインタ更新をcommit、という順序（`8f97c4a feat: AI dotfilesをObsidianで参照できるようにする`で確立済み）。

## 悪い例

- `_shared-ai/mirrors/`配下を直接編集する（次回同期で上書きされる。編集は必ずhome側の原本に対して行う）
- vault側の`.codex`submodule内で直接commit/pushし、親のobsidian-vaultリポジトリ側のポインタ更新コミットを忘れる（親はsubmoduleの参照commitをポインタとして持つだけなので、`git -C "$VAULT" add .codex && git commit`が別途必要）

## 完了条件

- [ ] Markdown抜粋ミラー: `git diff --check` と `git diff --cached --check` がexit 0、`git status --short` と対象差分を確認し、削除・リネーム・意図しないpath・実値の機密情報がない。未staged差分を含む対象差分を確認済み
- [ ] git submodule: 対象のsubmodule HEADがhome側の現HEADと一致
- [ ] vaultリポジトリに上記変更を記録したコミットが存在する。pushは対象remote・操作・差分が現在の依頼または既存の承認範囲に含まれる場合に続行し、含まれない場合だけユーザー確認を得る

## 除外されるもの

`_shared-ai/sync-manifest.toml`の`blocked_path_parts`・`blocked_file_names`・`blocked_name_fragments`で定義済み（セッションログ・キャッシュ・worktree・認証情報等）。一覧はマニフェスト側を正とし、このファイルには複製しない。
