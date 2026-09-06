from __future__ import annotations

import threading
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import IO

_READ_CHUNK_BYTES = 64 * 1024


@dataclass(frozen=True, slots=True)
class CapturedLog:
    path: Path
    saved_bytes: int
    truncated: bool


class ProcessLogError(RuntimeError):
    pass


@dataclass(slots=True)
class LogCaptureSession:
    threads: tuple[threading.Thread, threading.Thread]
    results: dict[str, CapturedLog | Exception]

    @classmethod
    def start(
        cls,
        stdout: IO[bytes],
        stderr: IO[bytes],
        root: Path,
        max_bytes: int,
    ) -> LogCaptureSession:
        results: dict[str, CapturedLog | Exception] = {}
        threads = (
            _capture_thread(
                "stdout", stdout, root / "harbor.stdout.log", max_bytes, results
            ),
            _capture_thread(
                "stderr", stderr, root / "harbor.stderr.log", max_bytes, results
            ),
        )
        return cls(threads, results)

    def finish(self) -> tuple[CapturedLog, CapturedLog]:
        for thread in self.threads:
            thread.join()
        return (
            _capture_result(self.results, "stdout"),
            _capture_result(self.results, "stderr"),
        )


def write_log(path: Path, content: bytes, max_bytes: int) -> CapturedLog:
    return _write_chunks(path, (content,), max_bytes)


def _capture_thread(
    name: str,
    source: IO[bytes],
    path: Path,
    max_bytes: int,
    results: dict[str, CapturedLog | Exception],
) -> threading.Thread:
    def capture() -> None:
        try:
            chunks = iter(lambda: source.read(_READ_CHUNK_BYTES), b"")
            results[name] = _write_chunks(path, chunks, max_bytes)
        except Exception as error:  # pragma: no cover - defensive I/O boundary
            results[name] = error

    thread = threading.Thread(
        target=capture, name=f"harbor-{name}-capture", daemon=True
    )
    thread.start()
    return thread


def _write_chunks(path: Path, chunks: Iterable[bytes], max_bytes: int) -> CapturedLog:
    saved = 0
    truncated = False
    with path.open("xb") as output:
        for chunk in chunks:
            remaining = max_bytes - saved
            if remaining > 0:
                written = chunk[:remaining]
                output.write(written)
                saved += len(written)
            if len(chunk) > max(remaining, 0):
                truncated = True
    return CapturedLog(path=path.resolve(), saved_bytes=saved, truncated=truncated)


def _capture_result(
    results: dict[str, CapturedLog | Exception], name: str
) -> CapturedLog:
    result = results.get(name)
    if isinstance(result, CapturedLog):
        return result
    if isinstance(result, Exception):
        raise ProcessLogError(f"Failed to capture Harbor {name}") from result
    raise ProcessLogError(f"Harbor {name} capture did not finish")
