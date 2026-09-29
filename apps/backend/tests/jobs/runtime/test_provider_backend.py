"""The owner Worker composes the provider route without ChatGPT authentication."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from eval_platform.adapters.artifacts.config import MinioConfig
from eval_platform.adapters.execution.harbor import adapter as adapter_module
from eval_platform.adapters.execution.harbor.adapter import HarborExecutionAdapter
from eval_platform.adapters.execution.harbor.config_mapper import (
    ARTIFACT_CONTRACT_VERSION,
    HARBOR_REVISION,
)
from eval_platform.application.ports.execution import (
    ExecutionJobRequest,
    ExecutionRunRequest,
    RunLimits,
)
from eval_platform.delivery.catalog_presets import INTERNAL_TEST_AGENT_PRESETS
from eval_platform.delivery.worker import runtime as worker_runtime
from eval_platform.delivery.worker.runtime import RuntimeWorkerConfig
from eval_platform.domain.task import EvaluationTask

IMAGE = "sha256:" + "d" * 64


def _request() -> ExecutionJobRequest:
    agent = next(iter(INTERNAL_TEST_AGENT_PRESETS.values()))[1]
    task = EvaluationTask(
        "dataset",
        "revision",
        "train",
        "python__mypy-15413",
        "python/mypy",
        "a" * 40,
        "public issue",
        "image@sha256:" + "b" * 64,
        "c" * 64,
    )
    return ExecutionJobRequest(
        "job-provider",
        (ExecutionRunRequest("run-provider", task, agent),),
        RunLimits(300, 1, 2048, 4096),
        HARBOR_REVISION,
        ARTIFACT_CONTRACT_VERSION,
    )


def test_provider_adapter_stages_overlay_and_removes_auth_placeholder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    executable = tmp_path / "harbor.exe"
    executable.touch()
    executable.with_name("python.exe").touch()
    archive = tmp_path / "codex.tgz"
    archive.write_bytes(b"placeholder")

    def prepare(_source: Path, destination: Path) -> Path:
        destination.mkdir()
        return destination

    observed: dict[str, object] = {}

    def run(_self, _plan, _request, run_root, config_path, bundle, *_args):
        observed["config"] = json.loads(config_path.read_text())
        observed["placeholder"] = run_root / ".provider-auth-placeholder.json"
        observed["bundle"] = bundle
        assert observed["placeholder"].is_file()
        return ()

    monkeypatch.setattr(adapter_module, "prepare_codex_bundle", prepare)
    monkeypatch.setattr(HarborExecutionAdapter, "_run", run)
    adapter = HarborExecutionAdapter(
        executable,
        tmp_path / "evidence",
        tmp_path,
        codex_archive=archive,
        provider_image_id=IMAGE,
    )
    assert adapter.execute(_request()) == ()
    config = observed["config"]
    overlays = config["environment"]["extra_docker_compose"]
    assert len(overlays) == 1 and overlays[0].endswith("provider-compose.json")
    assert not observed["placeholder"].exists()
    assert (tmp_path / "evidence/job-provider/provider-runtime.json").is_file()


def test_worker_provider_backend_requires_archive_and_pinned_image(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = RuntimeWorkerConfig(
        tmp_path,
        tmp_path / "runtime/evidence",
        tmp_path / "task.parquet",
        tmp_path / "codex.tgz",
        None,
        "host=127.0.0.1 password=must-not-connect",
        MinioConfig("http://127.0.0.1:9000", "bucket", "access", "secret"),
        IMAGE,
    )
    captured: dict[str, object] = {}
    monkeypatch.setattr(worker_runtime, "_verify_codex_archive", lambda path: None)
    monkeypatch.setattr(
        worker_runtime,
        "HarborExecutionAdapter",
        lambda *args, **kwargs: captured.update(args=args, kwargs=kwargs) or object(),
    )
    worker_runtime._create_provider_backend(config)
    assert captured["kwargs"] == {
        "codex_archive": config.codex_archive,
        "provider_image_id": IMAGE,
    }

    with pytest.raises(RuntimeError, match="PROVIDER_RUNTIME_NOT_READY"):
        worker_runtime._create_provider_backend(
            RuntimeWorkerConfig(
                config.project_root,
                config.evidence_root,
                config.task_parquet,
                config.codex_archive,
                None,
                config.dsn,
                config.minio,
                None,
            )
        )
