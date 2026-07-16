---
name: Agent form dual-component and icon-picker quirks
description: CreateAgentForm.jsx (create route) vs ApplicationEditForm.jsx (detail/edit route) are TWO different React components sharing identical agent-name-input/agent-description-input testid strings — a testid edit to only one has zero effect on the other route. Also documents the icon-picker's two-click-to-open quirk and its auto-persist-on-select behavior (decoupled from the form Save button).
type: feedback
---

## The gotcha

`EliteaUI/src/[fsd]/features/agent/ui/agent-details/configurations/form/CreateAgentForm.jsx`
(rendered only by `/agents/create`) and
`EliteaUI/src/pages/Applications/Components/Applications/ApplicationEditForm.jsx` (rendered by
the `/agents/all/{id}` detail/edit page) are **two separate component files** that happen to
reuse the exact same testid strings (`agent-name-input`, `agent-description-input`,
`agent-save-button`, etc.). This is easy to miss because a `grep` for the testid string alone
looks like "one component" if you only check one hit.

**Consequence:** if you add/change a `data-testid` prop on a shared child component (e.g.
`EntityIcon`) at only ONE of the two call sites, it silently has zero effect on the other route.
HMR will recompile fine, no console error, the testid will just be MISSING in the DOM on whichever
route you didn't touch. Symptom looks exactly like "HMR didn't pick up my change" — it's not a
caching bug, it's the wrong file.

**Fix/verification pattern:** before declaring a testid change complete, `grep -rln
"<existing-sibling-testid>" src/` for testids you know already work on both routes
(`agent-name-input` is a reliable canary) — if it returns 2+ files, your new testid prop needs to
land in ALL of them, not just the one you found first via the component tree from one route.

## Icon-picker behavior (SelectIconDialog / EntityIcon), confirmed live 2026-07-16

- The icon avatar (`EntityIcon` with `editable={true}`) only fires its `onClick` (which opens
  `SelectIconDialog`) once its hover-triggered `EditIcon` pencil overlay is already mounted. A
  single scripted Playwright `.click()` with no prior `hover()` lands on the pre-hover DOM node
  and only triggers the `onMouseEnter` state — it does NOT open the dialog. A second click (now
  hovering) does. Reproduced deterministically 2/2. **Automation must `hover()` before `click()`,
  or click twice.** Real users are unaffected (mouse naturally hovers before a real click).
- Selecting an icon in the picker **persists immediately and independently** via `PUT
  /api/v2/elitea_core/upload_icon/prompt_lib/{project}/{versionId}` — decoupled from the agent
  form's main Save/Discard state. The main "Save" button stays disabled after an icon-only change.
  Don't assert on the form Save button for icon persistence; assert on the PUT response or the
  DOM `img.src` update instead. Filed as CLARIFICATION `elitea-testing-public#566` since TMS case
  ELITEA-1899's step 5 ("Click Save") implies a mechanism that doesn't exist for this field.
