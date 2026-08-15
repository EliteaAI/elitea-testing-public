---
name: Manual gate scope — discover touched files via `git diff --name-only base...trunk`, never from memory of the report
description: when substituting a manual gate for a cut-off workflow gate, guessing which files a batch touched (from recollection of unit summaries) can silently skip a whole file — run the diff, don't recall it
type: feedback
---

## What happened (2026-08-15, chat-remaining wave-06, PR #1539)

The workflow's internal gate was cut off mid-run (0/3 banked, known failure
mode — `workflow_internal_gate_two_failures_run_it_yourself.md`). I ran my own
gate manually, but scoped it to the ONE file I remembered from the unit
summaries (`test_chat_folder_rename_checkmark_validation.py`, which held 5 of
the wave's 7 build units). I never ran `git diff --name-only base...trunk`
myself — I reconstructed the file list from memory of what I'd read in the
workflow's journal output. **I missed that ELITEA-2128/2129 landed in a
brand-new file, `test_chat_folder_rename_length_boundaries.py`**, created by a
LATER unit in the same wave. I merged the trunk→base PR having never run that
file once — a real "gate after merge" violation (`.agents/testing.md`'s
baf8f3cf anti-pattern class), caught only when back-writing the TMS and
cross-checking node-ids against `junit.xml` (which only had the one file's
7 tests, not the other file's 2).

Recovered: ran the missed file 3× immediately post-merge (clean 3/3), so the
delivered code was fine — but the PROCESS was wrong, and a genuinely broken
file could have merged undetected the same way.

## Rule going forward

**Before running a manual gate, always run the discovery command yourself —
never reconstruct the touched-file list from memory of unit summaries:**

```bash
git diff --name-only origin/automation/base...tests/batch-<slug> -- automation/tests/
```

This is the SAME discipline `large_batch_gate_scope_by_nodeid_not_file.md`
already established for the opposite failure (file-level scope sweeping in
TOO MANY unrelated tests) — the fix there and here is the same command, just
applied for a different reason: to get the COMPLETE and CORRECT file set, not
a remembered subset. A multi-unit wave where later units add whole new files
(not just new methods to files earlier units touched) is exactly the case
where memory-based reconstruction silently drops a file — the units complete
sequentially and their summaries scroll past each other in the journal long
before the gate step runs.

**Self-check before opening the trunk→base PR:** the manual gate's node-id/
file list must be cross-checked against `git diff --name-only` output, not
just "what I remember the units doing." If in doubt, run the diff twice —
once before starting the gate (to plan it), once right before merging (to
confirm nothing changed underneath you).
