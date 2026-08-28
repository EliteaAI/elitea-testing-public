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
  A **second** use without that card is laundering ⇒ `CHANGES_REQUESTED`.

## The distinguishing test

Does the control exist in the product at all?

- **Exists, conditionally rendered** ⇒ testid + `to_have_count(0)` is available
  and REQUIRED (merged precedent:
  `automation/tests/ui/admin/test_project_context_save_discard_dirty_state.py:112`
  asserts `context_page.save_button` — a `LocatorDescriptor` — has count 0).
- **Does not exist anywhere** ⇒ genuine gap; the role handle is the only route.

Related: [[teardown_that_reads_a_page_it_may_not_be_on]]
