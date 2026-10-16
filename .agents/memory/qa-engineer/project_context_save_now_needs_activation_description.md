---
name: Project Context Save now requires activation_description, not just isDirty
description: ELITEA-2272's "Save gated purely on isDirty" finding (2026-08-05) is STALE as of 2026-10-16 — the create/edit flow's Save button also requires a non-empty "Activation description" input (new testid project-context-activation-description) to enable; re-verify ELITEA-2272's own test before touching this page object.
type: feedback
---

## What changed

`test-specs/settings-project-params/l2_project-context-character-limit-2500_ELITEA-2272.md`
(analysed 2026-08-05, pre-ladder/pre-DEV-cutover) documents that the Project
Context editor's Save/Discard/Cancel buttons are gated purely on `isDirty`
(any edit at all), independent of character count or any other field. That
finding was correct **at the time** and is the basis of ELITEA-2272's own
regression assertion (#5667 — Save enabled at the 2500-char boundary).

Confirmed live on DEV (`https://dev.elitea.ai/app/settings/project-context`,
2026-10-16, during ELITEA-3252/3253/3254/3255 analysis): the create/edit
flow now has a second required field, "Activation description"
(`data-testid="project-context-activation-description"`, a plain `<input>`,
max 300 chars, label "When should this context be used?"). **Save stays
disabled even after typing into the main CodeMirror editor** until this
second field also has content. Only once BOTH fields are non-empty does Save
become clickable.

## Why it matters

- Any new test on this page that only fills the editor and expects Save to
  enable (following ELITEA-2272's documented pattern) will time out waiting
  for an enabled Save button that never arrives.
- ELITEA-2272's own merged test may itself now be failing/stale if its
  fixture doesn't fill this field — this is a shared-component regression
  risk, not something to patch silently inside a new test file. Re-run
  ELITEA-2272's test before/alongside any new Project Context work and flag
  it to the lead if red.
- The REST `GET`/`PUT` payload also grew an `activation_description` field
  (was absent from the shape ELITEA-2272 documented).

## Where the full detail lives

`test-specs/settings-project-params/_surface.md` (updated 2026-10-16) and the
family AFS `l1_project-context-char-limit-enforced-across-surfaces_ELITEA-3252.md`
— also documents three new entry points confirmed live: empty-state "Build
with AI" (testid-less, role/label rungs), saved-view "Edit with AI" (new
testids `ai-edit-project-context-*`), and the Chat `project_context_builder`
module tool (`put_project_context`, not `generate_project_context_draft` as
some TMS case text names it).
