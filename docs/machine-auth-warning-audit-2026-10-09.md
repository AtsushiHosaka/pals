# Certificate warning continued after the threshold change

Status: warning suppression remains unresolved. Current AWS authentication succeeds.
Read-only audit on October 9, 2026, following the new AWS Health email.

## Verified AWS state

`GetCallerIdentity` confirmed account `828786775577`; Roles Anywhere was queried in
`ap-northeast-1`. `ListTrustAnchors` returned one anchor:
`pals-macmini-machine`, ID `19ba8073-2d7e-4907-815a-68f979ebb580`, enabled.
An independent `GetTrustAnchor` returned the same settings:

| Event | Enabled | Threshold | Channel | Configured by |
| --- | --- | --- | --- | --- |
| `END_ENTITY_CERTIFICATE_EXPIRY` | true | 3 days | ALL | `828786775577` |
| `CA_CERTIFICATE_EXPIRY` | true | 45 days | ALL | `rolesanywhere.amazonaws.com` |

The anchor's `updatedAt` remains `2026-10-08T03:38:01.746883Z` (October 8,
12:38:01 JST). The October 8 threshold change is still present; there is no second
end-entity setting or additional anchor in this regional listing.

## The new notification was created after the change

The [October 9 email](https://mail.google.com/mail/u/?authuser=hosaka2917%40gmail.com#all/1a11dffbd13e982e)
arrived at 09:11:01 JST. `GetManagedNotificationEvent` confirmed:

- Notification ID: `a01m4ezd339j9wh6cffa4h6f2gv`.
- Creation: `2026-10-09T00:00:59.497Z` (09:00:59 JST).
- Source start time: `2026-10-09T00:00:53Z` (09:00:53 JST).
- Event: `AWS_IAMROLESANYWHERE_EE_CERT_EXPIRY_NOTIFICATION`.
- Aggregation type: `NONE`.
- Four certificates, November 4 expiry, 26 days remaining.

This establishes a newly created notification after the configuration change,
rather than delayed delivery of the October 8 email. It does not establish which
internal setting AWS Health evaluated.

## All four certificates currently authenticate successfully

`GetSubject` returned the following newest credential records with `failed=false`.
OpenSSL parsed the public certificates returned by AWS; their serials match the email.
Times below are JST on October 9; expiry dates are JST on November 4, 2026.

| Purpose | Latest success | Expiry time | Serial (hex) |
| --- | --- | --- | --- |
| API | 10:34:32 | 11:01:07 | `0fafd51ec01d8cc81fe0bf07f8a2c1a0396e3f` |
| worker | 10:34:38 | 11:39:34 | `12ea7e6203739b5404a139d640454b1023d52c` |
| backup-writer | 10:34:43 | 11:01:07 | `0b33d797c2ed0da095b10218f2e18d9730bd33` |
| release-signer | 10:36:59 | 11:01:07 | `008ad08dec8f7dda9fcefdfb8ec5fb9c67763398` |

`pals-macmini-machine-auth-stalled` is `OK`, actions enabled. Its current
configuration is three consecutive 1800-second periods below three successful
sessions, with missing samples filled with zero and missing expression data
treated as breaching. Its aggregate status does not prove each purpose is healthy;
the four individual success records above provide separate current evidence.

## Interpretation and remaining work

[AWS notification settings documentation](https://docs.aws.amazon.com/rolesanywhere/latest/userguide/customize-notification-settings.html)
states that ALL includes AWS Health and end-entity notification evaluation starts
when remaining days are at or below the threshold. Today's 26-day notification
conflicts with that documented behavior under the returned 3-day setting.

The cause is not established. Configuration propagation or an AWS service defect
are hypotheses, not confirmed findings. No notification setting, subscription,
certificate, IAM permission, or production process was changed in this audit.
The Health `DescribeEvents` API returned `SubscriptionRequiredException`; the
managed-notification API supplied the exact record instead.

The previous record, parent commit `6023f20493582a2e6a98fc9df700cab5e590ad7b`,
confirmed the threshold change but explicitly left the next daily email outcome
unobserved. Describing the entire issue as resolved was premature. Natural leaf
renewal around October 28 remains unverified; successful STS refresh today does
not prove that future leaf renewal will succeed.

## AWS support-case draft (not submitted)

Subject: Roles Anywhere AWS Health end-entity expiry notification at 26 days despite custom 3-day threshold

For account 828786775577, region ap-northeast-1, trust anchor
19ba8073-2d7e-4907-815a-68f979ebb580, we changed
END_ENTITY_CERTIFICATE_EXPIRY to enabled=true, threshold=3, channel=ALL at
2026-10-08T03:38:01.746883Z. Independent GetTrustAnchor reads on October 8 and 9
confirm the custom setting. CA expiry remains at 45 days. There is one anchor in
this regional listing. Nevertheless, notification a01m4ezd339j9wh6cffa4h6f2gv was
created at 2026-10-09T00:00:59.497Z, source start 00:00:53Z, aggregation NONE,
listing the four serials above at 26 days remaining. All four still authenticate.
Please explain which threshold generated this notification, whether propagation
or an existing certificate record affects evaluation, and how to make the enabled
custom threshold govern AWS Health without disabling expiry warnings.
