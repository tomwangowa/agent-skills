#!/usr/bin/env python3
"""Validate skills catalog metadata and render its deterministic index."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


VALID_CATEGORIES = frozenset(
    {
        "quality-gates",
        "research-critical-thinking",
        "multi-agent-roles",
        "design-planning",
        "content-generation",
        "productivity-tracking",
        "tools-meta",
    }
)
VALID_LIFECYCLES = frozenset({"promoted", "experimental", "personal", "deprecated"})
VALID_INVOCATION_INTENTS = frozenset({"model", "user"})

CATALOG_PATH = Path("skills-catalog.json")
ROUTER_PATH = Path("skill-router/skill-registry.yaml")
README_PATHS = (Path("README.md"), Path("README.zh.md"))
SYNC_IGNORE_PATH = Path(".skill-sync-ignore")
GENERATED_PATH = Path("SKILLS_CATALOG.md")
ROUTER_ID = re.compile(r"^\s*-\s+id:\s+([^\s#]+)")
WORKFLOWS_HEADER = re.compile(r"^workflows:\s*(?P<value>.*)$")
WORKFLOW_ITEM = re.compile(r"^(?P<indent>\s*)-\s+(?P<key>[^\s#:]+):")
WORKFLOW_STEP_ID = re.compile(r"^\s*-\s+([^\s#:]+(?::[^\s#:]+)?)\s*(?:#.*)?$")
WORKFLOW_STEPS = re.compile(r"^(?P<indent>\s*)steps:\s*(?P<value>.*)$")
CORE_START = "<!-- core-skills:start -->"
CORE_END = "<!-- core-skills:end -->"


class ValidationError(Exception):
    """A repository state that does not satisfy the catalog contract."""


def fail(message: str) -> None:
    raise ValidationError(message)


def discover_tracked_skill_ids(root: Path) -> set[str]:
    """Return only first-level SKILL.md directories present in Git's index."""
    result = subprocess.run(
        ["git", "ls-files", "--", "*/SKILL.md"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        detail = result.stderr.strip() or "git ls-files failed"
        fail(f"Git inventory: {detail}")

    ids: set[str] = set()
    for raw_path in result.stdout.splitlines():
        path = Path(raw_path)
        if len(path.parts) == 2 and path.name == "SKILL.md":
            ids.add(path.parts[0])
    return ids


def read_json_catalog(root: Path) -> list[dict[str, Any]]:
    path = root / CATALOG_PATH
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"{CATALOG_PATH}: missing file")
    except json.JSONDecodeError as error:
        fail(f"{CATALOG_PATH}: invalid JSON ({error.msg})")

    if not isinstance(payload, dict):
        fail(f"{CATALOG_PATH}: root must be an object")
    if type(payload.get("schema_version")) is not int or payload.get("schema_version") != 1:
        fail(f"{CATALOG_PATH}: schema_version must be 1")
    skills = payload.get("skills")
    if not isinstance(skills, list):
        fail(f"{CATALOG_PATH}: skills must be an array")

    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for position, raw_entry in enumerate(skills):
        location = f"{CATALOG_PATH}: skills[{position}]"
        if not isinstance(raw_entry, dict):
            fail(f"{location}: entry must be an object")

        required_fields = ("id", "category", "lifecycle", "invocation_intent", "surfaces")
        for field in required_fields:
            if field not in raw_entry:
                fail(f"{location}: missing required field {field}")

        skill_id = raw_entry["id"]
        if not isinstance(skill_id, str) or not skill_id:
            fail(f"{location}: id must be a non-empty string")
        if skill_id in seen_ids:
            fail(f"{CATALOG_PATH}: duplicate id {skill_id}")
        seen_ids.add(skill_id)

        for field, allowed in (
            ("category", VALID_CATEGORIES),
            ("lifecycle", VALID_LIFECYCLES),
            ("invocation_intent", VALID_INVOCATION_INTENTS),
        ):
            value = raw_entry[field]
            if not isinstance(value, str) or value not in allowed:
                fail(f"{CATALOG_PATH}: {skill_id}.{field} must be one of {sorted(allowed)}; got {value!r}")

        surfaces = raw_entry["surfaces"]
        if not isinstance(surfaces, dict):
            fail(f"{CATALOG_PATH}: {skill_id}.surfaces must be an object")
        for field in ("routable", "listed_in_readme", "sync"):
            if field not in surfaces:
                fail(f"{CATALOG_PATH}: {skill_id}.surfaces missing required field {field}")
            if type(surfaces[field]) is not bool:
                fail(f"{CATALOG_PATH}: {skill_id}.{field} must be a boolean")

        normalized.append(raw_entry)
    return normalized


def validate_inventory(entries: Iterable[Mapping[str, Any]], tracked_ids: set[str]) -> None:
    catalog_ids = {entry["id"] for entry in entries}
    missing = sorted(tracked_ids - catalog_ids)
    unexpected = sorted(catalog_ids - tracked_ids)
    errors: list[str] = []
    if missing:
        errors.append(f"tracked skills missing from {CATALOG_PATH}: {', '.join(missing)}")
    if unexpected:
        errors.append(f"catalog ids absent from Git inventory: {', '.join(unexpected)}")
    if errors:
        fail("; ".join(errors))


def validate_lifecycle_surfaces(entries: Iterable[Mapping[str, Any]]) -> None:
    """Keep deprecated skills available for migration but off promoted surfaces."""
    for entry in entries:
        if entry["lifecycle"] != "deprecated":
            continue
        surfaces = entry["surfaces"]
        if surfaces["routable"] or surfaces["listed_in_readme"]:
            fail(
                f"{CATALOG_PATH}: deprecated skill {entry['id']} must not be "
                "routable or listed in a README core set"
            )


def read_router_references(root: Path) -> tuple[list[str], list[str]]:
    """Return local category IDs and workflow step IDs from the router registry."""
    path = root / ROUTER_PATH
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"{ROUTER_PATH}: missing file")

    router_ids: list[str] = []
    workflow_step_ids: list[str] = []
    in_workflows = False
    workflow_item_indent: int | None = None
    workflow_field_indent: int | None = None
    workflow_steps_indent: int | None = None
    workflow_step_item_indent: int | None = None
    for line in content.splitlines():
        workflows_match = WORKFLOWS_HEADER.match(line)
        if workflows_match:
            value = workflows_match.group("value").strip()
            if value and not value.startswith("#"):
                fail(f"{ROUTER_PATH}: workflows must use a block sequence")
            in_workflows = True
            workflow_item_indent = None
            workflow_field_indent = None
            workflow_steps_indent = None
            workflow_step_item_indent = None
            continue
        if not in_workflows:
            match = ROUTER_ID.match(line)
            if match and ":" not in match.group(1):
                router_ids.append(match.group(1))
            continue
        indentation = len(line) - len(line.lstrip())
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and indentation == 0:
            in_workflows = False
            workflow_item_indent = None
            workflow_field_indent = None
            workflow_steps_indent = None
            workflow_step_item_indent = None
            continue
        if workflow_steps_indent is not None:
            if stripped and indentation <= workflow_steps_indent:
                workflow_steps_indent = None
                workflow_step_item_indent = None
            elif not stripped or stripped.startswith("#"):
                continue
            else:
                if not stripped.startswith("- "):
                    fail(f"{ROUTER_PATH}: workflow steps must contain only scalar skill IDs")
                if workflow_step_item_indent is None:
                    workflow_step_item_indent = indentation
                elif indentation != workflow_step_item_indent:
                    fail(f"{ROUTER_PATH}: workflow steps must contain only scalar skill IDs")
                match = WORKFLOW_STEP_ID.match(line)
                if not match:
                    fail(f"{ROUTER_PATH}: workflow steps must contain only scalar skill IDs")
                workflow_step_ids.append(match.group(1))
                continue
        workflow_item_match = WORKFLOW_ITEM.match(line)
        if workflow_item_match and (
            workflow_item_indent is None or indentation == workflow_item_indent
        ):
            if workflow_item_match.group("key") != "id":
                fail(f"{ROUTER_PATH}: workflow item must begin with - id")
            workflow_item_indent = indentation
            workflow_field_indent = None
            continue
        if (
            stripped.startswith("- ")
            and (workflow_item_indent is None or indentation == workflow_item_indent)
        ):
            fail(f"{ROUTER_PATH}: workflow item must begin with - id")
        if workflow_item_indent is None or indentation <= workflow_item_indent:
            continue
        if workflow_field_indent is None:
            workflow_field_indent = indentation
        if indentation > workflow_field_indent and WORKFLOW_STEPS.match(line):
            fail(f"{ROUTER_PATH}: workflow steps must be a direct workflow item field")
        if indentation != workflow_field_indent:
            continue
        steps_match = WORKFLOW_STEPS.match(line)
        if steps_match:
            value = steps_match.group("value").strip()
            if value and not value.startswith("#") and value != "[]":
                fail(
                    f"{ROUTER_PATH}: workflow steps must use one skill ID per indented line"
                )
            workflow_steps_indent = len(steps_match.group("indent"))
    return router_ids, workflow_step_ids


def validate_router(entries: Iterable[Mapping[str, Any]], root: Path) -> None:
    router_ids, workflow_step_ids = read_router_references(root)
    catalog_ids = {entry["id"] for entry in entries}
    # Namespaced IDs belong to external providers (for example, superpowers).
    # The catalog governs only this repository's top-level local skills.
    unknown_ids = sorted({skill_id for skill_id in router_ids if ":" not in skill_id} - catalog_ids)
    if unknown_ids:
        fail(
            f"{ROUTER_PATH}: local ids absent from {CATALOG_PATH}: "
            f"{', '.join(unknown_ids)}"
        )
    unknown_workflow_ids = sorted(
        {skill_id for skill_id in workflow_step_ids if ":" not in skill_id} - catalog_ids
    )
    if unknown_workflow_ids:
        fail(
            f"{ROUTER_PATH}: local workflow step ids absent from {CATALOG_PATH}: "
            f"{', '.join(unknown_workflow_ids)}"
        )
    deprecated_workflow_ids = sorted(
        entry["id"]
        for entry in entries
        if entry["lifecycle"] == "deprecated" and entry["id"] in workflow_step_ids
    )
    if deprecated_workflow_ids:
        fail(
            f"{ROUTER_PATH}: deprecated skill must not appear in workflow steps: "
            f"{', '.join(deprecated_workflow_ids)}"
        )
    for entry in entries:
        skill_id = entry["id"]
        expected_count = 1 if entry["surfaces"]["routable"] else 0
        actual_count = router_ids.count(skill_id)
        if actual_count != expected_count:
            expectation = "exactly once" if expected_count else "zero times"
            fail(
                f"{ROUTER_PATH}: {skill_id} must appear {expectation} before workflows "
                f"(found {actual_count})"
            )


def core_region(path: Path) -> str:
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"{path.name}: missing file")

    start = content.find(CORE_START)
    end = content.find(CORE_END)
    if start == -1 or end == -1 or end < start:
        fail(f"{path.name}: missing or malformed Core Skills markers")
    if content.find(CORE_START, start + len(CORE_START)) != -1:
        fail(f"{path.name}: duplicate Core Skills start marker")
    if content.find(CORE_END, end + len(CORE_END)) != -1:
        fail(f"{path.name}: duplicate Core Skills end marker")
    return content[start + len(CORE_START) : end]


def link_count(region: str, skill_id: str) -> int:
    return len(
        re.findall(
            rf"\[{re.escape(skill_id)}\]\(\./{re.escape(skill_id)}/SKILL\.md\)",
            region,
        )
    )


def validate_readmes(entries: Iterable[Mapping[str, Any]], root: Path) -> None:
    regions = {path.name: core_region(root / path) for path in README_PATHS}
    for entry in entries:
        skill_id = entry["id"]
        expected_count = 1 if entry["surfaces"]["listed_in_readme"] else 0
        for name, region in regions.items():
            actual_count = link_count(region, skill_id)
            if actual_count != expected_count:
                expectation = "exactly once" if expected_count else "zero times"
                fail(
                    f"{name}: Core Skills link for {skill_id} must appear {expectation} "
                    f"(found {actual_count})"
                )


def exact_sync_ignores(root: Path) -> set[str]:
    path = root / SYNC_IGNORE_PATH
    try:
        lines = path.read_text(encoding="utf-8").split("\n")
    except FileNotFoundError:
        fail(f"{SYNC_IGNORE_PATH}: missing file")
    return {clean_sync_line(line) for line in lines if clean_sync_line(line)}


def clean_sync_line(line: str) -> str:
    """Mirror skill-sync's clean_line before applying catalog policy."""
    if line.endswith("\r"):
        line = line[:-1]
    return line.split("#", 1)[0].strip()


def validate_sync(entries: Iterable[Mapping[str, Any]], root: Path) -> None:
    ignored = exact_sync_ignores(root)
    for entry in entries:
        skill_id = entry["id"]
        is_ignored = skill_id in ignored or f"{skill_id}/" in ignored
        should_sync = entry["surfaces"]["sync"]
        if should_sync and is_ignored:
            fail(f"{SYNC_IGNORE_PATH}: sync=true skill {skill_id} has an exact top-level ignore")
        if not should_sync and not is_ignored:
            fail(f"{SYNC_IGNORE_PATH}: sync=false skill {skill_id} needs an exact {skill_id} or {skill_id}/ ignore")


def render_index(entries: Iterable[Mapping[str, Any]]) -> str:
    lines = [
        "# Skills Catalog",
        "",
        "> Generated from skills-catalog.json. Do not edit by hand; run python3 scripts/validate_skills_catalog.py --write.",
        "",
        "| Skill | Category | Lifecycle | Invocation intent | Router | README | Sync |",
        "|---|---|---|---|---|---|---|",
    ]
    for entry in sorted(entries, key=lambda item: (item["category"], item["id"])):
        surfaces = entry["surfaces"]
        flags = ("yes" if surfaces[field] else "no" for field in ("routable", "listed_in_readme", "sync"))
        router, readme, sync = flags
        skill_id = entry["id"]
        lines.append(
            f"| [{skill_id}](./{skill_id}/SKILL.md) | {entry['category']} | "
            f"{entry['lifecycle']} | {entry['invocation_intent']} | {router} | {readme} | {sync} |"
        )
    return "\n".join(lines) + "\n"


def validate(root: Path) -> tuple[list[dict[str, Any]], str]:
    entries = read_json_catalog(root)
    validate_inventory(entries, discover_tracked_skill_ids(root))
    validate_lifecycle_surfaces(entries)
    validate_router(entries, root)
    validate_readmes(entries, root)
    validate_sync(entries, root)
    return entries, render_index(entries)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="validate without writing files")
    mode.add_argument("--write", action="store_true", help="validate then write SKILLS_CATALOG.md")
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    root = Path.cwd()
    try:
        _, expected_index = validate(root)
        output_path = root / GENERATED_PATH
        if arguments.check:
            try:
                actual_index = output_path.read_text(encoding="utf-8")
            except FileNotFoundError:
                fail(f"{GENERATED_PATH}: missing generated index; run --write")
            if actual_index != expected_index:
                fail(f"{GENERATED_PATH}: stale generated index; run --write")
        else:
            output_path.write_text(expected_index, encoding="utf-8")
    except ValidationError as error:
        print(f"validate_skills_catalog.py: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
