#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: validate-tha-deck.sh /absolute/path/to/deck.pptx /absolute/path/to/output-dir" >&2
  exit 2
fi

for command_name in unzip xmllint soffice pdftotext pdftoppm python3 grep; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Missing required command: $command_name" >&2
    exit 2
  fi
done

if ! python3 -c "import PIL" >/dev/null 2>&1; then
  echo "Missing required Python package: Pillow" >&2
  echo "Install it with: python3 -m pip install Pillow" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PPTX_PATH="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
OUTPUT_ROOT="$(mkdir -p "$2" && cd "$2" && pwd)"

if [[ ! -f "$PPTX_PATH" || "${PPTX_PATH##*.}" != "pptx" ]]; then
  echo "Not a PPTX file: $PPTX_PATH" >&2
  exit 2
fi

RUN_DIR="$(mktemp -d "$OUTPUT_ROOT/validation.XXXXXX")"
RENDER_DIR="$RUN_DIR/rendered"
mkdir -p "$RENDER_DIR"

unzip -t "$PPTX_PATH" > "$RUN_DIR/zip-integrity.txt"

SLIDE_CX="$(unzip -p "$PPTX_PATH" ppt/presentation.xml |
  xmllint --xpath 'string(//*[local-name()="sldSz"]/@cx)' - 2>/dev/null)"
SLIDE_CY="$(unzip -p "$PPTX_PATH" ppt/presentation.xml |
  xmllint --xpath 'string(//*[local-name()="sldSz"]/@cy)' - 2>/dev/null)"
SLIDE_SIZE="$SLIDE_CX,$SLIDE_CY"
if [[ "$SLIDE_SIZE" != "12192000,6858000" ]]; then
  echo "Unexpected slide size: $SLIDE_SIZE" >&2
  exit 1
fi

if [[ -f /opt/homebrew/etc/fonts/fonts.conf ]]; then
  export FONTCONFIG_FILE=/opt/homebrew/etc/fonts/fonts.conf
  export FONTCONFIG_PATH=/opt/homebrew/etc/fonts
fi

soffice --headless --convert-to pdf --outdir "$RUN_DIR" "$PPTX_PATH" >/dev/null
PDF_PATH="$RUN_DIR/$(basename "${PPTX_PATH%.pptx}").pdf"
if [[ ! -s "$PDF_PATH" ]]; then
  echo "LibreOffice did not create a PDF" >&2
  exit 1
fi

python3 "$SCRIPT_DIR/extract-pptx-text.py" \
  "$PPTX_PATH" "$RUN_DIR/extracted-text.txt" "$RUN_DIR/speaker-notes.txt"
pdftotext -layout "$PDF_PATH" "$RUN_DIR/pdf-text.txt"
if grep -Eiq 'xxx+|lorem|ipsum|TODO|\[insert|placeholder|this.*(page|slide).*layout' \
  "$RUN_DIR/extracted-text.txt"; then
  grep -Ei 'xxx+|lorem|ipsum|TODO|\[insert|placeholder|this.*(page|slide).*layout' \
    "$RUN_DIR/extracted-text.txt" > "$RUN_DIR/placeholders.txt"
  echo "Placeholder text found; see $RUN_DIR/placeholders.txt" >&2
  exit 1
fi

pdftoppm -png -r 150 "$PDF_PATH" "$RENDER_DIR/slide" >/dev/null 2>&1
python3 "$SCRIPT_DIR/create-overview.py" "$RENDER_DIR" "$RUN_DIR/overview.png" >/dev/null

SLIDE_COUNT="$(find "$RENDER_DIR" -type f -name 'slide-*.png' | wc -l | tr -d ' ')"
if [[ "$SLIDE_COUNT" -lt 1 ]]; then
  echo "No rendered slides found" >&2
  exit 1
fi

{
  echo "PPTX: $PPTX_PATH"
  echo "Run directory: $RUN_DIR"
  echo "Slide size: $SLIDE_SIZE"
  echo "Rendered slides: $SLIDE_COUNT"
  echo "ZIP integrity: PASS"
  echo "LibreOffice PDF conversion: PASS"
  echo "Placeholder scan: PASS"
  echo "Manual review required: overview.png and rendered/slide-*.png"
} > "$RUN_DIR/validation-summary.txt"

cat "$RUN_DIR/validation-summary.txt"
