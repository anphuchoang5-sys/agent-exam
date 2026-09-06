from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any


@dataclass(frozen=True, slots=True)
class AgentConfiguration:
    configuration_id: str
    agent_name: str
    agent_version: str
    model_provider: str
    model_name: str
    authentication_type: str
    credential_configuration_id: str
    critical_config: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        values = (
            self.configuration_id,
            self.agent_name,
            self.agent_version,
            self.model_provider,
            self.model_name,
            self.authentication_type,
            self.credential_configuration_id,
        )
        if any(not value.strip() for value in values):
            raise ValueError("Agent identity fields must not be empty")
        safe_config = json.loads(
            json.dumps(dict(self.critical_config), allow_nan=False)
        )
        object.__setattr__(self, "critical_config", _freeze(safe_config))

    @property
    def fingerprint(self) -> str:
        identity = {
            "agent_name": self.agent_name,
            "agent_version": self.agent_version,
            "authentication_type": self.authentication_type,
            "critical_config": _thaw(self.critical_config),
            "model_name": self.model_name,
            "model_provider": self.model_provider,
        }
        encoded = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value
