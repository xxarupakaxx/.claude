"""Use the shared Codex implementation without duplicating its behavior."""

import os
import sys
from pathlib import Path

runner = Path.home() / ".codex" / "scripts" / "quiet-run.py"
if not runner.is_file():
    sys.exit("quiet-run: shared ~/.codex/scripts/quiet-run.py is missing")
os.execv(sys.executable, [sys.executable, str(runner), *sys.argv[1:]])
