"""Read-only process metadata for both fixed production update locks.

Never prints private commands, paths, environment, configuration or credentials.
"""
import json
import os
import re
import stat
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path('/Users/hosakaatsushi/pals-mini-deploy')


def owner_summary(pid, raw):
    values = raw.split(None, 3)
    if len(values) != 4 or not all(re.fullmatch(r'[0-9]{1,10}', value) for value in values[:2]):
        return {'pid': pid, 'status': 'unavailable'}
    elapsed, command = values[2:]
    if not re.fullmatch(r'(?:[0-9]{1,9}-)?[0-9]{1,9}:[0-9]{2}(?::[0-9]{2})?', elapsed):
        return {'pid': pid, 'status': 'unavailable'}
    days, _, clock = elapsed.rpartition('-')
    seconds = int(days or 0) * 86400
    for value, weight in zip(reversed(clock.split(':')), (1, 60, 3600)):
        seconds += int(value) * weight
    is_deployer = bool(re.search(r'(?:^|\s)(?:\S*/)?pals-scripts/deploy-macmini\.py(?:\s|$)', command))
    revision = re.search(r'(?:^|\s)--revision\s+([0-9a-f]{40})(?:\s|$)', command) if is_deployer else None
    return {'pid': pid, 'parent_pid': int(values[0]), 'process_group': int(values[1]),
            'elapsed_seconds': seconds, 'command_mentions_deployer': is_deployer,
            'command_mentions_preflight_only': is_deployer and '--preflight-only' in command.split(),
            'claimed_revision': revision.group(1) if revision else None}


def inspect_lock(state, name):
    if name not in {'deploy.lock', 'host-update.lock'}:
        return {'status': 'unavailable', 'code': 'unsupported_lock'}
    path = state / name
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return {'status': 'missing', 'code': 'lock_file_missing'}
    except OSError:
        return {'status': 'unavailable', 'code': 'lock_metadata_unavailable'}
    if not (stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1
            and metadata.st_uid == os.geteuid() and stat.S_IMODE(metadata.st_mode) == 0o600):
        return {'status': 'unavailable', 'code': 'lock_metadata_invalid'}
    # lsof emits only PIDs; no lock is acquired, replaced, removed or released.
    deadline = time.monotonic() + 15
    try:
        result = subprocess.run(['/usr/sbin/lsof', '-t', '--', str(path)],
                                capture_output=True, timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return {'status': 'unavailable', 'code': 'lsof_unavailable'}
    if len(result.stdout) + len(result.stderr) > 65536:
        return {'status': 'unavailable', 'code': 'lsof_output_limit'}
    if result.stderr:
        return {'status': 'unavailable', 'code': 'lsof_stderr_present'}
    if result.returncode not in (0, 1):
        return {'status': 'unavailable', 'code': 'lsof_failed'}
    if result.returncode == 1 and result.stdout.strip():
        return {'status': 'unavailable', 'code': 'lsof_inconsistent_result'}
    try:
        ids = result.stdout.decode('ascii').split()
    except UnicodeDecodeError:
        return {'status': 'unavailable', 'code': 'lsof_invalid_pids'}
    if len(ids) > 128 or any(not re.fullmatch(r'[0-9]{1,10}', pid) for pid in ids):
        return {'status': 'unavailable', 'code': 'lsof_invalid_pids'}
    owners = []
    for pid in sorted({int(value) for value in ids}):
        if pid <= 0:
            return {'status': 'unavailable', 'code': 'lsof_invalid_pids'}
        try:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                owners.append({'pid': pid, 'status': 'unavailable'})
                continue
            result = subprocess.run(['/bin/ps', '-p', str(pid), '-o', 'ppid=,pgid=,etime=,command='],
                                    capture_output=True, timeout=min(5, remaining), check=False)
            owners.append(owner_summary(pid, result.stdout.decode('utf-8', errors='replace'))
                          if result.returncode == 0 and not result.stderr
                          and len(result.stdout) + len(result.stderr) <= 65536
                          else {'pid': pid, 'status': 'unavailable'})
        except (OSError, subprocess.TimeoutExpired):
            owners.append({'pid': pid, 'status': 'unavailable'})
    try:
        after = path.lstat()
    except OSError:
        return {'status': 'unavailable', 'code': 'lock_changed_during_inspection'}
    if (after.st_dev, after.st_ino, after.st_mode, after.st_uid, after.st_nlink) != (
            metadata.st_dev, metadata.st_ino, metadata.st_mode, metadata.st_uid, metadata.st_nlink):
        return {'status': 'unavailable', 'code': 'lock_changed_during_inspection'}
    return {'status': 'observed-lock-openers', 'read_only': True,
            'empty_openers_observed': not owners, 'processes': owners}


def main():
    if sys.platform != 'darwin' or os.geteuid() == 0:
        return {'status': 'unavailable', 'code': 'unsupported_host'}
    config = json.loads((ROOT / 'deploy-config.json').read_bytes())
    policy = json.loads((ROOT / 'controller-policy.json').read_bytes())
    state = Path(config['state_dir'])
    if state != Path(policy['state_dir']) or not state.is_absolute():
        return {'status': 'unavailable', 'code': 'state_directory_mismatch'}
    return {'status': 'lock-diagnostics', 'read_only': True,
            'pending_update_present': (state / 'normal-update-pending.json').exists(),
            'locks': {name: inspect_lock(state, name) for name in ('deploy.lock', 'host-update.lock')}}


if __name__ == '__main__':
    try:
        print(json.dumps(main()))
    except Exception:
        print(json.dumps({'status': 'unavailable', 'code': 'lock_inspection_unavailable'}))
