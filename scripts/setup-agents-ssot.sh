#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/setup-agents-ssot.sh [--import-existing]

Make ~/.agents/skills point at this repository's skills/ directory.

Options:
  --import-existing  Import the current ~/.agents/skills contents into ./skills
                     before replacing it with a symlink.

The previous ~/.agents/skills directory or symlink is preserved as:
  ~/.agents/skills.backup-YYYYMMDD-HHMMSS
USAGE
}

import_existing=0
for arg in "$@"; do
  case "$arg" in
    --import-existing)
      import_existing=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      usage >&2
      exit 2
      ;;
  esac
done

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd "${script_dir}/.." && pwd -P)"
ssot="${repo_root}/skills"
agents_dir="${HOME}/.agents"
target="${agents_dir}/skills"

if [ ! -d "$ssot" ]; then
  echo "SSoT skills directory not found: $ssot" >&2
  exit 1
fi

mkdir -p "$agents_dir"

if [ -L "$target" ] && [ "$(cd "$target" && pwd -P)" = "$(cd "$ssot" && pwd -P)" ]; then
  echo "Already configured: $target -> $ssot"
  exit 0
fi

backup="${agents_dir}/skills.backup-$(date +%Y%m%d-%H%M%S)"

if [ -e "$target" ] || [ -L "$target" ]; then
  if [ "$import_existing" -eq 1 ]; then
    if ! command -v rsync >/dev/null 2>&1; then
      echo "rsync is required for --import-existing" >&2
      exit 1
    fi
    echo "Importing existing skills from $target into $ssot"
    rsync -a "${target}/" "${ssot}/"
  fi

  echo "Preserving existing $target as $backup"
  mv "$target" "$backup"
fi

ln -s "$ssot" "$target"
echo "Configured: $target -> $ssot"
