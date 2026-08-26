---
name: App-wide toast masks a Save-that-also-navigates regression
description: A portal-rendered toast still fires even if Save silently navigates away — assert page.url too, not just toast+response
type: feedback
---

When an AFS calls out "stays on the same URL / no navigation" as the
distinguishing behavior of an edit-Save vs a create-Save (Elitea entity
forms reuse one `data-testid` for both — see
`.agents/memory/test-automation-engineer/shared_save_testid_create_vs_edit_navigation_false_pass.md`),
verify the test actually asserts the URL, not just the PUT status + toast
text. The `toast-message` testid is an **app-wide, portal-rendered**
component — it renders regardless of route, so it still appears even if a
regression made Save also navigate away. A PUT-200 + toast-text assertion
alone therefore cannot detect that regression; if the very next step does
its own explicit navigation (e.g. back to a list page), any incorrect
navigation from Save is silently masked for the rest of the test.

Caught reviewing ELITEA-2431 (`SkillDetailPage.save_edits()`,
`test_skill_management.py::TestEditSkill`): the AFS's own step-3 Verify
text names the URL check explicitly, the method's docstring is built
entirely around avoiding the create-flow's navigation-based false-pass,
and yet the implementation never reads `page.url` post-save. Flag this
as CHANGES_REQUESTED, not a nit — it's the one behavior the whole
method exists to get right.
