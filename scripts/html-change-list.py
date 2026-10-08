"""Use the shared Codex implementation without duplicating its behavior."""

import os
import sys
from pathlib import Path

runner = Path.home() / ".codex" / "scripts" / "html-change-list.py"
if not runner.is_file():
    sys.exit("html-change-list: shared ~/.codex/scripts/html-change-list.py is missing")
os.execv(sys.executable, [sys.executable, str(runner), *sys.argv[1:]])
