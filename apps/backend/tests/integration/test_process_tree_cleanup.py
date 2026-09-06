from __future__ import annotations

import ctypes
import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest

from eval_platform.adapters.execution.harbor.process_runner import (
    run_bounded_process,
)

pytestmark = pytest.mark.integration
_STILL_ACTIVE = 259
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


def test_timeout_removes_parent_and_child_processes(tmp_path: Path) -> None:
    if os.environ.get("AGENTEXAM_RUN_PROCESS_TREE_INTEGRATION") != "1":
        pytest.skip("Set AGENTEXAM_RUN_PROCESS_TREE_INTEGRATION=1 for this probe")

    evidence_root = tmp_path / "evidence"
    evidence_root.mkdir()
    child_pid_path = tmp_path / "child.pid"
    script = (
        "import pathlib, subprocess, sys, time; "
        "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
        "pathlib.Path(sys.argv[1]).write_text(str(child.pid)); "
        "print('ready', flush=True); time.sleep(60)"
    )
    outcome = run_bounded_process(
        [sys.executable, "-c", script, str(child_pid_path)],
        cwd=tmp_path,
        env=os.environ.copy(),
        timeout_sec=1,
        evidence_root=evidence_root,
        max_log_bytes=4096,
    )

    child_pid = int(child_pid_path.read_text(encoding="ascii"))
    try:
        assert outcome.returncode == 124 and outcome.timed_out
        assert outcome.warnings == ("HARBOR_PROCESS_TIMEOUT",)
        assert not _is_process_running(child_pid)
    finally:
        if _is_process_running(child_pid):
            _terminate_exact_process(child_pid)


def _is_process_running(pid: int) -> bool:
    if os.name != "nt":
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        return True
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return False
    try:
        exit_code = ctypes.c_ulong()
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            return False
        return exit_code.value == _STILL_ACTIVE
    finally:
        kernel32.CloseHandle(handle)


def _terminate_exact_process(pid: int) -> None:
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
        )
    else:
        os.kill(pid, signal.SIGKILL)
