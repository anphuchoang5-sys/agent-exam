"""Select a frozen Run's owner-local execution binding before Harbor starts.

The provider proxy path requires an explicit S10 backend factory with an
isolated network and short-lived token. Never fall back to ChatGPT for it.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from eval_platform.application.ports.execution import (
    ExecutionBackend,
    ExecutionJobRequest,
    ExecutionProgressObserver,
)
from eval_platform.domain.agent import (
    CHATGPT_CREDENTIAL_ID,
    CHATGPT_IDENTITY,
    CONTROLLED_IDENTITIES,
    INTERNAL_TEST_CREDENTIAL_ID,
    INTERNAL_TEST_IDENTITY,
    AgentConfiguration,
)
from eval_platform.domain.result import ExecutionTrialResult

CHATGPT_NETWORK_HOSTS = ("auth.openai.com", "chatgpt.com")


@dataclass(frozen=True, slots=True)
class WorkerRunBinding:
    route: Literal["chatgpt", "provider_proxy"]
    credential_configuration_id: str
    network_hosts: tuple[str, ...]
    needs_codex_archive: bool
    needs_chatgpt_auth: bool


def select_run_binding(agent: AgentConfiguration) -> WorkerRunBinding:
    """Match the controlled identity *and* its non-secret credential reference."""
    identity = (agent.model_provider, agent.authentication_type)
    if identity not in CONTROLLED_IDENTITIES:
        raise ValueError("WORKER_AGENT_IDENTITY_INVALID")
    if identity == CHATGPT_IDENTITY:
        if agent.credential_configuration_id != CHATGPT_CREDENTIAL_ID:
            raise ValueError("WORKER_CREDENTIAL_BINDING_INVALID")
        return WorkerRunBinding(
            "chatgpt", CHATGPT_CREDENTIAL_ID, CHATGPT_NETWORK_HOSTS, True, True
        )
    if identity == INTERNAL_TEST_IDENTITY:
        if agent.credential_configuration_id != INTERNAL_TEST_CREDENTIAL_ID:
            raise ValueError("WORKER_CREDENTIAL_BINDING_INVALID")
        return WorkerRunBinding(
            "provider_proxy", INTERNAL_TEST_CREDENTIAL_ID, (), True, False
        )
    raise ValueError("WORKER_AGENT_IDENTITY_INVALID")


@dataclass(slots=True)
class RunBoundExecutionBackend:
    """Keep the existing backend port; route one controlled proxy Run only."""

    chatgpt_backend: Callable[[], ExecutionBackend]
    provider_backend: Callable[[], ExecutionBackend] | None = None

    def execute(
        self,
        request: ExecutionJobRequest,
        progress: ExecutionProgressObserver | None = None,
    ) -> tuple[ExecutionTrialResult, ...]:
        bindings = tuple(select_run_binding(run.agent) for run in request.runs)
        if any(binding.route == "provider_proxy" for binding in bindings):
            if (
                len(bindings) != 1
                or bindings[0].route != "provider_proxy"
                or self.provider_backend is None
            ):
                raise RuntimeError("PROVIDER_RUNTIME_NOT_READY")
            return self.provider_backend().execute(request, progress)
        return self.chatgpt_backend().execute(request, progress)
