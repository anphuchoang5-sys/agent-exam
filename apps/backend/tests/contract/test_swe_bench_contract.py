from __future__ import annotations

import json
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from eval_platform.adapters.evaluation import process, swe_bench
from eval_platform.adapters.tasks.swe_gym import (
    CANDIDATE_INSTANCE_ID,
    DATASET_REVISION,
    SWEGymTaskSource,
)
from eval_platform.application.ports.evaluator import EvaluationRequest
from eval_platform.application.ports.execution import RunLimits
from eval_platform.domain.result import ArtifactRef, DeterministicResult

pytestmark = pytest.mark.contract


def test_freezes_exact_prediction_and_refuses_overwrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = Path(__file__).resolve().parents[4]
    parquet = (
        repo / "runtime/cache/swe-gym-lite" / DATASET_REVISION / "train-0000.parquet"
    )
    if not parquet.is_file():
        pytest.skip("Restore the fixed local SWE-Gym snapshot")
    source = SWEGymTaskSource(parquet)
    bundle = source.load(CANDIDATE_INSTANCE_ID)
    lock = tmp_path / "apps/backend/swebench-requirements.txt"
    lock.parent.mkdir(parents=True)
    lock.write_text("docker==7.2.0\n", encoding="utf-8")
    evaluator = swe_bench.SWEbenchEvaluator(
        repo_root=tmp_path,
        task_source=source,
        evidence_root=tmp_path / "evidence",
        limits=RunLimits(300, 1, 4096, 8192),
    )
    monkeypatch.setattr(evaluator, "_verify_fork", lambda: None)
    calls = []

    def fake_process(command, directory, deadline, run_id, *, artifact_root):
        calls.append((command, directory, deadline, run_id))
        assert artifact_root == tmp_path

    expected = DeterministicResult(
        "contract-run",
        True,
        True,
        ArtifactRef("report.json", "harness_report", 0, "a" * 64, "application/json"),
    )
    monkeypatch.setattr(swe_bench, "execute_fork", fake_process)
    monkeypatch.setattr(swe_bench, "map_evaluation", lambda *a, **kw: expected)
    request = EvaluationRequest(
        "contract-run",
        bundle.evaluator,
        bundle.evaluator.gold_patch.encode(),
        "config-1",
    )
    assert evaluator.evaluate(request) == expected
    directory = tmp_path / "evidence/contract-run"
    lines = (directory / "predictions.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == {
        "instance_id": CANDIDATE_INSTANCE_ID,
        "model_patch": bundle.evaluator.gold_patch,
        "model_name_or_path": "config-1",
    }
    assert (directory / "dataset.jsonl").read_bytes() == bundle.raw_record_json + b"\n"
    command = calls[0][0]
    assert command[command.index("--max_workers") + 1] == "1"
    assert command[command.index("--cache_level") + 1] == "instance"
    assert command[command.index("--clean") + 1] == "false"
    assert "PYTHON_DOTENV_DISABLED=1" in command and "-i" in command
    before = (directory / "profile.json").read_bytes()
    with pytest.raises(FileExistsError):
        evaluator.evaluate(request)
    assert (directory / "profile.json").read_bytes() == before
    assert len(calls) == 1
    changed = replace(
        request, run_id="mismatch", task=replace(request.task, version="other")
    )
    with pytest.raises(ValueError, match="frozen Task Catalog"):
        evaluator.evaluate(changed)
    assert not (tmp_path / "evidence/mismatch").exists()


def test_cleanup_filters_both_run_and_evidence_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "profile.json").write_text('{"evidence_identity":"owned"}')
    queries = []

    def fake_run(command, **kwargs):
        queries.append(command)
        if command[:3] == ["docker", "ps", "-aq"]:
            assert "label=agentexam.evaluator.run=run-1" in command
            assert "label=agentexam.evaluator.evidence=owned" in command
            return subprocess.CompletedProcess(
                command, 0, "abc123\n" if len(queries) == 1 else ""
            )
        assert command == ["docker", "rm", "-f", "abc123"]
        return subprocess.CompletedProcess(command, 0, "")

    monkeypatch.setattr(process.subprocess, "run", fake_run)
    assert process.cleanup_run("run-1", tmp_path)
    assert len(queries) == 3
    record = json.loads((tmp_path / "cleanup.json").read_text())
    assert record["removed_ids"] == ["abc123"]
    assert record["remaining_ids"] == []
