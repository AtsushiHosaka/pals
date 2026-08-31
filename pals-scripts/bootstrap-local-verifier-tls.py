#!/usr/bin/env python3
"""Create one ephemeral local mTLS generation without writing private keys to disk."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import boto3  # type: ignore[import-untyped]
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

SERVER_NAME = "pals-lean-verifier.pals.internal"
CLIENT_SPIFFE_URI = "spiffe://pals/local/verified-reconciler"


def main() -> None:
    arguments = _arguments()
    _require_sha256(arguments.toolchain_sha256, "toolchain SHA-256")
    if not arguments.image_digest.strip():
        raise SystemExit("image digest must be nonblank")
    output = arguments.output.resolve()
    if not output.parent.is_dir():
        raise SystemExit("output parent must already exist")

    release_id = str(uuid4())
    ca_key = ec.generate_private_key(ec.SECP256R1())
    server_key = ec.generate_private_key(ec.SECP256R1())
    client_key = ec.generate_private_key(ec.SECP256R1())
    now = datetime.now(UTC)
    ca_certificate = _ca_certificate(ca_key, now)
    server_certificate = _leaf_certificate(
        ca_certificate=ca_certificate,
        ca_key=ca_key,
        common_name=SERVER_NAME,
        key=server_key,
        now=now,
        server=True,
    )
    client_certificate = _leaf_certificate(
        ca_certificate=ca_certificate,
        ca_key=ca_key,
        common_name="pals-local-verified-reconciler",
        key=client_key,
        now=now,
        server=False,
    )

    secrets = boto3.client(
        "secretsmanager",
        endpoint_url=arguments.endpoint_url,
        region_name=arguments.region,
    )
    prefix = f"/pals/local/verifier/{release_id}"
    ca_reference = _create_secret(
        secrets,
        f"{prefix}/ca-certificate",
        _certificate_pem(ca_certificate),
    )
    server_certificate_reference = _create_secret(
        secrets,
        f"{prefix}/server-certificate",
        _certificate_pem(server_certificate),
    )
    server_key_reference = _create_secret(
        secrets,
        f"{prefix}/server-private-key",
        _private_key_pem(server_key),
    )
    client_certificate_reference = _create_secret(
        secrets,
        f"{prefix}/client-certificate",
        _certificate_pem(client_certificate),
    )
    client_key_reference = _create_secret(
        secrets,
        f"{prefix}/client-private-key",
        _private_key_pem(client_key),
    )
    ca_spki = _spki_sha256(ca_certificate)
    client_spki = _spki_sha256(client_certificate)
    deployment_binding = hashlib.sha256(
        json.dumps(
            {
                "client_spki_sha256": client_spki,
                "image_digest": arguments.image_digest,
                "release_id": release_id,
                "server_name": SERVER_NAME,
                "toolchain_sha256": arguments.toolchain_sha256,
            },
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    ).hexdigest()
    environment = {
        "PALS_RELEASE_ID": release_id,
        "PALS_VERIFIER_DEPLOYMENT_BINDING_SHA256": deployment_binding,
        "PALS_VERIFIER_IMAGE_DIGEST": arguments.image_digest,
        "PALS_VERIFIER_TOOLCHAIN_SHA256": arguments.toolchain_sha256,
        "PALS_VERIFIER_CA_SPKI_SHA256": ca_spki,
        "PALS_RECONCILER_CLIENT_SPKI_SHA256": client_spki,
        "PALS_RECONCILER_CLIENT_SPIFFE_URI": CLIENT_SPIFFE_URI,
        "PALS_VERIFIER_SERVER_CERTIFICATE_SECRET_ARN": server_certificate_reference[0],
        "PALS_VERIFIER_SERVER_CERTIFICATE_SECRET_VERSION_ID": server_certificate_reference[1],
        "PALS_VERIFIER_SERVER_PRIVATE_KEY_SECRET_ARN": server_key_reference[0],
        "PALS_VERIFIER_SERVER_PRIVATE_KEY_SECRET_VERSION_ID": server_key_reference[1],
        "PALS_VERIFIER_CA_CERTIFICATE_SECRET_ARN": ca_reference[0],
        "PALS_VERIFIER_CA_CERTIFICATE_SECRET_VERSION_ID": ca_reference[1],
        "PALS_RECONCILER_CLIENT_CERTIFICATE_SECRET_ARN": client_certificate_reference[0],
        "PALS_RECONCILER_CLIENT_CERTIFICATE_SECRET_VERSION_ID": client_certificate_reference[1],
        "PALS_RECONCILER_CLIENT_PRIVATE_KEY_SECRET_ARN": client_key_reference[0],
        "PALS_RECONCILER_CLIENT_PRIVATE_KEY_SECRET_VERSION_ID": client_key_reference[1],
    }
    _write_environment(output, environment)
    print(
        json.dumps(
            {
                "environment_file": str(output),
                "release_id": release_id,
                "secret_count": 5,
                "status": "ready",
            },
            separators=(",", ":"),
            sort_keys=True,
        )
    )


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint-url", required=True)
    parser.add_argument("--image-digest", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--region", default="ap-northeast-1")
    parser.add_argument("--toolchain-sha256", required=True)
    return parser.parse_args()


def _ca_certificate(
    key: ec.EllipticCurvePrivateKey,
    now: datetime,
) -> x509.Certificate:
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "PALS local verifier CA")])
    return (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(hours=24))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=False,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=None,
                decipher_only=None,
            ),
            critical=True,
        )
        .sign(key, hashes.SHA256())
    )


def _leaf_certificate(
    *,
    ca_certificate: x509.Certificate,
    ca_key: ec.EllipticCurvePrivateKey,
    common_name: str,
    key: ec.EllipticCurvePrivateKey,
    now: datetime,
    server: bool,
) -> x509.Certificate:
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    san = (
        x509.SubjectAlternativeName([x509.DNSName(SERVER_NAME)])
        if server
        else x509.SubjectAlternativeName([x509.UniformResourceIdentifier(CLIENT_SPIFFE_URI)])
    )
    usage = ExtendedKeyUsageOID.SERVER_AUTH if server else ExtendedKeyUsageOID.CLIENT_AUTH
    return (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_certificate.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(hours=24))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(san, critical=True)
        .add_extension(x509.ExtendedKeyUsage([usage]), critical=True)
        .sign(ca_key, hashes.SHA256())
    )


def _certificate_pem(certificate: x509.Certificate) -> bytes:
    return certificate.public_bytes(serialization.Encoding.PEM)


def _private_key_pem(key: ec.EllipticCurvePrivateKey) -> bytes:
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )


def _spki_sha256(certificate: x509.Certificate) -> str:
    return hashlib.sha256(
        certificate.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    ).hexdigest()


def _create_secret(client: object, name: str, value: bytes) -> tuple[str, str]:
    response = client.create_secret(Name=name, SecretBinary=value)  # type: ignore[attr-defined]
    arn = response.get("ARN") if isinstance(response, dict) else None
    version_id = response.get("VersionId") if isinstance(response, dict) else None
    if not isinstance(arn, str) or not arn or not isinstance(version_id, str) or not version_id:
        raise RuntimeError("Secrets Manager did not return an immutable secret reference")
    return arn, version_id


def _write_environment(path: Path, values: dict[str, str]) -> None:
    payload = "".join(f"{name}={value}\n" for name, value in sorted(values.items()))
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    descriptor = os.open(
        temporary,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
        stat.S_IRUSR | stat.S_IWUSR,
    )
    try:
        os.write(descriptor, payload.encode("utf-8"))
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, path)
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def _require_sha256(value: str, label: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise SystemExit(f"{label} must be lowercase SHA-256")


if __name__ == "__main__":
    main()
