#!/usr/bin/env python3

import os
import sys
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: rezip-pptx.py /absolute/path/to/deck.pptx")

    source = Path(sys.argv[1]).expanduser().resolve()
    if source.suffix.lower() != ".pptx" or not source.is_file():
        raise SystemExit(f"Not a PPTX file: {source}")

    with tempfile.NamedTemporaryFile(
        prefix=f".{source.stem}.", suffix=".pptx", dir=source.parent, delete=False
    ) as handle:
        temporary = Path(handle.name)

    try:
        with ZipFile(source, "r") as incoming, ZipFile(
            temporary, "w", compression=ZIP_DEFLATED, compresslevel=9
        ) as outgoing:
            for item in incoming.infolist():
                if item.is_dir():
                    continue
                outgoing.writestr(item, incoming.read(item.filename))
        os.replace(temporary, source)
    finally:
        if temporary.exists():
            temporary.unlink()

    print(f"Recompressed {source}")


if __name__ == "__main__":
    main()
