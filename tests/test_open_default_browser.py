from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "open-default-browser.py"
SPEC = importlib.util.spec_from_file_location("open_default_browser", SCRIPT)
assert SPEC and SPEC.loader
browser = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(browser)


class OpenDefaultBrowserTest(unittest.TestCase):
    def test_macos_resolves_https_handler_and_opens_file_with_that_app(self) -> None:
        probe = subprocess.CompletedProcess([], 0, stdout="/Applications/Arc.app\n")
        with (
            mock.patch.object(browser.sys, "platform", "darwin"),
            mock.patch.object(browser.subprocess, "run", side_effect=[probe, probe]) as run,
            mock.patch.object(Path, "resolve", return_value=Path("/tmp/dashboard.html")),
        ):
            self.assertTrue(browser.open_default_browser("/tmp/dashboard.html"))

        self.assertEqual(
            run.call_args_list[0].args[0][:3],
            ["/usr/bin/osascript", "-l", "JavaScript"],
        )
        self.assertEqual(
            run.call_args_list[1],
            mock.call(
                [
                    "/usr/bin/open",
                    "-a",
                    "/Applications/Arc.app",
                    "file:///tmp/dashboard.html",
                ],
                check=True,
            ),
        )

    def test_non_macos_uses_platform_default_browser(self) -> None:
        with (
            mock.patch.object(browser.sys, "platform", "linux"),
            mock.patch.object(browser.webbrowser, "open", return_value=True) as opener,
        ):
            self.assertTrue(browser.open_default_browser("https://example.com/dashboard"))
        opener.assert_called_once_with("https://example.com/dashboard")

    def test_missing_local_file_fails_before_browser_launch(self) -> None:
        with self.assertRaises(FileNotFoundError):
            browser.normalize_target("/tmp/definitely-missing-dashboard.html")


if __name__ == "__main__":
    unittest.main()
