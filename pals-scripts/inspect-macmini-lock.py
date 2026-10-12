"""Read-only process metadata for the fixed production deployment lock.

Never prints private commands, paths, environment, configuration or credentials.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path('/Users/hosakaatsushi/pals-mini-deploy')


def owner_summary(pid, raw):
    values = raw.split(None, 3)
    if len(values) != 4 or not all(value.isascii() and value.isdecimal() for value in values[:2]):
        return {'pid': pid, 'status': 'unavailable'}
    elapsed, command = values[2:]
    if not re.fullmatch(r'(?:[0-9]+-)?[0-9]+:[0-9]{2}(?::[0-9]{2})?', elapsed):
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


def main():
    if sys.platform != 'darwin' or os.geteuid() == 0:
        return {'status': 'unavailable'}
    config = json.loads((ROOT / 'deploy-config.json').read_bytes())
    policy = json.loads((ROOT / 'controller-policy.json').read_bytes())
    state = Path(config['state_dir'])
    if state != Path(policy['state_dir']) or not state.is_absolute():
        return {'status': 'unavailable'}
    # lsof emits only PIDs; no lock is acquired, replaced, removed or released.
    result = subprocess.run(['/usr/sbin/lsof', '-t', '--', str(state / 'deploy.lock')],
                            capture_output=True, timeout=5, check=False)
    if len(result.stdout) > 65536 or result.returncode not in (0, 1):
        return {'status': 'unavailable'}
    ids = result.stdout.decode('ascii').split()
    if len(ids) > 128 or any(not re.fullmatch(r'[0-9]{1,10}', pid) for pid in ids):
        return {'status': 'unavailable'}
    owners = []
    for pid in sorted({int(value) for value in ids}):
        if pid <= 0:
            return {'status': 'unavailable'}
        result = subprocess.run(['/bin/ps', '-p', str(pid), '-o', 'ppid=,pgid=,etime=,command='],
                                capture_output=True, timeout=5, check=False)
        owners.append(owner_summary(pid, result.stdout.decode('utf-8', errors='replace'))
                      if result.returncode == 0 and len(result.stdout) <= 65536
                      else {'pid': pid, 'status': 'unavailable'})
    return {'status': 'observed-lock-openers', 'read_only': True,
            'pending_update_present': (state / 'normal-update-pending.json').exists(),
            'processes': owners}


if __name__ == '__main__':
    try:
        print(json.dumps(main()))
    except Exception:
        print(json.dumps({'status': 'unavailable'}))
