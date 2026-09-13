#!/usr/bin/env python3

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile


def number(path: str) -> int:
    match = re.search(r"(\d+)\.xml$", path)
    return int(match.group(1)) if match else 0


def text_from_xml(data: bytes) -> list[str]:
    root = ET.fromstring(data)
    values = []
    for element in root.iter():
        if element.tag.endswith("}t") and element.text:
            values.append(element.text)
    return values


def write_sections(archive: ZipFile, paths: list[str], output: Path, label: str) -> None:
    with output.open("w", encoding="utf-8") as handle:
        for index, item in enumerate(sorted(paths, key=number), start=1):
            handle.write(f"## {label} {index}\n")
            for value in text_from_xml(archive.read(item)):
                handle.write(value + "\n")
            handle.write("\n")


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit(
            "Usage: extract-pptx-text.py deck.pptx extracted-text.txt speaker-notes.txt"
        )

    source = Path(sys.argv[1]).expanduser().resolve()
    slide_output = Path(sys.argv[2]).expanduser().resolve()
    notes_output = Path(sys.argv[3]).expanduser().resolve()

    with ZipFile(source, "r") as archive:
        names = archive.namelist()
        slides = [
            name for name in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
        ]
        notes = [
            name
            for name in names
            if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", name)
        ]
        write_sections(archive, slides, slide_output, "Slide")
        write_sections(archive, notes, notes_output, "Notes")


if __name__ == "__main__":
    main()
