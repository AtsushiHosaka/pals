# PALS Chat UI Redesign QA

final result: passed

Reference:
- User-provided ChatGPT sidebar/chat screenshot.
- User-provided Create project modal screenshot.
- AI Elements prompt-input reference: https://elements.ai-sdk.dev/components/prompt-input

Checked:
- Desktop home shows chat-first empty state, left navigation, project creation entry points, and prompt input above the fold.
- Desktop Create project modal matches the white/black rounded dialog direction with dimmed backdrop and compact controls.
- Desktop project page keeps chat as the main surface and shows proof progress without horizontal overflow.
- Mobile home keeps the primary prompt input visible in the initial viewport without horizontal or vertical clipping.
- Mobile project page preserves access to the project prompt and progress surface with vertical scrolling.

Evidence:
- `/private/tmp/pals-screenshots/11-chat-home-desktop-final.jpg`
- `/private/tmp/pals-screenshots/12-create-project-modal-desktop-final.jpg`
- `/private/tmp/pals-screenshots/13-project-chat-empty-desktop-final.jpg`
- `/private/tmp/pals-screenshots/14-project-chat-proof-job-desktop-final.jpg`
- `/private/tmp/pals-screenshots/17-chat-home-mobile-final-fit.jpg`
- `/private/tmp/pals-screenshots/16-project-chat-mobile-final.jpg`

Notes:
- The real agent runtime is still intentionally mocked; the project chat queues the existing proof job flow.
- Remaining polish is P3: simplify project creation advanced fields into a disclosure if the modal should match the reference even more tightly.
