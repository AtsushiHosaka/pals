# Geekten certificate renewal broker

This host-only broker is scoped to the four existing Geekten roles in account
`828786775577`. It extends the October 26 broker with leaf certificate renewal;
it does not provision AWS resources or change the judging environment.

Every normal session refresh checks the leaf lifetime. Within seven days of
expiry, the broker signs a 30-day replacement using the existing dedicated CA
and leaf key. It checks the certificate identity, key, chain and lifetime, then
requires successful Roles Anywhere authentication and an exact STS role/session
identity before atomically replacing the certificate. Keys remain on the host.
CA replacement remains operator maintenance.

The existing `--once` interface, 20-minute session refresh, one-minute failure
retry, private session files and role/session restrictions are preserved.
`renew(..., force_certificate_renewal=True)` exercises the same renewal path for
an operator's live acceptance check. Never print its credential intermediates.

Run the focused tests with:

```sh
python3 -m unittest discover -s pals-scripts/geekten-machine-auth -p 'test_*.py' -v
```

The installed path is
`/Users/hosakaatsushi/pals-geekten-20261026/runtime/broker.py`, supervised by the
existing `gui/501/site.pals.geekten.machine-runtime-broker` LaunchAgent. Before
installation, compare its source hash with the expected predecessor and retain
a private rollback copy. Restart only this label, preserving existing session
files and the contest broker.

AWS end-entity warnings stay enabled on the Geekten anchor with a three-day
threshold; CA warnings stay enabled at 45 days. The original production monitor
does not cover Geekten. A configuration readback and successful renewal do not
establish that the next AWS Health email cycle will honor the threshold.
