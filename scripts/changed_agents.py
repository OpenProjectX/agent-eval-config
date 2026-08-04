#!/usr/bin/env python3
"""Print changed immutable AgentSpec IDs for Jenkins downstream evaluation."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess

import yaml


ROOT = Path(__file__).resolve().parents[1]
AGENT_PATH = re.compile(r"^agents/([^/]+)/revisions/([0-9]{6})\.yaml$")


def changed_paths(base: str | None, paths_file: Path | None = None) -> list[str]:
    if paths_file is not None:
        return [
            line.strip()
            for line in paths_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    if base and base != "0" * 40:
        command = ["git", "diff", "--name-only", base, "HEAD"]
    else:
        command = ["git", "show", "--pretty=format:", "--name-only", "HEAD"]
    output = subprocess.run(
        command, cwd=ROOT, check=True, capture_output=True, text=True).stdout
    return [line.strip() for line in output.splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base")
    parser.add_argument("--paths-file", type=Path)
    args = parser.parse_args()
    specs = set()
    for relative in changed_paths(args.base, args.paths_file):
        match = AGENT_PATH.match(relative)
        if not match:
            continue
        document = yaml.safe_load((ROOT / relative).read_text(encoding="utf-8"))
        metadata = document["metadata"]
        specs.add(f"{metadata['id']}@{int(metadata['revision'])}")
    for spec in sorted(specs):
        print(spec)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
