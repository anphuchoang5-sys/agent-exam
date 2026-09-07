"""Internal known-value redaction; not detection of unknown or encoded secrets."""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator


class Redactor:
    """Stateless per-stream filtering; values are never included in repr or errors."""

    def __init__(self, values: tuple[bytes, ...]) -> None:
        if not isinstance(values, tuple) or any(
            not isinstance(value, bytes) or not value for value in values
        ):
            raise ValueError("Invalid redaction values")
        ordered = sorted(set(values), key=lambda value: (-len(value), value))
        self._pattern = (
            re.compile(b"|".join(re.escape(value) for value in ordered))
            if ordered
            else None
        )
        self._width = max(map(len, ordered), default=1)

    def filter(self, chunks: Iterable[bytes]) -> Iterator[bytes]:
        if self._pattern is None:
            yield from chunks
            return
        pending = b""
        for chunk in chunks:
            pending += chunk
            limit = max(0, len(pending) - self._width + 1)
            cursor = 0
            for match in self._pattern.finditer(pending):
                if match.start() >= limit:
                    break
                yield pending[cursor : match.start()]
                yield b"[REDACTED]"
                cursor = match.end()
            cutoff = max(cursor, limit)
            yield pending[cursor:cutoff]
            pending = pending[cutoff:]
        yield self._pattern.sub(b"[REDACTED]", pending)
