from __future__ import annotations

import io
import json
import sys

import pytest

from eval_platform.adapters.execution.harbor.process_runner import run_bounded_process


@pytest.mark.parametrize("mode", ["success", "failure", "timeout", "start-error"])
def test_known_secret_never_reaches_persisted_process_evidence(tmp_path, mode):
    secret = b"AGENTEXAM-FAKE-FILE-TOKEN"
    command = [sys.executable, "-c", "import sys; sys.exit(0)"]
    if mode == "start-error":
        command = [str(tmp_path / secret.decode() / "absent.exe")]
    else:
        script = (
            "import sys,time; value=sys.stdin.buffer.read(); "
            "sys.stdout.buffer.write(value); sys.stdout.flush(); "
            "sys.stderr.buffer.write(value); sys.stderr.flush(); "
            f"time.sleep({2 if mode == 'timeout' else 0}); "
            f"sys.exit({7 if mode == 'failure' else 0})"
        )
        # No secret is put in the child environment; fixtures are public fake values.
        script = script.replace("sys.stdin.buffer.read()", repr(secret))
        command = [sys.executable, "-c", script]
    outcome = run_bounded_process(
        command,
        cwd=tmp_path,
        env={},
        timeout_sec=0.3 if mode == "timeout" else 5,
        evidence_root=tmp_path,
        redactions=(secret,),
    )
    assert (
        outcome.returncode
        == {"success": 0, "failure": 7, "timeout": 124, "start-error": -1}[mode]
    )
    for path in tmp_path.glob("harbor*"):
        assert secret not in path.read_bytes()
    if mode != "start-error":
        assert outcome.stdout.path.read_bytes() == b"[REDACTED]"
        assert outcome.stderr.path.read_bytes() == b"[REDACTED]"
    manifest = json.loads((tmp_path / "harbor-process.json").read_text())
    assert "redactions" not in manifest


@pytest.mark.parametrize("split", range(1, 12))
def test_stream_redaction_catches_every_split_and_preserves_safe_bytes(split):
    from eval_platform.adapters.execution.redaction import Redactor

    source = b"prefix:fake-token-long|fake-token|suffix"
    chunks = (
        source[offset : offset + split] for offset in range(0, len(source), split)
    )
    assert b"".join(Redactor((b"fake-token", b"fake-token-long")).filter(chunks)) == (
        b"prefix:[REDACTED]|[REDACTED]|suffix"
    )


def test_log_limit_is_applied_after_redaction(tmp_path):
    from eval_platform.adapters.execution.harbor.process_evidence import write_log
    from eval_platform.adapters.execution.redaction import Redactor

    path = tmp_path / "bounded.log"
    result = write_log(path, b"xFAKESECRETtail", 5, redactor=Redactor((b"FAKESECRET",)))
    assert path.read_bytes() == b"x[RED"
    assert result.truncated and result.saved_bytes == 5


def test_streaming_both_channels_handles_read_chunk_boundary(tmp_path):
    from eval_platform.adapters.execution.harbor.process_evidence import (
        LogCaptureSession,
    )
    from eval_platform.adapters.execution.redaction import Redactor

    value = b"x" * (64 * 1024 - 3) + b"FAKESECRET" + b"tail"
    expected = value.replace(b"FAKESECRET", b"[REDACTED]")
    session = LogCaptureSession.start(
        io.BytesIO(value),
        io.BytesIO(value),
        tmp_path,
        128 * 1024,
        redactor=Redactor((b"FAKESECRET",)),
    )
    stdout, stderr, incomplete = session.finish(timeout_sec=2)
    assert incomplete == ()
    assert stdout.path.read_bytes() == stderr.path.read_bytes() == expected


@pytest.mark.parametrize("values", [(b"",), ("not-bytes",)])
def test_invalid_redaction_input_fails_before_start_or_file_write(tmp_path, values):
    with pytest.raises(ValueError, match="redaction"):
        run_bounded_process(
            ["must-not-start"],
            cwd=tmp_path,
            env={},
            timeout_sec=1,
            evidence_root=tmp_path,
            redactions=values,
        )
    assert list(tmp_path.iterdir()) == []


def test_empty_redactor_preserves_binary_and_repr_never_prints_values():
    from eval_platform.adapters.execution.redaction import Redactor

    assert b"".join(Redactor(()).filter([b"\x00abc\xff", b"end"])) == b"\x00abc\xffend"
    assert "FAKESECRET" not in repr(Redactor((b"FAKESECRET",)))


def test_start_exception_is_redacted_in_both_result_and_log(tmp_path, monkeypatch):
    import eval_platform.adapters.execution.harbor.process_runner as runner

    def fail(*args):
        raise OSError("cannot start with FAKESECRET")

    monkeypatch.setattr(runner, "_start_process", fail)
    outcome = run_bounded_process(
        ["not-started"],
        cwd=tmp_path,
        env={},
        timeout_sec=1,
        evidence_root=tmp_path,
        redactions=(b"FAKESECRET",),
    )
    assert "FAKESECRET" not in str(outcome.start_error)
    assert b"FAKESECRET" not in outcome.stderr.path.read_bytes()
    assert "[REDACTED]" in str(outcome.start_error)


def test_stream_matches_whole_buffer_for_overlapping_binary_patterns():
    import random
    import re

    from eval_platform.adapters.execution.redaction import Redactor

    rng = random.Random(7)
    for _ in range(200):
        values = tuple(
            bytes(rng.choices(b"abc\x00\xff", k=rng.randint(1, 8))) for _ in range(4)
        )
        source = bytes(rng.choices(b"abc\x00\xff", k=80))
        pattern = re.compile(
            b"|".join(
                re.escape(value)
                for value in sorted(set(values), key=lambda value: (-len(value), value))
            )
        )
        assert b"".join(
            Redactor(values).filter(source[i : i + 1] for i in range(80))
        ) == (pattern.sub(b"[REDACTED]", source))
