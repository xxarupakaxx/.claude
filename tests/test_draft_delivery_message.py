from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from draft_delivery_message import (  # noqa: E402
    WORKER_MODEL,
    claim_evidence_skeleton,
    prepare_draft_prompt,
    validate_draft_output,
)


class DraftDeliveryMessageTest(unittest.TestCase):
    @staticmethod
    def draft_input() -> dict[str, object]:
        return {
            "draft_id": "draft-1",
            "draft_kind": "commit",
            "source_hash": "a" * 64,
            "changed_paths": ["app.py"],
            "evidence_bundle_id": "eb-1",
            "acceptance_ids": ["A1"],
            "test_ids": ["T1"],
            "residual_risk_ids": [],
            "template_sections": [],
            "policy_source": "CLAUDE.md",
            "worker_patch": "safe bounded patch",
        }

    @staticmethod
    def valid_output() -> dict[str, object]:
        return {
            "draft_id": "draft-1",
            "draft_kind": "commit",
            "source_hash": "a" * 64,
            "status": "DRAFT_READY",
            "claim_references": ["app.py", "A1", "T1"],
            "content": {"type": "feat", "subject": "配送契約を追加", "body": ""},
        }

    def test_prompt_is_tool_free_haiku_worker_with_bounded_input(self) -> None:
        result, errors = prepare_draft_prompt(self.draft_input(), expected_source_hash="a" * 64)

        self.assertEqual(errors, [])
        assert result is not None
        self.assertEqual(result["worker"], {"tool": "Agent", "model": WORKER_MODEL, "tools": []})
        self.assertIn("DELIVERY_DRAFT_INPUT=", result["prompt"])
        self.assertIn("Do not call tools", result["prompt"])
        self.assertEqual(result["schema"]["properties"]["content"]["required"], ["type", "subject", "body"])

    def test_prompt_requires_hash_from_trusted_snapshot(self) -> None:
        result, errors = prepare_draft_prompt(self.draft_input(), expected_source_hash="trusted")

        self.assertIsNone(result)
        self.assertEqual(errors, ["input: source_hash does not match trusted snapshot"])

    def test_prompt_rechecks_worker_patch_for_secrets(self) -> None:
        draft_input = self.draft_input()
        draft_input["worker_patch"] = "+OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyz123456"

        result, errors = prepare_draft_prompt(draft_input, expected_source_hash="a" * 64)

        self.assertIsNone(result)
        self.assertIn("input: worker_patch contains secret-like content", errors)

    def test_validated_worker_output_is_returned(self) -> None:
        output, errors = validate_draft_output(
            self.draft_input(), self.valid_output(), expected_source_hash="a" * 64
        )

        self.assertEqual(errors, [])
        self.assertEqual(output, {"status": "VALIDATED", "verification": "structure_only", "draft": self.valid_output()})

    def test_prompt_rejects_changed_paths_that_differ_from_snapshot(self) -> None:
        snapshot = {"source_hash": "a" * 64, "changed_paths": ["other.py"]}

        result, errors = prepare_draft_prompt(self.draft_input(), expected_source_hash="a" * 64, snapshot=snapshot)

        self.assertIsNone(result)
        self.assertEqual(errors, ["input: changed_paths do not match trusted snapshot"])

    def test_privileged_worker_output_is_rejected(self) -> None:
        invalid = self.valid_output()
        invalid["content"] = {"type": "feat", "subject": "配送契約を追加", "body": "", "commands": ["git push"]}

        output, errors = validate_draft_output(self.draft_input(), invalid, expected_source_hash="a" * 64)

        self.assertIsNone(output)
        self.assertIn("delivery draft contains privileged fields: content.commands", errors)

    def test_pair_validation_requires_parent_claim_evidence(self) -> None:
        skeleton = claim_evidence_skeleton(self.valid_output(), expected_source_hash="a" * 64)
        self.assertEqual(skeleton["status"], "pending")

        output, errors = validate_draft_output(
            self.draft_input(), self.valid_output(), expected_source_hash="a" * 64,
            verified_claim_evidence=skeleton,
        )
        self.assertIsNone(output)
        self.assertIn("verified claim evidence is required for DRAFT_READY", errors)

        output, errors = validate_draft_output(
            self.draft_input(), self.valid_output(), expected_source_hash="a" * 64,
            verified_claim_evidence={**skeleton, "status": "pass"},
        )
        self.assertIsNone(output)
        self.assertIn("claim evidence checks must be a non-empty list of strings", errors)

        output, errors = validate_draft_output(
            self.draft_input(), self.valid_output(), expected_source_hash="a" * 64,
            verified_claim_evidence={**skeleton, "status": "pass", "checks": ["diff read: app.py adds delivery contract"]},
        )
        self.assertEqual(errors, [])
        self.assertEqual(output, {"status": "VALIDATED", "verification": "claim_verified", "draft": self.valid_output()})

    def test_cli_blocks_invalid_output_without_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "input.json"
            output_path = Path(directory) / "output.json"
            input_path.write_text(json.dumps(self.draft_input()), encoding="utf-8")
            output_path.write_text(json.dumps({"status": "DRAFT_READY"}), encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "draft_delivery_message.py"), "validate",
                 str(input_path), str(output_path), "--expected-source-hash", "a" * 64],
                capture_output=True, text=True, check=False,
            )

        self.assertEqual(result.returncode, 3)
        self.assertEqual(json.loads(result.stdout)["status"], "DRAFT_BLOCKED")


if __name__ == "__main__":
    unittest.main()
