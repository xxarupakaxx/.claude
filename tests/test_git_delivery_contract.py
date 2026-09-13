from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from git_delivery_contract import (  # noqa: E402
    collect_range_snapshot,
    collect_staged_snapshot,
    validate_range_refs,
    validate_snapshot_fresh,
)


class GitDeliveryContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary_directory.name)
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Claude Test")
        self.git("config", "user.email", "claude@example.invalid")
        (self.repo / "tracked.txt").write_text("initial\n", encoding="utf-8")
        self.git("add", "tracked.txt")
        self.git("commit", "-m", "initial")

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def git(self, *arguments: str) -> str:
        return subprocess.run(
            ["git", *arguments],
            cwd=self.repo,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def test_staged_snapshot_excludes_unstaged_and_untracked_changes(self) -> None:
        (self.repo / "tracked.txt").write_text("staged\n", encoding="utf-8")
        self.git("add", "tracked.txt")
        (self.repo / "tracked.txt").write_text("staged\nunstaged\n", encoding="utf-8")
        (self.repo / "untracked.txt").write_text("untracked\n", encoding="utf-8")

        snapshot = collect_staged_snapshot(self.repo, allowed_paths=["tracked.txt"])

        self.assertEqual(snapshot["changed_paths"], ["tracked.txt"])
        self.assertIn("+staged", snapshot["worker_patch"])
        self.assertNotIn("unstaged", snapshot["worker_patch"])
        self.assertNotIn("untracked.txt", snapshot["changed_paths"])

    def test_staged_snapshot_identifies_repository_branch_head_and_index(self) -> None:
        (self.repo / "tracked.txt").write_text("staged\n", encoding="utf-8")
        self.git("add", "tracked.txt")

        snapshot = collect_staged_snapshot(self.repo, allowed_paths=["tracked.txt"])

        self.assertEqual(snapshot["repository_root"], str(self.repo.resolve()))
        self.assertEqual(snapshot["branch"], "main")
        self.assertEqual(snapshot["head_sha"], self.git("rev-parse", "HEAD"))
        self.assertRegex(snapshot["index_fingerprint"], r"^[a-f0-9]{64}$")

    def test_empty_staged_snapshot_is_blocked(self) -> None:
        snapshot = collect_staged_snapshot(self.repo, allowed_paths=["tracked.txt"])

        self.assertEqual(snapshot["draft_status"], "DRAFT_BLOCKED")
        self.assertIn("empty_diff", snapshot["violations"])

    def test_staged_change_after_draft_marks_snapshot_stale(self) -> None:
        (self.repo / "tracked.txt").write_text("first staged version\n", encoding="utf-8")
        self.git("add", "tracked.txt")
        snapshot = collect_staged_snapshot(self.repo, allowed_paths=["tracked.txt"])
        (self.repo / "tracked.txt").write_text("second staged version\n", encoding="utf-8")
        self.git("add", "tracked.txt")

        decision = validate_snapshot_fresh(
            self.repo,
            snapshot,
            expected_source_hash=snapshot["source_hash"],
            allowed_paths=["tracked.txt"],
            allow_deletes=False,
            allow_renames=False,
            max_patch_bytes=64 * 1024,
        )

        self.assertEqual(decision["status"], "DRAFT_STALE")
        self.assertIsNone(decision["current"]["worker_patch"])

    def test_snapshot_blocks_staged_paths_outside_exact_allowlist(self) -> None:
        (self.repo / "tracked.txt").write_text("changed\n", encoding="utf-8")
        self.git("add", "tracked.txt")

        snapshot = collect_staged_snapshot(self.repo, allowed_paths=["expected.txt"])

        self.assertIn("path_not_allowed:tracked.txt", snapshot["violations"])

    def test_snapshot_requires_an_exact_allowlist(self) -> None:
        (self.repo / "tracked.txt").write_text("changed\n", encoding="utf-8")
        self.git("add", "tracked.txt")

        snapshot = collect_staged_snapshot(self.repo)

        self.assertIn("allowed_paths_required", snapshot["violations"])

    def test_snapshot_policy_change_marks_staged_snapshot_stale(self) -> None:
        (self.repo / "tracked.txt").write_text("changed\n", encoding="utf-8")
        self.git("add", "tracked.txt")
        snapshot = collect_staged_snapshot(self.repo, allowed_paths=["tracked.txt"])
        snapshot["allowed_paths"] = None

        decision = validate_snapshot_fresh(
            self.repo,
            snapshot,
            expected_source_hash=snapshot["source_hash"],
            allowed_paths=["tracked.txt"],
            allow_deletes=False,
            allow_renames=False,
            max_patch_bytes=64 * 1024,
        )

        self.assertEqual(decision["status"], "DRAFT_STALE")
        self.assertIsNone(decision["current"]["worker_patch"])

    def test_snapshot_blocks_delete_without_explicit_permission(self) -> None:
        self.git("rm", "tracked.txt")

        snapshot = collect_staged_snapshot(self.repo)

        self.assertIn("delete_not_allowed:tracked.txt", snapshot["violations"])

    def test_rename_requires_old_and_new_paths_in_allowlist(self) -> None:
        self.git("mv", "tracked.txt", "renamed.txt")

        snapshot = collect_staged_snapshot(
            self.repo,
            allowed_paths=["renamed.txt"],
            allow_renames=True,
        )

        self.assertIn("path_not_allowed:tracked.txt", snapshot["violations"])

    def test_rename_from_sensitive_path_is_blocked(self) -> None:
        (self.repo / ".env").write_text("not-a-real-secret\n", encoding="utf-8")
        self.git("add", ".env")
        self.git("commit", "-m", "add sensitive fixture")
        self.git("mv", ".env", "config.txt")

        snapshot = collect_staged_snapshot(
            self.repo,
            allowed_paths=[".env", "config.txt"],
            allow_renames=True,
        )

        self.assertIn("secret_in_patch", snapshot["violations"])
        self.assertIsNone(snapshot["worker_patch"])

    def test_snapshot_blocks_unmerged_entries(self) -> None:
        self.git("checkout", "-b", "other")
        (self.repo / "tracked.txt").write_text("other\n", encoding="utf-8")
        self.git("add", "tracked.txt")
        self.git("commit", "-m", "other")
        self.git("checkout", "main")
        (self.repo / "tracked.txt").write_text("main\n", encoding="utf-8")
        self.git("add", "tracked.txt")
        self.git("commit", "-m", "main")
        merge = subprocess.run(
            ["git", "merge", "other"],
            cwd=self.repo,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(merge.returncode, 0)

        snapshot = collect_staged_snapshot(self.repo)

        self.assertIn("unmerged:tracked.txt", snapshot["violations"])

    def test_snapshot_does_not_expose_high_confidence_secret_to_worker(self) -> None:
        (self.repo / "tracked.txt").write_text(
            "-----BEGIN PRIVATE KEY-----\nnot-a-real-key\n",
            encoding="utf-8",
        )
        self.git("add", "tracked.txt")

        snapshot = collect_staged_snapshot(self.repo)

        self.assertIsNone(snapshot["worker_patch"])
        self.assertIn("secret_in_patch", snapshot["violations"])

    def test_snapshot_blocks_common_api_tokens(self) -> None:
        (self.repo / "tracked.txt").write_text(
            "OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyz123456\n",
            encoding="utf-8",
        )
        self.git("add", "tracked.txt")

        snapshot = collect_staged_snapshot(self.repo, allowed_paths=["tracked.txt"])

        self.assertIsNone(snapshot["worker_patch"])
        self.assertIn("secret_in_patch", snapshot["violations"])

    def test_snapshot_omits_binary_patch_from_worker_input(self) -> None:
        (self.repo / "binary.bin").write_bytes(b"\x00\x01\x02\x03")
        self.git("add", "binary.bin")

        snapshot = collect_staged_snapshot(self.repo, allowed_paths=["binary.bin"])

        self.assertIsNone(snapshot["worker_patch"])

    def test_snapshot_blocks_patch_over_size_limit(self) -> None:
        (self.repo / "tracked.txt").write_text("x" * 200 + "\n", encoding="utf-8")
        self.git("add", "tracked.txt")

        snapshot = collect_staged_snapshot(
            self.repo, allowed_paths=["tracked.txt"], max_patch_bytes=80
        )

        self.assertIsNone(snapshot["worker_patch"])
        self.assertIn("patch_too_large", snapshot["violations"])

    def test_snapshot_disables_textconv_commands(self) -> None:
        marker = self.repo / "textconv-ran"
        converter = self.repo / "textconv.sh"
        converter.write_text(f"#!/bin/sh\ntouch '{marker}'\ncat \"$1\"\n", encoding="utf-8")
        converter.chmod(0o755)
        (self.repo / ".gitattributes").write_text("*.txt diff=unsafe\n", encoding="utf-8")
        self.git("add", ".gitattributes")
        self.git("commit", "-m", "configure textconv")
        self.git("config", "diff.unsafe.textconv", str(converter))
        (self.repo / "tracked.txt").write_text("changed\n", encoding="utf-8")
        self.git("add", "tracked.txt")

        collect_staged_snapshot(self.repo, allowed_paths=["tracked.txt"])

        self.assertFalse(marker.exists())

    def test_snapshot_reports_name_status_and_numstat(self) -> None:
        (self.repo / "tracked.txt").write_text("changed\n", encoding="utf-8")
        self.git("add", "tracked.txt")

        snapshot = collect_staged_snapshot(self.repo, allowed_paths=["tracked.txt"])

        self.assertEqual(snapshot["name_status"], [{"status": "M", "paths": ["tracked.txt"]}])
        self.assertIn("1\t1\ttracked.txt", snapshot["numstat"])

    def test_pr_snapshot_uses_explicit_base_and_head_not_worktree(self) -> None:
        base_sha = self.git("rev-parse", "HEAD")
        (self.repo / "tracked.txt").write_text("committed head\n", encoding="utf-8")
        self.git("add", "tracked.txt")
        self.git("commit", "-m", "head")
        head_sha = self.git("rev-parse", "HEAD")
        (self.repo / "tracked.txt").write_text("dirty worktree\n", encoding="utf-8")

        snapshot = collect_range_snapshot(self.repo, base_sha=base_sha, head_sha=head_sha)

        self.assertEqual(snapshot["changed_paths"], ["tracked.txt"])
        self.assertIn("+committed head", snapshot["worker_patch"])
        self.assertNotIn("dirty worktree", snapshot["worker_patch"])

    def test_pr_snapshot_becomes_stale_when_head_ref_moves(self) -> None:
        base_sha = self.git("rev-parse", "HEAD")
        (self.repo / "tracked.txt").write_text("first head\n", encoding="utf-8")
        self.git("add", "tracked.txt")
        self.git("commit", "-m", "first head")
        snapshot = collect_range_snapshot(
            self.repo,
            base_sha=base_sha,
            head_sha=self.git("rev-parse", "HEAD"),
            allowed_paths=["tracked.txt"],
        )
        (self.repo / "tracked.txt").write_text("second head\n", encoding="utf-8")
        self.git("add", "tracked.txt")
        self.git("commit", "-m", "second head")

        decision = validate_range_refs(
            self.repo,
            snapshot,
            expected_source_hash=snapshot["source_hash"],
            base_ref=base_sha,
            head_ref="HEAD",
            allowed_paths=["tracked.txt"],
            allow_deletes=False,
            allow_renames=False,
            max_patch_bytes=64 * 1024,
        )

        self.assertEqual(decision["status"], "DRAFT_STALE")

    def test_range_snapshot_recomputes_policy_and_violations(self) -> None:
        base_sha = self.git("rev-parse", "HEAD")
        (self.repo / "tracked.txt").write_text("head\n", encoding="utf-8")
        self.git("add", "tracked.txt")
        self.git("commit", "-m", "head")
        head_sha = self.git("rev-parse", "HEAD")
        snapshot = collect_range_snapshot(
            self.repo,
            base_sha=base_sha,
            head_sha=head_sha,
            allowed_paths=["tracked.txt"],
        )
        snapshot["violations"] = []
        snapshot["allowed_paths"] = None

        decision = validate_range_refs(
            self.repo,
            snapshot,
            expected_source_hash=snapshot["source_hash"],
            base_ref=base_sha,
            head_ref=head_sha,
            allowed_paths=["tracked.txt"],
            allow_deletes=False,
            allow_renames=False,
            max_patch_bytes=64 * 1024,
        )

        self.assertEqual(decision["status"], "DRAFT_STALE")

    def test_staged_snapshot_hash_tampering_cannot_replace_trusted_hash(self) -> None:
        (self.repo / "tracked.txt").write_text("first\n", encoding="utf-8")
        self.git("add", "tracked.txt")
        snapshot = collect_staged_snapshot(self.repo, allowed_paths=["tracked.txt"])
        trusted_hash = snapshot["source_hash"]
        (self.repo / "tracked.txt").write_text("second\n", encoding="utf-8")
        self.git("add", "tracked.txt")
        current = collect_staged_snapshot(self.repo, allowed_paths=["tracked.txt"])
        snapshot["source_hash"] = current["source_hash"]

        decision = validate_snapshot_fresh(
            self.repo,
            snapshot,
            expected_source_hash=trusted_hash,
            allowed_paths=["tracked.txt"],
            allow_deletes=False,
            allow_renames=False,
            max_patch_bytes=64 * 1024,
        )

        self.assertEqual(decision["status"], "DRAFT_STALE")

    def test_staged_cli_emits_machine_readable_snapshot(self) -> None:
        (self.repo / "tracked.txt").write_text("changed\n", encoding="utf-8")
        self.git("add", "tracked.txt")

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "git_delivery_contract.py"),
                "staged",
                str(self.repo),
                "--allowed-path",
                "tracked.txt",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["draft_status"], "DRAFT_READY")
        self.assertIsNone(payload["worker_patch"])
        self.assertRegex(payload["worker_patch_sha256"], r"^[a-f0-9]{64}$")

    def test_staged_cli_returns_blocked_exit_for_missing_allowlist(self) -> None:
        (self.repo / "tracked.txt").write_text("changed\n", encoding="utf-8")
        self.git("add", "tracked.txt")

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "git_delivery_contract.py"),
                "staged",
                str(self.repo),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 3)
        self.assertIn("allowed_paths_required", json.loads(result.stdout)["violations"])

    def test_range_cli_returns_structured_block_for_invalid_ref(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "git_delivery_contract.py"),
                "range",
                str(self.repo),
                "--base",
                "missing-ref",
                "--head",
                "HEAD",
                "--allowed-path",
                "tracked.txt",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 3)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["draft_status"], "DRAFT_BLOCKED")
        self.assertEqual(payload["violations"], ["git_contract_error"])


if __name__ == "__main__":
    unittest.main()
