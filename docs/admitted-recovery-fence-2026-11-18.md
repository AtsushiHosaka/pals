# Durable startup fence source slice — 2026-11-18

Tracking: [#433](https://github.com/AtsushiHosaka/pals/issues/433), required before
the normal #425 release and #318 production figure checks can resume.
Owner: [implementation chat](codex://threads/01a1ed09-2b3d-76c3-91c4-92efa30bdecc).
The sole live execution owner remains `01a1ebe7-a4ee-78c0-ab22-a16cfcccc3d2`.

The live owner explicitly assigned a WORKING slice of the
[recovery design PR #434](https://github.com/AtsushiHosaka/pals/pull/434): install
and inspect durable startup fences under the two hosts' existing launch locks.
This does not establish the full ARA-008 exclusion or recovery authority.

## Source and interface

[infra #194](https://github.com/AtsushiHosaka/pals-infra/pull/194) starts from
`76335a4fae7a12df89d28b220f94bb1b73c1965a` and targets the approved production
branch `claude/seq30-worker-trust`. Pushed source:
`25732a7795c7110751577504fbc3a59144578288`.
Only a new module, its dedicated tests and an explicitly assigned CI step changed.
The module SHA-256 is
`0d3dc156ad1b432bedd03660488d5585bd21da86873e259cacdbee0069fc1a12`.

The normal entry point is `FenceStore(runtime_root, host_role, expected_uid=0).locked()`.
It opens the role's existing launch-lock file, validates its metadata and path,
and holds an exclusive nonblocking flock. It never creates another lock namespace.
The context offers `install(record)` and `read(expected_record=None)`.

The closed record contains the schema, host role, canonical UUID attempt ID,
candidate-manifest digest and planned-owner-token **SHA-256**. The owner preimage
is neither accepted nor stored. Existing owner-hash uniqueness constraints are
preserved. Trusted callers supply the expected bindings; this file does not verify
a signature, DB epoch, remote host, or execution authorization.

Install writes a private staging file, fsyncs it, exclusively hardlinks the final
name without replacing an existing file, removes its staging name only on that
successful path, then fsyncs the directory and verifies exact bytes and inode.
It returns a durable installer ACK only after those operations succeed. A completed
same-byte retry fsyncs again. Different owner/attempt/candidate, unsafe paths or
metadata and any partial staging state are refused without deleting the fence.
There is no TTL, clear or automatic reconciliation operation. Partial states must
stay visible to the caller's same-attempt reconciliation; a new attempt is unsafe.

`read()` returns facts, not a new durability ACK. It refuses partial/hardlinked,
symlinked, oversized, noncanonical, duplicate-key and malformed records. Root and
lock inodes are checked against the protected paths before operations and at normal
context exit. Parent-directory traversal uses directory descriptors and no-follow
opens, and rejects group/world-writable or foreign-owned ancestors.

The optional borrowed descriptor is for trusted callers already holding the exact
exclusive lock. The module checks metadata and rejects obvious unlocked/shared
descriptors, but cannot portably prove the precondition across every foreign-lock
release race. It duplicates and closes its descriptor without `LOCK_UN`, preserving
the caller's shared open-file-description. Use normal acquisition by default;
never expose borrowed descriptors through untrusted transport arguments.

## Executed evidence

- 31 tests passed with zero skips on macOS using real files and independently
  exec'd flock probes. They cover both roles, exclusive locking and borrowed-lock
  preservation, exact identity, safe modes, hardlinks/symlinks, inode replacement,
  malformed/deep JSON, idempotence and preservation of partial state.
- Explicit file/directory-fsync exception injection verifies that no ACK is returned
  on failure. A final file visible before directory-fsync failure remains intact;
  same-byte retry fsyncs and retains the inode. A real two-link partial publication
  remains blocked and is not cleared. This is not a power-loss experiment.
- The existing `test_release_cycle.py` suite passed all 146 tests locally. Its
  cloud/native doubles establish controller contracts, not real recovery.
- Python compilation, diff checks and independent read-only source review passed.
- The dedicated canonical CI step refuses zero tests, failures and any skipped
  test. Linux exact CI remains separately tracked on infra #194. The first push
  run was superseded/cancelled when the PR run entered the concurrency lane;
  that cancellation was not a failed test. No older PASS substitutes for the latest run.

The non-root local run did not exercise a real file owned by a foreign UID.
Linux, actual power loss, both production hosts and new recovery consumers remain
unverified here. These unit/source regression counts are not product-success,
model-quality, answer-latency or cost measurements and are not new quality-ledger rows.

## Required integration and production continuation

The live owner must collect both hosts' durable ACKs for the same attempt,
observe installer termination and lock release, and then perform the existing
fresh quiet inventory. Boot/start/claim/admit/restore consumers must explicitly
read the fence under the same lock. Existing dispatched legacy recovery does not
read this new file and is not stopped merely by installing it. It needs separate
terminal observation or exact historical refusal evidence.

No existing hook, signature window, old manifest, IAM policy, admission, service
or model call changed in this slice. Consumer/executor/DB-currentness integration
is owned by #433's main task. This source artifact does not make #433 or #318 done.
After its reviewed live prerequisites and normal release, the figure readback and
real browser display/save/reload checks must still run before closing #318.
