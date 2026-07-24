---
name: get_node_count() counts the END node too
description: PipelineDetailPage.get_node_count() counts every .react-flow__node in the DOM, including the implicit END node — an AFS claiming "N custom nodes, END not counted" was factually wrong and caught only by running get_node_ids() live.
type: feedback
---

## What happened (ELITEA-2031, isolated worktree `wf_e44028a9-dec-156`)

The AFS for ELITEA-2031 (a pipeline with exactly 2 custom nodes — `LLM 1` +
`Printer 1`, both transitioning to `END`) asserted `get_node_count() == 2`,
with an explicit note: "the `END` node is not counted by the existing
helper's own convention." Written from the analyst's live session (pipeline
id `5771`), so not a guess — but wrong.

Phase 4 (Execute) failed on the very first run: `AssertionError: Expected 2
nodes ... got 3`. A quick debug test (`get_node_ids()`) confirmed the real
DOM state: `['END', 'LLM 1', 'Printer 1']` — `get_node_count()` counts every
`.react-flow__node` element, END included, with no special-casing.

**This matches the already-merged `test_save_multi_node_pipeline`
precedent**: 1 custom node (LLM) + END == 2 nodes. For 2 custom nodes + END,
3 is the only value consistent with that established, working test. The
AFS's "2, END not counted" framing directly contradicted a sibling test
already on `automation/base` — a contradiction that a coverage-map read alone
doesn't surface, only actually running `get_node_count()`/`get_node_ids()`
against the live fixture does.

## The generalizable lesson

**For any pipeline case asserting `get_node_count()` against a specific
number, count END as one of the nodes** (`custom_node_count + 1`), and don't
trust an AFS's node-count claim without a live `get_node_ids()` cross-check
against the pipeline's actual custom-node set — even when the AFS states the
count was "confirmed live this session," since a human/analyst miscounting a
small, easy-to-miss node in a screenshot is a real, recurring failure mode,
independent of whether the *feature under test* had a real defect (this one
didn't — the drag-connect/save/reload/persistence mechanism worked exactly
as described; only the incidental node-count baseline assertion was wrong).

Amended the AFS in place (`docs(afs): amend node-count assertion per
implementer exploration`) rather than silently drifting from it, per the
Phase 2 amend-in-PR rule — R1 fix, well within the implementer's 2-rerun
budget (from ELITEA-2031, PR TBD).
