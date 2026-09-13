from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from review_evidence_collector import (  # noqa: E402
    CollisionError,
    PathEscapeError,
    collect_review_evidence,
)


class ReviewEvidenceCollectorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    @staticmethod
    def read_jsonl(path: Path) -> list[dict[str, object]]:
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def event(self, **overrides: object) -> dict[str, object]:
        event: dict[str, object] = {
            "source_comment_id": "inline:1",
            "source_url": "https://example.invalid/review/1",
            "body": "missing assertion on escaped defects",
            "timestamp": "2026-08-30T12:00:00Z",
            "failure_classes": ["missing_test"],
            "earliest_preventable_gates": ["review"],
            "verified_against": ["diff:scripts/review_evidence_collector.py"],
            "allowed_fix_scope": ["scripts/review_evidence_collector.py"],
        }
        event.update(overrides)
        return event

    def test_verified_scoped_event_writes_raw_and_l0_defect(self) -> None:
        result = collect_review_evidence(
            task_id="task-1",
            changed_paths=["scripts/review_evidence_collector.py"],
            events=[self.event()],
            artifact_root=self.root,
            artifact_dir="artifacts",
        )

        artifact_dir = self.root / "artifacts"
        raw_records = self.read_jsonl(artifact_dir / "raw-review-events.jsonl")
        escaped_defects = self.read_jsonl(artifact_dir / "escaped-defects.jsonl")

        self.assertEqual(result["accepted_count"], 1)
        self.assertEqual(len(raw_records), 1)
        self.assertEqual(len(escaped_defects), 1)
        self.assertEqual(escaped_defects[0]["promotion_level"], "L0")

    def test_injection_body_is_not_executed_or_stored(self) -> None:
        marker = self.root / "pwned"

        collect_review_evidence(
            task_id="task-1",
            changed_paths=["scripts/review_evidence_collector.py"],
            events=[self.event(body=f"$(touch {marker})")],
            artifact_root=self.root,
            artifact_dir="artifacts",
        )

        output = "\n".join(
            [
                (self.root / "artifacts" / "raw-review-events.jsonl").read_text(encoding="utf-8"),
                (self.root / "artifacts" / "escaped-defects.jsonl").read_text(encoding="utf-8"),
            ]
        )
        self.assertFalse(marker.exists())
        self.assertNotIn("touch", output)
        self.assertNotIn(str(marker), output)

    def test_unverified_event_remains_raw_only(self) -> None:
        collect_review_evidence(
            task_id="task-1",
            changed_paths=["scripts/review_evidence_collector.py"],
            events=[self.event(verified_against=["comment:attacker"])],
            artifact_root=self.root,
            artifact_dir="artifacts",
        )

        artifact_dir = self.root / "artifacts"
        raw_records = self.read_jsonl(artifact_dir / "raw-review-events.jsonl")
        escaped_defects = self.read_jsonl(artifact_dir / "escaped-defects.jsonl")
        self.assertIn("verified_against", raw_records[0]["rejected_reason"])
        self.assertEqual(escaped_defects, [])

    def test_scope_outside_changed_paths_is_rejected(self) -> None:
        collect_review_evidence(
            task_id="task-1",
            changed_paths=["scripts/review_evidence_collector.py"],
            events=[self.event(allowed_fix_scope=["tests/test_review_evidence_collector.py"])],
            artifact_root=self.root,
            artifact_dir="artifacts",
        )

        artifact_dir = self.root / "artifacts"
        raw_records = self.read_jsonl(artifact_dir / "raw-review-events.jsonl")
        escaped_defects = self.read_jsonl(artifact_dir / "escaped-defects.jsonl")
        self.assertIn("outside changed_paths", raw_records[0]["rejected_reason"])
        self.assertEqual(escaped_defects, [])

    def test_same_event_is_idempotently_deduped(self) -> None:
        first = collect_review_evidence(
            task_id="task-1",
            changed_paths=["scripts/review_evidence_collector.py"],
            events=[self.event()],
            artifact_root=self.root,
            artifact_dir="artifacts",
        )
        artifact_dir = self.root / "artifacts"
        raw_before = (artifact_dir / "raw-review-events.jsonl").read_bytes()
        escaped_before = (artifact_dir / "escaped-defects.jsonl").read_bytes()

        second = collect_review_evidence(
            task_id="task-1",
            changed_paths=["scripts/review_evidence_collector.py"],
            events=[self.event()],
            artifact_root=self.root,
            artifact_dir="artifacts",
        )

        self.assertEqual(first["accepted_count"], 1)
        self.assertEqual(second["duplicate_count"], 1)
        self.assertEqual((artifact_dir / "raw-review-events.jsonl").read_bytes(), raw_before)
        self.assertEqual((artifact_dir / "escaped-defects.jsonl").read_bytes(), escaped_before)

    def test_same_comment_id_with_different_body_hash_fails_collision(self) -> None:
        collect_review_evidence(
            task_id="task-1",
            changed_paths=["scripts/review_evidence_collector.py"],
            events=[self.event(body="first")],
            artifact_root=self.root,
            artifact_dir="artifacts",
        )
        artifact_dir = self.root / "artifacts"
        raw_before = (artifact_dir / "raw-review-events.jsonl").read_bytes()
        escaped_before = (artifact_dir / "escaped-defects.jsonl").read_bytes()

        with self.assertRaises(CollisionError):
            collect_review_evidence(
                task_id="task-1",
                changed_paths=["scripts/review_evidence_collector.py"],
                events=[self.event(body="second")],
                artifact_root=self.root,
                artifact_dir="artifacts",
            )

        self.assertEqual((artifact_dir / "raw-review-events.jsonl").read_bytes(), raw_before)
        self.assertEqual((artifact_dir / "escaped-defects.jsonl").read_bytes(), escaped_before)

    def test_artifact_directory_cannot_traverse_or_symlink_escape(self) -> None:
        outside = self.root / "outside"
        outside.mkdir()
        (self.root / "link").symlink_to(outside, target_is_directory=True)

        for artifact_dir in ("../escape", "link/artifacts"):
            with self.assertRaises(PathEscapeError):
                collect_review_evidence(
                    task_id="task-1",
                    changed_paths=["scripts/review_evidence_collector.py"],
                    events=[self.event()],
                    artifact_root=self.root,
                    artifact_dir=artifact_dir,
                )

    def test_partial_write_failure_preserves_existing_jsonl(self) -> None:
        collect_review_evidence(
            task_id="task-1",
            changed_paths=["scripts/review_evidence_collector.py"],
            events=[self.event(source_comment_id="inline:1", body="first")],
            artifact_root=self.root,
            artifact_dir="artifacts",
        )
        artifact_dir = self.root / "artifacts"
        raw_before = (artifact_dir / "raw-review-events.jsonl").read_bytes()
        escaped_before = (artifact_dir / "escaped-defects.jsonl").read_bytes()

        def fail_before_replace(path: Path, lines: object) -> None:
            raise OSError("simulated atomic write failure")

        with mock.patch("review_evidence_collector._atomic_jsonl", side_effect=fail_before_replace):
            with self.assertRaises(OSError):
                collect_review_evidence(
                    task_id="task-1",
                    changed_paths=["scripts/review_evidence_collector.py"],
                    events=[self.event(source_comment_id="inline:2", body="second")],
                    artifact_root=self.root,
                    artifact_dir="artifacts",
                )

        self.assertEqual((artifact_dir / "raw-review-events.jsonl").read_bytes(), raw_before)
        self.assertEqual((artifact_dir / "escaped-defects.jsonl").read_bytes(), escaped_before)

    def test_rerun_backfills_escaped_after_raw_only_partial_write(self) -> None:
        artifact_dir = self.root / "artifacts"
        real_atomic_jsonl = __import__("review_evidence_collector")._atomic_jsonl
        write_count = 0

        def fail_second_write(path: Path, lines: object) -> None:
            nonlocal write_count
            write_count += 1
            if write_count == 2:
                raise OSError("simulated escaped write failure")
            real_atomic_jsonl(path, lines)

        with mock.patch(
            "review_evidence_collector._atomic_jsonl", side_effect=fail_second_write
        ):
            with self.assertRaises(OSError):
                collect_review_evidence(
                    task_id="task-1",
                    changed_paths=["scripts/review_evidence_collector.py"],
                    events=[self.event()],
                    artifact_root=self.root,
                    artifact_dir="artifacts",
                )

        raw_after_failure = self.read_jsonl(artifact_dir / "raw-review-events.jsonl")
        self.assertEqual(len(raw_after_failure), 1)
        self.assertFalse((artifact_dir / "escaped-defects.jsonl").exists())

        result = collect_review_evidence(
            task_id="task-1",
            changed_paths=["scripts/review_evidence_collector.py"],
            events=[self.event()],
            artifact_root=self.root,
            artifact_dir="artifacts",
        )

        raw_records = self.read_jsonl(artifact_dir / "raw-review-events.jsonl")
        escaped_defects = self.read_jsonl(artifact_dir / "escaped-defects.jsonl")
        self.assertEqual(result["raw_new_count"], 0)
        self.assertEqual(result["escaped_new_count"], 1)
        self.assertEqual(result["accepted_count"], 1)
        self.assertEqual(raw_records, raw_after_failure)
        self.assertEqual(len(escaped_defects), 1)


if __name__ == "__main__":
    unittest.main()
