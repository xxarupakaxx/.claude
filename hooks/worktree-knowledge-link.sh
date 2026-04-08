#!/bin/bash
# worktree-knowledge-link.sh
# Worktree内の知見ディレクトリをメインworktreeの.local/にシンボリックリンク
# 共有: memories/, solutions/, issues/, memory/, memory.db
# ローカル維持: HANDOVER.md, plans/
#
# 対象:
#   1. リポジトリルートの .local/
#   2. PJ CLAUDE.md の MEMORY_DIR で指定されたサブディレクトリの .local/

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

# --- リンク処理を関数化 ---
link_local() {
  local wt_local="$1"
  local main_local="$2"
  local linked=0

  # メインの.localとサブディレクトリを確保
  mkdir -p "$main_local/memories" "$main_local/solutions" "$main_local/issues" "$main_local/memory"

  # ワークツリーの.localディレクトリを確保
  mkdir -p "$wt_local"

  # 共有すべきディレクトリをシンボリックリンク
  for dir in memories solutions issues memory; do
    local target="$wt_local/$dir"
    local source="$main_local/$dir"

    if [ -L "$target" ]; then
      continue
    fi

    if [ -d "$target" ]; then
      cp -rn "$target"/* "$source/" 2>/dev/null || true
      rm -rf "$target"
    fi

    ln -s "$source" "$target"
    linked=$((linked + 1))
  done

  # memory.db ファイルのシンボリックリンク（SQLiteメモリDB共有）
  local db_target="$wt_local/memory.db"
  local db_source="$main_local/memory.db"
  if [ ! -L "$db_target" ] && [ ! -f "$db_target" ]; then
    ln -s "$db_source" "$db_target"
    linked=$((linked + 1))
  elif [ -f "$db_target" ] && [ ! -L "$db_target" ]; then
    if [ ! -f "$db_source" ]; then
      cp "$db_target" "$db_source"
    fi
    rm -f "$db_target" "${db_target}-wal" "${db_target}-shm"
    ln -s "$db_source" "$db_target"
    linked=$((linked + 1))
  fi

  if [ "$linked" -gt 0 ]; then
    echo "Worktree knowledge linked: $linked items -> $main_local/"
  fi
}

# 1. リポジトリルートの .local/ をリンク
link_local "$TOPLEVEL/.local" "$MAIN_WORKTREE/.local"

# 2. PJ CLAUDE.md の MEMORY_DIR で指定されたサブディレクトリの .local/ をリンク
# CWD配下のCLAUDE.mdからMEMORY_DIR=を探す（最も近いCLAUDE.mdを優先）
find_memory_dirs() {
  local search_dir="$CWD"
  while [ "$search_dir" != "$TOPLEVEL" ] && [ "$search_dir" != "/" ]; do
    if [ -f "$search_dir/CLAUDE.md" ]; then
      local mem_dir
      mem_dir=$(grep -m1 '^MEMORY_DIR=' "$search_dir/CLAUDE.md" 2>/dev/null | sed 's/MEMORY_DIR=//' | tr -d ' ')
      if [ -n "$mem_dir" ] && [ "$mem_dir" != ".local/" ] && [ "$mem_dir" != ".local" ]; then
        # MEMORY_DIRが.local/以外の場合（相対パス → CWDのCLAUDE.md所在地からの相対）
        local pj_local="$search_dir/$mem_dir"
        local rel_path="${search_dir#$TOPLEVEL/}"
        local main_pj_local="$MAIN_WORKTREE/$rel_path/$mem_dir"
        link_local "$pj_local" "$main_pj_local"
      elif [ -n "$mem_dir" ]; then
        # MEMORY_DIR=.local/ の場合、search_dir/.local/ をリンク
        local pj_local="$search_dir/.local"
        local rel_path="${search_dir#$TOPLEVEL/}"
        local main_pj_local="$MAIN_WORKTREE/$rel_path/.local"
        if [ "$pj_local" != "$TOPLEVEL/.local" ]; then
          link_local "$pj_local" "$main_pj_local"
        fi
      fi
    fi
    search_dir=$(dirname "$search_dir")
  done
}

find_memory_dirs

exit 0
