"""Reject outside the fixed CLI request shape before any egress.
Private CLI metadata is validated then stripped; no credential IO occurs here.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any
from uuid import UUID

from eval_platform.adapters.execution.provider_access.failures import (
    ProviderAccessError,
)

PATH = "/responses"
METHOD = "POST"
ALLOWED_FIELDS = frozenset(
    {
        "model",
        "stream",
        "input",
        "tools",
        "max_output_tokens",
        "instructions",
        "reasoning",
        "client_metadata",
        "include",
        "parallel_tool_calls",
        "prompt_cache_key",
        "store",
        "tool_choice",
    }
)
PRIVATE_CONTROL_FIELDS = frozenset({"client_metadata", "prompt_cache_key"})
REQUIRED_FIELDS = frozenset({"model", "input"})
CLIENT_AUTH_HEADERS = frozenset(
    {"authorization", "proxy-authorization", "x-api-key", "api-key"}
)
IGNORED_CLIENT_HEADERS = frozenset(
    {
        "content-length",
        "content-type",
        "originator",
        "session-id",
        "thread-id",
        "x-client-request-id",
        "x-codex-beta-features",
        "x-codex-turn-metadata",
        "x-codex-window-id",
    }
)
FORWARDED_CLIENT_HEADERS = frozenset({"accept", "accept-encoding", "user-agent"})
_METADATA_FIELDS = frozenset(
    {
        "root_turn_id",
        "session_id",
        "thread_id",
        "turn_id",
        "x-codex-installation-id",
        "x-codex-turn-metadata",
        "x-codex-window-id",
    }
)


@dataclass(frozen=True, slots=True)
class RequestPolicy:
    """Bound model, output ceiling and the only tools this run may request."""

    model: str
    max_output_tokens: int
    allowed_tools: frozenset[str]

    def __post_init__(self) -> None:
        if not self.model.strip():
            raise ProviderAccessError("REQUEST_POLICY_MODEL_EMPTY")
        if self.max_output_tokens <= 0:
            raise ProviderAccessError("REQUEST_POLICY_CEILING_INVALID")
        if not isinstance(self.allowed_tools, frozenset):
            raise ProviderAccessError("REQUEST_POLICY_TOOLS_NOT_IMMUTABLE")


def check_request(
    policy: RequestPolicy,
    *,
    method: str,
    path: str,
    body: Any,
) -> Mapping[str, Any]:
    """Return the whitelisted body, or raise a fixed code before any egress."""

    if method != METHOD:
        raise ProviderAccessError("REQUEST_METHOD_NOT_ALLOWED")
    if path != PATH:
        raise ProviderAccessError("REQUEST_PATH_NOT_ALLOWED")
    if not isinstance(body, Mapping):
        raise ProviderAccessError("REQUEST_BODY_NOT_OBJECT")
    keys = {key for key in body if isinstance(key, str)}
    if len(keys) != len(body):
        raise ProviderAccessError("REQUEST_BODY_NOT_OBJECT")
    if keys - ALLOWED_FIELDS:
        raise ProviderAccessError("REQUEST_UNKNOWN_FIELD")
    if REQUIRED_FIELDS - keys:
        raise ProviderAccessError("REQUEST_REQUIRED_FIELD_MISSING")
    if body["model"] != policy.model:
        raise ProviderAccessError("REQUEST_MODEL_MISMATCH")
    if body.get("stream") is not True:
        raise ProviderAccessError("REQUEST_STREAM_REQUIRED")
    _check_input(body["input"])
    _check_control_fields(body)
    _check_output_ceiling(policy, body.get("max_output_tokens"))
    _check_tools(policy, body.get("tools"))
    return MappingProxyType(
        {key: body[key] for key in sorted(keys - PRIVATE_CONTROL_FIELDS)}
    )


def strip_client_auth(headers: Mapping[str, str]) -> Mapping[str, str]:
    """Strip credentials and reject every non-approved client header."""

    forwarded: dict[str, str] = {}
    for key, value in headers.items():
        normalized = key.strip().lower()
        if normalized in CLIENT_AUTH_HEADERS | IGNORED_CLIENT_HEADERS:
            continue
        if normalized not in FORWARDED_CLIENT_HEADERS:
            raise ProviderAccessError("REQUEST_HEADER_NOT_ALLOWED")
        forwarded[key] = value
    return MappingProxyType(forwarded)


def _check_input(value: Any) -> None:
    if isinstance(value, str):
        if not value.strip():
            raise ProviderAccessError("REQUEST_INPUT_EMPTY")
        return
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray)):
        raise ProviderAccessError("REQUEST_INPUT_INVALID")
    if not value:
        raise ProviderAccessError("REQUEST_INPUT_EMPTY")


def _check_output_ceiling(policy: RequestPolicy, value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ProviderAccessError("REQUEST_MAX_OUTPUT_TOKENS_INVALID")
    if value > policy.max_output_tokens:
        raise ProviderAccessError("REQUEST_MAX_OUTPUT_TOKENS_EXCEEDED")


def _check_control_fields(body: Mapping[str, Any]) -> None:
    expected = {
        "include": ["reasoning.encrypted_content"],
        "parallel_tool_calls": True,
        "store": False,
        "tool_choice": "auto",
    }
    if any(key in body and body[key] != value for key, value in expected.items()):
        raise ProviderAccessError("REQUEST_CONTROL_FIELD_INVALID")
    reasoning = body.get("reasoning")
    if reasoning is not None and (
        not isinstance(reasoning, Mapping)
        or set(reasoning) != {"effort", "summary"}
        or reasoning.get("effort") not in {"low", "medium", "high", "xhigh"}
        or reasoning.get("summary") != "auto"
    ):
        raise ProviderAccessError("REQUEST_CONTROL_FIELD_INVALID")
    metadata = body.get("client_metadata")
    if metadata is not None and (
        not isinstance(metadata, Mapping)
        or set(metadata) != _METADATA_FIELDS
        or any(
            not isinstance(value, str) or not value or len(value) > 4096
            for value in metadata.values()
        )
    ):
        raise ProviderAccessError("REQUEST_CONTROL_FIELD_INVALID")
    cache_key = body.get("prompt_cache_key")
    if cache_key is not None:
        try:
            canonical = str(UUID(cache_key))
        except (AttributeError, TypeError, ValueError):
            raise ProviderAccessError("REQUEST_CONTROL_FIELD_INVALID") from None
        if cache_key != canonical:
            raise ProviderAccessError("REQUEST_CONTROL_FIELD_INVALID")


def _check_tools(policy: RequestPolicy, value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ProviderAccessError("REQUEST_TOOLS_INVALID")
    for entry in value:
        if not isinstance(entry, Mapping) or not isinstance(entry.get("type"), str):
            raise ProviderAccessError("REQUEST_TOOLS_INVALID")
        if entry["type"] not in policy.allowed_tools:
            raise ProviderAccessError("REQUEST_TOOL_NOT_ALLOWED")
