#!/usr/bin/env python3
"""Validate a Graph Engineering contract without external dependencies."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Any


NODE_KINDS = {"loop", "function", "tool", "human_gate"}
NODE_ROLES = {"worker", "checker", "judge"}
AUTHORITIES = {"read_only", "artifact_writer"}
STATE_SCOPES = {"context", "planning", "run", "artifact"}
ROUTES = {"static", "deterministic", "model", "human"}
SAFEGUARDS = {"approval", "idempotency_key", "target_resolution"}


def validate_contract(contract: dict[str, Any]) -> list[str]:
    """Return deterministic, human-readable contract errors."""
    errors: list[str] = []
    nodes = contract.get("nodes")
    state = contract.get("state")
    edges = contract.get("edges")
    entrypoints = contract.get("entrypoints")

    if contract.get("version") != "1":
        errors.append("version must be 1")
    if not isinstance(contract.get("name"), str) or not contract["name"].strip():
        errors.append("name must be a non-empty string")
    if not isinstance(nodes, dict) or not nodes:
        errors.append("nodes must be a non-empty object")
    if not isinstance(state, dict):
        errors.append("state must be an object")
    if not isinstance(edges, list):
        errors.append("edges must be an array")
    if not isinstance(entrypoints, list) or not entrypoints:
        errors.append("entrypoints must be a non-empty array")
    if errors:
        return errors

    node_names = set(nodes)
    state_names = set(state)

    for entrypoint in entrypoints:
        if entrypoint not in node_names:
            errors.append(f"unknown entrypoint: {entrypoint}")

    for field_name, field in state.items():
        if not isinstance(field, dict):
            errors.append(f"state field must be an object: {field_name}")
            continue
        if field.get("scope") not in STATE_SCOPES:
            errors.append(f"invalid state scope: {field_name}")
        writer = field.get("writer")
        if writer != "lead" and writer not in node_names:
            errors.append(f"unknown state writer: {field_name} -> {writer}")
        if not isinstance(field.get("provenance"), str) or not field["provenance"]:
            errors.append(f"state provenance is required: {field_name}")

    for node_name, node in nodes.items():
        if not isinstance(node, dict):
            errors.append(f"node must be an object: {node_name}")
            continue
        if node.get("kind") not in NODE_KINDS:
            errors.append(f"invalid node kind: {node_name}")
        if node.get("role") not in NODE_ROLES:
            errors.append(f"invalid node role: {node_name}")
        if node.get("authority") not in AUTHORITIES:
            errors.append(f"invalid node authority: {node_name}")

        reads = node.get("reads", [])
        writes = node.get("writes", [])
        if not isinstance(reads, list) or not isinstance(writes, list):
            errors.append(f"node reads and writes must be arrays: {node_name}")
            continue

        for field_name in reads + writes:
            if field_name not in state_names:
                errors.append(f"unknown state reference: {node_name} -> {field_name}")

        for field_name in writes:
            field = state.get(field_name)
            if isinstance(field, dict) and field.get("writer") != node_name:
                errors.append(f"state writer mismatch: {node_name} -> {field_name}")

        artifact_writes = [
            field_name
            for field_name in writes
            if isinstance(state.get(field_name), dict)
            and state[field_name].get("scope") == "artifact"
        ]
        if artifact_writes and node.get("authority") != "artifact_writer":
            errors.append(f"artifact write requires authority: {node_name}")

        if node.get("role") in {"checker", "judge"}:
            if artifact_writes:
                errors.append(f"checker cannot write artifact state: {node_name}")

        side_effect = node.get("side_effect")
        if side_effect not in {"none", "external"}:
            errors.append(f"invalid side effect mode: {node_name}")
        if side_effect == "external":
            safeguards = node.get("safeguards")
            if not isinstance(safeguards, dict) or any(
                not safeguards.get(key) for key in SAFEGUARDS
            ):
                errors.append(
                    f"external side effect requires safeguards: {node_name}"
                )

    artifact_writers = [
        node_name
        for node_name, node in nodes.items()
        if isinstance(node, dict) and node.get("authority") == "artifact_writer"
    ]
    if len(artifact_writers) > 1:
        errors.append("graph must have at most one artifact writer")

    outgoing_routes: dict[str, set[str]] = defaultdict(set)
    adjacency: dict[str, list[str]] = defaultdict(list)
    non_loop_adjacency: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        if not isinstance(edge, dict):
            errors.append("edge must be an object")
            continue
        source = edge.get("from")
        target = edge.get("to")
        route = edge.get("route")
        if source not in node_names or target not in node_names:
            errors.append(f"edge references unknown node: {source} -> {target}")
            continue
        if route not in ROUTES:
            errors.append(f"invalid edge route: {source} -> {target}")
        else:
            outgoing_routes[source].add(route)
            if route != "static" and not edge.get("condition"):
                errors.append(
                    f"decision edge requires condition: {source} -> {target}"
                )
        adjacency[source].append(target)
        if edge.get("loop") is not True:
            non_loop_adjacency[source].append(target)

        if edge.get("loop") is True:
            max_iterations = edge.get("max_iterations")
            if (
                not isinstance(max_iterations, int)
                or max_iterations < 1
                or not edge.get("stop_condition")
            ):
                errors.append(f"loop edge requires brake: {source} -> {target}")

    for source, routes in outgoing_routes.items():
        if len(routes) > 1:
            errors.append(f"mixed routing ownership: {source}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def has_undeclared_cycle(node_name: str) -> bool:
        if node_name in visiting:
            return True
        if node_name in visited:
            return False
        visiting.add(node_name)
        if any(has_undeclared_cycle(target) for target in non_loop_adjacency[node_name]):
            return True
        visiting.remove(node_name)
        visited.add(node_name)
        return False

    if any(has_undeclared_cycle(node_name) for node_name in node_names):
        errors.append("cycle requires an explicit loop edge")

    reachable: set[str] = set()
    queue = deque(entrypoint for entrypoint in entrypoints if entrypoint in node_names)
    while queue:
        node_name = queue.popleft()
        if node_name in reachable:
            continue
        reachable.add(node_name)
        queue.extend(adjacency[node_name])
    for node_name in sorted(node_names - reachable):
        errors.append(f"unreachable node: {node_name}")

    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path, help="Path to a JSON graph contract")
    args = parser.parse_args()

    try:
        contract = json.loads(args.contract.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"FAIL: {error}")
        return 1

    errors = validate_contract(contract)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print(f"PASS: {contract['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
