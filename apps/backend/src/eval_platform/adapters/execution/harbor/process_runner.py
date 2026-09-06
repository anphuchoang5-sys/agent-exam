from __future__ import annotations

import json
import os
import signal
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from eval_platform.adapters.execution.harbor.artifacts import RAW_ARTIFACT_MAX_BYTES
from eval_platform.adapters.execution.harbor.process_evidence import (
    CapturedLog,
    LogCaptureSession,
    write_log,
)

_CLEANUP_TIMEOUT_SEC = 5
_TIMEOUT_EXIT_CODE = 124


@dataclass(frozen=True, slots=True)
class ProcessOutcome:
    returncode: int
    timed_out: bool
    stdout: CapturedLog
    stderr: CapturedLog
    warnings: tuple[str, ...]
    start_error: OSError | None = None


def run_bounded_process(
    command: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    timeout_sec: int | float,
    evidence_root: Path,
    max_log_bytes: int = RAW_ARTIFACT_MAX_BYTES,
) -> ProcessOutcome:
    if timeout_sec <= 0 or max_log_bytes < 0:
        raise ValueError("Process limits must be valid")
    stdout_path = evidence_root / "harbor.stdout.log"
    stderr_path = evidence_root / "harbor.stderr.log"
    try:
        process = _start_process(command, cwd, env)
    except OSError as error:
        stdout = write_log(stdout_path, b"", max_log_bytes)
        message = f"{type(error).__name__}: {error}".encode("utf-8", errors="replace")
        stderr = write_log(stderr_path, message, max_log_bytes)
        start_warnings = ["HARBOR_PROCESS_START_FAILED"]
        _add_truncation_warnings(start_warnings, stdout, stderr)
        outcome = ProcessOutcome(
            -1, False, stdout, stderr, tuple(start_warnings), error
        )
        _write_manifest(evidence_root, outcome, max_log_bytes)
        return outcome

    assert process.stdout is not None and process.stderr is not None
    capture = LogCaptureSession.start(
        process.stdout, process.stderr, evidence_root, max_log_bytes
    )
    warnings: list[str] = []
    timed_out = False
    try:
        process.wait(timeout=timeout_sec)
    except subprocess.TimeoutExpired:
        timed_out = True
        warnings.append("HARBOR_PROCESS_TIMEOUT")
        warnings.extend(_terminate_process_tree(process))
    stdout, stderr = capture.finish()
    _add_truncation_warnings(warnings, stdout, stderr)
    returncode = (
        _TIMEOUT_EXIT_CODE
        if timed_out
        else process.returncode
        if process.returncode is not None
        else -1
    )
    outcome = ProcessOutcome(returncode, timed_out, stdout, stderr, tuple(warnings))
    _write_manifest(evidence_root, outcome, max_log_bytes)
    return outcome


def _start_process(
    command: Sequence[str], cwd: Path, env: Mapping[str, str]
) -> subprocess.Popen[bytes]:
    if os.name == "nt":
        return subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
    return subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )


def _terminate_process_tree(process: subprocess.Popen[bytes]) -> tuple[str, ...]:
    if process.poll() is not None:
        return ()
    failed = False
    try:
        if os.name == "nt":
            completed = subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=_CLEANUP_TIMEOUT_SEC,
                check=False,
            )
            failed = completed.returncode != 0
        else:
            posix_os = cast(Any, os)
            posix_signal = cast(Any, signal)
            posix_os.killpg(posix_os.getpgid(process.pid), posix_signal.SIGKILL)
    except (OSError, subprocess.SubprocessError):
        failed = True
    if failed and process.poll() is None:
        process.kill()
    try:
        process.wait(timeout=_CLEANUP_TIMEOUT_SEC)
    except subprocess.TimeoutExpired:
        failed = True
        process.kill()
        process.wait(timeout=_CLEANUP_TIMEOUT_SEC)
    return ("HARBOR_PROCESS_TREE_CLEANUP_FAILED",) if failed else ()


def _add_truncation_warnings(
    warnings: list[str], stdout: CapturedLog, stderr: CapturedLog
) -> None:
    if stdout.truncated:
        warnings.append("HARBOR_STDOUT_TRUNCATED")
    if stderr.truncated:
        warnings.append("HARBOR_STDERR_TRUNCATED")


def _write_manifest(root: Path, outcome: ProcessOutcome, max_bytes: int) -> None:
    value = {
        "returncode": outcome.returncode,
        "timed_out": outcome.timed_out,
        "start_error_type": type(outcome.start_error).__name__
        if outcome.start_error is not None
        else None,
        "warnings": list(outcome.warnings),
        "logs": {
            "stdout": _log_value(outcome.stdout, max_bytes),
            "stderr": _log_value(outcome.stderr, max_bytes),
        },
    }
    (root / "harbor-process.json").write_text(
        json.dumps(value, indent=2, sort_keys=True), encoding="utf-8", newline="\n"
    )


def _log_value(log: CapturedLog, max_bytes: int) -> dict[str, object]:
    return {
        "file": log.path.name,
        "max_bytes": max_bytes,
        "saved_bytes": log.saved_bytes,
        "truncated": log.truncated,
    }
