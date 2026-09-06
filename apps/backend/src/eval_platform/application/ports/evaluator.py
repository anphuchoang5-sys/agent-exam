from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from eval_platform.domain.result import ArtifactRef, DeterministicResult
from eval_platform.domain.task import EvaluatorTaskData


@dataclass(frozen=True, slots=True)
class EvaluationRequest:
    run_id: str
    task: EvaluatorTaskData
    model_patch: bytes
    model_name_or_path: str


class EvaluationError(RuntimeError):
    """The harness could not establish a trustworthy deterministic result."""

    def __init__(
        self, code: str, message: str, evidence_refs: tuple[ArtifactRef, ...] = ()
    ):
        super().__init__(message)
        self.code = code
        self.evidence_refs = evidence_refs


class PatchEvaluator(Protocol):
    def evaluate(self, request: EvaluationRequest) -> DeterministicResult:
        """Apply a validated patch in a clean fixed-Fork evaluation environment."""
