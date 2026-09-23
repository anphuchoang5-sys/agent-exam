"""Capture and probe two live provider Harbor Trials without owning their teardown."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from providers.runtime.s11.docker_io import DockerIO, service_ip
from providers.runtime.s11.verdicts import SERVICES


class DockerCapture:
    def __init__(self, evidence: Path, scopes: tuple[str, str], mount_root: Path):
        self.evidence, self.scopes = evidence, scopes
        self.io = DockerIO(evidence)
        self.snapshot: dict[str, Any] = {
            "scopes": scopes,
            "allowed_mount_root": str(mount_root.resolve()),
            "containers": [],
            "networks": [],
            "readings": {},
            "secret": {},
            "public_secret_hits": 0,
            "residual": {},
        }

    def close(self) -> None:
        self.io.close()

    def wait_and_capture(self, timeout_sec: float = 300) -> None:
        deadline = time.monotonic() + timeout_sec
        live: dict[str, dict[str, dict[str, Any]]] = {}
        while time.monotonic() < deadline:
            live = {}
            for scope in self.scopes:
                ids = self.io.ids("container", scope, all_items=True)
                values = self.io.inspect("docker", "inspect", *ids) if ids else []
                live[scope] = {
                    item.get("Config", {})
                    .get("Labels", {})
                    .get("com.docker.compose.service", ""): item
                    for item in values
                }
            if all(
                set(live.get(scope, {})) == set(SERVICES)
                and all(
                    item.get("State", {}).get("Running")
                    for item in live[scope].values()
                )
                for scope in self.scopes
            ):
                break
            time.sleep(0.2)
        else:
            raise RuntimeError(f"S11_TRIALS_NOT_CONCURRENT:{sorted(live)}")

        self.snapshot["containers"] = [
            item for scope in self.scopes for item in live[scope].values()
        ]
        network_ids = [
            identity
            for scope in self.scopes
            for identity in self.io.ids("network", scope)
        ]
        self.snapshot["networks"] = self.io.inspect(
            "docker", "network", "inspect", *network_ids
        )
        for scope in self.scopes:
            other = self.scopes[1] if scope == self.scopes[0] else self.scopes[0]
            self._probe_scope(scope, live[scope], live[other])
        self._wait_upstream_records(live)
        self._write_raw_logs(live)

    def _probe_scope(self, scope: str, own: dict, other: dict) -> None:
        main = own["main"]["Id"]
        other_ip = service_ip(other["proxy"], "internal")
        values = {
            "own_proxy": self.io.tcp(main, "proxy", 8080),
            "own_upstream": self.io.tcp(main, "fake-upstream.t05.invalid", 443),
            "public": self.io.tcp(main, "1.1.1.1", 443),
            "host_gateway": self.io.tcp(main, "host.docker.internal", 80),
            "metadata": self.io.tcp(main, "169.254.169.254", 80),
            "other_trial": self.io.tcp(main, other_ip, 8080),
            "proxy_upstream": "PENDING",
        }
        self.snapshot["readings"][scope] = values
        proxy = own["proxy"]["Id"]
        control = self.io.run(
            "docker",
            "exec",
            proxy,
            "python",
            "-c",
            "import json;v=json.load(open('/tmp/provider-profile.json'));"
            "print(int(bool(v['profiles']['t05-fake']['secret'])))",
        )
        scan = self.io.run("docker", "exec", "-i", main, "bash", "-s", stdin=_SCAN)
        if control.returncode or scan.returncode:
            raise RuntimeError(f"S11_SECRET_PROBE_FAILED:{scope}")
        counts = json.loads(scan.stdout)
        self.snapshot["secret"][scope] = {
            "proxy_private_control": int(control.stdout.strip()),
            **counts,
        }

    def _wait_upstream_records(self, live: dict, timeout_sec: float = 120) -> None:
        deadline = time.monotonic() + timeout_sec
        while time.monotonic() < deadline:
            complete = True
            for scope in self.scopes:
                proxy_ip = service_ip(live[scope]["proxy"], "egress")
                log = self.io.run("docker", "logs", live[scope]["fake-upstream"]["Id"])
                if (
                    f'"peer": "{proxy_ip}"' in log.stdout
                    and '"path": "/responses"' in log.stdout
                ):
                    self.snapshot["readings"][scope]["proxy_upstream"] = "RECORDED"
                else:
                    complete = False
            if complete:
                return
            time.sleep(0.2)
        raise RuntimeError("S11_UPSTREAM_RECORD_MISSING")

    def _write_raw_logs(self, live: dict) -> None:
        for scope in self.scopes:
            for service in ("proxy", "fake-upstream"):
                result = self.io.run("docker", "logs", live[scope][service]["Id"])
                (self.evidence / f"{scope}-{service}.log").write_text(
                    result.stdout + result.stderr, encoding="utf-8"
                )

    def finish(self) -> None:
        self.snapshot["residual"] = {
            kind + "s": [
                identity
                for scope in self.scopes
                for identity in self.io.ids(kind, scope, all_items=kind == "container")
            ]
            for kind in ("container", "network", "volume")
        }
        marker = b"FAKE-T05-UPSTREAM-ONLY"
        self.snapshot["public_secret_hits"] = sum(
            path.read_bytes().count(marker)
            for path in self.evidence.rglob("*")
            if path.is_file() and path.name != "snapshot.json"
        )
        (self.evidence / "snapshot.json").write_text(
            json.dumps(self.snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )


_SCAN = r"""marker='FAKE-T05-UPSTREAM-ONLY'
pattern='[F]AKE-T05-UPSTREAM-ONLY'
files=$(timeout 10 grep -rla "$marker" /tmp /run /var/tmp 2>/dev/null | wc -l)
envs=0; argv=0
for f in /proc/[0-9]*/environ; do
  tr '\0' ' ' < "$f" 2>/dev/null | grep -q "$pattern" && envs=$((envs+1))
done
for f in /proc/[0-9]*/cmdline; do
  tr '\0' ' ' < "$f" 2>/dev/null | grep -q "$pattern" && argv=$((argv+1))
done
printf '{"workload_file_hits":%s,' "$files"
printf '"workload_environ_hits":%s,' "$envs"
printf '"workload_argv_hits":%s}\n' "$argv"
"""
