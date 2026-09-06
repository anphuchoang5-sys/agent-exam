from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from eval_platform.adapters.execution.harbor.artifacts import (
    PATCH_MAX_BYTES,
    PATCH_WARNING_BYTES,
    PatchArtifactError,
    validate_patch_artifact,
)


def _write_artifact(
    root: Path,
    content: bytes,
    *,
    sha256: str | None = None,
    size: int | None = None,
    binary: str = "0",
) -> None:
    root.mkdir()
    (root / "model.patch").write_bytes(content)
    digest = sha256 or hashlib.sha256(content).hexdigest()
    (root / "patch.sha256").write_text(digest + "\n", encoding="ascii")
    (root / "patch.bytes").write_text(
        f"{len(content) if size is None else size}\n", encoding="ascii"
    )
    (root / "patch.binary").write_text(binary + "\n", encoding="ascii")


def test_empty_patch_is_a_valid_completed_output(tmp_path: Path) -> None:
    _write_artifact(tmp_path / "artifact", b"")

    result = validate_patch_artifact(tmp_path / "artifact")

    assert result.is_empty is True
    assert result.sha256 == hashlib.sha256(b"").hexdigest()
    assert result.warnings == ()


def test_normal_text_git_patch_is_preserved_byte_for_byte(tmp_path: Path) -> None:
    patch = b"diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -1 +1 @@\n-a\n+b\n"
    _write_artifact(tmp_path / "artifact", patch)

    result = validate_patch_artifact(tmp_path / "artifact")

    assert result.content == patch
    assert result.size_bytes == len(patch)
    assert result.is_empty is False


def test_patch_above_warning_threshold_is_not_truncated(tmp_path: Path) -> None:
    patch = b"diff --git a/a b/a\n" + b"+" * PATCH_WARNING_BYTES
    _write_artifact(tmp_path / "artifact", patch)

    result = validate_patch_artifact(tmp_path / "artifact")

    assert result.content == patch
    assert result.warnings == ("PATCH_SIZE_WARNING",)


def test_patch_above_hard_limit_is_rejected(tmp_path: Path) -> None:
    patch = b"diff --git a/a b/a\n" + b"+" * PATCH_MAX_BYTES
    _write_artifact(tmp_path / "artifact", patch)

    with pytest.raises(PatchArtifactError) as caught:
        validate_patch_artifact(tmp_path / "artifact")

    assert caught.value.code == "PATCH_TOO_LARGE"


@pytest.mark.parametrize(
    ("patch", "binary"),
    [
        (b"diff --git a/a b/a\nBinary files a/a and b/a differ\n", "0"),
        (b"diff --git a/a b/a\n", "1"),
        (b"diff --git a/a b/a\n\x00", "0"),
    ],
)
def test_binary_patch_is_rejected(tmp_path: Path, patch: bytes, binary: str) -> None:
    _write_artifact(tmp_path / "artifact", patch, binary=binary)

    with pytest.raises(PatchArtifactError) as caught:
        validate_patch_artifact(tmp_path / "artifact")

    assert caught.value.code == "BINARY_PATCH_NOT_ALLOWED"


def test_hash_mismatch_is_rejected(tmp_path: Path) -> None:
    _write_artifact(tmp_path / "artifact", b"", sha256="0" * 64)

    with pytest.raises(PatchArtifactError) as caught:
        validate_patch_artifact(tmp_path / "artifact")

    assert caught.value.code == "PATCH_HASH_MISMATCH"


def test_natural_language_is_not_accepted_as_a_patch(tmp_path: Path) -> None:
    _write_artifact(tmp_path / "artifact", b"I fixed the issue.")

    with pytest.raises(PatchArtifactError) as caught:
        validate_patch_artifact(tmp_path / "artifact")

    assert caught.value.code == "PATCH_FORMAT_INVALID"
