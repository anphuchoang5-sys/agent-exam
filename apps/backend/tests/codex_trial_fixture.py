"""Container-only CLI double: real sandbox, synthetic auth, never model traffic."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ORIGINAL = "AGENTEXAM-SYNTHETIC-ORIGINAL-ONLY"
REFRESHED = "AGENTEXAM-SYNTHETIC-REFRESHED-ONLY"
FAKE_REFRESH = "AGENTEXAM-SYNTHETIC-REFRESH-TOKEN-ONLY"


def main():
    assert (
        sys.argv[1] == "exec"
        and "--dangerously-bypass-approvals-and-sandbox" not in sys.argv
    )
    assert os.getuid() == 65534
    mode = Path("/opt/agentexam-mode").read_text().strip()
    assert mode in {"success", "failure", "timeout", "patch-secret"}
    credential = Path("/tmp/codex-secrets/auth.json")
    assert json.loads(credential.read_text())["tokens"]["access_token"] == ORIGINAL
    # Positive control outside the sandbox: this trusted CLI double can read auth.
    assert Path("/tmp/codex-home/auth.json").read_bytes() == credential.read_bytes()
    command = """
from pathlib import Path
Path('/testbed/agentexam-synthetic.txt').write_text('synthetic sandbox patch\\n')
for name in ('/tmp/codex-secrets/auth.json', '/tmp/codex-home/auth.json'):
    try:
        Path(name).read_bytes()
    except PermissionError:
        print('credential-denied')
    else:
        raise RuntimeError('SYNTHETIC_BOUNDARY_FAILED')
print('workspace-write-ok')
"""
    sandbox = subprocess.run(
        [
            "/opt/agentexam-codex/bin/codex-real",
            "sandbox",
            "--",
            "/usr/bin/python3",
            "-c",
            command,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if sandbox.returncode != 0 or sandbox.stdout.count("credential-denied") != 2:
        print("SYNTHETIC_SANDBOX_FAILURE", sandbox.stdout, sandbox.stderr, flush=True)
        return 9
    print("SYNTHETIC_SANDBOX_PASSED", flush=True)
    credential.write_text(
        json.dumps(
            {
                "tokens": {
                    "access_token": REFRESHED,
                    "refresh_token": FAKE_REFRESH,
                }
            }
        )
    )
    text = ORIGINAL + " " + REFRESHED + " " + FAKE_REFRESH
    sessions = Path("/tmp/codex-home/sessions/2026/09/07")
    sessions.mkdir(parents=True)
    events = [
        {
            "type": "session_meta",
            "payload": {
                "id": "00000000-0000-0000-0000-000000000001",
                "cli_version": "0.153.0",
            },
        },
        {
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": text}],
            },
        },
    ]
    (sessions / "rollout-synthetic.jsonl").write_text(
        "\n".join(
            json.dumps({"timestamp": "2026-09-07T00:00:00Z", **event})
            for event in events
        )
        + "\n"
    )
    print(text, flush=True)
    print(text, file=sys.stderr, flush=True)
    if mode == "patch-secret":
        Path("/testbed/agentexam-synthetic.txt").write_text(text + "\n")
    if mode == "timeout":
        time.sleep(120)
    return 7 if mode == "failure" else 0


if __name__ == "__main__":
    sys.exit(main())
