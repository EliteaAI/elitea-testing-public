---
name: Skills page_header testid was dead code
description: SkillsListPage.page_header ("skills-page-header") pointed at a testid that never existed in EliteaUI src until ELITEA-2429 fixed it
type: feedback
---

`automation/pages/skills_list_page.py`'s `page_header = LocatorDescriptor(testid="skills-page-header")`
field pre-dates any test that actually called it — a `git grep` of `page_header\.`
in that file returned zero hits before ELITEA-2429. The testid itself did not
exist anywhere in `EliteaAI/EliteaUI` src (neither `main` nor
`automation/testids`): `Skills.jsx`'s `<StickyTabs>` call never passed a
`titleTestId` prop, unlike the Agents equivalent
(`pages/Applications/Applications.jsx`, which passes
`titleTestId="agents-page-header"` to the same shared `StickyTabs.jsx`
component — the component already renders `data-testid={titleTestId}`
unconditionally, so it's a one-line fix).

**Symptom if you hit this cold:** `Locator.wait_for: Timeout 10000ms exceeded`
on `get_by_test_id("skills-page-header")`, with no obvious reason — the field
looks legitimate (LocatorDescriptor, testid-only, matches the Agents pattern
exactly) and the page visibly has a "Skills" header on screen.

**Diagnosis:** `git grep -- "skills-page-header" origin/main -- src/` (and
`origin/automation/testids`) in the `EliteaUI` sibling — zero hits means the
testid genuinely doesn't exist, not a timing issue.

**Fix (already landed, EliteaUI@b29c9b03 on `automation/testids`):** add
`titleTestId="skills-page-header"` to `Skills.jsx`'s `<StickyTabs>` call. If
you hit this again on a DIFFERENT dead pre-existing field elsewhere in the
suite, the same pattern applies — check whether the shared component already
accepts a `titleTestId`/`testId`-style prop before assuming a testid needs to
be invented from scratch.

Added `SkillsListPage.verify_dashboard_header_visible()` this run (previously
the field had no method wrapping it at all).
