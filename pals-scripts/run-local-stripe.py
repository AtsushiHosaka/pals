#!/usr/bin/env python3
"""Run the existing local Stripe CLI, without exposing test credentials.

Usage: python3 pals-scripts/run-local-stripe.py
Run in the foreground (or under your existing local process supervisor). Stop with
SIGINT/SIGTERM. Never start this helper alongside another listener. It uses the
existing ignored .local/e2e files, does not log in or create Stripe resources, and
never restarts the API. If it reports a changed webhook secret, restart the API
through the normal local release workflow before testing webhook deliveries.
"""

from __future__ import annotations

import fcntl
import json
import os
import re
import selectors
import signal
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
EVENTS = (
    "checkout.session.completed,customer.subscription.created,"
    "customer.subscription.updated,customer.subscription.deleted,"
    "invoice.paid,invoice.payment_failed"
)
MAX_LOG_BYTES = 1024 * 1024
SECRET = re.compile(rb"\bwhsec_[A-Za-z0-9]{16,256}\b")


class LocalStripeError(Exception):
    """Safe fixed-message operational failure; never include raw subprocess text."""


def private_file(path: Path, flags: int = os.O_RDONLY) -> int:
    """Open an owned regular file without following a final symlink."""
    fd = os.open(path, flags | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    info = os.fstat(fd)
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_uid != os.getuid()
        or stat.S_IMODE(info.st_mode) != 0o600
    ):
        os.close(fd)
        raise LocalStripeError(
            "Local Stripe files must be owned regular files with mode 0600."
        )
    return fd


def read_private(path: Path) -> bytes:
    fd = private_file(path)
    with os.fdopen(fd, "rb") as stream:
        data = stream.read(65537)
    if len(data) > 65536:
        raise LocalStripeError("Local Stripe configuration exceeds the supported size.")
    return data


def test_key(path: Path) -> str:
    key = read_private(path).decode("ascii").strip()
    if not re.fullmatch(r"sk_test_[A-Za-z0-9]{16,256}", key):
        raise LocalStripeError("A Stripe test secret key is required.")
    return key


def check_config(path: Path, key: str) -> dict:
    def object_pairs(pairs):
        result = {}
        for name, item in pairs:
            if name in result:
                raise LocalStripeError(
                    "Billing configuration contains duplicate fields."
                )
            result[name] = item
        return result

    value = json.loads(read_private(path), object_pairs_hook=object_pairs)
    fields = {
        "schema_version",
        "stripe_secret_key",
        "stripe_webhook_secret",
        "checkout_success_url",
        "checkout_cancel_url",
        "live_checkout_enabled",
    }
    version = value.get("schema_version") if isinstance(value, dict) else None
    if version == "pals.billing-runtime.v1":
        fields.add("pro_price_id")
        prices = [value.get("pro_price_id")]
    elif version == "pals.billing-runtime.v2":
        fields.update({"legacy_pro_price_id", "price_ids"})
        mapping = value.get("price_ids")
        if not isinstance(mapping, dict) or set(mapping) != {"plus", "pro", "research"}:
            raise LocalStripeError("Billing configuration has an invalid plan mapping.")
        prices = list(mapping.values())
        if value.get("legacy_pro_price_id") is not None:
            prices.append(value["legacy_pro_price_id"])
    else:
        raise LocalStripeError("Billing configuration schema is unsupported.")
    if (
        not isinstance(value, dict)
        or set(value) != fields
        or not re.fullmatch(r"sk_test_[A-Za-z0-9]{16,256}", key)
        or value.get("stripe_secret_key") != key
        or type(value.get("live_checkout_enabled")) is not bool
        or any(
            not isinstance(p, str) or not re.fullmatch(r"price_[A-Za-z0-9]{1,240}", p)
            for p in prices
        )
        or len(set(prices)) != len(prices)
        or not isinstance(value.get("stripe_webhook_secret"), str)
    ):
        raise LocalStripeError(
            "Billing configuration must match the supported local test contract."
        )
    # This historical flag enables Checkout, including sandbox Checkout. It does
    # not choose live mode: the test-key and local-origin checks enforce that.
    for field in ("checkout_success_url", "checkout_cancel_url"):
        raw = value[field]
        if not isinstance(raw, str) or any(ord(char) < 32 for char in raw):
            raise LocalStripeError("Checkout redirects must use the local app origin.")
        url = urlsplit(raw)
        if (url.scheme, url.netloc) != ("http", "localhost:3000") or url.fragment:
            raise LocalStripeError("Checkout redirects must use the local app origin.")
    return value


def update_webhook_secret(path: Path, key: str, secret: str) -> bool:
    if not SECRET.fullmatch(secret.encode("ascii")):
        raise LocalStripeError(
            "Listener readiness did not contain a valid signing secret."
        )
    config = check_config(path, key)
    if config.get("stripe_webhook_secret") == secret:
        return False
    original = path.stat(follow_symlinks=False)
    config["stripe_webhook_secret"] = secret
    fd, temp_name = tempfile.mkstemp(prefix=".stripe-config-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(config, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        # Fail closed if another process replaced the config while preparing it.
        current = path.stat(follow_symlinks=False)
        check_config(path, key)
        if (original.st_ino, original.st_mtime_ns) != (
            current.st_ino,
            current.st_mtime_ns,
        ):
            raise LocalStripeError(
                "Billing configuration changed; retry after coordinating the update."
            )
        os.replace(temp_name, path)
        return True
    finally:
        Path(temp_name).unlink(missing_ok=True)


def refuse_live_pid(path: Path) -> None:
    try:
        pid = int(read_private(path).strip())
    except FileNotFoundError:
        return
    except ValueError:
        raise LocalStripeError(
            "Listener PID file is invalid; inspect it before retrying."
        ) from None
    if pid <= 1:
        raise LocalStripeError(
            "Listener PID file is invalid; inspect it before retrying."
        )
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return
    except PermissionError:
        pass
    raise LocalStripeError("A listener PID is still alive; refusing duplicate startup.")


def command(cli: Path, config: Path) -> list[str]:
    return [
        str(cli),
        "--config",
        str(config),
        "listen",
        "--skip-update",
        "--events-from",
        "@self",
        "--events",
        EVENTS,
        "--forward-to",
        "http://127.0.0.1:8000/v1/internal/stripe/webhook",
    ]


def checked_directories(root: Path, path: Path) -> None:
    current = root
    for part in path.relative_to(root).parts:
        current = current / part
        info = current.lstat()
        if (
            not stat.S_ISDIR(info.st_mode)
            or info.st_uid != os.getuid()
            or info.st_mode & 0o022
        ):
            raise LocalStripeError(
                "Local Stripe directories must be owned and not writable by others."
            )


def run(root: Path = ROOT) -> int:
    local = root / ".local/e2e"
    state = local / "stripe"
    config = local / "billing/config.json"
    cli = local / "tools/stripe/stripe"
    for directory in (state, config.parent, cli.parent):
        checked_directories(root, directory)
    cli_info = cli.lstat()
    if (
        not stat.S_ISREG(cli_info.st_mode)
        or cli_info.st_uid != os.getuid()
        or cli_info.st_mode & 0o022
        or not os.access(cli, os.X_OK)
    ):
        raise LocalStripeError("The verified local Stripe executable is unavailable.")
    cli_config = cli.parent / "config.toml"
    if cli_config.exists() or cli_config.is_symlink():
        read_private(cli_config)
    lock_fd = private_file(state / "listener.lock", os.O_RDWR | os.O_CREAT)
    child = None
    log_fd = None
    pid_path = state / "listener.pid"
    previous_handlers = {}
    try:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise LocalStripeError(
                "Another local listener launcher holds the lock."
            ) from None
        refuse_live_pid(pid_path)
        key = test_key(state / "sandbox-key")
        check_config(config, key)
        # Open and validate before truncating; never chmod/follow an unsafe file.
        log_fd = private_file(state / "listener.log", os.O_WRONLY | os.O_CREAT)
        os.ftruncate(log_fd, 0)
        env = {**os.environ, "STRIPE_API_KEY": key}
        child = subprocess.Popen(
            command(cli, cli.parent / "config.toml"),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
        fd = private_file(pid_path, os.O_WRONLY | os.O_CREAT)
        with os.fdopen(fd, "w") as stream:
            stream.truncate(0)
            stream.write(str(child.pid) + "\n")
        stopped = False

        def stop(_signum, _frame):
            nonlocal stopped
            stopped = True

        for signum in (signal.SIGINT, signal.SIGTERM):
            previous_handlers[signum] = signal.signal(signum, stop)
        assert child.stdout is not None
        window = b""
        ready = False
        started = time.monotonic()
        with selectors.DefaultSelector() as selector:
            selector.register(child.stdout, selectors.EVENT_READ)
            while child.poll() is None and not stopped:
                if not ready and time.monotonic() - started > 45:
                    raise LocalStripeError(
                        "Listener readiness timed out; inspect the private log."
                    )
                for event, _ in selector.select(timeout=0.2):
                    chunk = os.read(event.fd, 8192)
                    if not chunk:
                        continue
                    if os.lseek(log_fd, 0, os.SEEK_CUR) + len(chunk) > MAX_LOG_BYTES:
                        os.ftruncate(log_fd, 0)
                        os.lseek(log_fd, 0, os.SEEK_SET)
                    os.write(log_fd, chunk)
                    window = (window + chunk)[-4096:]
                    # Require a terminated line: a pipe read may split the secret.
                    complete = window.rpartition(b"\n")[0]
                    match = SECRET.search(complete)
                    if not ready and b"Ready!" in complete and match:
                        changed = update_webhook_secret(
                            config, key, match.group().decode("ascii")
                        )
                        ready = True
                        print(
                            "Listener ready. Webhook secret changed: restart the API before testing."
                            if changed
                            else "Listener ready. The configured webhook secret is unchanged.",
                            flush=True,
                        )
        if stopped:
            return 0
        if not ready or child.returncode:
            raise LocalStripeError("Listener exited; inspect the private log.")
        return 0
    finally:
        if child is not None:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait(timeout=5)
            if child.stdout:
                child.stdout.close()
            try:
                if read_private(pid_path).strip() == str(child.pid).encode():
                    pid_path.unlink()
            except FileNotFoundError:
                pass
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)
        if log_fd is not None:
            os.close(log_fd)
        os.close(lock_fd)


def main() -> int:
    try:
        return run()
    except LocalStripeError as exc:
        print(str(exc), file=sys.stderr)
    except Exception:  # noqa: BLE001 -- the CLI boundary must never print credential-bearing errors.
        # Never expose exceptions which could include parsed secret values.
        print(
            "Local Stripe launcher failed; check private file permissions and configuration.",
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
