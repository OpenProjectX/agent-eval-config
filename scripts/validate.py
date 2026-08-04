#!/usr/bin/env python3
"""Validate AgentEval YAML files and cross-file tool references."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import yaml
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = {
    "Agent": "agent-spec.schema.json",
    "Tool": "tool-spec.schema.json",
    "Dataset": "dataset-spec.schema.json",
    "Policy": "policy-spec.schema.json",
}


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        document = yaml.safe_load(stream)
    if not isinstance(document, dict):
        raise ValueError("document must be a mapping")
    return document


def main() -> int:
    validators = {}
    for kind, filename in SCHEMAS.items():
        schema = json.loads((ROOT / "schemas" / filename).read_text(encoding="utf-8"))
        validators[kind] = Draft202012Validator(schema)

    errors: list[str] = []
    tools: set[tuple[str, int]] = set()
    agents: list[tuple[Path, dict]] = []
    validated = 0

    paths = sorted(
        list((ROOT / "agents").glob("*/revisions/*.yaml"))
        + list((ROOT / "tools").glob("*/versions/*.yaml"))
        + list((ROOT / "datasets").glob("*/versions/*.yaml"))
        + list((ROOT / "policies").glob("*.yaml"))
    )
    for path in paths:
        relative = path.relative_to(ROOT)
        try:
            document = load_yaml(path)
            kind = document.get("kind")
            validator = validators.get(kind)
            if validator is None:
                errors.append(f"{relative}: unsupported kind {kind!r}")
                continue
            for error in sorted(validator.iter_errors(document), key=lambda item: list(item.path)):
                location = ".".join(str(part) for part in error.path) or "<root>"
                errors.append(f"{relative}:{location}: {error.message}")
            if kind == "Tool":
                key = (document["metadata"]["id"], document["metadata"]["version"])
                if key in tools:
                    errors.append(f"{relative}: duplicate tool version {key[0]}@{key[1]}")
                tools.add(key)
            elif kind == "Agent":
                agents.append((relative, document))
            validated += 1
        except Exception as exc:  # provide all file failures in one Jenkins run
            errors.append(f"{relative}: {exc}")

    for path, agent in agents:
        for reference in agent["spec"]["tools"]:
            key = (reference["id"], reference["version"])
            if key not in tools:
                errors.append(f"{path}: unknown tool {key[0]}@{key[1]}")

    if errors:
        print("Configuration validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Validated {validated} immutable specifications and {len(tools)} tool versions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
