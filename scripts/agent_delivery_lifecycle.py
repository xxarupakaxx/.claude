#!/usr/bin/env python3
"""Deterministic contracts for the agent delivery lifecycle and its bounded loop."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


AXES = (
    "ambiguity",
    "blast_radius",
    "dependency_coupling",
    "verification_difficulty",
    "failure_risk",
    "context_volume",
)
MODEL_ROSTER = {
    "Fast": ("gpt-5.6-luna", "medium"),
    "Standard": ("gpt-5.6-terra", "high"),
    "Heavy": ("gpt-5.6-sol", "high"),
    "Judgment": ("gpt-5.6-sol", "max"),
}
CAPABILITY_CLASSES = ("Local", *MODEL_ROSTER)
SAFETY_TRIGGERS = {
    "external_write",
    "permission_change",
    "billing_change",
    "authentication_change",
    "destructive_action",
    "runtime_policy_change",
    "go_nogo_decision",
}
COMPLETION_STATES = ("implemented", "wired", "piloted", "effective", "adopted")
COMPLETION_ORDER = {state: index for index, state in enumerate(COMPLETION_STATES)}
HIGH_COMPLETION_STATES = {"effective", "adopted"}
NEXT_COMPLETION_ACTION = {
    "implemented": "WIRE",
    "wired": "PILOT",
    "piloted": "MEASURE",
    "effective": "ADOPT",
}
REVIEW_FINDING_SEVERITIES = {"CRITICAL", "IMPORTANT", "MINOR", "INFO"}
REVIEW_HIGH_FINDING_SEVERITIES = {"CRITICAL", "IMPORTANT"}
ARTIFACT_REQUIRED_FIELDS = {
    "delivery_draft_input": (
        "draft_id",
        "draft_kind",
        "source_hash",
        "changed_paths",
        "evidence_bundle_id",
        "acceptance_ids",
        "test_ids",
        "residual_risk_ids",
        "template_sections",
        "policy_source",
    ),
    "delivery_draft_output": (
        "draft_id",
        "draft_kind",
        "source_hash",
        "status",
        "claim_references",
        "content",
    ),
    "approved_prd": (
        "artifact_id",
        "source_hash",
        "objective",
        "scope",
        "out_of_scope",
        "acceptance_ids",
        "review_status",
    ),
    "work_packet": (
        "artifact_id",
        "source_hash",
        "objective",
        "scope",
        "out_of_scope",
        "owned_paths",
        "acceptance_ids",
        "constraints",
        "capability_class",
        "safety_decision_id",
        "side_effects_requested",
        "external_write_targets",
        "approval_required",
        "approval_evidence",
        "dry_run_required",
        "baseline",
        "reality_contract",
        "verification",
        "dependencies",
        "handoff_requirements",
        "reviewer_focus",
        "journey_scenarios",
        "negative_paths",
        "completion_target",
    ),
    "evidence_bundle": (
        "artifact_id",
        "source_hash",
        "acceptance_evidence",
        "tests",
        "findings",
        "residual_risks",
        "writes_performed",
        "safety_decision_id",
        "policy_source",
        "lineage",
        "journey_evidence",
        "negative_path_evidence",
        "completion_state",
    ),
    "escaped_defect_record": (
        "record_id",
        "source_trust",
        "source_comment_id",
        "failure_classes",
        "earliest_preventable_gates",
        "verified_against",
        "allowed_fix_scope",
        "rejected_instruction_reason",
        "promotion_level",
        "promotion_targets",
        "approval_required",
        "approval_evidence",
        "owner",
        "review_date",
        "rollback",
        "safety_decision_id",
    ),
}
LIST_FIELDS = {
    "changed_paths",
    "test_ids",
    "residual_risk_ids",
    "template_sections",
    "claim_references",
    "scope",
    "out_of_scope",
    "owned_paths",
    "acceptance_ids",
    "constraints",
    "baseline",
    "reality_contract",
    "verification",
    "dependencies",
    "handoff_requirements",
    "reviewer_focus",
    "journey_scenarios",
    "negative_paths",
    "side_effects_requested",
    "external_write_targets",
    "approval_evidence",
    "acceptance_evidence",
    "tests",
    "findings",
    "residual_risks",
    "writes_performed",
    "lineage",
    "journey_evidence",
    "negative_path_evidence",
    "failure_classes",
    "earliest_preventable_gates",
    "verified_against",
    "allowed_fix_scope",
    "promotion_targets",
}
WORK_PACKET_NON_EMPTY_LIST_FIELDS = {
    "scope",
    "out_of_scope",
    "owned_paths",
    "acceptance_ids",
    "baseline",
    "reality_contract",
    "verification",
    "dependencies",
    "handoff_requirements",
    "reviewer_focus",
    "journey_scenarios",
    "negative_paths",
}
EVIDENCE_BUNDLE_NON_EMPTY_LIST_FIELDS = {
    "acceptance_evidence",
    "tests",
    "writes_performed",
    "lineage",
    "journey_evidence",
    "negative_path_evidence",
}

POLICY_PROMOTION_PREFIXES = (
    "AGENTS.md", "agents/", "commands/", "context/", "hooks/", "ci/", "prompts/",
    "rules/", "scheduled-tasks/", "scripts/", "skills/", "workflows/",
)
APPROVAL_EVIDENCE = re.compile(
    r"^(?:human-approved|user-validation):[A-Za-z0-9._/-]+#[a-f0-9]{8,64}$"
)
ACCEPTANCE_EVIDENCE = re.compile(
    r"^(?P<id>[A-Za-z0-9][A-Za-z0-9._-]*)\|PASS\|source:"
    r"(?:task|workspace):(?P<path>[^|#\x00]+)#L[1-9]\d*(?:-L[1-9]\d*)?$"
)
NO_WORKSPACE_WRITES = "N/A: no workspace writes"
UNSAFE_ARTIFACT_CHARACTERS = re.compile(
    r"[\x00-\x1f\x7f-\x9f\u2028\u2029\ufeff]"
)
COMMIT_TYPES = {"feat", "fix", "docs", "refactor", "test", "chore", "perf", "build", "ci"}
PR_SECTIONS = {"summary", "why", "trade_off", "out_of_scope", "impact", "tests", "residual_risks"}
DRAFT_PRIVILEGED_FIELDS = {
    "tools", "commands", "approval_state", "approval_evidence", "side_effects_requested",
    "external_write_targets", "write_request",
}
DRAFT_PRIVILEGED_KEYS = {
    re.sub(r"[^a-z]", "", key.lower())
    for key in DRAFT_PRIVILEGED_FIELDS
} | {"tool", "command", "approval", "sideeffect", "externalwritetarget"}
COMPLETION_STATES_MESSAGE = ", ".join(COMPLETION_STATES)


@dataclass(frozen=True)
class RoutingDecision:
    status: str
    route_id: str
    capability_class: str
    model: str | None
    reasoning_effort: str | None
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class TransitionDecision:
    status: str
    action: str
    reason: str


@dataclass(frozen=True)
class DraftRoutingDecision:
    status: str
    handler: str
    model: str | None
    reasoning_effort: str | None
    reasons: tuple[str, ...]
    allowed_tools: tuple[str, ...] = ()


def _axis_values(factors: Mapping[str, Any]) -> dict[str, int]:
    unknown = sorted(set(factors) - set(AXES))
    if unknown:
        raise ValueError(f"unknown routing axes: {', '.join(unknown)}")
    values: dict[str, int] = {}
    for axis in AXES:
        value = factors.get(axis, 0)
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 3:
            raise ValueError(f"{axis} must be an integer from 0 to 3")
        values[axis] = value
    return values


def route_work_packet(
    factors: Mapping[str, Any],
    *,
    safety_triggers: Sequence[str] = (),
    deterministic_local: bool = False,
    work_packet_count: int = 1,
    available_models: Sequence[str] | None = None,
) -> RoutingDecision:
    values = _axis_values(factors)
    invalid_triggers = sorted(set(safety_triggers) - SAFETY_TRIGGERS)
    if invalid_triggers:
        raise ValueError(f"unknown safety triggers: {', '.join(invalid_triggers)}")
    if work_packet_count < 1:
        raise ValueError("work_packet_count must be positive")

    score = sum(values.values())
    peak = max(values.values())
    if safety_triggers:
        capability = "Judgment"
        reasons = ("safety_trigger", *sorted(set(safety_triggers)))
    elif values["ambiguity"] == 3 or values["failure_risk"] == 3:
        capability = "Judgment"
        reasons = ("forced_judgment",)
    elif deterministic_local and score == 0:
        capability = "Local"
        reasons = ("deterministic_local",)
    elif score <= 4 and peak <= 1:
        capability = "Fast"
        reasons = ("low_complexity",)
    elif score <= 9:
        capability = "Standard"
        reasons = ("bounded_complexity",)
    else:
        capability = "Heavy"
        reasons = ("high_complexity",)

    if work_packet_count > 1:
        route_id = "multi-packet-flow"
    elif capability in {"Local", "Fast"} and not safety_triggers:
        route_id = "fast-track"
    else:
        route_id = "prd-flow"

    if capability == "Local":
        return RoutingDecision("READY", route_id, capability, None, None, reasons)

    model, effort = MODEL_ROSTER[capability]
    if available_models is None:
        return RoutingDecision(
            "ROUTING_BLOCKED",
            route_id,
            capability,
            None,
            None,
            (*reasons, "model_roster_missing"),
        )
    if model not in available_models:
        return RoutingDecision(
            "ROUTING_BLOCKED",
            route_id,
            capability,
            None,
            None,
            (*reasons, f"model_unavailable:{model}"),
        )
    return RoutingDecision("READY", route_id, capability, model, effort, reasons)


def route_delivery_draft(
    *,
    requires_summary: bool,
    available_models: Sequence[str] | None = None,
) -> DraftRoutingDecision:
    """Choose local formatting or the tool-free Fast worker for a delivery draft."""
    if not requires_summary:
        return DraftRoutingDecision("READY", "LOCAL_TEMPLATE", None, None, ("deterministic",))
    model, effort = MODEL_ROSTER["Fast"]
    if available_models is None or model not in available_models:
        return DraftRoutingDecision(
            "LEAD_REQUIRED", "LEAD", None, None, (f"model_unavailable:{model}",)
        )
    return DraftRoutingDecision("READY", "FAST_WORKER", model, effort, ("summary_required",))


def _non_empty_list_errors(
    payload: Mapping[str, Any],
    fields: set[str],
) -> list[str]:
    return [
        f"{field} must be a non-empty list"
        for field in sorted(fields)
        if isinstance(payload.get(field), list) and not payload[field]
    ]


def _list_item_errors(payload: Mapping[str, Any], fields: set[str]) -> list[str]:
    return [
        f"{field} items must be non-empty strings"
        for field in sorted(fields)
        if isinstance(payload.get(field), list)
        and any(not isinstance(item, str) or not item.strip() for item in payload[field])
    ]


def _normalize_artifact_path(path: str, *, allow_directory: bool = False) -> str:
    normalized = path.removeprefix("./")
    if allow_directory and normalized.endswith("/") and not normalized.endswith("//"):
        return normalized[:-1]
    return normalized


def _artifact_path_is_safe(
    path: Any,
    *,
    allow_glob: bool,
    allow_root: bool,
    allow_directory: bool = False,
) -> bool:
    if not isinstance(path, str) or not path or path != path.strip():
        return False
    if UNSAFE_ARTIFACT_CHARACTERS.search(path) or "\\" in path or path.startswith("/"):
        return False
    normalized = _normalize_artifact_path(path, allow_directory=allow_directory)
    if normalized in {".", "*"}:
        return allow_root
    if not normalized or any(part in {"", ".", ".."} for part in normalized.split("/")):
        return False
    if re.search(r"[?\[\]{}]", normalized):
        return False
    star_runs = re.findall(r"\*+", normalized)
    return (allow_glob or not star_runs) and all(len(run) <= 2 for run in star_runs)


def _unsafe_relative_paths(payload: Mapping[str, Any], field: str) -> list[str]:
    value = payload.get(field)
    if not isinstance(value, list):
        return []
    return [
        item
        for item in value
        if isinstance(item, str)
        and item.strip()
        and not _artifact_path_is_safe(
            item,
            allow_glob=field == "scope",
            allow_root=field == "scope",
            allow_directory=True,
        )
    ]


def _scope_pattern_matches(pattern: str, path: str) -> bool:
    regex: list[str] = []
    index = 0
    while index < len(pattern):
        if pattern.startswith("**", index):
            regex.append(r"[\s\S]*")
            index += 2
        elif pattern[index] == "*":
            regex.append("[^/]*")
            index += 1
        else:
            regex.append(re.escape(pattern[index]))
            index += 1
    return re.fullmatch("".join(regex), path) is not None


def _scope_entry_covers_owned_path(scope_entry: str, owned_path: str) -> bool:
    scope_entry = _normalize_artifact_path(scope_entry, allow_directory=True)
    owned_path = _normalize_artifact_path(owned_path, allow_directory=True)
    if scope_entry in {".", "*"}:
        return True
    if "*" in scope_entry:
        return _scope_pattern_matches(scope_entry, owned_path)
    return owned_path == scope_entry or owned_path.startswith(f"{scope_entry}/")


def _owned_paths_outside_scope(payload: Mapping[str, Any]) -> list[str]:
    scope = payload.get("scope")
    owned_paths = payload.get("owned_paths")
    if not isinstance(scope, list) or not isinstance(owned_paths, list):
        return []
    scope_entries = [item for item in scope if isinstance(item, str) and item.strip()]
    return sorted(
        item
        for item in owned_paths
        if isinstance(item, str)
        and item.strip()
        and not any(
            _scope_entry_covers_owned_path(scope_entry, item)
            for scope_entry in scope_entries
        )
    )


def _duplicates(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    seen: set[str] = set()
    duplicates: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            continue
        if item in seen:
            duplicates.add(item)
        seen.add(item)
    return sorted(duplicates)


def _explicit_out_of_scope_path(value: Any) -> tuple[str | None, bool]:
    """Return an explicit path restriction without interpreting prose as a path."""
    if not isinstance(value, str):
        return None, False
    text = value.strip()
    if re.match(r"^[\s\ufeff]*N/A:", value):
        return None, True
    if UNSAFE_ARTIFACT_CHARACTERS.search(value):
        return text, False
    if text.startswith("path:"):
        candidate = text.removeprefix("path:").strip()
        return candidate, bool(candidate) and not _unsafe_relative_paths(
            {"scope": [candidate]}, "scope"
        )
    path_like = bool(
        re.fullmatch(r"[A-Za-z0-9._*?{}\[\]/-]+", text)
        and ("/" in text or "." in text or any(mark in text for mark in "*?[]{}"))
    )
    if not path_like:
        return None, True
    return text, not _unsafe_relative_paths({"scope": [text]}, "scope")


def validate_prd_work_packet_pair(
    approved_prd: Mapping[str, Any], work_packet: Mapping[str, Any]
) -> list[str]:
    """Validate the requirement-to-packet projection using snapshot data only."""
    errors: list[str] = []
    prd_ids = approved_prd.get("acceptance_ids")
    packet_ids = work_packet.get("acceptance_ids")
    for label, value in (("approved_prd", prd_ids), ("work_packet", packet_ids)):
        duplicates = _duplicates(value)
        if duplicates:
            errors.append(f"{label} acceptance_ids contain duplicates: {', '.join(duplicates)}")
    if isinstance(prd_ids, list) and isinstance(packet_ids, list):
        outside = sorted(set(packet_ids) - set(prd_ids))
        if outside:
            errors.append(f"work_packet acceptance_ids are outside approved_prd: {', '.join(outside)}")

    prd_scope = approved_prd.get("scope")
    packet_scope = work_packet.get("scope")
    if _unsafe_relative_paths(approved_prd, "scope"):
        errors.append("approved_prd scope must contain safe relative paths")
    if isinstance(prd_scope, list) and isinstance(packet_scope, list):
        allowed = [item for item in prd_scope if isinstance(item, str) and item.strip()]
        outside_scope = sorted(
            item
            for item in packet_scope
            if isinstance(item, str)
            and item.strip()
            and not any(_scope_entry_covers_owned_path(scope, item) for scope in allowed)
        )
        if outside_scope:
            errors.append(f"work_packet scope is outside approved_prd: {', '.join(outside_scope)}")

    exclusions: list[str] = []
    for value in approved_prd.get("out_of_scope", []):
        restriction, valid = _explicit_out_of_scope_path(value)
        if restriction is not None and not valid:
            errors.append(f"approved_prd out_of_scope path is unsafe: {value}")
        elif restriction is not None:
            exclusions.append(restriction)
    owned_paths = work_packet.get("owned_paths")
    if isinstance(packet_scope, list):
        conflicting_scope = sorted(
            item
            for item in packet_scope
            if isinstance(item, str)
            and any(
                _scope_entry_covers_owned_path(path, item)
                or _scope_entry_covers_owned_path(item, path)
                for path in exclusions
            )
        )
        if conflicting_scope:
            errors.append(
                f"work_packet scope conflicts with approved_prd out_of_scope: "
                f"{', '.join(conflicting_scope)}"
            )
    if isinstance(owned_paths, list):
        excluded = sorted(
            item
            for item in owned_paths
            if isinstance(item, str)
            and any(_scope_entry_covers_owned_path(path, item) for path in exclusions)
        )
        if excluded:
            errors.append(f"work_packet owned_paths are excluded by approved_prd: {', '.join(excluded)}")
    return errors


def validate_work_packet_evidence_pair(
    work_packet: Mapping[str, Any], evidence_bundle: Mapping[str, Any]
) -> list[str]:
    """Validate packet-to-evidence lineage without reading evidence files."""
    errors: list[str] = []
    if work_packet.get("source_hash") != evidence_bundle.get("source_hash"):
        errors.append("source_hash mismatch")
    if work_packet.get("safety_decision_id") != evidence_bundle.get("safety_decision_id"):
        errors.append("safety_decision_id mismatch")

    packet_ids = work_packet.get("acceptance_ids")
    duplicates = _duplicates(packet_ids)
    if duplicates:
        errors.append(f"work_packet acceptance_ids contain duplicates: {', '.join(duplicates)}")
    evidence_ids: list[str] = []
    entries = evidence_bundle.get("acceptance_evidence")
    if isinstance(entries, list):
        for entry in entries:
            match = ACCEPTANCE_EVIDENCE.fullmatch(entry) if isinstance(entry, str) else None
            if not match or not _artifact_path_is_safe(
                match.group("path"),
                allow_glob=False,
                allow_root=False,
            ):
                errors.append(f"acceptance_evidence is not canonical: {entry}")
                continue
            evidence_ids.append(match.group("id"))
    evidence_duplicates = _duplicates(evidence_ids)
    if evidence_duplicates:
        errors.append(f"acceptance_evidence contains duplicate IDs: {', '.join(evidence_duplicates)}")
    if isinstance(packet_ids, list) and set(evidence_ids) != set(packet_ids):
        errors.append("acceptance_evidence IDs must exactly match work_packet acceptance_ids")

    lineage = evidence_bundle.get("lineage")
    if isinstance(lineage, list) and work_packet.get("artifact_id") not in lineage:
        errors.append("lineage does not include work_packet artifact_id")

    writes = evidence_bundle.get("writes_performed")
    owned_paths = work_packet.get("owned_paths")
    if isinstance(writes, list) and isinstance(owned_paths, list):
        if NO_WORKSPACE_WRITES in writes:
            if writes != [NO_WORKSPACE_WRITES]:
                errors.append("no-workspace-writes marker must not be mixed with paths")
        else:
            if _duplicates(writes):
                errors.append("writes_performed contains duplicate paths")
            invalid_writes = sorted(
                item
                for item in writes
                if isinstance(item, str)
                and (
                    bool(_unsafe_relative_paths({"owned_paths": [item]}, "owned_paths"))
                    or not any(_scope_entry_covers_owned_path(path, item) for path in owned_paths)
                )
            )
            if invalid_writes:
                errors.append(f"writes_performed must be within owned_paths: {', '.join(invalid_writes)}")
    return errors


def _completion_value_error(field: str, value: Any) -> str | None:
    if value not in COMPLETION_STATES:
        return f"{field} must be one of: {COMPLETION_STATES_MESSAGE}"
    return None


def _valid_completion_evidence(payload: Mapping[str, Any]) -> bool:
    evidence = payload.get("completion_evidence")
    checks = evidence.get("checks") if isinstance(evidence, Mapping) else None
    return (
        isinstance(evidence, Mapping)
        and evidence.get("status") == "pass"
        and evidence.get("state") == payload.get("completion_state")
        and evidence.get("source_hash") == payload.get("source_hash")
        and isinstance(checks, list)
        and bool(checks)
        and all(isinstance(item, str) and item.strip() for item in checks)
    )


def validate_artifact(
    kind: str,
    payload: Mapping[str, Any],
    *,
    verified_approval_evidence: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[str]:
    required = ARTIFACT_REQUIRED_FIELDS.get(kind)
    if required is None:
        return [f"unknown artifact kind: {kind}"]
    errors = [f"missing required field: {field}" for field in required if field not in payload]
    for field in LIST_FIELDS.intersection(payload):
        if not isinstance(payload[field], list):
            errors.append(f"{field} must be a list")
    errors.extend(_list_item_errors(payload, LIST_FIELDS))
    if kind in {"delivery_draft_input", "delivery_draft_output"} and payload.get(
        "draft_kind"
    ) not in {"commit", "pull_request"}:
        errors.append("draft_kind must be commit or pull_request")
    if kind == "approved_prd" and payload.get("review_status") != "pass":
        errors.append("review_status must be pass")
    if kind == "escaped_defect_record":
        if payload.get("source_trust") != "external_untrusted":
            errors.append("source_trust must be external_untrusted")
        if payload.get("promotion_level") not in {"L0", "L1", "L2", "L3", "L4"}:
            errors.append("promotion_level must be L0 through L4")
        targets = payload.get("promotion_targets", [])
        policy_promotion = payload.get("promotion_level") in {"L3", "L4"} or (
            isinstance(targets, list) and any(_is_policy_target(target) for target in targets)
        )
        if policy_promotion and payload.get("approval_required") is not True:
            errors.append("approval_required must be true for policy promotion")
        if policy_promotion and not _verified_approval_evidence(
            payload.get("approval_evidence"),
            verified_approval_evidence,
            safety_decision_id=payload.get("safety_decision_id"),
            targets=targets if isinstance(targets, list) else [],
        ):
            errors.append("approval_evidence is required for policy promotion")
    if kind == "work_packet":
        errors.extend(_non_empty_list_errors(payload, WORK_PACKET_NON_EMPTY_LIST_FIELDS))
        if payload.get("capability_class") not in CAPABILITY_CLASSES:
            errors.append(
                "capability_class must be one of: "
                f"{', '.join(CAPABILITY_CLASSES)}"
            )
        for field in ("scope", "owned_paths"):
            if _unsafe_relative_paths(payload, field):
                errors.append(f"{field} must contain safe relative paths")
        completion_target_error = _completion_value_error(
            "completion_target", payload.get("completion_target")
        )
        if completion_target_error:
            errors.append(completion_target_error)
        owned_paths_outside_scope = _owned_paths_outside_scope(payload)
        if owned_paths_outside_scope:
            errors.append(
                f"owned_paths must be within scope: {', '.join(owned_paths_outside_scope)}"
            )
        side_effects = payload.get("side_effects_requested", [])
        external_targets = payload.get("external_write_targets", [])
        side_effects = side_effects if isinstance(side_effects, list) else []
        external_targets = external_targets if isinstance(external_targets, list) else []
        unknown_side_effects = sorted(
            item for item in side_effects if isinstance(item, str) and item not in SAFETY_TRIGGERS
        )
        if unknown_side_effects:
            errors.append(
                f"unknown side_effects_requested: {', '.join(unknown_side_effects)}"
            )
        requires_approval = bool(external_targets) or bool(side_effects)
        if requires_approval and payload.get("approval_required") is not True:
            errors.append("approval_required must be true for safety-triggering work")
        if (payload.get("approval_required") or requires_approval) and not _verified_approval_evidence(
            payload.get("approval_evidence"),
            verified_approval_evidence,
            safety_decision_id=payload.get("safety_decision_id"),
            targets=[
                *external_targets,
                *side_effects,
            ],
        ):
            errors.append("approval_evidence is required for approval-gated work")
    if kind == "evidence_bundle":
        errors.extend(_non_empty_list_errors(payload, EVIDENCE_BUNDLE_NON_EMPTY_LIST_FIELDS))
        completion_state_error = _completion_value_error(
            "completion_state", payload.get("completion_state")
        )
        if completion_state_error:
            errors.append(completion_state_error)
        if (
            payload.get("completion_state") in HIGH_COMPLETION_STATES
            and not _valid_completion_evidence(payload)
        ):
            errors.append(
                "completion_evidence is required for effective or adopted completion_state"
            )
    return errors


def delivery_draft_content_hash(draft_output: Mapping[str, Any]) -> str:
    bound_content = {
        "draft_id": draft_output.get("draft_id"),
        "draft_kind": draft_output.get("draft_kind"),
        "source_hash": draft_output.get("source_hash"),
        "claim_references": draft_output.get("claim_references"),
        "content": draft_output.get("content"),
    }
    encoded = json.dumps(
        bound_content, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def validate_delivery_draft_structure(
    draft_input: Mapping[str, Any],
    draft_output: Mapping[str, Any],
    *,
    expected_source_hash: str,
) -> list[str]:
    """Validate an untrusted delivery draft against its bounded input."""
    errors = [
        *(f"input: {error}" for error in validate_artifact("delivery_draft_input", draft_input)),
        *(f"output: {error}" for error in validate_artifact("delivery_draft_output", draft_output)),
    ]
    if draft_output.get("status") not in {"DRAFT_READY", "DRAFT_BLOCKED"}:
        errors.append("status must be DRAFT_READY or DRAFT_BLOCKED")
    def privileged_paths(value: Any, prefix: str = "") -> list[str]:
        if isinstance(value, Mapping):
            paths: list[str] = []
            for key, child in value.items():
                path = f"{prefix}.{key}" if prefix else str(key)
                normalized_key = re.sub(r"[^a-z]", "", str(key).lower())
                if normalized_key in DRAFT_PRIVILEGED_KEYS:
                    paths.append(path)
                paths.extend(privileged_paths(child, path))
            return paths
        if isinstance(value, list):
            return [
                path
                for index, child in enumerate(value)
                for path in privileged_paths(child, f"{prefix}[{index}]")
            ]
        return []

    privileged = sorted(privileged_paths(draft_output))
    if privileged:
        errors.append(f"delivery draft contains privileged fields: {', '.join(privileged)}")
    allowed_output_fields = set(ARTIFACT_REQUIRED_FIELDS["delivery_draft_output"])
    unknown_output_fields = sorted(
        str(key) for key in draft_output if key not in allowed_output_fields
    )
    if unknown_output_fields:
        errors.append(
            f"delivery draft contains unknown fields: {', '.join(unknown_output_fields)}"
        )
    for field in ("draft_id", "draft_kind", "source_hash"):
        if draft_output.get(field) != draft_input.get(field):
            errors.append(f"{field} does not match draft input")
    if draft_input.get("source_hash") != expected_source_hash:
        errors.append("source_hash does not match trusted snapshot")
    allowed_claims = {
        item
        for field in ("acceptance_ids", "test_ids", "residual_risk_ids", "changed_paths")
        for item in draft_input.get(field, [])
        if isinstance(item, str)
    }
    claim_references = draft_output.get("claim_references", [])
    if isinstance(claim_references, list):
        if any(not isinstance(item, str) for item in claim_references):
            errors.append("claim_references items must be strings")
        if draft_output.get("status") == "DRAFT_READY" and not claim_references:
            errors.append("claim_references are required for DRAFT_READY")
        unbound = sorted(
            item for item in claim_references if isinstance(item, str) and item not in allowed_claims
        )
        if unbound:
            errors.append(f"claim_references contain unbound evidence: {', '.join(unbound)}")
    content = draft_output.get("content")
    if draft_output.get("status") == "DRAFT_READY" and not isinstance(content, Mapping):
        errors.append("content must be an object for DRAFT_READY")
    elif draft_output.get("status") == "DRAFT_READY" and draft_input.get("draft_kind") == "commit":
        unknown_content = sorted(set(content) - {"type", "subject", "body"})
        if unknown_content:
            errors.append(f"commit content contains unknown fields: {', '.join(unknown_content)}")
        commit_type = content.get("type")
        subject = content.get("subject")
        body = content.get("body", "")
        if commit_type not in COMMIT_TYPES:
            errors.append("commit type is not allowed")
        if not isinstance(subject, str) or not subject.strip():
            errors.append("commit subject is required")
        elif len(subject) > 70:
            errors.append("commit subject must be 70 characters or fewer")
        elif any(ord(character) < 32 for character in subject):
            errors.append("commit subject must be a single line without control characters")
        elif not re.search(r"[\u3040-\u30ff\u3400-\u9fff]", subject):
            errors.append("commit subject must include Japanese text")
        if not isinstance(body, str) or "\x00" in body:
            errors.append("commit body must be text without NUL characters")
    elif draft_output.get("status") == "DRAFT_READY" and draft_input.get("draft_kind") == "pull_request":
        unknown_content = sorted(set(content) - {"title", "sections"})
        if unknown_content:
            errors.append(f"PR content contains unknown fields: {', '.join(unknown_content)}")
        title = content.get("title")
        sections = content.get("sections")
        if not isinstance(title, str) or not title.strip():
            errors.append("PR title is required")
        elif len(title) > 70:
            errors.append("PR title must be 70 characters or fewer")
        elif any(ord(character) < 32 for character in title):
            errors.append("PR title must be a single line without control characters")
        if not isinstance(sections, Mapping):
            errors.append("PR sections must be an object")
        else:
            template_sections = draft_input.get("template_sections", [])
            required_sections = PR_SECTIONS | {
                item for item in template_sections if isinstance(item, str)
            }
            missing_sections = sorted(required_sections - set(sections))
            if missing_sections:
                errors.append(f"PR sections are missing: {', '.join(missing_sections)}")
            invalid_sections = sorted(
                key
                for key, value in sections.items()
                if not isinstance(value, str) or not value.strip() or "\x00" in value
            )
            if invalid_sections:
                errors.append(
                    f"PR sections must be non-empty text: {', '.join(invalid_sections)}"
                )
    return errors


def validate_delivery_draft_pair(
    draft_input: Mapping[str, Any],
    draft_output: Mapping[str, Any],
    *,
    expected_source_hash: str,
    verified_claim_evidence: Mapping[str, Any] | None = None,
) -> list[str]:
    """Validate structure plus parent-produced, content-hash-bound semantic evidence."""
    errors = validate_delivery_draft_structure(
        draft_input,
        draft_output,
        expected_source_hash=expected_source_hash,
    )
    if draft_output.get("status") != "DRAFT_READY":
        return errors
    expected_claims = draft_output.get("claim_references")
    valid_evidence = (
        isinstance(verified_claim_evidence, Mapping)
        and verified_claim_evidence.get("status") == "pass"
        and verified_claim_evidence.get("source_hash") == expected_source_hash
        and verified_claim_evidence.get("content_hash")
        == delivery_draft_content_hash(draft_output)
        and verified_claim_evidence.get("claim_references") == expected_claims
    )
    if not valid_evidence:
        errors.append("verified claim evidence is required for DRAFT_READY")
    return errors


def _validated_artifact(
    snapshot: Mapping[str, Any],
    kind: str,
    verified_approval_evidence: Mapping[str, Mapping[str, Any]] | None = None,
) -> bool:
    payloads = snapshot.get("artifact_payloads", {})
    if not isinstance(payloads, Mapping):
        return False
    payload = payloads.get(kind)
    return isinstance(payload, Mapping) and not validate_artifact(
        kind, payload, verified_approval_evidence=verified_approval_evidence
    )


def _valid_approval_evidence(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(
        isinstance(item, str) and APPROVAL_EVIDENCE.fullmatch(item) for item in value
    )


def _verified_approval_evidence(
    value: Any,
    verified: Mapping[str, Mapping[str, Any]] | None,
    *,
    safety_decision_id: Any,
    targets: Sequence[Any],
) -> bool:
    if not _valid_approval_evidence(value):
        return False
    if not isinstance(verified, Mapping) or not isinstance(safety_decision_id, str):
        return False
    required_targets = {item for item in targets if isinstance(item, str)}
    for evidence_id in value:
        record = verified.get(evidence_id)
        if not isinstance(record, Mapping):
            return False
        if record.get("safety_decision_id") != safety_decision_id:
            return False
        approved_targets = record.get("approved_targets")
        if not isinstance(approved_targets, list) or not required_targets.issubset(approved_targets):
            return False
    return True


def _is_policy_target(target: Any) -> bool:
    if not isinstance(target, str):
        return False
    normalized = target.removeprefix(".codex/").removeprefix(".claude/")
    return normalized.startswith(POLICY_PROMOTION_PREFIXES)


def _completion_gap_action(current_state: Any, target_state: Any) -> str | None:
    if (
        current_state not in COMPLETION_ORDER
        or target_state not in COMPLETION_ORDER
        or COMPLETION_ORDER[current_state] >= COMPLETION_ORDER[target_state]
    ):
        return None
    return NEXT_COMPLETION_ACTION[current_state]


def _review_high_finding_count(snapshot: Mapping[str, Any]) -> tuple[int | None, str | None]:
    count: int | None = None
    if "high_findings" in snapshot:
        value = snapshot.get("high_findings")
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return None, "review findings count is invalid"
        count = value

    if "review_findings" in snapshot:
        findings = snapshot.get("review_findings")
        if not isinstance(findings, list):
            return None, "review_findings must be a list"
        derived = 0
        for finding in findings:
            if not isinstance(finding, Mapping):
                return None, "review_findings items must be objects"
            severity = finding.get("severity")
            if not isinstance(severity, str) or severity.upper() not in REVIEW_FINDING_SEVERITIES:
                return None, "review_findings severity is invalid"
            if severity.upper() in REVIEW_HIGH_FINDING_SEVERITIES:
                derived += 1
        if count is not None and count != derived:
            return None, "review findings count does not match structured findings"
        count = derived

    if count is None:
        return None, "review findings are required"
    return count, None


def next_action(
    snapshot: Mapping[str, Any],
    *,
    verified_approval_evidence: Mapping[str, Mapping[str, Any]] | None = None,
) -> TransitionDecision:
    state = str(snapshot.get("state", "RECEIVED"))
    route_id = str(snapshot.get("route_id", "prd-flow"))
    if snapshot.get("routing_status") == "ROUTING_BLOCKED":
        return TransitionDecision("ROUTING_BLOCKED", "STOP", "required model is unavailable")
    raw_triggers = snapshot.get("safety_triggers", [])
    safety_triggers = set(raw_triggers) if isinstance(raw_triggers, list) else set()
    raw_side_effects = snapshot.get("side_effects_requested", [])
    if isinstance(raw_side_effects, list):
        unknown_side_effects = sorted(
            item for item in raw_side_effects if item not in SAFETY_TRIGGERS
        )
        if unknown_side_effects:
            return TransitionDecision(
                "WAITING_HUMAN",
                "STOP",
                f"unknown side effect requires classification: {', '.join(unknown_side_effects)}",
            )
        safety_triggers.update(raw_side_effects)
    external_targets = snapshot.get("external_write_targets", [])
    external_targets = external_targets if isinstance(external_targets, list) else []
    approval_gated = bool(snapshot.get("safety_trigger")) or bool(safety_triggers) or bool(external_targets)
    approval_targets = [*external_targets, *safety_triggers]
    if approval_gated and (
        snapshot.get("approval_state") != "approved"
        or not _verified_approval_evidence(
            snapshot.get("approval_evidence"),
            verified_approval_evidence,
            safety_decision_id=snapshot.get("safety_decision_id"),
            targets=approval_targets,
        )
    ):
        return TransitionDecision("WAITING_HUMAN", "STOP", "safety approval is required")
    if int(snapshot.get("retry_count", 0)) >= int(snapshot.get("max_retries", 3)):
        return TransitionDecision("WAITING_HUMAN", "STOP", "bounded retry limit reached")

    if state == "RECEIVED":
        return TransitionDecision("RUNNING", "SURVEY", "establish current facts")
    if state == "SURVEYED":
        if route_id != "fast-track" and not _validated_artifact(
            snapshot, "approved_prd", verified_approval_evidence
        ):
            payloads = snapshot.get("artifact_payloads", {})
            action = "REVIEW_PRD" if isinstance(payloads, Mapping) and "prd_draft" in payloads else "DRAFT_PRD"
            return TransitionDecision("RUNNING", action, "approved PRD is required")
        if not _validated_artifact(snapshot, "work_packet", verified_approval_evidence):
            return TransitionDecision("RUNNING", "CREATE_WORK_PACKET", "implementation contract is missing")
        if route_id != "fast-track":
            payloads = snapshot.get("artifact_payloads", {})
            approved_prd = payloads.get("approved_prd") if isinstance(payloads, Mapping) else {}
            work_packet = payloads.get("work_packet") if isinstance(payloads, Mapping) else {}
            pair_errors = validate_prd_work_packet_pair(approved_prd, work_packet)
            if pair_errors:
                return TransitionDecision("RUNNING", "CREATE_WORK_PACKET", pair_errors[0])
        return TransitionDecision("RUNNING", "IMPLEMENT", "implementation contract is ready")
    if state == "IMPLEMENTED":
        return TransitionDecision("RUNNING", "REVIEW", "independent review is required")
    if state == "REVIEWED":
        high, review_error = _review_high_finding_count(snapshot)
        if review_error is not None or high is None:
            return TransitionDecision("RUNNING", "REVIEW", review_error or "review findings are required")
        if high:
            return TransitionDecision("RUNNING", "FIX", "critical or important findings remain")
        if not _validated_artifact(snapshot, "evidence_bundle", verified_approval_evidence):
            return TransitionDecision("RUNNING", "BUILD_EVIDENCE_BUNDLE", "delivery evidence is incomplete")
        if not _validated_artifact(snapshot, "work_packet", verified_approval_evidence):
            return TransitionDecision("RUNNING", "CREATE_WORK_PACKET", "implementation contract is missing")
        payloads = snapshot.get("artifact_payloads", {})
        work_packet = payloads.get("work_packet") if isinstance(payloads, Mapping) else {}
        evidence_bundle = payloads.get("evidence_bundle") if isinstance(payloads, Mapping) else {}
        if isinstance(work_packet, Mapping) and isinstance(evidence_bundle, Mapping):
            pair_errors = validate_work_packet_evidence_pair(work_packet, evidence_bundle)
            if pair_errors:
                reason = pair_errors[0]
                if reason == "source_hash mismatch":
                    reason = "work_packet and evidence_bundle source_hash mismatch"
                return TransitionDecision(
                    "RUNNING",
                    "BUILD_EVIDENCE_BUNDLE",
                    reason,
                )
            completion_action = _completion_gap_action(
                evidence_bundle.get("completion_state"),
                work_packet.get("completion_target"),
            )
            if completion_action:
                return TransitionDecision(
                    "RUNNING",
                    completion_action,
                    (
                        f"completion target {work_packet.get('completion_target')} "
                        f"is not met by {evidence_bundle.get('completion_state')}"
                    ),
                )
        return TransitionDecision("RUNNING", "DELIVER", "review and evidence gates passed")
    if state == "DELIVERED":
        if snapshot.get("escaped_defects"):
            return TransitionDecision("RUNNING", "RECORD_ESCAPED_DEFECT", "new review evidence must be classified")
        return TransitionDecision("COMPLETE", "STOP", "delivery loop converged")
    if state == "DEFECT_RECORDED":
        return TransitionDecision("RUNNING", "REPLAY", "verify the earliest preventable gate")
    if state == "REPLAYED":
        if snapshot.get("replay_passed"):
            targets = snapshot.get("promotion_targets", [])
            policy_promotion = snapshot.get("promotion_level") in {"L3", "L4"} or (
                isinstance(targets, list) and any(_is_policy_target(target) for target in targets)
            )
            if policy_promotion and (
                snapshot.get("approval_state") != "approved"
                or not _verified_approval_evidence(
                    snapshot.get("approval_evidence"),
                    verified_approval_evidence,
                    safety_decision_id=snapshot.get("safety_decision_id"),
                    targets=targets if isinstance(targets, list) else [],
                )
            ):
                return TransitionDecision(
                    "WAITING_HUMAN", "STOP", "policy promotion approval is required"
                )
            return TransitionDecision("COMPLETE", "STOP", "promoted guard prevents the defect")
        return TransitionDecision("WAITING_HUMAN", "STOP", "replay did not prevent the defect")
    if state == "COMPLETE":
        return TransitionDecision("COMPLETE", "STOP", "already complete")
    return TransitionDecision("INVALID_STATE", "STOP", f"unknown state: {state}")


def _load_json(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    route_parser = subparsers.add_parser("route")
    route_parser.add_argument("input")
    next_parser = subparsers.add_parser("next")
    next_parser.add_argument("input")
    artifact_parser = subparsers.add_parser("validate-artifact")
    artifact_parser.add_argument("kind", choices=sorted(ARTIFACT_REQUIRED_FIELDS))
    artifact_parser.add_argument("input")
    args = parser.parse_args()
    payload = _load_json(args.input)
    if not isinstance(payload, dict):
        print("FAIL: input must be a JSON object", file=sys.stderr)
        return 2
    if args.command == "route":
        if "factors" in payload:
            factors = payload["factors"]
            options = {key: value for key, value in payload.items() if key != "factors"}
        else:
            factors = payload
            options = {}
        if not isinstance(factors, dict):
            print("FAIL: factors must be a JSON object", file=sys.stderr)
            return 2
        decision = route_work_packet(factors, **options)
        print(json.dumps(asdict(decision), ensure_ascii=False, indent=2))
        return 0 if decision.status == "READY" else 3
    if args.command == "next":
        print(json.dumps(asdict(next_action(payload)), ensure_ascii=False, indent=2))
        return 0
    errors = validate_artifact(args.kind, payload)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: artifact contract is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
