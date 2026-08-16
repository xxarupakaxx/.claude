---
name: config-mirror-sync
description: "`~/.codex`・`~/.claude`の変更をObsidianボルト（`~/Documents/obsidian-vault`）へ反映する。Markdown抜粋ミラー（`_shared-ai/mirrors/`）とgit submodule（`.codex`/`.claude-global`）の両方が対象。「vaultに同期して」「obsidianに反映して」「ミラー更新して」等の依頼時、またはhome側でコミット・pushした直後にvault側も最新化したい場合に使用。**除外**: PJ内ドキュメント整合はproject-sync、単一ファイルの一時的なコピーは対象外。"
---

# Config Mirror Sync — Obsidianボルトへの反映

`~/.codex`・`~/.claude`は正本としてホームディレクトリに残したまま、Obsidianボルト（`~/Documents/obsidian-vault`）側の2種類の参照経路を最新化する。

- **Markdown抜粋ミラー**（`_shared-ai/mirrors/`）: `commands/*.md`・`prompts/*.md`・`context/**/*.md`・`rules/**/*.md`・`skills/*/SKILL.md`だけを人間が読める形でコピーする。同期定義は`_shared-ai/sync-manifest.toml`。
- **git submodule**（vault直下の`.codex`・`.claude-global`）: 設定ファイルやスクリプトも含めた実体を独立repoとして参照する。

## 対象の決定

明示があればそれに従う。なければ直前にhome側で編集・pushした方（`.codex`または`.claude`）を対象にする。両方編集していれば両方を対象にする。

## 手順

### 1. 現況確認

```bash
VAULT=~/Documents/obsidian-vault
git -C ~/.codex rev-parse HEAD   # 対象が.codexの場合。.claudeなら ~/.claude で確認
git -C "$VAULT" submodule status
```

対象submoduleのcommitがhome側の現HEADと一致していなければ、その対象は同期が必要。

### 2. Markdown抜粋ミラーの同期

```bash
cd "$VAULT"
python3 _shared-ai/scripts/sync-ai-dotfiles.py          # dry-run
```

差分が意図どおり（削除なし・新規/更新のみ）であることを確認してから適用する。

```bash
python3 _shared-ai/scripts/sync-ai-dotfiles.py --apply
git diff --cached --check
rg -i "access_token|api_key|credential|password|refresh_token|secret" _shared-ai/mirrors
```

`git diff --cached --check`がexit 0、`rg`のヒットが0件であることを確認する。

### 3. git submoduleの更新

```bash
git -C "$VAULT" submodule update --remote --merge .codex          # 対象が.codexの場合
git -C "$VAULT" submodule update --remote --merge .claude-global  # 対象が.claudeの場合
```

更新後、`git -C "$VAULT/.codex" rev-parse HEAD`がhome側の`git -C ~/.codex rev-parse HEAD`と一致することを確認する。

### 4. vault側のポインタ更新をコミット

submoduleを更新しても、親のobsidian-vaultリポジトリは自動では気づかない。ポインタ更新は別途コミットする。

```bash
cd "$VAULT"
git add .codex .claude-global _shared-ai/mirrors   # 実際に更新した対象のみ add
git commit -m "chore: AI dotfilesミラーとsubmoduleポインタを最新化"
```

pushはhome側の許可とは別に、その場でユーザーに確認してから実行する（vaultはhome側とは別のGitHub remoteの独立repoのため）。

## 良い例

home側（例: `~/.codex`）で編集・commit・push → vault側で本手順を実行しミラーとsubmoduleポインタを最新化 → vault側でポインタ更新をcommit、という順序（`8f97c4a feat: AI dotfilesをObsidianで参照できるようにする`で確立済み）。

## 悪い例

- `_shared-ai/mirrors/`配下を直接編集する（次回同期で上書きされる。編集は必ずhome側の原本に対して行う）
- vault側の`.codex`submodule内で直接commit/pushし、親のobsidian-vaultリポジトリ側のポインタ更新コミットを忘れる（親はsubmoduleの参照commitをポインタとして持つだけなので、`git -C "$VAULT" add .codex && git commit`が別途必要）

## 完了条件

- [ ] Markdown抜粋ミラー: `git diff --cached --check`がexit 0、secretパターンのrg走査がヒット0、削除が0件
- [ ] git submodule: 対象のsubmodule HEADがhome側の現HEADと一致
- [ ] vaultリポジトリに上記変更を記録したコミットが存在する（pushはユーザー確認後）

## 除外されるもの

`_shared-ai/sync-manifest.toml`の`blocked_path_parts`・`blocked_file_names`・`blocked_name_fragments`で定義済み（セッションログ・キャッシュ・worktree・認証情報等）。一覧はマニフェスト側を正とし、このファイルには複製しない。
