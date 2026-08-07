---
name: Pipeline Save As Version / node-count quirks (implementer)
description: Save As Version is NEVER dirty-gated (shared component, both Agents and Pipelines); ReactFlow always renders a synthetic END node so generic node-count is off-by-one; select_version_by_name needs the reload-cycle, not a simplified poll
type: feedback
---

## Context

From ELITEA-2002 ("Create Pipeline Version — Save, List, and Switch Preserves
Canvas State"). `PipelineDetailPage`/`PipelineFormPage` gained the same
version-management surface `AgentDetailPage` already had (see
`agent_save_as_version_quirks.md`) — `save_as_version_button`,
`copy_version_id_button`, `create_version_*` dialog fields, `VERSION_OPTION`,
and the `open_save_as_version_dialog()`/`confirm_new_version()`/
`save_as_version()`/`open_version_selector()`/`is_version_option_visible()`/
`select_version_by_name()`/`close_versions_menu()`/`get_version_id()` methods.

## Reusable facts

1. **"Save As Version" is NEVER gated on form dirtiness — for EITHER Agents
   or Pipelines.** Confirmed by reading `ApplicationTabBar.jsx` (source):
   `<SaveNewVersionButton onSuccess={onSuccess} />` passes **no `disabled`
   prop at all**, so `SaveNewVersionButton.jsx`'s own
   `disabled={isSavingNewVersion || disabled}` only ever reflects a
   mid-request state. Re-confirmed live on a fresh zero-node pipeline
   (immediately after navigate AND after a 3s settle, to rule out a load
   race): Save = disabled, Discard = disabled, **Save As Version = enabled**.
   The AFS/analyst claim "Save/Save-As-Version/Discard all disabled on a
   clean baseline" is FALSE — don't assert Save As Version disabled at a
   clean baseline on either entity type; assert it enabled instead. (The
   Agent sibling test never actually asserted the pre-edit disabled state,
   so it never caught this — only "enabled once dirty", which stays
   trivially true since dirty is a subset of "always enabled".)

2. **ReactFlow always renders a synthetic END node — even on a truly
   zero-configured-node pipeline** (`PipelineAPI.create_pipeline()`, empty
   `pipeline_settings.nodes`/`edges`). Confirmed live: a fresh such pipeline
   shows ONE `.react-flow__node` (`data-id="END"`) before any node is ever
   added. This makes the pre-existing generic `get_node_count()`/
   `wait_for_node_count(expected_count)` (which count EVERY
   `.react-flow__node`) off-by-one for any "how many nodes of TYPE X"
   check — e.g. after adding 1 LLM node, total count is 2 (END + LLM), not
   1. Use the new `wait_for_node_type_count(node_type, expected_count)`
   instead (type-scoped via `.react-flow__node-{css_type}`, same mapping
   `wait_for_node_on_canvas()` already uses, scoped under `canvas_wrapper`
   per the #579 sanctioned-exception discipline) for any type-specific
   count assertion.

3. **`select_version_by_name()` needs the SAME reload-based belt-and-braces
   cycle `AgentDetailPage`'s method already uses — a simplified single
   DOM-poll is NOT sufficient, and this ISN'T the Agent-specific #614
   Publish bug.** A poll checking "VERSION trigger text == target AND
   Information-panel version-id == URL's version-id path segment" can
   resolve on a transient state where the trigger has ALREADY flipped to
   the target name while the Information-panel id / URL are STILL
   self-consistently showing the PREVIOUS version's id (both equal each
   other, so the same-value check passes without actually being on the
   target version) — observed live: switching to "base" resolved the poll
   while `copy-version-id` and the URL segment both still read the
   just-created named version's id. A full select+reload cycle (2
   attempts, same shape as the Agent method) forces a fresh server refetch
   and clears it. Since Pipelines have no Publish flow, this confirms the
   underlying staleness class is general to the VERSION-selector's
   multi-signal convergence, not tied to #614's specific trigger.

4. **`PipelineAPI.create_pipeline()` (zero-node) is genuinely a clean,
   reusable fixture — no need to hand-roll test data.** The pre-existing
   `pipeline_id` fixture (`fixtures/data_fixtures.py`) already does exactly
   what an AFS's "dedicated zero-node pipeline, created via API" precondition
   wants (name = `f"autotest_{request.node.name}"[:32]`, create + delete).
   Prefer it over a custom setup/teardown block unless the AFS needs a
   non-default name/description.

## Where

- `automation/pages/pipeline_detail_page.py` — version-management locators +
  methods (search "ELITEA-2002" in the file's section header comment) +
  `wait_for_node_type_count()`.
- `automation/pages/pipeline_form_page.py` — `save_as_version_button` +
  `is_save_as_version_enabled()`.
- `automation/tests/ui/pipelines/test_pipeline_create_version.py`.
