#!/usr/bin/env python3
"""Prepare five runtime SecureStrings from the existing Mini; Python 3.9+.

Default is a source-only, read-only plan. Only --apply writes SSM. --reconcile
reads SSM and resolves a previous uncertain write; it never writes SSM. Run on
the Mini with its existing SSO login. No credentials, values, value hashes,
fingerprints, raw command output or environment files are persisted/emitted.
An interrupted apply requires explicit reconciliation; there are no retries.
Writes are not a transaction: a failure can leave a verified subset in SSM.
--reconcile reports verified or reconciled_absent truthfully; only an explicit
later --apply can create parameters observed absent during reconciliation.
The metadata journal is ~/pals-mini-deploy/aws-migration-20261030/
runtime-secrets-receipt.json (0600). Never delete it to bypass reconciliation.
Secret puts use the existing trusted Homebrew AWS CLI interpreter's bundled SDK
in a fixed isolated child; JSON values travel only through ordinary stdin.
--probe-sdk-transport checks its import, fixed STS account and SSM metadata read;
it never puts a parameter. CLI/FIFO probes remain diagnostic only.
"""
from __future__ import annotations

import argparse
import configparser
import errno
import fcntl
import json
import os
import re
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

ACCOUNT = "828786775577"
REGION = "ap-northeast-1"
PROFILE = "pals-migration-operator"
ACTORS = {
    "api": "pals-mini-prod-webfix-20261004-api",
    "worker": "pals-mini-prod-20261004-worker",
    "assessment-worker": "pals-assessment-worker",
}
SPEC = {
    "PALS_GUEST_HASH_KEY": ("guest-hash-key", ("api",)),
    "PALS_WORKER_SHARED_SECRET": (
        "worker-shared-secret", ("api", "worker", "assessment-worker")
    ),
    "PALS_RECIPE_WORKER_SECRET": ("recipe-worker-secret", ("api", "worker")),
    "PALS_RECIPE_SEMANTIC_REVIEWER_SECRET": (
        "recipe-semantic-reviewer-secret", ("api",)
    ),
    "PALS_OPENAI_API_KEY": ("openai-api-key", ("worker", "assessment-worker")),
}
ALIASES = {
    "PALS_WORKER_SHARED_SECRET": ("PALS_AGENT_WORKER_SECRET",),
    "PALS_OPENAI_API_KEY": ("OPENAI_API_KEY",),
}
HEX = re.compile(r"[0-9a-f]{64}")
IMAGE = re.compile(r"sha256:[0-9a-f]{64}")
MAX_OUTPUT = 4 * 1024 * 1024
JOURNAL = "runtime-secrets-receipt.json"
DEADLINE = 0.0
LOCK_FD = None
LOCK_WAIT_SECONDS = 30.0
PHASE = "initialization"
SAFE_FAILURE_CODES = frozenset({
    "guard_rejected", "unsafe_path", "unsafe_parent", "not_private",
    "wrong_path_type", "file_too_large", "duplicate_member", "invalid_arguments",
    "lock_changed", "total_timeout", "command_timeout", "command_output_limit",
    "command_failed", "actor_mismatch", "pending_transition", "image_mismatch",
    "ambiguous_environment", "required_secret_absent", "invalid_secret",
    "alias_mismatch", "aws_config_too_large", "missing_fixed_profile",
    "cli_history_forbidden", "custom_aws_CA_forbidden", "cli_plugins_forbidden",
    "reconcile_required", "existing_value_differs", "controller_changed",
    "source_changed", "explicit_apply_required", "write_outcome_unverified",
    "incomplete_transfer",
    "wrong_account", "parameter_read_failed", "parameter_metadata_mismatch",
    "parameter_batch_response_invalid",
    "fifo_transport_failed",
    "sdk_interpreter_untrusted", "sdk_transport_failed",
})
# Diagnostic labels from AWS SSM PutParameter/CommonErrors documentation.
# A text match never establishes permissions, absence, success, or retry safety.
AWS_ERROR_CODES = frozenset({
    "AccessDeniedException", "ExpiredTokenException", "IncompleteSignature", "InternalFailure",
    "MalformedHttpRequestException", "NotAuthorized", "OptInRequired", "RequestAbortedException",
    "RequestEntityTooLargeException", "RequestTimeoutException", "ServiceUnavailable",
    "ThrottlingException", "UnknownOperationException", "UnrecognizedClientException", "ValidationError",
    "ValidationException", "HierarchyLevelLimitExceededException", "HierarchyTypeMismatchException",
    "IncompatiblePolicyException", "InternalServerError", "InvalidAllowedPatternException",
    "InvalidKeyId", "InvalidPolicyAttributeException", "InvalidPolicyTypeException", "ParameterAlreadyExists",
    "ParameterLimitExceeded", "ParameterMaxVersionLimitExceeded", "ParameterPatternMismatchException",
    "PoliciesLimitExceededException", "TooManyUpdates", "UnsupportedParameterType",
})


class GuardError(RuntimeError):
    """Only fixed internal labels; never include untrusted data."""


class Parser(argparse.ArgumentParser):
    def error(self, _message):
        raise GuardError("invalid_arguments")


def failure_summary(error):
    """Emit fixed diagnostic labels only; exception text may contain secrets."""
    code = "unexpected_failure"
    if isinstance(error, GuardError):
        code = error.args[0] if len(error.args) == 1 and isinstance(
            error.args[0], str
        ) and error.args[0] in SAFE_FAILURE_CODES else "guard_rejected"
    elif isinstance(error, BlockingIOError):
        code = "source_lock_busy"
    elif isinstance(error, FileNotFoundError):
        code = "required_path_absent"
    elif isinstance(error, PermissionError):
        code = "permission_denied"
    elif isinstance(error, json.JSONDecodeError):
        code = "invalid_json"
    elif isinstance(error, KeyError):
        code = "required_field_absent"
    result = {"status": "runtime_secret_transfer_failed", "phase": PHASE,
              "code": code,
              "action": "inspect_protected_receipt_and_explicitly_reconcile_before_retry"}
    exit_code = getattr(error, "aws_exit_code", None)
    if type(exit_code) is int and 0 <= exit_code <= 255:
        result["aws_exit_code"] = exit_code
        result["parameter_not_found_label"] = getattr(error, "parameter_not_found_label", False) is True
        result["ansi_formatting_present"] = getattr(error, "ansi_formatting_present", False) is True
    for key in ("stdin_device_unavailable", "parameter_file_error"):
        if hasattr(error, key):
            result[key] = getattr(error, key) is True
    for key in ("stdout_bytes", "stderr_bytes"):
        size = getattr(error, key, None)
        if type(size) is int and 0 <= size <= MAX_OUTPUT+65536:
            result[key] = size
    label = getattr(error, "aws_error_code", None)
    if label in AWS_ERROR_CODES | {"unclassified", "multiple_known_codes"}:
        result["aws_error_code"] = label
    sdk_stage = getattr(error, "sdk_stage", None)
    if sdk_stage in {"sdk_import", "input_validation", "sdk_config", "sdk_construction", "aws_identity", "ssm_metadata", "ssm_put"}:
        result["sdk_stage"] = sdk_stage
    return result


def require(condition, code="guard_rejected"):
    if not condition:
        raise GuardError(code)


def pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, "duplicate_member")
        result[key] = value
    return result


def decode(raw):
    return json.loads(raw, object_pairs_hook=pairs)


def protected(path, directory=False):
    require(path.is_absolute() and path.resolve(strict=True) == path, "unsafe_path")
    for parent in (path.parent, *path.parent.parents):
        info = parent.stat()
        require(info.st_uid in (0, os.geteuid()) and not (
            info.st_mode & 0o022 and not (
                info.st_uid == 0 and info.st_mode & stat.S_ISVTX
            )
        ), "unsafe_parent")
    flags = os.O_RDONLY | os.O_NOFOLLOW
    if directory:
        flags |= os.O_DIRECTORY
    fd = os.open(path, flags)
    info = os.fstat(fd)
    try:
        require(info.st_uid == os.geteuid() and not info.st_mode & 0o077,
                "not_private")
        require(stat.S_ISDIR(info.st_mode) if directory else (
            stat.S_ISREG(info.st_mode) and info.st_nlink == 1
        ), "wrong_path_type")
    except BaseException:
        os.close(fd)
        raise
    return fd


def read_json(path):
    fd = protected(path)
    try:
        before = os.fstat(fd)
        require(before.st_size <= 1024 * 1024, "file_too_large")
        raw = os.read(fd, 1024 * 1024 + 1)
        after = os.fstat(fd)
        require((before.st_ino, before.st_size, before.st_mtime_ns,
                 before.st_ctime_ns) == (after.st_ino, after.st_size,
                                        after.st_mtime_ns, after.st_ctime_ns))
        value = decode(raw)
        require(isinstance(value, dict))
        return value, raw
    finally:
        os.close(fd)


@contextmanager
def lock(path):
    global LOCK_FD
    fd = protected(path)
    try:
        original = os.fstat(fd)

        def verify():
            opened, named = os.fstat(fd), path.lstat()
            require(path.resolve(strict=True) == path and all(
                stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid()
                and not info.st_mode & 0o077 and info.st_nlink == 1
                and (info.st_dev,info.st_ino)==(original.st_dev,original.st_ino)
                for info in (opened,named)), "lock_changed")

        require(0 < LOCK_WAIT_SECONDS <= 30)
        until = min(DEADLINE, time.monotonic()+LOCK_WAIT_SECONDS)
        while True:
            verify()
            now = time.monotonic()
            require(now < DEADLINE, "total_timeout")
            if now >= until:
                raise BlockingIOError(errno.EAGAIN, "source_lock_busy")
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                time.sleep(min(0.1,max(0,until-time.monotonic())))
        LOCK_FD = fd
        verify()
        yield verify
        verify()
    finally:
        LOCK_FD = None
        os.close(fd)


def command(args, data=None):
    """Bounded pipes only: secret JSON never enters argv, files or stderr logs."""
    remaining = DEADLINE - time.monotonic()
    require(remaining > 0, "total_timeout")
    environment = {
        "HOME": str(Path.home()),
        "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
        "LANG": "C", "LC_ALL": "C", "AWS_PAGER": "",
        "AWS_CLI_AUTO_PROMPT": "off", "AWS_MAX_ATTEMPTS": "1",
        "AWS_RETRY_MODE": "standard", "AWS_EC2_METADATA_DISABLED": "true",
    }
    output = {"out": bytearray(), "err": bytearray()}
    with subprocess.Popen(
        args, stdin=subprocess.PIPE if data is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment,
        start_new_session=True, pass_fds=(() if LOCK_FD is None else (LOCK_FD,)),
    ) as child:
        try:
            until = time.monotonic() + min(30, remaining)
            with selectors.DefaultSelector() as selector:
                for stream, label in ((child.stdout, "out"), (child.stderr, "err")):
                    os.set_blocking(stream.fileno(), False)
                    selector.register(stream, selectors.EVENT_READ, label)
                pending = memoryview(data) if data is not None else None
                if pending is not None:
                    os.set_blocking(child.stdin.fileno(), False)
                    selector.register(child.stdin, selectors.EVENT_WRITE, "in")
                while selector.get_map():
                    require(time.monotonic() < until, "command_timeout")
                    for key, _events in selector.select(min(0.2, max(0, until-time.monotonic()))):
                        if key.data == "in":
                            written = os.write(key.fd, pending[:65536])
                            pending = pending[written:]
                            if not pending:
                                selector.unregister(key.fileobj)
                                key.fileobj.close()
                        else:
                            block = os.read(key.fd, 65536)
                            if not block:
                                selector.unregister(key.fileobj)
                            else:
                                output[key.data].extend(block)
                                require(len(output[key.data]) <= MAX_OUTPUT,
                                        "command_output_limit")
                child.wait(timeout=max(0.01, until-time.monotonic()))
            return child.returncode, bytes(output["out"]), bytes(output["err"])
        except GuardError as error:
            diagnose(error, bytes(output["out"]), bytes(output["err"]))
            raise
        finally:
            if child.poll() is None:
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                child.wait(timeout=5)


def successful(args):
    code, out, _err = command(args)
    require(code == 0, "command_failed")
    return decode(out)


def controller(root):
    p, p_raw = read_json(root / "controller-policy.json")
    c, c_raw = read_json(root / "deploy-config.json")
    require(p.get("schema_version") == "pals.macmini-host-controller.v1")
    require(p.get("runtime_profile") == "isolated-lean-v1")
    containers = p.get("containers", {})
    require(set(containers) == {"api", "web", "worker", "assessment-worker",
                                "verifier", "reconciler"})
    require(all(containers.get(k) == v for k, v in ACTORS.items()), "actor_mismatch")
    require(len(set(containers.values())) == 6)
    require(c.get("containers") == containers and c.get("state_dir") == p.get("state_dir")
            and c.get("docker_context") == p.get("docker_context"))
    state = Path(p["state_dir"])
    require(root in state.parents and state.resolve(strict=True) == state)
    os.close(protected(state, directory=True))
    current, raw = read_json(state / "current.json")
    require(current.get("status") == "healthy" and
            HEX.fullmatch(current.get("manifest_sha256", "")) and
            current.get("database_identity") == p.get("database_identity") and
            c.get("database_identity") == p.get("database_identity"))
    for name in ("normal-update-pending.json", "initial-runtime-pending.json"):
        require(not (state / name).exists() and not (state / name).is_symlink(),
                "pending_transition")
    docker = [p["docker_binary"], "--config", p["docker_config"],
              "--context", p["docker_context"]]
    require(Path(docker[0]).is_absolute() and Path(docker[2]).is_absolute())
    return state, current, docker, (p_raw, c_raw, raw)


def source(current, docker):
    items = successful(docker + ["inspect", *ACTORS.values()])
    require(isinstance(items, list) and len(items) == 3, "actor_mismatch")
    by_name = {x.get("Name"): x for x in items}
    require(set(by_name) == {"/" + x for x in ACTORS.values()}, "actor_mismatch")
    environments, identities = {}, {}
    for role, name in ACTORS.items():
        item = by_name["/" + name]
        state = item.get("State", {})
        component = "worker" if role == "assessment-worker" else role
        require(state.get("Running") is True and not any(
            state.get(k) for k in ("Paused", "Restarting", "Dead")))
        require(HEX.fullmatch(item.get("Id", "")) and
                IMAGE.fullmatch(item.get("Image", "")) and
                item["Image"] == current["images"][component], "image_mismatch")
        env = {}
        for entry in item["Config"]["Env"]:
            key, sep, value = entry.partition("=")
            require(sep and key not in env, "ambiguous_environment")
            env[key] = value
        require(env.get("PALS_ENV") == "prod")
        environments[role] = env
        identities[role] = (item["Id"], item["Image"])
    values = {}
    for key, (suffix, required_roles) in SPEC.items():
        observed = []
        for role, env in environments.items():
            if role in required_roles:
                require(key in env, "required_secret_absent")
            for candidate in (key, *ALIASES.get(key, ())):
                if candidate in env:
                    value = env[candidate]
                    require(isinstance(value, str) and 0 < len(value.encode()) <= 4096
                            and not any(ord(c) < 32 or ord(c) == 127 for c in value),
                            "invalid_secret")
                    observed.append(value)
        require(observed and all(x == observed[0] for x in observed), "alias_mismatch")
        values["/pals/prod/" + suffix] = observed[0]
    return values, identities


def arn(name):
    return "arn:aws:ssm:" + REGION + ":" + ACCOUNT + ":parameter" + name


def aws_cli_privacy():
    """CLI history can record parsed stdin values; refuse that configuration."""
    fd = protected(Path.home() / ".aws" / "config")
    try:
        require(os.fstat(fd).st_size <= 1024 * 1024, "aws_config_too_large")
        parser = configparser.ConfigParser(interpolation=None)
        parser.read_string(os.read(fd, 1024 * 1024 + 1).decode())
        require(parser.has_section("profile " + PROFILE), "missing_fixed_profile")
        for section in parser.sections():
            settings = parser[section]
            require(settings.get("cli_history", "disabled").strip().lower() == "disabled",
                    "cli_history_forbidden")
            require("ca_bundle" not in settings, "custom_aws_CA_forbidden")
            require(section != "plugins" or not settings, "cli_plugins_forbidden")
    finally:
        os.close(fd)


def transport_labels(err):
    """Diagnostic booleans only; never use stderr to permit a write/retry."""
    return {"stdin_device_unavailable": b"[Errno 6]" in err or b"Device not configured" in err,
            "parameter_file_error": b"paramfile" in err or b"Error parsing parameter" in err}


def diagnose(error, out, err):
    """Bounded output sizes and allowlisted diagnostic labels, never raw text."""
    error.stdout_bytes, error.stderr_bytes = len(out), len(err)
    matched = [code for code in sorted(AWS_ERROR_CODES) if re.search(
        rb"(?<![A-Za-z0-9_])"+code.encode()+rb"(?![A-Za-z0-9_])", err)]
    error.aws_error_code = matched[0] if len(matched) == 1 else "multiple_known_codes" if matched else "unclassified"
    for label, observed in transport_labels(err).items():
        setattr(error, label, observed)


def fifo_json(arguments, payload, directory):
    """Named FIFO: no regular secret file, argv value, shell, or CLI stdin open."""
    require(isinstance(payload, bytes) and 0 < len(payload) <= MAX_OUTPUT, "fifo_transport_failed")
    os.close(protected(directory, directory=True))
    path = directory/(".runtime-json-"+uuid4().hex)
    os.mkfifo(path, 0o600)
    original = path.lstat()
    require(stat.S_ISFIFO(original.st_mode) and stat.S_IMODE(original.st_mode) == 0o600
            and original.st_uid == os.geteuid() and original.st_nlink == 1, "fifo_transport_failed")
    stop = threading.Event()
    completed = threading.Event()
    failed = threading.Event()
    until = min(DEADLINE, time.monotonic()+30)

    def writer():
        fd = None
        try:
            while not stop.is_set() and time.monotonic() < until:
                try:
                    fd = os.open(path, os.O_WRONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
                    break
                except OSError as error:
                    if error.errno != errno.ENXIO:
                        raise
                    stop.wait(0.02)
            if fd is None:
                failed.set(); return
            info = os.fstat(fd)
            require(stat.S_ISFIFO(info.st_mode) and (info.st_dev, info.st_ino) ==
                    (original.st_dev, original.st_ino), "fifo_transport_failed")
            pending = memoryview(payload)
            while pending and not stop.is_set() and time.monotonic() < until:
                try:
                    pending = pending[os.write(fd, pending[:4096]):]
                except BlockingIOError:
                    stop.wait(0.02)
            (failed if pending else completed).set()
        except (OSError, GuardError):
            failed.set()
        finally:
            if fd is not None:
                os.close(fd)

    thread = threading.Thread(target=writer, name="runtime-json-fifo", daemon=True)
    thread.start()
    try:
        result = command(arguments+["--cli-input-json", "file://"+str(path)])
        if result[0] == 0:
            require(completed.is_set() and not failed.is_set(), "fifo_transport_failed")
        return result
    finally:
        stop.set(); thread.join(timeout=1)
        named = path.lstat()
        require(not thread.is_alive() and (named.st_dev, named.st_ino) ==
                (original.st_dev, original.st_ino), "fifo_transport_failed")
        path.unlink()


SDK_CHILD = r'''
import sys,json,logging
logging.disable(logging.CRITICAL)
stage='sdk_import'
try:
 from awscli.botocore.session import Session
 from awscli.botocore.config import Config
 stage='input_validation'
 def unique(items):
  result={}
  for key,value in items:
   if key in result: raise ValueError()
   result[key]=value
  return result
 raw=sys.stdin.buffer.read(32769)
 if not 0<len(raw)<=32768: raise ValueError()
 request=json.loads(raw,object_pairs_hook=unique)
 if not isinstance(request,dict): raise ValueError()
 operation=request.get('operation')
 names={'/pals/prod/guest-hash-key','/pals/prod/worker-shared-secret','/pals/prod/recipe-worker-secret','/pals/prod/recipe-semantic-reviewer-secret','/pals/prod/openai-api-key'}
 if operation in ('inspect','probe'):
  if set(request)!={'operation'}: raise ValueError()
 elif operation=='put':
  if set(request)!={'operation','Name','Value'} or request['Name'] not in names: raise ValueError()
  value=request['Value']
  if not isinstance(value,str) or not 0<len(value.encode())<=4096 or any(ord(c)<32 or ord(c)==127 for c in value): raise ValueError()
 else: raise ValueError()
 stage='sdk_config'
 config=Config(connect_timeout=5,read_timeout=5,retries={'max_attempts':1},signature_version='v4')
 if operation=='inspect':
  stage='sdk_construction'
  import socket
  def no_network(*args,**kwargs): raise RuntimeError()
  socket.socket.connect=no_network
  socket.getaddrinfo=no_network
  session=Session()
  for service in ('sts','ssm'):
   endpoint='https://'+service+'.ap-northeast-1.amazonaws.com'
   client=session.create_client(service,region_name='ap-northeast-1',endpoint_url=endpoint,use_ssl=True,verify=True,config=config,aws_access_key_id='synthetic-no-request-key',aws_secret_access_key='synthetic-no-request-value')
   if client.meta.endpoint_url!=endpoint or client.meta.config.retries.get('max_attempts')!=1: raise ValueError()
  print('{"status":"sdk_construction_verified","network_disabled":true,"max_attempts":1}')
 else:
  session=Session(profile='pals-migration-operator')
  stage='aws_identity'
  sts=session.create_client('sts',region_name='ap-northeast-1',endpoint_url='https://sts.ap-northeast-1.amazonaws.com',use_ssl=True,verify=True,config=config)
  if sts.get_caller_identity().get('Account')!='828786775577': raise ValueError()
  ssm=session.create_client('ssm',region_name='ap-northeast-1',endpoint_url='https://ssm.ap-northeast-1.amazonaws.com',use_ssl=True,verify=True,config=config)
  if ssm.meta.endpoint_url!='https://ssm.ap-northeast-1.amazonaws.com': raise ValueError()
  if operation=='probe':
   stage='ssm_metadata'
   response=ssm.describe_parameters(ParameterFilters=[{'Key':'Name','Option':'Equals','Values':['/pals/prod/guest-hash-key']}],MaxResults=5)
   found=response.get('Parameters')
   if not isinstance(found,list) or len(found)>1 or response.get('NextToken') or any(item.get('Name')!='/pals/prod/guest-hash-key' for item in found): raise ValueError()
   print('{"status":"sdk_probe_verified","account_verified":true,"endpoint_verified":true,"metadata_read_verified":true}')
  else:
   stage='ssm_put'
   response=ssm.put_parameter(Name=request['Name'],Value=request['Value'],Type='SecureString',Overwrite=False)
   if type(response.get('Version')) is not int or response['Version']!=1: raise ValueError()
   print('{"status":"sdk_put_verified","Version":1}')
except BaseException as error:
 response=getattr(error,'response',{})
 code=response.get('Error',{}).get('Code') if isinstance(response,dict) else None
 allowed=__ERROR_CODES__
 print(json.dumps({'status':'sdk_failed','stage':stage,'error_code':code if code in allowed else 'unclassified'}))
 sys.exit(2)
'''.replace('__ERROR_CODES__', repr(sorted(AWS_ERROR_CODES)))


def sdk_interpreter():
    """Use the already installed Homebrew AWS CLI SDK, never install/export."""
    candidate = shutil.which("aws", path="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin")
    require(candidate is not None, "sdk_interpreter_untrusted")
    script = Path(candidate).resolve(strict=True)
    require(re.fullmatch(r"/opt/homebrew/Cellar/awscli/[0-9]+\.[0-9]+\.[0-9]+(?:_[0-9]+)?/libexec/bin/aws",
                         str(script)), "sdk_interpreter_untrusted")
    def trusted_tool(path):
        require(path.resolve(strict=True) == path and path.is_file() and os.access(path, os.X_OK),
                "sdk_interpreter_untrusted")
        for selected in (path, *path.parents):
            if selected == Path('/opt/homebrew/Cellar'):
                break  # Existing Homebrew admin-owned Cellar can be0775.
            info = selected.stat()
            require(info.st_uid in (0, os.geteuid()) and not info.st_mode & 0o022,
                    "sdk_interpreter_untrusted")
    trusted_tool(script)
    with script.open('rb') as stream:
        shebang = stream.readline(512)
    expected = script.parent/'python'
    require(shebang == ('#!'+str(expected)+'\n').encode(), "sdk_interpreter_untrusted")
    interpreter = expected.resolve(strict=True)
    require(re.fullmatch(r'/opt/homebrew/Cellar/python(?:@[0-9]+\.[0-9]+)?/[0-9]+\.[0-9]+\.[0-9]+(?:_[0-9]+)?/.+',
                         str(interpreter)), "sdk_interpreter_untrusted")
    trusted_tool(interpreter)
    return str(expected)


def sdk_request(request):
    payload = json.dumps(request, ensure_ascii=True, separators=(',', ':')).encode()
    require(0 < len(payload) <= 32768, "sdk_transport_failed")
    code, out, err = command([sdk_interpreter(), '-I', '-B', '-c', SDK_CHILD], payload)
    try:
        result = decode(out)
    except (ValueError, UnicodeError, GuardError):
        result = None
    if code or not isinstance(result, dict) or result.get('status') == 'sdk_failed':
        failure = GuardError('write_outcome_unverified' if request.get('operation') == 'put' else 'sdk_transport_failed')
        failure.aws_exit_code = code
        diagnose(failure, out, err)
        if isinstance(result, dict) and set(result) == {'status','stage','error_code'}:
            failure.sdk_stage = result.get('stage')
            if result.get('error_code') in AWS_ERROR_CODES | {'unclassified'}:
                failure.aws_error_code = result['error_code']
        raise failure
    return result


class Parameters:
    def __init__(self, directory=None):
        self.directory = directory or Path.home()/"pals-mini-deploy/aws-migration-20261030"
        self.prefix = ["aws", "--profile", PROFILE, "--region", REGION,
                       "--output", "json", "--color", "off", "--no-cli-pager",
                       "--cli-connect-timeout", "10", "--cli-read-timeout", "20"]

    def identity(self):
        result = successful(self.prefix + ["--endpoint-url", "https://sts." + REGION +
                                          ".amazonaws.com", "sts", "get-caller-identity"])
        require(result.get("Account") == ACCOUNT, "wrong_account")

    def get(self, name):
        code, out, err = command(self.prefix + ["--endpoint-url", "https://ssm." + REGION +
                                                ".amazonaws.com", "ssm", "get-parameters", "--names", name,
                                                "--with-decryption"])
        if code:
            failure = GuardError("parameter_read_failed")
            failure.aws_exit_code = code
            diagnose(failure, out, err)
            raise failure
        try:
            response = decode(out)
        except (ValueError, UnicodeError, GuardError):
            raise GuardError("parameter_batch_response_invalid") from None
        require(isinstance(response, dict) and set(response) == {"Parameters", "InvalidParameters"}
                and isinstance(response["Parameters"], list) and isinstance(response["InvalidParameters"], list),
                "parameter_batch_response_invalid")
        if response["Parameters"] == [] and response["InvalidParameters"] == [name]:
            return None
        require(len(response["Parameters"]) == 1 and response["InvalidParameters"] == [],
                "parameter_batch_response_invalid")
        result = response["Parameters"][0]
        require(isinstance(result, dict), "parameter_batch_response_invalid")
        require(result.get("Name") == name and result.get("ARN") == arn(name)
                and result.get("Type") == "SecureString"
                and type(result.get("Version")) is int and result["Version"] >= 1
                and result.get("DataType", "text") == "text"
                and isinstance(result.get("Value"), str), "parameter_metadata_mismatch")
        return result

    def put(self, name, value):
        result = sdk_request({'operation':'put','Name':name,'Value':value})
        require(set(result) == {'status','Version'} and result['status'] == 'sdk_put_verified'
                and type(result.get("Version")) is int and result["Version"] == 1,
                "write_outcome_unverified")
        return result["Version"]

    def probe_sdk(self):
        result = sdk_request({'operation':'probe'})
        require(result == {'status':'sdk_probe_verified','account_verified':True,
                           'endpoint_verified':True,'metadata_read_verified':True}, 'sdk_transport_failed')
        return {**result,'service_write_attempted':False}

    def probe_transport(self, transport="both"):
        global PHASE
        require(transport in ("both", "stdin", "fifo"), "invalid_arguments")
        # --generate-cli-skeleton output validates inputs locally and sends no
        # service request. The payload is a fixed synthetic value, never source.
        payload = json.dumps({"Name": "/pals/prod/guest-hash-key", "Value": "synthetic-transport-probe",
                              "Type": "SecureString", "Overwrite": False}).encode()
        args = self.prefix+["--endpoint-url", "https://ssm."+REGION+".amazonaws.com", "ssm", "put-parameter",
                            "--generate-cli-skeleton", "output"]
        result = {"status": "cli_json_transport_probe", "service_write_attempted": False}
        for selected in ("stdin", "fifo"):
            if transport not in ("both", selected):
                continue
            PHASE = "cli_transport_probe_"+selected
            try:
                code, out, err = (command(args+["--cli-input-json", "file:///dev/stdin"], payload)
                                  if selected == "stdin" else fifo_json(args, payload, self.directory))
                observed = GuardError("command_failed")
                diagnose(observed, out, err)
                detail = failure_summary(observed)
                result[selected] = {"input_loaded": code == 0, "exit_code": code,
                                    **{key: detail[key] for key in ("stdout_bytes", "stderr_bytes", "aws_error_code",
                                       "stdin_device_unavailable", "parameter_file_error")}}
            except GuardError as error:
                detail = failure_summary(error)
                result[selected] = {"input_loaded": False, "failure_code": detail["code"],
                                    "phase": PHASE, **{key: detail[key] for key in ("stdout_bytes", "stderr_bytes",
                                    "aws_error_code", "stdin_device_unavailable", "parameter_file_error") if key in detail}}
        return result


def receipt(directory, value):
    """Replace metadata only, under the existing private directory and host lock."""
    fd = protected(directory, directory=True)
    tmp = ".runtime-secrets-" + uuid4().hex
    try:
        path = directory / JOURNAL
        if path.exists() or path.is_symlink():
            read_json(path)
        stream = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=fd)
        with os.fdopen(stream, "wb") as output:
            output.write(json.dumps(value, sort_keys=True).encode())
            output.flush()
            os.fsync(output.fileno())
        os.replace(tmp, JOURNAL, src_dir_fd=fd, dst_dir_fd=fd)
        os.fsync(fd)
    finally:
        os.close(fd)


def transfer(store, values, apply, reconcile, directory, recheck):
    path = directory / JOURNAL
    previous = read_json(path)[0] if path.exists() or path.is_symlink() else None
    if previous:
        require(previous.get("schema_version") == "pals.runtime-secrets-transfer.v1")
        require(reconcile or previous.get("status") in ("verified", "reconciled_absent"),
                "reconcile_required")
    store.identity()
    found = {}
    # A difference in the last parameter must prevent even the first put.
    for name, value in values.items():
        existing = store.get(name)
        require(existing is None or existing["Value"] == value, "existing_value_differs")
        found[name] = existing
    recheck()
    result = {"schema_version": "pals.runtime-secrets-transfer.v1",
              "account": ACCOUNT, "region": REGION, "status": "in_progress",
              "admission_eligible": False, "parameters": [], "pending_parameter": None}
    if not reconcile:
        require(apply, "explicit_apply_required")
    for name, value in values.items():
        existing = found[name]
        if existing is None and not reconcile:
            result.update(status="reconcile_required", pending_parameter=name)
            receipt(directory, result)
            recheck()
            version = store.put(name, value)
            existing = store.get(name)
            require(existing is not None and existing["Value"] == value and
                    existing["Version"] == version, "write_outcome_unverified")
            outcome = "created"
        else:
            outcome = "reconciled" if reconcile else "reused"
        if existing is not None:
            result["parameters"].append({"name": name, "arn": existing["ARN"],
                                         "version": existing["Version"], "outcome": outcome})
        result.update(status="in_progress", pending_parameter=None)
        receipt(directory, result)
    recheck()
    missing = [name for name in values if name not in
               {p["name"] for p in result["parameters"]}]
    require(not missing or reconcile, "incomplete_transfer")
    result.update(status="reconciled_absent" if missing else "verified",
                  missing_parameters=missing)
    receipt(directory, result)
    return result


def main(arguments=None):
    global DEADLINE, PHASE
    PHASE = "source_preflight"
    DEADLINE = time.monotonic() + 420
    parser = Parser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--reconcile", action="store_true")
    mode.add_argument("--probe-cli-transport", action="store_true")
    mode.add_argument("--probe-cli-transport-stdin", action="store_true")
    mode.add_argument("--probe-cli-transport-fifo", action="store_true")
    mode.add_argument("--probe-sdk-transport", action="store_true")
    args = parser.parse_args(arguments)
    root = Path.home() / "pals-mini-deploy"
    os.close(protected(root, directory=True))
    first = controller(root)
    with lock(first[0] / "host-update.lock") as verify_lock:
        _state, current, docker, binding = controller(root)
        require(binding == first[3], "controller_changed")
        values, identities = source(current, docker)

        def recheck():
            verify_lock()
            repeated = controller(root)
            require(repeated[3] == binding, "controller_changed")
            actual, ids = source(current, docker)
            require(actual == values and ids == identities, "source_changed")

        probing = args.probe_cli_transport or args.probe_cli_transport_stdin or args.probe_cli_transport_fifo or args.probe_sdk_transport
        if args.apply or args.reconcile or probing:
            PHASE = "receipt_directory_preflight"
            directory = root / "aws-migration-20261030"
            os.close(protected(directory, directory=True))
            PHASE = "aws_cli_privacy_preflight"
            aws_cli_privacy()
            if probing:
                if args.probe_sdk_transport:
                    PHASE = "sdk_transport_probe"
                    print(json.dumps(Parameters(directory).probe_sdk(),sort_keys=True))
                    return 0
                PHASE = "cli_transport_probe"
                selected = "stdin" if args.probe_cli_transport_stdin else "fifo" if args.probe_cli_transport_fifo else "both"
                print(json.dumps(Parameters(directory).probe_transport(selected), sort_keys=True))
                return 0
            PHASE = "ssm_reconciliation" if args.reconcile else "ssm_transfer"
            result = transfer(Parameters(), values, args.apply, args.reconcile,
                              directory, recheck)
            print(json.dumps({"status": result["status"],
                              "verified_parameter_count": len(result["parameters"]),
                              "admission_eligible": False}))
        else:
            recheck()
            print(json.dumps({"status": "plan_only_no_AWS_calls", "account": ACCOUNT,
                              "region": REGION, "profile": PROFILE,
                              "parameters": [{"name": name, "arn": arn(name)}
                                             for name in values],
                              "admission_eligible": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException as error:  # noqa: BLE001 -- fixed-label privacy boundary
        print(json.dumps(failure_summary(error)), file=sys.stderr)
        sys.exit(2)
