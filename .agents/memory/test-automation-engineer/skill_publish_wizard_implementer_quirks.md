---
name: Skill Publish wizard implementer quirks
description: Skills-tab Catalog category heading had NO testid (unlike Agents) — added via add-data-testid; icon-upload-before-tag-save ordering race (Formik reinitialize can revert an unsaved tag); a uuid-suffixed "generic name" fixture can downgrade the AI validator's WARN to PASS; AFS testid typo (agent-publish-category-select, no -combobox suffix).
type: feedback
---

From ELITEA-2595/2596/2598 (Skill Publish wizard — happy path, AI validation
blockers, WARN status). Implementer pass, `SkillDetailPage` + `AgentHubPage`.
The shared wizard component/testids/known-defect handling (#611/#614) mirror
`test_agent_publish_unpublish_version.py` (ELITEA-1892) almost exactly — see
`publish_unpublish_wizard_implementer_quirks.md` for that side. This entry
covers what's SKILL-specific.

## Catalog Skills-tab category heading had NO testid at all (unlike Agents)

`AgentCategorySection.jsx` (Agents tab) already carries
`data-testid="catalog-category-heading-{slug}"`. Its Skills-tab sibling,
`SkillCategorySection.jsx`, renders the identical category-name
`<Typography>` with **no testid whatsoever** — a genuinely different
component, not a shared one, despite the page object's `CATEGORY_HEADING`
constant sounding entity-agnostic. `is_category_section_visible()` /
`get_visible_category_heading_texts()` on `AgentHubPage` silently return
`[]` on the Skills tab until this is fixed — no error, just an empty list
that looks like "the category section isn't rendering" when it's really
"there's nothing to find." Added the identical testid pattern via
`add-data-testid` (`EliteaAI/EliteaUI@32ad365f` on `automation/testids`) so
the existing page-object methods work unchanged for both tabs. Check ANY
Skills-tab Catalog assertion that reaches for a category heading — this
gap likely still hits other in-flight cases until the testid promotes.

## Icon-upload-before-tag-save ordering race (Formik reinitialize can revert an unsaved tag)

Calling `add_tag()` then `upload_skill_icon_edit_mode()` then `save_edits()`
(tag added, icon uploaded, THEN save) produced a 10s
`TimeoutError: waiting for event "response"` inside `save_edits()` — the PUT
never fired, because the icon upload's own PUT invalidates
`TAG_TYPE_SKILL_DETAILS`, which (very plausibly) triggers Formik's
`enableReinitialize` refetch and **silently reverts the not-yet-saved local
tag chip**, leaving the form clean (nothing to save = no PUT = no request to
wait for). No assertion catches this until the timeout — `get_tags()` right
after `add_tag()` still reads the correct local chip, so the earlier
assertion passes; only the LATER `save_edits()` call times out with no
obvious connection back to the icon upload three steps earlier.

**Fix: save the tag FIRST (its own `save_edits()`), THEN upload the icon**
(the icon upload persists itself immediately via its own POST+PUT pair — no
extra Save needed afterward). This ordering has no such race since nothing
is left in unsaved local-only state when the icon's invalidation fires.
Apply this ordering to ANY skill edit-mode flow that combines a tag/name/
description change with an icon upload in the same test.

## A uuid-suffixed "generic name" fixture can downgrade AI validation WARN -> PASS

ELITEA-2598's WARN scenario needs a name the AI validator classifies as
generic (`field: "name"` in the `warnings` list). Using
`f"skill-{uuid.uuid4().hex[:8]}"` (to avoid a name collision across repeat
runs) produced `status: "PASS"` with an EMPTY `warnings` list and the
generic-name signal downgraded into `recommendations` instead — the AI
apparently reads a hyphenated compound with a hex suffix as no longer
"purely generic" once other characters are appended, even though the
prefix is the same literal word. **Use the case's exact literal name
UNSUFFIXED** (here: bare `"skill"`) when a fixture's TEXT content itself is
what the AI grades — the AFS's own exploration note ("no uniqueness
collision observed this run") is not a throwaway aside, it's the reason the
analyst didn't append a suffix either. Any AI-graded content-quality
assertion (length/placeholder/secrets/generic-name/…) should be treated as
content-sensitive to cosmetic changes like this, not just to the semantic
substance a human would expect it to key off of.

## AFS Concrete Handles table had a testid typo (implementer-caught, amended)

ELITEA-2595's AFS named the Category select trigger
`agent-publish-category-select-combobox`. Live source
(`PreparationStep.jsx`) confirms the real testid is
`agent-publish-category-select` — no `-combobox` suffix. Caught via a fresh
`git grep` verification before writing the `LocatorDescriptor`, not by a
failed test (a wrong testid on a `LocatorDescriptor` field just times out
waiting for the element, same class of silent failure as the missing
category-heading testid above — always re-verify an AFS's literal testid
string against source when something that specific reads unusually, don't
trust-and-transcribe). Amended in the AFS with the correction + why.
