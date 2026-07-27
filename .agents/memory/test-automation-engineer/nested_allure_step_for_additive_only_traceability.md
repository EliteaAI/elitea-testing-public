---
name: Nested allure.step for additive-only traceability on extend-existing
description: When an AFS asks you to "append the new case-ID to the existing step's label," editing that label string directly breaks the strict additive-only diff (git diff | grep '^-[^-]' must be empty). Wrap the new insertion in its own nested allure.step(...) instead — same report-level traceability, zero modified existing lines. Same trick applies to docstring headers with an item count ("Two CLARIFICATIONs").
type: feedback
---

## The conflict

The `extend-existing` mechanics (test-automation-workflow skill § Phase 3,
`.agents/role-overrides.md`) require BOTH:
1. Traceability — the new case's insertions should be visible in the Allure
   report, and the AFS commonly instructs "append the case-ID to the
   existing step's label."
2. Strict additive-only — `git diff <covering-spec> | grep -E '^-[^-]'` must
   be EMPTY. Existing `test()` bodies (including existing `allure.step(...)`
   label strings) must stay byte-identical.

Literally editing an existing `allure.step("...")` label to append
`[ELITEA-NNNN — ...]` satisfies (1) but violates (2): the diff shows the old
label string as removed and the new one as added, which is exactly what the
mechanical `grep -E '^-[^-]'` check is designed to catch.

## The fix

Wrap ONLY the newly-inserted assertion lines in their own **nested**
`with allure.step("ELITEA-NNNN — ..."): ...` block, indented one level
deeper than the surrounding existing code. Allure renders nested steps
under their parent in the report — the traceability the AFS asked for is
fully satisfied — and because every line of the wrapper + its body is
BRAND NEW code (not a modification of an existing line), the diff stays
100% additive. The parent step's original label string is never touched.

```python
# Existing code, unchanged:
with allure.step("Step 23 (AFS workaround...)"):
    artifacts_page.close_upload_path_dialog(...)
    artifacts_page.click_bucket_row(bucket_name, ...)

    # NEW — nested step, not an edit to the parent's label:
    with allure.step("ELITEA-1835 Steps 2-3 — verify bucket selected..."):
        assert artifacts_page.is_bucket_selected(bucket_name, ...)
        ...

    artifacts_page.open_bucket_menu(bucket_name, ...)  # existing, unchanged
```

## Same trick for docstring/comment headers with a count

An existing docstring said "Two CLARIFICATIONs (case-text drift...):" with
two bullets. My extension added a third CLARIFICATION. Editing "Two" →
"Three" is a one-word modification of an existing line — same diff
problem. Fix: leave the header untouched, and add the third item as its
own new paragraph below the original list ("One more CLARIFICATION, added
by the ELITEA-NNNN extension: ..."), rather than renumbering the header.
Slightly less polished English, fully additive diff.

## Verification

Always re-run the additive-only grep AFTER making traceability edits, not
just after the assertion insertions — it's easy to satisfy it for the
assertions and then break it again with a "helpful" traceability update:

```bash
git diff automation/base -- <covering-spec-path> | grep -E '^-[^-]'   # must be empty
git diff automation/base -- <page-object-path> | grep -E '^-[^-]'     # must be empty
```

From ELITEA-1835 (PR #675) — first case where the AFS's own traceability
instruction and the skill's additive-only rule pulled in different
literal directions; nested steps + non-renumbered headers resolve both.
