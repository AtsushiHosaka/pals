#!/usr/bin/env python3
"""Allow only the requested SHA that is still the fixed parent repository's main.

Explicitly selects saved host gh login or the step-only PALS_MAIN_READ_TOKEN.
Never changes the checkout or chooses a replacement revision. Prints only
current/superseded. GitHub/API errors fail closed with a code-owned diagnostic.
"""

from __future__ import annotations

import argparse
import http.client
import importlib.util
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "macmini_checkout_auth", Path(__file__).with_name("checkout-macmini-submodules.py")
)
assert SPEC is not None and SPEC.loader is not None
checkout = importlib.util.module_from_spec(SPEC)
previous_bytecode = sys.dont_write_bytecode
sys.dont_write_bytecode = True
try:
    SPEC.loader.exec_module(checkout)
finally:
    sys.dont_write_bytecode = previous_bytecode

SHA = re.compile(r"[0-9a-f]{40}\Z")
MAIN_REF = "refs/heads/main"
MAIN_ENDPOINT = "repos/AtsushiHosaka/pals/git/ref/heads/main"
MAIN_API_URL = "https://api.github.com/" + MAIN_ENDPOINT


class MainCheckError(ValueError):
    """Invalid inputs or an unverified current parent main."""


def unique_members(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise MainCheckError("Duplicate GitHub response member.")
        result[key] = value
    return result


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, stream, code, message, headers, new_url):
        return None


def token_response(environment: dict[str, str]) -> str:
    token = environment.get("PALS_MAIN_READ_TOKEN", "")
    if (
        not isinstance(token, str)
        or not 0 < len(token) <= 4096
        or any(not 33 <= ord(character) <= 126 for character in token)
    ):
        raise MainCheckError("An explicit step-only main read token is required.")
    # No proxy, redirect, saved login, SDK credential chain or credential file.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    request = urllib.request.Request(
        MAIN_API_URL,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "pals-macmini-main-guard",
        },
        method="GET",
    )
    with opener.open(request, timeout=30) as response:
        if response.getcode() != 200 or response.geturl() != MAIN_API_URL:
            raise MainCheckError("The fixed GitHub main request was not successful.")
        content = response.read(65537)
    if len(content) > 65536:
        raise MainCheckError("Invalid GitHub main response.")
    return content.decode("utf-8")


def check_main(revision: str, environment: dict[str, str], *, auth: str) -> str:
    if not isinstance(revision, str) or SHA.fullmatch(revision) is None:
        raise MainCheckError("A full requested parent SHA is required.")
    if auth == "host-gh":
        response = checkout.capture(
            [
                checkout.GH,
                "api",
                "--hostname",
                "github.com",
                "--method",
                "GET",
                MAIN_ENDPOINT,
            ],
            checkout.checkout_environment(environment),
            timeout=30,
        )
    elif auth == "repository-token":
        response = token_response(environment)
    else:
        raise MainCheckError("An explicit supported authentication mode is required.")
    if not 0 < len(response) <= 65536:
        raise MainCheckError("Invalid GitHub main response.")
    try:
        value = json.loads(response, object_pairs_hook=unique_members)
    except (ValueError, RecursionError) as error:
        raise MainCheckError("Invalid GitHub main response.") from error
    if not isinstance(value, dict) or value.get("ref") != MAIN_REF:
        raise MainCheckError("GitHub did not confirm the fixed main ref.")
    target = value.get("object")
    if (
        not isinstance(target, dict)
        or target.get("type") != "commit"
        or not isinstance(target.get("sha"), str)
        or SHA.fullmatch(target["sha"]) is None
    ):
        raise MainCheckError("GitHub did not confirm a full main commit SHA.")
    return "current" if target["sha"] == revision else "superseded"


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", required=True)
    parser.add_argument(
        "--auth", choices=("host-gh", "repository-token"), required=True
    )
    args = parser.parse_args(arguments)
    try:
        status = check_main(args.revision, dict(os.environ), auth=args.auth)
    except (
        MainCheckError,
        checkout.CheckoutError,
        OSError,
        subprocess.SubprocessError,
        http.client.HTTPException,
        UnicodeError,
    ):
        print("Mac mini main check failed; deployment is blocked.", file=sys.stderr)
        return 1
    print(status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
