---
name: pipeline_import_preview_dialog_missing_field_testids
description: Import preview dialog (agent-import-preview-dialog, shared Agent/Skill/Pipeline) has no testid on Type/Description/Chat-starters/Step-limit fields
type: project
---

The shared "Import parameters" preview dialog (`IWModalEntityCard.jsx` /
`IWModalEntityCardWrapper.jsx`, used by Agent/Skill/Pipeline import alike) only
carries `data-testid` on the dialog root (`agent-import-preview-dialog`), the
Main-entity-name title (`titleTestId` prop — `agent-import-preview-name`), and
the "Show details" toggle. The `subtitleTestId` prop the wrapper ALREADY
supports (for the "Type: pipeline"/"Type: agent" line) is never wired at the
`IWModalEntityCard.jsx` call site, and the Description/Chat-starters/Step-limit
`Typography` nodes carry no testid hook at all.

Established suite pattern (confirmed twice: ELITEA-1901
`test_import_agent_valid_md_file.py`, and ELITEA-2012
`test_pipeline_import_via_file.py`): assert only dialog rendering + Main entity
name inside the preview dialog; verify full config equivalence (description,
chat starters, step limit, node structure) on the POST-IMPORT detail page
instead (UI fields + `pipeline_api.get_pipeline()`/`agent_api` readback for
node/instructions structure) — durable and testid-backed, and matches what the
AFS's own Automation Hints usually already prefer (API readback over dialog
DOM). Don't burn a testid-adding cycle on the preview dialog's deeper fields
unless a case specifically needs to assert something ONLY visible there
(e.g. distinguishing forked vs plain import) — none has so far.

Also reconfirmed: the post-delete auto-redirect to `/pipelines/all`
(`useDeleteApplication`'s `navigate(-1)`) only works when the detail page was
reached via in-app SPA navigation with real browser history (dashboard → "+
Pipeline" → Save → detail page) — ELITEA-2022's own sanctioned-RED #1332 setup
reaches the detail page via a direct `page.goto()` instead, which is why THAT
test sees the no-op. A test that creates its pipeline entirely through UI
clicks (no `page.goto()` mid-flow) gets a working redirect and can assert it
as a hard requirement, not a soft/known-defect one.
