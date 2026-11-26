"""Disposable local sockets only. Neither Docker nor a model provider is used."""

import importlib.util
import os
import shutil
import socket
import ssl
import struct
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from pathlib import Path
from threading import BoundedSemaphore
from types import SimpleNamespace
from unittest.mock import Mock, patch

SCRIPTS = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


relay = load("local_provider_relay_test", "local-qualification/provider_relay.py")
tls = load("local_provider_relay_tls_test", "bootstrap-local-provider-tls.py")


def pair(stack):
    left, right = socket.socketpair()
    for endpoint in (left, right):
        stack.enter_context(endpoint)
        endpoint.settimeout(3)
    return left, right


def receive(endpoint, length):
    raw = bytearray()
    while len(raw) < length:
        part = endpoint.recv(length - len(raw))
        if not part:
            raise ValueError("fixture_received_truncated_bytes")
        raw.extend(part)
    return raw


class ProviderRelayTests(unittest.TestCase):
    def test_docker_stop_runs_the_relay_shutdown_path(self):
        server = Mock()
        handlers = []

        def register(_number, handler):
            handlers.append(handler)
            return relay.signal.SIG_DFL

        server.serve_forever.side_effect = lambda: handlers[0](relay.signal.SIGTERM, None)
        with patch.object(relay.signal, "signal", side_effect=register):
            relay.serve_until_stop(server)
        self.assertEqual(handlers[1:], [relay.signal.SIG_DFL])

    @unittest.skipUnless(shutil.which("openssl"), "OpenSSL fixture required")
    def test_tls_runs_end_to_end_across_both_byte_relays(self):
        request = bytes(range(256)) * 640
        response = request[::-1]
        with tempfile.TemporaryDirectory() as scratch, ExitStack() as endpoints:
            material = Path(scratch) / "test-ca"
            tls.issue(material, lifetime_hours=1)
            central_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            central_context.load_cert_chain(
                material / "server.pem", material / "server-key.pem"
            )
            worker_context = ssl.create_default_context(
                cafile=material / "ca-bundle.pem"
            )
            client, lane_input = pair(endpoints)
            lane_output, authority_input = pair(endpoints)
            authority_output, provider = pair(endpoints)

            def central():
                with central_context.wrap_socket(provider, server_side=True) as secure:
                    self.assertEqual(receive(secure, len(request)), request)
                    secure.sendall(response)
                    secure.unwrap().close()

            with ThreadPoolExecutor(max_workers=3) as pool:
                jobs = [
                    pool.submit(relay.transfer, left, right, session_seconds=6)
                    for left, right in (
                        (lane_input, lane_output),
                        (authority_input, authority_output),
                    )
                ]
                jobs.append(pool.submit(central))
                with worker_context.wrap_socket(
                    client, server_hostname=tls.HOST
                ) as secure:
                    self.assertEqual(
                        secure.getpeercert()["subjectAltName"], (("DNS", tls.HOST),)
                    )
                    secure.sendall(request)
                    self.assertEqual(receive(secure, len(response)), response)
                    secure.unwrap().close()
                for job in jobs:
                    job.result(timeout=6)

    def test_half_close_does_not_discard_the_response(self):
        with ExitStack() as endpoints, ThreadPoolExecutor(max_workers=1) as pool:
            client, left = pair(endpoints)
            right, service = pair(endpoints)
            result = pool.submit(relay.transfer, left, right, session_seconds=3)
            client.sendall(b"request")
            client.shutdown(socket.SHUT_WR)
            self.assertEqual(receive(service, 7), b"request")
            self.assertEqual(service.recv(1), b"")
            service.sendall(b"response")
            service.shutdown(socket.SHUT_WR)
            self.assertEqual(receive(client, 8), b"response")
            self.assertEqual(client.recv(1), b"")
            result.result(timeout=5)

    def test_authority_accepts_only_the_lane_peer_and_the_fixed_budget_target(self):
        client = Mock()
        with (
            patch.object(socket, "SO_PEERCRED", 17, create=True),
            patch.object(socket, "create_connection") as connect,
        ):
            client.getsockopt.return_value = struct.pack("3i", 18, 65532, 65532)
            with self.assertRaisesRegex(
                ValueError, "provider_relay_peer_identity_differs"
            ):
                relay.to_budget(client)
            connect.assert_not_called()
            client.getsockopt.return_value = struct.pack(
                "3i", 18, relay.LANE_UID, relay.RELAY_GID
            )
            self.assertIs(relay.to_budget(client), connect.return_value)
            connect.assert_called_once_with(("127.0.0.1", 443), relay.CONNECT_SECONDS)

    def test_missing_authority_is_closed_without_attempting_replay(self):
        disconnected = Mock(side_effect=FileNotFoundError)
        with patch.object(relay, "transfer") as transfer:
            relay.RelayHandler(object(), None, SimpleNamespace(connect=disconnected))
        disconnected.assert_called_once()
        transfer.assert_not_called()

    def test_idle_relay_exits_and_saturated_listener_refuses_new_connections(self):
        with ExitStack() as endpoints, ThreadPoolExecutor(max_workers=1) as pool:
            _client, left = pair(endpoints)
            right, _provider = pair(endpoints)
            pool.submit(relay.transfer, left, right, idle_seconds=0.05).result(
                timeout=2
            )

        server = object.__new__(relay.LaneRelay)
        server.slots = BoundedSemaphore(1)
        server.slots.acquire()
        server.shutdown_request = Mock()
        client = object()
        server.process_request(client, None)
        server.shutdown_request.assert_called_once_with(client)

    def test_private_socket_checks_refuse_foreign_or_exposed_paths(self):
        with tempfile.TemporaryDirectory() as scratch:
            directory = Path(scratch).resolve()
            path = directory / "authority.sock"
            path.write_bytes(b"foreign file")
            with (
                patch.object(relay, "AUTHORITY_UID", os.geteuid()),
                patch.object(relay, "RELAY_GID", directory.stat().st_gid),
            ):
                directory.chmod(0o755)
                with self.assertRaisesRegex(
                    ValueError, "provider_relay_directory_unprotected"
                ):
                    relay.private_socket_directory(path)
                directory.chmod(0o750)
                relay.private_socket_directory(path)
                with self.assertRaisesRegex(
                    ValueError, "provider_relay_socket_unprotected"
                ):
                    relay.socket_identity(path)
            self.assertEqual(path.read_bytes(), b"foreign file")

    def test_both_relay_roles_refuse_provider_credentials_before_binding(self):
        with (
            patch.dict(os.environ, {"OPENAI_API_KEY": "local-test-placeholder"}),
            patch.object(relay, "LaneRelay") as lane,
            patch.object(relay, "AuthorityRelay") as authority,
        ):
            for start in (relay.serve_lane, relay.serve_authority_socket):
                with self.assertRaisesRegex(
                    ValueError, "provider_relay_must_not_receive_authority_environment"
                ):
                    start()
            lane.assert_not_called()
            authority.assert_not_called()


if __name__ == "__main__":
    unittest.main()
