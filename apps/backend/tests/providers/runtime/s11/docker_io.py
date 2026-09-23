"""Small recorded Docker command boundary for the S11 harness."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


class DockerIO:
    def __init__(self, evidence: Path) -> None:
        self._commands = (evidence / "docker-commands.jsonl").open(
            "x", encoding="utf-8", newline="\n"
        )

    def close(self) -> None:
        self._commands.close()

    def run(
        self, *args: str, stdin: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            list(args),
            input=stdin.encode("utf-8") if stdin is not None else None,
            capture_output=True,
            timeout=30,
        )
        result = subprocess.CompletedProcess(
            completed.args,
            completed.returncode,
            completed.stdout.decode("utf-8", errors="replace"),
            completed.stderr.decode("utf-8", errors="replace"),
        )
        self._commands.write(
            json.dumps({"argv": list(args), "returncode": result.returncode}) + "\n"
        )
        self._commands.flush()
        return result

    def ids(self, kind: str, scope: str, *, all_items: bool = False) -> list[str]:
        args = ["docker", kind, "ls", "--quiet"]
        if kind == "container" and all_items:
            args.append("--all")
        args += [
            "--filter",
            "label=agentexam.task=05",
            "--filter",
            f"label=agentexam.scope={scope}",
        ]
        return self.run(*args).stdout.split()

    def inspect(self, *command: str) -> list[dict[str, Any]]:
        result = self.run(*command)
        if result.returncode:
            raise RuntimeError(f"S11_DOCKER_INSPECT_FAILED:{command[1:3]}")
        value = json.loads(result.stdout)
        return value if isinstance(value, list) else [value]

    def tcp(self, container: str, host: str, port: int) -> str:
        result = self.run(
            "docker",
            "exec",
            container,
            "timeout",
            "3",
            "bash",
            "-c",
            "exec 3<>/dev/tcp/$1/$2",
            "probe",
            host,
            str(port),
        )
        return "OPEN" if result.returncode == 0 else "CLOSED"


def service_ip(container: dict[str, Any], role: str) -> str:
    for name, value in container["NetworkSettings"]["Networks"].items():
        if name.endswith("_" + role):
            return str(value["IPAddress"])
    raise RuntimeError(f"S11_NETWORK_ROLE_MISSING:{role}")
