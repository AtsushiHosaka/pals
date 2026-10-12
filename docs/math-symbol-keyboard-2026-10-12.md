# Math symbol keyboard — 2026-10-12

PALS now has a Σ toggle immediately beside the file + button in the shared composer. The keyboard starts closed. Clicking its toggle opens or closes it; Escape or the close button closes it. Existing attachment, model selection, and submission controls remain available.

The palette follows Wolfram Alpha's grouped symbol/template pattern, adapted to PALS's ordinary-text composer. Official reference: [Math Input](https://www.wolframalpha.com/math/math-input). The symbol inventory is a PALS selection, not a complete copy of Wolfram Alpha's keyboard.

| Group | Keys |
| --- | --- |
| Common | Fraction, power, subscript, root; + − × ÷ ± = ≠ < > ≤ ≥ ≈ · ∞ π and brackets |
| Calculus | ∑ ∏ ∫ ∬ ∮ ∂ ∇ → ′ ″ lim sin cos tan log ln |
| Logic & sets | ∀ ∃ ¬ ∧ ∨ ⇒ ⇔ ∈ ∉ ⊂ ⊆ ⊃ ⊇ ∪ ∩ ∅ ℕ ℤ ℚ ℝ ℂ and braces |
| Greek | Lowercase Greek letters and common uppercase Greek letters |

Keys insert at the saved cursor or replace selected text. Templates place the cursor inside an editable slot. Power/subscript shortcuts wrap a selected base in parentheses, preserving the grouping of composite expressions. These are text shortcuts; the composer remains a textarea. Length-limit overflow is rejected atomically. Disabled, uploading, pending, and active IME composition states block symbol insertion. All four UI locales have translated control labels.

Frontend commit: `e71277599d3d968fec7b8bf22750ff57a35bb677`. Draft implementation PR: [pals-webfront #19](https://github.com/AtsushiHosaka/pals-webfront/pull/19).

Validation: 58 focused tests, TypeScript, focused ESLint, and diff checks pass after integrating frontend main. Browser checks confirm selection replacement and caret focus, toggling, Escape, desktop layout, and 390px mobile width without horizontal overflow. Mobile keys scroll within a 194px area. The guest layout used a temporary local session fixture, and no proof request was submitted. Production deployment, provider processing, and authenticated backend outcomes are not claimed.

Local visual evidence (outside Git):

- Desktop: `/Users/atsushi/.codex/visualizations/2026/10/12/01a12eaa-c882-7512-9921-59ff93d92203/math-keyboard-chat-desktop.jpg`
- Mobile: `/Users/atsushi/.codex/visualizations/2026/10/12/01a12eaa-c882-7512-9921-59ff93d92203/math-keyboard-chat-mobile.jpg`
- Collapsed: `/Users/atsushi/.codex/visualizations/2026/10/12/01a12eaa-c882-7512-9921-59ff93d92203/math-keyboard-chat-collapsed.jpg`

This integration preserves the existing attachment work from [parent PR #47](https://github.com/AtsushiHosaka/pals/pull/47). Its inherited API/agent/infra pins belong to that prerequisite; the keyboard changes are frontend-only. The parent pointer was updated after the frontend push succeeded. No merge or deployment was performed.
