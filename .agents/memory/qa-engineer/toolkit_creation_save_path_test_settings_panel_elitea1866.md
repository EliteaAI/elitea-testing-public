---
name: Toolkit-creation Save path + TEST SETTINGS/RUN TOOL panel are testid'd (ELITEA-1866)
description: The full Save path of Artifact-toolkit creation (16 tool chips with data-selected state, MCP checkbox, post-save detail view) and the TEST SETTINGS/Tool-dropdown/RUN TOOL panel are largely testid'd on automation/testids already (mui-patterns.md's legacy "TESTIDS NEEDED" note for this panel is now stale) — only the Recursive checkbox and RUN TOOL button remain gaps. Info-tooltip click-vs-hover interaction-mode CLARIFICATION pattern documented.
type: feedback
---

## Context

ELITEA-1866 (analyst pass, 2026-07-20): create an Artifact toolkit via the Save path (not
Cancel — that's the sibling ELITEA-1868 case), verify the full creation-form UI, run the "List
files" tool against the newly-created bucket via the toolkit detail page's TEST SETTINGS panel,
then confirm the bucket shows up empty in the Artifacts section. AFS:
`test-specs/artifacts/l2_create-bucket-via-toolkit-verify-list-files_ELITEA-1866.md`.

## Findings worth keeping

1. **TOOLS section's 16 tool "checkmarks" are MUI Chips with a compliant
   testid+data-attribute state pattern.** `toolkit-tool-chip-{tool_key}` (dynamic
   template, `ToolActionsItems.jsx`) + `data-selected="true"/"false"` on the SAME
   element — exactly the shape `.agents/testing.md`'s PR #581 ruling requires (stable
   testid, state via `data-*`, never a state-toggled testid). Assert BOTH the count
   (16) and every chip's `data-selected==="true"`, not count alone — a chip present
   but unselected would silently pass a count-only check while failing the case's
   real "with checkmarks" intent.

2. **`.claude/rules/mui-patterns.md`'s "Test Settings Panel — TESTIDS NEEDED" section
   is now STALE for most of the panel.** That doc (predates this ruling) says to use
   label-text + bounding-box filtering because "Test Settings panel has NO testids".
   Live reality this session: `toolkit-test-tool-select`/`-combobox` (Tool dropdown),
   `toolkit-test-param-{fieldKey}` (a generic template covering `bucket_name`,
   `folder`, `include`, `skip` — shared by `CommonStringField.jsx`/
   `AnyOfPatternField.jsx`), and `model-selector-button`/`-name` are ALL testid'd on
   `automation/testids`. Only 2 genuine gaps remain in this exact panel: the
   **Recursive checkbox** (`CommonBooleanField.jsx`'s wrapper `<Box>` omits the
   `data-testid={...}` its sibling string/array-field renderers set — a one-renderer
   gap in an otherwise-consistent template family, `testid needed:
   toolkit-test-param-recursive`) and the **RUN TOOL button**
   (`TestToolSettings.jsx`'s `Button.BaseBtn`, no `data-testid` prop wired at all,
   `testid needed: toolkit-test-run-tool-button`). Don't trust that legacy doc's
   blanket "no testids" claim without re-checking live — it will mislead a future
   case into using the label-text/bounding-box workaround for fields that already
   have a real testid.

3. **`select-option-{value}` (the generic MUI-select-menu-item testid,
   `SingleSelectMenuItem.jsx`) is already ON MAIN**, not just `automation/testids` —
   confirmed via fresh `git grep` against both refs. Useful precedent: this shared
   component's default-testid mechanism (`option.testId ?? \`select-option-${value}\`\`)
   is reused for BOTH the toolkit-type-picker's category dropdown context AND the
   TEST SETTINGS Tool dropdown — same component, two different call sites, zero
   duplication needed.

4. **Toolkit-create's POST doubles as bucket-create — no separate bucket POST
   fires.** `POST /api/v2/elitea_core/tools/prompt_lib/{project}` returns `201` and
   IS the entire mutation for "create toolkit + create its bucket" — confirmed via
   full network-log inspection across the whole create-and-save flow, no
   `/artifacts/buckets/...` POST appears anywhere. If a future case needs to assert
   "toolkit save creates a bucket" at the network level (not just the eventual UI
   empty-state), this is the single request to watch, not two.

5. **Info-tooltip interaction-mode CLARIFICATION pattern (reusable across ANY case
   touching `InfoTooltip.jsx`)**: this shared component (used on Pgvector
   Configuration / Embedding Model / Bucket fields on this SAME form, and elsewhere
   in the app) is a plain MUI `<Tooltip>` with no `onClick` wired — it opens on
   **hover**, not click, confirmed via source read. A TMS case saying "click the
   info icon" is describing the WRONG activation mode; per the interaction-discovery
   ladder, this is case-text drift (CLARIFICATION, [#669](https://github.com/EliteaAI/elitea-testing-public/issues/669)),
   not a product defect — the tooltip content itself was correct. Any future case
   touching an `InfoTooltip` instance should default to `.hover()`, verify via source
   first if the case text says "click".

6. **Toolkit deletion (kebab "..." menu -> "Delete" -> type name to confirm -> Delete)
   has NO equivalent to the #636 bucket-delete defect.** `ArtifactAPI._toolkits_url()`/
   `delete_toolkit()` in `automation/api/client.py` builds
   `elitea_core/tool/prompt_lib/{project_id}/{toolkit_id}` — the EXACT same shape the
   live UI's own delete call uses (confirmed live, clean `204 No Content`). Safe to
   use directly for any future case's toolkit teardown, unlike bucket teardown (see
   the amended ELITEA-1817 memory entry for the bucket-delete gotcha and its live
   confirmation this session).

7. **Cleanup design for a case with literal (non-randomized), case-mandated test-data
   names**: most artifact/toolkit AFSs randomize their own test data
   (`autotest-*-{random}`) to sidestep collision entirely. This case's TMS Test Data
   table specifies fixed literal names (`my-artifact-toolkit`/`new-bucket`) AND its
   own Preconditions require their ABSENCE before the run — randomizing them would
   deviate from the case. The correct shape (documented in full in this AFS's
   § Test Data): idempotent PRE-test best-effort cleanup (handles a leftover from a
   previously-failed run) + guaranteed POST-test teardown (`finally`/fixture), with
   the bucket half specifically routed through the UI dot-menu flow (not the broken
   API method) per finding #6 above and the ELITEA-1817 memory entry.
