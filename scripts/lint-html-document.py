"""Use the shared Codex implementation without duplicating its behavior."""

import os
import sys
from pathlib import Path

runner = Path.home() / ".codex" / "scripts" / "lint-html-document.py"
if not runner.is_file():
    sys.exit("lint-html-document: shared ~/.codex/scripts/lint-html-document.py is missing")
os.execv(sys.executable, [sys.executable, str(runner), *sys.argv[1:]])
