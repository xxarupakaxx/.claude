# ログインと `.codex`・`.claude` のGit運用

## なぜログインを何度も求めたのか

通常のCodexやClaudeをTerminalから使うだけなら、毎回ログインする必要はありません。すでにログイン済みの環境で、普段どおり実行できます。

今回ログインを繰り返したのは、比較評価用に新しい実行環境（ROOT）を作るたび、認証情報やセッションを旧環境からコピーしない方針を取ったためです。認証情報・セッション・DBを持ち込まず、source、設定、runtimeを固定した新環境で本人の公式ログインをやり直す必要がありました。この扱いは、`harness-benchmark.md` の認証・固定環境・新ROOTに関する節に沿ったもので、製品の通常要件ではありません。

source・設定・runtimeが変わらない、レビュー済みのv22環境を一度認証できれば、その環境でCodexとClaudeの接続テストを行い、その後にhost比較216件へ進めます。native比較72件は実行能力がまだ不明で、改善効果と採用可否も比較が終わるまで未確認です。認証の有効期限切れ、失効、ログアウトなどで認証が無効になった場合は再認証が必要ですが、変更のたびに一律で再ログインする運用ではありません。

したがって、先にローカルの修正と確認をすべて終え、固定した同じ環境で一度だけ両方を公式ログインする、という順序にできます。変更のたびにROOTを作り直したり、ログインを繰り返したりする運用ではありません。

## Terminalでの通常利用

普段の作業は、通常のTerminalからCodexまたはClaudeを起動すれば足ります。比較評価の認証入口は、通常利用のログインとは用途が異なり、固定した評価環境に本人の契約アカウントを接続するための一回限りの入口です。

Gitの認証は、CodexやClaudeのサブスクリプション認証とは別です。GitHubへpull・pushするには、GitHubアカウント（確認済みのprincipalは`xxarupakaxx`）の認証が必要です。

## Home側のpull・確認・push

作業前に、未コミットの個人変更と今回の所有対象を確認します。未コミット変更があるだけでpullを止める必要はありません。所有対象と重なる変更、分岐、統合時の衝突がある場合は、変更を保全してpullを止めます。無関係な既存変更を残したまま安全なfast-forwardができる場合は、そのまま進めます。

1. 状態を確認する。

   ```sh
   git -C "$HOME/.codex" status --short
   git -C "$HOME/.claude" status --short
   ```

2. 所有対象との重なり・分岐・衝突がなく、安全に直線更新できることを確認してpullする。

   ```sh
   git -C "$HOME/.codex" pull --ff-only
   git -C "$HOME/.claude" pull --ff-only
   ```

   `--ff-only` は、競合や分岐があると停止します。自動stash、全ファイルのadd、強制更新は行いません。

3. 変更を確認する。今回のHome側の主な変更は、Codexの比較環境で内蔵Skillの自動生成を抑制する設定と、それに対応するハーネス・文書です。`.claude`側に変更がある場合は、既存の個人変更と今回の変更を分けて確認します。

4. 今回のガイドだけをcommitする場合は、他のstaged変更がないことを確認し、あれば先に分離する。対象ファイルを明示して、次のように確認・commitする。

   ```sh
   git -C "$HOME/.codex" add -- context/harness-terminal-and-git.md
   git -C "$HOME/.codex" diff --cached --check
   git -C "$HOME/.codex" commit -m "docs: TerminalとGitの運用手順を追加"
   ```

   `.claude`側も同じ対象ファイルを管理している場合は、同じ3段階を`.claude`で行います。既存のstaged変更を混ぜず、今回のガイド以外を一括addしません。

5. 既存のupstreamへpushする。

   ```sh
   git -C "$HOME/.codex" push
   git -C "$HOME/.claude" push
   ```

6. push先と到達を確認する。

   ```sh
   git -C "$HOME/.codex" rev-parse HEAD
   git -C "$HOME/.codex" ls-remote origin refs/heads/main
   git -C "$HOME/.claude" rev-parse HEAD
   git -C "$HOME/.claude" ls-remote origin refs/heads/main
   ```

Home側の基準は元のHomeリポジトリです。Vault側の`.codex`・`.claude-global`は、旧submoduleを再初期化・更新する対象ではありません。Vaultには必要な文書ミラーだけを同期します。submoduleのinit・updateや、毎朝の自動更新をこの手順から追加しません。

このガイド自体をcommitする場合も、対象ファイルを明示してからcommit・pushします。pushできない場合は、認証、upstream、分岐、未コミット変更を確認し、force pushで解決しません。

参照: [比較手順](/Users/yoshiki/.codex/context/harness-benchmark.md)。Home側とVault側のガイドから同じHome側の手順を参照するため、Vault内の旧表示手順や旧submoduleの文書を参照しません。
