from dataclasses import asdict
from datetime import timedelta
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from jobs.artifacts.cleanup_support import NOW, OWNER, expired
from jobs.execution.support.fakes import MemoryArtifacts

from eval_platform.adapters.persistence.jobs.retention.records import (
    mark_artifact_deleted,
)
from eval_platform.adapters.persistence.jobs.retention.state import completed
from eval_platform.domain.jobs.execution import ArtifactDeletionIntent
from eval_platform.domain.jobs.models import JobUnavailable


def completed_deletion(uuid_type=UUID):
    item = expired(MemoryArtifacts())
    intent = ArtifactDeletionIntent(
        item, str(uuid4()), OWNER.user_id, "raw_retention_expired", NOW, NOW
    )
    row = {
        **asdict(item.reference),
        "run_id": uuid_type(item.run_id),
        "deletion_intent_id": uuid_type(intent.intent_id),
        "deletion_intent_by": uuid_type(intent.actor_user_id),
        "deletion_intent_reason": intent.reason,
        "deletion_verified_at": intent.verified_at,
        "deleted_at": NOW,
        "deleted_by": uuid_type(intent.actor_user_id),
        "deletion_reason": intent.reason,
    }
    return intent, row


def zero_row_update_then_stored(row):
    rows = iter((None, row))
    return SimpleNamespace(
        execute=lambda *_args: SimpleNamespace(fetchone=lambda: next(rows))
    )


@pytest.mark.parametrize("uuid_type", [UUID, str])
def test_completed_audit_accepts_database_uuid_and_string_rows(uuid_type):
    intent, row = completed_deletion(uuid_type)

    assert completed(row, intent) is True
    mark_artifact_deleted(zero_row_update_then_stored(row), intent, NOW)
    mark_artifact_deleted(zero_row_update_then_stored(row), intent, NOW)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("run_id", UUID(int=1)),
        ("object_key", "runs/wrong-owner/raw/key"),
        ("sha256", "0" * 64),
        ("size_bytes", 999),
        ("original_size_bytes", 999),
        ("expires_at", NOW),
        ("deletion_intent_id", UUID(int=2)),
        ("deletion_intent_id", None),
        ("deletion_intent_by", UUID(int=3)),
        ("deletion_intent_reason", "unexpected"),
        ("deletion_verified_at", None),
        ("deletion_verified_at", NOW - timedelta(seconds=1)),
        ("deleted_at", None),
        ("deleted_by", UUID(int=4)),
        ("deletion_reason", "unexpected"),
    ],
)
def test_completed_audit_rejects_changed_identity_or_missing_confirmation(field, value):
    intent, row = completed_deletion()
    row[field] = value

    assert completed(row, intent) is False
    with pytest.raises(JobUnavailable):
        mark_artifact_deleted(zero_row_update_then_stored(row), intent, NOW)


def test_completed_audit_rejects_missing_row_and_missing_identity_field():
    intent, row = completed_deletion()
    del row["deletion_intent_id"]
    assert completed(row, intent) is False
    with pytest.raises(JobUnavailable):
        mark_artifact_deleted(zero_row_update_then_stored(row), intent, NOW)
    with pytest.raises(JobUnavailable):
        mark_artifact_deleted(zero_row_update_then_stored(None), intent, NOW)
