#!/usr/bin/env python3
"""Run the shared Codex decision-evidence check without a second implementation."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> int:
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
    runner = codex_home / "scripts" / "decision-preflight.py"
    if not runner.is_file():
        print(f"Shared decision-preflight is missing: {runner}", file=sys.stderr)
        return 2
    try:
        os.execv(sys.executable, [sys.executable, str(runner), *sys.argv[1:]])
    except OSError as exc:
        print(f"Unable to start shared decision-preflight: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
