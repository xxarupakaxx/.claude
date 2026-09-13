from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from agent_delivery_lifecycle import (  # noqa: E402
    delivery_draft_content_hash,
    next_action,
    route_delivery_draft,
    route_work_packet,
    validate_artifact,
    validate_delivery_draft_pair,
)


ZERO_FACTORS = {
    "ambiguity": 0,
    "blast_radius": 0,
    "dependency_coupling": 0,
    "verification_difficulty": 0,
    "failure_risk": 0,
    "context_volume": 0,
}
ALL_MODELS = ["gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol"]


def valid_work_packet() -> dict[str, object]:
    return {
        "artifact_id": "wp-1", "source_hash": "abc", "objective": "edit",
        "scope": ["core"], "out_of_scope": ["docs"], "owned_paths": ["core"],
        "acceptance_ids": ["A1"], "constraints": [],
        "capability_class": "Fast", "safety_decision_id": "safe-1",
        "side_effects_requested": [], "external_write_targets": [],
        "approval_required": False, "approval_evidence": [], "dry_run_required": False,
        "baseline": ["current behavior captured"],
        "reality_contract": ["validate against current source"],
        "verification": ["unit test"],
        "dependencies": ["none"],
        "handoff_requirements": ["report files and tests"],
        "reviewer_focus": ["contract transitions"],
        "journey_scenarios": ["happy path"],
        "negative_paths": ["invalid artifact"],
        "completion_target": "implemented",
    }


def valid_evidence_bundle() -> dict[str, object]:
    return {
        "artifact_id": "eb-1", "source_hash": "abc",
        "acceptance_evidence": ["A1|PASS|source:task:90_verification.md#L1"],
        "tests": ["python3 -m unittest tests.test_agent_delivery_lifecycle"],
        "findings": [], "residual_risks": [],
        "writes_performed": ["core"],
        "safety_decision_id": "safe-1",
        "policy_source": "AGENTS.md",
        "lineage": ["wp-1"],
        "journey_evidence": ["happy path covered"],
        "negative_path_evidence": ["invalid artifact covered"],
        "completion_state": "implemented",
    }


class RoutingTest(unittest.TestCase):
    def test_nontrivial_delivery_draft_routes_to_luna_without_tools(self) -> None:
        decision = route_delivery_draft(
            requires_summary=True,
            available_models=ALL_MODELS,
        )

        self.assertEqual(
            (decision.status, decision.handler, decision.model, decision.reasoning_effort),
            ("READY", "FAST_WORKER", "gpt-5.6-luna", "medium"),
        )
        self.assertEqual(decision.allowed_tools, ())

    def test_unavailable_luna_returns_delivery_draft_to_lead(self) -> None:
        decision = route_delivery_draft(
            requires_summary=True,
            available_models=["gpt-5.6-terra"],
        )

        self.assertEqual((decision.status, decision.handler, decision.model), ("LEAD_REQUIRED", "LEAD", None))

    def test_deterministic_local_uses_no_model(self) -> None:
        decision = route_work_packet(ZERO_FACTORS, deterministic_local=True)
        self.assertEqual((decision.route_id, decision.capability_class), ("fast-track", "Local"))
        self.assertIsNone(decision.model)

    def test_low_risk_work_routes_to_luna(self) -> None:
        factors = {**ZERO_FACTORS, "ambiguity": 1, "verification_difficulty": 1}
        decision = route_work_packet(factors, available_models=ALL_MODELS)
        self.assertEqual((decision.route_id, decision.capability_class), ("fast-track", "Fast"))
        self.assertEqual((decision.model, decision.reasoning_effort), ("gpt-5.6-luna", "medium"))

    def test_medium_work_routes_to_terra(self) -> None:
        factors = {**ZERO_FACTORS, "ambiguity": 2, "blast_radius": 2, "context_volume": 2}
        decision = route_work_packet(factors, available_models=ALL_MODELS)
        self.assertEqual((decision.route_id, decision.capability_class), ("prd-flow", "Standard"))
        self.assertEqual(decision.model, "gpt-5.6-terra")

    def test_large_work_routes_to_multi_packet_sol(self) -> None:
        factors = {axis: 2 for axis in ZERO_FACTORS}
        decision = route_work_packet(factors, work_packet_count=2, available_models=ALL_MODELS)
        self.assertEqual((decision.route_id, decision.capability_class), ("multi-packet-flow", "Heavy"))
        self.assertEqual(decision.model, "gpt-5.6-sol")

    def test_safety_trigger_forces_judgment(self) -> None:
        decision = route_work_packet(
            ZERO_FACTORS, safety_triggers=["external_write"], available_models=ALL_MODELS
        )
        self.assertEqual(decision.capability_class, "Judgment")
        self.assertEqual((decision.model, decision.reasoning_effort), ("gpt-5.6-sol", "max"))

    def test_unavailable_required_model_fails_closed(self) -> None:
        decision = route_work_packet(
            ZERO_FACTORS,
            safety_triggers=["billing_change"],
            available_models=["gpt-5.6-luna"],
        )
        self.assertEqual(decision.status, "ROUTING_BLOCKED")
        self.assertIsNone(decision.model)

    def test_unknown_axis_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            route_work_packet({**ZERO_FACTORS, "file_count": 2})

    def test_nonlocal_route_requires_runtime_roster(self) -> None:
        decision = route_work_packet({**ZERO_FACTORS, "ambiguity": 1})
        self.assertEqual(decision.status, "ROUTING_BLOCKED")
        self.assertIn("model_roster_missing", decision.reasons)

    def test_score_boundaries_are_stable(self) -> None:
        score_four = {**ZERO_FACTORS, "ambiguity": 1, "blast_radius": 1, "dependency_coupling": 1, "verification_difficulty": 1}
        score_five = {**score_four, "context_volume": 1}
        score_ten = {**ZERO_FACTORS, "blast_radius": 2, "dependency_coupling": 2, "verification_difficulty": 2, "context_volume": 2, "failure_risk": 2}
        score_eleven = {**score_ten, "ambiguity": 1}
        self.assertEqual(route_work_packet(score_four, available_models=ALL_MODELS).capability_class, "Fast")
        self.assertEqual(route_work_packet(score_five, available_models=ALL_MODELS).capability_class, "Standard")
        self.assertEqual(route_work_packet(score_ten, available_models=ALL_MODELS).capability_class, "Heavy")
        self.assertEqual(route_work_packet(score_eleven, available_models=ALL_MODELS).route_id, "prd-flow")
        self.assertEqual(
            route_work_packet(score_eleven, work_packet_count=2, available_models=ALL_MODELS).route_id,
            "multi-packet-flow",
        )

    def test_judgment_boundaries_and_invalid_inputs(self) -> None:
        for axis in ("ambiguity", "failure_risk"):
            decision = route_work_packet({**ZERO_FACTORS, axis: 3}, available_models=ALL_MODELS)
            self.assertEqual(decision.capability_class, "Judgment")
        with self.assertRaises(ValueError):
            route_work_packet(ZERO_FACTORS, work_packet_count=0)
        with self.assertRaises(ValueError):
            route_work_packet(ZERO_FACTORS, safety_triggers=["unknown"])


class ArtifactContractTest(unittest.TestCase):
    def test_delivery_draft_input_requires_bound_source_fields(self) -> None:
        errors = validate_artifact("delivery_draft_input", {"draft_id": "draft-1"})

        self.assertIn("missing required field: source_hash", errors)

    def test_delivery_draft_rejects_unknown_kind(self) -> None:
        payload = {
            "draft_id": "draft-1", "draft_kind": "push", "source_hash": "abc",
            "changed_paths": [], "evidence_bundle_id": "eb-1", "acceptance_ids": [],
            "test_ids": [], "residual_risk_ids": [], "template_sections": [],
            "policy_source": "AGENTS.md",
        }

        self.assertIn(
            "draft_kind must be commit or pull_request",
            validate_artifact("delivery_draft_input", payload),
        )

    def test_delivery_draft_output_rejects_unknown_status(self) -> None:
        draft_input = {
            "draft_id": "draft-1", "draft_kind": "commit", "source_hash": "abc",
            "changed_paths": ["app.py"], "evidence_bundle_id": "eb-1",
            "acceptance_ids": ["A1"], "test_ids": ["T1"], "residual_risk_ids": [],
            "template_sections": [], "policy_source": "AGENTS.md",
        }
        output = {
            "draft_id": "draft-1", "draft_kind": "commit", "source_hash": "abc",
            "status": "APPROVED", "claim_references": ["A1", "T1"],
            "content": {"type": "feat", "subject": "配送契約を追加", "body": ""},
        }

        self.assertIn(
            "status must be DRAFT_READY or DRAFT_BLOCKED",
            validate_delivery_draft_pair(draft_input, output, expected_source_hash="abc"),
        )

    def test_delivery_draft_rejects_claims_outside_bound_evidence(self) -> None:
        draft_input = {
            "draft_id": "draft-1", "draft_kind": "commit", "source_hash": "abc",
            "changed_paths": ["app.py"], "evidence_bundle_id": "eb-1",
            "acceptance_ids": ["A1"], "test_ids": ["T1"],
            "residual_risk_ids": ["R1"], "template_sections": [],
            "policy_source": "AGENTS.md",
        }
        output = {
            "draft_id": "draft-1", "draft_kind": "commit", "source_hash": "abc",
            "status": "DRAFT_READY", "claim_references": ["A1", "T-fabricated"],
            "content": {"type": "feat", "subject": "配送契約を追加", "body": ""},
        }

        self.assertIn(
            "claim_references contain unbound evidence: T-fabricated",
            validate_delivery_draft_pair(draft_input, output, expected_source_hash="abc"),
        )

    def test_delivery_draft_rejects_source_hash_drift(self) -> None:
        draft_input = {
            "draft_id": "draft-1", "draft_kind": "commit", "source_hash": "before",
            "changed_paths": ["app.py"], "evidence_bundle_id": "eb-1",
            "acceptance_ids": [], "test_ids": [], "residual_risk_ids": [],
            "template_sections": [], "policy_source": "AGENTS.md",
        }
        output = {
            "draft_id": "draft-1", "draft_kind": "commit", "source_hash": "after",
            "status": "DRAFT_READY", "claim_references": [],
            "content": {"type": "fix", "subject": "差分を修正", "body": ""},
        }

        self.assertIn(
            "source_hash does not match draft input",
            validate_delivery_draft_pair(draft_input, output, expected_source_hash="before"),
        )

    def test_commit_draft_rejects_subject_over_seventy_characters(self) -> None:
        draft_input = {
            "draft_id": "draft-1", "draft_kind": "commit", "source_hash": "abc",
            "changed_paths": [], "evidence_bundle_id": "eb-1", "acceptance_ids": [],
            "test_ids": [], "residual_risk_ids": [], "template_sections": [],
            "policy_source": "AGENTS.md",
        }
        output = {
            "draft_id": "draft-1", "draft_kind": "commit", "source_hash": "abc",
            "status": "DRAFT_READY", "claim_references": [],
            "content": {"type": "feat", "subject": "あ" * 71, "body": ""},
        }

        self.assertIn(
            "commit subject must be 70 characters or fewer",
            validate_delivery_draft_pair(draft_input, output, expected_source_hash="abc"),
        )

    def test_commit_draft_requires_japanese_subject(self) -> None:
        draft_input = {
            "draft_id": "draft-1", "draft_kind": "commit", "source_hash": "abc",
            "changed_paths": ["app.py"], "evidence_bundle_id": "eb-1",
            "acceptance_ids": [], "test_ids": [], "residual_risk_ids": [],
            "template_sections": [], "policy_source": "AGENTS.md",
        }
        output = {
            "draft_id": "draft-1", "draft_kind": "commit", "source_hash": "abc",
            "status": "DRAFT_READY", "claim_references": ["app.py"],
            "content": {"type": "feat", "subject": "add delivery adapter", "body": ""},
        }

        self.assertIn(
            "commit subject must include Japanese text",
            validate_delivery_draft_pair(draft_input, output, expected_source_hash="abc"),
        )

    def test_pr_draft_requires_canonical_and_template_sections(self) -> None:
        draft_input = {
            "draft_id": "draft-2", "draft_kind": "pull_request", "source_hash": "abc",
            "changed_paths": [], "evidence_bundle_id": "eb-1", "acceptance_ids": [],
            "test_ids": [], "residual_risk_ids": [], "template_sections": ["security"],
            "policy_source": "AGENTS.md",
        }
        output = {
            "draft_id": "draft-2", "draft_kind": "pull_request", "source_hash": "abc",
            "status": "DRAFT_READY", "claim_references": [],
            "content": {"title": "配送契約を追加", "sections": {"summary": "概要"}},
        }

        errors = validate_delivery_draft_pair(
            draft_input, output, expected_source_hash="abc"
        )

        self.assertIn("PR sections are missing: impact, out_of_scope, residual_risks, security, tests, trade_off, why", errors)

    def test_delivery_draft_cannot_request_tools_or_approval(self) -> None:
        draft_input = {
            "draft_id": "draft-1", "draft_kind": "commit", "source_hash": "abc",
            "changed_paths": [], "evidence_bundle_id": "eb-1", "acceptance_ids": [],
            "test_ids": [], "residual_risk_ids": [], "template_sections": [],
            "policy_source": "AGENTS.md",
        }
        output = {
            "draft_id": "draft-1", "draft_kind": "commit", "source_hash": "abc",
            "status": "DRAFT_READY", "claim_references": [], "tools": ["git"],
            "approval_state": "approved",
            "content": {"type": "feat", "subject": "配送契約を追加", "body": ""},
        }

        self.assertIn(
            "delivery draft contains privileged fields: approval_state, tools",
            validate_delivery_draft_pair(draft_input, output, expected_source_hash="abc"),
        )

    def test_delivery_draft_rejects_nested_privileged_fields(self) -> None:
        draft_input = {
            "draft_id": "draft-1", "draft_kind": "commit", "source_hash": "abc",
            "changed_paths": ["app.py"], "evidence_bundle_id": "eb-1",
            "acceptance_ids": [], "test_ids": [], "residual_risk_ids": [],
            "template_sections": [], "policy_source": "AGENTS.md",
        }
        output = {
            "draft_id": "draft-1", "draft_kind": "commit", "source_hash": "abc",
            "status": "DRAFT_READY", "claim_references": ["app.py"],
            "content": {
                "type": "feat", "subject": "配送契約を追加", "body": "",
                "commands": ["git push"],
            },
        }

        self.assertIn(
            "delivery draft contains privileged fields: content.commands",
            validate_delivery_draft_pair(draft_input, output, expected_source_hash="abc"),
        )

    def test_delivery_draft_rejects_non_string_claim_reference(self) -> None:
        draft_input = {
            "draft_id": "draft-1", "draft_kind": "commit", "source_hash": "abc",
            "changed_paths": ["app.py"], "evidence_bundle_id": "eb-1",
            "acceptance_ids": [], "test_ids": [], "residual_risk_ids": [],
            "template_sections": [], "policy_source": "AGENTS.md",
        }
        output = {
            "draft_id": "draft-1", "draft_kind": "commit", "source_hash": "abc",
            "status": "DRAFT_READY", "claim_references": [{"id": "app.py"}],
            "content": {"type": "feat", "subject": "配送契約を追加", "body": ""},
        }

        self.assertIn(
            "claim_references items must be strings",
            validate_delivery_draft_pair(draft_input, output, expected_source_hash="abc"),
        )

    def test_delivery_draft_rejects_untrusted_source_hash(self) -> None:
        draft_input = {
            "draft_id": "draft-1", "draft_kind": "commit", "source_hash": "worker-hash",
            "changed_paths": ["app.py"], "evidence_bundle_id": "eb-1",
            "acceptance_ids": [], "test_ids": [], "residual_risk_ids": [],
            "template_sections": [], "policy_source": "AGENTS.md",
        }
        output = {
            "draft_id": "draft-1", "draft_kind": "commit", "source_hash": "worker-hash",
            "status": "DRAFT_READY", "claim_references": ["app.py"],
            "content": {"type": "feat", "subject": "配送契約を追加", "body": ""},
        }

        self.assertIn(
            "source_hash does not match trusted snapshot",
            validate_delivery_draft_pair(
                draft_input, output, expected_source_hash="trusted-snapshot-hash"
            ),
        )

    def test_ready_draft_requires_claim_references(self) -> None:
        draft_input = {
            "draft_id": "draft-1", "draft_kind": "commit", "source_hash": "abc",
            "changed_paths": ["app.py"], "evidence_bundle_id": "eb-1",
            "acceptance_ids": [], "test_ids": [], "residual_risk_ids": [],
            "template_sections": [], "policy_source": "AGENTS.md",
        }
        output = {
            "draft_id": "draft-1", "draft_kind": "commit", "source_hash": "abc",
            "status": "DRAFT_READY", "claim_references": [],
            "content": {"type": "feat", "subject": "配送契約を追加", "body": ""},
        }

        self.assertIn(
            "claim_references are required for DRAFT_READY",
            validate_delivery_draft_pair(draft_input, output, expected_source_hash="abc"),
        )

    def test_delivery_draft_rejects_unknown_content_fields_and_multiline_title(self) -> None:
        draft_input = {
            "draft_id": "draft-2", "draft_kind": "pull_request", "source_hash": "abc",
            "changed_paths": ["app.py"], "evidence_bundle_id": "eb-1",
            "acceptance_ids": [], "test_ids": [], "residual_risk_ids": [],
            "template_sections": [], "policy_source": "AGENTS.md",
        }
        sections = {name: "確認済み" for name in (
            "summary", "why", "trade_off", "out_of_scope", "impact", "tests",
            "residual_risks",
        )}
        output = {
            "draft_id": "draft-2", "draft_kind": "pull_request", "source_hash": "abc",
            "status": "DRAFT_READY", "claim_references": ["app.py"],
            "content": {"title": "安全な題名\n--body", "sections": sections, "extra": "x"},
        }

        errors = validate_delivery_draft_pair(
            draft_input, output, expected_source_hash="abc"
        )

        self.assertIn("PR title must be a single line without control characters", errors)
        self.assertIn("PR content contains unknown fields: extra", errors)

    def test_delivery_draft_rejects_unknown_top_level_and_reserved_aliases(self) -> None:
        draft_input = {
            "draft_id": "draft-1", "draft_kind": "commit", "source_hash": "abc",
            "changed_paths": ["app.py"], "evidence_bundle_id": "eb-1",
            "acceptance_ids": [], "test_ids": [], "residual_risk_ids": [],
            "template_sections": [], "policy_source": "AGENTS.md",
        }
        output = {
            "draft_id": "draft-1", "draft_kind": "commit", "source_hash": "abc",
            "status": "DRAFT_READY", "claim_references": ["app.py"],
            "tool": "git", "whatever": "x",
            "content": {"type": "feat", "subject": "配送契約を追加", "body": ""},
        }

        errors = validate_delivery_draft_pair(
            draft_input, output, expected_source_hash="abc"
        )

        self.assertIn("delivery draft contains privileged fields: tool", errors)
        self.assertIn("delivery draft contains unknown fields: tool, whatever", errors)

    def test_ready_draft_requires_content_hash_bound_semantic_review(self) -> None:
        draft_input = {
            "draft_id": "draft-1", "draft_kind": "commit", "source_hash": "abc",
            "changed_paths": ["app.py"], "evidence_bundle_id": "eb-1",
            "acceptance_ids": [], "test_ids": [], "residual_risk_ids": [],
            "template_sections": [], "policy_source": "AGENTS.md",
        }
        output = {
            "draft_id": "draft-1", "draft_kind": "commit", "source_hash": "abc",
            "status": "DRAFT_READY", "claim_references": ["app.py"],
            "content": {
                "type": "feat", "subject": "配送契約を追加",
                "body": "未検証のテストが通った",
            },
        }

        self.assertIn(
            "verified claim evidence is required for DRAFT_READY",
            validate_delivery_draft_pair(draft_input, output, expected_source_hash="abc"),
        )
        evidence = {
            "status": "pass",
            "source_hash": "abc",
            "content_hash": delivery_draft_content_hash(output),
            "claim_references": ["app.py"],
        }
        self.assertEqual(
            validate_delivery_draft_pair(
                draft_input,
                output,
                expected_source_hash="abc",
                verified_claim_evidence=evidence,
            ),
            [],
        )

    def test_approved_prd_requires_independent_pass(self) -> None:
        payload = {
            "artifact_id": "prd-1",
            "source_hash": "abc",
            "objective": "ship",
            "scope": ["core"],
            "out_of_scope": [],
            "acceptance_ids": ["A1"],
            "review_status": "revise",
        }
        self.assertIn("review_status must be pass", validate_artifact("approved_prd", payload))

    def test_work_packet_blocks_missing_approval_evidence(self) -> None:
        payload = {
            "artifact_id": "wp-1",
            "source_hash": "abc",
            "objective": "publish",
            "scope": ["docs"],
            "acceptance_ids": ["A1"],
            "constraints": [],
            "capability_class": "Judgment",
            "safety_decision_id": "safe-1",
            "side_effects_requested": ["external_write"],
            "external_write_targets": ["GitHub"],
            "approval_required": True,
            "approval_evidence": [],
            "dry_run_required": True,
        }
        self.assertIn(
            "approval_evidence is required for approval-gated work",
            validate_artifact("work_packet", payload),
        )

    def test_work_packet_requires_cold_start_contract_fields(self) -> None:
        payload = {
            "artifact_id": "wp-cold-start",
            "source_hash": "abc",
            "objective": "edit",
            "scope": ["scripts/agent_delivery_lifecycle.py"],
            "acceptance_ids": ["A1"],
            "constraints": [],
            "capability_class": "Fast",
            "safety_decision_id": "safe-cold-start",
            "side_effects_requested": [],
            "external_write_targets": [],
            "approval_required": False,
            "approval_evidence": [],
            "dry_run_required": False,
        }

        errors = validate_artifact("work_packet", payload)

        for field in (
            "out_of_scope",
            "owned_paths",
            "baseline",
            "reality_contract",
            "verification",
            "dependencies",
            "handoff_requirements",
            "reviewer_focus",
            "journey_scenarios",
            "negative_paths",
            "completion_target",
        ):
            self.assertIn(f"missing required field: {field}", errors)

    def test_work_packet_requires_non_empty_cold_start_lists(self) -> None:
        payload = {
            **valid_work_packet(),
            "out_of_scope": [],
            "owned_paths": [],
            "baseline": [],
            "reality_contract": [],
            "verification": [],
            "dependencies": [],
            "handoff_requirements": [],
            "reviewer_focus": [],
            "journey_scenarios": [],
            "negative_paths": [],
        }

        errors = validate_artifact("work_packet", payload)

        for field in (
            "out_of_scope",
            "owned_paths",
            "baseline",
            "reality_contract",
            "verification",
            "dependencies",
            "handoff_requirements",
            "reviewer_focus",
            "journey_scenarios",
            "negative_paths",
        ):
            self.assertIn(f"{field} must be a non-empty list", errors)

    def test_work_packet_owned_paths_must_be_within_scope(self) -> None:
        payload = {
            **valid_work_packet(),
            "scope": ["scripts/"],
            "owned_paths": [
                "scripts/agent_delivery_lifecycle.py",
                "tests/test_agent_delivery_lifecycle.py",
            ],
        }

        self.assertIn(
            "owned_paths must be within scope: tests/test_agent_delivery_lifecycle.py",
            validate_artifact("work_packet", payload),
        )

    def test_work_packet_rejects_unsafe_relative_paths(self) -> None:
        for field, value in (
            ("scope", ["../outside"]),
            ("owned_paths", ["../outside"]),
            ("owned_paths", ["/absolute/path"]),
        ):
            with self.subTest(field=field, value=value):
                payload = {**valid_work_packet(), field: value}
                self.assertIn(
                    f"{field} must contain safe relative paths",
                    validate_artifact("work_packet", payload),
                )

    def test_scope_globs_have_portable_star_and_globstar_semantics(self) -> None:
        cases = (
            ("src/*.py", "src/a.py", False),
            ("src/*.py", "src/nested/a.py", True),
            ("src/**", "src/nested/a.py", False),
            (".", "src/nested/a.py", False),
            ("*", "src/nested/a.py", False),
            ("./src/**", "src/nested/a.py", False),
            ("src/**", "src/日本語 file.py", False),
        )
        for scope, owned, outside in cases:
            with self.subTest(scope=scope, owned=owned):
                errors = validate_artifact(
                    "work_packet",
                    {**valid_work_packet(), "scope": [scope], "owned_paths": [owned]},
                )
                self.assertEqual(
                    any(error.startswith("owned_paths must be within scope") for error in errors),
                    outside,
                )

    def test_scope_and_owned_directory_allow_one_trailing_slash(self) -> None:
        payload = {
            **valid_work_packet(),
            "scope": ["src/"],
            "owned_paths": ["src/package/"],
        }

        self.assertEqual(validate_artifact("work_packet", payload), [])

    def test_scope_and_owned_paths_reject_nonportable_or_ambiguous_paths(self) -> None:
        for field, path in (
            ("scope", "src/?.py"),
            ("scope", "src/[ab].py"),
            ("scope", "src/{a,b}.py"),
            ("scope", "src/***.py"),
            ("scope", "src//a.py"),
            ("scope", "src//"),
            ("scope", "src///"),
            ("scope", "././src"),
            ("owned_paths", "src/*.py"),
            ("owned_paths", "src//a.py"),
            ("owned_paths", "src//"),
            ("owned_paths", "././src/a.py"),
        ):
            with self.subTest(field=field, path=path):
                errors = validate_artifact(
                    "work_packet", {**valid_work_packet(), field: [path]}
                )
                self.assertIn(f"{field} must contain safe relative paths", errors)

    def test_scope_and_owned_paths_reject_controls_at_every_position(self) -> None:
        codepoints = (0x00, 0x0D, 0x1F, 0x7F, 0x85, 0x9F, 0x2028, 0x2029, 0xFEFF)
        for field in ("scope", "owned_paths"):
            for codepoint in codepoints:
                char = chr(codepoint)
                for path in (f"{char}src/a.py", f"src/a{char}b.py", f"src/a.py{char}"):
                    with self.subTest(field=field, codepoint=codepoint, path=path):
                        errors = validate_artifact(
                            "work_packet", {**valid_work_packet(), field: [path]}
                        )
                        self.assertIn(f"{field} must contain safe relative paths", errors)

    def test_work_packet_rejects_unknown_completion_target(self) -> None:
        payload = {**valid_work_packet(), "completion_target": "demoed"}

        self.assertIn(
            "completion_target must be one of: implemented, wired, piloted, effective, adopted",
            validate_artifact("work_packet", payload),
        )

    def test_work_packet_rejects_unknown_capability_class(self) -> None:
        payload = {**valid_work_packet(), "capability_class": "Automatic"}

        self.assertIn(
            "capability_class must be one of: Local, Fast, Standard, Heavy, Judgment",
            validate_artifact("work_packet", payload),
        )

    def test_contract_list_fields_reject_non_string_or_empty_entries(self) -> None:
        cases = (
            ("work_packet", {**valid_work_packet(), "scope": ["core", ""]}, "scope"),
            ("work_packet", {**valid_work_packet(), "owned_paths": ["core", 123]}, "owned_paths"),
            ("work_packet", {**valid_work_packet(), "approval_evidence": ["ok", "   "]}, "approval_evidence"),
            ("evidence_bundle", {**valid_evidence_bundle(), "acceptance_evidence": ["A1", None]}, "acceptance_evidence"),
            ("evidence_bundle", {**valid_evidence_bundle(), "findings": ["F1", {"severity": "IMPORTANT"}]}, "findings"),
        )

        for kind, payload, field in cases:
            with self.subTest(kind=kind, field=field):
                self.assertIn(
                    f"{field} items must be non-empty strings",
                    validate_artifact(kind, payload),
                )

    def test_high_completion_state_requires_bound_machine_evidence(self) -> None:
        payload = {**valid_evidence_bundle(), "completion_state": "effective"}

        self.assertIn(
            "completion_evidence is required for effective or adopted completion_state",
            validate_artifact("evidence_bundle", payload),
        )

    def test_high_completion_state_accepts_bound_machine_evidence(self) -> None:
        payload = {
            **valid_evidence_bundle(),
            "completion_state": "effective",
            "completion_evidence": {
                "status": "pass",
                "state": "effective",
                "source_hash": "abc",
                "checks": ["measurement:test-pass"],
            },
        }

        self.assertEqual(validate_artifact("evidence_bundle", payload), [])

    def test_work_packet_and_evidence_bundle_source_hash_must_match(self) -> None:
        decision = next_action({
            "state": "REVIEWED",
            "high_findings": 0,
            "artifact_payloads": {
                "work_packet": valid_work_packet(),
                "evidence_bundle": {**valid_evidence_bundle(), "source_hash": "def"},
            },
        })

        self.assertEqual((decision.action, decision.reason), ("BUILD_EVIDENCE_BUNDLE", "work_packet and evidence_bundle source_hash mismatch"))

    def test_evidence_bundle_requires_lineage_and_completion_state(self) -> None:
        payload = {
            "artifact_id": "eb-1",
            "source_hash": "abc",
            "acceptance_evidence": ["A1:test-pass"],
            "tests": ["python3 -m unittest tests.test_agent_delivery_lifecycle"],
            "findings": [],
            "residual_risks": [],
            "writes_performed": ["scripts/agent_delivery_lifecycle.py"],
            "safety_decision_id": "safe-1",
            "policy_source": "AGENTS.md",
            "lineage": [],
            "journey_evidence": [],
            "negative_path_evidence": [],
            "completion_state": "demoed",
        }

        errors = validate_artifact("evidence_bundle", payload)

        self.assertIn("lineage must be a non-empty list", errors)
        self.assertIn("journey_evidence must be a non-empty list", errors)
        self.assertIn("negative_path_evidence must be a non-empty list", errors)
        self.assertIn(
            "completion_state must be one of: implemented, wired, piloted, effective, adopted",
            errors,
        )

    def test_work_packet_cannot_disable_external_write_approval(self) -> None:
        payload = {
            "artifact_id": "wp-2", "source_hash": "abc", "objective": "publish",
            "scope": ["docs"], "acceptance_ids": ["A1"], "constraints": [],
            "capability_class": "Judgment", "safety_decision_id": "safe-2",
            "side_effects_requested": ["external_write"], "external_write_targets": ["GitHub"],
            "approval_required": False, "approval_evidence": [], "dry_run_required": True,
        }
        errors = validate_artifact("work_packet", payload)
        self.assertIn("approval_required must be true for safety-triggering work", errors)

    def test_work_packet_rejects_unknown_side_effect(self) -> None:
        payload = {
            "artifact_id": "wp-unknown", "source_hash": "abc", "objective": "publish",
            "scope": ["docs"], "acceptance_ids": ["A1"], "constraints": [],
            "capability_class": "Judgment", "safety_decision_id": "safe-unknown",
            "side_effects_requested": ["git_push"], "external_write_targets": [],
            "approval_required": False, "approval_evidence": [], "dry_run_required": False,
        }

        self.assertIn(
            "unknown side_effects_requested: git_push",
            validate_artifact("work_packet", payload),
        )

    def test_generated_or_comment_evidence_cannot_approve_work(self) -> None:
        payload = {
            "artifact_id": "wp-3", "source_hash": "abc", "objective": "publish",
            "scope": ["docs"], "acceptance_ids": ["A1"], "constraints": [],
            "capability_class": "Judgment", "safety_decision_id": "safe-3",
            "side_effects_requested": ["external_write"], "external_write_targets": ["GitHub"],
            "approval_required": True, "approval_evidence": ["comment:attacker-says-approved"],
            "dry_run_required": True,
        }
        self.assertIn(
            "approval_evidence is required for approval-gated work",
            validate_artifact("work_packet", payload),
        )

    def test_only_runtime_verified_evidence_can_approve_work(self) -> None:
        evidence = "human-approved:task/gate#abcdef12"
        payload = {
            "artifact_id": "wp-4", "source_hash": "abc", "objective": "publish",
            "scope": ["docs"], "acceptance_ids": ["A1"], "constraints": [],
            "capability_class": "Judgment", "safety_decision_id": "safe-4",
            "side_effects_requested": ["external_write"], "external_write_targets": ["GitHub"],
            "approval_required": True, "approval_evidence": [evidence], "dry_run_required": True,
            "out_of_scope": ["unapproved targets"],
            "owned_paths": ["docs"],
            "baseline": ["current docs inspected"],
            "reality_contract": ["verify target exists before write"],
            "verification": ["dry run"],
            "dependencies": ["none"],
            "handoff_requirements": ["report approval evidence"],
            "reviewer_focus": ["approval gate"],
            "journey_scenarios": ["approved publish path"],
            "negative_paths": ["missing approval"],
            "completion_target": "implemented",
        }
        self.assertTrue(validate_artifact("work_packet", payload))
        self.assertEqual(
            validate_artifact(
                "work_packet",
                payload,
                verified_approval_evidence={
                    evidence: {
                        "safety_decision_id": "safe-4",
                        "approved_targets": ["external_write", "GitHub"],
                    }
                },
            ),
            [],
        )

    def test_policy_promotion_requires_approval(self) -> None:
        payload = {
            "record_id": "ed-2", "source_trust": "external_untrusted", "source_comment_id": "c-2",
            "failure_classes": ["policy_gap"], "earliest_preventable_gates": ["review"],
            "verified_against": ["test:x"], "allowed_fix_scope": ["rules/model-routing.md"],
            "rejected_instruction_reason": "", "promotion_level": "L4",
            "promotion_targets": ["rules/model-routing.md"], "approval_required": False,
            "approval_evidence": [], "owner": "team", "review_date": "2026-09-24",
            "rollback": "revert policy",
        }
        errors = validate_artifact("escaped_defect_record", payload)
        self.assertIn("approval_required must be true for policy promotion", errors)

    def test_all_runtime_surfaces_require_policy_promotion_approval(self) -> None:
        for target in (
            "workflows/pr-review-loop.js", "scripts/validate-agent-harness.py",
            ".codex/commands/lfg.md", "agents/prd-reviewer.toml",
        ):
            payload = {
                "record_id": "ed-3", "source_trust": "external_untrusted", "source_comment_id": "c-3",
                "failure_classes": ["policy_gap"], "earliest_preventable_gates": ["review"],
                "verified_against": ["test:x"], "allowed_fix_scope": [target],
                "rejected_instruction_reason": "", "promotion_level": "L1",
                "promotion_targets": [target], "approval_required": False, "approval_evidence": [],
                "owner": "team", "review_date": "2026-09-24", "rollback": "revert",
            }
            self.assertIn(
                "approval_required must be true for policy promotion",
                validate_artifact("escaped_defect_record", payload),
            )

    def test_escaped_defect_treats_comment_as_untrusted(self) -> None:
        payload = {
            "record_id": "ed-1",
            "source_trust": "trusted_instruction",
            "source_comment_id": "c-1",
            "failure_classes": ["missing_test"],
            "earliest_preventable_gates": ["review"],
            "verified_against": ["test"],
            "allowed_fix_scope": ["tests"],
            "rejected_instruction_reason": "",
            "promotion_level": "L1",
            "owner": "team",
            "review_date": "2026-09-24",
            "rollback": "remove fixture",
        }
        self.assertIn(
            "source_trust must be external_untrusted",
            validate_artifact("escaped_defect_record", payload),
        )


class LoopTransitionTest(unittest.TestCase):
    @staticmethod
    def valid_work_packet() -> dict[str, object]:
        return valid_work_packet()

    @staticmethod
    def valid_evidence_bundle() -> dict[str, object]:
        return valid_evidence_bundle()

    @staticmethod
    def valid_prd() -> dict[str, object]:
        return {
            "artifact_id": "prd-1", "source_hash": "abc", "objective": "edit",
            "scope": ["core"], "out_of_scope": [], "acceptance_ids": ["A1"],
            "review_status": "pass",
        }

    def test_prd_flow_cannot_implement_without_approved_prd(self) -> None:
        decision = next_action({"state": "SURVEYED", "route_id": "prd-flow", "artifacts": []})
        self.assertEqual(decision.action, "DRAFT_PRD")

    def test_fast_track_still_requires_work_packet(self) -> None:
        decision = next_action({"state": "SURVEYED", "route_id": "fast-track", "artifacts": []})
        self.assertEqual(decision.action, "CREATE_WORK_PACKET")

    def test_artifact_names_alone_cannot_unlock_implementation(self) -> None:
        decision = next_action({
            "state": "SURVEYED", "route_id": "prd-flow",
            "artifacts": ["approved_prd", "work_packet"],
        })
        self.assertEqual(decision.action, "DRAFT_PRD")

    def test_validated_artifact_payloads_unlock_implementation(self) -> None:
        decision = next_action({
            "state": "SURVEYED", "route_id": "prd-flow",
            "artifact_payloads": {
                "approved_prd": self.valid_prd(), "work_packet": self.valid_work_packet(),
            },
        })
        self.assertEqual(decision.action, "IMPLEMENT")

    def test_prd_flow_rebuilds_packet_with_unrelated_or_duplicate_acceptance(self) -> None:
        for acceptance_ids in (["A2"], ["A1", "A1"]):
            with self.subTest(acceptance_ids=acceptance_ids):
                decision = next_action({
                    "state": "SURVEYED", "route_id": "prd-flow",
                    "artifact_payloads": {
                        "approved_prd": self.valid_prd(),
                        "work_packet": {
                            **self.valid_work_packet(),
                            "acceptance_ids": acceptance_ids,
                        },
                    },
                })

                self.assertEqual(decision.action, "CREATE_WORK_PACKET")

        duplicate_prd = {**self.valid_prd(), "acceptance_ids": ["A1", "A1"]}
        decision = next_action({
            "state": "SURVEYED", "route_id": "prd-flow",
            "artifact_payloads": {
                "approved_prd": duplicate_prd,
                "work_packet": self.valid_work_packet(),
            },
        })
        self.assertEqual(decision.action, "CREATE_WORK_PACKET")

    def test_prd_flow_binds_packet_scope_and_explicit_exclusions(self) -> None:
        cases = (
            ({"scope": ["other"], "owned_paths": ["other/file.py"]}, "outside"),
            ({"scope": ["core"], "owned_paths": ["core/private.py"]}, "excluded"),
            ({"scope": ["core/private.py"], "owned_paths": ["core/private.py"]}, "glob excluded"),
        )
        for packet_updates, label in cases:
            with self.subTest(label=label):
                exclusion = "path:core/*.py" if label == "glob excluded" else "core/private.py"
                prd = {**self.valid_prd(), "out_of_scope": [exclusion]}
                packet = {**self.valid_work_packet(), **packet_updates}
                decision = next_action({
                    "state": "SURVEYED", "route_id": "prd-flow",
                    "artifact_payloads": {"approved_prd": prd, "work_packet": packet},
                })
                self.assertEqual(decision.action, "CREATE_WORK_PACKET")

    def test_prd_flow_ignores_prose_out_of_scope_and_does_not_bind_source_hashes(self) -> None:
        prd = {
            **self.valid_prd(),
            "source_hash": "prd-own-source",
            "out_of_scope": [
                "\x85N/A: 認証や\r課金は今回の対象外",
                "\ufeffN/A: 通常の説明文",
            ],
        }
        decision = next_action({
            "state": "SURVEYED", "route_id": "multi-packet-flow",
            "artifact_payloads": {
                "approved_prd": prd,
                "work_packet": self.valid_work_packet(),
            },
        })

        self.assertEqual(decision.action, "IMPLEMENT")

    def test_prd_flow_rejects_controls_in_explicit_out_of_scope_before_stripping(self) -> None:
        for exclusion in ("path:core/a\x85", "path: \x1ccore/a", "core/a\ufeff"):
            with self.subTest(exclusion=exclusion):
                decision = next_action({
                    "state": "SURVEYED", "route_id": "prd-flow",
                    "artifact_payloads": {
                        "approved_prd": {**self.valid_prd(), "out_of_scope": [exclusion]},
                        "work_packet": self.valid_work_packet(),
                    },
                })
                self.assertEqual(decision.action, "CREATE_WORK_PACKET")

    def test_prd_flow_rejects_unsupported_out_of_scope_glob(self) -> None:
        for exclusion in ("path:core/?.py", "path:core/[ab].py", "path:core/{a,b}.py"):
            with self.subTest(exclusion=exclusion):
                decision = next_action({
                    "state": "SURVEYED", "route_id": "prd-flow",
                    "artifact_payloads": {
                        "approved_prd": {
                            **self.valid_prd(),
                            "out_of_scope": [exclusion],
                        },
                        "work_packet": self.valid_work_packet(),
                    },
                })
                self.assertEqual(decision.action, "CREATE_WORK_PACKET")

    def test_safety_change_waits_for_human(self) -> None:
        decision = next_action({"state": "SURVEYED", "safety_trigger": True, "approval_state": "pending"})
        self.assertEqual(decision.status, "WAITING_HUMAN")

    def test_safety_trigger_array_and_external_targets_wait_for_evidence(self) -> None:
        for extra in (
            {"safety_triggers": ["external_write"]},
            {"external_write_targets": ["GitHub"]},
        ):
            decision = next_action({"state": "SURVEYED", "approval_state": "approved", **extra})
            self.assertEqual(decision.status, "WAITING_HUMAN")

    def test_unknown_requested_side_effect_fails_closed(self) -> None:
        decision = next_action(
            {
                "state": "SURVEYED",
                "approval_state": "approved",
                "side_effects_requested": ["git_push"],
            }
        )

        self.assertEqual(decision.status, "WAITING_HUMAN")

    def test_runtime_verified_evidence_unlocks_safety_transition(self) -> None:
        evidence = "user-validation:task/gate#abcdef12"
        decision = next_action(
            {
                "state": "SURVEYED", "route_id": "fast-track",
                "safety_triggers": ["external_write"], "approval_state": "approved",
                "approval_evidence": [evidence],
                "safety_decision_id": "safe-1",
                "artifact_payloads": {"work_packet": self.valid_work_packet()},
            },
            verified_approval_evidence={
                evidence: {
                    "safety_decision_id": "safe-1",
                    "approved_targets": ["external_write"],
                }
            },
        )
        self.assertEqual(decision.action, "IMPLEMENT")

    def test_review_findings_loop_back_to_fix(self) -> None:
        decision = next_action({"state": "REVIEWED", "high_findings": 2})
        self.assertEqual(decision.action, "FIX")

    def test_reviewed_fails_closed_without_review_findings_or_trusted_count(self) -> None:
        decision = next_action({
            "state": "REVIEWED",
            "artifact_payloads": {
                "work_packet": self.valid_work_packet(),
                "evidence_bundle": self.valid_evidence_bundle(),
            },
        })

        self.assertEqual((decision.status, decision.action), ("RUNNING", "REVIEW"))

    def test_reviewed_derives_high_findings_from_structured_review(self) -> None:
        decision = next_action({
            "state": "REVIEWED",
            "review_findings": [
                {"id": "R1", "severity": "MINOR"},
                {"id": "R2", "severity": "IMPORTANT"},
            ],
            "artifact_payloads": {
                "work_packet": self.valid_work_packet(),
                "evidence_bundle": self.valid_evidence_bundle(),
            },
        })

        self.assertEqual(decision.action, "FIX")

    def test_reviewed_fails_closed_when_review_count_mismatches_structure(self) -> None:
        decision = next_action({
            "state": "REVIEWED",
            "high_findings": 0,
            "review_findings": [{"id": "R1", "severity": "CRITICAL"}],
            "artifact_payloads": {
                "work_packet": self.valid_work_packet(),
                "evidence_bundle": self.valid_evidence_bundle(),
            },
        })

        self.assertEqual((decision.status, decision.action), ("RUNNING", "REVIEW"))

    def test_reviewed_delivers_when_completion_target_is_met(self) -> None:
        decision = next_action({
            "state": "REVIEWED",
            "high_findings": 0,
            "artifact_payloads": {
                "work_packet": {**self.valid_work_packet(), "completion_target": "piloted"},
                "evidence_bundle": {**self.valid_evidence_bundle(), "completion_state": "piloted"},
            },
        })

        self.assertEqual(decision.action, "DELIVER")

    def test_reviewed_rebuilds_bundle_for_noncanonical_or_wrong_acceptance(self) -> None:
        cases = (
            ["A1: verified"],
            ["A1|FAIL|source:task:90_verification.md#L1"],
            ["UNRELATED|PASS|source:task:proof.md#L1"],
            ["A1|PASS|source:task:proof/*.md#L1"],
            ["A1|PASS|source:task:././proof.md#L1"],
            [
                "A1|PASS|source:task:90_verification.md#L1",
                "A1|PASS|source:task:90_verification.md#L2",
            ],
        ) + tuple(
            [f"A1|PASS|source:task:proof{chr(codepoint)}.md#L1"]
            for codepoint in (0x0D, 0x1F, 0x7F, 0x85, 0x9F, 0x2028, 0x2029, 0xFEFF)
        )
        for acceptance_evidence in cases:
            with self.subTest(acceptance_evidence=acceptance_evidence):
                decision = next_action({
                    "state": "REVIEWED", "high_findings": 0,
                    "artifact_payloads": {
                        "work_packet": self.valid_work_packet(),
                        "evidence_bundle": {
                            **self.valid_evidence_bundle(),
                            "acceptance_evidence": acceptance_evidence,
                        },
                    },
                })
                self.assertEqual(decision.action, "BUILD_EVIDENCE_BUNDLE")

    def test_reviewed_rebuilds_bundle_for_wrong_lineage_safety_or_write_scope(self) -> None:
        cases = (
            {"lineage": ["another-packet"]},
            {"safety_decision_id": "safe-other"},
            {"writes_performed": ["core-other/file.py"]},
            {"writes_performed": ["N/A: no workspace writes", "core"]},
        )
        for evidence_updates in cases:
            with self.subTest(evidence_updates=evidence_updates):
                decision = next_action({
                    "state": "REVIEWED", "high_findings": 0,
                    "artifact_payloads": {
                        "work_packet": self.valid_work_packet(),
                        "evidence_bundle": {
                            **self.valid_evidence_bundle(),
                            **evidence_updates,
                        },
                    },
                })
                self.assertEqual(decision.action, "BUILD_EVIDENCE_BUNDLE")

    def test_reviewed_accepts_canonical_no_workspace_write_evidence(self) -> None:
        decision = next_action({
            "state": "REVIEWED", "high_findings": 0,
            "artifact_payloads": {
                "work_packet": self.valid_work_packet(),
                "evidence_bundle": {
                    **self.valid_evidence_bundle(),
                    "writes_performed": ["N/A: no workspace writes"],
                },
            },
        })

        self.assertEqual(decision.action, "DELIVER")

    def test_reviewed_wires_before_delivery_when_target_is_unmet(self) -> None:
        decision = next_action({
            "state": "REVIEWED",
            "high_findings": 0,
            "artifact_payloads": {
                "work_packet": {**self.valid_work_packet(), "completion_target": "piloted"},
                "evidence_bundle": {**self.valid_evidence_bundle(), "completion_state": "implemented"},
            },
        })

        self.assertEqual((decision.status, decision.action), ("RUNNING", "WIRE"))

    def test_reviewed_pilots_before_delivery_when_pilot_target_is_unmet(self) -> None:
        decision = next_action({
            "state": "REVIEWED",
            "high_findings": 0,
            "artifact_payloads": {
                "work_packet": {**self.valid_work_packet(), "completion_target": "piloted"},
                "evidence_bundle": {**self.valid_evidence_bundle(), "completion_state": "wired"},
            },
        })

        self.assertEqual((decision.status, decision.action), ("RUNNING", "PILOT"))

    def test_reviewed_measures_before_delivery_when_effectiveness_is_unmet(self) -> None:
        decision = next_action({
            "state": "REVIEWED",
            "high_findings": 0,
            "artifact_payloads": {
                "work_packet": {**self.valid_work_packet(), "completion_target": "effective"},
                "evidence_bundle": {**self.valid_evidence_bundle(), "completion_state": "piloted"},
            },
        })

        self.assertEqual((decision.status, decision.action), ("RUNNING", "MEASURE"))

    def test_reviewed_adopts_before_delivery_when_adoption_is_unmet(self) -> None:
        decision = next_action({
            "state": "REVIEWED",
            "high_findings": 0,
            "artifact_payloads": {
                "work_packet": {**self.valid_work_packet(), "completion_target": "adopted"},
                "evidence_bundle": {
                    **self.valid_evidence_bundle(),
                    "completion_state": "effective",
                    "completion_evidence": {
                        "status": "pass",
                        "state": "effective",
                        "source_hash": "abc",
                        "checks": ["measurement:test-pass"],
                    },
                },
            },
        })

        self.assertEqual((decision.status, decision.action), ("RUNNING", "ADOPT"))

    def test_reviewed_refuses_effective_label_without_machine_evidence(self) -> None:
        decision = next_action({
            "state": "REVIEWED",
            "high_findings": 0,
            "artifact_payloads": {
                "work_packet": {**self.valid_work_packet(), "completion_target": "effective"},
                "evidence_bundle": {**self.valid_evidence_bundle(), "completion_state": "effective"},
            },
        })

        self.assertEqual((decision.status, decision.action), ("RUNNING", "BUILD_EVIDENCE_BUNDLE"))

    def test_retry_limit_stops_loop(self) -> None:
        decision = next_action({"state": "REVIEWED", "retry_count": 3, "max_retries": 3})
        self.assertEqual(decision.status, "WAITING_HUMAN")

    def test_escaped_defect_enters_learning_loop(self) -> None:
        decision = next_action({"state": "DELIVERED", "escaped_defects": ["ed-1"]})
        self.assertEqual(decision.action, "RECORD_ESCAPED_DEFECT")

    def test_failed_replay_does_not_auto_promote(self) -> None:
        decision = next_action({"state": "REPLAYED", "replay_passed": False})
        self.assertEqual(decision.status, "WAITING_HUMAN")

    def test_policy_replay_waits_for_separate_promotion_approval(self) -> None:
        decision = next_action({
            "state": "REPLAYED", "replay_passed": True, "promotion_level": "L4",
            "promotion_targets": ["rules/model-routing.md"], "approval_state": "pending",
            "approval_evidence": [],
        })
        self.assertEqual(decision.status, "WAITING_HUMAN")


if __name__ == "__main__":
    unittest.main()
