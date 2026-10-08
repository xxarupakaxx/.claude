#!/bin/bash
# sui-memory-hook.sh
# SessionStart / Stop: sui-memory のフックを起動する。
#   sui-memory-hook.sh hook_session_start | hook_stop
#
# 仮想環境の Python があればそれで実行し、なければ uv で実行する。
# uv を先に試して失敗時に切り替える形にはしない（uv の失敗が隠れるため）。
# どちらも使えないときは、原因を1行で出して終了コード 1 で終わる。
# pyproject.toml の依存を変えたときは、uv sync --project ~/.claude/sui-memory が要る。
set -u

MODULE="${1:?usage: sui-memory-hook.sh <hook_session_start|hook_stop>}"
PROJECT="$HOME/.claude/sui-memory"
PYTHON="$PROJECT/.venv/bin/python"

if [ -x "$PYTHON" ]; then
  exec "$PYTHON" -m "sui_memory.$MODULE"
fi
if command -v uv >/dev/null 2>&1; then
  exec uv run --project "$PROJECT" python -m "sui_memory.$MODULE"
fi
echo "[sui-memory] ~/.claude/sui-memory/.venv がなく、uv も見つからない。uv を入れて uv sync --project ~/.claude/sui-memory を実行する。" >&2
exit 1
