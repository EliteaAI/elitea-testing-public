---
name: An AFS's "per the pattern X already established" precedent claim can be false — verify it
description: ELITEA-2220 AFS's Automation Hints claimed the family test could read `HelpCenterPage.TOUR_LINK.format(slug)` directly in the spec file "per the same pattern the ELITEA-2227 implementer already established." ELITEA-2227's own spec (test_help_center_sidebar_tour.py) never does this — it only calls the page-object method open_resource_link_in_new_tab(). The precedent didn't exist; POM encapsulation rules were violated on its authority. Fix round 1 left it unaddressed because the finding named only the symptom (direct page.locator calls), not the false-precedent root cause in the AFS.
type: feedback
---

## What happened

The ELITEA-2220 family AFS's Automation Hints section said: "No new page-object
methods strictly required; the family test reads
`HelpCenterPage.TOUR_LINK.format(slug)` directly ... per the same pattern the
ELITEA-2227 implementer already established for dynamic testids." The original
implementation took this literally and wrote four `page.locator(HelpCenterPage
.TOUR_LINK.format(slug))` calls directly in the spec file.

Review flagged this as a POM-encapsulation violation
(`.claude/rules/page-objects.md` / `.claude/rules/ui-tests.md`: locators live
only as page-object class fields, never constructed in spec files). Fix round 1
left it unaddressed — no visible attempt in the diff. Checking the cited
precedent (`test_help_center_sidebar_tour.py`, ELITEA-2227) showed it never
constructs a `TOUR_LINK`-based locator inline at all — it only calls
`open_resource_link_in_new_tab()`, a page-object method. The AFS's precedent
claim was simply wrong.

## Resolution

Added `HelpCenterPage.resource_link(slug) -> Locator` (same shape as
`ai_providers_page.py`'s `card_for_model()` / `agent_form_page.py`'s
`get_tag_chip()`: a method wrapping a dynamic-testid class constant).
`open_resource_link_in_new_tab()` now calls `self.resource_link(slug)`
internally instead of duplicating the locator construction. The spec calls
`help_center.resource_link(slug)` at all four call sites. Amended the AFS's
Automation Hints in place to correct the false precedent claim and record what
actually shipped, per the Phase 2 amend-in-PR rule.

## Rule for next time

When an AFS's Automation Hints cites another case/spec as an established
pattern ("per the same pattern X already established"), don't take it on
faith — especially when the recommendation contradicts baseline conventions
(here: POM encapsulation, `.claude/rules/page-objects.md`). Open the cited
spec and check. A false precedent claim is exactly the kind of gap that costs
a whole fix round when the review finding only names the symptom (raw
locators in a spec file) and not the AFS-level root cause — fixing the two
symptoms without noting *why* the AFS was wrong leaves the false claim
sitting there for the next implementer to trust again.
