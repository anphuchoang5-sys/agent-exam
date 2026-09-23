"""S10 fake upstream/product proxy; private values exist only in container tmpfs."""

from __future__ import annotations

import json
import os
import ssl
import sys
import threading
from pathlib import Path

from providers.contract.support.fake_responses import FakeUpstream, RecordedRequest

from eval_platform.adapters.execution.provider_access.binding import TokenRegistry
from eval_platform.adapters.execution.provider_access.budget import (
    BudgetLedger,
    RunBudget,
)
from eval_platform.adapters.execution.provider_access.secrets import owner_only_verifier
from eval_platform.adapters.execution.provider_access.server import (
    ProviderProxyService,
    ProxyIdentity,
    RunRunner,
    build_server,
)
from eval_platform.adapters.execution.provider_access.server.contracts import (
    ProviderRejection,
)
from eval_platform.adapters.execution.provider_access.server.egress import open_stream
from eval_platform.domain.agent import (
    INTERNAL_TEST_MODEL,
    INTERNAL_TEST_PROVIDER,
    INTERNAL_TEST_UPSTREAM,
)

MODEL = INTERNAL_TEST_MODEL
PROXY_PORT, UPSTREAM_PORT = 8080, 443  # Fixed URL has no explicit upstream port.
PROFILE, TOKEN = Path("/tmp/provider-profile.json"), Path("/tmp/run-token")
CERT, KEY = "/opt/agentexam/tls/upstream.crt", "/opt/agentexam/tls/upstream.key"


def _exclusive_private(path: Path, value: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as output:
        output.write(value)


def _proxy() -> None:
    run_id = os.environ.get("AGENTEXAM_RUN_ID", "")
    if not run_id or not run_id.isascii() or len(run_id) > 64:
        raise SystemExit("PROVIDER_BINDING_IDENTITY_EMPTY")
    budget = RunBudget(200_000, 10_000, 1800)
    registry = TokenRegistry()
    binding = registry.issue(
        run_id=run_id,
        provider=INTERNAL_TEST_PROVIDER,
        model=MODEL,
        ttl_seconds=1800,
        budget=budget,
    )
    _exclusive_private(TOKEN, binding.token.encode("ascii"))
    _exclusive_private(
        PROFILE,
        json.dumps(
            {
                "version": 1,
                "profiles": {
                    "t05-fake": {
                        "provider": INTERNAL_TEST_PROVIDER,
                        "model": MODEL,
                        "upstream_base_url": INTERNAL_TEST_UPSTREAM,
                        "secret": "FAKE-T05-UPSTREAM-ONLY",
                    }
                },
            }
        ).encode("utf-8"),
    )
    ledger = BudgetLedger(budget, consumed_input_tokens=0, consumed_output_tokens=0)
    identity = ProxyIdentity(
        run_id, frozenset({"function", "namespace"}), PROFILE, "t05-fake"
    )
    service = _DiagnosticProxyService(
        identity,
        registry=registry,
        ledger=ledger,
        verify_access=owner_only_verifier,
    )
    server = build_server(
        service,
        RunRunner(ledger, sender=open_stream),
        host="0.0.0.0",
        port=PROXY_PORT,
    )
    print("proxy-ready", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        registry.revoke_run(run_id)
        TOKEN.unlink(missing_ok=True)
        PROFILE.unlink(missing_ok=True)


class _DiagnosticProxyService(ProviderProxyService):
    """Print rejection structure only; never print body or header values."""

    def decide(self, *, method, path, raw_body, headers):
        try:
            return super().decide(
                method=method, path=path, raw_body=raw_body, headers=headers
            )
        except ProviderRejection as error:
            try:
                body = json.loads(raw_body)
            except (UnicodeDecodeError, json.JSONDecodeError):
                body = None
            tools = body.get("tools") if isinstance(body, dict) else None
            tool_types = sorted(
                item.get("type", "") for item in tools or [] if isinstance(item, dict)
            )
            cache_key = body.get("prompt_cache_key") if isinstance(body, dict) else None
            controls = {
                key: body.get(key)
                for key in (
                    "include",
                    "parallel_tool_calls",
                    "reasoning",
                    "store",
                    "tool_choice",
                )
                if isinstance(body, dict) and key in body
            }
            metadata = body.get("client_metadata") if isinstance(body, dict) else None
            controls["client_metadata"] = {
                "keys": sorted(metadata) if isinstance(metadata, dict) else [],
                "types": {key: type(value).__name__ for key, value in metadata.items()}
                if isinstance(metadata, dict)
                else {},
            }
            controls["prompt_cache_key"] = {
                "type": type(cache_key).__name__,
                "length": len(cache_key) if isinstance(cache_key, str) else None,
            }
            print(
                json.dumps(
                    {
                        "proxy_refusal": error.internal_code,
                        "method": method,
                        "path": path.split("?", 1)[0],
                        "body_keys": sorted(body) if isinstance(body, dict) else [],
                        "controls": controls,
                        "tool_types": tool_types,
                        "header_names": sorted(str(key) for key in headers),
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
            raise


def _upstream() -> None:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(CERT, KEY)

    def record(request: RecordedRequest) -> None:
        # The upstream's own log proves which network-side address connected.
        print(
            json.dumps(
                {
                    "peer": request.peer_address,
                    "method": request.method,
                    "path": request.path,
                    "model": (request.body or {}).get("model"),
                    "header_names": request.header_names,
                },
                sort_keys=True,
            ),
            flush=True,
        )

    with FakeUpstream(
        port=UPSTREAM_PORT,
        host="0.0.0.0",
        tls_context=context,
        on_request=record,
    ):
        print("fake-upstream-ready", flush=True)
        threading.Event().wait()


if __name__ == "__main__":
    if sys.argv[1:] == ["proxy"]:
        _proxy()
    elif sys.argv[1:] == ["fake-upstream"]:
        _upstream()
    else:
        raise SystemExit("T05_FIXTURE_ROLE_INVALID")
