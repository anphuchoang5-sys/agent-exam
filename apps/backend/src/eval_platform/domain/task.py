from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EvaluationTask:
    """The task view that may cross into an evaluated Agent environment."""

    dataset_id: str
    dataset_revision: str
    split: str
    instance_id: str
    repo: str
    base_commit: str
    problem_statement: str
    environment_image: str
    raw_record_sha256: str

    def __post_init__(self) -> None:
        required = {
            "dataset_id": self.dataset_id,
            "dataset_revision": self.dataset_revision,
            "split": self.split,
            "instance_id": self.instance_id,
            "repo": self.repo,
            "problem_statement": self.problem_statement,
            "environment_image": self.environment_image,
        }
        missing = [name for name, value in required.items() if not value.strip()]
        if missing:
            raise ValueError(f"Task fields must not be empty: {', '.join(missing)}")
        _require_sha("base_commit", self.base_commit)
        _require_sha("raw_record_sha256", self.raw_record_sha256)


@dataclass(frozen=True, slots=True)
class EvaluatorTaskData:
    """Hidden task data that must never be passed to an evaluated Agent."""

    instance_id: str
    version: str
    gold_patch: str
    test_patch: str
    fail_to_pass: tuple[str, ...]
    pass_to_pass: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TaskBundle:
    """Task Catalog result with deliberately separate public and hidden views."""

    public: EvaluationTask
    evaluator: EvaluatorTaskData
    raw_record_json: bytes

    def __post_init__(self) -> None:
        if self.public.instance_id != self.evaluator.instance_id:
            raise ValueError("Public and evaluator task identities do not match")


def _require_sha(name: str, value: str) -> None:
    if len(value) != 40 and name == "base_commit":
        raise ValueError(f"{name} must be a full 40-character Git commit")
    expected_length = 64 if name == "raw_record_sha256" else 40
    if len(value) != expected_length or any(c not in "0123456789abcdef" for c in value):
        raise ValueError(f"{name} must be lowercase hexadecimal")
