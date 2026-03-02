#!/bin/bash
# worktree-knowledge-link.sh
# Worktree内の知見ディレクトリをメインworktreeの.local/にシンボリックリンク
# 共有: memories/, solutions/, issues/, memory/
# ローカル維持: HANDOVER.md, plans/

INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd // ""')

if [ -z "$CWD" ] || [ "$CWD" = "null" ]; then
  exit 0
fi

# Git repoか確認
TOPLEVEL=$(git -C "$CWD" rev-parse --show-toplevel 2>/dev/null) || exit 0

# Worktreeかどうか確認（.gitがファイルならworktree）
if [ ! -f "$TOPLEVEL/.git" ]; then
  # メインworktreeなのでスキップ
  exit 0
fi

# メインworktreeのパスを取得
MAIN_WORKTREE=$(git -C "$CWD" worktree list --porcelain | head -1 | sed 's/worktree //')
MAIN_LOCAL="$MAIN_WORKTREE/.local"
WT_LOCAL="$TOPLEVEL/.local"

# メインの.localとサブディレクトリを確保
mkdir -p "$MAIN_LOCAL/memories" "$MAIN_LOCAL/solutions" "$MAIN_LOCAL/issues" "$MAIN_LOCAL/memory"

# ワークツリーの.localディレクトリを確保
mkdir -p "$WT_LOCAL"

# 共有すべきディレクトリをシンボリックリンク
LINKED=0
for dir in memories solutions issues memory; do
  target="$WT_LOCAL/$dir"
  source="$MAIN_LOCAL/$dir"

  if [ -L "$target" ]; then
    # 既にシンボリックリンク → スキップ
    continue
  fi

  if [ -d "$target" ]; then
    # 既存データをメインにマージしてからリンク
    cp -rn "$target"/* "$source/" 2>/dev/null || true
    rm -rf "$target"
  fi

  ln -s "$source" "$target"
  LINKED=$((LINKED + 1))
done

if [ "$LINKED" -gt 0 ]; then
  echo "Worktree knowledge linked: $LINKED dirs -> $MAIN_LOCAL/"
fi

exit 0
