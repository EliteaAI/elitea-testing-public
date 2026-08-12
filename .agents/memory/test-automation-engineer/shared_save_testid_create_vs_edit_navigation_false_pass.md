---
name: Shared save testid, create vs edit navigation false-pass
description: Reusing a create-flow save-and-wait-for-navigation helper on an edit form silently no-ops
type: feedback
---

Elitea entity forms (confirmed for Skills; likely the same shape for
Agents/Pipelines — check before assuming) reuse the SAME `data-testid`
(e.g. `skill-save-button`) for both the create form's Save button and the
edit/detail form's Save button — but they drive different hooks with
different outcomes:

- **Create flow**: Save → creates the entity → **navigates** from
  `/…/create` to `/…/{id}` (the new detail page).
- **Edit flow** (editing an already-existing entity): Save → `PUT`s the
  change → **stays on the same URL**, shows a "Saved" toast, no
  navigation.

A helper written for the create flow (e.g.
`save_and_wait_for_navigation()`) typically completes via a check like
`"/…/{id}" in url and "/create" not in url`. On an edit form that
condition is **already true before the click** (you're already on the
detail page) — reusing the helper there returns immediately without ever
waiting for the PUT to land. This is a silent false-pass, not a real
wait: the test can read stale field values right after "save" and still
go green by accident (values happened to match), or flake under load.

**Fix**: write a SEPARATE method for the edit-flow save that waits on the
actual network signal (the `PUT` response, or a save-confirmation toast
distinct from the create-flow's implicit navigation) — never reuse a
navigation-based completion check for a save that doesn't navigate.
Confirmed live for Skills: `SkillDetailPage.save_edits()`
(ELITEA-2431) waits on `PUT .../skill/prompt_lib/{project}/{skillId}` →
200 + the reused `toast-message` testid showing exact text `"Skill
saved"`, as a new additive method alongside the pre-existing
create-flow `save_and_wait_for_navigation()`.

Before writing an edit/update test for ANY entity with a create/edit form
pair, check the shared Save button's underlying hook logic
(`grep -rn "useSave" ../EliteaUI/src/[fsd]/features/<entity>/lib/hooks/`)
rather than assuming the create-flow save helper is safe to reuse.

**Round-2 gap (ELITEA-2431 fix round 1, review-caught):** waiting on the
save-confirmation toast alone is NOT sufficient to prove "no navigation" —
the toast (`version_toast_message` / `toast-message` testid) renders
app-wide via a portal, so it would still appear even if the click somehow
also routed the user away. The edit-flow save method must ALSO capture
`page.url` immediately before the click and assert it is unchanged after
the toast + network-idle wait. This is the assertion that actually proves
"stayed put" — the toast only proves "the save happened". Both checks now
live together inside `save_edits()`.
