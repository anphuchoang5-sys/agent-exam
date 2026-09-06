from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from eval_platform.adapters.evaluation.process import execute_fork, fork_command
from eval_platform.adapters.evaluation.result_mapper import (
    map_evaluation,
    safe_identity,
)
from eval_platform.adapters.execution.harbor.artifacts import validate_patch_artifact
from eval_platform.adapters.tasks.swe_gym import SWEGymTaskSource
from eval_platform.application.ports.evaluator import EvaluationRequest
from eval_platform.application.ports.execution import RunLimits
from eval_platform.domain.result import DeterministicResult

FORK_REVISION = "242429c188fcfd06aad13fce9a54d450470bf0ac"


class SWEbenchEvaluator:
    """Freeze one request and run the original Fork grading with pinned Docker IO."""

    def __init__(
        self,
        *,
        repo_root: Path,
        task_source: SWEGymTaskSource,
        evidence_root: Path,
        limits: RunLimits,
        distro: str = "Ubuntu",
    ):
        self._repo = repo_root.resolve()
        self._tasks = task_source
        self._root = evidence_root.resolve()
        self._limits = limits
        self._distro = safe_identity(distro)
        self._root.relative_to(self._repo)

    def evaluate(self, request: EvaluationRequest) -> DeterministicResult:
        run_id = safe_identity(request.run_id)
        model = safe_identity(request.model_name_or_path)
        instance = safe_identity(request.task.instance_id)
        bundle = self._tasks.load(instance)
        if bundle.evaluator != request.task:
            raise ValueError(
                "Evaluation request does not match the frozen Task Catalog"
            )
        self._verify_fork()
        directory = self._root / run_id
        directory.mkdir(parents=True, exist_ok=False)
        (directory / "home").mkdir()
        patch_dir = directory / "input"
        patch_dir.mkdir()
        patch = request.model_patch
        (patch_dir / "model.patch").write_bytes(patch)
        (patch_dir / "patch.sha256").write_text(hashlib.sha256(patch).hexdigest())
        (patch_dir / "patch.bytes").write_text(str(len(patch)))
        (patch_dir / "patch.binary").write_text("0")
        validated = validate_patch_artifact(patch_dir)
        # This directory belongs only to the trusted evaluator, never the Agent.
        (directory / "dataset.jsonl").write_bytes(bundle.raw_record_json + b"\n")
        _write(
            directory / "predictions.jsonl",
            {
                "instance_id": instance,
                "model_patch": validated.content.decode("utf-8"),
                "model_name_or_path": model,
            },
        )
        lock = self._repo / "apps/backend/swebench-requirements.txt"
        profile = {
            "run_id": run_id,
            "evidence_identity": hashlib.sha256(
                directory.relative_to(self._repo).as_posix().encode()
            ).hexdigest(),
            "instance_id": instance,
            "repo": bundle.public.repo,
            "version": bundle.evaluator.version,
            "image": bundle.public.environment_image,
            "dataset_id": bundle.public.dataset_id,
            "revision": bundle.public.dataset_revision,
            "split": bundle.public.split,
            "task_sha256": bundle.public.raw_record_sha256,
            "base_commit": bundle.public.base_commit,
            "fork_revision": FORK_REVISION,
            "requirements_sha256": hashlib.sha256(lock.read_bytes()).hexdigest(),
            "patch_sha256": validated.sha256,
            "patch_warnings": validated.warnings,
            "cpus": self._limits.cpus,
            "memory_mb": self._limits.memory_mb,
            "pids_limit": 256,
            "test_timeout_sec": self._limits.wall_timeout_sec,
            "infrastructure_bridge": "pinned-image-v1",
        }
        _write(directory / "profile.json", profile)
        arguments = [
            "--dataset_name",
            "dataset.jsonl",
            "--split",
            bundle.public.split,
            "--instance_ids",
            instance,
            "--predictions_path",
            "predictions.jsonl",
            "--max_workers",
            "1",
            "--timeout",
            str(self._limits.wall_timeout_sec),
            "--run_id",
            run_id,
            "--force_rebuild",
            "false",
            "--cache_level",
            "instance",
            "--clean",
            "false",
            "--open_file_limit",
            "4096",
        ]
        deadline = self._limits.wall_timeout_sec + 180
        command = fork_command(self._repo, directory, arguments, deadline, self._distro)
        _write(directory / "command.json", {"argv": command, "timeout_sec": deadline})
        execute_fork(command, directory, deadline, run_id, artifact_root=self._repo)
        return map_evaluation(request, directory, artifact_root=self._repo)

    def _verify_fork(self) -> None:
        fork = self._repo / "framework/swe-bench-fork"
        result = subprocess.run(
            ["git", "-C", str(fork), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.stdout.strip() != FORK_REVISION:
            raise ValueError("SWE-Bench-Fork is not at the fixed revision")
        status = subprocess.run(
            ["git", "-C", str(fork), "status", "--porcelain", "--untracked-files=no"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if status.stdout.strip():
            raise ValueError("SWE-Bench-Fork has modified tracked source")


def _write(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(
            value, ensure_ascii=False, indent=None if path.suffix == ".jsonl" else 2
        )
        + "\n",
        encoding="utf-8",
    )
