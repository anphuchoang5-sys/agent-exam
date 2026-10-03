import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from threading import Event

import pytest
from jobs.execution.support.fakes import Backend, Evaluator, MemoryArtifacts
from jobs.execution.support.fixtures import queued_job
from jobs.execution.support.memory import ExecutableMemoryJobs

from eval_platform.application.execute_job import JobExecutor
from eval_platform.application.job_lifecycle.cancellation import JobCancellation
from eval_platform.delivery.worker.command import run_command
from eval_platform.delivery.worker.main import WorkerShell
from eval_platform.domain.identity import AuthenticatedActor
from eval_platform.domain.jobs.execution import JobLeaseConflict
from eval_platform.domain.jobs.models import JobNotFound, JobUnavailable


def _executor(repository, bundle, now):
    artifacts = MemoryArtifacts()
    backend = Backend(artifacts, b"diff --git a/a b/a\n")
    source = type("Source", (), {"load": lambda self, identity: bundle})()
    executor = JobExecutor(
        repository, artifacts, backend, Evaluator(artifacts), source, lambda: now
    )
    return executor, backend


def _cancel(repository, job, now):
    actor = AuthenticatedActor(job.created_by, "owner", "owner")
    return JobCancellation(repository, lambda: now).cancel(
        actor, job.job_id, "Cancel before execution", "preparing-cancel-0001"
    )


def test_preparing_cancellation_keeps_worker_loop_running(tmp_path, capsys):
    now = datetime(2026, 10, 3, tzinfo=UTC)
    first, bundle = queued_job(now)
    second, _ = queued_job(now + timedelta(seconds=1))
    now += timedelta(seconds=2)
    ready, resume = Event(), Event()

    class PausedJobs(ExecutableMemoryJobs):
        def start_execution(self, lease, at):
            if lease.job_id == first.job_id:
                ready.set()
                assert resume.wait(5), "Cancellation did not release the claim barrier"
            return super().start_execution(lease, at)

    repository = PausedJobs(first, second)
    executor, backend = _executor(repository, bundle, now)
    worker = WorkerShell(repository, executor, lambda: now)
    stop = tmp_path / "stop"
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(
            run_command,
            ["worker-one", "--loop", "--stop-file", str(stop)],
            lambda: worker,
            wait=lambda _seconds: stop.touch(),
        )
        try:
            assert ready.wait(5), "Worker did not reach the claim/start barrier"
            assert repository.get(first.job_id).status == "PREPARING"
            canceled = _cancel(repository, first, now).record
        finally:
            resume.set()
        assert future.result(timeout=5) == 0

    assert repository.get(first.job_id) == canceled
    assert canceled.status == "CANCELED"
    assert {run.status for run in canceled.runs} == {"CANCELED"}
    assert repository.get(second.job_id).status == "COMPLETED"
    assert [request.job_id for request in backend.requests] == [second.job_id]
    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == {
        "status": "worker_stopped",
        "completed_cycles": 2,
    }


@pytest.mark.parametrize("mismatch", ["worker", "job_version", "run_version", "expiry"])
def test_non_cancellation_lease_conflicts_still_fail_closed(mismatch):
    now = datetime(2026, 10, 3, tzinfo=UTC)
    job, bundle = queued_job(now)
    repository = ExecutableMemoryJobs(job)
    claimed = repository.claim("worker-one", now)
    overrides = {
        "worker": {"worker_id": "wrong-worker"},
        "job_version": {"job_version": claimed.lease.job_version + 1},
        "run_version": {"run_version": claimed.lease.run_version + 1},
        "expiry": {"lease_expires_at": now},
    }
    claimed = replace(claimed, lease=replace(claimed.lease, **overrides[mismatch]))
    executor, backend = _executor(repository, bundle, now)

    with pytest.raises(JobLeaseConflict):
        executor.execute(claimed)

    assert repository.get(job.job_id).status == "PREPARING"
    assert backend.requests == []


@pytest.mark.parametrize("failure", [JobUnavailable, JobNotFound, OSError])
def test_cancellation_reread_errors_are_not_swallowed(monkeypatch, failure):
    now = datetime(2026, 10, 3, tzinfo=UTC)
    job, bundle = queued_job(now)
    repository = ExecutableMemoryJobs(job)
    claimed = repository.claim("worker-one", now)
    _cancel(repository, job, now)
    executor, backend = _executor(repository, bundle, now)

    def unavailable(_job_id):
        raise failure("reread failed")

    monkeypatch.setattr(repository, "get", unavailable)
    with pytest.raises(failure, match="reread failed"):
        executor.execute(claimed)
    assert backend.requests == []


def test_start_storage_failure_is_not_reclassified_as_cancellation(monkeypatch):
    now = datetime(2026, 10, 3, tzinfo=UTC)
    job, bundle = queued_job(now)
    repository = ExecutableMemoryJobs(job)
    claimed = repository.claim("worker-one", now)
    _cancel(repository, job, now)
    executor, backend = _executor(repository, bundle, now)

    def unavailable(_lease, _now):
        raise JobUnavailable("start failed")

    monkeypatch.setattr(repository, "start_execution", unavailable)
    with pytest.raises(JobUnavailable, match="start failed"):
        executor.execute(claimed)
    assert backend.requests == []
