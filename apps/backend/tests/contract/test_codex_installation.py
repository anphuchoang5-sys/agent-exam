from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import tarfile
import uuid
from pathlib import Path

import pytest

from eval_platform.adapters.execution import codex_install as installer
from eval_platform.adapters.execution.harbor.process_runner import run_bounded_process
from eval_platform.adapters.execution.harbor_entry import harbor_environment

pytestmark = pytest.mark.contract


def _archive(tmp_path, monkeypatch, *, change=None):
    prefix = installer._PREFIX
    files = dict.fromkeys(installer._FILES, b"test-only-not-an-executable")
    files["package/package.json"] = json.dumps(
        {
            "name": "@openai/codex",
            "version": installer.PACKAGE_VERSION,
            "os": ["linux"],
            "cpu": ["x64"],
        }
    ).encode()
    files[prefix + "codex-package.json"] = json.dumps(
        {
            "layoutVersion": 1,
            "version": installer.VERSION,
            "target": installer.TARGET,
            "variant": "codex",
            "entrypoint": "bin/codex",
            "resourcesDir": "codex-resources",
            "pathDir": "codex-path",
        }
    ).encode()
    if change == "platform":
        files["package/package.json"] = b"{}"
    archive = tmp_path / "synthetic.tgz"
    with tarfile.open(archive, "w:gz") as package:
        for name, value in files.items():
            member = tarfile.TarInfo(name)
            member.size = len(value)
            if name.endswith("README.md") and change == "traversal":
                member.name = "../escape"
            if name.endswith("README.md") and change == "symlink":
                member.type, member.linkname, member.size = tarfile.SYMTYPE, "/tmp/x", 0
            package.addfile(member, io.BytesIO(value))
    monkeypatch.setattr(installer, "ARCHIVE_BYTES", archive.stat().st_size)
    monkeypatch.setattr(
        installer, "ARCHIVE_SHA512", hashlib.sha512(archive.read_bytes()).hexdigest()
    )
    return archive


@pytest.mark.parametrize("change", ["size", "hash", "platform", "traversal", "symlink"])
def test_invalid_installation_input_is_rejected_before_extracting(
    tmp_path, monkeypatch, change
):
    archive = _archive(tmp_path, monkeypatch, change=change)
    if change == "size":
        monkeypatch.setattr(installer, "ARCHIVE_BYTES", 0)
    if change == "hash":
        monkeypatch.setattr(installer, "ARCHIVE_SHA512", "0" * 128)
    destination = tmp_path / "output"
    with pytest.raises(ValueError, match="CODEX_PACKAGE_"):
        installer.prepare_codex_bundle(archive, destination)
    assert not destination.exists() and not (tmp_path / "escape").exists()


def test_bundle_manifest_and_no_overwrite(tmp_path, monkeypatch):
    archive = _archive(tmp_path, monkeypatch)
    destination = tmp_path / "output"
    bundle = installer.prepare_codex_bundle(archive, destination)
    assert (bundle / "bin/codex").read_bytes() == b"test-only-not-an-executable"
    manifest = json.loads((destination / "installation-input.json").read_text())
    assert not manifest["real_codex_ready"] and len(manifest["files_sha256"]) == 8
    with pytest.raises(FileExistsError):
        installer.prepare_codex_bundle(archive, destination)


@pytest.mark.integration
def test_fixed_codex_installs_offline_and_harbor_reuses_it(tmp_path):
    if os.environ.get("AGENTEXAM_RUN_CODEX_INSTALLATION") != "1":
        pytest.skip("Set AGENTEXAM_RUN_CODEX_INSTALLATION=1 for the Docker contract")
    repo = Path(__file__).resolve().parents[4]
    tmp_path.resolve().relative_to(repo / "runtime")
    archive = Path(os.environ["AGENTEXAM_CODEX_ARCHIVE"])
    bundle = installer.prepare_codex_bundle(archive, tmp_path / "input")
    label = uuid.uuid4().hex
    try:
        outcome = run_bounded_process(
            [
                str(repo / "framework/harbor/.venv/Scripts/python.exe"),
                str(Path(__file__).with_name("codex_install_probe.py")),
                str(bundle),
                str(tmp_path),
                label,
            ],
            cwd=repo,
            env=harbor_environment(),
            timeout_sec=300,
            evidence_root=tmp_path,
            max_log_bytes=1024 * 1024,
        )
        assert outcome.returncode == 0 and not outcome.timed_out, tmp_path
        assert not outcome.warnings
        summary = json.loads((tmp_path / "installation-result.json").read_text())
        assert summary["harbor_reused_preinstalled"] and not summary["model_called"]
        cleanup = json.loads((tmp_path / "installation-cleanup.json").read_text())
        assert cleanup["verified"]
    finally:
        command = [
            "docker",
            "ps",
            "-aq",
            "--filter",
            f"label=agentexam.installation_probe={label}",
        ]
        ids = subprocess.check_output(command, text=True, timeout=30).split()
        for identity in ids:
            subprocess.run(
                ["docker", "rm", "-f", identity],
                check=True,
                capture_output=True,
                timeout=30,
            )
        assert not subprocess.check_output(command, text=True, timeout=30).strip()
