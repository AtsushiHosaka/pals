from __future__ import annotations

import importlib.util
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "pals-scripts/run-local-stripe.py"
SPEC = importlib.util.spec_from_file_location("local_stripe", SCRIPT)
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
KEY = "sk_test_" + "a" * 24
SECRET = "whsec_" + "b" * 24
CONFIG = {
    "schema_version": "pals.billing-runtime.v1",
    "stripe_secret_key": KEY,
    "stripe_webhook_secret": "whsec_" + "c" * 24,
    "pro_price_id": "price_preserved",
    "checkout_success_url": "http://localhost:3000/?checkout=success",
    "checkout_cancel_url": "http://localhost:3000/?checkout=cancel",
    "live_checkout_enabled": True,
}


def private(path, content):
    path.write_text(content)
    path.chmod(0o600)
    return path


def test_private_files_reject_symlinks_wrong_modes_and_live_keys(tmp_path):
    source = private(tmp_path / "key", KEY)
    assert M.test_key(source) == KEY
    link = tmp_path / "link"
    link.symlink_to(source)
    with pytest.raises(OSError):
        M.test_key(link)
    source.chmod(0o644)
    with pytest.raises(M.LocalStripeError):
        M.test_key(source)
    private(source, "sk_live_" + "a" * 24)
    with pytest.raises(M.LocalStripeError):
        M.test_key(source)


def test_config_update_preserves_settings_and_requires_matching_test_key(tmp_path):
    original = dict(CONFIG)
    path = private(tmp_path / "config.json", json.dumps(original))
    assert M.update_webhook_secret(path, KEY, SECRET)
    assert not M.update_webhook_secret(path, KEY, SECRET)
    value = json.loads(path.read_text())
    assert value == {**original, "stripe_webhook_secret": SECRET}
    assert path.stat().st_mode & 0o777 == 0o600
    before = path.read_bytes()
    with pytest.raises(M.LocalStripeError):
        M.update_webhook_secret(path, KEY + "x", SECRET)
    assert path.read_bytes() == before
    assert not list(tmp_path.glob(".stripe-config-*"))


def test_existing_live_pid_is_refused_and_command_never_contains_credentials(tmp_path):
    path = private(tmp_path / "listener.pid", str(os.getpid()))
    with pytest.raises(M.LocalStripeError, match="refusing duplicate"):
        M.refuse_live_pid(path)
    args = M.command(Path("/verified/stripe"), Path("/private/config"))
    assert KEY not in " ".join(args)
    assert "--api-key" not in args and "--live" not in args
    assert args[-1] == "http://127.0.0.1:8000/v1/internal/stripe/webhook"
    assert len(args[args.index("--events") + 1].split(",")) == 6


def test_main_never_prints_an_unexpected_exception_secret(monkeypatch, capsys):
    def fail():
        raise ValueError(KEY + SECRET)

    monkeypatch.setattr(M, "run", fail)
    assert M.main() == 1
    captured = capsys.readouterr()
    assert KEY not in captured.err and SECRET not in captured.err
    assert not captured.out


def test_local_fake_process_readiness_and_sigterm_cleanup_do_not_expose_secrets(
    tmp_path,
):
    # A local process fixture only: never starts Stripe or uses network.
    state = tmp_path / ".local/e2e/stripe"
    billing = tmp_path / ".local/e2e/billing"
    tools = tmp_path / ".local/e2e/tools/stripe"
    for path in (state, billing, tools):
        path.mkdir(parents=True, mode=0o700)
    private(state / "sandbox-key", KEY)
    config = private(
        billing / "config.json",
        json.dumps(CONFIG),
    )
    fake = tools / "stripe"
    fake.write_text(
        f"#!{sys.executable}\nimport os,time\nassert os.environ['STRIPE_API_KEY']=={KEY!r}\nprint('Ready! Your webhook signing secret is {SECRET[:24]}',end='',flush=True)\ntime.sleep(.05)\nprint('{SECRET[24:]}',flush=True)\nwhile True: time.sleep(.1)\n"
    )
    fake.chmod(0o700)
    runner = f"import runpy; m=runpy.run_path({str(SCRIPT)!r}); raise SystemExit(m['run'](__import__('pathlib').Path({str(tmp_path)!r})))"
    process = subprocess.Popen(
        [sys.executable, "-c", runner],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if json.loads(config.read_text())["stripe_webhook_secret"] == SECRET:
                break
            if process.poll() is not None:
                pytest.fail("Fixture launcher exited before readiness")
            time.sleep(0.02)
        else:
            pytest.fail("Fixture readiness timed out")
        child_pid = int((state / "listener.pid").read_text())
        process.send_signal(signal.SIGTERM)
        out, err = process.communicate(timeout=7)
        assert process.returncode == 0
        assert "restart the API" in out
        assert KEY not in out + err and SECRET not in out + err
        assert not (state / "listener.pid").exists()
        with pytest.raises(ProcessLookupError):
            os.kill(child_pid, 0)
        assert (state / "listener.log").stat().st_mode & 0o777 == 0o600
        assert (state / "listener.log").stat().st_size <= M.MAX_LOG_BYTES
    finally:
        if process.poll() is None:
            process.send_signal(signal.SIGTERM)
            process.communicate(timeout=7)


@pytest.mark.parametrize("enabled", [True, False])
def test_checkout_enable_gate_is_preserved_for_real_local_contract(tmp_path, enabled):
    value = {**CONFIG, "live_checkout_enabled": enabled}
    path = private(tmp_path / "config.json", json.dumps(value))
    assert M.check_config(path, KEY) == value
    M.update_webhook_secret(path, KEY, SECRET)
    assert json.loads(path.read_text())["live_checkout_enabled"] is enabled


@pytest.mark.parametrize(
    "patch",
    [
        {"stripe_secret_key": "sk_live_" + "a" * 24},
        {"schema_version": "unsupported"},
        {"pro_price_id": "not-a-price"},
        {"live_checkout_enabled": "true"},
        {"checkout_success_url": "https://app.palschat.site/"},
        {"checkout_cancel_url": "https://app.palschat.site/"},
        {"checkout_cancel_url": "http://localhost:3000.attacker.example/"},
        {"checkout_success_url": "http://localhost:3000/#fragment"},
    ],
)
def test_config_rejects_live_keys_invalid_schema_and_nonlocal_redirects(
    tmp_path, patch
):
    path = private(tmp_path / "config.json", json.dumps({**CONFIG, **patch}))
    with pytest.raises(M.LocalStripeError):
        M.check_config(path, KEY)
    if "stripe_secret_key" in patch:
        with pytest.raises(M.LocalStripeError):
            M.check_config(path, patch["stripe_secret_key"])


def test_fifo_is_rejected_without_waiting_for_writer(tmp_path):
    fifo = tmp_path / "fifo"
    os.mkfifo(fifo, 0o600)
    runner = f"import runpy; m=runpy.run_path({str(SCRIPT)!r}); m['read_private'](__import__('pathlib').Path({str(fifo)!r}))"
    result = subprocess.run(
        [sys.executable, "-c", runner], capture_output=True, timeout=2, check=False
    )
    assert result.returncode != 0
    assert b"owned regular files" in result.stderr


def v2_config():
    value = {k: v for k, v in CONFIG.items() if k != "pro_price_id"}
    return {
        **value,
        "schema_version": "pals.billing-runtime.v2",
        "legacy_pro_price_id": "price_legacy",
        "price_ids": {p: "price_" + p for p in ("plus", "pro", "research")},
    }


@pytest.mark.parametrize("legacy", [None, "price_legacy"])
def test_v2_listener_update_preserves_closed_plan_mapping(tmp_path, legacy):
    value = {**v2_config(), "legacy_pro_price_id": legacy}
    path = private(tmp_path / "config.json", json.dumps(value))
    assert M.check_config(path, KEY) == value
    assert M.update_webhook_secret(path, KEY, SECRET)
    assert json.loads(path.read_text()) == {**value, "stripe_webhook_secret": SECRET}


@pytest.mark.parametrize(
    "patch",
    [
        {"price_ids": {"plus": "price_plus", "pro": "price_pro"}},
        {
            "price_ids": {
                "plus": "price_same",
                "pro": "price_same",
                "research": "price_research",
            }
        },
        {"legacy_pro_price_id": "price_plus"},
        {"price_ids": {"plus": None, "pro": "price_pro", "research": "price_research"}},
        {"pro_price_id": "price_old"},
        {
            "price_ids": {
                "plus": "price_plus",
                "pro": "price_pro",
                "research": "price_research",
                "unknown": "price_x",
            }
        },
    ],
)
def test_v2_listener_rejects_ambiguous_or_open_config(tmp_path, patch):
    path = private(tmp_path / "config.json", json.dumps({**v2_config(), **patch}))
    before = path.read_bytes()
    with pytest.raises(M.LocalStripeError):
        M.update_webhook_secret(path, KEY, SECRET)
    assert path.read_bytes() == before


def test_listener_rejects_duplicate_json_members(tmp_path):
    raw = json.dumps(v2_config()).replace(
        '"price_plus"', '"price_plus", "plus": "price_other"'
    )
    path = private(tmp_path / "config.json", raw)
    with pytest.raises(M.LocalStripeError, match="duplicate"):
        M.check_config(path, KEY)
