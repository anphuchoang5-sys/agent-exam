from __future__ import annotations

import pytest

from eval_platform.adapters.execution.harbor.result_values import (
    exception_reason,
    resource_summary,
    usage_summary,
)
from eval_platform.domain.result import TerminationReason


@pytest.mark.parametrize(
    ("exception_type", "expected"),
    [
        ("AgentAuthenticationError", TerminationReason.AGENT_UNAVAILABLE),
        ("AgentTimeoutError", TerminationReason.TIMED_OUT),
        ("DockerError", TerminationReason.SANDBOX_FAILED),
        ("NetworkPolicyError", TerminationReason.POLICY_FAILED),
        ("RuntimeError", TerminationReason.AGENT_FAILED),
    ],
)
def test_maps_harbor_exception_types(
    exception_type: str,
    expected: TerminationReason,
) -> None:
    assert exception_reason(exception_type) is expected


def test_invalid_usage_is_unknown_with_warning() -> None:
    usage, warning = usage_summary({"n_input_tokens": "unknown"})

    assert usage is None
    assert warning == "HARBOR_USAGE_INVALID"


def test_valid_usage_preserves_reported_values() -> None:
    usage, warning = usage_summary(
        {
            "n_input_tokens": 10,
            "n_cache_tokens": 2,
            "n_output_tokens": 3,
            "cost_usd": 1,
        }
    )

    assert warning is None
    assert usage is not None
    assert (
        usage.n_input_tokens,
        usage.n_cache_tokens,
        usage.n_output_tokens,
        usage.cost_usd,
    ) == (10, 2, 3, 1.0)


def test_invalid_timing_is_unknown_with_warning() -> None:
    resources, warning = resource_summary(
        {"started_at": "invalid", "finished_at": "2026-09-06T04:14:52Z"}
    )

    assert resources is None
    assert warning == "HARBOR_TIMING_INVALID"


def test_valid_timing_produces_wall_time() -> None:
    resources, warning = resource_summary(
        {
            "started_at": "2026-09-06T04:14:35Z",
            "finished_at": "2026-09-06T04:14:52Z",
        }
    )

    assert warning is None
    assert resources is not None and resources.wall_time_sec == 17
