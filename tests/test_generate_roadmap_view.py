from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate-roadmap-view.py"
SPEC = importlib.util.spec_from_file_location("generate_roadmap_view", SCRIPT)
assert SPEC and SPEC.loader
roadmap = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(roadmap)


class RoadmapGeneratorContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.task_dir = self.root / "task"
        self.task_dir.mkdir()
        (self.task_dir / "00_spec.md").write_text("# Sample roadmap\n")

        self.template = self.root / "roadmap_viewer.html"
        self.template.write_text(
            '<script id="embedded-snapshot" type="application/json">'
            f"{roadmap.PLACEHOLDER}"
            "</script>"
        )
        self.previous_template = roadmap.TEMPLATE
        roadmap.TEMPLATE = self.template

    def tearDown(self) -> None:
        roadmap.TEMPLATE = self.previous_template
        self.temp_dir.cleanup()

    def test_hub_mode_does_not_require_task_dir(self) -> None:
        args = roadmap.parse_args(["--hub", "--memory-root", "/tmp/memory"])

        self.assertTrue(args.hub)
        self.assertIsNone(args.task_dir)

    def test_single_task_serve_watch_cli_remains_supported(self) -> None:
        args = roadmap.parse_args([str(self.task_dir), "--serve", "--watch"])

        self.assertEqual(args.task_dir, str(self.task_dir))
        self.assertTrue(args.serve)
        self.assertTrue(args.watch)
        self.assertFalse(args.hub)

    def test_hub_mode_rejects_task_dir(self) -> None:
        with self.assertRaises(SystemExit):
            roadmap.parse_args([str(self.task_dir), "--hub"])

    def test_hub_mode_delegates_memory_roots_and_server_options(self) -> None:
        with mock.patch.object(roadmap, "run_task_hub", return_value=17) as run_hub:
            result = roadmap.main([
                "--hub",
                "--memory-root", "/tmp/one",
                "--memory-root", "/tmp/two",
                "--host", "localhost",
                "--port", "4321",
                "--open",
            ])

        self.assertEqual(result, 17)
        run_hub.assert_called_once_with(
            [Path("/tmp/one").resolve(), Path("/tmp/two").resolve()],
            host="localhost",
            port=4321,
            open_browser=True,
        )

    def test_snapshot_v1_includes_optional_workflow_inputs(self) -> None:
        (self.task_dir / "team-journal.md").write_text("# Team Journal\n")
        (self.task_dir / "90_verification.md").write_text("# Verification\n")

        snapshot = roadmap.build_snapshot(self.task_dir)

        self.assertEqual(snapshot["version"], 1)
        self.assertEqual(snapshot["files"]["team-journal.md"], "# Team Journal\n")
        self.assertEqual(snapshot["files"]["90_verification.md"], "# Verification\n")

    def test_default_source_symlink_is_not_followed(self) -> None:
        target = self.root / "outside-plan.md"
        target.write_text("# Outside secret\n")
        (self.task_dir / "30_plan.md").symlink_to(target)

        snapshot = roadmap.build_snapshot(self.task_dir)

        self.assertNotIn("30_plan.md", snapshot["files"])
        self.assertNotIn("Outside secret", json.dumps(snapshot))

    def test_artifacts_are_recursive_sorted_metadata_without_outputs_or_symlinks(self) -> None:
        artifact_dir = self.task_dir / "artifacts"
        artifact_dir.mkdir()
        binary = artifact_dir / "result.bin"
        binary.write_bytes(b"\x00\x01secret payload")
        (artifact_dir / "alpha.txt").write_text("alpha")
        (self.task_dir / "roadmap.html").write_text("old output")
        (self.task_dir / "roadmap-snapshot.json").write_text("{}")
        (self.task_dir / ".roadmap.html.123.tmp").write_text("temporary")
        (self.task_dir / "scratch.tmp").write_text("temporary")

        custom_output = artifact_dir / "published.html"
        custom_output.write_text("custom output")

        symlink = artifact_dir / "linked-result.bin"
        symlink.symlink_to(binary)
        external_dir = self.root / "external"
        external_dir.mkdir()
        (external_dir / "outside.txt").write_text("outside")
        (self.task_dir / "linked-dir").symlink_to(external_dir, target_is_directory=True)

        snapshot = roadmap.build_snapshot(self.task_dir, output=custom_output)
        artifacts = snapshot["artifacts"]
        paths = [item["path"] for item in artifacts]

        self.assertEqual(paths, sorted(paths))
        self.assertIn("artifacts/alpha.txt", paths)
        self.assertIn("artifacts/result.bin", paths)
        self.assertNotIn("artifacts/published.html", paths)
        self.assertNotIn("artifacts/linked-result.bin", paths)
        self.assertNotIn("linked-dir/outside.txt", paths)
        self.assertNotIn("roadmap.html", paths)
        self.assertNotIn("roadmap-snapshot.json", paths)
        self.assertNotIn(".roadmap.html.123.tmp", paths)
        self.assertNotIn("scratch.tmp", paths)

        result = next(item for item in artifacts if item["path"] == "artifacts/result.bin")
        self.assertEqual(
            set(result),
            {"name", "path", "type", "size", "modifiedAt"},
        )
        self.assertEqual(result["name"], "result.bin")
        self.assertEqual(result["type"], "bin")
        self.assertEqual(result["size"], len(b"\x00\x01secret payload"))
        self.assertNotIn("secret payload", json.dumps(snapshot))

    def test_fingerprint_tracks_source_content_and_artifact_metadata(self) -> None:
        artifact = self.task_dir / "artifact.txt"
        artifact.write_text("unchanged content")

        first = roadmap.build_snapshot(self.task_dir)
        same = roadmap.build_snapshot(self.task_dir)
        self.assertEqual(first["fingerprint"], same["fingerprint"])

        before = artifact.stat()
        os.utime(
            artifact,
            ns=(before.st_atime_ns, before.st_mtime_ns + 1_000_000_000),
        )
        metadata_changed = roadmap.build_snapshot(self.task_dir)
        self.assertNotEqual(first["fingerprint"], metadata_changed["fingerprint"])

        spec = self.task_dir / "00_spec.md"
        spec_mtime = spec.stat().st_mtime_ns
        spec.write_text("# Changed roadmap\n")
        os.utime(spec, ns=(spec.stat().st_atime_ns, spec_mtime))
        source_changed = roadmap.build_snapshot(self.task_dir)
        self.assertNotEqual(metadata_changed["fingerprint"], source_changed["fingerprint"])

    def test_unchanged_fingerprint_does_not_rewrite_html_or_json(self) -> None:
        output = self.task_dir / "roadmap.html"
        first = roadmap.write_outputs(self.task_dir, output, write_json=True)
        json_output = self.task_dir / "roadmap-snapshot.json"
        before = {
            output: (output.stat().st_ino, output.stat().st_mtime_ns),
            json_output: (json_output.stat().st_ino, json_output.stat().st_mtime_ns),
        }

        time.sleep(0.02)
        second = roadmap.write_outputs(self.task_dir, output, write_json=True)

        self.assertEqual(first["fingerprint"], second["fingerprint"])
        self.assertEqual(
            before,
            {
                output: (output.stat().st_ino, output.stat().st_mtime_ns),
                json_output: (json_output.stat().st_ino, json_output.stat().st_mtime_ns),
            },
        )

    def test_artifact_only_change_rewrites_outputs_and_snapshot_fingerprint(self) -> None:
        artifact = self.task_dir / "artifact.txt"
        artifact.write_text("unchanged content")
        output = self.task_dir / "roadmap.html"
        first = roadmap.write_outputs(self.task_dir, output, write_json=True)
        json_output = self.task_dir / "roadmap-snapshot.json"
        before = (output.stat().st_mtime_ns, json_output.stat().st_mtime_ns)

        stat = artifact.stat()
        os.utime(
            artifact,
            ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000),
        )
        time.sleep(0.02)
        second = roadmap.write_outputs(self.task_dir, output, write_json=True)

        self.assertNotEqual(first["fingerprint"], second["fingerprint"])
        self.assertNotEqual(before[0], output.stat().st_mtime_ns)
        self.assertNotEqual(before[1], json_output.stat().st_mtime_ns)


if __name__ == "__main__":
    unittest.main()
