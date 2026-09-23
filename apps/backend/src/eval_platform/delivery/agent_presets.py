"""Fixed production Agent identities shared by catalog and isolated runtime."""

from eval_platform.domain.agent import AgentConfiguration

AGENT_PRESETS = {
    "codex-0153-terra-medium": (
        "Codex 0.153.0 / gpt-5.6-terra / medium",
        AgentConfiguration(
            "codex-0153-terra-medium",
            "codex",
            "0.153.0",
            "openai_chatgpt",
            "gpt-5.6-terra",
            "chatgpt_auth_json",
            "owner-codex",
            {"reasoning_effort": "medium"},
        ),
    ),
    "codex-0153-luna-low": (
        "Codex 0.153.0 / gpt-5.6-luna / low",
        AgentConfiguration(
            "codex-0153-luna-low",
            "codex",
            "0.153.0",
            "openai_chatgpt",
            "gpt-5.6-luna",
            "chatgpt_auth_json",
            "owner-codex",
            {"reasoning_effort": "low"},
        ),
    ),
    "codex-0153-sol-medium": (
        "Codex 0.153.0 / gpt-5.6-sol / medium",
        AgentConfiguration(
            "codex-0153-sol-medium",
            "codex",
            "0.153.0",
            "openai_chatgpt",
            "gpt-5.6-sol",
            "chatgpt_auth_json",
            "owner-codex",
            {"reasoning_effort": "medium"},
        ),
    ),
}
