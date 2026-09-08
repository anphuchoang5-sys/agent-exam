from __future__ import annotations

import hashlib
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from eval_platform.adapters.tasks.swe_gym import (
    CANDIDATE_IMAGE,
    CANDIDATE_INSTANCE_ID,
    DatasetIdentity,
    SWEGymTaskSource,
    render_harbor_task,
)
from eval_platform.application.ports.execution import RunLimits

GOLD_SENTINEL = "SECRET_GOLD_PATCH_SENTINEL"
TEST_SENTINEL = "SECRET_TEST_PATCH_SENTINEL"
TEST_ID_SENTINEL = "secret_test_identifier"


def _record() -> dict[str, object]:
    return {
        "instance_id": CANDIDATE_INSTANCE_ID,
        "hints_text": "hidden hint",
        "patch": GOLD_SENTINEL,
        "test_patch": TEST_SENTINEL,
        "created_at": "2026-01-01T00:00:00Z",
        "problem_statement": "Repair the public behavior without seeing tests.",
        "repo": "python/mypy",
        "base_commit": "e7b917ec7532206b996542570f4b68a33c3ff771",
        "version": "1.4",
        "PASS_TO_PASS": [],
        "FAIL_TO_PASS": [TEST_ID_SENTINEL],
    }


def _source(tmp_path: Path) -> SWEGymTaskSource:
    path = tmp_path / "tasks.parquet"
    pq.write_table(pa.Table.from_pylist([_record()]), path)
    content = path.read_bytes()
    identity = DatasetIdentity(
        revision="a" * 40,
        size_bytes=len(content),
        sha256=hashlib.sha256(content).hexdigest(),
    )
    return SWEGymTaskSource(path, identity)


def test_load_separates_agent_and_evaluator_views(tmp_path: Path) -> None:
    bundle = _source(tmp_path).load(CANDIDATE_INSTANCE_ID)

    assert bundle.public.instance_id == CANDIDATE_INSTANCE_ID
    assert bundle.public.environment_image == CANDIDATE_IMAGE
    assert bundle.evaluator.gold_patch == GOLD_SENTINEL
    assert bundle.evaluator.test_patch == TEST_SENTINEL
    assert TEST_ID_SENTINEL in bundle.evaluator.fail_to_pass
    assert GOLD_SENTINEL.encode() in bundle.raw_record_json
    assert not hasattr(bundle.public, "gold_patch")
    assert not hasattr(bundle.public, "test_patch")


def test_rendered_harbor_task_contains_only_public_view(tmp_path: Path) -> None:
    bundle = _source(tmp_path).load(CANDIDATE_INSTANCE_ID)
    task_dir = render_harbor_task(
        bundle.public,
        tmp_path / "harbor-tasks",
        RunLimits(wall_timeout_sec=900, cpus=1, memory_mb=4096, storage_mb=8192),
    )

    files = sorted(
        path.relative_to(task_dir).as_posix() for path in task_dir.rglob("*")
    )
    assert files == [
        "environment",
        "environment/Dockerfile",
        "environment/collect-patch.sh",
        "environment/docker-compose.yaml",
        "instruction.md",
        "task.toml",
    ]
    rendered = "\n".join(
        path.read_text(encoding="utf-8")
        for path in task_dir.rglob("*")
        if path.is_file()
    )
    for forbidden in (
        GOLD_SENTINEL,
        TEST_SENTINEL,
        TEST_ID_SENTINEL,
        "FAIL_TO_PASS",
        "PASS_TO_PASS",
        "test_patch",
    ):
        assert forbidden not in rendered
    assert bundle.public.problem_statement in rendered
    assert bundle.public.base_commit in rendered
    assert rendered.count('user = "65534:65534"') == 2
    assert "RUN chown -R 65534:65534 /testbed" in rendered


def test_dataset_hash_mismatch_is_rejected(tmp_path: Path) -> None:
    source = _source(tmp_path)
    source._path.write_bytes(source._path.read_bytes() + b"tampered")

    with pytest.raises(ValueError, match="size does not match"):
        source.load(CANDIDATE_INSTANCE_ID)


def test_render_never_overwrites_existing_task(tmp_path: Path) -> None:
    bundle = _source(tmp_path).load(CANDIDATE_INSTANCE_ID)
    limits = RunLimits(900, 1, 4096, 8192)
    root = tmp_path / "harbor-tasks"
    render_harbor_task(bundle.public, root, limits)

    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        render_harbor_task(bundle.public, root, limits)
