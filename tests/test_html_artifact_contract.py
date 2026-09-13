from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "html_artifact_contract.py"
SPEC = importlib.util.spec_from_file_location("html_artifact_contract", SCRIPT)
assert SPEC and SPEC.loader
contract = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = contract
SPEC.loader.exec_module(contract)


def valid_html(*, artifact_kind: str = "html-plan", extra_body: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="artifact-kind" content="{artifact_kind}">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; connect-src 'self'; base-uri 'none'; form-action 'none'">
  <title>Valid Artifact</title>
</head>
<body>
  <main id="main-content"><a href="https://example.com" rel="noopener noreferrer">external nav</a>{extra_body}</main>
</body>
</html>
"""


class HtmlArtifactContractTest(unittest.TestCase):
    def test_strict_profile_accepts_self_contained_document(self) -> None:
        issues = contract.validate_html_text(
            valid_html(),
            profile_name="strict-self-contained",
            path="roadmap.html",
            expected_artifact_kind="html-plan",
        )

        self.assertEqual([item.to_dict() for item in issues if item.severity == "error"], [])

    def test_navigation_links_are_not_resource_loads(self) -> None:
        issues = contract.validate_html_text(
            valid_html(extra_body='<a href="https://openai.com" rel="noopener noreferrer">OpenAI</a>'),
            profile_name="strict-self-contained",
            path="nav.html",
        )

        self.assertNotIn("external-load", {item.code for item in issues})

    def test_data_navigation_is_rejected_without_becoming_resource_load(self) -> None:
        issues = contract.validate_html_text(
            valid_html(extra_body='<a href="data:text/html,<h1>bad</h1>">bad</a>'),
            profile_name="strict-self-contained",
            path="data-nav.html",
        )
        error_codes = {item.code for item in issues if item.severity == "error"}

        self.assertIn("unsafe-url", error_codes)
        self.assertNotIn("external-load", error_codes)

    def test_srcset_checks_every_candidate_for_external_loads(self) -> None:
        cases = {
            "img-srcset-space": '<img alt="x" srcset="/local.png 1x, https://cdn.example/x.png 2x">',
            "img-srcset-no-space": '<img alt="x" srcset="/local.png 1x,https://evil.example/x.png 2x">',
            "source-srcset-no-space": '<picture><source srcset="/local.webp 1x,https://evil.example/x.webp 2x"><img alt="x" src="/local.png"></picture>',
        }

        for label, body in cases.items():
            with self.subTest(label=label):
                issues = contract.validate_html_text(
                    valid_html(extra_body=body),
                    profile_name="strict-self-contained",
                    path=f"{label}.html",
                )
                external_loads = [
                    item
                    for item in issues
                    if item.code == "external-load" and "https://" in item.message
                ]

                self.assertEqual(len(external_loads), 1)

    def test_image_data_url_requires_image_mime_and_image_context(self) -> None:
        allowed = contract.validate_html_text(
            valid_html(extra_body='<img alt="inline" src="data:image/png;base64,AAAA">'),
            profile_name="strict-self-contained",
            path="image-data.html",
        )
        allowed_srcset = contract.validate_html_text(
            valid_html(extra_body='<img alt="inline" srcset="data:image/png;base64,AAAA 1x,/local.png 2x">'),
            profile_name="strict-self-contained",
            path="image-data-srcset.html",
        )
        self.assertNotIn(
            "unsafe-url",
            {item.code for item in allowed if item.severity == "error"},
        )
        self.assertNotIn(
            "unsafe-url",
            {item.code for item in allowed_srcset if item.severity == "error"},
        )

        wrong_context = contract.validate_html_text(
            valid_html(extra_body='<a href="data:image/png;base64,AAAA">image nav</a>'),
            profile_name="strict-self-contained",
            path="image-data-nav.html",
        )
        wrong_mime = contract.validate_html_text(
            valid_html(extra_body='<img alt="bad" src="data:text/html,<h1>bad</h1>">'),
            profile_name="strict-self-contained",
            path="text-data-img.html",
        )

        self.assertIn("unsafe-url", {item.code for item in wrong_context if item.severity == "error"})
        self.assertIn("unsafe-url", {item.code for item in wrong_mime if item.severity == "error"})

    def test_strict_profile_rejects_static_contract_violations(self) -> None:
        cases = {
            "doctype-missing": valid_html().replace("<!DOCTYPE html>\n", ""),
            "artifact-kind-missing": valid_html().replace('  <meta name="artifact-kind" content="html-plan">\n', ""),
            "csp-missing": valid_html().replace("  <meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; connect-src 'self'; base-uri 'none'; form-action 'none'\">\n", ""),
            "external-load": valid_html(extra_body='<script src="https://cdn.example/app.js"></script>'),
            "duplicate-id": valid_html(extra_body='<section id="main-content"></section>'),
            "event-handler": valid_html(extra_body='<button onclick="alert(1)">run</button>'),
            "forbidden-element": valid_html(extra_body='<iframe src="/preview"></iframe>'),
            "external-link-rel": valid_html(extra_body='<a href="https://example.com/no-rel">bad</a>'),
            "unsafe-url": valid_html(extra_body='<a href="javascript:alert(1)">bad</a>'),
        }

        for expected_code, html in cases.items():
            with self.subTest(expected_code=expected_code):
                codes = {
                    item.code
                    for item in contract.validate_html_text(
                        html,
                        profile_name="strict-self-contained",
                        path=f"{expected_code}.html",
                    )
                    if item.severity == "error"
                }
                self.assertIn(expected_code, codes)

    def test_manifest_records_effective_html_and_all_routes(self) -> None:
        manifest = contract.load_manifest()
        issues = contract.check_manifest(manifest, ROOT)
        errors = [item.to_dict() for item in issues if item.severity == "error"]

        self.assertEqual(errors, [])
        self.assertEqual(
            {item["id"] for item in manifest["routes"]},
            {
                "html",
                "design-artifact",
                "html-wireframe",
                "html-prototype",
                "html-plan",
                "html-diagram",
            },
        )
        self.assertEqual(
            manifest["effectiveHtml"]["upstreamCommit"],
            "d95debbaef15af1d201fc6c10c77cf92b524a0d6",
        )
        self.assertEqual(manifest["effectiveHtml"]["license"], "MIT")

    def test_manifest_checker_rejects_unregistered_tracked_html(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "tools").mkdir()
            (root / "tools" / "unregistered.html").write_text(valid_html())
            manifest = json.loads(json.dumps(contract.load_manifest()))
            manifest["surfaces"] = []
            manifest["producers"] = []

            issues = contract.check_manifest(manifest, root)

        self.assertIn("unregistered-surface", {item.code for item in issues})

    def test_manifest_checker_rejects_canonical_reference_to_legacy_surface(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "canonical.html").write_text(valid_html(extra_body="legacy.html"))
            (root / "legacy.html").write_text(valid_html())
            manifest = json.loads(json.dumps(contract.load_manifest()))
            manifest["surfaces"] = [
                {"path": "canonical.html", "lifecycle": "canonical", "owner": "test", "artifactKind": "html-plan", "staticProfile": "strict-self-contained", "browserProfile": "roadmap-matrix"},
                {"path": "legacy.html", "lifecycle": "legacy", "owner": "test", "artifactKind": "legacy", "staticProfile": "strict-self-contained", "browserProfile": "roadmap-matrix"},
            ]
            manifest["producers"] = []
            manifest["literalExceptions"] = []

            issues = contract.check_manifest(manifest, root)

        self.assertIn("canonical-live-legacy-ref", {item.code for item in issues})


if __name__ == "__main__":
    unittest.main()
