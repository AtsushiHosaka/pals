# Closed figure aggregate readback — 2026-11-18

Tracking: #318. This is a source-only helper for the sole live owner in #433/#425.
It has not been executed against PostgreSQL or the production API runtime.
It is not a cutover controller, admission tool or replacement acceptance runner.

## Reviewed scope

`pals-scripts/figure-readback.py` runs as a new standalone process inside the exact
existing API image, with that image's approved environment and dependencies. It
uses the canonical `Settings`, active-toolchain helper and `db_pool`. It refuses
all CLI arguments; no URL, SQL, role, registry path or ID override is available.

The registry file inside the API image must have this exact SHA-256:
`16e8d4b6d104489b9373ccbbedae6b09950068f8b1ae836195bfb93a9fffcdc7`.
Only its fixed 35 Recipe IDs are queried. Both reads use separate repeatable-read
read-only transactions, a five-second statement timeout and one-second lock
timeout. `SHOW transaction_read_only` must confirm `on` before the data query.

The first query uses the API's selector connection and existing selector role.
It selects only Recipe ID and the answer digest from `pals_recipe_search.selectable_entries`,
restricted to Japanese and the API's exact configured active toolchain. A sentinel
limit rejects more than 350 returned variants. Missing, mismatched and ambiguous
Recipe IDs remain distinct; multiple eligible rows do not count as a unique match.

The second query uses the base API connection in a separate transaction. It
returns only counts of saved answers and answers with an object-valued
`visualization`. It returns no request IDs, account IDs, statements, answers,
figure payloads, credentials or URLs. Exception text and arbitrary reasons are
not serialized; stdout contains a single JSON object with closed status/reason
codes, aggregate counts and known catalog IDs. Python logging/warnings and Python
stdout/stderr from the imported API modules are suppressed in this subprocess.

## Execution conditions for the live owner

1. Wait for the approved canonical remote read entry point and its exact access
   window. This helper does not grant SSM/DB access or extend expired authority.
2. Bind the execution receipt to the reviewed parent commit, script SHA-256,
   actual API image digest, admitted manifest and environment binding. The helper
   pins registry bytes; it does not establish source/image identity by itself.
3. Use the existing approved native read adapter to execute the hash-frozen script
   in a **new standalone API-image process**. Do not import it into the serving
   process, install dependencies, mutate the image, create a new application/DB,
   change environment flags or improvise an alternate remote execution route.
4. The execution wrapper must enforce an external 30-second process timeout and
   collect exit/timeout plus redacted stdout. The script's 29-second SIGALRM is an
   additional cooperative guard, not a strict bound for a blocked native library.
   The owner must arrange cancellation through the canonical adapter, including
   confirming that the standalone process ended if an external timeout fires.
5. Invoke the script without arguments and execute once. Preserve its raw private
   receipt. Do not retry an unavailable read by changing roles, timeouts or SQL.
   An inaccessible relation, source mismatch or privilege failure stays NOT VERIFIED.

The helper rejects pre-existing pools in its process while allowing `db_pool`'s
always-present `module` counters. Its final cleanup requests bounded pool closure.
The canonical `close_all()` swallows internal close failures, so that request is
**not proof of successful cleanup**; standalone-process termination must be observed
by the caller. This task has not modified or stopped the serving API process.

## Interpreting output

`READ_ONLY_OBSERVED` means both bounded queries returned interpretable aggregates.
It is not PASS for a feature, a release, semantic matching or mathematical correctness.
`NOT_VERIFIED` with exit 2 means at least one prerequisite/read/cleanup request failed;
successful sections may remain recorded but cannot promote the missing section.

Even 35 unique matching catalog rows do not prove a live answer received a figure.
Even a positive object-valued visualization count does not prove the object is
valid, rendered, owned by a permitted test account or preserved through HTTP/reload.
Use only existing approved test requests for those separate browser observations.
This helper deliberately does not return request references or expose user data.

Local verification: 11 standard-library policy/aggregation tests passed, with no
database doubles. The hash-pinned registry parser also accepted the inspected API
source's actual file (35 rows) without connecting to a database. Independent review
found and corrected the initial always-truthy pool-stat guard, and found no additional
material source blocker. Actual image imports, privileges, PostgreSQL execution,
external cancellation and live cleanup remain **NOT VERIFIED**.
