from __future__ import annotations

import os
import re
import subprocess
import uuid
from pathlib import Path

import pytest

from eval_platform.adapters.execution.harbor.artifacts import (
    validate_patch_artifact,
)
from eval_platform.adapters.tasks.swe_gym import CANDIDATE_IMAGE

pytestmark = pytest.mark.integration
_BASE_COMMIT = "e7b917ec7532206b996542570f4b68a33c3ff771"
_CASES = (
    (
        "modified",
        "printf '\\n# agentexam tracked probe\\n' >> CREDITS",
        ("diff --git a/CREDITS b/CREDITS", "+# agentexam tracked probe"),
        False,
    ),
    (
        "new",
        "printf 'agentexam new file\\n' > agentexam-new.txt",
        ("diff --git a/agentexam-new.txt b/agentexam-new.txt", "new file mode"),
        False,
    ),
    (
        "deleted",
        "rm CREDITS",
        ("diff --git a/CREDITS b/CREDITS", "deleted file mode"),
        False,
    ),
    (
        "committed",
        "printf '\\n# agentexam committed probe\\n' >> CREDITS; "
        "git add CREDITS; "
        "git -c user.name=AgentExam -c user.email=agentexam@example.invalid "
        "commit -m agentexam-probe >/dev/null",
        ("diff --git a/CREDITS b/CREDITS", "+# agentexam committed probe"),
        True,
    ),
)


@pytest.mark.parametrize(
    ("case_name", "mutation", "expected", "head_changed"),
    _CASES,
)
def test_collects_complete_patch_from_fixed_image(
    tmp_path: Path,
    case_name: str,
    mutation: str,
    expected: tuple[str, str],
    head_changed: bool,
) -> None:
    if os.environ.get("AGENTEXAM_RUN_PATCH_INTEGRATION") != "1":
        pytest.skip("Set AGENTEXAM_RUN_PATCH_INTEGRATION=1 for this Docker probe")

    script = (
        Path(__file__).resolve().parents[2]
        / "src/eval_platform/adapters/tasks/collect_patch.sh"
    )
    assert script.is_file()
    name = f"agentexam-patch-{case_name}-{uuid.uuid4().hex[:12]}"
    assert re.fullmatch(r"[a-z0-9-]+", name)
    command = (
        "set -euo pipefail; cd /testbed; "
        f'test "$(git rev-parse HEAD)" = "{_BASE_COMMIT}"; '
        f"{mutation}; "
        f"bash /tmp/collect-patch.sh {_BASE_COMMIT}; "
        "printf 'AGENTEXAM_HEAD='; git rev-parse HEAD"
    )
    artifact_dir = tmp_path / case_name / "artifacts"
    artifact_dir.mkdir(parents=True)
    try:
        _docker(
            "create",
            "--name",
            name,
            "--network",
            "none",
            CANDIDATE_IMAGE,
            "bash",
            "-lc",
            command,
        )
        _docker("cp", str(script), f"{name}:/tmp/collect-patch.sh")
        completed = _docker("start", "--attach", name)
        _docker("cp", f"{name}:/logs/artifacts/.", str(artifact_dir))
    finally:
        subprocess.run(
            ["docker", "rm", "--force", name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=30,
            check=False,
        )

    patch = validate_patch_artifact(artifact_dir)
    text = patch.content.decode("utf-8")
    assert not patch.is_empty and not patch.warnings
    assert all(marker in text for marker in expected)
    head = completed.stdout.rsplit("AGENTEXAM_HEAD=", maxsplit=1)[1].strip()
    assert (head != _BASE_COMMIT) is head_changed


def _docker(*arguments: str) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["docker", *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr[-4000:]
    return completed
