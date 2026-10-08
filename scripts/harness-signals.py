"""Use the shared Codex implementation without duplicating its behavior."""

import os
import sys
from pathlib import Path

runner = Path.home() / ".codex" / "scripts" / "harness-signals.py"
if not runner.is_file():
    sys.exit("harness-signals: shared ~/.codex/scripts/harness-signals.py is missing")
os.execv(sys.executable, [sys.executable, str(runner), *sys.argv[1:]])
