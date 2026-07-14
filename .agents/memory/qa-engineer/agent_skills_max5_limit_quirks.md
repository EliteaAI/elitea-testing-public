---
name: Agent skills max-5 limit quirks
description: Agent-Skills 5-skill limit is enforced by proactively disabling the add-skill button (aria-label wrapper "Maximum number of skills reached") the instant 5/5 is reached, not by rejecting a 6th click; verified live, no defect
type: feedback
---

Discovered while analysing ELITEA-1790 (Maximum 5 Skills can be attached to one
Agent, localhost:5173):

- **The 5-skill-per-agent limit is enforced client-side, proactively, at
  exactly 5/5** — not by allowing a 6th attach attempt and then showing an
  error. The instant the 5th skill's `PATCH .../skill/prompt_lib/{project}/{id}`
  → `201` resolves, the add-skill button itself gets wrapped in
  `<span aria-label="Maximum number of skills reached">` and the inner
  `<button>` receives the `disabled` attribute. Confirmed via `browser_evaluate`
  DOM inspection.
- **The disable is real at the actionability level, not just a visual/CSS
  cue.** A genuine Playwright `click()` targeting the button (scoped via the
  `aria-label` wrapper) times out after 5s with "element is not enabled" — it
  never becomes clickable, so there's no click-and-see-error flow to automate.
  **Automation should assert `expect(button).toBeDisabled()` (+ optionally the
  wrapper's `aria-label` text), not attempt a literal click expecting a
  rejection message** — that click would hang by design.
- **No `data-testid` on the add-skill button or its tooltip wrapper** — same
  gap already documented for the normal (<5) state in
  `agent_skill_mention_and_autoload_quirks.md`. The only reliable handle at 5/5
  is `[aria-label="Maximum number of skills reached"] button`.
- **At 4/5, the popper still lists all remaining unattached skills as
  selectable** — the limit engages strictly at 5, confirmed by reopening the
  popper right before the 5th attach.
- **`getByRole('menuitem', { name: 'elitea-1790-skill-N' })` without
  `exact: true` ambiguously matches multiple menuitems** when skill names share
  a common prefix (e.g. `elitea-1790-skill-2` through `-skill-6`) — Playwright's
  generated code silently collapsed the accessible name to a shared substring
  in one attempt. Always pass `exact: true` when skill/agent test-data names
  share a prefix.
- **No defect found** — this case passed cleanly end-to-end; the product's
  enforcement is actually stronger than the case text's "error message or
  disabled state" bar (proactive disable beats reactive rejection for both UX
  and automatability).
- Full AFS: `test-specs/skills/lp1_max-5-skills-per-agent_ELITEA-1790.md`.
