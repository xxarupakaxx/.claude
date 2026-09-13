#!/usr/bin/env python3

import re
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError as error:
    raise SystemExit("Pillow is required: python3 -m pip install Pillow") from error


def slide_number(path: Path) -> int:
    match = re.search(r"(\d+)$", path.stem)
    return int(match.group(1)) if match else 0


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: create-overview.py <render-dir> <overview.png>")

    render_dir = Path(sys.argv[1]).expanduser().resolve()
    output = Path(sys.argv[2]).expanduser().resolve()
    slides = sorted(render_dir.glob("slide-*.png"), key=slide_number)
    if not slides:
        raise SystemExit(f"No slide PNGs found in {render_dir}")

    columns = 3
    thumb_w = 480
    label_h = 28
    with Image.open(slides[0]) as first:
        thumb_h = round(thumb_w * first.height / first.width)
    rows = (len(slides) + columns - 1) // columns
    canvas = Image.new("RGB", (columns * thumb_w, rows * (thumb_h + label_h)), "white")
    draw = ImageDraw.Draw(canvas)

    for index, slide_path in enumerate(slides):
        with Image.open(slide_path) as image:
            thumb = image.convert("RGB")
            thumb.thumbnail((thumb_w, thumb_h))
            x = (index % columns) * thumb_w
            y = (index // columns) * (thumb_h + label_h)
            canvas.paste(thumb, (x, y))
            draw.text((x + 8, y + thumb_h + 6), slide_path.name, fill="#46546E")

    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)
    print(f"Created {output}")


if __name__ == "__main__":
    main()
