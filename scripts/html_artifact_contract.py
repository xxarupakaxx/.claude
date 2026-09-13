#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "config" / "html-surfaces.json"
REQUIRED_ROUTES = {
    "html",
    "design-artifact",
    "html-wireframe",
    "html-prototype",
    "html-plan",
    "html-diagram",
}
FORBIDDEN_ELEMENTS = {"base", "embed", "iframe", "object"}
RESOURCE_ATTRS = {
    "audio": ("src",),
    "embed": ("src",),
    "iframe": ("src",),
    "img": ("src", "srcset"),
    "image": ("href", "xlink:href"),
    "input": ("src",),
    "link": ("href",),
    "object": ("data",),
    "script": ("src",),
    "source": ("src", "srcset"),
    "track": ("src",),
    "video": ("poster", "src"),
}
HTML_LITERAL_RE = re.compile(r"(?P<literal>[A-Za-z0-9_./:${}*<>-]+\.html)")


@dataclass(frozen=True)
class ContractIssue:
    code: str
    severity: str
    path: str
    message: str
    line: int | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "code": self.code,
            "severity": self.severity,
            "path": self.path,
            "message": self.message,
        }
        if self.line is not None:
            payload["line"] = self.line
        return payload


class HtmlContractError(ValueError):
    pass


def issue(
    code: str,
    severity: str,
    path: str,
    message: str,
    line: int | None = None,
) -> ContractIssue:
    return ContractIssue(code, severity, path, message, line)


def load_manifest(path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise HtmlContractError(f"manifest could not be loaded: {path}: {error}") from error
    if not isinstance(value, dict):
        raise HtmlContractError("manifest root must be an object")
    return value


def merge_profile(manifest: dict[str, Any], name: str) -> dict[str, Any]:
    profiles = manifest.get("staticProfiles")
    if not isinstance(profiles, dict) or name not in profiles:
        raise HtmlContractError(f"unknown static profile: {name}")
    raw = profiles[name]
    if not isinstance(raw, dict):
        raise HtmlContractError(f"static profile must be an object: {name}")
    parent_name = raw.get("extends")
    if isinstance(parent_name, str):
        parent = merge_profile(manifest, parent_name)
    else:
        parent = {}
    merged = {**parent, **raw}
    merged.pop("extends", None)
    return merged


def is_external_url(value: str) -> bool:
    candidate = value.strip()
    if not candidate or candidate.startswith("#"):
        return False
    if candidate.startswith("//"):
        return True
    parsed = urlparse(candidate)
    return parsed.scheme.lower() in {"http", "https"}


def is_navigation_url(value: str) -> bool:
    candidate = value.strip()
    if not candidate or candidate.startswith("#"):
        return False
    parsed = urlparse(candidate)
    return parsed.scheme.lower() in {"http", "https", "mailto", "tel"} or candidate.startswith("//")


def url_scheme(value: str) -> str:
    return urlparse(value.strip()).scheme.lower()


def always_unsafe_url(value: str) -> bool:
    return url_scheme(value) in {"javascript", "vbscript"}


def is_data_url(value: str) -> bool:
    return url_scheme(value) == "data"


def srcset_url_candidates(value: str) -> list[str]:
    candidates: list[str] = []
    candidate = []
    seen_descriptor = False
    for char in value.strip():
        if char.isspace():
            seen_descriptor = True
            candidate.append(char)
            continue
        if char == ",":
            current = "".join(candidate).strip()
            if seen_descriptor or not current.lower().startswith("data:"):
                if current:
                    candidates.append(current.split()[0])
                candidate = []
                seen_descriptor = False
                continue
        candidate.append(char)
    tail = "".join(candidate).strip()
    if tail:
        candidates.append(tail.split()[0])
    return candidates


def resource_url_candidates(attr: str, value: str) -> list[str]:
    if attr.lower() == "srcset":
        return srcset_url_candidates(value)
    return [value]


def data_url_media_type(value: str) -> str:
    payload = value.strip()[5:]
    return payload.split(",", 1)[0].split(";", 1)[0].strip().lower()


def data_url_allowed_in_context(
    profile: dict[str, Any],
    tag: str,
    attr: str,
    value: str,
    attrs_map: dict[str, str],
) -> bool:
    if not profile.get("allowImageDataUrls"):
        return False
    if not data_url_media_type(value).startswith("image/"):
        return False
    rel_tokens = set(attrs_map.get("rel", "").lower().split())
    return (
        (tag in {"img", "image"} and attr in {"src", "srcset", "href", "xlink:href"})
        or (tag == "source" and attr in {"src", "srcset"})
        or (tag == "video" and attr == "poster")
        or (tag == "link" and attr == "href" and bool(rel_tokens & {"icon", "apple-touch-icon", "mask-icon"}))
    )


def parse_csp(value: str) -> dict[str, list[str]]:
    directives: dict[str, list[str]] = {}
    for chunk in value.split(";"):
        parts = chunk.strip().split()
        if parts:
            directives[parts[0].lower()] = parts[1:]
    return directives


class StaticHtmlScanner(HTMLParser):
    def __init__(self, path: str) -> None:
        super().__init__(convert_charrefs=True)
        self.path = path
        self.has_doctype = False
        self.lang = ""
        self.charsets: list[str] = []
        self.has_viewport = False
        self.artifact_kind = ""
        self.csp = ""
        self.title = ""
        self.in_title = False
        self.ids: dict[str, int] = {}
        self.duplicate_ids: list[tuple[str, int]] = []
        self.external_loads: list[tuple[str, str, int]] = []
        self.external_links: list[tuple[str, str, int]] = []
        self.forbidden_elements: list[tuple[str, int]] = []
        self.event_handlers: list[tuple[str, str, int]] = []
        self.unsafe_navigation: list[tuple[str, str, int]] = []
        self.data_urls: list[tuple[str, str, str, int, dict[str, str]]] = []

    def handle_decl(self, decl: str) -> None:
        if decl.strip().lower() == "doctype html":
            self.has_doctype = True

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_name = tag.lower()
        attrs_map = {name.lower(): value or "" for name, value in attrs}
        line = self.getpos()[0]
        if tag_name == "html":
            self.lang = attrs_map.get("lang", "").strip()
        if tag_name == "title":
            self.in_title = True
        if tag_name in FORBIDDEN_ELEMENTS:
            self.forbidden_elements.append((tag_name, line))
        element_id = attrs_map.get("id")
        if element_id:
            if element_id in self.ids:
                self.duplicate_ids.append((element_id, line))
            self.ids[element_id] = line
        for name, value in attrs_map.items():
            if name.startswith("on"):
                self.event_handlers.append((tag_name, name, line))
            if always_unsafe_url(value):
                self.unsafe_navigation.append((tag_name, name, line))
            elif is_data_url(value) and name in {"action", "formaction"}:
                self.data_urls.append((tag_name, name, value, line, attrs_map))
        if tag_name == "meta":
            name = attrs_map.get("name", "").lower()
            http_equiv = attrs_map.get("http-equiv", "").lower()
            if "charset" in attrs_map:
                self.charsets.append(attrs_map["charset"].lower())
            if http_equiv == "content-type" and "charset=" in attrs_map.get("content", "").lower():
                self.charsets.append(attrs_map["content"].lower().split("charset=", 1)[1].split(";", 1)[0].strip())
            if name == "viewport" and attrs_map.get("content", "").strip():
                self.has_viewport = True
            if name == "artifact-kind":
                self.artifact_kind = attrs_map.get("content", "").strip()
            if http_equiv == "content-security-policy":
                self.csp = attrs_map.get("content", "").strip()
        for attr in RESOURCE_ATTRS.get(tag_name, ()):
            value = attrs_map.get(attr, "")
            for candidate in resource_url_candidates(attr, value):
                if is_external_url(candidate):
                    self.external_loads.append((tag_name, candidate, line))
                if always_unsafe_url(candidate):
                    self.unsafe_navigation.append((tag_name, attr, line))
                elif is_data_url(candidate):
                    self.data_urls.append((tag_name, attr, candidate, line, attrs_map))
        if tag_name == "a":
            href = attrs_map.get("href", "")
            if always_unsafe_url(href):
                self.unsafe_navigation.append((tag_name, "href", line))
            elif is_data_url(href):
                self.data_urls.append((tag_name, "href", href, line, attrs_map))
            if is_navigation_url(href) and is_external_url(href):
                rel_tokens = set(attrs_map.get("rel", "").lower().split())
                if not {"noopener", "noreferrer"}.issubset(rel_tokens):
                    self.external_links.append((tag_name, href, line))

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title += data


def validate_html_text(
    text: str,
    *,
    manifest: dict[str, Any] | None = None,
    profile_name: str = "strict-self-contained",
    path: str = "<html>",
    expected_artifact_kind: str | None = None,
) -> list[ContractIssue]:
    manifest = manifest or load_manifest()
    profile = merge_profile(manifest, profile_name)
    scanner = StaticHtmlScanner(path)
    scanner.feed(text)
    issues: list[ContractIssue] = []

    def require(flag: str, code: str, message: str) -> None:
        if profile.get(flag):
            issues.append(issue(code, "error", path, message))

    if not scanner.has_doctype:
        require("requireDoctype", "doctype-missing", "HTML must start with <!DOCTYPE html>.")
    if not scanner.lang:
        require("requireLang", "lang-missing", "The <html> element must declare lang.")
    if not any(value in {"utf-8", "utf8"} for value in scanner.charsets):
        require("requireCharset", "charset-missing", "A UTF-8 charset meta tag is required.")
    if not scanner.has_viewport:
        require("requireViewport", "viewport-missing", "A viewport meta tag is required.")
    if not scanner.title.strip():
        require("requireTitle", "title-missing", "A non-empty <title> is required.")
    if not scanner.artifact_kind:
        require("requireArtifactKind", "artifact-kind-missing", "meta name=\"artifact-kind\" is required.")
    elif expected_artifact_kind and scanner.artifact_kind != expected_artifact_kind:
        issues.append(issue("artifact-kind-mismatch", "error", path, f"artifact-kind must be {expected_artifact_kind}."))
    if not scanner.csp:
        require("requireCsp", "csp-missing", "A Content-Security-Policy meta tag is required.")
    else:
        directives = parse_csp(scanner.csp)
        for directive in profile.get("requiredCspDirectives", []):
            if str(directive).lower() not in directives:
                issues.append(issue("csp-directive-missing", "error", path, f"CSP directive is required: {directive}."))
    if profile.get("forbidExternalLoads"):
        for tag, value, line in scanner.external_loads:
            issues.append(issue("external-load", "error", path, f"External resource load from <{tag}> is forbidden: {value}", line))
    if profile.get("forbidDuplicateIds"):
        for element_id, line in scanner.duplicate_ids:
            issues.append(issue("duplicate-id", "error", path, f"Duplicate id is forbidden: {element_id}", line))
    if profile.get("forbidForbiddenElements"):
        for tag, line in scanner.forbidden_elements:
            issues.append(issue("forbidden-element", "error", path, f"<{tag}> is not allowed in static artifacts.", line))
    if profile.get("forbidEventHandlers"):
        for tag, name, line in scanner.event_handlers:
            issues.append(issue("event-handler", "error", path, f"Inline event handler is forbidden: <{tag} {name}>", line))
    for tag, attr, line in scanner.unsafe_navigation:
        issues.append(issue("unsafe-url", "error", path, f"Unsafe URL value is forbidden: <{tag} {attr}>", line))
    for tag, attr, value, line, attrs_map in scanner.data_urls:
        if not data_url_allowed_in_context(profile, tag, attr, value, attrs_map):
            issues.append(issue("unsafe-url", "error", path, f"data: URL is not allowed in this context: <{tag} {attr}>", line))
    if profile.get("externalLinksRequireRel"):
        for _tag, value, line in scanner.external_links:
            issues.append(issue("external-link-rel", "error", path, f"External navigation link must use rel=\"noopener noreferrer\": {value}", line))
    if profile.get("navigationWarnings"):
        for tag, value, line in scanner.external_links:
            issues.append(issue("navigation-url", "warning", path, f"Navigation URL is external and was checked separately from resource loads: <{tag}> {value}", line))
    if not profile.get("forbidExternalLoads"):
        for tag, value, line in scanner.external_loads:
            issues.append(issue("external-load-grandfathered", "warning", path, f"External resource load is grandfathered for this profile: <{tag}> {value}", line))
    return issues


def git_tracked_html(root: Path) -> list[str]:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "ls-files", "*.html"],
            capture_output=True,
            check=False,
            text=True,
        )
    except OSError:
        completed = subprocess.CompletedProcess([], 1, "", "")
    if completed.returncode == 0:
        return sorted(line.strip() for line in completed.stdout.splitlines() if line.strip())
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*.html") if ".git" not in path.parts)


def exception_matches(exceptions: list[dict[str, Any]], relative_path: str, literal: str) -> bool:
    return any(
        item.get("path") == relative_path and str(item.get("contains", "")) in literal
        for item in exceptions
        if isinstance(item, dict)
    )


def discover_html_literals(root: Path, directories: tuple[str, ...]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for directory in directories:
        base = root / directory
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_dir() or path.suffix not in {".py", ".js", ".mjs", ".ts", ".md"}:
                continue
            if directory == "skills" and path.name != "SKILL.md":
                continue
            relative = path.relative_to(root).as_posix()
            for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                if ".html" not in line:
                    continue
                for match in HTML_LITERAL_RE.finditer(line):
                    records.append({"path": relative, "line": line_number, "literal": match.group("literal")})
    return records


def check_manifest(manifest: dict[str, Any], root: Path = ROOT) -> list[ContractIssue]:
    issues: list[ContractIssue] = []
    if manifest.get("schemaVersion") != 1:
        issues.append(issue("manifest-schema", "error", "html-surfaces.json", "schemaVersion must be 1."))
    upstream = manifest.get("effectiveHtml", {})
    for key in ("upstreamRepository", "upstreamCommit", "license", "adaptationMode"):
        if not str(upstream.get(key, "")).strip():
            issues.append(issue("effective-html-metadata", "error", "html-surfaces.json", f"effectiveHtml.{key} is required."))
    if upstream.get("upstreamCommit") != "d95debbaef15af1d201fc6c10c77cf92b524a0d6":
        issues.append(issue("effective-html-commit", "error", "html-surfaces.json", "Effective HTML commit must remain pinned."))

    routes = manifest.get("routes", [])
    route_ids = {item.get("id") for item in routes if isinstance(item, dict)}
    missing_routes = REQUIRED_ROUTES - route_ids
    extra_routes = route_ids - REQUIRED_ROUTES
    for route in sorted(missing_routes):
        issues.append(issue("route-missing", "error", "html-surfaces.json", f"Route is missing: {route}."))
    for route in sorted(extra_routes):
        issues.append(issue("route-extra", "error", "html-surfaces.json", f"Unexpected route: {route}."))
    static_profiles = set((manifest.get("staticProfiles") or {}).keys())
    browser_profiles = set((manifest.get("browserProfiles") or {}).keys())
    for item in routes:
        if not isinstance(item, dict):
            continue
        for field in ("localOwner", "artifactKind", "staticProfile", "browserProfile", "validationCommands"):
            if not item.get(field):
                issues.append(issue("route-field-missing", "error", "html-surfaces.json", f"Route {item.get('id')} missing {field}."))
        if item.get("staticProfile") not in static_profiles:
            issues.append(issue("route-static-profile", "error", "html-surfaces.json", f"Route {item.get('id')} has unknown static profile."))
        if item.get("browserProfile") not in browser_profiles:
            issues.append(issue("route-browser-profile", "error", "html-surfaces.json", f"Route {item.get('id')} has unknown browser profile."))

    producers = [item for item in manifest.get("producers", []) if isinstance(item, dict)]
    producer_sources = {str(item.get("source")) for item in producers}
    for item in producers:
        source = str(item.get("source", ""))
        for field in ("id", "route", "owner", "source", "outputPatterns", "artifactKind", "staticProfile", "browserProfile"):
            if not item.get(field):
                issues.append(issue("producer-field-missing", "error", "html-surfaces.json", f"Producer {item.get('id')} missing {field}."))
        if item.get("route") not in route_ids:
            issues.append(issue("producer-route", "error", "html-surfaces.json", f"Producer {item.get('id')} references unknown route."))
        if item.get("staticProfile") not in static_profiles:
            issues.append(issue("producer-static-profile", "error", "html-surfaces.json", f"Producer {item.get('id')} has unknown static profile."))
        if source and not (root / source).is_file():
            issues.append(issue("producer-source-missing", "error", source, f"Producer source is missing: {source}."))

    surfaces = [item for item in manifest.get("surfaces", []) if isinstance(item, dict)]
    surface_by_path = {str(item.get("path")): item for item in surfaces}
    for path in git_tracked_html(root):
        if path not in surface_by_path:
            issues.append(issue("unregistered-surface", "error", path, "Tracked HTML surface is not registered in manifest."))
    for path, item in surface_by_path.items():
        lifecycle = item.get("lifecycle")
        if lifecycle not in {"canonical", "compatibility", "legacy", "grandfathered"}:
            issues.append(issue("surface-lifecycle", "error", path, "Surface lifecycle must be canonical, compatibility, legacy, or grandfathered."))
        profile_name = str(item.get("staticProfile", ""))
        if profile_name not in static_profiles:
            issues.append(issue("surface-static-profile", "error", path, "Surface has unknown static profile."))
            continue
        target = root / path
        if not target.is_file():
            profile = merge_profile(manifest, profile_name)
            if item.get("allowMissingInWorkingTree") or profile.get("allowMissingInWorkingTree"):
                issues.append(issue("surface-missing-grandfathered", "warning", path, "Registered surface is tracked but missing in the current dirty working tree."))
            else:
                issues.append(issue("surface-missing", "error", path, "Registered surface file is missing."))
            continue
        text = target.read_text(encoding="utf-8", errors="replace")
        issues.extend(validate_html_text(text, manifest=manifest, profile_name=profile_name, path=path, expected_artifact_kind=item.get("expectedArtifactKind")))

    legacy_refs = [
        path for path, item in surface_by_path.items()
        if item.get("lifecycle") in {"legacy", "grandfathered"}
    ]
    for path, item in surface_by_path.items():
        if item.get("lifecycle") != "canonical":
            continue
        target = root / path
        if not target.is_file():
            continue
        text = target.read_text(encoding="utf-8", errors="ignore")
        for legacy in legacy_refs:
            if legacy in text:
                issues.append(issue("canonical-live-legacy-ref", "error", path, f"Canonical surface must not live-reference legacy/grandfathered surface: {legacy}."))

    exceptions = [item for item in manifest.get("literalExceptions", []) if isinstance(item, dict)]
    for record in discover_html_literals(root, ("scripts", "workflows")):
        path = str(record["path"])
        literal = str(record["literal"])
        if path not in producer_sources and not exception_matches(exceptions, path, literal):
            issues.append(issue("unregistered-producer-literal", "error", path, f"HTML literal is not owned by a registered producer: {literal}", int(record["line"])))
    for record in discover_html_literals(root, ("skills",)):
        path = str(record["path"])
        literal = str(record["literal"])
        if path not in producer_sources and not exception_matches(exceptions, path, literal):
            issues.append(issue("unregistered-skill-html-reference", "error", path, f"Skill HTML artifact reference is not registered: {literal}", int(record["line"])))
    return issues


def assert_valid_html(
    text: str,
    *,
    manifest_path: Path = DEFAULT_MANIFEST,
    profile_name: str = "strict-self-contained",
    path: str = "<html>",
    expected_artifact_kind: str | None = None,
) -> None:
    manifest = load_manifest(manifest_path)
    issues = validate_html_text(
        text,
        manifest=manifest,
        profile_name=profile_name,
        path=path,
        expected_artifact_kind=expected_artifact_kind,
    )
    errors = [item for item in issues if item.severity == "error"]
    if errors:
        detail = "; ".join(f"{item.code}: {item.message}" for item in errors[:5])
        raise HtmlContractError(f"HTML artifact contract failed for {path}: {detail}")


def run_checks(manifest_path: Path = DEFAULT_MANIFEST, root: Path = ROOT) -> list[ContractIssue]:
    return check_manifest(load_manifest(manifest_path), root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    issues = run_checks(args.manifest, args.root)
    if args.json:
        print(json.dumps([item.to_dict() for item in issues], ensure_ascii=False, indent=2))
    else:
        for item in issues:
            location = f"{item.path}:{item.line}" if item.line else item.path
            print(f"{item.severity.upper()} {item.code} {location} - {item.message}")
        error_count = sum(item.severity == "error" for item in issues)
        warning_count = sum(item.severity == "warning" for item in issues)
        status = "PASS" if error_count == 0 else "FAIL"
        print(f"html surface contract: {status} ({error_count} errors, {warning_count} warnings)")
    return 1 if any(item.severity == "error" for item in issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())
