"""Use the shared Codex implementation without duplicating its behavior."""

import os
import sys
from pathlib import Path

runner = Path.home() / ".codex" / "scripts" / "session-metrics.py"
if not runner.is_file():
    sys.exit("session-metrics: shared ~/.codex/scripts/session-metrics.py is missing")
os.execv(sys.executable, [sys.executable, str(runner), *sys.argv[1:]])
