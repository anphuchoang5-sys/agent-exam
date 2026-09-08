"""M0 wiring only: no Web, database, approval, ranking, or automatic retry."""

from __future__ import annotations

import argparse
import json
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Literal

from eval_platform.adapters.execution.harbor.artifacts import (
    PatchArtifactError,
    validate_patch_artifact,
)
from eval_platform.adapters.execution.harbor.config_mapper import (
    build_job_plan,
    validate_job_id,
)
from eval_platform.adapters.execution.preflight import (
    network_preflight,
    task_preflight,
)
from eval_platform.application.ports.evaluator import (
    EvaluationError,
    EvaluationRequest,
    PatchEvaluator,
)
from eval_platform.application.ports.execution import (
    ExecutionBackend,
    ExecutionJobRequest,
)
from eval_platform.domain.result import (
    ArtifactRef,
    DeterministicResult,
    TerminationReason,
)
from eval_platform.domain.task import TaskBundle


def run_prototype(
    request: ExecutionJobRequest,
    bundle: TaskBundle,
    *,
    execution: ExecutionBackend,
    evaluator: PatchEvaluator,
    evidence_dir: Path,
    execution_kind: Literal["internal_test", "harbor_nop", "codex"],
) -> DeterministicResult:
    """Join the fixed execution, patch-validation, and evaluator ports."""
    if execution_kind not in {"internal_test", "harbor_nop", "codex"}:
        raise ValueError("Unknown M0 execution kind")
    if len(request.runs) != 1:
        raise ValueError("M0 requires exactly one run")
    (run,) = request.runs
    validate_job_id(request.job_id)
    validate_job_id(run.run_id)
    if run.task != bundle.public:
        raise ValueError("Execution and evaluator must use the same frozen task")
    root = evidence_dir.resolve()
    build_job_plan(
        request,
        jobs_dir=root / "execution",
        task_dirs={run.task.instance_id: root / "tasks" / run.task.instance_id},
    )
    root.mkdir(parents=True, mode=0o700, exist_ok=False)
    frozen = {
        "schema_version": 1,
        "prototype": True,
        "ranking_eligible": False,
        "execution_kind": execution_kind,
        "job_id": request.job_id,
        "run_id": run.run_id,
        "task": asdict(bundle.public),
        "agent_fingerprint": run.agent.fingerprint,
        "agent_version": run.agent.agent_version,
        "model_provider": run.agent.model_provider,
        "model_name": run.agent.model_name,
        "reasoning_effort": run.agent.critical_config["reasoning_effort"],
        "limits": asdict(request.limits),
        "backend_revision": request.backend_revision,
        "artifact_contract_version": request.artifact_contract_version,
        "evaluation_track": request.evaluation_track,
    }
    _write(root / "request.json", frozen)
    stage = "execution"
    try:
        trials = execution.execute(request)
        if len(trials) != 1 or trials[0].run_id != run.run_id:
            raise ValueError("Execution returned an unexpected run identity")
        (trial,) = trials
        _write(root / "execution.json", asdict(trial))
        if trial.termination_reason is not TerminationReason.COMPLETED:
            raise ValueError(
                "Execution did not complete; do not evaluate a partial patch"
            )
        stage = "patch_validation"
        if trial.patch_ref is None:
            raise ValueError("Execution has no patch reference")
        patch = _read_patch(trial.patch_ref, root)
        stage = "evaluation"
        result = evaluator.evaluate(
            EvaluationRequest(
                run.run_id, bundle.evaluator, patch, run.agent.fingerprint
            )
        )
        if result.run_id != run.run_id:
            raise ValueError("Evaluator returned an unexpected run identity")
        _write(root / "evaluation.json", asdict(result))
        _write(
            root / "result.json",
            {"prototype": True, "status": "completed", "resolved": result.resolved},
        )
        return result
    except (Exception, KeyboardInterrupt) as exc:
        failure: dict[str, object] = {
            "prototype": True,
            "status": "failed",
            "stage": stage,
            "resolved": None,
            "error_type": type(exc).__name__,
        }
        if isinstance(exc, (EvaluationError, PatchArtifactError)):
            failure["error_code"] = exc.code
        if isinstance(exc, EvaluationError):
            failure["evidence_refs"] = [asdict(ref) for ref in exc.evidence_refs]
        # Do not persist exception text: upstream errors may contain secrets.
        _write(root / "result.json", failure)
        raise


def _read_patch(ref: ArtifactRef, root: Path) -> bytes:
    path = Path(ref.object_key)
    if not path.is_absolute():
        path = root / path
    path.resolve().relative_to(root)
    if (
        path.is_symlink()
        or path.name != "model.patch"
        or ref.artifact_type != "model_patch"
        or ref.truncated
        or ref.deleted_at is not None
    ):
        raise ValueError("Unusable patch reference")
    validated = validate_patch_artifact(path.parent)
    if (validated.size_bytes, validated.sha256) != (ref.size_bytes, ref.sha256):
        raise ValueError("Execution patch reference does not match its content")
    return validated.content


def _write(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, default=_date)
        stream.write("\n")


def _date(value: object) -> str:
    from datetime import datetime

    if not isinstance(value, datetime):
        raise TypeError("Unsupported evidence value")
    return value.isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--check-network", action="store_true")
    arguments = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    report = task_preflight(repo)
    accepted = True
    if arguments.check_network:
        directory = (
            repo / "runtime/prototype" / f"network-preflight-{uuid.uuid4().hex[:12]}"
        )
        network = network_preflight(directory)
        report["network"] = network
        report["evidence_directory"] = str(directory)
        accepted = network["status"] == "SUPPORTED_KERNEL"
    print(json.dumps(report, indent=2))
    return 0 if accepted else 2


if __name__ == "__main__":
    raise SystemExit(main())
