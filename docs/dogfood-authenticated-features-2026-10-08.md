# Authenticated feature dogfood — partial, October 8, 2026

The requested full feature QA is incomplete. The approved test account's public PALS session was reused, but the deployed UI identifies it as Free. Project creation redirects to Billing, and purchases are disabled. QA Pro activation is still a prerequisite; no entitlement or infrastructure changes were performed in this QA run.

The `dogfood` skill was used against the deployed browser UI, approximately 20:38–20:49 JST. The coordinator alone operated the existing Chrome tab; an independent agent prepared and validated synthetic text PDF, scanned PDF and PNG fixtures and reviewed the answers. The deployed revision is unknown. No application implementation was inspected to discover bugs.

| Coverage | Observed result |
|---|---|
| Chat generation and formulas | A substantive continuous zero theorem succeeded on first submission, with rendered prompt/answer formulas and a mathematically correct IVT/EVT proof. |
| Context and response language | Japanese follow-up produced a correct discontinuous ±1 counterexample with zero integral. |
| Search and persistence | Search found the synthetic chat; navigation and reload retained question/answer; subsequent navigation retained follow-up. |
| Settings | Language and a representative notation substitution persisted after settling; identifier validation worked. Original preferences restored. Mathematics settings failed on open and Retry. |
| Sharing | Snapshot preview failed on open, Retry and again after successful answers. Publication and shared view remain untested. |
| Formal Lean job | Coprime-divisibility request failed on initial submission and Retry; source stayed disabled. Formal compilation, receipts and source/explanation mapping remain unverified. |
| Usage | Two successful answers reduced Free requests from 3 to 1. Failed formal attempts left the remaining request available. Pro accounting and exhaustion untested. |
| Responsive/keyboard slice | 390×844 chat and mobile navigation inspected; Escape closed the menu and restored trigger focus. Actual mobile hardware and screen reader untested. |
| Projects, PDF/PNG and AI OCR | Project empty list/paywall checked only. Project creation/edit/save/reload, uploads, OCR and material-backed answers remain pending. Fixtures were prepared, not uploaded. |
| Model selection | No selector in inspected Free home/chat/settings surfaces. Actual model identity/switching unverified. |

Three failed feature paths were reproduced: Mathematics loading (2 attempts), sharing preview (3 attempts), and the explicit formal request (2 attempts). These counts describe this run, not prevalence across users. Root causes were not investigated or repaired. No app-wide PASS is claimed.

Local detailed report and screenshots: `outputs/dogfood/2026-10-08-pro-full/report.md` and `qa/`. Generated evidence and synthetic fixtures are ignored and excluded from Git. No credentials, account identifiers or authentication state are included in this tracked record.

The user was asked to activate QA Pro or confirm activation in progress. The existing Pro setup chat reports activation pending Mac mini administrator authentication. Resume in the same browser when the test account visibly has Pro, then finish Projects, text/scanned PDF, PNG/OCR, material-backed chat, newly exposed paid/model features and unresolved paths. No message was sent to another chat.
