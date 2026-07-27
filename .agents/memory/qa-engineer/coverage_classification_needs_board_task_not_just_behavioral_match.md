---
name: Coverage classification needs a completed board task, not just behavioral match
description: "already-covered" requires a tracked backlog task that actually delivered the case's traceability, not merely an existing test that does the same thing — behavioral equivalence alone routes to extend-existing when a small gap (e.g. a missing @allure.issue tag) remains
type: feedback
---

**The correction (human rejected an analyst verdict on ELITEA-1796, 2026-07-15):**
a prior analyst pass found the case's TMS steps behaviorally identical, step-for-step,
to an existing merged test (`test_launcher_visible_and_opens_widget`) and classified
the case `already-covered`. A human overturned this. Verbatim correction:

> execution_type: automated metadata doesn't mean it's automated - in that folder
> all cases planned for automation and some of them may be automated but it means
> it need to have a task on our board, it may be data issue. The only judgement is
> actually do we have such task in our backlog and it's already automated by us,
> metadata changed fully accordingly and if we have it implemented in code already
> or not.

**What this means in practice for coverage classification (Phase 5 of
`test-case-analysis`):**

1. `execution_type: automated` / `status: draft` in a TMS case's frontmatter is a
   **folder-level planning flag** (every case in that automation-planned folder
   carries it), never proof any specific case is done. Don't classify off it.
2. **The judgment is board-first, not code-first**: does THIS repo's tracked
   backlog (board #9 here) have an issue for this exact case that reached a
   completed/terminal state (`Ready`/`Done`), with the case's own traceability
   actually delivered? Check `env -u GITHUB_TOKEN gh issue view <N>` /
   `gh project item-list` for the case's own card — not just "does a test
   somewhere do the same thing."
3. A `CLOSED`/`NOT_PLANNED` card (e.g. a mis-filed duplicate) is NOT a
   completion — don't let "the issue is closed" read as "this shipped."
4. **Behavioral equivalence to an existing test is necessary but not
   sufficient for `already-covered`.** If the existing test's own traceability
   doesn't reach this case (e.g. its `@allure.issue` decorators link only to
   older/legacy case IDs, never this one), that is a real — if small — code
   gap. Classify `extend-existing` and name the exact gap assertion (e.g.
   "append one `@allure.issue(<this-case-URL>)` decorator"), not
   `already-covered`. The size of the gap doesn't matter; whether it requires
   ANY code change does.
5. Corollary: don't default to `already-covered` just because re-implementing
   would be pure duplication. If duplication-avoidance is the right call but a
   traceability/tag gap remains, `extend-existing` is the status that captures
   both facts at once — no new test body, but a real code change is still
   owed.

Applies to any case where a downstream analyst is tempted to write "an existing
test already does this" as the sole justification for `already-covered` — always
also check the board-task-completion question and the traceability-tag question
before landing on that status.
