#!/usr/bin/env python3
"""Same-source native verifier artifact; architecture/dependency resolution differs from prod."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import tarfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "local_web_build", HERE / "local-web-build.py"
)
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)
sha, need, run, reference = common.sha, common.need, common.run, common.reference
spec = importlib.util.spec_from_file_location(
    "local_verifier_archives", HERE / "local-verifier-archives.py"
)
archives = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archives)
SCHEMA = "pals.local-verifier-build.v2"
PLAN_ARCHIVES_DIFFER = "native_plan_archive_differs_from_the_built_commit"
LEAN = "leanprover/lean4:v4.32.0-rc1"
LAKE = "290f048c4a499d34a3b21f8db30ade48a2b8d05b0fe79709f1868fa6748944fa"


def probe(image):
    code = "import sys,json,hashlib,subprocess,importlib.metadata as m;from pathlib import Path;p=Path('/app/lean-workspace');print(json.dumps({'python':sys.version.split()[0],'packages':{d.metadata['Name']:d.version for d in m.distributions()},'lean_toolchain':(p/'lean-toolchain').read_text().strip(),'lake_manifest_sha256':hashlib.sha256((p/'lake-manifest.json').read_bytes()).hexdigest(),'lean_version':subprocess.check_output(['lean','--version'],cwd=p,text=True,timeout=15).strip()}))"
    result = json.loads(
        run(
            [
                "docker",
                "run",
                "--rm",
                "--read-only",
                "--network",
                "none",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges:true",
                "--user",
                "65532:65532",
                "--label",
                "codex.owner=01a1bb4b-dec2-76f0-a6fe-32405e465d6e",
                "--entrypoint",
                "python",
                image,
                "-c",
                code,
            ]
        )
    )
    need(
        result["lean_toolchain"] == LEAN
        and result["lake_manifest_sha256"] == LAKE
        and "aarch64" in result["lean_version"],
        "actual_native_compiler_library_pin_changed",
    )
    return result


def observe(ref, context, revision, image):
    record = json.loads(
        run(["docker", "buildx", "history", "inspect", ref, "--format", "json"])
    )
    need(
        record["Status"] == "completed"
        and Path(record["Context"]).resolve() == context.resolve()
        and record["Dockerfile"] == "docker/lean-verifier.Dockerfile"
        and record["Platform"] == ["linux/arm64"]
        and not record.get("BuildArgs"),
        "actual_native_build_record_changed",
    )
    need(
        {x["Name"]: x["Value"] for x in record["Labels"]}.get(
            "org.opencontainers.image.revision"
        )
        == revision,
        "actual_native_source_label_changed",
    )
    need(
        any(
            x["Digest"] == image
            and x["Type"] == "application/vnd.oci.image.manifest.v1+json"
            for x in record["Attachments"]
        ),
        "actual_native_build_output_changed",
    )
    # See local-web-build.stored_build_record: the printed value depends on the cwd.
    record["Context"] = str(context.resolve())
    return record


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-root", type=Path)
    p.add_argument("--revision")
    p.add_argument("--source-archive", type=Path)
    p.add_argument("--output-dir", type=Path)
    p.add_argument("--verify-receipt", type=Path)
    a = p.parse_args()
    if a.verify_receipt:
        old = json.loads(a.verify_receipt.read_bytes())
        need(
            old.get("schema_version") == SCHEMA
            and old["builder_sha256"] == sha(Path(__file__).read_bytes())
            and old["context_checker_sha256"]
            == sha((HERE / "local-web-build.py").read_bytes())
            and old["archive_checker_sha256"]
            == sha((HERE / "local-verifier-archives.py").read_bytes()),
            "native_builder_changed",
        )
        for key in (
            "build_archive",
            "source_archive",
            "recipe_archive",
            "build_metadata",
            "build_record",
        ):
            need(
                reference(Path(old[key]["path"])) == old[key],
                "native_frozen_artifact_changed",
            )
        archive = Path(old["build_archive"]["path"])
        # Both plan archives are re-derived from git at the commit and compared, member
        # by member, with the complete archive this image was built from.
        try:
            archives.verify(
                old["source_root"],
                old["source_revision"],
                archive,
                {name: old[name] for name in archives.PROJECTIONS},
                PLAN_ARCHIVES_DIFFER,
            )
        except ValueError:
            raise ValueError(PLAN_ARCHIVES_DIFFER) from None
        need(
            run(
                [
                    "git",
                    "-C",
                    old["source_root"],
                    "archive",
                    "--format=tar",
                    old["source_revision"],
                ]
            )
            == archive.read_bytes(),
            "native_exact_git_source_changed",
        )
        need(
            common.context_tree(archive, Path(old["build_context"]))
            == old["context_tree_sha256"],
            "native_build_context_changed",
        )
        need(
            observe(
                old["build_record_ref"],
                Path(old["build_context"]),
                old["source_revision"],
                old["built_image_id"],
            )
            == common.stored_build_record(
                old["build_record"]["path"],
                old["build_context"],
                "native_actual_build_record_changed",
            ),
            "native_actual_build_record_changed",
        )
        need(
            probe(old["built_image_id"]) == old["actual_image_probe"],
            "native_actual_compiler_or_dependencies_changed",
        )
        print(
            json.dumps(
                {
                    "state": "verified_actual_native_build",
                    "image_id": old["built_image_id"],
                }
            )
        )
        return
    need(
        all((a.source_root, a.revision, a.source_archive, a.output_dir)),
        "native_build_inputs_required",
    )
    raw = a.source_archive.read_bytes()
    need(
        raw
        == run(
            ["git", "-C", str(a.source_root), "archive", "--format=tar", a.revision]
        ),
        "native_exact_git_archive_changed",
    )
    a.output_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
    # The release plan pins two partial archives of this commit; the image needs more
    # files than they hold. Derive both now and prove them against the complete archive
    # before anything is built from it.
    projections = archives.derive(
        a.source_root, a.revision, a.source_archive, a.output_dir
    )
    context = a.output_dir / "context"
    context.mkdir(mode=0o700)
    with tarfile.open(a.source_archive) as t:
        t.extractall(context, filter="data")
    tree = common.context_tree(a.source_archive, context)
    dockerfile = context / "docker/lean-verifier.Dockerfile"
    need(
        dockerfile.read_bytes()
        == run(
            [
                "git",
                "-C",
                str(a.source_root),
                "show",
                a.revision + ":docker/lean-verifier.Dockerfile",
            ]
        ),
        "native_exact_dockerfile_changed",
    )
    need(
        (context / "lean-workspace/lean-toolchain").read_text().strip() == LEAN
        and sha((context / "lean-workspace/lake-manifest.json").read_bytes()) == LAKE,
        "native_source_toolchain_changed",
    )
    metadata = a.output_dir / "build-metadata.json"
    tag = "pals-reliability-verifier:" + a.revision[:12] + "-native-verified"
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
        "org.opencontainers.image.revision=" + a.revision,
        "--label",
        "codex.owner=01a1bb4b-dec2-76f0-a6fe-32405e465d6e",
        "-f",
        str(dockerfile),
        "-t",
        tag,
        str(context),
    ]
    with (a.output_dir / "build.log").open("xb") as log:
        process = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT)
        started = time.monotonic()
        try:
            while process.poll() is None:
                try:
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    need(
                        time.monotonic() - started < 1800,
                        "native_build_deadline_exceeded",
                    )
            need(process.returncode == 0, "native_build_failed")
        except BaseException:
            process.terminate()
            process.wait(timeout=10)
            raise
    image = json.loads(run(["docker", "image", "inspect", tag]))[0]
    meta = json.loads(metadata.read_bytes())
    need(
        image["Id"] == meta["containerimage.digest"]
        and image["Architecture"] == "arm64"
        and image["Config"]["Labels"]["org.opencontainers.image.revision"]
        == a.revision,
        "actual_native_built_image_changed",
    )
    need(
        tree == common.context_tree(a.source_archive, context),
        "native_context_changed_during_build",
    )
    ref = meta["buildx.build.ref"].split("/")[-1]
    record = a.output_dir / "actual-build-record.json"
    record.write_text(
        json.dumps(
            observe(ref, context, a.revision, image["Id"]),
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )
    receipt = {
        "schema_version": SCHEMA,
        "source_root": str(a.source_root.resolve()),
        "source_revision": a.revision,
        # What the image was built from: the complete archive of the commit.
        "build_archive": reference(a.source_archive),
        # What the release plan pins: `git archive <commit> pals_agent` and
        # `git archive <commit> docker/lean-verifier.Dockerfile lean-workspace`.
        "source_archive": reference(projections["source_archive"]),
        "recipe_archive": reference(projections["recipe_archive"]),
        "plan_archive_paths": {k: list(v) for k, v in archives.PROJECTIONS.items()},
        "dockerfile_sha256": sha(dockerfile.read_bytes()),
        "lean_version": LEAN,
        "lake_manifest_sha256": LAKE,
        "built_image_id": image["Id"],
        "platform": "linux/arm64",
        "build_context": str(context.resolve()),
        "context_tree_sha256": tree,
        "build_metadata": reference(metadata),
        "build_record": reference(record),
        "build_record_ref": ref,
        "builder_sha256": sha(Path(__file__).read_bytes()),
        "context_checker_sha256": sha((HERE / "local-web-build.py").read_bytes()),
        "archive_checker_sha256": sha(
            (HERE / "local-verifier-archives.py").read_bytes()
        ),
        "actual_image_probe": probe(image["Id"]),
        "difference_scope": "native ARM64 and actual resolver/dependency versions; same exact source/Dockerfile/Lean/Mathlib; not production byte equivalence",
    }
    out = a.output_dir / "provenance.json"
    out.write_text(json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n")
    out.chmod(0o600)
    print(
        json.dumps(
            {
                "state": "built_real_native_verifier",
                "receipt": reference(out),
                "image_id": image["Id"],
            }
        )
    )


if __name__ == "__main__":
    main()
