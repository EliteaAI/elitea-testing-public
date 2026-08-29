---
name: Absence assertion of a control that does not exist is a canon gap, not a #579 exception
description: How to judge a get_by_role hit whose whole point is that no such element exists in the product
type: feedback
aliases: [no save button, absence assertion, get_by_role count 0, save_buttons, canon gap locator]
tags: [area/locator-policy, type/review-rule]
created: 2026-08-29
updated: 2026-08-29
---

## The situation

A spec must assert that a control **does not exist anywhere in the product**
(ELITEA-2387: "there is no Save button on the personalization pages"). The
testid-only policy has no shape for this: you cannot add a `data-testid` to an
element that was never rendered, so the handle is necessarily a role/text one
(`get_by_role("button", name="save")` → `to_have_count(0)`).

## How to judge it as reviewer

- It is **not** the #579 exception. #579 covers exactly two shapes — third-party
  widget subtrees and third-party editor internals — and its discipline forbids
  free-floating page-level handles, which a page-wide absence check is by
  construction. A docstring calling it "#579 sanctioned" is **borrowed
  authority** (`role-overrides.md` § precedent is not authority) — ask for the
  wording to be fixed even when you approve the code.
- It **is** a canon gap ⇒ § declared-improvisation protocol. Declared (Run
  Report + PR body) with sound reasoning, it cannot solo-FAIL: verify the
  reasoning, approve, and tell the lead it owes a `question` card (limit 2).

## The distinguishing test

Does the control exist in the product at all?

- **Exists, conditionally rendered** ⇒ testid + `to_have_count(0)` is available
  and REQUIRED (merged precedent:
  `automation/tests/ui/admin/test_project_context_save_discard_dirty_state.py:112`
  asserts `context_page.save_button` — a `LocatorDescriptor` — has count 0).
- **Does not exist anywhere** ⇒ genuine gap; the role handle is the only route.

## Second use: weigh the harm, do not reflex-block (settled PR #1961, 2026-08-29)

Limit 3 of the protocol ("second use is a blocker") reads as categorical, and
this pattern reached its second use — `SettingsProfilePage.drawer_logout_controls()`
(ELITEA-2252, merged) then `SettingsPersonalizationPage.save_buttons()` /
`page_save_buttons()` — with no canon card filed. **Approved anyway**, and the
reasoning generalises:

- The remedy limit 3 names is *the canon card*, which is the **lead's** action at
  batch close, not a code change any implementer round can produce. Blocking sends
  the wrong actor another round.
- The ceiling test is what actually decides it: a declaration may not change **what
  is verified**. An absence assertion changes nothing — there is no honest
  alternative handle, and the coverage metric is untouched because no element is
  being claimed as covered. The harm is precedent hygiene only.
- So: approve, correct the false `#579` citation in docstring + Run Report, and
  name the overdue `question` card as the lead's obligation. Reserve the hard block
  for a second use whose declaration *does* touch the ceiling (a terminal
  substitution, a dropped observable, a swapped subject).

## Third use, and the canon card now EXISTS — #1782 (PR #1983, 2026-08-29)

`SettingsAIConfigurationPage.panel_progress_indicators()` (ELITEA-2394) is the
third instance: `'[data-testid="ai-configurations"] [role="progressbar"]'` →
`to_have_count(0)`, because `AIConfiguration.jsx` renders **no spinner at all**
and the case step demands "no permanent loading spinner".

Two things changed since the second use, and both should shape the next review:

1. **The overdue `question` card was filed** — `#1782` *"[Canon] #579 needs a
   third raw-handle category: app-native absence assertion for a control that
   never renders"*, still OPEN. So limit 2's obligation is discharged; what a
   4th use owes is a **citation of #1782**, not a fresh from-scratch declaration.
   Check for that citation and ask for it — it is what keeps the occurrence
   count visible to the lead instead of scattered across docstrings.
2. **The `#579` mis-citation is fixed at the source.** This docstring opens with
   "NOT the #579 exception" and explains why, so the borrowed-authority defect
   the earlier entries flagged no longer needs correcting — approve the wording.

Verdict stayed APPROVED, same reasoning as the second use (ceiling untouched:
nothing about *what* is verified changes, and no honest alternative handle
exists). Escalating detail for the lead: three occurrences now, one open card —
#1782 needs a ruling before a 4th accrues.

Note the shape here is one step MORE compliant than the earlier two: the raw
part is a descendant of a real app testid inside an UPPER_CASE class constant
(`[data-testid="ai-configurations"] [role="progressbar"]`), so it PASSES the
mechanical locator grep's one-hop check outright — unlike
`settings_drawer.get_by_text(...)`, which passes only via its parent descriptor.

Related: [[teardown_that_reads_a_page_it_may_not_be_on]]
