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

### Update (fix round, 2026-08-12) — the bare literal ALSO flips WARN <-> PASS, and the wording varies too

The uuid-suffix fix above reduces the flake but does NOT eliminate it: the
SAME bare literal `"skill"` (unchanged desc/instructions) has been observed
classified as `status: "WARN"` (issue in `warnings[]`) in most runs and as
`status: "PASS"` (identical signal downgraded to `recommendations[]`) in
occasional runs — reproduced first by the lead's gate run, then again by a
targeted 5-run local check during the fix itself (1 PASS in the first 4
runs, 5/5 stable after the assertion was corrected). No fixture text change
can make this fully deterministic — it's LLM judge boundary noise on a
genuinely borderline generic name, not a function purely of the input
string (same input -> different output across runs is the tell). **The
free-text WORDING of the finding also varies independently of the
status/bucket** — live-observed for the identical fixture: `"The name is
too generic to convey the skill's purpose."` (warnings), `"Use a more
descriptive name than \"skill\"..."` (recommendations), `"Use a more
specific name than \"skill\"..."` (recommendations, a DIFFERENT run) — a
keyword match on `"generic"`/`"descriptive"` failed on the third phrasing.
**Lesson for any AI-graded borderline-severity assertion:** (1) assert on
the STATUS SET that maps to the real behavioral contract (`status in
("WARN", "PASS")`, i.e. "not FAIL", when the case's actual pass criterion
is "doesn't block" rather than a specific label) plus the deterministic
gate field (`critical_issues == []`); (2) assert on STRUCTURED presence
(`field == "name"` entry exists, non-empty text) rather than matching
free-text keywords against AI-generated prose — the keyword list will keep
growing as new phrasings surface, and each one is a needless red run, not
a real regression. Full case for grounding this in the TMS case's own
Pass/Fail criteria (not a scope change) is in the AFS's amended Test Steps
4/5 + `l3_skill-publishing-warn-status-allows-publishing_ELITEA-2598.md`.

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

## Fix round (PR #1464 review): page-wide checks don't prove "under THIS category"

Reviewer's blocking finding: `get_skill_card(skill_name)` + the
`CATEGORY_NAME in visible_headings` check are two UNRELATED page-wide
assertions — a card with the right name existing anywhere, and a heading
with the right text existing anywhere. Neither proves the card is a
descendant of that category's section, so a skill published under the
WRONG category would still pass. `SkillCategorySection.jsx`'s outer `Box`
had no testid at all (only its inner heading `<Typography>` did — see the
section above). Added `catalog-category-section-{slug}` via
`add-data-testid` (`EliteaAI/EliteaUI@c80de351`) and a `category` kwarg on
`AgentHubPage.get_skill_card()` that scopes the card locator to
`.locator(CATEGORY_SECTION.format(slug)).locator(SKILL_CARD_PREFIX)` —
same slugify convention as `CATEGORY_HEADING`. Same fix would apply to
`AgentCategorySection.jsx`/`get_agent_card()` if a future case needs an
agent-under-category check; not added yet (no test on this branch
exercises it — "referenced = called on the executed path").

## `wait_for_any_skill_card()` races the category-specific heading (Trending resolves first)

Discovered live while re-verifying the fix above: `wait_for_any_skill_card()`
followed immediately by `get_visible_category_heading_texts()` intermittently
under-read the heading list (`['Trending']` only, target category's section
not yet mounted) — NOT the reviewer's scoping gap, a separate pre-existing
race. `useSkillHubData.hooks.js` fires three INDEPENDENT fetches on Skills-tab
mount: `fetchAllAndCategorize` (the bulk `ALL_SKILLS_LIMIT=1000` fetch that
buckets everything into non-Trending sections), `fetchTrendingSkills` (its
own much smaller page-sized request), `fetchMyLikedSkills`. Trending's
smaller request resolves first, satisfies "any card visible", and the read
happens before the bulk-categorize fetch (and therefore the target
category's own section) has landed. This breaks the assumption
`wait_for_any_agent_card()`'s docstring documents for the AGENTS tab (one
bulk fetch, React 18 batches the per-category dispatches into one commit —
"any card visible" really does mean every category landed) — that
assumption does NOT hold for Skills, which has three separate fetches, not
one. Fix: added `AgentHubPage.wait_for_category_heading(category_label,
timeout)` — waits on `CATEGORY_HEADING.format(slug)` directly (Playwright
auto-retry, no sleep) — call it before reading
`get_visible_category_heading_texts()` whenever asserting a SPECIFIC
category's presence on the Skills tab.
