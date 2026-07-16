---
name: Fork agent flow and localhost dev-token permission scoping
description: ELITEA-1893 — Fork wizard testid gaps (Fork menuitem/button/project-select all missing), select-option-{projectId} stable handle, and the critical localhost caveat that VITE_DEV_TOKEN has non-uniform per-project permissions
type: feedback
---

## Fork wizard (agent → different project) — what's live-confirmed

- Entry point: agent-actions overflow menu (`agent-actions-menu-button`) →
  VERSION group → **Fork** menuitem. Wizard dialog testid swaps between
  `agent-import-preview-dialog` (pre-fork) and `agent-import-complete-dialog`
  (post-fork) — same container, don't assert a single fixed testid across
  the action.
- Project-select dropdown options carry a genuinely stable, semantic handle:
  `select-option-{projectId}` (numeric project id, not list position) —
  confirmed for 399/400/471. Reusable pattern for any MUI-Select-driven
  project picker in this app.
- Success dialog's per-category value carries `agent-import-complete-list-{entityKey}`
  where `entityKey` ∈ `pipelines|agents|toolkits|skills|skipped_toolkits`.
- Fork correctly shows ONLY a "Main entity" card (no "Nested entities"
  section) when the source agent has no attached toolkits/skills/sub-agents
  — data-driven, not a missing-UI bug (same pattern as ELITEA-1894's export
  finding).
- Forked agent has a "Forked from: {name}" traceability link back to the
  source — no testid, bonus handle, not required by ELITEA-1893's case
  text.

## Testid gap: THREE elements on the Fork path have zero testid

1. **Fork menuitem** — `useForkEntityMenu()` in `ForkEntityButton.jsx` never
   sets `key` on its returned `menuItem`; the rendering `DotMenu.jsx` only
   emits `data-testid={testId ? \`${testId}-menuitem\` : undefined}` where
   `testId = item.key`. Sibling `Export` menuitem DOES set
   `key: 'agent-actions-export'` in its own hook — Fork's hook simply
   forgot to. One-line fix: add `key: 'agent-actions-fork'`.
2. **Fork confirm button** (`IWModalForkButton.jsx`) — bare `Button.BaseBtn`,
   no `data-testid` prop at all. Sibling `IWModalImportButton.jsx` DOES have
   `agent-import-confirm-button`.
3. **Fork wizard Project selector** (`@/components/ProjectSelect`) — no
   testid on the trigger itself (only the dropdown's individual options
   have one, via `select-option-{id}`).

This is the same recurring pattern already logged in
`pin_toggler_widget_testid_gaps.md` and `ELITEA-1974/1975` sessions: a
shared component family gets testids added to SOME call sites/siblings but
not others — always diff against the nearest sibling (Export vs Fork,
Import-button vs Fork-button) rather than assuming parity.

## CRITICAL environment caveat — localhost dev-token has non-uniform per-project permissions

On localhost, every request is authenticated by ONE fixed identity
(`VITE_DEV_TOKEN`, injected by the Vite proxy in `EliteaUI/vite.config.js`)
— **regardless of which project is selected in the UI**. This identity's
permission set is NOT uniform across projects. Confirmed live:

- `Private` (399, the identity's own/home project) and `UI Testing` (400):
  full CRUD, including `models.applications.application.delete`.
- `Elitea Testing Team` (471): has `models.applications.fork.post` (so
  Fork-INTO this project succeeds, 201) but LACKS
  `models.applications.application.delete` (so cleanup DELETE 403s with
  `{"error":"access_denied","required":["models.applications.application.delete"]}`
  and a UI toast "Insufficient permissions to perform this action on
  {project} project").

**Actionable rule for future cases needing a "different project" as test
data**: before choosing a target/cross-project fixture, verify
`GET /api/v2/auth/permissions/prompt_lib/{id}` includes the permission
you'll need for cleanup (`models.applications.application.delete` for
agents), don't just check the action-under-test's own permission. `Private`
(399) and `UI Testing` (400) are known-good full-CRUD projects for the
dev-token identity as of this session (2026-07-16) — prefer them as
cross-project fixture targets over `Elitea Testing Team` (471) or the
untested `Bugs & Features` (406) / `Elitea Development` (25).

Known leftover from this session: forked agent id 146 ("Test Agent",
version 151) still lives, undeleted, in project 471 — needs an
admin/elevated credential to clean up; not a product defect.
