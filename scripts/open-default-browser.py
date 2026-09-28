#!/usr/bin/env python3
"""Open a URL or local file in the operating system's default web browser."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import webbrowser


DEFAULT_BROWSER_PROBE_URL = "https://example.com/"


def macos_default_browser_app() -> str:
    script = (
        'ObjC.import("AppKit");'
        f'const url=$.NSURL.URLWithString("{DEFAULT_BROWSER_PROBE_URL}");'
        "const app=$.NSWorkspace.sharedWorkspace.URLForApplicationToOpenURL(url);"
        'if (!app) throw new Error("default HTTPS browser not found");'
        "ObjC.unwrap(app.path);"
    )
    result = subprocess.run(
        ["/usr/bin/osascript", "-l", "JavaScript", "-e", script],
        check=True,
        capture_output=True,
        text=True,
    )
    app_path = result.stdout.strip()
    if not app_path:
        raise RuntimeError("default HTTPS browser returned an empty application path")
    return app_path


def normalize_target(target: str) -> str:
    if "://" in target:
        return target
    return Path(target).expanduser().resolve(strict=True).as_uri()


def open_default_browser(target: str) -> bool:
    normalized = normalize_target(target)
    if sys.platform == "darwin":
        app_path = macos_default_browser_app()
        subprocess.run(["/usr/bin/open", "-a", app_path, normalized], check=True)
        return True
    if os.name == "nt":
        os.startfile(normalized)  # type: ignore[attr-defined]
        return True
    return webbrowser.open(normalized)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Open a target in the OS default HTTPS browser."
    )
    parser.add_argument("target", help="URL or existing local file")
    args = parser.parse_args(argv)
    try:
        if not open_default_browser(args.target):
            raise RuntimeError("the platform browser opener rejected the target")
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"failed to open default browser: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
