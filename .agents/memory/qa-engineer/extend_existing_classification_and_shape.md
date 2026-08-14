---
name: extend-existing — classification and shape
description: already-covered needs a completed board task that delivered THIS case's traceability, not just a behaviourally identical test; and extend-existing has three shapes (insert at the end, insert at an interior point, or a sibling method) chosen by state-machine fit and data-precondition conflict.
type: feedback
---

## Classification

- **`already-covered` is board-first, not code-first.** It requires a tracked
  card for THIS case that reached a terminal state with the case's own
  traceability actually delivered. Behavioural equivalence to a merged test is
  necessary, never sufficient.
- TMS frontmatter `execution_type: automated` is a folder-level planning flag —
  never proof any specific case is done. A `CLOSED`/`NOT_PLANNED` card is not a
  completion.
- **Any remaining code change ⇒ `extend-existing`**, however small — one
  missing `@allure.issue` link to this case is real work. Size doesn't matter;
  whether ANY code change is owed does.
- Targets must be specs **merged to base**, never a same-batch AFS.
- **Deeper/wider instance of the same parameter** (depth 1→2, one file→N, one
  entry point→another): ask whether the deeper instance could pass while a real
  bug exists that the shallow instance's assertions structurally cannot catch.
  Yes ⇒ `extend-existing`; if it's only "the identical assertion with bigger
  N" ⇒ `already-covered`.
- If the extension would be a near-rewrite of the covering spec ⇒
  `ready-for-automation`, not `extend-existing`.

## Shape — three options, in order of preference

1. **Insert into the covering test's own body** (default). Use when the gap
   assertions are more states of a single continuous state machine (validation
   progressions, wizard steps, toggle sequences). Reuses setup already paid
   for; renumber the `allure.step` labels. The skill's own wording — "extends
   the covering spec" — means the existing test grows, not that a second one
   appears beside it.
2. **Insert at an interior point that already walks the needed state.** Before
   defaulting to "append at the end", check whether the covering test's
   existing code already reaches and asserts near the state the new case needs
   — if so, insert two small assertions there rather than duplicating the walk.
3. **New sibling `test()` method in the same file/class.** Only when the gap is
   a genuinely separate scenario sharing only setup: a different entry point,
   or a **data-precondition conflict** — the gap case needs an object to
   survive that the covering test deletes as its own core assertion (breaking
   its later numeric asserts). Check for that conflict BEFORE defaulting to
   "insert". Duplicated setup is then the honest cost of test independence.

## Seen 5×

- ELITEA-1796 — human overturned an analyst's `already-covered`; a behaviourally identical merged test with no `@allure.issue` for this case is `extend-existing`. Source of the board-first criterion.
- ELITEA-1871 — insert-into-body default established (Save-enablement state machine; 2 inserted steps + renumbering).
- ELITEA-1827 — depth-1 → depth-2 of the same parameter ⇒ extend, appended as a new flow at the end of the covering test.
- ELITEA-1835 — the covering test's own existing recovery block already reached the state; correct shape was two interior insertions, not a third appended flow.
- ELITEA-1846 — sibling method: the covering test deletes the very folder this case needs to survive, and computes pagination asserts from that deletion.

(Surface facts for the Artifacts cases live in their own demoted files.)

See also: extend_existing_means_insert_into_same_test_not_sibling_method.md ·
coverage_classification_needs_board_task_not_just_behavioral_match.md ·
artifacts_nested_folder_lazy_tree_and_extend_boundary_elitea1827.md ·
artifacts_upload_dialog_description_text_generic_at_root_elitea1835.md ·
artifacts_stale_selection_after_delete_and_sibling_method_extend_shape_elitea1846.md
