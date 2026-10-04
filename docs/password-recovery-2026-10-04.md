# Password recovery investigation (2026-10-04)

The production account reported in the reset failure was enabled and `CONFIRMED`,
but had no `email_verified` attribute. Its Cognito pool uses `verified_email` as
the only recovery mechanism. Account confirmation and email verification are
separate states: this combination prevents self-service password recovery.
The account's creation timestamp also matched a successful email invitation.
Invitation delivery alone was not treated as proof of mailbox ownership.

Read-only AWS checks found no MFA, custom Lambda triggers, or browser-client
secret. After the user confirmed ownership and access to the registered mailbox,
the administrator set `email_verified=true` for this account only. A fresh
`AdminGetUser` read confirmed the other attributes, enabled state, and account
status were unchanged. The pool configuration and password were not changed.

`ForgotPassword` then succeeded using the existing browser client and returned
`CodeDeliveryDetails` with `DeliveryMedium=EMAIL` and `AttributeName=email`.
Actual inbox receipt and confirmation of the user's new password remain for
the user to complete. No password or confirmation code was obtained or stored.

The web frontend now explains the known missing-recovery-address error and code
delivery failures in all four UI languages. It retains the generic fallback for
unrelated `InvalidParameterException` errors and does not display provider
diagnostics. The user can retry, and a visible error follows language changes.

Validation: four relevant Vitest files passed (77 tests), TypeScript checking
and targeted ESLint passed, and both Japanese text checks found no issues.
Only this chat's changes were committed to the frontend. Production deployment
of the new messages has not been verified.

For administrator invitations, confirm email ownership before setting
`email_verified=true`. Completing the initial password challenge does not
replace email verification. Do not solve one account's missing verification by
weakening the pool's recovery rules or marking every user's email as verified.

AWS documents the verified recovery destination requirement in
[ForgotPassword](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_ForgotPassword.html)
and distinguishes account confirmation from attribute verification in
[sign-up confirmation](https://docs.aws.amazon.com/cognito/latest/developerguide/signing-up-users-in-your-app.html).
