"""The private trigger must use the network covered by its peer allowlist."""
from pathlib import Path
from urllib.parse import urlsplit

import yaml


class ComposeLoader(yaml.SafeLoader):
    pass


ComposeLoader.add_constructor("!override", ComposeLoader.construct_sequence)


def test_reconciler_trigger_resolves_on_exactly_the_allowed_api_network():
    services = yaml.load(
        (Path(__file__).resolve().parents[1] / "docker-compose.e2e.yml").read_text(),
        Loader=ComposeLoader,
    )["services"]
    api = services["api"]
    reconciler = services["reconciler"]
    endpoint = urlsplit(api["environment"]["PALS_CANDIDATE_RECONCILER_URL"])
    # Compose service names resolve on every shared network, which can select
    # the DB-side source address and be rejected by the private trigger.
    assert endpoint.hostname != "reconciler"
    routes = [
        network
        for network, settings in reconciler["networks"].items()
        if endpoint.hostname in (settings or {}).get("aliases", [])
        and network in api["networks"]
    ]
    assert len(routes) == 1
    assert api["networks"][routes[0]]["ipv4_address"] == reconciler["environment"][
        "PALS_RECONCILER_TRIGGER_ALLOWED_PEER_IP"
    ]
    assert endpoint.scheme == "http"
    assert endpoint.port == int(reconciler["environment"]["PALS_RECONCILER_TRIGGER_PORT"])
