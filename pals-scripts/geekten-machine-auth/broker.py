"""Geekten-only host STS broker with verified, atomic leaf certificate renewal."""
from __future__ import annotations
import argparse
from datetime import UTC, datetime, timedelta
import fcntl
import json
import os
from pathlib import Path
import stat
import subprocess
import secrets
import tempfile
import time

ACCOUNT = '828786775577'
REGION = 'ap-northeast-1'
ROOT = Path('/Users/hosakaatsushi/pals-geekten-20261026')
ROLES = {'api': ('pals-geekten-api', 'pals-geekten-api'),
         'worker': ('pals-geekten-worker', 'pals-mini-worker'),
         'assessment-worker': ('pals-geekten-assessment-worker', 'pals-mini-worker'),
         'reconciler': ('pals-geekten-reconciler', 'pals-geekten-reconciler')}


def private(path: Path):
    if path.is_symlink() or not path.is_dir() or path.stat().st_uid != os.geteuid() or path.stat().st_mode & 0o077:
        raise ValueError('Private directory required')


def private_file(path: Path):
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or info.st_mode & 0o077:
        raise ValueError('Private regular file required')


def atomic(directory: Path, name: str, data: dict):
    private(directory)
    temporary = directory / ('.' + name + '.' + str(os.getpid()))
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(data, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, directory / name)
    finally:
        temporary.unlink(missing_ok=True)


def check_credentials(record, *, now):
    if set(record) != {'Version', 'AccessKeyId', 'SecretAccessKey', 'SessionToken', 'Expiration'} or record['Version'] != 1:
        raise ValueError('Unexpected credential process schema')
    expires = datetime.fromisoformat(record['Expiration'].replace('Z', '+00:00'))
    if not now + timedelta(minutes=10) < expires <= now + timedelta(minutes=65):
        raise ValueError('Session lifetime invalid')
    if not all(isinstance(record[k], str) and record[k] for k in ('AccessKeyId', 'SecretAccessKey', 'SessionToken')):
        raise ValueError('Session unavailable')
    return {**record, 'Expiration': expires.astimezone(UTC).isoformat(timespec='seconds')}


def openssl(*args):
    # All command output stays private, including failures; callers log only generic errors.
    return subprocess.run(['/usr/bin/openssl', *map(str, args)], capture_output=True,
                          timeout=15, check=True).stdout


def certificate_dates(path):
    lines = openssl('x509', '-in', path, '-noout', '-dates').decode('ascii').splitlines()
    return tuple(datetime.strptime(line.split('=', 1)[1], '%b %d %H:%M:%S %Y %Z')
                 .replace(tzinfo=UTC) for line in lines)


def validate_leaf(path, key, purpose):
    subject = openssl('x509', '-in', path, '-noout', '-subject', '-nameopt', 'RFC2253')
    if subject.decode('ascii').strip().split('=', 1)[1].strip() != 'CN=pals-geekten-20261026-' + purpose:
        raise ValueError('Unexpected leaf identity')
    if openssl('x509', '-in', path, '-noout', '-pubkey') != openssl('pkey', '-in', key, '-pubout'):
        raise ValueError('Leaf key mismatch')


class CertificatePublishedError(RuntimeError):
    """Replacement succeeded, but directory durability could not be confirmed."""


def with_certificate(purpose, authority, authenticate, *, now, force=False):
    """Authenticate before publishing; retain current cert on prepublication failure."""
    cert, key = authority / (purpose + '.crt'), authority / (purpose + '.key')
    private(authority)
    private_file(cert)
    private_file(key)
    lock = os.open(authority / ('.' + purpose + '.renew.lock'),
                   os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX)
        private_file(authority / ('.' + purpose + '.renew.lock'))
        validate_leaf(cert, key, purpose)
        starts, expires = certificate_dates(cert)
        if starts > now:
            raise ValueError('Leaf not yet valid')
        if not force and expires > now + timedelta(days=7):
            return authenticate(cert)
        try:
            return rotate_certificate(purpose, authority, cert, key, authenticate, now=now)
        except CertificatePublishedError:
            raise
        except Exception:
            if expires <= datetime.now(UTC):
                raise
            # Transient issuance/authentication failure must not discard a usable old session.
            result = authenticate(cert)
            print('Geekten ' + purpose + ' certificate renewal failed; current certificate authenticated', flush=True)
            return result
    finally:
        os.close(lock)


def rotate_certificate(purpose, authority, cert, key, authenticate, *, now):
    ca, ca_key = authority / 'ca.crt', authority / 'ca.key'
    private_file(ca)
    private_file(ca_key)
    ca_start, ca_end = certificate_dates(ca)
    if ca_start > now or ca_end <= now + timedelta(days=30, minutes=5):
        raise ValueError('CA cannot cover renewal lifetime; operator action required')
    subject = openssl('x509', '-in', ca, '-noout', '-subject', '-nameopt', 'RFC2253')
    if subject.decode('ascii').strip().split('=', 1)[1].strip() != 'CN=pals-geekten-20261026-ca':
        raise ValueError('Unexpected signing authority')
    openssl('verify', '-CAfile', ca, ca)
    with tempfile.TemporaryDirectory(prefix='.' + purpose + '-renew-', dir=authority) as temporary:
        directory = Path(temporary)
        request, candidate, extensions = directory / 'request.csr', directory / 'candidate.crt', directory / 'leaf.cnf'
        extensions.write_text('basicConstraints=critical,CA:false\nkeyUsage=critical,digitalSignature\n'
                              'extendedKeyUsage=clientAuth\nsubjectKeyIdentifier=hash\nauthorityKeyIdentifier=keyid,issuer\n')
        openssl('req', '-new', '-sha256', '-key', key, '-out', request,
                '-subj', '/CN=pals-geekten-20261026-' + purpose)
        openssl('x509', '-req', '-sha256', '-days', '30', '-in', request,
                '-CA', ca, '-CAkey', ca_key, '-set_serial', hex(secrets.randbits(159) | 1),
                '-out', candidate, '-extfile', extensions)
        candidate.chmod(0o600)
        validate_leaf(candidate, key, purpose)
        openssl('verify', '-purpose', 'sslclient', '-CAfile', ca, candidate)
        new_start, new_end = certificate_dates(candidate)
        if not new_start <= now + timedelta(minutes=1) or not now + timedelta(days=29) < new_end <= ca_end:
            raise ValueError('Candidate lifetime invalid')
        result = authenticate(candidate)
        with candidate.open('rb') as stream:
            os.fsync(stream.fileno())
        os.replace(candidate, cert)
        try:
            directory_fd = os.open(authority, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except OSError as error:
            raise CertificatePublishedError('Certificate published; durability confirmation failed') from error
        return result


def authenticate(purpose, config, certificate, *, root, now):
    import boto3
    role, session = ROLES[purpose]
    authority = root / 'machine-auth'
    role_arn = f'arn:aws:iam::{ACCOUNT}:role/pals-geekten/{role}'
    args = [config['helper'], 'credential-process', '--certificate', str(certificate),
            '--private-key', str(authority / (purpose + '.key')),
            '--trust-anchor-arn', config['trust_anchor_arn'], '--profile-arn', config['profile_arn'],
            '--role-arn', role_arn, '--role-session-name', session, '--session-duration', '3600', '--region', REGION]
    # No SSO/profile/config inheritance and no helper credential output in logs.
    env = {'PATH': '/usr/bin:/bin', 'HOME': str(root), 'AWS_CONFIG_FILE': '/dev/null',
           'AWS_SHARED_CREDENTIALS_FILE': '/dev/null', 'AWS_EC2_METADATA_DISABLED': 'true'}
    completed = subprocess.run(args, env=env, capture_output=True, timeout=45, check=True)
    if len(completed.stdout) > 16384:
        raise ValueError('Oversized session')
    creds = check_credentials(json.loads(completed.stdout), now=now)
    sts = boto3.client('sts', region_name=REGION, aws_access_key_id=creds['AccessKeyId'],
        aws_secret_access_key=creds['SecretAccessKey'], aws_session_token=creds['SessionToken'])
    identity = sts.get_caller_identity()
    if identity['Account'] != ACCOUNT or identity['Arn'] != f'arn:aws:sts::{ACCOUNT}:assumed-role/{role}/{session}':
        raise ValueError('Runtime identity mismatch')
    return creds


def renew(purpose: str, config: dict, *, root=ROOT, force_certificate_renewal=False):
    role, session = ROLES[purpose]
    authority = root / 'machine-auth'
    out = root / 'runtime-sessions' / purpose
    private(root / 'runtime-sessions')
    private(out)
    now = datetime.now(UTC).replace(microsecond=0)
    creds = with_certificate(purpose, authority,
        lambda cert: authenticate(purpose, config, cert, root=root, now=now),
        now=now, force=force_certificate_renewal)
    role_arn = f'arn:aws:iam::{ACCOUNT}:role/pals-geekten/{role}'
    state = {'version': 1, 'ready': True, 'role_arn': role_arn, 'session_name': session,
             'checked_at': now.isoformat(), 'expires_at': creds['Expiration'], 'reason': None}
    atomic(out, 'credentials.json', creds)
    atomic(out, 'state.json', state)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    private(ROOT)
    authority = ROOT / 'machine-auth'
    private(authority)
    private_file(authority / 'broker.json')
    config = json.loads((authority / 'broker.json').read_text())
    if config['trust_anchor_arn'].split(':trust-anchor/')[0] != f'arn:aws:rolesanywhere:{REGION}:{ACCOUNT}':
        raise ValueError('Unexpected trust anchor account')
    if config['profile_arn'].split(':profile/')[0] != f'arn:aws:rolesanywhere:{REGION}:{ACCOUNT}':
        raise ValueError('Unexpected profile account')
    # Identity resources must be new Geekten resources recorded in the reviewed manifest.
    lock = os.open(ROOT / 'broker.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    while True:
        failed = False
        for purpose in ROLES:
            try:
                renew(purpose, config)
            except Exception:
                failed = True
                role, session = ROLES[purpose]
                atomic(ROOT / 'runtime-sessions' / purpose, 'state.json', {
                    'version': 1, 'ready': False, 'role_arn': f'arn:aws:iam::{ACCOUNT}:role/pals-geekten/{role}',
                    'session_name': session, 'checked_at': datetime.now(UTC).replace(microsecond=0).isoformat(),
                    'expires_at': None, 'reason': 'refresh_failed'})
                print('Geekten ' + purpose + ' credential refresh failed', flush=True)
        if args.once:
            raise SystemExit(1 if failed else 0)
        time.sleep(60 if failed else 1200)

if __name__ == '__main__':
    main()
