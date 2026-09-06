from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from eval_platform.adapters.evaluation.result_mapper import (
    map_evaluation,
    safe_identity,
)
from eval_platform.application.ports.evaluator import EvaluationError, EvaluationRequest
from eval_platform.domain.task import EvaluatorTaskData

INSTANCE = "python__mypy-15413"
PATCH = b"diff --git a/example.py b/example.py\n"


def _evidence(tmp_path: Path, outcome: str = "resolved") -> EvaluationRequest:
    request = EvaluationRequest(
        "unit-run",
        EvaluatorTaskData(INSTANCE, "1.4", "", "", ("fix",), ("keep",)),
        b"" if outcome == "empty_patch" else PATCH,
        "codex-config",
    )
    summary: dict[str, object] = {
        "schema_version": 2,
        "total_instances": 1,
        "submitted_instances": 1,
        "submitted_ids": [INSTANCE],
        "incomplete_ids": [],
        "unstopped_containers": [],
        "unstopped_instances": 0,
    }
    for category in ("resolved", "unresolved", "empty_patch", "error", "completed"):
        included = category == outcome or (
            category == "completed" and outcome in {"resolved", "unresolved"}
        )
        summary[f"{category}_ids"] = [INSTANCE] if included else []
        summary[f"{category}_instances"] = int(included)
    _summary(tmp_path).write_text(json.dumps(summary), encoding="utf-8")
    if outcome in {"resolved", "unresolved"}:
        folder = _report(tmp_path).parent
        folder.mkdir(parents=True)
        result = {
            "patch_exists": True,
            "patch_successfully_applied": True,
            "resolved": outcome == "resolved",
            "tests_status": {
                "FAIL_TO_PASS": {
                    "success": ["fix"] if outcome == "resolved" else [],
                    "failure": [] if outcome == "resolved" else ["fix"],
                },
                "PASS_TO_PASS": {"success": ["keep"], "failure": []},
            },
        }
        _report(tmp_path).write_text(json.dumps({INSTANCE: result}), encoding="utf-8")
        (folder / "patch.diff").write_bytes(PATCH)
        (folder / "test_output.txt").write_text(
            "test execution evidence", encoding="utf-8"
        )
    return request


def _summary(root: Path) -> Path:
    return root / "codex-config.unit-run.json"


def _report(root: Path) -> Path:
    return root / "logs/run_evaluation/unit-run/codex-config" / INSTANCE / "report.json"


@pytest.mark.parametrize("outcome", ["resolved", "unresolved", "empty_patch"])
def test_maps_complete_and_empty_evidence(tmp_path: Path, outcome: str) -> None:
    request = _evidence(tmp_path, outcome)
    result = map_evaluation(request, tmp_path, artifact_root=tmp_path)
    assert result.resolved is (outcome == "resolved")
    assert result.patch_applied is (outcome != "empty_patch")
    assert result.run_id == request.run_id
    assert result.report_ref.sha256
    if outcome == "empty_patch":
        assert result.report_ref.artifact_type == "harness_summary"


def test_error_summary_is_never_an_unresolved_result(tmp_path: Path) -> None:
    request = _evidence(tmp_path, "error")
    with pytest.raises(EvaluationError) as exc:
        map_evaluation(request, tmp_path, artifact_root=tmp_path)
    assert exc.value.code == "HARNESS_EVALUATION_FAILED"
    assert exc.value.evidence_refs[0].artifact_type == "harness_summary"


@pytest.mark.parametrize(
    "mutation", ["identity", "boolean", "tests", "patch", "summary", "missing"]
)
def test_rejects_inconsistent_or_incomplete_evidence(
    tmp_path: Path, mutation: str
) -> None:
    request = _evidence(tmp_path)
    report = json.loads(_report(tmp_path).read_text(encoding="utf-8"))
    if mutation == "identity":
        report["another-task"] = report.pop(INSTANCE)
    elif mutation == "boolean":
        report[INSTANCE]["resolved"] = "false"
    elif mutation == "tests":
        report[INSTANCE]["tests_status"]["FAIL_TO_PASS"]["success"] = ["another-test"]
    elif mutation == "patch":
        (_report(tmp_path).parent / "patch.diff").write_bytes(b"different")
    elif mutation == "summary":
        data = json.loads(_summary(tmp_path).read_text(encoding="utf-8"))
        data["error_ids"] = [INSTANCE]
        data["error_instances"] = 1
        _summary(tmp_path).write_text(json.dumps(data), encoding="utf-8")
    _report(tmp_path).write_text(json.dumps(report), encoding="utf-8")
    if mutation == "missing":
        _report(tmp_path).unlink()
    with pytest.raises(EvaluationError):
        map_evaluation(request, tmp_path, artifact_root=tmp_path)


@pytest.mark.parametrize(
    "identity", ["../run", "/tmp/run", "a/b", "a\\b", "-option", "."]
)
def test_rejects_path_and_argument_injection(identity: str) -> None:
    with pytest.raises(ValueError):
        safe_identity(identity)


@pytest.mark.skipif(os.name != "nt", reason="Windows extended-path regression")
def test_imports_report_beyond_windows_max_path(tmp_path: Path) -> None:
    root = tmp_path / ("a" * 60) / ("b" * 60) / ("c" * 60)
    extended = Path("\\\\?\\" + str(root))
    extended.mkdir(parents=True)
    request = _evidence(extended)
    assert len(str(_report(root))) > 260
    assert _report(extended).is_file()
    result = map_evaluation(request, root, artifact_root=root)
    assert result.resolved
    assert result.report_ref.object_key == _report(root).relative_to(root).as_posix()
    assert any(ref.object_key.endswith("test_output.txt") for ref in result.log_refs)
