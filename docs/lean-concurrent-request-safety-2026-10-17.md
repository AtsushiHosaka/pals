# Lean concurrent-request safety — 2026-10-17

The requested target is the production Mac mini. The reported failure with two
or more simultaneous users has not yet been reproduced. No production setting,
service, permission, queue or database record was changed during this inspection.

## Current production observation

[Guarded inspection 39018743539](https://github.com/AtsushiHosaka/pals/actions/runs/39018743539)
completed on October 17 at 08:48:51 UTC. It observed signed release sequence 34,
manifest `e1c515838750121ae6a2b2cfdccd9462017baa9685b33d850b20c79397226452`.
API and worker effective capability is `full`; the API reports Lean flow enabled,
current runtime catalog and complete full-runtime configuration. Declared roles
are API, Web, assessment worker, proof worker, verifier and reconciler. Exactly
one fixed verifier and one fixed reconciler were observed running. This is a
configuration/runtime inventory observation, not a successful concurrent proof.

The inspection used parent `be61b47c602ae916bb275c96182ae247586c06a7`, API
`0abc2f5cdc0ec57255c909c72d3aebf544150a28`, agent
`807b7beb0b52b5ef5ca15f6b8a7ab073e8caec5e`, infra
`985bcda9e27ee4ac96a240e420accc10ae6f8273` and frontend
`ee35e1f92012c5a02b7bcf6e804da5d500194729`. These inspection source pins alone
do not establish the deployed image contents.

The older initial-activation inspection
[39018595337](https://github.com/AtsushiHosaka/pals/actions/runs/39018595337)
refused `initial_staged_three_role_runtime_required`. That command expects the
former three-role predecessor; its refusal does not show a broken current Lean
runtime. General inspection
[39018670680](https://github.com/AtsushiHosaka/pals/actions/runs/39018670680)
then refused `another_host_update_is_active`. Normal retry succeeded without
removing locks or bypassing their checks.

## Existing execution boundaries

- The isolated verifier admits one compilation. A second simultaneous call gets
  the bound, retryable `verifier_unavailable` response. Existing HTTP regressions
  verify that the first compilation survives and the slot is released.
- Candidate reconciliation consumes one candidate at a time and retries its
  current candidate before taking the next. The HTTP client and reconciliation
  service recognize the capacity response as retryable.
- Assessment and proof workers use separate lanes; existing lane regressions
  verify assessment progresses while proof work is blocked.
- Each compiler invocation uses a distinct scratch directory.

These facts do not identify the user's reported crash. Increasing compilation
capacity without measuring memory, queue behavior and output isolation would
change the existing safety boundary without evidence that it fixes the failure.

## Verification and remaining work

The existing Python 3.12 environment passed 41 isolated-verifier HTTP and worker
lane checks. Twenty API candidate-runtime, reconciler-process and trigger checks
also passed; the API checks were rerun at the current parent pin. The relevant
agent HTTP/worker source is unchanged between the original worktree pin and the
current pin. Two additional event-gated candidate-runtime regressions were then
added in API commit `45094e7`: overlapping distinct candidates and the same
scenario while the first candidate schedules a retry. They check duplicate
trigger coalescing, serial execution and completion of both candidates. The API
set now passes 22 checks; combined focused coverage is 63 checks. Production
behavior is unchanged. These are local regression results, not production load
evidence.

Production PALS opens in the existing Chrome profile, but the session is signed
out. User-assisted sign-in was requested; no credentials were requested in chat.
The exact failing screen, failure message and whether the whole application or
only a Lean job fails remain unconfirmed.

Before a behavior change is considered complete:

1. Reproduce two overlapping requests through the normal application, retaining
   each request/job identity and ownership; record queue and processing times.
2. Check both requests reach their own terminal outcome without overwritten
   sources, duplicate settlement or loss of the queued request. For claimed
   verification success, compare actual compiler evidence, answer binding and
   learner-opened source for each request.
3. Correlate any failure with bounded host resource/restart diagnostics and the
   exact request stage. Preserve authentication, accounting, leases and source
   bindings while fixing the demonstrated cause.
4. Run the affected regression checks and existing critical user flows. Use the
   signed update/recovery path for any release and repeat the concurrent test on
   the actual updated runtime. A health response alone is insufficient.
