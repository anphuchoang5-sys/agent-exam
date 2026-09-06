from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from eval_platform.domain.result import DeterministicResult
from eval_platform.domain.task import EvaluatorTaskData


@dataclass(frozen=True, slots=True)
class EvaluationRequest:
    run_id: str
    task: EvaluatorTaskData
    model_patch: bytes
    model_name_or_path: str


class PatchEvaluator(Protocol):
    def evaluate(self, request: EvaluationRequest) -> DeterministicResult:
        """Apply a validated patch in a clean fixed-Fork evaluation environment."""
