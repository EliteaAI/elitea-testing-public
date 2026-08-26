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

## Skill icon upload — same dialog, extra asymmetry (ELITEA-2604, confirmed live 2026-08-12)

- **Create mode (no `entityId` yet) vs edit mode (`entityId` present) fire a DIFFERENT number of
  requests on a successful upload.** Create: one `POST .../upload_skill_icon/prompt_lib/{project}`
  → 200, applied to local form state only. Edit: the SAME `POST` (200) is immediately followed by a
  second `PUT .../upload_skill_icon/prompt_lib/{project}/{versionId}` → 200 that applies+persists
  to the version right away — two toasts fire in sequence ("The image has been uploaded" then "The
  icon has been changed"), not one. An assertion written against create mode's single-toast
  behavior (e.g. `SkillFormPage.upload_skill_icon()`'s exact-text toast check) is WRONG if reused
  verbatim for an edit-mode variant — assert on the network pair or the resulting `img.src` instead.
- **Oversized-file (>500KB) rejection is 100% server-side**, no client pre-flight check exists —
  the POST always fires, the backend returns 400 with body `{"error": "File size exceeds 512 KB"}`.
  The dialog's own tooltip says "less than 500KB" (same numeric limit, inconsistent unit-label
  string vs the error's "512 KB" — cosmetic, not a bug). Dialog stays open, previous icon retained
  on rejection.
- **Two independent, both-testid'd "revert to default" mechanisms exist** — don't assume only one:
  (a) delete the currently-selected icon from the "Uploaded" gallery (hover-revealed delete
  `IconButton` inside `UserIconItem.jsx`, **NO testid on that button as of 2026-08-12** — only a
  `className="deleteButton"`; confirms via `DELETE .../upload_skill_icon/prompt_lib/{project}/
  {icon_name}` → 200, toast "The icon has been successfully deleted."), or (b) click the "Default"
  tile (`agent-icon-picker-default-icon`, pre-existing testid) which in edit mode PUTs
  `{name: "", url: ""}`, toast "The icon has been reset to default icon". Both revert
  `*-form-icon-img` to an ABSENT `<img>` element (the product's actual default state — never a
  literal `skill-icon.svg`/similar filename despite some case text implying one), confirmed to
  survive a full page reload (server-persisted, not optimistic-only).
