"""Pinned offline Codex installation inputs; never reads authentication files."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import tarfile
from pathlib import Path

VERSION = "0.153.0"
TARGET = "x86_64-unknown-linux-musl"
PACKAGE_VERSION = f"{VERSION}-linux-x64"
ARCHIVE_URL = f"https://registry.npmjs.org/@openai/codex/-/codex-{PACKAGE_VERSION}.tgz"
ARCHIVE_BYTES = 129_210_185
ARCHIVE_SHA512 = (
    "b0517e83ba75a3ab1954be8f1ddf494d8acfda3df16a8dd07aee409e072b0f96"
    "eb5ab09cfb0f627c124226e45233bdbc59f8235cc2fd3d03dd1cf69949e1c010"
)
_PREFIX = f"package/vendor/{TARGET}/"
_EXECUTABLES = (
    "bin/codex",
    "bin/codex-code-mode-host",
    "codex-path/rg",
    "codex-resources/bwrap",
    "codex-resources/zsh/bin/zsh",
)
_FILES = {
    "package/package.json",
    "package/README.md",
    _PREFIX + "codex-package.json",
    *(_PREFIX + name for name in _EXECUTABLES),
}
INSTALL_ROOT = "/opt/agentexam-codex"
INSTALL_PATH = (
    f"{INSTALL_ROOT}/bin:{INSTALL_ROOT}/codex-path:"
    "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
)
PREPARE_INSTALL_COMMAND = f"test ! -e {INSTALL_ROOT} && mkdir -p {INSTALL_ROOT}"
INSTALL_COMMAND = (
    f"chmod -R a+rX {INSTALL_ROOT} && chmod 0555 "
    f"{INSTALL_ROOT}/bin/codex {INSTALL_ROOT}/bin/codex-code-mode-host "
    f"{INSTALL_ROOT}/codex-path/rg {INSTALL_ROOT}/codex-resources/bwrap "
    f"{INSTALL_ROOT}/codex-resources/zsh/bin/zsh"
)


def prepare_codex_bundle(archive: Path, destination: Path) -> Path:
    """Validate the entire pinned archive before creating an exclusive destination."""
    if archive.is_symlink() or not archive.is_file():
        raise ValueError("CODEX_PACKAGE_INVALID")
    if archive.stat().st_size != ARCHIVE_BYTES:
        raise ValueError("CODEX_PACKAGE_SIZE_MISMATCH")
    with archive.open("rb") as source:
        if hashlib.file_digest(source, "sha512").hexdigest() != ARCHIVE_SHA512:
            raise ValueError("CODEX_PACKAGE_HASH_MISMATCH")
        source.seek(0)
        with tarfile.open(fileobj=source, mode="r:gz") as package:
            members = package.getmembers()
            if (
                len(members) != len(_FILES)
                or {member.name for member in members} != _FILES
                or any(not member.isfile() or member.size < 0 for member in members)
                or sum(member.size for member in members) > 350 * 1024 * 1024
            ):
                raise ValueError("CODEX_PACKAGE_LAYOUT_MISMATCH")
            _validate_identity(package)
            destination.mkdir(exist_ok=False)
            hashes = {}
            for member in members:
                # Exact member allowlist above excludes traversal, links and devices.
                target = destination / member.name
                target.parent.mkdir(parents=True, exist_ok=True)
                contents = package.extractfile(member)
                assert contents is not None
                with contents, target.open("xb") as output:
                    shutil.copyfileobj(contents, output, length=1024 * 1024)
                with target.open("rb") as extracted:
                    hashes[member.name] = hashlib.file_digest(
                        extracted, "sha256"
                    ).hexdigest()
            manifest = {
                "version": VERSION,
                "target": TARGET,
                "archive_url": ARCHIVE_URL,
                "archive_sha512": ARCHIVE_SHA512,
                "archive_bytes": ARCHIVE_BYTES,
                "files_sha256": hashes,
                "real_codex_ready": False,
            }
            with (destination / "installation-input.json").open("x") as output:
                json.dump(manifest, output, indent=2)
    return destination / "package/vendor" / TARGET


def validate_codex_bundle(root: Path) -> Path:
    """Recheck a prepared bundle immediately before it reaches Harbor."""
    if root.is_symlink() or not root.is_dir():
        raise ValueError("CODEX_BUNDLE_INVALID")
    resolved = root.resolve()
    manifest_path = resolved / "installation-input.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError("CODEX_BUNDLE_INVALID")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        hashes = manifest["files_sha256"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        raise ValueError("CODEX_BUNDLE_INVALID") from None
    identity = {
        "version": VERSION,
        "target": TARGET,
        "archive_url": ARCHIVE_URL,
        "archive_sha512": ARCHIVE_SHA512,
        "archive_bytes": ARCHIVE_BYTES,
        "real_codex_ready": False,
    }
    if (
        not isinstance(manifest, dict)
        or any(manifest.get(key) != value for key, value in identity.items())
        or set(manifest) != {*identity, "files_sha256"}
        or not isinstance(hashes, dict)
        or set(hashes) != _FILES
    ):
        raise ValueError("CODEX_BUNDLE_INVALID")
    for name, expected in hashes.items():
        target = resolved / name
        try:
            target.resolve().relative_to(resolved)
            if (
                not isinstance(expected, str)
                or not re.fullmatch(r"[a-f0-9]{64}", expected)
                or target.is_symlink()
                or not target.is_file()
            ):
                raise ValueError
            with target.open("rb") as source:
                actual = hashlib.file_digest(source, "sha256").hexdigest()
        except (OSError, ValueError):
            raise ValueError("CODEX_BUNDLE_INVALID") from None
        if actual != expected:
            raise ValueError("CODEX_BUNDLE_INVALID")
    return resolved / "package/vendor" / TARGET


def _validate_identity(package: tarfile.TarFile) -> None:
    documents = []
    for name in ("package/package.json", _PREFIX + "codex-package.json"):
        member = package.getmember(name)
        if member.size > 32 * 1024:
            raise ValueError("CODEX_PACKAGE_METADATA_TOO_LARGE")
        contents = package.extractfile(member)
        assert contents is not None
        with contents:
            document = json.load(contents)
        if not isinstance(document, dict):
            raise ValueError("CODEX_PACKAGE_IDENTITY_MISMATCH")
        documents.append(document)
    metadata, layout = documents
    expected = {
        "name": "@openai/codex",
        "version": PACKAGE_VERSION,
        "os": ["linux"],
        "cpu": ["x64"],
    }
    bundle = {
        "layoutVersion": 1,
        "version": VERSION,
        "target": TARGET,
        "variant": "codex",
        "entrypoint": "bin/codex",
        "resourcesDir": "codex-resources",
        "pathDir": "codex-path",
    }
    if any(metadata.get(k) != v for k, v in expected.items()) or layout != bundle:
        raise ValueError("CODEX_PACKAGE_IDENTITY_MISMATCH")
