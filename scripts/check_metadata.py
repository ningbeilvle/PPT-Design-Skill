#!/usr/bin/env python3
"""Validate skill metadata and version references.

``skill.json`` is the single source of truth for the skill name and version.
This check fails when the manifest is malformed or when a version string in the
README badge or the Chinese usage guide drifts away from it, so a release does
not have to keep a hard-coded version in the CI workflow.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION_RE = re.compile(r"^\d+\.\d+$")
EXPECTED_NAME = "ppt-design-skill"

# (relative path, required snippet with a {version} placeholder)
VERSION_REFERENCES = [
    ("README.md", "version-{version}-"),
    ("README.md", 'Version {version}"'),
    ("docs/usage-guide.md", "当前 Skill 版本为 {version}"),
    ("skill/scripts/init_presentation_task.py", 'SKILL_VERSION = "{version}"'),
]


def main() -> int:
    failures: list[str] = []

    manifest_path = ROOT / "skill.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except OSError as exc:
        print(f"[FAIL] skill.json: {exc}")
        return 1
    except json.JSONDecodeError as exc:
        print(f"[FAIL] skill.json: invalid JSON: {exc}")
        return 1

    name = manifest.get("name", "")
    if name != EXPECTED_NAME:
        failures.append(f"skill.json: name is {name!r}, expected {EXPECTED_NAME!r}")
    else:
        print(f"[OK] skill.json: name={name}")

    version = manifest.get("version", "")
    if not isinstance(version, str) or not VERSION_RE.fullmatch(version):
        failures.append(f"skill.json: version {version!r} is not a MAJOR.MINOR string")
    else:
        print(f"[OK] skill.json: version={version}")

    entrypoint = manifest.get("entrypoint", "")
    if not entrypoint or not (ROOT / entrypoint).is_file():
        failures.append(f"skill.json: entrypoint {entrypoint!r} does not exist")
    else:
        print(f"[OK] skill.json: entrypoint={entrypoint}")

    if version and VERSION_RE.fullmatch(version):
        for rel_path, snippet in VERSION_REFERENCES:
            path = ROOT / rel_path
            if not path.is_file():
                failures.append(f"{rel_path}: file is missing")
                continue
            expected = snippet.format(version=version)
            if expected not in path.read_text(encoding="utf-8"):
                failures.append(
                    f"{rel_path}: missing version reference {expected!r} "
                    f"(skill.json version is {version})"
                )
            else:
                print(f"[OK] {rel_path}: found {expected!r}")

    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        return 1

    print(f"[OK] metadata is consistent for version {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
