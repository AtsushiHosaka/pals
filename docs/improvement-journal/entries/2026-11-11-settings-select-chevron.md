# Settings select chevron spacing (2026-11-11)

- Target: interface visual correctness. No claim about mathematical answer success,
  generation time or model cost.
- Hypothesis: native dropdown decoration ignores the intended shared field inset;
  controlling only the chevron can correct spacing while preserving native input.
- Change: [#339](https://github.com/AtsushiHosaka/pals/issues/339), based on Web
  `272b8af06999f59be146ae6e2b61050901f9ed7c`. Single-line select decoration and
  an enforced browser appearance regression; all settings behavior is preserved.
- Conditions: local macOS Chromium, actual source CSS in an isolated fixture,
  desktop 1024px and phone-width 375px, no authentication or provider/model calls.
- Result: visible chevron edge inset 5px before and 17px after in both layouts.
  Baseline fails the 10px minimum; corrected controls pass. Final vertical center
  error is 0.5px. Five browser regression checks pass, including native fallback
  and keyboard behavior. These checks are not proof of production acceptance.
- Decision: prepare the fix for review and normal release. No deployment or
  account setting changes were performed.
- Cost: no paid model calls. No answer-latency or cost improvement was measured.
- Limits: isolated CSS/browser fixture; Safari, physical devices and authenticated
  production save/reload remain unverified.
- Evidence: [measurement report](../../settings-select-chevron-2026-11-11.md),
  ledger IDs `2026-11-11-select-chevron-baseline` and
  `2026-11-11-select-chevron-corrected`.
