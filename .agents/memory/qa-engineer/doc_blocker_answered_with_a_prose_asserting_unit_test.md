---
name: Doc blocker answered with a prose-asserting unit test
description: A "docstring states retracted facts" blocker can come back fixed PLUS a permanent unit test asserting docstring wording — judge the guard, not just the fix
type: feedback
aliases: [docstring guard test, prose policing test, static-analysis guard scope creep, meta test on documentation]
tags: [area/review, type/pattern]
created: 2026-08-21
updated: 2026-08-21
---

## What happens

Round-1 blocker: a spec's module docstring stated a **retracted** mechanism and
retracted measurements as fact. Round-2 diff fixed the docstring *and* added
`automation/tests/unit/test_artifacts_tree_expand_collapse_docstring_mechanism.py`
— three unit tests asserting that the docstring (a) contains the literal helper
name, (b) only cites the old mechanism alongside a retraction word, (c) does not
contain two hard-coded stale phrases.

## Why it deserves a second look, not an automatic pass

The suite already has a genre of static-analysis guards under `automation/tests/unit/`
(locator inventory, pinned-literal bans, known-defect matchers, and the
`@allure.issue`-link resolvers — that last one is a GOOD guard: cheap, no network,
checks a fact that really can rot). Prose guards are the weak member of the family:

- They freeze one review round's wording into a permanent test.
- They invert on a correct change: "the docstring must name `wait_for_tree_item_stable`"
  goes RED the day the product defect is fixed and the settle wait is deleted.
- They assert documentation, not behaviour, so they add no coverage and cannot fail
  for a reason a user would care about.

**Review stance:** flag as an Important non-blocking finding (drop it, or keep only
the name-coupling half). Do not block a unit's cases on it — it removes no coverage
and masks no defect. Do check the *link*-resolution flavour actually resolves on the
local sibling clone rather than calling the network.

Related: [[future_issue_tms_link_filename_must_be_verified]]
