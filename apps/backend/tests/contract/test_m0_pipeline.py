from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

from eval_platform.application.ports.evaluator import EvaluationError
from eval_platform.domain.result import (
    ArtifactRef,
    DeterministicResult,
    ExecutionTrialResult,
    TerminationReason,
)
from prototype_codex_harbor_e2e import run_prototype

pytestmark = pytest.mark.contract


@pytest.mark.parametrize(
    "scenario",
    [
        "resolved",
        "unresolved",
        "empty",
        "execution_failed",
        "wrong_run",
        "wrong_eval_run",
        "hash_wrong",
        "size_wrong",
        "truncated",
        "outside",
        "patch_changed",
        "eval_error",
        "execution_exception",
    ],
)
def test_pipeline_evidence_and_failure_boundaries(pipeline, scenario):
    calls = []
    content = b"" if scenario == "empty" else b"diff --git a/a b/a\n"

    def execute(request):
        calls.append("execute")
        assert request == pipeline.request
        assert not hasattr(request.runs[0].task, "gold_patch")
        if scenario == "execution_exception":
            raise RuntimeError("SECRET_EXCEPTION_MUST_NOT_BE_SAVED")
        directory = pipeline.root / "execution/artifacts"
        if scenario == "outside":
            directory = pipeline.root.parent / "unrelated"
        directory.mkdir(parents=True)
        (directory / "model.patch").write_bytes(content)
        digest = hashlib.sha256(content).hexdigest()
        for name, value in (
            ("sha256", digest),
            ("bytes", str(len(content))),
            ("binary", "0"),
        ):
            (directory / f"patch.{name}").write_text(value)
        ref = ArtifactRef(
            str(directory / "model.patch"),
            "model_patch",
            len(content),
            digest,
            "text/plain",
            truncated=scenario == "truncated",
        )
        if scenario == "hash_wrong":
            ref = replace(ref, sha256="f" * 64)
        if scenario == "size_wrong":
            ref = replace(ref, size_bytes=999)
        if scenario == "patch_changed":
            (directory / "model.patch").write_bytes(content + b"changed")
        return (
            ExecutionTrialResult(
                "other" if scenario == "wrong_run" else "run-1",
                "job-1",
                "trial-1",
                TerminationReason.TIMED_OUT
                if scenario == "execution_failed"
                else TerminationReason.COMPLETED,
                ref,
                None,
            ),
        )

    report = ArtifactRef(
        "report.json", "harness_report", 0, "a" * 64, "application/json"
    )

    def evaluate(request):
        calls.append("evaluate")
        assert (
            request.model_patch == content and request.task == pipeline.bundle.evaluator
        )
        assert request.model_name_or_path == pipeline.request.runs[0].agent.fingerprint
        if scenario == "eval_error":
            raise EvaluationError(
                "HARNESS_EVALUATION_FAILED", "SECRET_ERROR", (report,)
            )
        return DeterministicResult(
            "other" if scenario == "wrong_eval_run" else "run-1",
            scenario == "resolved",
            scenario != "empty",
            report,
        )

    arguments = dict(
        execution=SimpleNamespace(execute=execute),
        evaluator=SimpleNamespace(evaluate=evaluate),
        evidence_dir=pipeline.root,
        execution_kind="internal_test",
    )
    if scenario in {"resolved", "unresolved", "empty"}:
        result = run_prototype(pipeline.request, pipeline.bundle, **arguments)
        assert result.resolved == (scenario == "resolved")
        assert calls == ["execute", "evaluate"]
        assert (pipeline.root / "evaluation.json").is_file()
    else:
        with pytest.raises((ValueError, RuntimeError)):
            run_prototype(pipeline.request, pipeline.bundle, **arguments)
        if scenario not in {"wrong_eval_run", "eval_error"}:
            assert calls == ["execute"]
    frozen = (pipeline.root / "request.json").read_text()
    assert "HIDDEN" not in frozen and "secret-logical-id" not in frozen
    assert not json.loads(frozen)["ranking_eligible"]
    final = (pipeline.root / "result.json").read_text()
    assert "SECRET" not in final
    if scenario not in {"resolved", "unresolved", "empty"}:
        assert json.loads(final)["resolved"] is None
    if scenario == "eval_error":
        assert json.loads(final)["evidence_refs"][0]["object_key"] == "report.json"
    before = (pipeline.root / "request.json").read_bytes()
    with pytest.raises(FileExistsError):
        run_prototype(pipeline.request, pipeline.bundle, **arguments)
    assert (pipeline.root / "request.json").read_bytes() == before


@pytest.mark.parametrize(
    "scenario", ["multiple_runs", "different_task", "unknown_kind"]
)
def test_preflight_rejects_before_creating_evidence(pipeline, scenario):
    request = pipeline.request
    if scenario == "multiple_runs":
        request = replace(
            request, runs=(*request.runs, replace(request.runs[0], run_id="r2"))
        )
    if scenario == "different_task":
        run = request.runs[0]
        request = replace(
            request, runs=(replace(run, task=replace(run.task, repo="other")),)
        )
    with pytest.raises(ValueError):
        run_prototype(
            request,
            pipeline.bundle,
            execution=object(),
            evaluator=object(),
            evidence_dir=pipeline.root,
            execution_kind="unknown" if scenario == "unknown_kind" else "internal_test",
        )
    assert not pipeline.root.exists()


def test_codex_mode_reaches_the_existing_execution_port(pipeline):
    class ExpectedStop(Exception):
        pass

    def execute(_request):
        raise ExpectedStop

    with pytest.raises(ExpectedStop):
        run_prototype(
            pipeline.request,
            pipeline.bundle,
            execution=SimpleNamespace(execute=execute),
            evaluator=object(),
            evidence_dir=pipeline.root,
            execution_kind="codex",
        )
    request = json.loads((pipeline.root / "request.json").read_text())
    assert request["execution_kind"] == "codex"
    assert json.loads((pipeline.root / "result.json").read_text())["stage"] == (
        "execution"
    )
