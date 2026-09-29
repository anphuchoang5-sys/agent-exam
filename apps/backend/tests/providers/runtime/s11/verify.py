"""CLI for the live two-Trial portion of task 05 S11."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from providers.runtime.s11.concurrent_trials import run_concurrent_trials


def _inventory(root: Path, suffix: str) -> None:
    commands = {
        "images": (
            "docker",
            "image",
            "ls",
            "--digests",
            "--no-trunc",
            "--format",
            "{{json .}}",
        ),
        "volumes": ("docker", "volume", "ls", "--format", "{{json .}}"),
    }
    for name, command in commands.items():
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        (root / f"{name}-{suffix}.jsonl").write_text(result.stdout, encoding="utf-8")


def _inventory_identities(path: Path, kind: str) -> set[str]:
    fields = {
        "images": ("ID", "Repository", "Tag", "Digest"),
        "volumes": ("Name", "Driver", "Labels", "Scope"),
    }[kind]
    values = (
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    )
    return {
        json.dumps({field: value.get(field) for field in fields}, sort_keys=True)
        for value in values
    }


def _manifest(root: Path) -> None:
    lines = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if path.name == "SHA256SUMS.txt":
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.relative_to(root).as_posix()}")
    (root / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--parquet", type=Path, required=True)
    parser.add_argument("--codex-archive", type=Path, required=True)
    parser.add_argument("--provider-image", required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    root = args.evidence.resolve()
    root.mkdir(parents=True, exist_ok=False)
    _inventory(root, "before")
    summary = run_concurrent_trials(
        project_root=args.project_root.resolve(),
        parquet=args.parquet.resolve(),
        codex_archive=args.codex_archive.resolve(),
        provider_image=args.provider_image,
        evidence=root / "trials",
    )
    _inventory(root, "after")
    difference = {
        kind: {
            "added": sorted(
                _inventory_identities(root / f"{kind}-after.jsonl", kind)
                - _inventory_identities(root / f"{kind}-before.jsonl", kind)
            ),
            "removed": sorted(
                _inventory_identities(root / f"{kind}-before.jsonl", kind)
                - _inventory_identities(root / f"{kind}-after.jsonl", kind)
            ),
        }
        for kind in ("images", "volumes")
    }
    (root / "inventory-diff.json").write_text(
        json.dumps(difference, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _manifest(root)
    print(json.dumps({**summary, "inventory_diff": difference}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
