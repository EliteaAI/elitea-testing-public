---
name: Console listener registered after flow start gap
description: A page.on("console", ...) listener must be registered BEFORE the first step it claims to cover, not mid-flow — and "N other callers, all re-run green" claims must be verified per-class, not per-file
type: feedback
---

Two related review findings from PR #606 (ELITEA-1902), both reviewer-caught
CHANGES_REQUESTED items.

**1. Listener registered after the flow it claims to cover.**

`test_import_agent_zip_nested_agent_dependencies.py` asserted "zero console
errors during the export/import/attach flow," but `page.on("console", ...)`
was registered inside the Step-2 (`export`) `allure.step` block — AFTER
Step 1 (agent creation + `attach_agent()`) had already run and completed.
Step 1's console output was never observed, despite the assertion's wording
implying full-flow coverage.

**Fix:** register any `page.on("console", ...)` listener before the FIRST
step your zero-console-errors (or console-issues) assertion claims to
cover — usually right before `try:`/Step 1, not inside whichever later step
happens to be convenient. Write the registration comment explaining why it's
there early ("so the assertion genuinely covers the full flow") so the next
reader doesn't move it back down "for tidiness." Re-run after moving it
earlier — moving registration earlier can legitimately surface pre-existing
noise from the now-covered earlier steps; if it does, extend the AFS's
already-documented known-warning filter rather than weakening the assertion
or reverting the registration point.

**2. "N other callers, all re-run green" must be verified per resolved
class/method, not per file that happens to call a same-named method.**

The PR claimed `expand_import_preview_details()` (on `AgentsListPage`) had
"2 other merged callers, both re-run green" — citing
`test_import_agent_recreates_skills_with_new_ids.py` AND
`test_skill_export_import.py`. Only the first is real: the second
instantiates a wholly separate `SkillsListPage` class with its own
unrelated same-named method — no inheritance link, zero lines of the diff
touched it. Root cause of the false claim: both files were run together in
one `pytest` invocation and "both pass" got reported as "both call the
method I changed," without checking which class each file's call actually
resolves to.

**Fix:** before writing "N other callers, all re-run green" in a Run Report
or PR description, `grep` for the method name, then open EACH hit and
confirm it's calling the SAME class/method (not a same-named method on an
unrelated class) before counting it. A same-named method on a different
page-object class is a real, recurring trap in this repo — several page
objects share method names like `expand_import_preview_details`,
`get_raw_json`, `is_toolkit_attached` across otherwise-unrelated classes.
