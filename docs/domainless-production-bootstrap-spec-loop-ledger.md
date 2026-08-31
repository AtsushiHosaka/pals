# Domainless Production Bootstrap Spec Loop Ledger

## Iterations

| Iteration | Spec revision | Trigger | Expected delta | Findings opened/closed | Routes | Result |
|---|---|---|---|---|---|---|
| 1 | parent `6dcecaa` + uncommitted spec | Initial implementation-ready draft | Define safe no-domain production bootstrap | Opened: infrastructure source gate, release/runtime DB privilege separation | `sdd-review-spec` → `sdd-update-spec` | Corrected in current working tree |
| 2 | parent `6dcecaa` + revised uncommitted spec | Targeted re-review | Define complete dirty-worktree identity | Closed prior two P1s; opened dirty-source identity | `sdd-review-spec` → `sdd-run-loop` → `sdd-update-spec` | Awaiting targeted re-review |
| 3 | parent `6dcecaa` + revised uncommitted spec | Source-identity re-review | Bind staged index state as well as deployed working-tree state | Repaired staged-content gap | `sdd-update-spec` → `sdd-review-spec` | Awaiting targeted re-review |

## Delegated review evidence

| Delegation | Scope | Inputs | Result | Next route |
|---|---|---|---|---|
| `domainless_deploy_audit` | Existing production root and image/migration constraints, read-only | parent `6dcecaa`, infra `fb92917` | Domain/TLS, ECR/secret ordering, and DB-release constraints identified | Incorporated into the initial spec |
| `domainless_spec_review` | DPB-001–007 specification review, read-only | parent `6dcecaa`, infra `fb92917`, current spec files | Two P1s found and repaired; targeted re-review then found the source-identity gap | Targeted re-review of `pals.source-worktree.v1` |

## Requirement evidence

| Requirement | Current design/task coverage | Code/runtime evidence | Status | Next action |
|---|---|---|---|---|
| DPB-001–007 | `specs/domainless-production-bootstrap/{requirements,design,tasks}.md` | Terraform foundation implemented in `pals-infra` `1e9c162`; full release orchestration blocked on admission authority | Partial implementation evidence | Define signed admission input, then implement deployment script and DB release completion |

## Deferred evidence

- No real AWS, Terraform apply, or secret operation has been run.
- ACM/DNS/frontend public enablement remains intentionally deferred until a domain and certificate exist.

## Implementation discovery

- `pals-infra` commit `1e9c162` implements and tests the closed Terraform modes, secret
  containers, private release task definition, and public-mode gate. It does not create
  AWS resources.
- The existing PJR foundation installer rejects an empty database without a previously
  committed signed release admission. The release task cannot manufacture that admission
  from database URLs alone without bypassing the release-authority boundary. The remaining
  orchestration/release slice therefore needs an operator-supplied signed, prevalidated
  admission artifact and a decision on its signing authority.
