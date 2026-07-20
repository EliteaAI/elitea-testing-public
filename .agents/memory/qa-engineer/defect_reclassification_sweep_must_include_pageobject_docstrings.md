---
name: Defect-reclassification sweep must include page-object docstrings, not just the test file
description: PR #688/ELITEA-2094 round-2 review — a fix-only pass that split a defect reference (#684→#689) across the test file's constant/comment/allure-decorator missed the SAME claim living in a page-object method's own docstring; grep the defect number across every touched file, not just the file the reviewer's finding literally cited
type: feedback
---

Found reviewing PR #688 (ELITEA-2094, chat participants panel) round 2. Round 1 flagged that
Step 8's picker-exclusion check was bucketed under issue #684 on correlation, not a confirmed
shared root cause (#684's own comment explicitly says that symptom is "not yet root-caused to a
specific line"). The fix-only pass filed a new issue (#689), and correctly updated every
reference INSIDE `test_chat_participants_panel.py`: the `KNOWN_DEFECT_PICKER_EXCLUSION`
constant, the `expect.soft()` message, the `@allure.issue(...)` decorator, and the inline
comment block.

**What it missed**: `automation/pages/chat_page.py`'s `get_picker_matching_rows_locator()` — the
page-object method the test calls — has its OWN docstring making the same claim, independently
of the test file:

> "...to soft-assert around a known product defect (ELITEA-2094, known defect
> EliteaAI/elitea-testing-public**#684** — confirmed live this is the **same participant-state
> fragility as that issue's main finding**..."

This is exactly the retracted attribution the whole reclassification was meant to correct, and
it survived because the fix-only pass swept the test file (where the reviewer's finding was
anchored) but never grepped the defect number across the OTHER file the same PR touched
(`chat_page.py`). Confirmed via the scoped commit diff (`ece86144..b254e61c`) that this exact
docstring block is untouched between the pre-fix and post-fix commits — not a merge artifact,
a genuine miss.

**Reviewer technique**: when a fix reclassifies/splits a defect reference (old-issue → new-issue),
`grep -rn "<old-issue-number>"` across EVERY file the PR touches — not just the file the
originating finding named — before accepting the reclassification as complete. A defect number
frequently lives in at least two places for the same check: the test's inline
comment/constant/decorator AND the page-object method's own docstring (which documents "why this
method soft-asserts," independently of any one caller). The test-file sweep is necessary but not
sufficient.

Verdict on this PR: CHANGES_REQUESTED, narrowly for this one docstring paragraph — everything
else (Step 9 runtime signature check, the EliteaUI icon testid) verified clean on independent
re-derivation (fresh `gh issue view`, fresh `git fetch` on EliteaUI, scoped commit diffs, not
trusting the implementer's PR-comment summary).
