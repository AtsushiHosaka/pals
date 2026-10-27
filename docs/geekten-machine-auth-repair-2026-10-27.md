# Geekten certificate warning and renewal repair

October 27, 2026, account `828786775577`, region `ap-northeast-1`.

## Cause and scope

The October 27, 09:11 JST AWS Health email lists four certificates issued by
`pals-geekten-20261026-ca`, expiring November 25 with 29 days remaining. These
are separate from the original production certificates covered by the October 9
repair. Live AWS readback confirmed Geekten's anchor
`cef7a1dc-8d0a-46ed-9c3d-d892f2640ad0` used the default enabled 45-day end-entity
warning. A 30-day certificate is already inside that warning window.

The installed Geekten broker refreshed STS sessions every 20 minutes but did
not renew certificates. Its source matched the October 26 staged broker,
SHA-256 `d285d2fdd5467c568f9b5978168625b689c5db2c18a322eda32463196710a688`.

## Changes and verification

- Set only Geekten's end-entity warning to enabled, three days, channel ALL.
  Independent `GetTrustAnchor` readback confirmed the setting and retained the
  enabled anchor and enabled 45-day CA warning.
- Installed [the scoped broker](../pals-scripts/geekten-machine-auth/README.md)
  at the existing Geekten runtime path, preserving a private predecessor copy.
  It automatically renews certificates within seven days of expiry, validating
  each candidate and its exact live AWS identity before atomic replacement.
  It retains authentication with a still-valid certificate if renewal fails.
- Fourteen tests passed both locally and on the actual Mini Python 3.13 and
  OpenSSL runtime. Independent source review found no deployment blockers.
  Installed broker SHA-256:
  `6e23951b19372e57fb7e4108fdd787bbfcfdb5d0f9864d85114eb263c528ae75`.
- Exercised the actual renewal path for all four roles at 12:08:50–52 JST.
  Each new certificate authenticated through Roles Anywhere and exact STS
  identity validation before installation. Existing private keys were retained.
  All new certificates expire November 26, 2026, at 12:08:50–52 JST.
- Restarted only the existing Geekten LaunchAgent. It refreshed all four sessions
  at 12:08:53–54 JST and reported ready for every purpose. Independent AWS
  `GetSubject` readback reported `failed=false` for the new serials below.

| Purpose | Renewed certificate serial, hexadecimal |
| --- | --- |
| API | `5f1d952d0098d81d1cd800eab2bcd13d0f5ea7b3` |
| worker | `321d82f6e1a79c6c25e5ffe623bdfc9e4263dcfd` |
| assessment-worker | `1ee51494dbb908c05efa81a102da3ce4253793eb` |
| reconciler | `6f04727086faf24a36e1db2a061717d7382e3081` |

The original production broker retained PID 77205. No original production
certificate, session, role, trust anchor, monitor or container was modified.
All ten existing production alarms were OK with actions enabled at the initial
live readback. No key, session credential, environment file or raw log is stored
in this repository.

## Evidence limits

The daily AWS Health cycle after this change remains unobserved. The previous
production incident demonstrated that a threshold readback alone does not prove
email suppression. Both Geekten expiry warnings remain enabled; none were
disabled to hide this incident. The original independent monitor covers only
the original production subjects, not Geekten.

The real forced renewal and immediate subsequent broker authentication passed.
Calendar-triggered renewal at the next seven-day boundary, application SDK
consumption of renewed sessions, and reboot recovery were not exercised by this
repair. CA renewal is operator maintenance; the current dedicated CA expires
October 26, 2027.
