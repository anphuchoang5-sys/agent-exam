from dataclasses import replace
from datetime import UTC, datetime
from hashlib import sha256
from unittest.mock import Mock

import pytest
from jobs.execution.support.fakes import MemoryArtifacts
from jobs.execution.support.fixtures import queued_job

from eval_platform.application.execution.completion import CompletionFactory
from eval_platform.application.execution.evidence import EvidencePublication
from eval_platform.domain.catalog import ArtifactUnavailable
from eval_platform.domain.result import (
    ArtifactRef,
    DeterministicResult,
    ExecutionTrialResult,
    TerminationReason,
)

NOW = datetime(2026, 10, 3, tzinfo=UTC)
RUN_ID = "5e87af1c-a652-4c64-a1a3-e454e4638ebd"


def source(store, name, kind, content, content_type="text/plain"):
    reference = ArtifactRef(
        f"private/{name}", kind, len(content), sha256(content).hexdigest(), content_type
    )
    store.content[reference.object_key] = content
    return reference


@pytest.mark.parametrize("content", [b"", b"x" * 128, b"h" * 128 + b"t" * 128])
def test_raw_duplicates_count_one_verified_object_and_one_budget_contribution(content):
    origin, durable = MemoryArtifacts(), MemoryArtifacts()
    first = source(origin, "stdout.log", "harness_log", content)
    second = source(origin, "stderr.log", "harness_log", content)
    distinct_kind = source(origin, "test_output.txt", "harness_test_output", content)
    clock = Mock(return_value=NOW)
    durable.put_immutable = Mock(wraps=durable.put_immutable)
    publication = EvidencePublication(origin, durable, clock)

    published, warnings = publication.publish_raw(
        RUN_ID, (first, second, distinct_kind, second), 128, 256
    )

    assert warnings == ()
    assert len(published) == len(durable.content) == 2
    assert durable.put_immutable.call_count == clock.call_count == 2
    assert [item.artifact_type for item in published] == [
        "harness_log_raw",
        "harness_test_output_raw",
    ]
    assert sum(item.size_bytes for item in published) == min(len(content), 128) * 2
    assert published[0].original_size_bytes == len(content)
    assert published[0].truncated == (len(content) > 128)


def test_duplicate_source_is_still_independently_verified():
    origin, durable = MemoryArtifacts(), MemoryArtifacts()
    first = source(origin, "stdout.log", "harness_log", b"same")
    second = replace(first, object_key="private/stderr.log")
    origin.content[second.object_key] = b"fake"

    with pytest.raises(ArtifactUnavailable):
        EvidencePublication(origin, durable).publish_raw(
            RUN_ID, (first, second), 128, 256
        )


@pytest.mark.parametrize("reverse", [False, True])
def test_same_retained_body_with_conflicting_truncation_audit_fails_closed(reverse):
    origin, durable = MemoryArtifacts(), MemoryArtifacts()
    first = source(origin, "large.log", "harness_log", b"h" * 128 + b"t" * 128)
    retained = origin.read_bounded_verified(first, 128).content
    second = source(origin, "literal-marker.log", "harness_log", retained)
    sources = (second, first) if reverse else (first, second)

    with pytest.raises(ArtifactUnavailable):
        EvidencePublication(origin, durable).publish_raw(RUN_ID, sources, 128, 256)
    assert len(durable.content) == 1


@pytest.mark.parametrize("content", [b"", b"same synthetic log\n"])
def test_completion_assigns_one_id_and_index_to_same_content_raw_logs(content):
    job, _bundle = queued_job(NOW)
    run = job.runs[0]
    origin, durable = MemoryArtifacts(), MemoryArtifacts()
    publication = EvidencePublication(origin, durable, lambda: NOW)
    patch = source(
        origin, "model.patch", "model_patch", b"diff --git a/a b/a\n", "text/x-diff"
    )
    patch, patch_body = publication.prepare_patch(run.run_id, patch)
    publication.persist(patch, patch_body)
    report = source(origin, "report.json", "harness_report", b"{}", "application/json")
    logs = tuple(
        source(origin, name, kind, content)
        for name, kind in (
            ("test_output.txt", "harness_test_output"),
            ("stdout.log", "harness_log"),
            ("stderr.log", "harness_log"),
        )
    )
    result = DeterministicResult(
        run.run_id,
        True,
        True,
        report,
        logs,
        {"FAIL_TO_PASS": {"success": 1, "failure": 0}},
    )
    trial = ExecutionTrialResult(
        run.run_id,
        "harbor-job",
        "harbor-trial",
        TerminationReason.COMPLETED,
        patch,
        None,
    )

    completion = CompletionFactory(job, durable, publication, lambda: NOW).build(
        run, trial, result
    )

    records = completion.artifacts
    assert len(records) == len({item.reference.object_key for item in records}) == 7
    assert len({item.artifact_id for item in records}) == 7
    raw_logs = [
        item for item in records if item.reference.artifact_type == "harness_log_raw"
    ]
    assert len(raw_logs) == 1 and raw_logs[0].redaction_status == "blocked"
    assert durable.read_verified(raw_logs[0].reference) == content
    indexed_ids = {item.artifact_id for item in records}
    assert completion.result.report_artifact_id in indexed_ids
    assert completion.result.test_output_artifact_id in indexed_ids
