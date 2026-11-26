"""Fixed TLS transport between a local lane and the sole provider budget authority."""

from __future__ import annotations

import errno
import os
import select
import signal
import socket
import stat
import struct
import time
from pathlib import Path
from socketserver import (
    BaseRequestHandler,
    ThreadingTCPServer,
    ThreadingUnixStreamServer,
)
from threading import BoundedSemaphore

LOCAL_PROVIDER = ("127.0.0.1", 443)
AUTHORITY_SOCKET = Path("/run/pals-provider/authority.sock")
AUTHORITY_UID = 0
LANE_UID = 65531
RELAY_GID = 65531
MAX_BUFFER = 64 * 1024
CONNECT_SECONDS = 3
IDLE_SECONDS = 180
SESSION_SECONDS = 240
MAX_CONNECTIONS = 32


def need(condition, code):
    if not condition:
        raise ValueError(code)


def transfer(
    left, right, *, idle_seconds=IDLE_SECONDS, session_seconds=SESSION_SECONDS
):
    """Copy ciphertext in bounded buffers, preserving independent TCP half-closes."""
    peer = {left: right, right: left}
    pending = {endpoint: bytearray() for endpoint in peer}
    read_ended = set()
    write_ended = set()
    for endpoint in peer:
        endpoint.setblocking(False)
    start = time.monotonic()
    active_until = start + idle_seconds
    until = start + session_seconds
    while len(write_ended) < len(peer):
        for endpoint, remote in peer.items():
            if (
                remote in read_ended
                and endpoint not in write_ended
                and not pending[endpoint]
            ):
                try:
                    endpoint.shutdown(socket.SHUT_WR)
                except OSError as error:
                    if error.errno != errno.ENOTCONN:
                        raise
                write_ended.add(endpoint)
        if len(write_ended) == len(peer):
            return
        remaining = min(active_until, until) - time.monotonic()
        if remaining <= 0:
            return
        reads = [
            endpoint
            for endpoint, remote in peer.items()
            if endpoint not in read_ended and len(pending[remote]) < MAX_BUFFER
        ]
        writes = [endpoint for endpoint in peer if pending[endpoint]]
        readable, writable, _ = select.select(reads, writes, [], remaining)
        for endpoint in readable:
            remote = peer[endpoint]
            try:
                data = endpoint.recv(MAX_BUFFER - len(pending[remote]))
            except BlockingIOError:
                continue
            if data:
                pending[remote].extend(data)
                active_until = time.monotonic() + idle_seconds
            else:
                read_ended.add(endpoint)
        for endpoint in writable:
            try:
                sent = endpoint.send(pending[endpoint])
            except BlockingIOError:
                continue
            if not sent:
                return
            del pending[endpoint][:sent]
            active_until = time.monotonic() + idle_seconds


def private_socket_directory(path):
    parent = path.parent
    info = parent.lstat()
    need(
        parent.resolve(strict=True) == parent
        and stat.S_ISDIR(info.st_mode)
        and info.st_uid == AUTHORITY_UID
        and info.st_gid == RELAY_GID
        and stat.S_IMODE(info.st_mode) == 0o750,
        "provider_relay_directory_unprotected",
    )


def socket_identity(path):
    info = path.lstat()
    need(
        stat.S_ISSOCK(info.st_mode)
        and info.st_uid == AUTHORITY_UID
        and info.st_gid == RELAY_GID
        and stat.S_IMODE(info.st_mode) == 0o660,
        "provider_relay_socket_unprotected",
    )
    return info.st_dev, info.st_ino


def require_peer(endpoint, uid):
    need(hasattr(socket, "SO_PEERCRED"), "provider_relay_peer_credentials_unavailable")
    format_ = "3i"
    _, peer_uid, _ = struct.unpack(
        format_,
        endpoint.getsockopt(
            socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize(format_)
        ),
    )
    need(peer_uid == uid, "provider_relay_peer_identity_differs")


def to_authority(_client):
    private_socket_directory(AUTHORITY_SOCKET)
    expected = socket_identity(AUTHORITY_SOCKET)
    remote = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        remote.settimeout(CONNECT_SECONDS)
        remote.connect(str(AUTHORITY_SOCKET))
        require_peer(remote, AUTHORITY_UID)
        need(
            socket_identity(AUTHORITY_SOCKET) == expected,
            "provider_relay_socket_changed",
        )
    except BaseException:
        remote.close()
        raise
    return remote


def to_budget(client):
    require_peer(client, LANE_UID)
    return socket.create_connection(LOCAL_PROVIDER, CONNECT_SECONDS)


class RelayHandler(BaseRequestHandler):
    def handle(self):
        try:
            with self.server.connect(self.request) as remote:
                transfer(self.request, remote)
        except (OSError, ValueError):
            # No second connect and no replay after any ambiguous transfer.
            return


class BoundedConnections:
    daemon_threads = False

    def __init__(self, address, connect, *, bind_and_activate=True):
        self.connect = connect
        self.slots = BoundedSemaphore(MAX_CONNECTIONS)
        super().__init__(address, RelayHandler, bind_and_activate=bind_and_activate)

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self.slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.slots.release()


class LaneRelay(BoundedConnections, ThreadingTCPServer):
    pass


class AuthorityRelay(BoundedConnections, ThreadingUnixStreamServer):
    pass


class StopRelay(Exception):
    """Stop accepting connections and let the bounded transfers close."""


def serve_until_stop(server):
    def stop(_signum, _frame):
        raise StopRelay

    previous = signal.signal(signal.SIGTERM, stop)
    try:
        server.serve_forever()
    except StopRelay:
        pass
    finally:
        signal.signal(signal.SIGTERM, previous)


def require_credential_free_environment():
    names = {"OPENAI_API_KEY", "PALS_OPENAI_API_KEY", "PALS_BUDGET_RESUME_SHA256"}
    need(
        not any(os.environ.get(name) for name in names),
        "provider_relay_must_not_receive_authority_environment",
    )


def serve_lane():
    require_credential_free_environment()
    need(
        os.geteuid() == LANE_UID and os.getegid() == RELAY_GID,
        "provider_relay_lane_identity_required",
    )
    with LaneRelay(LOCAL_PROVIDER, to_authority) as server:
        serve_until_stop(server)


def serve_authority_socket():
    """Run beside the existing budget server in its network namespace only."""
    require_credential_free_environment()
    need(
        os.geteuid() == AUTHORITY_UID and os.getegid() == RELAY_GID,
        "provider_relay_authority_identity_required",
    )
    path = AUTHORITY_SOCKET
    private_socket_directory(path)
    created = None
    with AuthorityRelay(str(path), to_budget, bind_and_activate=False) as server:
        try:
            # Never remove an existing path to start. An old or foreign listener is a refusal.
            mask = os.umask(0o077)
            try:
                server.server_bind()
            finally:
                os.umask(mask)
            info = path.lstat()
            created = info.st_dev, info.st_ino
            os.chmod(path, 0o660)
            need(socket_identity(path) == created, "provider_relay_socket_changed")
            server.server_activate()
            serve_until_stop(server)
        finally:
            if created is not None:
                try:
                    info = path.lstat()
                except FileNotFoundError:
                    pass
                else:
                    if (
                        stat.S_ISSOCK(info.st_mode)
                        and (info.st_dev, info.st_ino) == created
                    ):
                        path.unlink()
