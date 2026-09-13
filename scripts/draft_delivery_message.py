#!/usr/bin/env python3
"""Prepare and validate a tool-free Fast-class delivery draft for Claude Code.

Claude Code has no isolated CLI worker, so the lead runs the drafter itself as
``Agent(model: "haiku")`` with no tools. This script owns everything around
that call: it validates the bounded ``Delivery Draft Input`` and emits the
worker prompt (``prompt``), it validates the untrusted worker output against
the input and the trusted snapshot hash (``validate``), and it prints the
claim-evidence skeleton the parent must bind after its own semantic review
(``claim-evidence``); a pass must list the checks the parent performed. Missing or
invalid material blocks the draft; there is no
fallback to another model.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from agent_delivery_lifecycle import (
    delivery_draft_content_hash,
    validate_artifact,
    validate_delivery_draft_pair,
    validate_delivery_draft_structure,
)
from git_delivery_contract import validate_worker_patch

WORKER_MODEL = "haiku"
MAX_INPUT_BYTES = 96 * 1024
CANONICAL_PR_SECTIONS = (
    "summary",
    "why",
    "trade_off",
    "out_of_scope",
    "impact",
    "tests",
    "residual_risks",
)
WORKER_INSTRUCTIONS = (
    "You are an output-only delivery drafter. Do not call tools, make decisions, "
    "or request side effects. Return only JSON matching the provided schema. "
    "Use only the supplied evidence identifiers and content. claim_references may contain "
    "only exact strings from changed_paths, acceptance_ids, test_ids, and "
    "residual_risk_ids; never use evidence_bundle_id. For commit, content must contain "
    "only type, subject, and body, and type must be one of feat, fix, docs, refactor, "
    "test, chore, perf, build, or ci. The commit subject must be concise Japanese. "
    "For pull_request, content must contain only "
    "title and sections; sections must include summary, why, trade_off, out_of_scope, "
    "impact, tests, residual_risks, and every supplied template section. Every ready "
    "draft must include one or more allowed claim_references."
)


def output_schema(draft_input: Mapping[str, Any]) -> dict[str, Any]:
    if draft_input.get("draft_kind") == "commit":
        content_properties: dict[str, Any] = {
            "type": {"type": "string"},
            "subject": {"type": "string"},
            "body": {"type": "string"},
        }
    else:
        template_sections = tuple(
            item for item in draft_input.get("template_sections", []) if isinstance(item, str)
        )
        section_names = tuple(dict.fromkeys((*CANONICAL_PR_SECTIONS, *template_sections)))
        content_properties = {
            "title": {"type": "string"},
            "sections": {
                "type": "object",
                "additionalProperties": False,
                "required": list(section_names),
                "properties": {name: {"type": "string"} for name in section_names},
            },
        }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "draft_id",
            "draft_kind",
            "source_hash",
            "status",
            "claim_references",
            "content",
        ],
        "properties": {
            "draft_id": {"type": "string"},
            "draft_kind": {"enum": ["commit", "pull_request"]},
            "source_hash": {"type": "string"},
            "status": {"enum": ["DRAFT_READY", "DRAFT_BLOCKED"]},
            "claim_references": {"type": "array", "items": {"type": "string"}},
            "content": {
                "type": "object",
                "additionalProperties": False,
                "required": list(content_properties),
                "properties": content_properties,
            },
        },
    }


def validate_draft_input(
    draft_input: Mapping[str, Any],
    *,
    expected_source_hash: str,
    snapshot: Mapping[str, Any] | None = None,
) -> list[str]:
    errors = validate_artifact("delivery_draft_input", draft_input)
    if draft_input.get("source_hash") != expected_source_hash:
        errors.append("source_hash does not match trusted snapshot")
    if snapshot is not None:
        if snapshot.get("source_hash") != expected_source_hash:
            errors.append("snapshot source_hash does not match trusted snapshot")
        if sorted(draft_input.get("changed_paths", [])) != sorted(snapshot.get("changed_paths", [])):
            errors.append("changed_paths do not match trusted snapshot")
    errors.extend(
        validate_worker_patch(
            draft_input.get("worker_patch"),
            [path for path in draft_input.get("changed_paths", []) if isinstance(path, str)],
        )
    )
    if errors:
        return [f"input: {error}" for error in errors]
    encoded = json.dumps(draft_input, ensure_ascii=False, separators=(",", ":"))
    if len(encoded.encode("utf-8")) > MAX_INPUT_BYTES:
        return ["input exceeds worker limit"]
    return []


def build_worker_prompt(draft_input: Mapping[str, Any]) -> str:
    encoded = json.dumps(draft_input, ensure_ascii=False, separators=(",", ":"))
    schema = json.dumps(output_schema(draft_input), ensure_ascii=False)
    return f"{WORKER_INSTRUCTIONS}\n\nOUTPUT_SCHEMA={schema}\n\nDELIVERY_DRAFT_INPUT={encoded}"


def prepare_draft_prompt(
    draft_input: Mapping[str, Any],
    *,
    expected_source_hash: str,
    snapshot: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    errors = validate_draft_input(
        draft_input, expected_source_hash=expected_source_hash, snapshot=snapshot
    )
    if errors:
        return None, errors
    return (
        {
            "status": "PROMPT_READY",
            "worker": {"tool": "Agent", "model": WORKER_MODEL, "tools": []},
            "prompt": build_worker_prompt(draft_input),
            "schema": output_schema(draft_input),
        },
        [],
    )


def validate_draft_output(
    draft_input: Mapping[str, Any],
    draft_output: Any,
    *,
    expected_source_hash: str,
    verified_claim_evidence: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    if not isinstance(draft_output, Mapping):
        return None, ["worker output must be an object"]
    if verified_claim_evidence is None:
        errors = validate_delivery_draft_structure(
            draft_input, draft_output, expected_source_hash=expected_source_hash
        )
        verification = "structure_only"
    else:
        errors = validate_delivery_draft_pair(
            draft_input,
            draft_output,
            expected_source_hash=expected_source_hash,
            verified_claim_evidence=verified_claim_evidence,
        )
        errors.extend(claim_evidence_check_errors(verified_claim_evidence))
        verification = "claim_verified"
    if errors:
        return None, errors
    return {"status": "VALIDATED", "verification": verification, "draft": dict(draft_output)}, []


def claim_evidence_check_errors(evidence: Mapping[str, Any]) -> list[str]:
    """Require the parent to record what it actually checked before a pass counts."""
    if evidence.get("status") != "pass":
        return []
    checks = evidence.get("checks")
    if not isinstance(checks, list) or not checks or any(
        not isinstance(item, str) or not item.strip() for item in checks
    ):
        return ["claim evidence checks must be a non-empty list of strings"]
    return []


def claim_evidence_skeleton(
    draft_output: Mapping[str, Any], *, expected_source_hash: str
) -> dict[str, Any]:
    return {
        "status": "pending",
        "checks": [],
        "source_hash": expected_source_hash,
        "content_hash": delivery_draft_content_hash(draft_output),
        "claim_references": list(draft_output.get("claim_references", [])),
    }


def _load_json(path: str) -> Any:
    text = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    return json.loads(text)


def _load_object(path: str) -> dict[str, Any]:
    value = _load_json(path)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _blocked(errors: Sequence[str]) -> int:
    print(json.dumps({"status": "DRAFT_BLOCKED", "errors": list(errors)}, ensure_ascii=False))
    return 3


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)

    prompt = commands.add_parser("prompt", help="validate input and emit the haiku worker prompt")
    prompt.add_argument("input")
    prompt.add_argument("--expected-source-hash", required=True)
    prompt.add_argument(
        "--snapshot", help="trusted git_delivery_contract snapshot; changed_paths must match"
    )

    validate = commands.add_parser("validate", help="validate untrusted worker output")
    validate.add_argument("input")
    validate.add_argument("output")
    validate.add_argument("--expected-source-hash", required=True)
    validate.add_argument(
        "--claim-evidence",
        help="parent-produced claim verification evidence; enables pair validation",
    )

    evidence = commands.add_parser(
        "claim-evidence", help="print the claim evidence skeleton bound to the output"
    )
    evidence.add_argument("output")
    evidence.add_argument("--expected-source-hash", required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "prompt":
            result, errors = prepare_draft_prompt(
                _load_object(args.input),
                expected_source_hash=args.expected_source_hash,
                snapshot=_load_object(args.snapshot) if args.snapshot else None,
            )
        elif args.command == "validate":
            claim = _load_object(args.claim_evidence) if args.claim_evidence else None
            result, errors = validate_draft_output(
                _load_object(args.input),
                _load_json(args.output),
                expected_source_hash=args.expected_source_hash,
                verified_claim_evidence=claim,
            )
        else:
            result, errors = (
                claim_evidence_skeleton(
                    _load_object(args.output), expected_source_hash=args.expected_source_hash
                ),
                [],
            )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return _blocked([str(error)])
    if errors:
        return _blocked(errors)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
