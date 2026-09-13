#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
CONTRACT_PATH = SCRIPT_DIR / "html_artifact_contract.py"
SPEC = importlib.util.spec_from_file_location("html_artifact_contract", CONTRACT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load HTML artifact contract: {CONTRACT_PATH}")
contract = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = contract
SPEC.loader.exec_module(contract)


def main(argv: list[str] | None = None) -> int:
    return contract.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
