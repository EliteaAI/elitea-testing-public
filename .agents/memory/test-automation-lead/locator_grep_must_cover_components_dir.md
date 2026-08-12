---
name: Locator grep must cover components/, not just pages/
description: The item-1 mechanical locator-policy grep must scan the whole automation/ diff, including automation/components/ shared helpers — a new raw locator built inside a shared component method is just as much a violation as one in a page object, and "mirrors an existing method one line above" is never an exemption
type: feedback
---

Found auditing issue #70 (ELITEA-1950, PR #531). The PR added
`components/mui.py::Dialog.wait_for_visible()`, a new sibling to the
pre-existing `Dialog.wait_for()`. Both build a raw `page.locator('[role="dialog"]...')`
CSS locator inside a method body — non-testid, and constructed outside a
class-level `LocatorDescriptor` field. The new method is genuinely NEW code
added by this PR (confirmed via the merge diff), so `.agents/role-overrides.md`'s
"surrounding code is not precedent" clause applies squarely: it cannot borrow
legitimacy from the adjacent pre-existing raw handle just because it's one
method above in the same file.

The reviewer's PR comment explicitly claimed "no raw non-testid locators" —
wrong, because (apparently) the mechanical grep was run against
`automation/pages/` and `automation/tests/` (the two paths role-overrides
names explicitly for the reviewer-slot check) and never against
`automation/components/`, where this hit actually lived. `.agents/testing.md`'s
own audit-checklist grep command scans the whole `automation/` tree — components/
is in scope even though the per-slot override text happens to name only
pages/tests/ as examples.

Takeaway: when running the item-1 mechanical grep (as auditor or as reviewer),
always target `automation/` (or the full merge diff), never narrow it to
`pages/`+`tests/` by habit — shared `components/`/`fixtures/`/`utils/` helper
files are exactly where a new raw locator is likely to hide, since they don't
get the same page-object scrutiny. And never accept "it mirrors an existing
method" as grounds to skip re-checking a new method against the locator policy
— matching a neighbor is how the ~350-line raw-handle debt grew in the first
place (role-overrides' own stated concern).
