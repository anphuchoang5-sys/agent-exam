"""Request admission, reservation, and trusted outbound normalization."""

import json
from collections.abc import Iterator

import pytest
from providers.contract.support.fake_responses import FakeUpstream
from providers.lifecycle.support import (
    CLIENT_TOKEN,
    FAKE_SECRET,
    RUN_ID,
    make_harness,
    permissions_too_wide,
    profile_document,
    request_body,
)

from eval_platform.adapters.execution.provider_access.budget import (
    FRAMING_ALLOWANCE_TOKENS,
)
from eval_platform.adapters.execution.provider_access.server import ProviderRejection
from eval_platform.domain.agent import INTERNAL_TEST_UPSTREAM


@pytest.fixture
def upstream() -> Iterator[FakeUpstream]:
    with FakeUpstream() as fake:
        yield fake


def test_the_run_remainder_is_the_output_ceiling(tmp_path):
    harness = make_harness(tmp_path, consumed=(0, 31_000))
    assert harness.ledger.remaining_output_tokens == 1_000
    with pytest.raises(ProviderRejection, match="REQUEST_MAX_OUTPUT_TOKENS_EXCEEDED"):
        harness.decide(body=request_body(max_output_tokens=1_001))
    assert harness.ledger.remaining_output_tokens == 1_000
    spent = make_harness(tmp_path, consumed=(0, 32_000))
    with pytest.raises(ProviderRejection, match="BUDGET_OUTPUT_EXCEEDED"):
        spent.decide()


def test_an_unknown_or_mismatched_profile_is_refused(tmp_path):
    harness = make_harness(tmp_path)
    assert harness.decide().binding.run_id == RUN_ID
    with pytest.raises(ProviderRejection, match="PRIVATE_PROFILE_NOT_FOUND"):
        make_harness(tmp_path, profile_id="not-in-the-file").decide()
    for entry in (
        {"model": "kimi-k3"},
        {"provider": "deepseek"},
        {"upstream_base_url": "https://api.deepseek.com"},
        {"secret": "  "},
    ):
        with pytest.raises(ProviderRejection):
            make_harness(tmp_path, document=profile_document(**entry)).decide()


def test_a_refusal_never_carries_the_path_the_secret_or_the_token(tmp_path):
    harness = make_harness(tmp_path)
    refusals = []
    for attempt in (
        lambda: harness.decide(authorization=False),
        lambda: make_harness(
            tmp_path / "wide", verify_access=permissions_too_wide
        ).decide(),
        lambda: harness.decide(body=request_body(tools=[{"type": "web_search"}])),
    ):
        with pytest.raises(ProviderRejection) as error:
            attempt()
        refusals.append(error.value)
    for error in refusals:
        text = f"{error.internal_code} {error.failure_code} {error.failure_summary}"
        assert harness.private.name not in text
        assert str(harness.private.parent) not in text
        assert FAKE_SECRET not in text and CLIENT_TOKEN not in text


def test_a_refusal_keeps_the_ledger_untouched(tmp_path, upstream):
    harness = make_harness(tmp_path)
    for attempt in (
        lambda: harness.decide(method="GET"),
        lambda: harness.decide(path="/v1/responses"),
        lambda: harness.decide(authorization=False),
        lambda: harness.decide(body=request_body(model="kimi-k3")),
        lambda: harness.decide(body=request_body(tools=[{"type": "web_search"}])),
        lambda: harness.decide(headers={"X-Forwarded-Host": "evil.example.com"}),
    ):
        with pytest.raises(ProviderRejection):
            attempt()
    assert upstream.request_count == 0
    assert harness.ledger.remaining_output_tokens == 32_000


def test_admission_holds_the_input_bound_and_the_requested_output(tmp_path):
    harness = make_harness(tmp_path)
    raw = request_body(max_output_tokens=1_000)
    admission = harness.decide(body=raw)
    compact = json.dumps(
        json.loads(raw), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    assert admission.reservation.input_tokens == len(compact) + FRAMING_ALLOWANCE_TOKENS
    assert admission.reservation.max_output_tokens == 1_000
    assert harness.ledger.remaining_output_tokens == 31_000


def test_an_unstated_output_ceiling_holds_the_whole_remainder(tmp_path):
    harness = make_harness(tmp_path, consumed=(0, 8_000))
    admission = harness.decide(body=request_body())
    assert admission.reservation.max_output_tokens == 24_000
    assert harness.ledger.remaining_output_tokens == 0


def test_admission_swaps_the_client_credential_for_the_trusted_one(tmp_path):
    harness = make_harness(tmp_path)
    admission = harness.decide(headers={"Content-Type": "application/json"})
    sent = dict(admission.outbound.send_headers())
    assert sent.pop("Authorization") == f"Bearer {FAKE_SECRET}"
    assert "authorization" not in {name.lower() for name in sent}
    assert CLIENT_TOKEN not in json.dumps(sent)
    assert admission.outbound.url == f"{INTERNAL_TEST_UPSTREAM}/responses"
    assert admission.outbound.max_attempts == 1
    assert admission.outbound.follow_redirects is False


def test_the_destination_is_never_taken_from_the_request(tmp_path):
    harness = make_harness(tmp_path)
    admission = harness.decide(headers={"Host": "evil.example.com"})
    assert admission.outbound.url == f"{INTERNAL_TEST_UPSTREAM}/responses"
    assert "evil.example.com" not in admission.outbound.url
    assert "host" not in {name.lower() for name in admission.outbound.send_headers()}


def test_a_routing_header_is_refused_where_it_used_to_be_forwarded(tmp_path):
    harness = make_harness(tmp_path)
    for name in ("X-Forwarded-Host", "Forwarded", "Location", "X-Trace"):
        with pytest.raises(ProviderRejection) as refusal:
            harness.decide(headers={name: "evil.example.com"})
        assert refusal.value.internal_code == "REQUEST_HEADER_NOT_ALLOWED"
        assert refusal.value.failure_code == "PROVIDER_REQUEST_REJECTED"


def test_no_secret_reaches_a_representation_or_a_client_header(tmp_path):
    harness = make_harness(tmp_path)
    admission = harness.decide()
    for text in (repr(admission), str(admission), repr(admission.outbound)):
        assert FAKE_SECRET not in text
        assert CLIENT_TOKEN not in text
