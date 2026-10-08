"""Use the shared Codex implementation without duplicating its behavior."""

import os
import sys
from pathlib import Path

runner = Path.home() / ".codex" / "scripts" / "lint-hook-wiring.py"
if not runner.is_file():
    if "--hook" in sys.argv:
        # セッション開始のフックでは、共有実装がなくてもセッションを止めない。
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        print("[hook-wiring] 共有実装 ~/.codex/scripts/lint-hook-wiring.py がないので検査していない")
        sys.exit(0)
    sys.exit("lint-hook-wiring: shared ~/.codex/scripts/lint-hook-wiring.py is missing")
os.execv(sys.executable, [sys.executable, str(runner), *sys.argv[1:]])
