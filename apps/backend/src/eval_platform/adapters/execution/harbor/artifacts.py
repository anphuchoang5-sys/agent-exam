from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

PATCH_WARNING_BYTES = 256 * 1024
PATCH_MAX_BYTES = 1024 * 1024
_HEX_64 = re.compile(r"[0-9a-f]{64}")


class PatchArtifactError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class ValidatedPatch:
    content: bytes
    size_bytes: int
    sha256: str
    is_empty: bool
    warnings: tuple[str, ...]


def validate_patch_artifact(artifact_dir: Path) -> ValidatedPatch:
    patch_path = artifact_dir / "model.patch"
    size = _regular_file_size(patch_path, "PATCH_MISSING")
    if size > PATCH_MAX_BYTES:
        raise PatchArtifactError(
            "PATCH_TOO_LARGE",
            f"Patch is {size} bytes; maximum is {PATCH_MAX_BYTES}",
        )
    content = patch_path.read_bytes()
    if len(content) != size:
        raise PatchArtifactError("PATCH_SIZE_CHANGED", "Patch changed while reading")
    actual_sha = hashlib.sha256(content).hexdigest()
    expected_sha = _metadata(artifact_dir / "patch.sha256")
    if not _HEX_64.fullmatch(expected_sha) or expected_sha != actual_sha:
        raise PatchArtifactError("PATCH_HASH_MISMATCH", "Patch SHA-256 is invalid")
    expected_size = _metadata(artifact_dir / "patch.bytes")
    if not expected_size.isdecimal() or int(expected_size) != size:
        raise PatchArtifactError("PATCH_SIZE_MISMATCH", "Patch byte count is invalid")
    binary_flag = _metadata(artifact_dir / "patch.binary")
    if binary_flag not in {"0", "1"}:
        raise PatchArtifactError("PATCH_METADATA_INVALID", "Binary flag is invalid")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PatchArtifactError(
            "BINARY_PATCH_NOT_ALLOWED", "Patch is not UTF-8 text"
        ) from exc
    binary_markers = ("GIT binary patch", "Binary files ")
    if binary_flag == "1" or "\x00" in text or any(x in text for x in binary_markers):
        raise PatchArtifactError(
            "BINARY_PATCH_NOT_ALLOWED", "Binary changes are not accepted"
        )
    if content and not text.startswith("diff --git "):
        raise PatchArtifactError("PATCH_FORMAT_INVALID", "Patch is not a Git diff")
    warnings = ("PATCH_SIZE_WARNING",) if size > PATCH_WARNING_BYTES else ()
    return ValidatedPatch(
        content=content,
        size_bytes=size,
        sha256=actual_sha,
        is_empty=size == 0,
        warnings=warnings,
    )


def _regular_file_size(path: Path, missing_code: str) -> int:
    if not path.is_file() or path.is_symlink():
        raise PatchArtifactError(
            missing_code, f"Required artifact is missing: {path.name}"
        )
    return path.stat().st_size


def _metadata(path: Path) -> str:
    size = _regular_file_size(path, "PATCH_METADATA_MISSING")
    if size > 256:
        raise PatchArtifactError(
            "PATCH_METADATA_INVALID", "Patch metadata is too large"
        )
    try:
        return path.read_text(encoding="ascii").strip()
    except UnicodeError as exc:
        raise PatchArtifactError(
            "PATCH_METADATA_INVALID", "Patch metadata is not ASCII"
        ) from exc
