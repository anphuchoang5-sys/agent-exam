from __future__ import annotations

import os
import threading
import time
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
    paths: tuple[Path, Path]
    max_bytes: int

    @classmethod
    def start(
        cls,
        stdout: IO[bytes],
        stderr: IO[bytes],
        root: Path,
        max_bytes: int,
    ) -> LogCaptureSession:
        results: dict[str, CapturedLog | Exception] = {}
        paths = (root / "harbor.stdout.log", root / "harbor.stderr.log")
        threads = (
            _capture_thread("stdout", stdout, paths[0], max_bytes, results),
            _capture_thread("stderr", stderr, paths[1], max_bytes, results),
        )
        return cls(threads, results, paths, max_bytes)

    def finish(
        self, *, timeout_sec: float
    ) -> tuple[CapturedLog, CapturedLog, tuple[str, ...]]:
        if timeout_sec <= 0:
            raise ValueError("Log capture timeout must be positive")
        deadline = time.monotonic() + timeout_sec
        for thread in self.threads:
            thread.join(timeout=max(0.0, deadline - time.monotonic()))
        incomplete = tuple(
            name
            for name, thread in zip(("stdout", "stderr"), self.threads, strict=True)
            if thread.is_alive()
        )
        for thread in self.threads:
            if thread.is_alive():
                _cancel_windows_read(thread)
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=0.5)
        return (
            self._result("stdout", 0, incomplete),
            self._result("stderr", 1, incomplete),
            incomplete,
        )

    def _result(
        self, name: str, index: int, incomplete: tuple[str, ...]
    ) -> CapturedLog:
        if name not in incomplete:
            return _capture_result(self.results, name)
        path = self.paths[index].resolve()
        saved = path.stat().st_size if path.is_file() else 0
        return CapturedLog(
            path=path,
            saved_bytes=saved,
            truncated=self.max_bytes > 0 and saved >= self.max_bytes,
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


def _cancel_windows_read(thread: threading.Thread) -> None:
    if os.name != "nt" or thread.native_id is None:
        return
    import ctypes

    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenThread(0x0001, False, thread.native_id)
    if handle:
        try:
            kernel32.CancelSynchronousIo(handle)
        finally:
            kernel32.CloseHandle(handle)
