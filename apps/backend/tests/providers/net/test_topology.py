"""S10's topology is a fixed shape, not a caller-supplied Compose escape hatch."""

import pytest

from eval_platform.adapters.execution.provider_access.net.topology import (
    compose_overlay,
    validate_compose_file,
    validate_overlay,
)

PROXY_IMAGE = "sha256:" + "a" * 64
UPSTREAM_IMAGE = "sha256:" + "b" * 64
SCOPE = "t05-s10-run-001"


def overlay():
    return compose_overlay(
        scope=SCOPE, proxy_image=PROXY_IMAGE, upstream_image=UPSTREAM_IMAGE
    )


def test_main_cannot_join_egress_and_proxy_is_only_bridge():
    document = overlay()
    services = document["services"]
    networks = document["networks"]
    assert networks["internal"]["internal"] is True
    assert networks["egress"]["internal"] is False
    assert services["main"]["networks"] == ["internal"]
    assert set(services["proxy"]["networks"]) == {"internal", "egress"}
    assert list(services["fake-upstream"]["networks"]) == ["egress"]
    assert list(services["harbor-docker-egress-control-sidecar"]["networks"]) == [
        "egress"
    ]
    assert services["main"]["depends_on"]["proxy"]["condition"] == ("service_healthy")
    assert "fake-upstream.t05.invalid" in services["proxy"]["healthcheck"]["test"][-1]


def test_all_resources_have_task_and_run_scope_and_no_host_ports_or_mounts():
    document = overlay()
    for resource in (*document["services"].values(), *document["networks"].values()):
        assert resource["labels"] == {
            "agentexam.task": "05",
            "agentexam.scope": SCOPE,
        }
    for service in document["services"].values():
        assert "ports" not in service
        assert "volumes" not in service
        assert "network_mode" not in service


def test_fixture_roles_are_fixed_and_proxy_receives_only_non_secret_scope():
    document = overlay()
    proxy = document["services"]["proxy"]
    upstream = document["services"]["fake-upstream"]
    assert proxy["command"] == ["proxy"]
    assert proxy["environment"] == {"AGENTEXAM_RUN_ID": SCOPE}
    assert upstream["command"] == ["fake-upstream"]
    assert "environment" not in upstream
    assert "uid=65534,gid=65534" in proxy["tmpfs"][0]


@pytest.mark.parametrize(
    "field,value",
    [
        ("main-egress", ["internal", "egress"]),
        ("public-internal", False),
        ("host-port", ["8080:8080"]),
        ("host-volume", ["/host:/secrets"]),
    ],
)
def test_tampered_topology_fails_closed(field, value):
    document = overlay()
    if field == "main-egress":
        document["services"]["main"]["networks"] = value
    elif field == "public-internal":
        document["networks"]["internal"]["internal"] = value
    elif field == "host-port":
        document["services"]["proxy"]["ports"] = value
    else:
        document["services"]["fake-upstream"]["volumes"] = value
    with pytest.raises(ValueError, match="PROVIDER_TOPOLOGY_INVALID"):
        validate_overlay(
            document,
            scope=SCOPE,
            proxy_image=PROXY_IMAGE,
            upstream_image=UPSTREAM_IMAGE,
        )


@pytest.mark.parametrize(
    "scope,proxy_image",
    [("bad/scope", PROXY_IMAGE), (SCOPE, "python:latest"), ("", PROXY_IMAGE)],
)
def test_invalid_identity_or_mutable_image_fails_closed(scope, proxy_image):
    with pytest.raises(ValueError, match="PROVIDER_TOPOLOGY_INVALID"):
        compose_overlay(
            scope=scope, proxy_image=proxy_image, upstream_image=UPSTREAM_IMAGE
        )


def test_product_gate_rejects_a_different_path_or_tampered_file(tmp_path):
    import json

    path = tmp_path / "provider-compose.json"
    document = overlay()
    path.write_text(json.dumps(document))
    options = {
        "scope": SCOPE,
        "proxy_image": PROXY_IMAGE,
        "upstream_image": UPSTREAM_IMAGE,
    }
    validate_compose_file(path, [str(path.resolve())], **options)
    with pytest.raises(ValueError, match="HARBOR_NETWORK_CONFIG_INVALID"):
        validate_compose_file(path, [str(tmp_path / "other.json")], **options)
    document["services"]["main"]["networks"].append("egress")
    path.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="HARBOR_NETWORK_CONFIG_INVALID"):
        validate_compose_file(path, [str(path.resolve())], **options)
