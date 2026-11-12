#!/usr/bin/env python3
"""Issue or inspect the LOCAL-ONLY TLS material of the qualification budget proxy.

The local guard terminates the workers' provider connections on 127.0.0.1:443 and forwards
them to the real provider. Its leaf certificate is signed by a one-off local CA whose private
key is destroyed after issuance. Only the three guarded task containers trust that CA through
``SSL_CERT_FILE``; no host, system or global trust store is read or changed. The CA is name
constrained to the single proxied host. This proves nothing about production transport.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import ssl
import subprocess
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

HOST = "api.openai.com"
CA_NAME = "PALS explicitly local budget transport"
FILES = ("ca-bundle.pem", "server.pem", "server-key.pem")
DEFAULT_LIFETIME_HOURS = 12
MAXIMUM_LIFETIME_HOURS = 24
BACKDATE_SECONDS = 300
CONFIG = """[ca]
default_ca=local
[local]
dir=@@DIR@@
database=$dir/index.txt
new_certs_dir=$dir/new
serial=$dir/serial
default_md=sha256
policy=any
unique_subject=no
copy_extensions=none
[any]
commonName=supplied
[req]
distinguished_name=name
prompt=no
[name]
commonName=@@NAME@@
[v3_ca]
basicConstraints=critical,CA:TRUE,pathlen:0
keyUsage=critical,keyCertSign
nameConstraints=critical,permitted;DNS:@@HOST@@
subjectKeyIdentifier=hash
[v3_leaf]
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature
extendedKeyUsage=serverAuth
subjectAltName=DNS:@@HOST@@
authorityKeyIdentifier=keyid
"""


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def need(ok, code):
    if not ok:
        raise ValueError(code)


def private_directory(directory, *, create=False):
    directory = Path(directory)
    if create:
        directory.mkdir(mode=0o700, exist_ok=True)
    need(
        directory.is_dir()
        and not directory.is_symlink()
        and directory.stat().st_mode & 0o777 == 0o700,
        "local_provider_tls_private_directory_required",
    )
    return directory


def tool(openssl, args, cwd):
    # Output is discarded on purpose: nothing from key generation may reach a log.
    result = subprocess.run(
        [openssl, *args],
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=30,
        check=False,
    )
    need(result.returncode == 0, "local_provider_tls_issuer_tool_failed")


def write(path, raw, mode):
    temporary = path.with_name("." + path.name + ".new")
    # A stale leftover is removed (never followed or reused); the new file must be
    # created by this call and must not be a link.
    try:
        os.unlink(temporary)
    except FileNotFoundError:
        pass
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(temporary, flags, 0o600)
    with os.fdopen(descriptor, "wb") as output:
        output.write(raw)
        output.flush()
        os.fsync(output.fileno())
    os.chmod(temporary, mode)
    os.replace(temporary, path)


def issue(
    directory, *, lifetime_hours=DEFAULT_LIFETIME_HOURS, openssl="openssl", now=None
):
    """Replace the three files with one fresh generation. Returns public facts only."""
    need(
        type(lifetime_hours) is int and 1 <= lifetime_hours <= MAXIMUM_LIFETIME_HOURS,
        "local_provider_tls_short_lifetime_required",
    )
    directory = private_directory(directory, create=True)
    now = now or datetime.now(timezone.utc)
    start = (now - timedelta(seconds=BACKDATE_SECONDS)).strftime("%Y%m%d%H%M%SZ")
    end = (now + timedelta(hours=lifetime_hours)).strftime("%Y%m%d%H%M%SZ")
    with tempfile.TemporaryDirectory(prefix="pals-local-provider-tls-") as scratch:
        work = Path(scratch)
        work.chmod(0o700)
        (work / "new").mkdir(mode=0o700)
        (work / "index.txt").write_bytes(b"")
        (work / "serial").write_text("%032X\n" % int.from_bytes(os.urandom(15), "big"))
        # The subject comes from the configuration: ``-subj`` handling differs between
        # OpenSSL and LibreSSL when ``prompt=no`` is set.
        for file, name in (("ca.cnf", CA_NAME), ("leaf.cnf", HOST)):
            (work / file).write_text(
                CONFIG.replace("@@DIR@@", str(work))
                .replace("@@HOST@@", HOST)
                .replace("@@NAME@@", name)
            )
        # Named-curve encoding is explicit: LibreSSL otherwise writes explicit parameters,
        # which OpenSSL-based clients reject.
        key = ["genpkey", "-algorithm", "EC", "-pkeyopt", "ec_paramgen_curve:P-256"]
        key += ["-pkeyopt", "ec_param_enc:named_curve"]
        sign = ["ca", "-batch", "-notext", "-config", "ca.cnf"]
        window = ["-startdate", start, "-enddate", end]
        tool(openssl, [*key, "-out", "ca-key.pem"], work)
        tool(
            openssl,
            [
                "req",
                "-new",
                "-config",
                "ca.cnf",
                "-key",
                "ca-key.pem",
                "-out",
                "ca.csr",
            ],
            work,
        )
        tool(
            openssl,
            [*sign, "-selfsign", "-keyfile", "ca-key.pem", "-in", "ca.csr"]
            + ["-out", "ca.pem", "-extensions", "v3_ca", *window],
            work,
        )
        tool(openssl, [*key, "-out", "server-key.pem"], work)
        tool(
            openssl,
            ["req", "-new", "-config", "leaf.cnf", "-key", "server-key.pem"]
            + ["-out", "server.csr"],
            work,
        )
        tool(
            openssl,
            [*sign, "-cert", "ca.pem", "-keyfile", "ca-key.pem", "-in", "server.csr"]
            + ["-out", "server.pem", "-extensions", "v3_leaf", *window],
            work,
        )
        # The CA key never leaves this scratch directory, which is removed on exit, so no
        # further certificate can ever be issued under the trusted local root.
        ca, leaf = (work / "ca.pem").read_bytes(), (work / "server.pem").read_bytes()
        leaf_key = (work / "server-key.pem").read_bytes()
        (work / "ca-key.pem").write_bytes(b"\0" * 512)
        # Prove the new generation with a real handshake before replacing anything, so a
        # failed issuance leaves the previous material untouched.
        stage = work / "stage"
        stage.mkdir(mode=0o700)
        for name, raw in zip(FILES, (ca, leaf, leaf_key)):
            write(stage / name, raw, 0o600)
        need(
            inspect(stage, minimum_remaining_seconds=0)["state"] == "valid",
            "local_provider_tls_issued_material_invalid",
        )
    # The bundle holds the local CA and nothing else. It is the only world-readable file:
    # the guarded task containers read it as UID 65532 through a read-only bind mount.
    write(directory / "server-key.pem", leaf_key, 0o600)
    write(directory / "server.pem", leaf, 0o600)
    write(directory / "ca-bundle.pem", ca, 0o644)
    return inspect(directory, minimum_remaining_seconds=0)


def _pump(client, incoming, outgoing, server, server_in, server_out):
    for _ in range(20):
        done = True
        for side, out, peer_in in (
            (client, outgoing, server_in),
            (server, server_out, incoming),
        ):
            try:
                side.do_handshake()
            except ssl.SSLWantReadError:
                done = False
            data = out.read()
            if data:
                peer_in.write(data)
        if done:
            return
    raise ssl.SSLError("handshake_did_not_complete")


def handshake(directory):
    """In-memory TLS handshake: key matches leaf, leaf chains to the bundle, host matches."""
    server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server_context.load_cert_chain(
        directory / "server.pem", directory / "server-key.pem"
    )
    client_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    client_context.load_verify_locations(cafile=directory / "ca-bundle.pem")
    c_in, c_out, s_in, s_out = (ssl.MemoryBIO() for _ in range(4))
    client = client_context.wrap_bio(c_in, c_out, server_hostname=HOST)
    server = server_context.wrap_bio(s_in, s_out, server_side=True)
    _pump(client, c_in, c_out, server, s_in, s_out)
    return client.getpeercert(), client.getpeercert(binary_form=True)


def inspect(directory, *, minimum_remaining_seconds, now=None):
    """Read-only state. ``state`` is valid, expired, expires_within_window or invalid."""
    directory = Path(directory)
    result = {"scope": "local_budget_proxy_transport_only", "host": HOST}
    try:
        private_directory(directory)
        for name in FILES:
            path = directory / name
            need(path.is_file() and not path.is_symlink(), "missing")
        need((directory / "server-key.pem").stat().st_mode & 0o077 == 0, "key_mode")
        bundle = (directory / "ca-bundle.pem").read_bytes()
        need(b"PRIVATE KEY" not in bundle, "key_in_bundle")
        peer, der = handshake(directory)
    except ssl.SSLCertVerificationError as error:
        # X509_V_ERR_CERT_HAS_EXPIRED: the only verification failure reissue alone repairs.
        result["state"] = "expired" if error.verify_code == 10 else "invalid"
        return result
    except (ValueError, OSError, ssl.SSLError):
        result["state"] = "invalid"
        return result
    remaining = int(ssl.cert_time_to_seconds(peer["notAfter"]) - (now or time.time()))
    result.update(
        state="valid"
        if remaining >= minimum_remaining_seconds
        else ("expired" if remaining <= 0 else "expires_within_window"),
        remaining_seconds=remaining,
        not_after=peer["notAfter"],
        server_certificate_sha256=sha(der),
        ca_bundle_sha256=sha(bundle),
        ca_bundle_certificates=len(re.findall(rb"-----BEGIN CERTIFICATE-----", bundle)),
    )
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--directory", type=Path, required=True)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--issue", action="store_true")
    mode.add_argument("--check", action="store_true")
    p.add_argument("--lifetime-hours", type=int, default=DEFAULT_LIFETIME_HOURS)
    p.add_argument("--minimum-remaining-seconds", type=int, default=0)
    p.add_argument("--openssl", default="openssl")
    a = p.parse_args()
    try:
        if a.issue:
            result = issue(
                a.directory, lifetime_hours=a.lifetime_hours, openssl=a.openssl
            )
        else:
            result = inspect(
                a.directory, minimum_remaining_seconds=a.minimum_remaining_seconds
            )
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        code = (
            str(error)
            if isinstance(error, ValueError)
            else "local_provider_tls_io_failed"
        )
        print(json.dumps({"state": "refused", "code": code}))
        raise SystemExit(1) from None
    # Public certificate facts only: never key material or certificate bodies.
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["state"] == "valid" else 1)


if __name__ == "__main__":
    main()
