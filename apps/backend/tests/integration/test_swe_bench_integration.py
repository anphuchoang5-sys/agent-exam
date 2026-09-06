from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

import pytest

from eval_platform.adapters.evaluation.swe_bench import SWEbenchEvaluator
from eval_platform.adapters.tasks.swe_gym import (
    CANDIDATE_INSTANCE_ID,
    DATASET_REVISION,
    SWEGymTaskSource,
)
from eval_platform.application.ports.evaluator import EvaluationError, EvaluationRequest
from eval_platform.application.ports.execution import RunLimits

pytestmark = pytest.mark.integration

WRONG = (
    "diff --git a/agentexam_wrong_probe.txt b/agentexam_wrong_probe.txt\n"
    "new file mode 100644\n--- /dev/null\n+++ b/agentexam_wrong_probe.txt\n"
    "@@ -0,0 +1 @@\n+This deliberately does not fix the issue.\n"
)
UNAPPLICABLE = (
    "diff --git a/agentexam_missing.txt b/agentexam_missing.txt\n"
    "--- a/agentexam_missing.txt\n+++ b/agentexam_missing.txt\n"
    "@@ -1 +1 @@\n-not-present\n+cannot-apply\n"
)


@pytest.mark.parametrize(
    "scenario", ["empty", "gold", "wrong", "unapplicable", "timeout"]
)
def test_fixed_fork_grades_patch_and_cleans_container(
    tmp_path: Path, scenario: str
) -> None:
    if os.environ.get("AGENTEXAM_RUN_FORK_INTEGRATION") != "1":
        pytest.skip("Set AGENTEXAM_RUN_FORK_INTEGRATION=1 for the real Fork probe")
    repo = Path(__file__).resolve().parents[4]
    tmp_path.resolve().relative_to(repo)
    parquet = (
        repo / "runtime/cache/swe-gym-lite" / DATASET_REVISION / "train-0000.parquet"
    )
    source = SWEGymTaskSource(parquet)
    bundle = source.load(CANDIDATE_INSTANCE_ID)
    run_id = f"m0-fork-{scenario}-{uuid.uuid4().hex[:12]}"
    patches = {
        "empty": "",
        "gold": bundle.evaluator.gold_patch,
        "wrong": WRONG,
        "unapplicable": UNAPPLICABLE,
        "timeout": bundle.evaluator.gold_patch,
    }
    request = EvaluationRequest(
        run_id, bundle.evaluator, patches[scenario].encode("utf-8"), f"probe-{scenario}"
    )
    evaluator = SWEbenchEvaluator(
        repo_root=repo,
        task_source=source,
        evidence_root=tmp_path,
        limits=RunLimits(1 if scenario == "timeout" else 300, 1, 4096, 8192),
    )
    directory = tmp_path / run_id
    if scenario in {"timeout", "unapplicable"}:
        with pytest.raises(EvaluationError) as error:
            evaluator.evaluate(request)
        assert error.value.code == "HARNESS_EVALUATION_FAILED"
        logs = directory / "logs/run_evaluation" / run_id / request.model_name_or_path
        message = (logs / CANDIDATE_INSTANCE_ID / "run_instance.log").read_text(
            encoding="utf-8"
        )
        expected = (
            "Test timed out after"
            if scenario == "timeout"
            else ">>>>> Patch Apply Failed"
        )
        assert expected in message
    else:
        result = evaluator.evaluate(request)
        assert result.resolved is (scenario == "gold")
        assert result.patch_applied is (scenario != "empty")
        assert (repo / result.report_ref.object_key).is_file()
    cleanup = json.loads((directory / "cleanup.json").read_text(encoding="utf-8"))
    assert cleanup["verified"] is True
    assert cleanup["remaining_ids"] == []
    process = json.loads((directory / "fork-process.json").read_text(encoding="utf-8"))
    assert process["returncode"] == 0
    assert process["warnings"] == []
    if scenario != "empty":
        container = json.loads(
            (directory / "container.json").read_text(encoding="utf-8")
        )
        assert container["image_digest"] == bundle.public.environment_image
        assert container["host_config"]["NetworkMode"] == "none"
        assert container["host_config"]["Memory"] == 4096 * 1024 * 1024
        assert container["host_config"]["NanoCpus"] == 1_000_000_000
        assert container["host_config"]["PidsLimit"] == 256
        assert container["mounts"] == []
