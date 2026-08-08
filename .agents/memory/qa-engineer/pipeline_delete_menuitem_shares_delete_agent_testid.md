---
name: Pipeline delete-pipeline menuitem shares delete-agent testid
description: "PIPELINE-group 'Delete pipeline' three-dot menu item resolves to testid delete-agent-menuitem, not delete-pipeline-menuitem — shared ApplicationControls.jsx menu-item object across Agent/Pipeline, only the label switches"
type: project
---

Confirmed live 2026-08-08 (ELITEA-2022 analysis, pipeline detail page three-dot
Actions menu): the PIPELINE-group "Delete pipeline" menu item's testid is
`delete-agent-menuitem`. `EliteaUI/src/[fsd]/entities/application-tab-bar/ui/
ApplicationControls.jsx` builds ONE `deleteApplicationMenuItem` object with
`key: 'delete-agent'`, reused for both Agent and Pipeline detail pages — only
the label text switches (`Delete ${isFromPipeline ? 'pipeline' : 'agent'}`).
`DotMenu.jsx`'s `testId: item.key` → `data-testid={testId}-menuitem` mechanism
then always produces `delete-agent-menuitem` regardless of entity type.

Don't go looking for `delete-pipeline-menuitem` — it doesn't exist. Same
pattern likely applies to any other shared `ApplicationControls.jsx` menu item
whose LABEL is entity-conditional but whose `key` is not (check the item's
`key:` field in source, not the rendered label, when deriving a testid).

Also: `PipelineDetailPage.open_actions_menu()` and `delete_pipeline_via_menu()`
still use a bounding-box JS hack / `get_by_role(name="Delete pipeline")` text
match internally despite `agent-actions-menu-button` and `delete-agent-menuitem`
both resolving correctly via `getByTestId` — pre-existing tech debt, not this
case's blocker, flagged for an opportunistic implementer simplification (same
note already left by ELITEA-2003's AFS for the three-dot button).

See `test-specs/pipelines/lextend_delete-pipeline-via-actions-menu_ELITEA-2022.md`
and `test-specs/pipelines/_surface.md`.
