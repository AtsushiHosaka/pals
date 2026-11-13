#!/usr/bin/env python3
"""Build the single closed loopback Web variant from exact Git bytes; never start services."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tarfile
import time
from pathlib import Path

LOCAL_ARGS = {
    "NEXT_PUBLIC_PALS_API_BASE_URL": "http://localhost:58000",
    "NEXT_PUBLIC_COGNITO_USER_POOL_ID": "ap-northeast-1_local",
    "NEXT_PUBLIC_COGNITO_CLIENT_ID": "pals-local-acceptance",
    "NEXT_PUBLIC_COGNITO_ENDPOINT": "http://localhost:59229",
    "NEXT_PUBLIC_COGNITO_GOOGLE_ENABLED": "false",
    "NEXT_PUBLIC_COGNITO_HOSTED_UI_DOMAIN": "",
    "NEXT_PUBLIC_COGNITO_REDIRECT_URI": "http://localhost:53000",
    "NEXT_PUBLIC_COGNITO_LOGOUT_URI": "http://localhost:53000",
}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def need(ok, code):
    if not ok:
        raise ValueError(code)


def run(args, timeout=30):
    p = subprocess.run(args, capture_output=True, timeout=timeout, check=False)
    need(p.returncode == 0, "local_web_build_dependency_failed")
    return p.stdout


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha(path.read_bytes())}


def context_tree(archive, context):
    expected = {}
    with tarfile.open(archive) as t:
        for m in t.getmembers():
            if m.isfile():
                expected[m.name] = sha(t.extractfile(m).read())
            elif m.issym():
                expected[m.name] = "symlink:" + m.linkname
            else:
                need(m.isdir(), "unsupported_source_archive_member")
    actual = {}
    for p in context.rglob("*"):
        if p.is_symlink():
            actual[str(p.relative_to(context))] = "symlink:" + os.readlink(p)
        elif p.is_file():
            actual[str(p.relative_to(context))] = sha(p.read_bytes())
    need(actual == expected, "actual_build_context_differs_from_exact_git_archive")
    return sha(json.dumps(actual, sort_keys=True, separators=(",", ":")).encode())


def stored_build_record(path, context, code="real_build_record_changed"):
    """Frozen record with ``Context`` in canonical absolute form.

    ``docker buildx history inspect`` prints ``Context`` relative to the caller's working
    directory when the context lies below it. Receipts written from one directory then
    failed verification from another although nothing had changed. The observed value is
    resolved against the working directory it was printed for and must equal the frozen
    build context; a stored legacy relative value must be a trailing part of that same
    absolute context. Every other field is still compared exactly.
    """
    record = json.loads(Path(path).read_bytes())
    expected = Path(context).resolve()
    value = Path(record["Context"])
    if value.is_absolute():
        need(value.resolve() == expected, code)
    else:
        parts = value.parts
        need(
            parts and ".." not in parts and expected.parts[-len(parts) :] == parts,
            code,
        )
    record["Context"] = str(expected)
    return record


def observe_build(ref, context, revision, image):
    record = json.loads(
        run(["docker", "buildx", "history", "inspect", ref, "--format", "json"])
    )
    need(
        record["Status"] == "completed"
        and Path(record["Context"]).resolve() == context.resolve()
        and record["Dockerfile"] == "Dockerfile"
        and record["Platform"] == ["linux/arm64"],
        "actual_build_record_identity_changed",
    )
    args = {x["Name"]: x["Value"] for x in record["BuildArgs"]}
    # The Dockerfile has no default for this optional ARG; its effective public ENV is empty.
    args.setdefault("NEXT_PUBLIC_COGNITO_HOSTED_UI_DOMAIN", "")
    need(args == LOCAL_ARGS, "actual_build_args_not_closed_loopback_profile")
    labels = {x["Name"]: x["Value"] for x in record["Labels"]}
    need(
        labels.get("org.opencontainers.image.revision") == revision,
        "actual_build_source_label_changed",
    )
    need(
        any(
            x["Digest"] == image
            and x["Type"] == "application/vnd.oci.image.manifest.v1+json"
            for x in record["Attachments"]
        ),
        "actual_build_output_digest_changed",
    )
    # Identity was checked above against this caller's working directory; store and
    # compare the working-directory independent absolute form.
    record["Context"] = str(context.resolve())
    return record


def build(
    source_root, revision, archive, publication, production_args, expected_image, work
):
    need(
        len(revision) == 40 and all(x in "0123456789abcdef" for x in revision),
        "exact_source_required",
    )
    raw = run(["git", "-C", str(source_root), "archive", "--format=tar", revision])
    need(raw == archive.read_bytes(), "actual_git_archive_changed")
    pub = json.loads(publication.read_bytes())
    cfg_raw = production_args.read_bytes()
    cfg = json.loads(cfg_raw)
    need(
        pub["source_commit"] == revision and pub["source_archive_sha256"] == sha(raw),
        "production_source_binding_differs",
    )
    need(
        pub["build_args_sha256"] == sha(cfg_raw)
        and set(cfg) == set(LOCAL_ARGS)
        and all(type(v) is str for v in cfg.values()),
        "production_public_build_configuration_changed",
    )
    need(
        pub["platform"] == "linux/arm64"
        and pub["image_uri"].endswith("@" + pub["docker_image_id"]),
        "production_actual_image_required",
    )
    context = work / "context"
    context.mkdir(mode=0o700)
    with tarfile.open(archive) as t:
        t.extractall(context, filter="data")
    tree = context_tree(archive, context)
    dockerfile = (context / "Dockerfile").read_bytes()
    need(
        dockerfile
        == run(["git", "-C", str(source_root), "show", revision + ":Dockerfile"]),
        "actual_dockerfile_changed",
    )
    metadata = work / "build-metadata.json"
    tag = "pals-reliability-web:" + revision[:12] + "-local-verified"
    argv = [
        "docker",
        "buildx",
        "build",
        "--load",
        "--provenance=false",
        "--platform",
        "linux/arm64",
        "--metadata-file",
        str(metadata),
        "--label",
        "org.opencontainers.image.revision=" + revision,
        "--label",
        "codex.owner=01a1bb4b-dec2-76f0-a6fe-32405e465d6e",
    ]
    for key, value in LOCAL_ARGS.items():
        # Omitted empty ARG and an explicit empty ENV have the same fixed public value.
        # Preserve the original controlled local invocation exactly for cache reuse.
        if key != "NEXT_PUBLIC_COGNITO_HOSTED_UI_DOMAIN":
            argv.extend(["--build-arg", key + "=" + value])
    argv.extend(["-t", tag, str(context)])
    with (work / "build.log").open("xb") as log:
        p = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT)
        started = time.monotonic()
        try:
            while p.poll() is None:
                try:
                    p.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    need(time.monotonic() - started < 600, "local_web_build_timeout")
            need(p.returncode == 0, "controlled_local_web_build_failed")
        except BaseException:
            p.terminate()
            p.wait(timeout=10)
            raise
    actual = json.loads(run(["docker", "image", "inspect", tag]))[0]
    meta = json.loads(metadata.read_bytes())
    need(
        meta["containerimage.digest"] == actual["Id"],
        "actual_build_metadata_image_differs",
    )
    if expected_image:
        need(
            actual["Id"] == expected_image,
            "controlled_build_did_not_reproduce_running_image",
        )
    need(
        actual["Os"] + "/" + actual["Architecture"] == "linux/arm64"
        and actual["Config"]["Labels"]["org.opencontainers.image.revision"] == revision,
        "controlled_build_identity_mismatch",
    )
    need(tree == context_tree(archive, context), "build_context_changed_during_build")
    ref = meta["buildx.build.ref"].split("/")[-1]
    observed = observe_build(ref, context, revision, actual["Id"])
    record_file = work / "actual-build-record.json"
    record_file.write_text(
        json.dumps(observed, sort_keys=True, separators=(",", ":")) + "\n"
    )
    return {
        "schema_version": "pals.local-web-build.v1",
        "source_root": str(source_root.resolve()),
        "source_revision": revision,
        "source_archive": reference(archive),
        "production_publication": reference(publication),
        "production_public_args": reference(production_args),
        "dockerfile_sha256": sha(dockerfile),
        "local_build_args": LOCAL_ARGS,
        "built_image_id": actual["Id"],
        "platform": "linux/arm64",
        "build_metadata": reference(metadata),
        "build_record": reference(record_file),
        "build_record_ref": ref,
        "build_context": str(context.resolve()),
        "context_tree_sha256": tree,
        "builder_sha256": sha(Path(__file__).read_bytes()),
        "rootfs_diff_ids": actual["RootFS"]["Layers"],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-root", type=Path)
    p.add_argument("--revision")
    p.add_argument("--source-archive", type=Path)
    p.add_argument("--production-publication", type=Path)
    p.add_argument("--production-public-args", type=Path)
    p.add_argument("--expected-image-id")
    p.add_argument("--output-dir", type=Path)
    p.add_argument("--verify-receipt", type=Path)
    a = p.parse_args()
    if a.verify_receipt:
        previous = json.loads(a.verify_receipt.read_bytes())
        need(
            previous["builder_sha256"] == sha(Path(__file__).read_bytes()),
            "frozen_builder_changed",
        )
        for key in (
            "source_archive",
            "production_publication",
            "production_public_args",
            "build_metadata",
            "build_record",
        ):
            need(
                reference(Path(previous[key]["path"])) == previous[key],
                "frozen_build_input_changed",
            )
        archive = Path(previous["source_archive"]["path"])
        source = run(
            [
                "git",
                "-C",
                previous["source_root"],
                "archive",
                "--format=tar",
                previous["source_revision"],
            ]
        )
        need(source == archive.read_bytes(), "actual_source_git_archive_changed")
        need(
            previous["context_tree_sha256"]
            == context_tree(archive, Path(previous["build_context"])),
            "frozen_build_context_changed",
        )
        need(previous["local_build_args"] == LOCAL_ARGS, "local_public_args_changed")
        need(
            sha((Path(previous["build_context"]) / "Dockerfile").read_bytes())
            == previous["dockerfile_sha256"],
            "frozen_dockerfile_changed",
        )
        observed = observe_build(
            previous["build_record_ref"],
            Path(previous["build_context"]),
            previous["source_revision"],
            previous["built_image_id"],
        )
        need(
            stored_build_record(
                previous["build_record"]["path"], previous["build_context"]
            )
            == observed,
            "real_build_record_changed",
        )
        actual = json.loads(
            run(["docker", "image", "inspect", previous["built_image_id"]])
        )[0]
        need(
            actual["RootFS"]["Layers"] == previous["rootfs_diff_ids"]
            and actual["Os"] + "/" + actual["Architecture"] == previous["platform"],
            "actual_built_image_changed",
        )
        print(json.dumps({"state": "verified_actual_build", "image_id": actual["Id"]}))
        return
    need(
        all(
            (
                a.source_root,
                a.revision,
                a.source_archive,
                a.production_publication,
                a.production_public_args,
                a.output_dir,
            )
        ),
        "all_build_inputs_required",
    )
    a.output_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
    receipt = build(
        a.source_root,
        a.revision,
        a.source_archive,
        a.production_publication,
        a.production_public_args,
        a.expected_image_id,
        a.output_dir,
    )
    out = a.output_dir / "provenance.json"
    out.write_text(json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n")
    out.chmod(0o600)
    print(
        json.dumps(
            {
                "state": "built_exact_local_variant",
                "receipt": reference(out),
                "image_id": receipt["built_image_id"],
            }
        )
    )


if __name__ == "__main__":
    main()
