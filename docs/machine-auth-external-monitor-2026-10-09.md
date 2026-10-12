# Replacement monitoring for Roles Anywhere certificate warnings

Status: deployed, production alerting enabled, and warning cutover verified.
The next daily email cycle remains unobserved.
Account `828786775577`, region `ap-northeast-1`, October 9, 2026.

The recurring AWS Health email still reported 26-day certificate expiry after the
anchor's end-entity threshold was changed to three days. The cause remains
unconfirmed. [The audit and Support restriction](machine-auth-warning-audit-2026-10-09.md)
record the evidence. This replacement independently observes the four machine
authentication purposes. The misleading end-entity warning was disabled only
after replacement alerting and delivered fault/recovery tests passed.

## Installed monitor

The isolated CloudFormation stack, Lambda and EventBridge rule are named
`pals-macmini-machine-auth-monitor`. EventBridge invokes Node.js 24 Lambda every
five minutes, independently of the Mac mini and human SSO. Lambda reads four
fixed Roles Anywhere subjects and publishes nine metrics in `PALS/MachineAuth`.
Its dedicated role has only fixed-subject read, namespace-scoped metric write,
and its own log-stream permissions. It cannot issue credentials or change IAM.

| Alarm | Breach |
| --- | --- |
| Four purpose-specific expiry alarms | Certificate lifetime at or below three days |
| API, worker, backup-writer freshness | Last audited successful authentication at least 45 minutes ago |
| release-signer freshness | Last audited successful authentication at least 90 minutes ago |
| Monitor health | Query/parse failure or missing heartbeat |

The eight purpose alarms require two five-minute breaching periods. The heartbeat
uses `FILL(hb,0)` to turn missing samples into explicit failures, with two of three
five-minute periods. All alarms treat missing data as breaching. The heartbeat
rule allows a delayed latest sample but does not eliminate all late-data noise or
promise an exact ten-minute detection deadline. ALARM and OK
actions use the existing `pals-macmini-auth-alerts` confirmed email subscription.
The existing aggregate alarm and local broker recovery remain in place.

The collector chooses the newest credential record with `failed=false`, parses
its public certificate, and checks CN, issuer, serial and validity against the
audit timestamp. Subject attempt timestamps are not proof of successful auth.
Optional subject/credential `enabled` fields are absent in current AWS responses;
omission is accepted, while explicit disabled/malformed values fail closed.
Unavailable or malformed evidence emits fault values, never a healthy heartbeat.
The Lambda invocation response contains only purpose/status/age/remaining days.

## Verification

- Source: 16 Node tests with real temporary EC certificates and 42 Python tests.
- CloudFormation template validation succeeded; initial deployment kept alarm
  actions disabled. The corrected deployed source SHA-256 is
  `562701e3580ca9e2c12a4273cca129eef6f8fa6d64039d87afedc3370d26429d`.
- Actual Lambda invocation returned `status=ok` for all four purposes, about
  25.97 days remaining and successful-auth ages of 414–588 seconds.
- Independent AWS/Events and AWS/Lambda metrics confirmed scheduled invocations
  at 02:38 and 02:43 UTC (11:38 and 11:43 JST). Lambda errors were zero and actual
  monitor-health samples were one at both times. The manual 02:44 test is excluded
  from this scheduled-execution evidence.
- All nine live metric streams passed the recent/finite/healthy check.
- The first delivery acceptance run delivered expiry and stale-authentication
  ALARM emails, but the stopped-heartbeat alarm did not transition within eight
  minutes. Its final actual heartbeat was at 02:47 UTC. The script cleaned up
  all three test alarms and temporary topic grants. This run was not accepted;
  production actions remained disabled and the original warning remained enabled.
  The heartbeat was changed to explicit zero filling with two-of-three evaluation
  before the next disabled deployment and full delivery test.
- After the heartbeat correction deployed at 03:01:13 UTC, independent readback
  confirmed every production alarm matched the reviewed configuration. Scheduled
  runs at 03:03 and 03:08 UTC each had one EventBridge/Lambda invocation, zero
  Lambda errors and a real heartbeat value of one. IAM readback matched the scoped
  trust/inline policy, with no attached managed policies.
- The second delivery test passed real ALARM and subsequent OK SNS actions for
  all three conditions. All six message subjects, received times and snippets
  were verified in the primary Gmail account through its existing Chrome tab;
  the Gmail connector was temporarily unavailable. The search was restricted to
  messages after the second run began, excluding the first run's old deliveries.
- The acceptance script exited successfully after deleting its three owned alarms
  and restoring the SNS grant to only the nine production alarm ARNs.
- CloudFormation completed production alert enablement at 03:18:31 UTC.
  At 03:22:47 UTC all nine alarms matched the reviewed configuration, had actions
  enabled and were `OK`; all nine recent metric streams were healthy. Test alarms
  were absent and the SNS grant contained only the nine production alarm ARNs.
- Post-cutover readback at 03:24:14 UTC repeated those checks and confirmed the
  original aggregate alarm configuration and email subscription were unchanged,
  the aggregate alarm was `OK`, and the enabled anchor retained its CA warning.

| Test | Successful SNS ALARM (JST) | Successful SNS OK (JST) | Gmail |
| --- | --- | --- | --- |
| Certificate expiry | 12:05:11 | 12:09:11 | Both received |
| Stale authentication | 12:05:40 | 12:09:40 | Both received |
| Stopped heartbeat | 12:06:30 | 12:13:30 | Both received |

[Gmail receipt search](https://mail.google.com/mail/u/?authuser=hosaka2917%40gmail.com#search/after%3A1791514884+subject%3Apals-macmini-auth-acceptance).

The acceptance script uses three isolated dimensions and temporary alarms with
the production comparators, thresholds, missing-data behavior and SNS delivery.
Its period is shortened to 60 seconds. It publishes expiry/staleness faults and
actually stops the isolated heartbeat, then restores healthy data. It never
injects synthetic production-purpose metrics or calls `SetAlarmState`. Successful
ALARM and subsequent OK SNS action history must belong to this run; all six
message arrivals must also be verified in Gmail. Cleanup removes owned test alarms and their
exact temporary topic grants, preserving other statements and subscriptions.

## Cutover and remaining observations

Production alerts were enabled after current metrics, scheduled execution,
isolated fault/recovery delivery and installed configuration passed. At
`2026-10-09T03:23:03.087420Z` (12:23:03 JST), only
`END_ENTITY_CERTIFICATE_EXPIRY` on anchor
`19ba8073-2d7e-4907-815a-68f979ebb580` was disabled. Independent `GetTrustAnchor`
readback confirmed `enabled=false` for that event; AWS omits its threshold in
the disabled-event response. The anchor remains enabled, and the CA setting is
unchanged: enabled, 45 days, channel ALL. Unrelated AWS Health settings were not
modified.

A single read-only follow-up in this chat is scheduled for October 10 at 10:00
JST (`pals-certificate-warning-follow-up`). It will check the first daily email
cycle and live monitoring. Absence of one email cannot prove permanent suppression.
The next daily AWS email outcome remains a future observation. The monitor
checks AWS audit evidence; it does not prove that each application consumed its
credentials or that automatic leaf renewal around October 28 will succeed.
After renewal, verify the new leaf expiries, continuing subject IDs, and live
consumer behavior. Nine custom metrics/alarms, scheduled Lambda and logs incur
normal AWS usage charges; no Support plan was upgraded.

Implementation commit: `06f45b65b52aaa5f2dea9df0484204b2d8667a50` in `pals-infra`
(pushed before updating the parent pin).

Implementation and deployment procedures live in
`pals-infra/cloud/machine-auth-monitor/README.md`. Public source and this evidence
are tracked; certificates, keys, credentials, generated templates and raw logs
are excluded from Git.
