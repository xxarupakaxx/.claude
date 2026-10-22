from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "render_review_guide.py"
SPEC = importlib.util.spec_from_file_location("render_review_guide", SCRIPT)
assert SPEC and SPEC.loader
rg = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = rg
SPEC.loader.exec_module(rg)

SOURCE = "package demo\n\nfunc Guard(x int) bool {\n\t// <承認> & \"確認\"\n\tif x == 0 {\n \n\t\treturn false\n\t}\n\treturn true\n}\n"
SHELL = "#!/bin/bash\r\nif [[ -n \"$X\" ]]; then\r\n  echo [[TAG:fact]]\r\nfi\r\n"


class RenderReviewGuideTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.repo = self.dir / "repo"
        self.repo.mkdir()
        git = ["git", "-C", str(self.repo), "-c", "user.name=t", "-c", "user.email=t@example.com"]
        subprocess.run(git[:3] + ["init", "-q"], check=True)
        (self.repo / "guard.go").write_text(SOURCE, encoding="utf-8")
        (self.repo / "run.sh").write_bytes(SHELL.encode("utf-8"))
        subprocess.run(git + ["add", "guard.go", "run.sh"], check=True)
        subprocess.run(git + ["commit", "-q", "-m", "init"], check=True)
        self.sha = subprocess.run(git[:3] + ["rev-parse", "HEAD"], capture_output=True, check=True, text=True).stdout.strip()
        self.out = self.dir / "out.html"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write(self, quotes: list[dict], body: str) -> tuple[Path, Path]:
        spec = {"repo": str(self.repo), "github": "owner/name", "title": "t", "reader": "r",
                "revs": {"head": self.sha}, "quotes": quotes}
        spec_path, body_path = self.dir / "spec.json", self.dir / "body.html"
        spec_path.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        body_path.write_text(body, encoding="utf-8")
        return spec_path, body_path

    def test_render_escapes_code_and_verify_passes(self) -> None:
        spec, body = self.write(
            [{"id": "q-guard", "rev": "head", "path": "guard.go", "start": 3, "end": 9, "focus": [5], "title": "ガード"},
             {"id": "q-find", "rev": "head", "path": "guard.go", "find": "return false", "before": 1, "after": 0}],
            '<main><h1 id="x">x</h1>[[q-guard]] [[TAG:fact]] [[q-find]] <a href="#q-guard">戻る</a></main>\n',
        )
        rg.render(spec, body, self.out)
        doc = self.out.read_text(encoding="utf-8")
        self.assertIn("&lt;承認&gt; &amp; &quot;確認&quot;", doc)
        self.assertIn('<span class="tag fact">確認済み</span>', doc)
        self.assertIn(f'data-rev="{self.sha}"', doc)
        self.assertIn('<span class="mk">注目</span>', doc)
        self.assertEqual(rg.verify(self.out, str(self.repo)), 0)

    def test_verify_detects_edited_code(self) -> None:
        spec, body = self.write([{"id": "q-guard", "rev": "head", "path": "guard.go", "start": 3, "end": 9}], "[[q-guard]]")
        rg.render(spec, body, self.out)
        doc = self.out.read_text(encoding="utf-8")
        self.out.write_text(doc.replace("return true", "return false", 1), encoding="utf-8")
        self.assertEqual(rg.verify(self.out, str(self.repo)), 1)

    def test_unused_or_duplicate_quote_is_rejected(self) -> None:
        q = [{"id": "q-guard", "rev": "head", "path": "guard.go", "start": 3, "end": 4},
             {"id": "q-unused", "rev": "head", "path": "guard.go", "start": 1, "end": 1}]
        spec, body = self.write(q, "[[q-guard]]")
        with self.assertRaises(rg.SpecError):
            rg.render(spec, body, self.out)
        spec, body = self.write(q[:1], "[[q-guard]] [[q-guard]]")
        with self.assertRaises(rg.SpecError):
            rg.render(spec, body, self.out)

    def test_ambiguous_find_and_out_of_range_focus_are_rejected(self) -> None:
        spec, body = self.write([{"id": "q-r", "rev": "head", "path": "guard.go", "find": "return"}], "[[q-r]]")
        with self.assertRaises(rg.SpecError):
            rg.render(spec, body, self.out)
        spec, body = self.write([{"id": "q-f", "rev": "head", "path": "guard.go", "start": 3, "end": 4, "focus": [9]}], "[[q-f]]")
        with self.assertRaises(rg.SpecError):
            rg.render(spec, body, self.out)

    def test_broken_anchor_keeps_existing_output(self) -> None:
        self.out.write_text("previous", encoding="utf-8")
        spec, body = self.write([{"id": "q-guard", "rev": "head", "path": "guard.go", "start": 3, "end": 4}], '[[q-guard]] <a href="#missing">x</a>')
        with self.assertRaises(rg.SpecError):
            rg.render(spec, body, self.out)
        self.assertEqual(self.out.read_text(encoding="utf-8"), "previous")

    def test_brackets_and_crlf_in_code_render_and_verify(self) -> None:
        spec, body = self.write([{"id": "q-sh", "rev": "head", "path": "run.sh", "start": 2, "end": 3}], "[[q-sh]] [[TAG:guess]]")
        rg.render(spec, body, self.out)
        doc = self.out.read_text(encoding="utf-8")
        self.assertIn("&#91;&#91; -n", doc)
        self.assertIn("echo &#91;&#91;TAG:fact]]", doc)
        self.assertNotIn("\r", doc)
        self.assertEqual(rg.verify(self.out, str(self.repo)), 0)

    def test_verify_detects_removed_line_and_changed_range(self) -> None:
        spec, body = self.write([{"id": "q-guard", "rev": "head", "path": "guard.go", "start": 3, "end": 5}], "[[q-guard]]")
        rg.render(spec, body, self.out)
        doc = self.out.read_text(encoding="utf-8")
        removed = doc.replace('<span class="ln"><span class="no">4</span>', '<span class="ln"><span class="no">X</span>', 1)
        self.out.write_text(removed, encoding="utf-8")
        self.assertEqual(rg.verify(self.out, str(self.repo)), 1)
        self.out.write_text(doc.replace("3〜5行", "3〜9行", 1), encoding="utf-8")
        self.assertEqual(rg.verify(self.out, str(self.repo)), 1)
        self.out.write_text(doc.replace('<div class="quote wide" id="q-guard" data-rev', '<div class="quote wide" id="q-guard" data-x', 1), encoding="utf-8")
        self.assertEqual(rg.verify(self.out, str(self.repo)), 1)

    def test_spec_and_body_errors_are_reported_as_spec_errors(self) -> None:
        spec, body = self.write([{"id": "q-guard", "rev": "head", "path": "guard.go"}], "[[q-guard]]")
        with self.assertRaises(rg.SpecError):
            rg.render(spec, body, self.out)
        spec, body = self.write([{"id": "q-Guard", "rev": "head", "path": "guard.go", "start": 1, "end": 1}], "[[q-Guard]]")
        with self.assertRaises(rg.SpecError):
            rg.render(spec, body, self.out)
        spec, body = self.write([{"id": "q-guard", "rev": "head", "path": "guard.go", "start": 1, "end": 1}], "<!doctype html><body>[[q-guard]]</body>")
        with self.assertRaises(rg.SpecError):
            rg.render(spec, body, self.out)
        spec, body = self.write([{"id": "q-last", "rev": "head", "path": "guard.go", "start": 11, "end": 11}], "[[q-last]]")
        with self.assertRaises(rg.SpecError):
            rg.render(spec, body, self.out)

    def test_ref_name_or_unknown_sha_in_revs_is_rejected(self) -> None:
        spec, body = self.write([{"id": "q-guard", "rev": "head", "path": "guard.go", "start": 1, "end": 1}], "[[q-guard]]")
        data = json.loads(spec.read_text(encoding="utf-8"))
        for rev in ("HEAD", "0" * 40):
            data["revs"]["head"] = rev
            spec.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(rg.SpecError):
                rg.render(spec, body, self.out)

    def test_wrong_types_in_quote_are_rejected(self) -> None:
        cases = [
            {"start": "3", "end": 4},
            {"start": 3, "end": 4, "ctx": -1},
            {"start": 3, "end": 4, "focus": 3},
            {"find": "Guard", "start": 3, "end": 4},
        ]
        for extra in cases:
            spec, body = self.write([{"id": "q-guard", "rev": "head", "path": "guard.go", **extra}], "[[q-guard]]")
            with self.subTest(extra=extra), self.assertRaises(rg.SpecError):
                rg.render(spec, body, self.out)

    def test_verify_does_not_depend_on_attribute_order(self) -> None:
        spec, body = self.write([{"id": "q-guard", "rev": "head", "path": "guard.go", "start": 3, "end": 5}], "[[q-guard]]")
        rg.render(spec, body, self.out)
        doc = self.out.read_text(encoding="utf-8")
        reordered = doc.replace(f'<div class="quote wide" id="q-guard" data-rev="{self.sha}" data-path="guard.go">',
                                f'<div data-path="guard.go" id="q-guard" class="quote wide" data-rev="{self.sha}">', 1)
        self.assertNotEqual(doc, reordered)
        self.out.write_text(reordered, encoding="utf-8")
        self.assertEqual(rg.verify(self.out, str(self.repo)), 0)

    def test_verify_detects_edited_header_link_and_mark(self) -> None:
        spec, body = self.write([{"id": "q-guard", "rev": "head", "path": "guard.go", "start": 3, "end": 5, "focus": [4]}], "[[q-guard]]")
        rg.render(spec, body, self.out)
        doc = self.out.read_text(encoding="utf-8")
        edits = [
            ('<code class="path">guard.go</code>', '<code class="path">other.go</code>'),
            (f"head {self.sha[:7]}", "head 0000000"),
            (f"/blob/{self.sha}/guard.go", "/blob/main/guard.go"),
            ('<span class="mk">注目</span>', '<span class="mk">return nil</span>'),
        ]
        for old, new in edits:
            self.assertIn(old, doc)
            self.out.write_text(doc.replace(old, new, 1), encoding="utf-8")
            with self.subTest(edit=new):
                self.assertEqual(rg.verify(self.out, str(self.repo)), 1)

    def test_text_keeps_inline_code_and_drops_code_blocks(self) -> None:
        body = ('<nav aria-label="目次"><a href="#x">目次の項目</a></nav><!-- 作業メモ -->'
                '<p id="x">状態は <code>completed</code> です。</p><p><a href="#x">一つ目</a><a href="#x">二つ目</a></p>[[q-guard]]')
        spec, body_path = self.write([{"id": "q-guard", "rev": "head", "path": "guard.go", "start": 3, "end": 5}], body)
        rg.render(spec, body_path, self.out)
        text = rg.visible_text(self.out)
        self.assertIn("状態は completed です。", text)
        self.assertIn("一つ目\n二つ目", text)
        for absent in ("Guard", "目次の項目", "作業メモ"):
            self.assertNotIn(absent, text)


if __name__ == "__main__":
    unittest.main()
