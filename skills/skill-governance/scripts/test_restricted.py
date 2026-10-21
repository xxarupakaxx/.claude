from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("governance", SCRIPTS / "governance.py")
assert spec and spec.loader
gov = importlib.util.module_from_spec(spec)
sys.modules["governance"] = gov
spec.loader.exec_module(gov)
spec = importlib.util.spec_from_file_location("restricted", SCRIPTS / "restricted.py")
assert spec and spec.loader
restricted = importlib.util.module_from_spec(spec)
sys.modules["restricted"] = restricted
spec.loader.exec_module(restricted)


def write(path: Path, data: bytes = b"x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def finding_rows(*items: tuple[str, str, str, int]) -> list[dict[str, object]]:
    return [{"severity": a, "code": b, "subject": c, "count": d} for a, b, c, d in items]


def evidence_envelope(kind: str, target_hash: str, **updates: object) -> bytes:
    value: dict[str, object] = {
        "schema_version": 1,
        "kind": kind,
        "profile_id": restricted.PROFILE_ID,
        "source": {"id": restricted.SOURCE_ID, "revision": restricted.SOURCE_REVISION},
        "target_tree_sha256": {"codex": target_hash, "claude": target_hash},
        "status": "PASS",
        "reviewer": {"identity": f"reviewer-{kind}", "independent": kind == "code-review"},
        "reviewed_at": "2026-10-20T00:00:00Z",
        "details": {"fixture": kind},
    }
    value.update(updates)
    return json.dumps(value, sort_keys=True).encode()


def delivery_fixture(base: Path, *, stale_ancestor: bool = False, missing_artifact: bool = False, stale_integration: bool = False) -> tuple[dict[str, object], dict[str, object], Path]:
    repos: dict[str, dict[str, object]] = {}
    commits: dict[str, str] = {}
    target_hash = "a" * 64
    for name in ("codex", "claude"):
        repo = base / name
        repo.mkdir()
        subprocess.run(["/usr/bin/git", "init", "-q", str(repo)], check=True)
        subprocess.run(["/usr/bin/git", "-C", str(repo), "remote", "add", "origin", restricted.EXPECTED_REMOTES[name]], check=True)
        subprocess.run(["/usr/bin/git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "--allow-empty", "-qm", "base"], check=True)
        write(repo / "skills/imozuru/SKILL.md", b"stale" if stale_ancestor else name.encode())
        write(repo / "scripts/governance.py", b"stale-module" if stale_ancestor else b"module")
        write(repo / "skills/research/SKILL.md", b"caller")
        write(repo / "skills/research/references/source.md", b"stale" if stale_integration else b"fixed")
        artifact_dir = repo / "restricted-profiles" / restricted.PROFILE_ID
        for filename in restricted.PROFILE_ARTIFACTS:
            if missing_artifact and filename == "approval-receipt.json":
                continue
            current = b"profile" if filename == "profile.json" else filename.encode()
            write(artifact_dir / filename, b"stale-" + current if stale_ancestor else current)
        subprocess.run(["/usr/bin/git", "-C", str(repo), "add", "."], check=True)
        subprocess.run(["/usr/bin/git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-qm", "fixture"], check=True)
        proof_commit = subprocess.check_output(["/usr/bin/git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
        if stale_ancestor:
            write(repo / "skills/imozuru/SKILL.md", name.encode())
            write(repo / "scripts/governance.py", b"module")
            for filename in restricted.PROFILE_ARTIFACTS:
                write(artifact_dir / filename, b"profile" if filename == "profile.json" else filename.encode())
            subprocess.run(["/usr/bin/git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["/usr/bin/git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-qm", "current"], check=True)
        elif missing_artifact:
            write(artifact_dir / "approval-receipt.json", b"approval-receipt.json")
        if stale_integration:
            write(repo / "skills/research/references/source.md", b"fixed")
        commits[name] = proof_commit
        subprocess.run(["/usr/bin/git", "-C", str(repo), "update-ref", "refs/remotes/origin/main", proof_commit], check=True)
        scope_paths = ("skills/imozuru/SKILL.md", "scripts/governance.py", "skills/research/SKILL.md", "skills/research/references/source.md")
        repos[name] = {
            "path": str(repo),
            "scope_files": [
                {"path": path, "sha256": gov.sha256_path(repo / path), "executable": False}
                for path in scope_paths
            ],
        }
    profile: dict[str, object] = {
        "targets": {"runtime": {name: {"path": str(base / name / "skills/imozuru"), "tree_sha256": target_hash} for name in repos}},
        "packages": {"authority": {"path": str(base / "codex")}, "replica": {"path": str(base / "claude")}},
        "governance": {
            "file_manifest_by_package": {
                side: [{"path": "scripts/governance.py"}]
                for side in ("authority", "replica")
            }
        },
        "generation": 2,
        "integration_trees": [
            {"path": str(base / name / "skills/research"), "tree_sha256": restricted._safe_tree(base / name / "skills/research").tree_sha256}
            for name in repos
        ],
        "integration_files": [],
        "delivery": {"repos": repos},
        "valid_until": "2027-01-18T00:00:00Z",
    }
    profile_sha = gov.sha256_bytes(b"profile")
    proof = {
        "schema_version": 2, "observation_scope": "delivery-commit-reachability", "generation": 2, "success": True,
        "profile_sha256": profile_sha,
        "target_tree_sha256": {name: target_hash for name in repos},
        "delivery_commits": commits,
        "remote_observations": {
            name: {
                "url": restricted.EXPECTED_REMOTES[name],
                "branch": restricted.REMOTE_BRANCH,
                "oid": commit,
                "observed_at": datetime.now(timezone.utc).isoformat(),
            }
            for name, commit in commits.items()
        },
    }
    proof_path = base / "proof.json"
    proof_path.write_text(json.dumps(proof), encoding="utf-8")
    return profile, repos, proof_path


def fixture_artifacts(base: Path) -> dict[str, bytes]:
    artifact_dir = base / "codex/restricted-profiles" / restricted.PROFILE_ID
    return {name: (artifact_dir / name).read_bytes() for name in restricted.PROFILE_ARTIFACTS}


def ephemeral_inventory(token: str) -> dict[str, object]:
    prefix = "/Users/yoshiki/ghq/github.com/xxarupakaxx/.codex/tmp/arg0"
    rows = [
        {
            "allowlisted": False,
            "excluded": True,
            "path": f"{prefix}/codex-arg0{token}/{leaf}",
            "root_relative_path": f"arg0/codex-arg0{token}/{leaf}",
            "target": str(restricted.EPHEMERAL_ARG0_TARGET),
            "target_exists": True,
        }
        for leaf in ("apply_patch", "applypatch", "codex-execve-wrapper")
    ]
    unrelated = {
        "allowlisted": False,
        "excluded": True,
        "path": f"{prefix}/persistent/unrelated",
        "root_relative_path": "arg0/persistent/unrelated",
        "target": "/fixed/unrelated",
        "target_exists": False,
    }
    rows.append(unrelated)
    return {
        "records": [],
        "coverage": {},
        "surface_probe": {"symlinks": json.loads(json.dumps(rows))},
        "symlinks": rows,
        "raw_name_collisions": {},
    }


def ephemeral_findings(token: str) -> list[dict[str, object]]:
    prefix = "/Users/yoshiki/ghq/github.com/xxarupakaxx/.codex/tmp/arg0"
    message = f"Excluded-surface symlink recorded without following: {restricted.EPHEMERAL_ARG0_TARGET}"
    return [
        {
            "severity": "ADVISORY",
            "code": "discovery_excluded_symlink_recorded",
            "message": message,
            "path": f"{prefix}/codex-arg0{token}/{leaf}",
        }
        for leaf in ("apply_patch", "applypatch", "codex-execve-wrapper")
    ]


class RestrictedAuditTests(unittest.TestCase):
    def mirror_fixture(self, base: Path):
        mirrors = {f"vault-{name}-mirror": base / name / "mirror" for name in ("codex", "claude")}
        runtimes = {name: base / name / "runtime" for name in ("codex", "claude")}
        profile = {"targets": {"runtime": {}}}
        registry = {"roots": []}
        records = []
        for name, runtime in runtimes.items():
            root_id = f"vault-{name}-mirror"
            write(runtime / "SKILL.md", b"approved document")
            write(runtime / "scripts/run.py", b"runtime only")
            write(mirrors[root_id] / "imozuru/SKILL.md", b"approved document")
            profile["targets"]["runtime"][name] = {"path": str(runtime), "root_id": name, "tree_sha256": restricted._safe_tree(runtime).tree_sha256}
            registry["roots"].append({"id": root_id, "path": str(mirrors[root_id]), "role": "mirror-only", "collision_scope": "catalog-only", "runtimes": [], "targetable": False})
            records.append({"root_id": root_id, "relative_path": "imozuru", "record_scope": "mirror-only", "root_role": "mirror-only", "runtimes": [], "directory_name": "imozuru", "resolved_name": "imozuru", "raw_tree_sha256": restricted._safe_tree(mirrors[root_id] / "imozuru").tree_sha256})
        return profile, registry, records, mirrors, runtimes

    def test_mirror_requires_fixed_identity_and_approved_content(self) -> None:
        cases = [("valid", None, None)]
        cases += [("row", key, value) for key, value in {"relative_path": "other/imozuru", "record_scope": "active", "root_role": "active", "runtimes": ["codex"], "directory_name": "other", "resolved_name": "other"}.items()]
        cases += [("root", key, value) for key, value in {"path": "/other", "role": "active", "collision_scope": "runtime", "runtimes": ["codex"], "targetable": True}.items()]
        cases += [("runtime", "path", "/other"), ("runtime", "root_id", "other"), ("runtime", "tree_sha256", "0" * 64), ("row", "raw_tree_sha256", "0" * 64), ("duplicate-root", None, None)]
        for case, key, value in cases:
            with self.subTest(case=case, key=key), tempfile.TemporaryDirectory() as temporary:
                profile, registry, rows, mirrors, runtimes = self.mirror_fixture(Path(os.path.realpath(temporary)))
                if case == "row":
                    rows[0][key] = value
                elif case == "root":
                    registry["roots"][0][key] = value
                elif case == "runtime":
                    profile["targets"]["runtime"]["codex"][key] = value
                elif case == "duplicate-root":
                    registry["roots"].append(dict(registry["roots"][0]))
                findings = []
                with mock.patch.object(restricted, "EXPECTED_MIRRORS", mirrors), mock.patch.object(restricted, "EXPECTED_RUNTIMES", runtimes):
                    pairs = restricted._verified_mirror_pairs(profile, registry, rows, findings)
                self.assertEqual(sum(pairs.values()), 2 if case == "valid" else 1)
                self.assertEqual(bool(findings), case != "valid")

    def test_mirror_rejects_changed_content_extra_executable_and_unsafe_files(self) -> None:
        for name in ("codex", "claude"):
            for case in ("changed", "extra", "executable", "symlink", "hardlink", "fifo", "ancestor-symlink"):
                with self.subTest(name=name, case=case), tempfile.TemporaryDirectory() as temporary:
                    base = Path(os.path.realpath(temporary))
                    profile, registry, rows, mirrors, runtimes = self.mirror_fixture(base)
                    root_id = f"vault-{name}-mirror"
                    mirror = mirrors[root_id] / "imozuru"
                    document = mirror / "SKILL.md"
                    if case == "changed":
                        document.write_bytes(b"different document")
                    elif case == "extra":
                        write(mirror / "scripts/run.py")
                    elif case == "executable":
                        document.chmod(0o755)
                    elif case == "symlink":
                        document.unlink()
                        document.symlink_to(runtimes[name] / "SKILL.md")
                    elif case == "hardlink":
                        document.unlink()
                        os.link(runtimes[name] / "SKILL.md", document)
                    elif case == "fifo":
                        os.mkfifo(mirror / "pipe")
                    else:
                        moved = base / "moved"
                        mirrors[root_id].rename(moved)
                        mirrors[root_id].symlink_to(moved, target_is_directory=True)
                    # Even a freshly observed inventory hash must not authorize unsafe content.
                    for row in rows:
                        if row["root_id"] == root_id:
                            row["raw_tree_sha256"] = restricted._safe_tree(mirror).tree_sha256
                    findings = []
                    with mock.patch.object(restricted, "EXPECTED_MIRRORS", mirrors), mock.patch.object(restricted, "EXPECTED_RUNTIMES", runtimes):
                        pairs = restricted._verified_mirror_pairs(profile, registry, rows, findings)
                    self.assertNotIn(root_id, {pair[0] for pair in pairs})
                    self.assertTrue(findings)

    def test_mirror_rejects_observation_race_and_leaves_unknown_root_unapproved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile, registry, rows, mirrors, runtimes = self.mirror_fixture(Path(os.path.realpath(temporary)))
            unknown = dict(rows[0], root_id="unknown-mirror")
            failed = gov.TreeResult("raced", None, [], [restricted._finding("toctou", "changed", "raced")])
            findings = []
            with mock.patch.object(restricted, "EXPECTED_MIRRORS", mirrors), mock.patch.object(restricted, "EXPECTED_RUNTIMES", runtimes), mock.patch.object(restricted, "_safe_tree", return_value=failed):
                pairs = restricted._verified_mirror_pairs(profile, registry, [*rows, unknown], findings)
            self.assertFalse(pairs)
            self.assertEqual(len(findings), 2)

    def test_governance_pins_restricted_checker_bytes(self) -> None:
        self.assertEqual(gov.RESTRICTED_CHECKER_SHA256, gov.sha256_path(SCRIPTS / "restricted.py"))

    def test_strict_json_rejects_duplicate_and_nonfinite(self) -> None:
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}'):
            with self.subTest(raw=raw), self.assertRaises((gov.StrictJSONError, json.JSONDecodeError)):
                gov._strict_json_loads(raw)

    def test_secure_tree_rejects_symlink_hardlink_and_special_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(root / "file")
            os.link(root / "file", root / "hard")
            (root / "link").symlink_to(root / "file")
            os.mkfifo(root / "fifo")
            result = gov.scan_tree(root, reject_hardlinks=True)
            self.assertTrue({"hardlink", "symlink", "special_file"}.issubset({item.code for item in result.findings}))
            self.assertIsNone(result.tree_sha256)

    def test_profile_scan_rejects_hardlink_inside_fd_anchored_chain(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "skill-governance"
            profile = package / "restricted-profiles" / restricted.PROFILE_ID
            write(profile / "profile.json", b"{}")
            os.link(profile / "profile.json", profile / "copy.json")
            findings: list[gov.Finding] = []
            restricted._profile_artifacts(profile, findings)
            self.assertIn("restricted_profile_tree", {item.code for item in findings})
            self.assertTrue(any("hardlink" in item.message for item in findings))

    def test_ready_runtime_must_be_both_absent_or_both_exact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(os.path.realpath(temporary))
            reviews = {name: base / f"review-{name}" for name in ("codex", "claude")}
            runtimes = {name: base / f"runtime-{name}" for name in reviews}
            for path in reviews.values():
                write(path / "SKILL.md")
            profile = {"targets": {"review": {}, "runtime": {}}}
            for name in reviews:
                digest = gov.scan_tree(reviews[name]).tree_sha256
                profile["targets"]["review"][name] = {"root_id": name, "path": str(reviews[name]), "tree_sha256": digest}
                profile["targets"]["runtime"][name] = {"root_id": name, "path": str(runtimes[name]), "tree_sha256": digest}
            findings: list[gov.Finding] = []
            self.assertEqual(restricted._tree_state(profile, "ready", findings), "ready_absent")
            self.assertFalse(findings)
            write(runtimes["codex"] / "SKILL.md")
            findings = []
            restricted._tree_state(profile, "ready", findings)
            self.assertIn("restricted_runtime_split", {item.code for item in findings})
            write(runtimes["claude"] / "SKILL.md")
            findings = []
            self.assertEqual(restricted._tree_state(profile, "active", findings), "active")
            self.assertFalse(findings)

    def test_finding_delta_requires_exact_non_wildcard_subject(self) -> None:
        findings: list[gov.Finding] = []
        counter = restricted._finding_counter(
            finding_rows(("BLOCKING", "baseline_drift", "*/imozuru", 1)), findings, "delta"
        )
        self.assertFalse(counter)
        self.assertIn("restricted_finding_shape", {item.code for item in findings})

    def test_global_audit_compares_complete_multiset_and_inventory(self) -> None:
        baseline = finding_rows(("BLOCKING", "old", "unrelated", 1), ("BLOCKING", "fix", "imozuru", 1))
        audit_rows = [
            {"severity": "BLOCKING", "code": "old", "message": "x", "path": "unrelated"},
            {"severity": "ADVISORY", "code": "resolved", "message": "x", "path": "imozuru"},
        ]
        inventory = {
            "records": [
                {"root_id": root, "resolved_name": "skill-governance", "tree_sha256": "f" * 64, "raw_tree_sha256": "e" * 64}
                for root in ("codex", "claude")
            ],
            "coverage": {}, "surface_probe": {}, "symlinks": [], "raw_name_collisions": {},
        }
        profile = {
            "packages": {"authority": {"path": "/pkg"}},
            "governance": {
                "base_files": {name: "0" * 64 for name in ("registry.toml", "registry.lock.json", "estate.lock.json", "catalog.lock.json")},
                "base_tree_sha256_by_package": {"authority": "a" * 64, "replica": "b" * 64},
            },
            "audit": {
                "baseline_findings": baseline,
                "allowed_delta_by_state": {"ready_absent": {"remove": [baseline[1]], "add": finding_rows(("ADVISORY", "resolved", "imozuru", 1))}},
                "related_subjects": [{"code": "fix", "subject": "imozuru"}, {"code": "resolved", "subject": "imozuru"}],
                "inventory_sha256_by_state": {"ready_absent": ""},
            },
            "collision_roots": [{"root_id": "root", "path": "/skills"}],
            "targets": {"runtime": {}},
        }
        profile["audit"]["inventory_sha256_by_state"]["ready_absent"] = restricted._digest_json(
            restricted._bound_inventory(profile, inventory, [])
        )
        registry = {"roots": [{"id": "root", "path": "/skills"}]}
        with mock.patch.object(gov, "audit_payload", return_value=({"status": "DEGRADED", "mutation_allowed": False, "findings": audit_rows}, [])), mock.patch.object(gov, "load_registry", return_value=(registry, [])), mock.patch.object(gov, "inventory_payload", return_value=inventory), mock.patch.object(gov, "parity_payload", return_value=({"status": "ok"}, [])), mock.patch.object(restricted, "_validate_observations"):
            findings: list[gov.Finding] = []
            restricted._check_global(profile, "ready_absent", findings)
            self.assertFalse(findings)
            audit_rows.append({"severity": "BLOCKING", "code": "new", "message": "x", "path": "unrelated"})
            restricted._check_global(profile, "ready_absent", findings)
            self.assertIn("restricted_global_findings", {item.code for item in findings})
            inventory["records"].append({"root_id": "unknown-mirror", "directory_name": "imozuru", "raw_tree_sha256": "a" * 64})
            findings = []
            restricted._check_global(profile, "ready_absent", findings)
            self.assertIn("restricted_collision", {item.code for item in findings})

    def test_inventory_binding_removes_only_governance_profile_self_reference(self) -> None:
        profile = {
            "governance": {
                "base_tree_sha256_by_package": {
                    "authority": "a" * 64,
                    "replica": "b" * 64,
                }
            }
        }
        inventory = {
            "records": [
                {
                    "root_id": root,
                    "resolved_name": "skill-governance",
                    "tree_sha256": "c" * 64,
                    "raw_tree_sha256": "d" * 64,
                    "other": f"preserved-{root}",
                }
                for root in ("codex", "claude")
            ]
            + [
                {
                    "root_id": "codex",
                    "resolved_name": "research",
                    "tree_sha256": "e" * 64,
                    "raw_tree_sha256": "f" * 64,
                }
            ],
            "coverage": {"kept": True},
            "surface_probe": {},
            "symlinks": [],
            "raw_name_collisions": {},
        }
        findings: list[gov.Finding] = []
        bound = restricted._bound_inventory(profile, inventory, findings)
        self.assertFalse(findings)
        self.assertEqual(bound["records"][0]["tree_sha256"], "a" * 64)
        self.assertEqual(bound["records"][1]["raw_tree_sha256"], "b" * 64)
        self.assertEqual(bound["records"][0]["other"], "preserved-codex")
        self.assertEqual(inventory["records"][0]["tree_sha256"], "c" * 64)

        profile_artifact_drift = json.loads(json.dumps(inventory))
        for record in profile_artifact_drift["records"][:2]:
            record["tree_sha256"] = "0" * 64
            record["raw_tree_sha256"] = "1" * 64
        rebound = restricted._bound_inventory(profile, profile_artifact_drift, findings)
        self.assertEqual(restricted._digest_json(bound), restricted._digest_json(rebound))

        unrelated_drift = json.loads(json.dumps(inventory))
        unrelated_drift["records"][2]["tree_sha256"] = "0" * 64
        rebound = restricted._bound_inventory(profile, unrelated_drift, findings)
        self.assertNotEqual(restricted._digest_json(bound), restricted._digest_json(rebound))

    def test_current_exec_symlink_normalization_is_narrow_and_lossless(self) -> None:
        before = ephemeral_inventory("Ab12Cd")
        after = ephemeral_inventory("Ef34Gh")
        normalized_before = restricted.normalize_restricted_inventory(before)
        normalized_after = restricted.normalize_restricted_inventory(after)
        self.assertEqual(restricted._digest_json(normalized_before), restricted._digest_json(normalized_after))
        self.assertEqual(len(normalized_before["symlinks"]), 4)
        self.assertEqual(
            len(normalized_before["surface_probe"]["symlinks"]),
            4,
        )

        def mutate_rows(value: dict[str, object], change: object) -> None:
            for location in (value["symlinks"], value["surface_probe"]["symlinks"]):
                change(location)

        bad: dict[str, dict[str, object]] = {}
        for scenario in (
            "path_only", "relative_only", "arg0_macos", "tmp_path",
            "target", "flags", "unknown_leaf", "count",
        ):
            candidate = json.loads(json.dumps(after))
            if scenario == "path_only":
                mutate_rows(candidate, lambda rows: rows[0].update(path=rows[0]["path"].replace("Ef34Gh", "Ij56Kl")))
            elif scenario == "relative_only":
                mutate_rows(candidate, lambda rows: rows[0].update(root_relative_path=rows[0]["root_relative_path"].replace("Ef34Gh", "Ij56Kl")))
            elif scenario == "arg0_macos":
                mutate_rows(candidate, lambda rows: rows[0].update(path=rows[0]["path"].replace("/arg0/", "/arg0-macos/"), root_relative_path=rows[0]["root_relative_path"].replace("arg0/", "arg0-macos/")))
            elif scenario == "tmp_path":
                mutate_rows(candidate, lambda rows: rows[0].update(path=rows[0]["path"].replace("/tmp/arg0/", "/tmp/path/"), root_relative_path=rows[0]["root_relative_path"].replace("arg0/", "path/")))
            elif scenario == "target":
                mutate_rows(candidate, lambda rows: rows[0].update(target="/wrong/target"))
            elif scenario == "flags":
                mutate_rows(candidate, lambda rows: rows[0].update(target_exists=False))
            elif scenario == "unknown_leaf":
                mutate_rows(candidate, lambda rows: rows.append({**rows[0], "path": rows[0]["path"].rsplit("/", 1)[0] + "/other", "root_relative_path": rows[0]["root_relative_path"].rsplit("/", 1)[0] + "/other"}))
            else:
                mutate_rows(candidate, lambda rows: rows.pop(0))
            bad[scenario] = candidate
        expected = restricted._digest_json(normalized_before)
        for scenario, candidate in bad.items():
            with self.subTest(scenario=scenario):
                actual = restricted._digest_json(restricted.normalize_restricted_inventory(candidate))
                self.assertNotEqual(expected, actual)

    def test_current_exec_finding_normalization_preserves_exact_multiset(self) -> None:
        before = restricted.normalize_restricted_findings(ephemeral_findings("Ab12Cd"))
        after = restricted.normalize_restricted_findings(ephemeral_findings("Ef34Gh"))
        key = lambda row: (row["severity"], row["code"], row["path"])
        self.assertEqual(Counter(map(key, before)), Counter(map(key, after)))
        wrong_target = ephemeral_findings("Ef34Gh")
        wrong_target[0]["message"] = "Excluded-surface symlink recorded without following: /wrong/target"
        self.assertNotEqual(
            Counter(map(key, before)),
            Counter(map(key, restricted.normalize_restricted_findings(wrong_target))),
        )
        added = ephemeral_findings("Ef34Gh") + [dict(ephemeral_findings("Ef34Gh")[0])]
        self.assertNotEqual(
            Counter(map(key, before)),
            Counter(map(key, restricted.normalize_restricted_findings(added))),
        )

    def test_related_runtime_subject_allowlist_is_exact(self) -> None:
        expected = {
            f"{root}:{skill}"
            for root in ("codex", "claude")
            for skill in (
                "imozuru", "research", "ask-skill-router", "skill-governance",
                "creating-html-documents",
            )
        }
        self.assertEqual(restricted.RELATED_RUNTIME_SUBJECTS, expected)
        self.assertNotIn("other:imozuru", restricted.RELATED_RUNTIME_SUBJECTS)
        self.assertNotIn("codex:other", restricted.RELATED_RUNTIME_SUBJECTS)

    def test_receipts_bind_profile_review_approval_and_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(os.path.realpath(temporary))
            target_hash = "a" * 64
            profile = {"targets": {"review": {name: {"tree_sha256": target_hash} for name in ("codex", "claude")}}}
            profile_raw = json.dumps(profile, sort_keys=True).encode()
            profile_sha = gov.sha256_bytes(profile_raw)
            refs = []
            for kind in sorted(restricted.EVIDENCE_KINDS):
                evidence = base / f"{kind}.json"
                write(evidence, evidence_envelope(kind, target_hash))
                refs.append({"kind": kind, "path": str(evidence), "sha256": gov.sha256_path(evidence)})
            review = {"schema_version": 1, "profile_sha256": profile_sha, "evidence_refs": refs}
            review_raw = json.dumps(review, sort_keys=True).encode()
            approval = {"schema_version": 1, "profile_sha256": profile_sha, "review_receipt_sha256": gov.sha256_bytes(review_raw), "approved": True, "approved_at": "2026-10-20T00:00:00Z", "subject": {"profile_id": restricted.PROFILE_ID, "collection_id": restricted.COLLECTION_ID, "source_id": restricted.SOURCE_ID, "revision": restricted.SOURCE_REVISION}}
            approval_raw = json.dumps(approval, sort_keys=True).encode()
            lock = {"schema_version": 1, "profile_sha256": profile_sha, "review_receipt_sha256": gov.sha256_bytes(review_raw), "approval_receipt_sha256": gov.sha256_bytes(approval_raw)}
            raws = {"lock.json": json.dumps(lock, sort_keys=True).encode(), "review-receipt.json": review_raw, "approval-receipt.json": approval_raw}
            findings: list[gov.Finding] = []
            restricted._check_receipts(raws, profile_raw, profile, "ready", findings)
            self.assertFalse(findings)
            changed_profile_findings: list[gov.Finding] = []
            restricted._check_receipts(raws, profile_raw + b" ", profile, "ready", changed_profile_findings)
            self.assertIn("restricted_lock_binding", {item.code for item in changed_profile_findings})
            raws["review-receipt.json"] = review_raw + b" "
            restricted._check_receipts(raws, profile_raw, profile, "ready", findings)
            self.assertIn("restricted_lock_binding", {item.code for item in findings})

    def test_evidence_rejects_wrong_subject_failure_and_reused_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(os.path.realpath(temporary))
            target_hash = "a" * 64
            profile = {"targets": {"review": {name: {"tree_sha256": target_hash} for name in ("codex", "claude")}}}
            profile_raw = json.dumps(profile, sort_keys=True).encode()
            profile_sha = gov.sha256_bytes(profile_raw)
            shared = base / "shared.json"
            write(shared, evidence_envelope("source-manifest", target_hash, profile_id="wrong", status="FAIL"))
            refs = [
                {"kind": kind, "path": str(shared), "sha256": gov.sha256_path(shared)}
                for kind in sorted(restricted.EVIDENCE_KINDS)
            ]
            review_raw = json.dumps({"schema_version": 1, "profile_sha256": profile_sha, "evidence_refs": refs}, sort_keys=True).encode()
            approval_raw = json.dumps({"schema_version": 1, "profile_sha256": profile_sha, "review_receipt_sha256": gov.sha256_bytes(review_raw), "approved": True, "approved_at": "2026-10-20T00:00:00Z", "subject": {"profile_id": restricted.PROFILE_ID, "collection_id": restricted.COLLECTION_ID, "source_id": restricted.SOURCE_ID, "revision": restricted.SOURCE_REVISION}}, sort_keys=True).encode()
            lock_raw = json.dumps({"schema_version": 1, "profile_sha256": profile_sha, "review_receipt_sha256": gov.sha256_bytes(review_raw), "approval_receipt_sha256": gov.sha256_bytes(approval_raw)}, sort_keys=True).encode()
            findings: list[gov.Finding] = []
            restricted._check_receipts({"lock.json": lock_raw, "review-receipt.json": review_raw, "approval-receipt.json": approval_raw}, profile_raw, profile, "ready", findings)
            codes = {item.code for item in findings}
            self.assertIn("restricted_evidence_unique", codes)
            self.assertIn("restricted_evidence_envelope", codes)

    def test_active_delivery_commit_contains_scope_and_four_chain_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(os.path.realpath(temporary))
            profile, repos, proof_path = delivery_fixture(base)
            with mock.patch.object(restricted, "DELIVERY_PROOF", proof_path):
                findings: list[gov.Finding] = []
                restricted._check_delivery(profile, gov.sha256_bytes(b"profile"), fixture_artifacts(base), findings)
                self.assertFalse(findings)
                for repo in repos.values():
                    declared = {row["path"] for row in repo["scope_files"]}
                    self.assertFalse(any(name in path for name in restricted.PROFILE_ARTIFACTS for path in declared))
                write(Path(repos["codex"]["path"]) / "scripts/governance.py", b"drift")
                restricted._check_delivery(profile, gov.sha256_bytes(b"profile"), fixture_artifacts(base), findings)
                self.assertIn("restricted_delivery_scope", {item.code for item in findings})

    def test_delivery_allows_only_fixed_codex_repository_alias(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(os.path.realpath(temporary))
            profile, repos, proof_path = delivery_fixture(base)
            canonical = Path(repos["codex"]["path"])
            logical = base / "codex-logical"
            logical.symlink_to(canonical, target_is_directory=True)
            profile["delivery"]["repos"]["codex"]["path"] = str(logical)
            profile["packages"]["authority"]["path"] = str(logical)
            profile["targets"]["runtime"]["codex"]["path"] = str(logical / "skills/imozuru")
            expected_repos = {"codex": logical, "claude": Path(repos["claude"]["path"])}
            with (
                mock.patch.object(restricted, "DELIVERY_PROOF", proof_path),
                mock.patch.object(restricted, "EXPECTED_REPOS", expected_repos),
                mock.patch.object(restricted, "EXPECTED_CODEX_REPO_CANONICAL", canonical),
            ):
                findings: list[gov.Finding] = []
                restricted._check_delivery(profile, gov.sha256_bytes(b"profile"), fixture_artifacts(base), findings)
                logical_tree = restricted._safe_tree(logical / "skills/imozuru")
                logical_record = restricted._external_record(logical / "scripts/governance.py", findings)
            self.assertFalse(findings)
            self.assertFalse(logical_tree.findings)
            self.assertIsNotNone(logical_record)

            claude_alias = base / "claude-logical"
            claude_alias.symlink_to(Path(repos["claude"]["path"]), target_is_directory=True)
            findings = []
            self.assertIsNone(restricted._delivery_repo_path("claude", claude_alias, findings))
            self.assertIn("restricted_delivery_repo", {item.code for item in findings})

            wrong_alias = base / "codex-wrong"
            wrong_target = base / "wrong-target"
            wrong_target.mkdir()
            wrong_alias.symlink_to(wrong_target, target_is_directory=True)
            with (
                mock.patch.object(restricted, "EXPECTED_REPOS", {"codex": wrong_alias, "claude": Path(repos["claude"]["path"])}),
                mock.patch.object(restricted, "EXPECTED_CODEX_REPO_CANONICAL", canonical),
            ):
                findings = []
                self.assertIsNone(restricted._delivery_repo_path("codex", wrong_alias, findings))

            canonical_alias = base / "canonical-alias"
            canonical_alias.symlink_to(canonical, target_is_directory=True)
            nested_logical = base / "codex-nested-logical"
            nested_logical.symlink_to(canonical_alias, target_is_directory=True)
            with (
                mock.patch.object(restricted, "EXPECTED_REPOS", {"codex": nested_logical, "claude": Path(repos["claude"]["path"])}),
                mock.patch.object(restricted, "EXPECTED_CODEX_REPO_CANONICAL", canonical_alias),
            ):
                findings = []
                self.assertIsNone(restricted._delivery_repo_path("codex", nested_logical, findings))

            with (
                mock.patch.object(restricted, "EXPECTED_REPOS", expected_repos),
                mock.patch.object(restricted, "EXPECTED_CODEX_REPO_CANONICAL", canonical),
                mock.patch.object(restricted.os, "readlink", side_effect=(str(canonical), str(wrong_target))),
            ):
                findings = []
                self.assertIsNone(restricted._codex_physical_path(logical / "skills", findings, "race"))

    def test_delivery_rejects_random_ancestor_and_missing_artifact(self) -> None:
        for scenario in ("stale", "missing", "integration_scope", "integration_blob"):
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as temporary:
                base = Path(os.path.realpath(temporary))
                profile, repos, proof_path = delivery_fixture(base, stale_ancestor=scenario == "stale", missing_artifact=scenario == "missing", stale_integration=scenario == "integration_blob")
                if scenario == "integration_scope":
                    repos["codex"]["scope_files"] = [row for row in repos["codex"]["scope_files"] if row["path"] != "skills/research/references/source.md"]
                with mock.patch.object(restricted, "DELIVERY_PROOF", proof_path):
                    findings: list[gov.Finding] = []
                    restricted._check_delivery(profile, gov.sha256_bytes(b"profile"), fixture_artifacts(base), findings)
                if scenario == "integration_scope":
                    self.assertIn("restricted_delivery_scope_coverage", {item.code for item in findings})
                elif scenario == "integration_blob":
                    self.assertIn("restricted_delivery_tree_blob", {item.code for item in findings})
                    self.assertTrue(any(item.code == "restricted_delivery_tree_blob" and "skills/research/references/source.md" in item.path for item in findings))
                else:
                    self.assertTrue({"restricted_delivery_tree_blob", "restricted_delivery_tree_paths"} & {item.code for item in findings})

    def test_delivery_ignores_replace_refs_and_blocks_grafts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(os.path.realpath(temporary))
            profile, repos, proof_path = delivery_fixture(base)
            proof = json.loads(proof_path.read_text(encoding="utf-8"))
            repo = Path(repos["codex"]["path"])
            empty_tree = subprocess.check_output(
                ["/usr/bin/git", "-C", str(repo), "rev-parse", "HEAD^^{tree}"],
                text=True,
            ).strip()
            unrelated = subprocess.check_output(
                ["/usr/bin/git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit-tree", empty_tree, "-m", "unrelated"],
                text=True,
            ).strip()
            current_tree = subprocess.check_output(["/usr/bin/git", "-C", str(repo), "rev-parse", "HEAD^{tree}"], text=True).strip()
            forged = subprocess.check_output(
                ["/usr/bin/git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit-tree", current_tree, "-p", unrelated, "-m", "forged"],
                text=True,
            ).strip()
            subprocess.run(["/usr/bin/git", "-C", str(repo), "replace", "HEAD", forged], check=True)
            self.assertEqual(subprocess.run(["/usr/bin/git", "-C", str(repo), "merge-base", "--is-ancestor", unrelated, "HEAD"]).returncode, 0)
            subprocess.run(["/usr/bin/git", "-C", str(repo), "replace", unrelated, "HEAD"], check=True)
            proof["delivery_commits"]["codex"] = unrelated
            proof["remote_observations"]["codex"]["oid"] = unrelated
            subprocess.run(["/usr/bin/git", "-C", str(repo), "update-ref", "refs/remotes/origin/main", unrelated], check=True)
            proof_path.write_text(json.dumps(proof), encoding="utf-8")
            with mock.patch.object(restricted, "DELIVERY_PROOF", proof_path):
                findings: list[gov.Finding] = []
                restricted._check_delivery(profile, gov.sha256_bytes(b"profile"), fixture_artifacts(base), findings)
            self.assertIn("restricted_delivery_ancestor", {item.code for item in findings})

        with tempfile.TemporaryDirectory() as temporary:
            base = Path(os.path.realpath(temporary))
            profile, repos, proof_path = delivery_fixture(base)
            grafts = Path(repos["codex"]["path"]) / ".git/info/grafts"
            write(grafts, b"")
            with mock.patch.object(restricted, "DELIVERY_PROOF", proof_path):
                findings = []
                restricted._check_delivery(profile, gov.sha256_bytes(b"profile"), fixture_artifacts(base), findings)
            self.assertIn("restricted_delivery_grafts", {item.code for item in findings})

    def test_delivery_accepts_remote_updates_without_importing_them(self) -> None:
        for name in ("codex", "claude"):
            for topology in ("remote-descendant", "diverged", "remote-merge"):
                with self.subTest(name=name, topology=topology), tempfile.TemporaryDirectory() as temporary:
                    base = Path(os.path.realpath(temporary))
                    profile, repos, proof_path = delivery_fixture(base)
                    repo = Path(repos[name]["path"])
                    def git(*args):
                        return subprocess.check_output(["/usr/bin/git", "-C", str(repo), *args], text=True).strip()
                    approved = git("rev-parse", "HEAD")
                    if topology == "remote-merge":
                        git("checkout", "-q", "--detach", "HEAD^")
                    # The observed remote tree may differ; only the approved C is bound.
                    remote_file = "remote-unreviewed" if topology == "remote-merge" else "scripts/governance.py"
                    write(repo / remote_file, b"unreviewed remote update")
                    git("add", remote_file)
                    git("-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-qm", "remote update")
                    if topology == "remote-merge":
                        git("-c", "user.name=t", "-c", "user.email=t@example.invalid", "merge", "-q", "--no-edit", approved)
                    observed = git("rev-parse", "HEAD")
                    git("checkout", "-q", "--detach", approved)
                    if topology == "diverged":
                        write(repo / "local-note", b"local only")
                        git("add", "local-note")
                        git("-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-qm", "local unrelated")
                    proof = json.loads(proof_path.read_bytes())
                    proof["remote_observations"][name]["oid"] = observed
                    proof_path.write_text(json.dumps(proof))
                    git("update-ref", "refs/remotes/origin/main", observed)
                    self.assertEqual((repo / "scripts/governance.py").read_bytes(), b"module")
                    with mock.patch.object(restricted, "DELIVERY_PROOF", proof_path):
                        findings = []
                        restricted._check_delivery(profile, gov.sha256_bytes(b"profile"), fixture_artifacts(base), findings)
                    self.assertFalse(findings)

    def test_delivery_rejects_legacy_or_ambiguous_observation_scope(self) -> None:
        for scenario in ("legacy", "missing-scope", "wrong-scope"):
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as temporary:
                base = Path(os.path.realpath(temporary))
                profile, repos, proof_path = delivery_fixture(base)
                proof = json.loads(proof_path.read_bytes())
                if scenario == "legacy":
                    proof["schema_version"] = 1
                elif scenario == "missing-scope":
                    del proof["observation_scope"]
                else:
                    proof["observation_scope"] = "remote-runtime-approved"
                proof_path.write_text(json.dumps(proof))
                with mock.patch.object(restricted, "DELIVERY_PROOF", proof_path):
                    findings = []
                    restricted._check_delivery(profile, gov.sha256_bytes(b"profile"), fixture_artifacts(base), findings)
                self.assertTrue(findings)

    def test_delivery_rejects_invalid_remote_observations(self) -> None:
        for scenario in ("missing", "branch", "unreached", "tracking", "future"):
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as temporary:
                base = Path(os.path.realpath(temporary))
                profile, repos, proof_path = delivery_fixture(base)
                proof = json.loads(proof_path.read_text(encoding="utf-8"))
                if scenario == "missing":
                    del proof["remote_observations"]["claude"]
                elif scenario == "branch":
                    proof["remote_observations"]["codex"]["branch"] = "refs/heads/not-main"
                elif scenario == "unreached":
                    repo = Path(repos["codex"]["path"])
                    base_commit = subprocess.check_output(["/usr/bin/git", "-C", str(repo), "rev-parse", "HEAD^"], text=True).strip()
                    proof["remote_observations"]["codex"]["oid"] = base_commit
                    subprocess.run(["/usr/bin/git", "-C", str(repo), "update-ref", "refs/remotes/origin/main", base_commit], check=True)
                elif scenario == "tracking":
                    repo = Path(repos["codex"]["path"])
                    base_commit = subprocess.check_output(["/usr/bin/git", "-C", str(repo), "rev-parse", "HEAD^"], text=True).strip()
                    subprocess.run(["/usr/bin/git", "-C", str(repo), "update-ref", "refs/remotes/origin/main", base_commit], check=True)
                else:
                    proof["remote_observations"]["codex"]["observed_at"] = "2100-01-01T00:00:00Z"
                proof_path.write_text(json.dumps(proof), encoding="utf-8")
                with mock.patch.object(restricted, "DELIVERY_PROOF", proof_path):
                    findings: list[gov.Finding] = []
                    restricted._check_delivery(profile, gov.sha256_bytes(b"profile"), fixture_artifacts(base), findings)
                expected = {
                    "missing": "restricted_delivery_repos",
                    "branch": "restricted_delivery_remote",
                    "unreached": "restricted_delivery_remote_graph",
                    "tracking": "restricted_delivery_tracking",
                    "future": "restricted_delivery_remote_time",
                }
                self.assertIn(expected[scenario], {item.code for item in findings})

    def test_capability_drift_preserves_default_exit_and_summary(self) -> None:
        profile_raw = b'{"packages":{"authority":{"path":"/fixture"}}}'
        audit = {"status": "DEGRADED", "mutation_allowed": False, "findings": []}
        for codes in (("global_findings", "inventory"), ("inventory", "observation"), ("unknown",)):
            with self.subTest(codes=codes), mock.patch.object(restricted, "_profile_artifacts", return_value={"profile.json": profile_raw}), mock.patch.object(restricted, "_validate_profile", return_value=True), mock.patch.object(gov, "load_registry", return_value=({}, [])), mock.patch.object(restricted, "_check_hashes"), mock.patch.object(restricted, "_check_source"), mock.patch.object(restricted, "_check_integration"), mock.patch.object(restricted, "_tree_state", return_value="active"), mock.patch.object(restricted, "_check_receipts"):
                def observe(profile, state, findings):
                    findings.extend(restricted._finding(code, code) for code in codes)
                    return audit, {}
                with mock.patch.object(restricted, "_check_global", side_effect=observe):
                    payload, findings = restricted.restricted_audit_payload(Path("/fixture"), "active")
                expected = "active" if set(codes) == {"global_findings", "inventory"} else "blocked"
                self.assertEqual(payload["restricted_status"], "blocked")
                self.assertEqual(payload["capability_status"], expected)
                self.assertEqual(restricted.audit_exit_code(payload, findings, "active", False), 2)
                self.assertEqual(restricted.audit_exit_code(payload, findings, "active", True), 0 if expected == "active" else 2)
                summary = restricted.summary_payload(payload)
                self.assertEqual(summary["capability_status"], expected)
                self.assertNotIn("global_findings", summary)
                for key in ("capability_status", "capability_scope", "global_drift", "restricted_status"):
                    bad = dict(payload); bad.pop(key)
                    self.assertEqual(restricted.audit_exit_code(bad, findings, "active", True), 2)
                bad = dict(payload, restricted_status="active")
                self.assertEqual(restricted.audit_exit_code(bad, findings, "active", True), 2)

    def test_cli_capability_mode_is_explicit_and_unknown_flags_fail(self) -> None:
        args = ["restricted-audit", "--phase", "active", "--json"]
        self.assertFalse(gov.build_parser().parse_args(args).require_capability)
        self.assertTrue(gov.build_parser().parse_args(args + ["--require-capability", "--summary"]).require_capability)
        with mock.patch("sys.stderr"), self.assertRaises(SystemExit):
            gov.build_parser().parse_args(args + ["--ignore-global"])

    def test_fixed_integration_trees_reject_omissions_duplicates_and_other_paths(self) -> None:
        rows = [{"path": path, "tree_sha256": "a" * 64} for path in sorted(restricted.EXPECTED_INTEGRATIONS)]
        findings = []; restricted._validate_integration_trees(rows, findings)
        self.assertFalse(findings)
        for bad in (None, [], rows[:-1], rows + rows[:1], [{**rows[0], "path": "/other"}] + rows[1:], [{**rows[0], "tree_sha256": "bad"}] + rows[1:]):
            findings = []; restricted._validate_integration_trees(bad, findings)
            self.assertTrue(gov.has_blockers(findings))

    def test_integration_tree_rejects_changed_missing_extra_and_unsafe_files(self) -> None:
        for scenario in ("modify", "remove", "extra", "symlink", "hardlink"):
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as temporary:
                root = Path(os.path.realpath(temporary))
                write(root / "SKILL.md", b"fixed")
                profile = {"integration_files": [], "integration_trees": [{"path": str(root), "tree_sha256": restricted._safe_tree(root).tree_sha256}]}
                findings = []; restricted._check_integration(profile, findings)
                self.assertFalse(findings)
                if scenario == "modify": write(root / "SKILL.md", b"changed")
                elif scenario == "remove": (root / "SKILL.md").unlink()
                elif scenario == "extra": write(root / "extra.py", b"extra")
                elif scenario == "symlink": (root / "extra").symlink_to(root / "SKILL.md")
                else: os.link(root / "SKILL.md", root / "extra")
                restricted._check_integration(profile, findings)
                self.assertIn("restricted_integration_tree", {item.code for item in findings})

    def test_observation_distinguishes_absence_from_failed_or_malformed_scan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            missing = str(Path(temporary) / "absent")
            registry = {"roots": [{"id": "test", "path": missing}]}
            audit = {"command": "audit", "findings": []}
            inventory = {
                "command": "inventory", "status": "blocked", "hash_algorithm": gov.HASH_ALGORITHM,
                "records": [], "coverage": {"test": {"path": missing, "discovered": 0, "recorded": 0, "complete": False}},
                "summary": {"total_entries": 0, "roots": {"test": 0}},
                "surface_probe": {}, "collisions": {}, "raw_name_collisions": {}, "symlinks": [],
                "findings": [{"severity": "BLOCKING", "code": "root_unavailable", "message": "[Errno 2] fixture path missing", "path": missing}],
            }
            findings = []; restricted._validate_observations(audit, inventory, registry, findings)
            self.assertFalse(findings)
            known_policy = {"command": "audit", "findings": [{"severity": "BLOCKING", "code": "baseline_drift", "message": "legacy mismatch", "path": "unrelated"}]}
            findings = []; restricted._validate_observations(known_policy, inventory, registry, findings)
            self.assertFalse(findings)
            for scenario in ("unknown", "audit_unknown", "stat_error", "read", "count", "roots", "schema", "present", "permission", "race"):
                with self.subTest(scenario=scenario):
                    inv = json.loads(json.dumps(inventory)); aud = json.loads(json.dumps(audit))
                    if scenario == "unknown": inv["findings"][0]["code"] = "new_unknown"
                    elif scenario in ("audit_unknown", "stat_error"): aud["findings"] = [{"severity": "BLOCKING", "code": "scanner_timeout" if scenario == "audit_unknown" else "stat_error", "message": "failed", "path": missing}]
                    elif scenario == "read": inv["findings"][0]["code"] = "discovery_unreadable"
                    elif scenario == "count": inv["summary"]["total_entries"] = 1
                    elif scenario == "roots": inv["coverage"]["extra"] = {}
                    elif scenario == "schema": inv["findings"] = "bad"
                    elif scenario == "race": aud["findings"] = [{"severity": "BLOCKING", "code": "toctou_changed", "message": "changed", "path": missing}]
                    probe = mock.patch.object(Path, "lstat", side_effect=PermissionError("denied")) if scenario == "permission" else mock.patch.object(Path, "lstat", return_value=object()) if scenario == "present" else mock.patch.object(restricted, "SHA256_RE", restricted.SHA256_RE)
                    with probe:
                        findings = []; restricted._validate_observations(aud, inv, registry, findings)
                    self.assertTrue(gov.has_blockers(findings))

    def test_malformed_profile_is_blocked_without_exception(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "skill-governance"
            profile_dir = package / "restricted-profiles" / restricted.PROFILE_ID
            write(profile_dir / "profile.json", b'{"schema_version":1}')
            payload, findings = restricted.restricted_audit_payload(profile_dir, "ready")
            self.assertEqual(payload["restricted_status"], "blocked")
            self.assertTrue(gov.has_blockers(findings))


if __name__ == "__main__":
    unittest.main()
