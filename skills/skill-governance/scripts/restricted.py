#!/usr/bin/env python3
"""Fail-closed, read-only audit for the single reviewed imozuru adoption.

Remote observations prove delivery for this profile generation.  This offline
checker does not claim to observe the remote's current state.
"""

from __future__ import annotations

import errno
import copy
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    import __main__ as gov
    gov.BASE_DIR
except (AttributeError, ImportError):
    import governance as gov


PROFILE_ID = "marycache-imozuru-2026-10"
CAPABILITY_SCOPE = "imozuru-public-source-v1"
GLOBAL_DRIFT_CODES = frozenset({"restricted_global_findings", "restricted_inventory"})
OBSERVED_AUDIT_POLICY_CODES = frozenset({
    'active_shadow_override',
    'approval_receipt_binding',
    'baseline_drift',
    'candidate_invisible_control',
    'catalog_license_evidence_gap',
    'catalog_skill_name_invalid',
    'code_present',
    'codex_disabled_skill_missing',
    'discovery_excluded_scan_truncated',
    'discovery_excluded_symlink_recorded',
    'discovery_symlink_allowlisted',
    'discovery_symlink_unreviewed',
    'executable_file',
    'external_url',
    'lock_field_mismatch',
    'promotion_receipt_binding',
    'promotion_target_drift',
    'root_unavailable',
    'runtime_estate_added',
    'runtime_estate_drift',
    'runtime_estate_removed',
    'runtime_skill_identity_mismatch',
    'safety_receipt_binding',
    'stale_hold',
    'target_frontmatter_requires_full_validation',
    'unknown_frontmatter_key',
    'unregistered_skill_surface',
    'value_receipt_binding',
})
COLLECTION_ID = PROFILE_ID
SOURCE_ID = "marycache-imozuru"
SOURCE_REVISION = "980ec7f50f0b954e9e1b1d85865c29a427c8e776"
PROFILE_DIR = gov.BASE_DIR / "restricted-profiles" / PROFILE_ID
TRUSTED_HOME = Path("/Users/yoshiki")
DELIVERY_PROOF = TRUSTED_HOME / ".local/share/skill-governance/delivery" / f"{PROFILE_ID}.json"
VERIFIER_PYTHON = TRUSTED_HOME / ".local/share/skill-governance/runtime/pyyaml-6.0.2/bin/python"
EXPECTED_PACKAGES = {
    "authority": TRUSTED_HOME / ".codex/skills/skill-governance",
    "replica": TRUSTED_HOME / ".claude/skills/skill-governance",
}
EXPECTED_RUNTIMES = {
    "codex": TRUSTED_HOME / ".codex/skills/imozuru",
    "claude": TRUSTED_HOME / ".claude/skills/imozuru",
}
EXPECTED_REVIEWS = {
    name: TRUSTED_HOME / ".local/share/skill-governance/review" / PROFILE_ID / "imozuru" / name
    for name in ("codex", "claude")
}
QUARANTINE_PATH = TRUSTED_HOME / ".local/share/skill-governance/quarantine/marycache-imozuru" / SOURCE_REVISION / "imozuru"
QUARANTINE_TREE_SHA256 = "33a79d5de6e28e20582f35d439ef753d691ae5537506888195f9e6442ce0b75b"
EXPECTED_REPOS = {"codex": TRUSTED_HOME / ".codex", "claude": TRUSTED_HOME / ".claude"}
EXPECTED_CODEX_REPO_CANONICAL = TRUSTED_HOME / "ghq/github.com/xxarupakaxx/.codex"
EXPECTED_REMOTES = {
    "codex": "ssh://git@github.com/xxarupakaxx/.codex.git",
    "claude": "ssh://git@github.com/xxarupakaxx/.claude.git",
}
EXPECTED_INTEGRATIONS = frozenset(
    str(root / "skills" / skill)
    for root in EXPECTED_REPOS.values()
    for skill in ("research", "ask-skill-router", "creating-html-documents")
)
REMOTE_BRANCH = "refs/heads/main"
REMOTE_OBSERVATION_FUTURE_SKEW = timedelta(minutes=5)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
PROFILE_ARTIFACTS = ("profile.json", "lock.json", "review-receipt.json", "approval-receipt.json")
EVIDENCE_KINDS = {
    "source-manifest", "quarantine-manifest", "frontmatter-receipt",
    "code-review", "safety-receipt", "value-receipt",
}
RELATED_RUNTIME_SUBJECTS = {
    f"{root}:{skill}"
    for root in ("codex", "claude")
    for skill in (
        "imozuru", "research", "ask-skill-router", "skill-governance",
        "creating-html-documents",
    )
}
EPHEMERAL_ARG0_TARGET = TRUSTED_HOME / ".local/share/npm-global/lib/node_modules/@openai/codex/node_modules/@openai/codex-darwin-arm64/vendor/aarch64-apple-darwin/bin/codex"
EPHEMERAL_ARG0_TOKEN = "codex-arg0__CURRENT_EXEC__"
EPHEMERAL_ARG0_LEAVES = {"apply_patch", "applypatch", "codex-execve-wrapper"}
EPHEMERAL_ARG0_PATH_RE = re.compile(
    r"^/Users/yoshiki/ghq/github\.com/xxarupakaxx/\.codex/tmp/arg0/"
    r"codex-arg0([A-Za-z0-9]{6})/(apply_patch|applypatch|codex-execve-wrapper)$"
)
EPHEMERAL_ARG0_RELATIVE_RE = re.compile(
    r"^arg0/codex-arg0([A-Za-z0-9]{6})/(apply_patch|applypatch|codex-execve-wrapper)$"
)


def _finding(code: str, message: str, subject: str = "") -> gov.Finding:
    return gov.blocker(f"restricted_{code}", message, subject)


def _keys(value: Any, expected: set[str], subject: str, findings: list[gov.Finding]) -> bool:
    if not isinstance(value, dict):
        findings.append(_finding("schema", "Expected a JSON object", subject))
        return False
    if set(value) != expected:
        findings.append(_finding("schema", f"expected={sorted(expected)} actual={sorted(value)}", subject))
        return False
    return True


def _digest_json(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _ephemeral_arg0_match(path: str) -> tuple[str, str] | None:
    match = EPHEMERAL_ARG0_PATH_RE.fullmatch(path)
    return (match.group(1), match.group(2)) if match else None


def normalize_restricted_findings(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Bind only the current Codex exec wrapper path to a stable token."""
    result: list[dict[str, Any]] = []
    message = f"Excluded-surface symlink recorded without following: {EPHEMERAL_ARG0_TARGET}"
    prefix = str(EXPECTED_CODEX_REPO_CANONICAL / "tmp/arg0")
    for original in rows:
        row = dict(original)
        matched = _ephemeral_arg0_match(str(row.get("path", "")))
        leaf = matched[1] if matched else None
        if (
            leaf in EPHEMERAL_ARG0_LEAVES
            and row.get("severity") == "ADVISORY"
            and row.get("code") == "discovery_excluded_symlink_recorded"
            and row.get("message") == message
        ):
            row["path"] = f"{prefix}/{EPHEMERAL_ARG0_TOKEN}/{leaf}"
        result.append(row)
    return result


def normalize_restricted_inventory(inventory: dict[str, Any]) -> dict[str, Any]:
    """Normalize the same three-field symlink records without dropping multiplicity."""
    result = copy.deepcopy(inventory)
    prefix = str(EXPECTED_CODEX_REPO_CANONICAL / "tmp/arg0")

    def normalized_rows(rows: Any) -> Any:
        if not isinstance(rows, list):
            return rows
        changed = False
        normalized: list[Any] = []
        for original in rows:
            if not isinstance(original, dict):
                normalized.append(original)
                continue
            row = dict(original)
            path_match = _ephemeral_arg0_match(str(row.get("path", "")))
            relative = EPHEMERAL_ARG0_RELATIVE_RE.fullmatch(str(row.get("root_relative_path", "")))
            if (
                path_match is not None
                and relative is not None
                and relative.group(1) == path_match[0]
                and relative.group(2) == path_match[1]
                and row.get("target") == str(EPHEMERAL_ARG0_TARGET)
                and row.get("excluded") is True
                and row.get("allowlisted") is False
                and row.get("target_exists") is True
            ):
                path_leaf = path_match[1]
                row["path"] = f"{prefix}/{EPHEMERAL_ARG0_TOKEN}/{path_leaf}"
                row["root_relative_path"] = f"arg0/{EPHEMERAL_ARG0_TOKEN}/{path_leaf}"
                changed = True
            normalized.append(row)
        return sorted(normalized, key=_digest_json) if changed else normalized

    result["symlinks"] = normalized_rows(result.get("symlinks"))
    surface = result.get("surface_probe")
    if isinstance(surface, dict):
        surface["symlinks"] = normalized_rows(surface.get("symlinks"))
    return result


def _strict_json(raw: bytes, subject: str, findings: list[gov.Finding]) -> dict[str, Any] | None:
    try:
        value = gov._strict_json_loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError, gov.StrictJSONError) as exc:
        findings.append(_finding("json", str(exc), subject))
        return None
    if not isinstance(value, dict):
        findings.append(_finding("schema", "Top-level JSON value must be an object", subject))
        return None
    return value


def _path_snapshot(info: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _codex_physical_path(path: Path, findings: list[gov.Finding], subject: str) -> Path | None:
    logical_root = EXPECTED_REPOS["codex"]
    absolute = path.absolute()
    try:
        relative = absolute.relative_to(logical_root)
    except ValueError:
        return absolute
    try:
        alias_before = logical_root.lstat()
        link_before = os.readlink(logical_root)
    except OSError as exc:
        findings.append(_finding("codex_alias", str(exc), subject))
        return None
    if not stat.S_ISLNK(alias_before.st_mode):
        findings.append(_finding("codex_alias", "Fixed Codex logical root must be a symlink", subject))
        return None
    link_path = Path(link_before)
    target = link_path if link_path.is_absolute() else logical_root.parent / link_path
    target = Path(os.path.normpath(target))
    if target != EXPECTED_CODEX_REPO_CANONICAL:
        findings.append(_finding("codex_alias", "Codex alias target differs from the fixed canonical repository", subject))
        return None
    try:
        target_before = target.lstat()
        alias_after = logical_root.lstat()
        link_after = os.readlink(logical_root)
        target_after = target.lstat()
    except OSError as exc:
        findings.append(_finding("codex_alias", str(exc), subject))
        return None
    if (
        stat.S_ISLNK(target_before.st_mode)
        or not stat.S_ISDIR(target_before.st_mode)
        or _path_snapshot(alias_before) != _path_snapshot(alias_after)
        or link_before != link_after
        or _path_snapshot(target_before) != _path_snapshot(target_after)
    ):
        findings.append(_finding("codex_alias", "Codex alias or canonical repository is unsafe or changed", subject))
        return None
    return target / relative


def _external_file(path: Path, findings: list[gov.Finding]) -> bytes | None:
    physical = _codex_physical_path(path, findings, str(path))
    if physical is None:
        return None
    raw, issue = gov._read_regular_path(physical, Path("/"), reject_hardlinks=True)
    if issue or raw is None:
        findings.append(_finding("unsafe_file", issue.message if issue else "File unavailable", str(path)))
        return None
    return raw


def _external_record(path: Path, findings: list[gov.Finding]) -> tuple[bytes, bool] | None:
    metadata: dict[str, Any] = {}
    physical = _codex_physical_path(path, findings, str(path))
    if physical is None:
        return None
    raw, issue = gov._read_regular_path(
        physical, Path("/"), reject_hardlinks=True, metadata=metadata
    )
    if issue or raw is None or type(metadata.get("executable")) is not bool:
        findings.append(_finding("unsafe_file", issue.message if issue else "File unavailable", str(path)))
        return None
    return raw, metadata["executable"]


def _profile_artifacts(profile_dir: Path, findings: list[gov.Finding]) -> dict[str, bytes]:
    package = profile_dir.parents[1]
    try:
        parts = profile_dir.absolute().relative_to(package.absolute()).parts
    except ValueError:
        findings.append(_finding("profile_path", "Profile directory escaped the governance package", str(profile_dir)))
        return {}
    tree = gov._scan_canonical_tree(
        package,
        parts,
        str(profile_dir),
        "restricted_profile",
        reject_hardlinks=True,
    )
    findings.extend(_finding("profile_tree", f"{item.code}: {item.message}", item.path) for item in tree.findings)
    result = {record.path: record.data for record in tree.files}
    expected = set(PROFILE_ARTIFACTS)
    if set(result) != expected:
        findings.append(_finding("profile_files", f"expected={sorted(expected)} actual={sorted(result)}", str(profile_dir)))
    return result


def _manifest(tree: gov.TreeResult) -> dict[str, gov.FileRecord]:
    return {item.path: item for item in tree.files}


def _safe_tree(path: Path) -> gov.TreeResult:
    alias_findings: list[gov.Finding] = []
    physical = _codex_physical_path(path, alias_findings, str(path))
    if physical is None:
        return gov.TreeResult(str(path), None, [], alias_findings)
    absolute = physical.absolute()
    if absolute == Path("/"):
        return gov.scan_tree(absolute, reject_hardlinks=True)
    return gov._scan_canonical_tree(
        Path("/"),
        absolute.parts[1:],
        str(absolute),
        "restricted_target",
        reject_hardlinks=True,
    )


def _validate_profile(profile: dict[str, Any], findings: list[gov.Finding]) -> bool:
    top = {
        "schema_version", "profile_id", "collection_id", "source", "valid_until",
        "governance", "packages", "targets", "integration_files", "audit",
        "collision_roots", "delivery", "verifier", "capability_scope", "generation", "integration_trees",
    }
    if not _keys(profile, top, "profile", findings):
        return False
    if profile.get("schema_version") != 2 or profile.get("capability_scope") != CAPABILITY_SCOPE or type(profile.get("generation")) is not int or profile["generation"] != 2 or profile.get("profile_id") != PROFILE_ID or profile.get("collection_id") != COLLECTION_ID:
        findings.append(_finding("identity", "Profile schema or fixed identity differs", "profile"))
    _validate_integration_trees(profile.get("integration_trees"), findings)
    source = profile.get("source")
    source_keys = {"id", "revision", "quarantine_path", "quarantine_tree_sha256"}
    if _keys(source, source_keys, "source", findings):
        expected_source = {
            "id": SOURCE_ID,
            "revision": SOURCE_REVISION,
            "quarantine_path": str(QUARANTINE_PATH),
            "quarantine_tree_sha256": QUARANTINE_TREE_SHA256,
        }
        if source != expected_source:
            findings.append(_finding("source", "Only the fixed MaryCache/imozuru revision is allowed", "source"))
    try:
        expiry = datetime.fromisoformat(str(profile["valid_until"]).replace("Z", "+00:00"))
        if expiry.tzinfo is None or expiry.astimezone(timezone.utc) <= datetime.now(timezone.utc):
            raise ValueError("expired or timezone missing")
    except (TypeError, ValueError) as exc:
        findings.append(_finding("expiry", str(exc), "valid_until"))
    governance = profile.get("governance")
    if _keys(governance, {"base_files", "base_tree_sha256_by_package", "file_manifest_by_package"}, "governance", findings):
        if set(governance["base_files"]) != {"registry.toml", "registry.lock.json", "estate.lock.json", "catalog.lock.json"}:
            findings.append(_finding("base_files", "Exactly four immutable base files are required", "governance.base_files"))
        for field in ("base_files", "base_tree_sha256_by_package"):
            if not isinstance(governance[field], dict) or any(not SHA256_RE.fullmatch(str(value)) for value in governance[field].values()):
                findings.append(_finding("hash", "Expected SHA-256 mapping", f"governance.{field}"))
        manifests = governance["file_manifest_by_package"]
        if not isinstance(manifests, dict) or set(manifests) != {"authority", "replica"}:
            findings.append(_finding("file_manifest", "Both package manifests are required", "governance"))
        else:
            required_code = {"scripts/governance.py", "scripts/restricted.py"}
            for side, rows in manifests.items():
                paths = {row.get("path") for row in rows if isinstance(row, dict)} if isinstance(rows, list) else set()
                if not required_code.issubset(paths):
                    findings.append(_finding("file_manifest", "Checker code hashes are required", side))
    if not _keys(profile.get("packages"), {"authority", "replica"}, "packages", findings):
        return False
    for side, entry in profile["packages"].items():
        if not _keys(entry, {"path"}, f"packages.{side}", findings) or not Path(entry.get("path", "")).is_absolute():
            findings.append(_finding("package_path", "Package path must be absolute", side))
        elif Path(entry["path"]) != EXPECTED_PACKAGES[side]:
            findings.append(_finding("package_path", "Package path differs from the fixed home", side))
    if not _keys(profile.get("targets"), {"review", "runtime"}, "targets", findings):
        return False
    target_hashes: list[str] = []
    for group in ("review", "runtime"):
        entries = profile["targets"].get(group)
        if _keys(entries, {"codex", "claude"}, f"targets.{group}", findings):
            for target, entry in entries.items():
                if _keys(entry, {"root_id", "path", "tree_sha256"}, f"targets.{group}.{target}", findings):
                    if not Path(entry["path"]).is_absolute() or "*" in str(entry["root_id"]) or not SHA256_RE.fullmatch(str(entry["tree_sha256"])):
                        findings.append(_finding("hash", "Invalid SHA-256", f"targets.{group}.{target}"))
                    target_hashes.append(str(entry["tree_sha256"]))
                    if group == "review" and Path(entry["path"]) != EXPECTED_REVIEWS[target]:
                        findings.append(_finding("review_path", "Review path differs from the fixed canonical path", target))
                    if group == "runtime" and Path(entry["path"]) != EXPECTED_RUNTIMES[target]:
                        findings.append(_finding("runtime_path", "Runtime path differs from the fixed home", target))
    if len(target_hashes) == 4 and len(set(target_hashes)) != 1:
        findings.append(_finding("target_parity", "All review and runtime target digests must be identical", "targets"))
    audit = profile.get("audit")
    if _keys(audit, {"required_status", "required_mutation_allowed", "baseline_findings", "allowed_delta_by_state", "related_subjects", "inventory_sha256_by_state"}, "audit", findings):
        if audit["required_status"] != "DEGRADED" or audit["required_mutation_allowed"] is not False:
            findings.append(_finding("global_policy", "Global audit must remain DEGRADED with mutation disabled", "audit"))
        states = {"ready_absent", "ready_exact", "active"}
        if set(audit["allowed_delta_by_state"]) != states or set(audit["inventory_sha256_by_state"]) != states:
            findings.append(_finding("audit_states", "Audit state bindings must be exact", "audit"))
    if not isinstance(profile.get("integration_files"), list) or not isinstance(profile.get("collision_roots"), list):
        findings.append(_finding("schema", "integration_files and collision_roots must be arrays", "profile"))
    else:
        for label, rows, expected in (
            ("integration_files", profile["integration_files"], {"path", "sha256"}),
            ("collision_roots", profile["collision_roots"], {"root_id", "path"}),
        ):
            for row in rows:
                if not _keys(row, expected, label, findings) or any("*" in str(value) for value in row.values()):
                    findings.append(_finding("schema", "Only exact entries are accepted", label))
        related = audit.get("related_subjects", []) if isinstance(audit, dict) else []
        bound_subjects = {COLLECTION_ID, f"{COLLECTION_ID}/imozuru", "imozuru"}
        bound_subjects.update(RELATED_RUNTIME_SUBJECTS)
        bound_subjects.update(str(row.get("path")) for row in profile["integration_files"] if isinstance(row, dict))
        for group in profile["targets"].values():
            bound_subjects.update(str(row.get("path")) for row in group.values() if isinstance(row, dict))
        for side, package in profile["packages"].items():
            package_path = Path(package.get("path", "")) if isinstance(package, dict) else Path("")
            manifest = governance.get("file_manifest_by_package", {}).get(side, []) if isinstance(governance, dict) else []
            bound_subjects.update(str(package_path / str(row.get("path"))) for row in manifest if isinstance(row, dict))
        for row in related:
            if not _keys(row, {"code", "subject"}, "related_subjects", findings) or any("*" in str(value) for value in row.values()):
                findings.append(_finding("schema", "Related subjects must be exact", "related_subjects"))
            elif str(row["subject"]) not in bound_subjects:
                findings.append(_finding("related_binding", "Related subject is not bound by a target or governance manifest", str(row["subject"])))
    if not _keys(profile.get("delivery"), {"repos"}, "delivery", findings):
        return False
    repos = profile["delivery"]["repos"]
    if not isinstance(repos, dict) or set(repos) != {"codex", "claude"}:
        findings.append(_finding("delivery_repos", "Exactly Codex and Claude repositories are required", "delivery"))
    else:
        for name, repo in repos.items():
            if not _keys(repo, {"path", "scope_files"}, f"delivery.{name}", findings):
                continue
            if not Path(repo["path"]).is_absolute() or not isinstance(repo["scope_files"], list) or not repo["scope_files"]:
                findings.append(_finding("delivery_repo", "Absolute repo and non-empty scope are required", name))
            elif Path(repo["path"]) != EXPECTED_REPOS[name]:
                findings.append(_finding("delivery_repo", "Repository path differs from the fixed home", name))
            scope_paths: list[str] = []
            for row in repo["scope_files"]:
                if not _keys(row, {"path", "sha256", "executable"}, f"delivery.{name}.scope", findings):
                    continue
                relative = Path(row["path"])
                scope_paths.append(str(row["path"]))
                if relative.is_absolute() or ".." in relative.parts or not SHA256_RE.fullmatch(str(row["sha256"])) or type(row["executable"]) is not bool:
                    findings.append(_finding("delivery_scope", "Safe relative path, SHA-256, and executable flag are required", name))
            if len(scope_paths) != len(set(scope_paths)):
                findings.append(_finding("delivery_scope", "Scope paths must be unique", name))
    verifier = profile.get("verifier")
    if _keys(verifier, {"python_path", "python_sha256", "pyyaml_version", "isolated", "dont_write_bytecode"}, "verifier", findings):
        expected = Path(verifier["python_path"])
        if expected != VERIFIER_PYTHON or Path(sys.executable).absolute() != expected:
            findings.append(_finding("verifier_python", "Current interpreter differs from the fixed verifier", "verifier"))
        if not SHA256_RE.fullmatch(str(verifier["python_sha256"])):
            findings.append(_finding("verifier_python", "Verifier Python SHA-256 is invalid", "verifier"))
        else:
            python_raw = _external_file(expected.resolve(), findings)
            if python_raw is not None and gov.sha256_bytes(python_raw) != verifier["python_sha256"]:
                findings.append(_finding("verifier_python", "Verifier Python bytes differ", "verifier"))
        if verifier["pyyaml_version"] != "6.0.2" or verifier["isolated"] is not True or verifier["dont_write_bytecode"] is not True:
            findings.append(_finding("verifier_contract", "Verifier must require PyYAML 6.0.2 with -I -B", "verifier"))
        if sys.flags.isolated != 1 or sys.dont_write_bytecode is not True:
            findings.append(_finding("verifier_flags", "Checker must run with Python -I -B", "verifier"))
        try:
            import yaml
        except ImportError as exc:
            findings.append(_finding("verifier_pyyaml", str(exc), "verifier"))
        else:
            if getattr(yaml, "__version__", None) != "6.0.2":
                findings.append(_finding("verifier_pyyaml", "PyYAML version differs", "verifier"))
    return not gov.has_blockers(findings)


def _check_hashes(profile: dict[str, Any], registry: dict[str, Any], findings: list[gov.Finding]) -> None:
    packages = profile["packages"]
    parity = registry.get("parity", {})
    expected_paths = {
        "authority": str(gov.expand_path(parity.get("authority_package", "")).absolute()),
        "replica": str(gov.expand_path(parity.get("replica_package", "")).absolute()),
    }
    for side in ("authority", "replica"):
        if not _keys(packages[side], {"path"}, f"packages.{side}", findings):
            continue
        root = Path(packages[side]["path"]).absolute()
        if str(root) != expected_paths[side]:
            findings.append(_finding("package_path", "Package path differs from registry parity", side))
            continue
        tree = _safe_tree(root)
        findings.extend(_finding("package_tree", f"{item.code}: {item.message}", f"{side}:{item.path}") for item in tree.findings)
        excluded = f"restricted-profiles/{PROFILE_ID}"
        base_records = [record for record in tree.files if record.path != excluded and not record.path.startswith(excluded + "/")]
        base_tree_sha256 = gov._tree_hash(base_records, tree.findings)
        expected_tree = profile["governance"]["base_tree_sha256_by_package"].get(side)
        if base_tree_sha256 != expected_tree:
            findings.append(_finding("package_hash", f"expected={expected_tree} actual={base_tree_sha256}", side))
        records = _manifest(tree)
        declared = profile["governance"]["file_manifest_by_package"].get(side)
        if not isinstance(declared, list):
            findings.append(_finding("file_manifest", "Manifest must be an array", side))
            continue
        declared_paths = [entry.get("path") for entry in declared if isinstance(entry, dict)]
        if len(declared_paths) != len(set(declared_paths)):
            findings.append(_finding("file_manifest", "Manifest paths must be unique", side))
        for entry in declared:
            if not _keys(entry, {"path", "sha256", "executable"}, f"manifest:{side}", findings):
                continue
            record = records.get(entry["path"])
            if record is None or record.sha256 != entry["sha256"] or record.executable is not entry["executable"]:
                findings.append(_finding("file_manifest", "Code/document file differs", f"{side}:{entry['path']}"))
        for name, digest in profile["governance"]["base_files"].items():
            record = records.get(name)
            if record is None or record.sha256 != digest:
                findings.append(_finding("base_file", "Base governance file differs", f"{side}:{name}"))


def _validate_integration_trees(rows: Any, findings: list[gov.Finding]) -> None:
    if not isinstance(rows, list):
        findings.append(_finding("integration_trees", "Exactly six integration trees are required", "integration_trees"))
        return
    paths = []
    for row in rows:
        if not _keys(row, {"path", "tree_sha256"}, "integration_tree", findings):
            continue
        paths.append(row["path"])
        if not isinstance(row["path"], str) or row["path"] not in EXPECTED_INTEGRATIONS or not SHA256_RE.fullmatch(str(row["tree_sha256"])):
            findings.append(_finding("integration_trees", "Integration path or hash is not fixed", "integration_trees"))
    if len(paths) != 6 or set(paths) != EXPECTED_INTEGRATIONS:
        findings.append(_finding("integration_trees", "All six unique fixed integration trees are required", "integration_trees"))


def _check_integration(profile: dict[str, Any], findings: list[gov.Finding]) -> None:
    for entry in profile["integration_files"]:
        path = Path(entry["path"])
        if not path.is_absolute() or not SHA256_RE.fullmatch(str(entry["sha256"])):
            findings.append(_finding("integration", "Absolute path and SHA-256 are required", str(path)))
            continue
        raw = _external_file(path, findings)
        if raw is not None and gov.sha256_bytes(raw) != entry["sha256"]:
            findings.append(_finding("integration", "Integration file differs", str(path)))

    for entry in profile["integration_trees"]:
        tree = _safe_tree(Path(entry["path"]))
        if tree.findings or tree.tree_sha256 != entry["tree_sha256"]:
            findings.append(_finding("integration_tree", "Integration package differs or is unsafe", entry["path"]))


def _check_source(profile: dict[str, Any], findings: list[gov.Finding]) -> None:
    tree = _safe_tree(QUARANTINE_PATH)
    if tree.findings or tree.tree_sha256 != QUARANTINE_TREE_SHA256:
        findings.append(
            _finding(
                "quarantine_tree",
                f"expected={QUARANTINE_TREE_SHA256} actual={tree.tree_sha256}",
                str(QUARANTINE_PATH),
            )
        )


def _tree_state(profile: dict[str, Any], phase: str, findings: list[gov.Finding]) -> str:
    for target, entry in profile["targets"]["review"].items():
        tree = _safe_tree(Path(entry["path"]))
        if tree.tree_sha256 != entry["tree_sha256"] or tree.findings:
            findings.append(_finding("review_tree", "Review tree differs or is unsafe", target))
    runtime_presence: dict[str, bool] = {}
    for target, entry in profile["targets"]["runtime"].items():
        path = Path(entry["path"])
        try:
            path.lstat()
            runtime_presence[target] = True
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                findings.append(_finding("runtime_probe", str(exc), target))
            runtime_presence[target] = False
    if len(set(runtime_presence.values())) != 1:
        findings.append(_finding("runtime_split", "Both runtime targets must be absent or present", "runtime"))
        return "ready_absent"
    if not any(runtime_presence.values()):
        if phase == "active":
            findings.append(_finding("runtime_missing", "Active requires both runtime targets", "runtime"))
        return "ready_absent"
    for target, entry in profile["targets"]["runtime"].items():
        tree = _safe_tree(Path(entry["path"]))
        if tree.tree_sha256 != entry["tree_sha256"] or tree.findings:
            findings.append(_finding("runtime_tree", "Runtime tree differs or is unsafe", target))
    return "active" if phase == "active" else "ready_exact"


def _finding_counter(rows: list[dict[str, Any]], findings: list[gov.Finding], subject: str) -> Counter[tuple[str, str, str]]:
    result: Counter[tuple[str, str, str]] = Counter()
    for row in rows:
        if not _keys(row, {"severity", "code", "subject", "count"}, subject, findings):
            continue
        count = row["count"]
        if type(count) is not int or count < 1 or any("*" in str(row[key]) for key in ("code", "subject")):
            findings.append(_finding("finding_shape", "Finding count and exact subject/code are required", subject))
            continue
        result[(row["severity"], row["code"], row["subject"])] += count
    return result


def _bound_inventory(
    profile: dict[str, Any],
    inventory: dict[str, Any],
    findings: list[gov.Finding],
) -> dict[str, Any]:
    inventory = normalize_restricted_inventory(inventory)
    replacements = {"codex": "authority", "claude": "replica"}
    seen: Counter[str] = Counter()
    records: list[Any] = []
    for original in inventory.get("records", []):
        if not isinstance(original, dict):
            records.append(original)
            continue
        record = dict(original)
        root_id = str(record.get("root_id", ""))
        if record.get("resolved_name") == "skill-governance" and root_id in replacements:
            seen[root_id] += 1
            if not {"tree_sha256", "raw_tree_sha256"}.issubset(record):
                findings.append(_finding("inventory_binding", "Governance inventory record lacks both tree hashes", root_id))
            digest = profile["governance"]["base_tree_sha256_by_package"][replacements[root_id]]
            record["tree_sha256"] = digest
            record["raw_tree_sha256"] = digest
        records.append(record)
    if seen != Counter({"codex": 1, "claude": 1}):
        findings.append(_finding("inventory_binding", f"Expected one fixed governance record per root, found {dict(seen)}", "inventory"))
    return {
        "records": records,
        **{
            key: inventory.get(key)
            for key in ("coverage", "surface_probe", "symlinks", "raw_name_collisions")
        },
    }


def _validate_observations(audit: dict[str, Any], inventory: dict[str, Any], registry: dict[str, Any], findings: list[gov.Finding]) -> None:
    """Distinguish observed legacy policy failures from an incomplete scan."""
    def fail(message: str) -> None:
        findings.append(_finding("observation", message, "audit/inventory"))

    for label, value in (("audit", audit), ("inventory", inventory)):
        rows = value.get("findings")
        if value.get("command") != label or not isinstance(rows, list):
            fail(f"Malformed {label} result")
            return
        if any(not isinstance(row, dict) or set(row) != {"severity", "code", "message", "path"} or any(not isinstance(item, str) for item in row.values()) or row["severity"] not in {"BLOCKING", "ADVISORY"} or not row["code"] for row in rows):
            fail(f"Malformed {label} findings")
            return
    roots = {row["id"]: row for row in registry["roots"]}
    records, coverage, summary = inventory.get("records"), inventory.get("coverage"), inventory.get("summary")
    if inventory.get("status") not in {"ok", "blocked"} or inventory.get("hash_algorithm") != gov.HASH_ALGORITHM or not isinstance(records, list) or not isinstance(coverage, dict) or not isinstance(summary, dict) or set(coverage) != set(roots):
        fail("Inventory schema or root set differs")
        return
    if any(not isinstance(inventory.get(key), dict) for key in ("surface_probe", "collisions", "raw_name_collisions")) or not isinstance(inventory.get("symlinks"), list):
        fail("Inventory surface schema differs")
        return
    counts: Counter[str] = Counter()
    identities = set()
    for row in records:
        if not isinstance(row, dict) or row.get("root_id") not in roots or any(not isinstance(row.get(key), str) for key in ("directory_name", "resolved_name", "relative_path")) or not isinstance(row.get("tree_finding_codes"), list):
            fail("Malformed inventory record")
            return
        identity = (row["root_id"], row["relative_path"])
        if identity in identities:
            fail("Duplicate inventory record")
        identities.add(identity)
        counts[row["root_id"]] += 1
        # The existing vendor cache may contain oversized assets; it cannot
        # supply the fixed runner or the pinned integration packages.
        allowed_tree = {"file_too_large"} if row.get("record_scope") == "plugin-managed" else set()
        if any(code not in allowed_tree for code in row["tree_finding_codes"]):
            fail("Inventory tree scan failed")
    if type(summary.get("total_entries")) is not int or summary["total_entries"] != len(records) or summary.get("roots") != {root: counts[root] for root in roots}:
        fail("Inventory summary counts differ")
    for root_id, row in coverage.items():
        if not isinstance(row, dict) or any(type(row.get(key)) is not int or row[key] != counts[root_id] for key in ("discovered", "recorded")) or type(row.get("complete")) is not bool or row.get("path") != str(gov.expand_path(roots[root_id]["path"])):
            fail("Inventory root coverage differs")
    observed_codes = {
        "codex_disabled_skill_missing", "runtime_skill_identity_mismatch",
        "runtime_skill_name_inferred", "runtime_skill_name_unverified",
        "discovery_symlink_unreviewed", "discovery_symlink_allowlisted",
        "discovery_excluded_scan_truncated", "discovery_excluded_symlink_recorded",
        "unregistered_skill_surface",
    }
    root_paths = {str(gov.expand_path(row["path"])) for row in roots.values()}
    observations = [*inventory["findings"], *[row for row in audit["findings"] if row["code"] in {"root_unavailable", "root_missing", "codex_disabled_skill_missing"}]]
    for row in observations:
        if row["code"] in {"root_unavailable", "root_missing", "codex_disabled_skill_missing"}:
            try:
                Path(row["path"]).lstat()
            except OSError as exc:
                if exc.errno == errno.ENOENT and row["message"].startswith("[Errno 2]") and (row["code"] == "codex_disabled_skill_missing" or row["path"] in root_paths):
                    continue
            fail("Missing path was not confirmed as ENOENT")
        elif row["code"] not in observed_codes:
            fail(f"Unknown or failed inventory observation: {row['code']}")
    # Audit also scans governance receipts and sources. Read/race failures
    # there cannot be reclassified as an exact-comparison drift.
    for row in audit["findings"]:
        if row["code"] not in OBSERVED_AUDIT_POLICY_CODES:
            fail(f"Unknown audit observation: {row['code']}")
        if any(token in row["code"] for token in ("toctou", "unreadable", "open_failed", "read_failed", "lstat_failed", "directory_changed", "path_replaced", "revalidation_failed")):
            fail(f"Audit observation failed: {row['code']}")


def _check_global(profile: dict[str, Any], state: str, findings: list[gov.Finding]) -> tuple[dict[str, Any], dict[str, Any]]:
    base = profile["governance"]["base_files"]
    package = Path(profile["packages"]["authority"]["path"])
    paths = {name: package / name for name in base}
    audit, _ = gov.audit_payload(paths["registry.toml"], paths["registry.lock.json"], paths["catalog.lock.json"], paths["estate.lock.json"], package / "reputation.lock.json")
    if audit.get("status") != "DEGRADED" or audit.get("mutation_allowed") is not False:
        findings.append(_finding("global_status", "Fresh global audit no longer has the required degraded status", "audit"))
    normalized_findings = normalize_restricted_findings(audit.get("findings", []))
    actual = Counter((row["severity"], row["code"], row.get("path", "")) for row in normalized_findings)
    rules = profile["audit"]
    baseline = _finding_counter(rules["baseline_findings"], findings, "baseline_findings")
    delta = rules["allowed_delta_by_state"].get(state, {})
    if not _keys(delta, {"remove", "add"}, f"delta:{state}", findings):
        delta = {"remove": [], "add": []}
    removed = _finding_counter(delta["remove"], findings, f"delta:{state}:remove")
    added = _finding_counter(delta["add"], findings, f"delta:{state}:add")
    related = {(row.get("code"), row.get("subject")) for row in rules["related_subjects"] if isinstance(row, dict) and set(row) == {"code", "subject"}}
    if any((key[1], key[2]) not in related for counter in (removed, added) for key in counter):
        findings.append(_finding("delta_scope", "Allowed delta contains an unrelated code/subject", state))
    if removed - baseline:
        findings.append(_finding("delta_remove", "Allowed removal exceeds the baseline multiset", state))
    expected = baseline - removed + added
    if actual != expected:
        findings.append(_finding("global_findings", f"expected={sorted(expected.items())} actual={sorted(actual.items())}", state))
    registry, registry_findings = gov.load_registry(paths["registry.toml"])
    findings.extend(_finding("registry", f"{item.code}: {item.message}", item.path) for item in registry_findings)
    inventory = gov.inventory_payload(registry) if not gov.has_blockers(registry_findings) else {"records": []}
    _validate_observations(audit, inventory, registry, findings)
    bound_inventory = _bound_inventory(profile, inventory, findings)
    digest = _digest_json(bound_inventory)
    if digest != rules["inventory_sha256_by_state"].get(state):
        findings.append(_finding("inventory", f"expected={rules['inventory_sha256_by_state'].get(state)} actual={digest}", state))
    declared_roots = {(row.get("root_id"), row.get("path")) for row in profile["collision_roots"] if isinstance(row, dict) and set(row) == {"root_id", "path"}}
    actual_roots = {(row.get("id"), str(gov.expand_path(row.get("path", "")))) for row in registry.get("roots", [])}
    if declared_roots != actual_roots:
        findings.append(_finding("collision_roots", "Profile does not enumerate every registry root exactly", "collision_roots"))
    for root_id, root_path in declared_roots:
        try:
            info = Path(root_path).lstat()
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                findings.append(_finding("collision_root_probe", str(exc), str(root_id)))
        else:
            if not info or not Path(root_path).is_dir() or Path(root_path).is_symlink():
                findings.append(_finding("collision_root_type", "Existing root must be a real directory", str(root_id)))
    imozuru = [row for row in inventory.get("records", []) if row.get("resolved_name") == "imozuru" or row.get("directory_name") == "imozuru"]
    expected_runtime = profile["targets"]["runtime"]
    expected_pairs = Counter((entry["root_id"], entry["tree_sha256"]) for entry in expected_runtime.values()) if state != "ready_absent" else Counter()
    actual_pairs = Counter((row.get("root_id"), row.get("raw_tree_sha256")) for row in imozuru)
    if actual_pairs != expected_pairs:
        findings.append(_finding("collision", f"expected={sorted(expected_pairs.items())} actual={sorted(actual_pairs.items())}", "imozuru"))
    parity, parity_findings = gov.parity_payload(registry)
    if parity.get("status") != "ok" or gov.has_blockers(parity_findings):
        findings.append(_finding("package_parity", "Authority and replica governance packages differ", "skill-governance"))
    return audit, inventory


def _check_receipts(raws: dict[str, bytes], profile_raw: bytes, profile: dict[str, Any], phase: str, findings: list[gov.Finding]) -> None:
    required = {"lock.json", "review-receipt.json", "approval-receipt.json"}
    if not required.issubset(raws):
        findings.append(_finding("receipt_missing", f"Missing {sorted(required - set(raws))}", "receipts"))
        return
    lock = _strict_json(raws["lock.json"], "lock.json", findings)
    review = _strict_json(raws["review-receipt.json"], "review-receipt.json", findings)
    approval = _strict_json(raws["approval-receipt.json"], "approval-receipt.json", findings)
    if not all((lock, review, approval)):
        return
    if not _keys(lock, {"schema_version", "profile_sha256", "review_receipt_sha256", "approval_receipt_sha256"}, "lock", findings):
        return
    profile_sha = gov.sha256_bytes(profile_raw)
    if lock != {"schema_version": 1, "profile_sha256": profile_sha, "review_receipt_sha256": gov.sha256_bytes(raws["review-receipt.json"]), "approval_receipt_sha256": gov.sha256_bytes(raws["approval-receipt.json"])}:
        findings.append(_finding("lock_binding", "Lock does not exactly bind profile and receipts", "lock"))
    if _keys(review, {"schema_version", "profile_sha256", "evidence_refs"}, "review_receipt", findings):
        if review["schema_version"] != 1 or review["profile_sha256"] != profile_sha or not review["evidence_refs"]:
            findings.append(_finding("review_receipt", "Review receipt identity or evidence is invalid", "review-receipt"))
        kinds: set[str] = set()
        evidence_paths: set[str] = set()
        evidence_hashes: set[str] = set()
        target_hash = profile["targets"]["review"]["codex"]["tree_sha256"]
        expected_targets = {"codex": target_hash, "claude": target_hash}
        for ref in review["evidence_refs"]:
            if _keys(ref, {"kind", "path", "sha256"}, "evidence_ref", findings):
                kind = str(ref["kind"])
                kinds.add(kind)
                evidence_path = Path(ref["path"])
                if not evidence_path.is_absolute() or not SHA256_RE.fullmatch(str(ref["sha256"])):
                    findings.append(_finding("evidence_ref", "Absolute path and SHA-256 are required", str(evidence_path)))
                    continue
                if str(evidence_path) in evidence_paths or ref["sha256"] in evidence_hashes:
                    findings.append(_finding("evidence_unique", "Each evidence kind needs unique path and bytes", kind))
                evidence_paths.add(str(evidence_path))
                evidence_hashes.add(ref["sha256"])
                data = _external_file(evidence_path, findings)
                if data is None:
                    continue
                if gov.sha256_bytes(data) != ref["sha256"]:
                    findings.append(_finding("evidence_hash", "Evidence differs", ref["path"]))
                    continue
                envelope = _strict_json(data, ref["path"], findings)
                envelope_keys = {
                    "schema_version", "kind", "profile_id", "source", "target_tree_sha256",
                    "status", "reviewer", "reviewed_at", "details",
                }
                if envelope is None or not _keys(envelope, envelope_keys, "evidence_envelope", findings):
                    continue
                source = {"id": SOURCE_ID, "revision": SOURCE_REVISION}
                reviewer = envelope.get("reviewer")
                valid_reviewer = _keys(reviewer, {"identity", "independent"}, "evidence_reviewer", findings)
                if (
                    envelope.get("schema_version") != 1
                    or envelope.get("kind") != kind
                    or envelope.get("profile_id") != PROFILE_ID
                    or envelope.get("source") != source
                    or envelope.get("target_tree_sha256") != expected_targets
                    or envelope.get("status") != "PASS"
                    or not isinstance(envelope.get("details"), dict)
                    or not valid_reviewer
                    or not isinstance(reviewer.get("identity"), str)
                    or not reviewer.get("identity").strip()
                    or type(reviewer.get("independent")) is not bool
                    or (kind == "code-review" and reviewer.get("independent") is not True)
                ):
                    findings.append(_finding("evidence_envelope", "Evidence subject, result, reviewer, or target differs", kind))
                try:
                    reviewed_at = datetime.fromisoformat(str(envelope["reviewed_at"]).replace("Z", "+00:00"))
                    if reviewed_at.tzinfo is None:
                        raise ValueError("timezone missing")
                except (KeyError, TypeError, ValueError) as exc:
                    findings.append(_finding("evidence_time", str(exc), kind))
        if kinds != EVIDENCE_KINDS or len(review["evidence_refs"]) != len(EVIDENCE_KINDS):
            findings.append(_finding("review_evidence", f"Expected exactly {sorted(EVIDENCE_KINDS)}", "review-receipt"))
    subject = {"profile_id": PROFILE_ID, "collection_id": COLLECTION_ID, "source_id": SOURCE_ID, "revision": SOURCE_REVISION}
    if _keys(approval, {"schema_version", "profile_sha256", "review_receipt_sha256", "approved", "approved_at", "subject"}, "approval_receipt", findings):
        if approval.get("schema_version") != 1 or approval.get("profile_sha256") != profile_sha or approval.get("review_receipt_sha256") != gov.sha256_bytes(raws["review-receipt.json"]) or approval.get("approved") is not True or approval.get("subject") != subject:
            findings.append(_finding("approval_receipt", "Approval receipt chain or subject differs", "approval-receipt"))
        try:
            approved_at = datetime.fromisoformat(str(approval["approved_at"]).replace("Z", "+00:00"))
            if approved_at.tzinfo is None:
                raise ValueError("timezone missing")
        except (TypeError, ValueError) as exc:
            findings.append(_finding("approval_time", str(exc), "approval-receipt"))
    if phase == "active":
        _check_delivery(profile, profile_sha, raws, findings)


def _git(repo: Path, arguments: list[str]) -> subprocess.CompletedProcess[bytes]:
    environment = {
        "PATH": "/usr/bin:/bin", "LC_ALL": "C", "HOME": "/nonexistent",
        "XDG_CONFIG_HOME": "/nonexistent", "GIT_CONFIG_NOSYSTEM": "1",
    }
    return subprocess.run(
        [
            "/usr/bin/git", "--no-replace-objects", "--literal-pathspecs",
            "-C", str(repo), *arguments,
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
        env=environment,
        close_fds=True,
    )


def _check_git_object_overrides(repo: Path, findings: list[gov.Finding], subject: str) -> bool:
    result = _git(repo, ["rev-parse", "--path-format=absolute", "--git-common-dir"])
    raw_path = result.stdout.strip().decode("utf-8", "replace")
    if result.returncode != 0 or not raw_path or not Path(raw_path).is_absolute():
        findings.append(_finding("delivery_git_dir", "Canonical common Git directory is unavailable", subject))
        return False
    common_dir = Path(os.path.realpath(raw_path))
    try:
        (common_dir / "info/grafts").lstat()
    except OSError as exc:
        if exc.errno == errno.ENOENT:
            return True
        findings.append(_finding("delivery_grafts", str(exc), subject))
        return False
    findings.append(_finding("delivery_grafts", "Legacy Git graft file is forbidden", subject))
    return False


def _delivery_repo_path(name: str, logical: Path, findings: list[gov.Finding]) -> Path | None:
    if name == "codex" and logical == EXPECTED_REPOS["codex"]:
        return _codex_physical_path(logical, findings, name)
    try:
        info = logical.lstat()
    except OSError as exc:
        findings.append(_finding("delivery_repo", str(exc), name))
        return None
    if stat.S_ISLNK(info.st_mode):
        findings.append(_finding("delivery_repo", "Only the fixed Codex repository alias is allowed", name))
        return None
    if not stat.S_ISDIR(info.st_mode):
        findings.append(_finding("delivery_repo", "Repository root must be a real directory", name))
        return None
    return logical


def _git_blob_oid(data: bytes, object_format: str) -> str:
    body = b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    return (hashlib.sha1(body) if object_format == "sha1" else hashlib.sha256(body)).hexdigest()


def _commit_tree_records(
    repo: Path,
    commit: str,
    expected: dict[str, tuple[bytes, bool]],
    findings: list[gov.Finding],
    subject: str,
) -> None:
    format_result = _git(repo, ["rev-parse", "--show-object-format"])
    object_format = format_result.stdout.strip().decode("ascii", "replace")
    if format_result.returncode != 0 or object_format not in {"sha1", "sha256"}:
        findings.append(_finding("delivery_git_format", "Unsupported or unavailable Git object format", subject))
        return
    expected_commit_length = 40 if object_format == "sha1" else 64
    if len(commit) != expected_commit_length:
        findings.append(_finding("delivery_commit", "Commit length differs from repository object format", subject))
        return
    result = _git(repo, ["ls-tree", "-r", "-z", "--full-tree", commit, "--", *sorted(expected)])
    if result.returncode != 0:
        findings.append(_finding("delivery_tree", "Could not read delivery commit tree", subject))
        return
    actual: dict[str, tuple[str, str, str]] = {}
    try:
        for record in result.stdout.split(b"\0"):
            if not record:
                continue
            header, raw_path = record.split(b"\t", 1)
            mode, object_type, oid = header.decode("ascii", "strict").split(" ")
            path = raw_path.decode("utf-8", "strict")
            if path in actual:
                raise ValueError(f"duplicate path: {path}")
            actual[path] = (mode, object_type, oid)
    except (UnicodeDecodeError, ValueError) as exc:
        findings.append(_finding("delivery_tree", f"Malformed ls-tree output: {exc}", subject))
        return
    if set(actual) != set(expected):
        findings.append(
            _finding(
                "delivery_tree_paths",
                f"expected={sorted(expected)} actual={sorted(actual)}",
                subject,
            )
        )
        return
    for path, (data, executable) in expected.items():
        expected_entry = (
            "100755" if executable else "100644",
            "blob",
            _git_blob_oid(data, object_format),
        )
        if actual[path] != expected_entry:
            findings.append(_finding("delivery_tree_blob", "Commit bytes or executable mode differ", f"{subject}:{path}"))


def _check_delivery(
    profile: dict[str, Any],
    profile_sha: str,
    expected_artifacts: dict[str, bytes],
    findings: list[gov.Finding],
) -> None:
    raw = _external_file(DELIVERY_PROOF, findings)
    proof = _strict_json(raw, str(DELIVERY_PROOF), findings) if raw is not None else None
    keys = {
        "schema_version", "generation", "success", "profile_sha256", "target_tree_sha256",
        "delivery_commits", "remote_observations",
    }
    if proof is None or not _keys(proof, keys, "delivery_proof", findings):
        return
    target_hashes = {name: entry["tree_sha256"] for name, entry in profile["targets"]["runtime"].items()}
    if proof.get("schema_version") != 1 or proof.get("generation") != profile["generation"] or proof.get("success") is not True or proof.get("profile_sha256") != profile_sha or proof.get("target_tree_sha256") != target_hashes:
        findings.append(_finding("delivery_proof", "Delivery proof identity or target hashes differ", str(DELIVERY_PROOF)))
    repos = profile["delivery"]["repos"]
    observations = proof.get("remote_observations")
    if (
        set(repos) != {"codex", "claude"}
        or set(proof.get("delivery_commits", {})) != set(repos)
        or not isinstance(observations, dict)
        or set(observations) != set(repos)
    ):
        findings.append(_finding("delivery_repos", "Exactly Codex and Claude delivery commits and observations are required", "delivery_proof"))
        return
    for name, repo in repos.items():
        if not _keys(repo, {"path", "scope_files"}, f"delivery.{name}", findings):
            continue
        repo_path = Path(repo["path"])
        physical_repo = _delivery_repo_path(name, repo_path, findings)
        if physical_repo is None:
            continue
        if not _check_git_object_overrides(physical_repo, findings, name):
            continue
        side = "authority" if name == "codex" else "replica"
        required_scope = {
            Path(profile["packages"][side]["path"]) / row["path"]
            for row in profile["governance"]["file_manifest_by_package"][side]
        }
        target_root = Path(profile["targets"]["runtime"][name]["path"])
        try:
            physical_target_root = physical_repo / target_root.relative_to(repo_path)
        except ValueError:
            findings.append(_finding("delivery_target_path", "Runtime target is outside its fixed repository", name))
            continue
        target_tree = _safe_tree(physical_target_root)
        required_scope.update(target_root / record.path for record in target_tree.files)
        required_scope.update(
            Path(entry["path"])
            for entry in profile["integration_files"]
            if Path(entry["path"]).is_relative_to(repo_path)
        )
        for entry in profile["integration_trees"]:
            integration_root = Path(entry["path"])
            if integration_root.is_relative_to(repo_path):
                tree = _safe_tree(physical_repo / integration_root.relative_to(repo_path))
                if tree.findings or tree.tree_sha256 != entry["tree_sha256"]:
                    findings.append(_finding("delivery_integration", "Integration tree differs during delivery validation", entry["path"]))
                required_scope.update(integration_root / record.path for record in tree.files)
        declared_scope = {repo_path / entry["path"] for entry in repo["scope_files"]}
        artifact_paths = {
            Path(profile["packages"][side]["path"]) / "restricted-profiles" / PROFILE_ID / filename
            for filename in PROFILE_ARTIFACTS
        }
        if declared_scope & artifact_paths:
            findings.append(_finding("delivery_scope_cycle", "Receipt-chain artifacts must not be declared in profile scope", name))
            continue
        if not required_scope.issubset(declared_scope):
            missing = sorted(str(path) for path in required_scope - declared_scope)
            findings.append(_finding("delivery_scope_coverage", f"Missing governed paths: {missing}", name))
            continue
        scope_ok = True
        commit_records: dict[str, tuple[bytes, bool]] = {}
        for entry in repo["scope_files"]:
            if not _keys(entry, {"path", "sha256", "executable"}, f"delivery.{name}.scope", findings):
                scope_ok = False
                continue
            record = _external_record(physical_repo / entry["path"], findings)
            if record is None or gov.sha256_bytes(record[0]) != entry["sha256"] or record[1] is not entry["executable"]:
                findings.append(_finding("delivery_scope", "Governed file differs from delivered bytes", f"{name}:{entry['path']}"))
                scope_ok = False
                continue
            commit_records[str(Path(entry["path"]).as_posix())] = record
        for artifact_path in artifact_paths:
            try:
                relative = artifact_path.relative_to(repo_path).as_posix()
            except ValueError:
                findings.append(_finding("delivery_artifact_path", "Receipt-chain artifact is outside repository", str(artifact_path)))
                scope_ok = False
                continue
            record = _external_record(physical_repo / relative, findings)
            if record is None:
                scope_ok = False
                continue
            if record[0] != expected_artifacts.get(artifact_path.name):
                findings.append(_finding("delivery_artifact", "Receipt-chain bytes changed after validation", str(artifact_path)))
                scope_ok = False
                continue
            commit_records[relative] = record
        if not scope_ok:
            continue
        commit = proof["delivery_commits"].get(name, "")
        if not COMMIT_RE.fullmatch(commit):
            findings.append(_finding("delivery_commit", "Invalid commit", name))
            continue
        result = _git(physical_repo, ["merge-base", "--is-ancestor", commit, "HEAD"])
        if result.returncode != 0:
            findings.append(_finding("delivery_ancestor", "Delivery commit is not an ancestor of local HEAD", name))
            continue
        _commit_tree_records(physical_repo, commit, commit_records, findings, name)
        observation = observations[name]
        observation_keys = {"url", "branch", "oid", "observed_at"}
        if not _keys(observation, observation_keys, f"remote_observations.{name}", findings):
            continue
        observed_oid = observation.get("oid", "")
        if (
            observation.get("url") != EXPECTED_REMOTES[name]
            or observation.get("branch") != REMOTE_BRANCH
            or not isinstance(observed_oid, str)
            or not COMMIT_RE.fullmatch(observed_oid)
        ):
            findings.append(_finding("delivery_remote", "Remote URL, branch, or observed OID differs", name))
            continue
        local_remote = _git(physical_repo, ["remote", "get-url", "origin"])
        if local_remote.returncode != 0 or local_remote.stdout.strip().decode("utf-8", "replace") != EXPECTED_REMOTES[name]:
            findings.append(_finding("delivery_remote", "Local origin URL differs from the fixed remote", name))
            continue
        try:
            observed_at = datetime.fromisoformat(str(observation["observed_at"]).replace("Z", "+00:00"))
            if observed_at.tzinfo is None:
                raise ValueError("timezone missing")
            observed_at = observed_at.astimezone(timezone.utc)
            expiry = datetime.fromisoformat(str(profile["valid_until"]).replace("Z", "+00:00")).astimezone(timezone.utc)
            if observed_at > datetime.now(timezone.utc) + REMOTE_OBSERVATION_FUTURE_SKEW or observed_at > expiry:
                raise ValueError("remote observation is from the future or outside the profile validity window")
        except (TypeError, ValueError) as exc:
            findings.append(_finding("delivery_remote_time", str(exc), name))
            continue
        tracking = _git(physical_repo, ["rev-parse", "--verify", "refs/remotes/origin/main"])
        tracking_oid = tracking.stdout.strip().decode("ascii", "replace")
        if tracking.returncode != 0 or not COMMIT_RE.fullmatch(tracking_oid):
            findings.append(_finding("delivery_tracking", "origin/main tracking ref is unavailable", name))
            continue
        if tracking_oid != observed_oid:
            findings.append(_finding("delivery_tracking", "origin/main differs from the recorded observation", name))
            continue
        graph = ((commit, observed_oid), (observed_oid, "HEAD"))
        if any(_git(physical_repo, ["merge-base", "--is-ancestor", older, newer]).returncode != 0 for older, newer in graph):
            findings.append(_finding("delivery_remote_graph", "Expected delivery <= observation == origin/main <= HEAD", name))


def _restricted_audit_payload(profile_dir: Path, phase: str) -> tuple[dict[str, Any], list[gov.Finding]]:
    findings: list[gov.Finding] = []
    raws = _profile_artifacts(profile_dir, findings)
    profile_raw = raws.get("profile.json")
    profile = _strict_json(profile_raw, "profile.json", findings) if profile_raw is not None else None
    if profile_raw is None:
        findings.append(_finding("profile_missing", "Fixed profile is missing", str(profile_dir)))
    audit: dict[str, Any] = {}
    state = "unknown"
    if profile is not None and _validate_profile(profile, findings):
        registry_path = Path(profile["packages"]["authority"]["path"]) / "registry.toml"
        registry, registry_findings = gov.load_registry(registry_path)
        findings.extend(_finding("registry", f"{item.code}: {item.message}", item.path) for item in registry_findings)
        if not gov.has_blockers(registry_findings):
            _check_hashes(profile, registry, findings)
            _check_source(profile, findings)
            _check_integration(profile, findings)
            state = _tree_state(profile, phase, findings)
            audit, _ = _check_global(profile, state, findings)
            _check_receipts(raws, profile_raw, profile, phase, findings)
    drift = [item for item in findings if item.code in GLOBAL_DRIFT_CODES]
    scoped = [item for item in findings if item.code not in GLOBAL_DRIFT_CODES]
    payload = {
        "command": "restricted-audit",
        "phase": phase,
        "profile_id": PROFILE_ID,
        "restricted_status": "blocked" if gov.has_blockers(findings) else phase,
        "capability_scope": CAPABILITY_SCOPE,
        "capability_status": "blocked" if gov.has_blockers(scoped) else phase,
        "global_drift": "HOLD" if drift else "unchanged",
        "global_drift_findings": [asdict(item) for item in drift],
        "global_status": audit.get("status", "unknown"),
        "global_mutation_allowed": audit.get("mutation_allowed"),
        "runtime_state": state,
        "delivery_proof_path": str(DELIVERY_PROOF),
        "findings": [asdict(item) for item in findings],
        "global_findings": audit.get("findings", []),
    }
    return payload, findings


def restricted_audit_payload(profile_dir: Path, phase: str) -> tuple[dict[str, Any], list[gov.Finding]]:
    """Convert malformed or racing external state into a blocking scoped result."""
    try:
        return _restricted_audit_payload(profile_dir, phase)
    except (KeyError, TypeError, ValueError, OSError, subprocess.SubprocessError) as exc:
        finding = _finding("invalid_state", f"{type(exc).__name__}: {exc}", str(profile_dir))
        return {
            "command": "restricted-audit",
            "phase": phase,
            "profile_id": PROFILE_ID,
            "restricted_status": "blocked",
            "capability_scope": CAPABILITY_SCOPE,
            "capability_status": "blocked",
            "global_drift": "unknown",
            "global_drift_findings": [],
            "global_status": "unknown",
            "global_mutation_allowed": None,
            "runtime_state": "unknown",
            "delivery_proof_path": str(DELIVERY_PROOF),
            "findings": [asdict(finding)],
            "global_findings": [],
        }, [finding]


def audit_exit_code(payload: dict[str, Any], findings: list[gov.Finding], phase: str, require_capability: bool) -> int:
    """Keep the old exit contract unless the fixed capability is requested."""
    if not require_capability:
        return 0 if payload.get("restricted_status") == phase and not gov.has_blockers(findings) else 2
    scoped = [item for item in findings if item.code not in GLOBAL_DRIFT_CODES]
    drift = any(item.code in GLOBAL_DRIFT_CODES for item in findings)
    expected_status = "blocked" if drift or gov.has_blockers(scoped) else phase
    valid = (
        payload.get("capability_scope") == CAPABILITY_SCOPE
        and payload.get("capability_status") == phase
        and payload.get("restricted_status") == expected_status
        and payload.get("global_drift") == ("HOLD" if drift else "unchanged")
        and payload.get("global_status") == "DEGRADED"
        and payload.get("global_mutation_allowed") is False
        and not gov.has_blockers(scoped)
    )
    return 0 if valid else 2


def summary_payload(payload: dict[str, Any]) -> dict[str, Any]:
    result = {key: value for key, value in payload.items() if key not in {"findings", "global_findings", "global_drift_findings"}}
    result["findings"] = [row for row in payload.get("findings", []) if row["code"] not in GLOBAL_DRIFT_CODES]
    result["global_finding_count"] = len(payload.get("global_findings", []))
    result["global_drift_finding_count"] = len(payload.get("global_drift_findings", []))
    result["global_drift_codes"] = [row["code"] for row in payload.get("global_drift_findings", [])]
    return result
