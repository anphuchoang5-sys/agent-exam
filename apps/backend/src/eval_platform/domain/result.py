from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class TerminationReason(StrEnum):
    COMPLETED = "completed"
    AGENT_UNAVAILABLE = "agent_unavailable"
    AGENT_FAILED = "agent_failed"
    TIMED_OUT = "timed_out"
    SANDBOX_FAILED = "sandbox_failed"
    POLICY_FAILED = "policy_failed"
    PATCH_EXTRACTION_FAILED = "patch_extraction_failed"
    PATCH_TOO_LARGE = "PATCH_TOO_LARGE"
    BINARY_PATCH_NOT_ALLOWED = "BINARY_PATCH_NOT_ALLOWED"
    BACKEND_PROTOCOL_ERROR = "backend_protocol_error"
    INFRASTRUCTURE_INTERRUPTED = "INFRASTRUCTURE_INTERRUPTED"


@dataclass(frozen=True, slots=True)
class ArtifactRef:
    object_key: str
    artifact_type: str
    size_bytes: int
    sha256: str
    content_type: str
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.object_key or not self.artifact_type:
            raise ValueError("Artifact identity must not be empty")
        if self.size_bytes < 0:
            raise ValueError("Artifact size must not be negative")
        if len(self.sha256) != 64 or any(
            char not in "0123456789abcdef" for char in self.sha256
        ):
            raise ValueError("Artifact SHA-256 must be lowercase hexadecimal")


@dataclass(frozen=True, slots=True)
class ExecutionTrialResult:
    run_id: str
    backend_job_ref: str
    backend_trial_ref: str
    termination_reason: TerminationReason
    patch_ref: ArtifactRef | None
    trajectory_ref: ArtifactRef | None
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if (
            self.termination_reason is TerminationReason.COMPLETED
            and self.patch_ref is None
        ):
            raise ValueError("A completed execution must include a patch artifact")


@dataclass(frozen=True, slots=True)
class DeterministicResult:
    run_id: str
    resolved: bool
    patch_applied: bool
    report_ref: ArtifactRef
    log_refs: tuple[ArtifactRef, ...] = ()
