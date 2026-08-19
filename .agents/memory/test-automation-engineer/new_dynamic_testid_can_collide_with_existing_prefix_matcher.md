---
name: New dynamic testid can collide with an existing prefix matcher
description: Grep an existing `^=` prefix constant before naming a sibling dynamic testid — a new testid literally starting with that prefix silently over-counts in an unrelated existing method.
type: feedback
---

## What happened (ELITEA-2196)

`ChatPage` already had `CHAT_ATTACHMENT_CHIP_PREFIX = '[data-testid^="chat-attachment-chip-"]'`,
consumed by the EXISTING, merged `get_attachment_chip_count()` (ELITEA-2197) to count
visible attachment chips.

The ELITEA-2197 AFS had reserved a NEW sibling testid, `chat-attachment-chip-remove-{index}`,
for a future case (this one) to use on the chip's remove (X) button. That name is a perfectly
reasonable, self-documenting choice on its own — and it literally **starts with** the string
`chat-attachment-chip-`, so it silently matched `CHAT_ATTACHMENT_CHIP_PREFIX` too.

Result: attaching 4 files made `CHAT_ATTACHMENT_CHIP_PREFIX`'s locator resolve to **8**
elements (4 chips + 4 remove buttons), corrupting `get_attachment_chip_count()` — a method
with an existing merged caller I never touched. First test run failed with
`Locator expected to have count '4', Actual value: 8`. Fixed by renaming the new testid to
`chat-attachment-remove-chip-{index}` (distinct prefix, `element` and `chip` swapped in the
naming) — zero collision, both the new test and the pre-existing sibling specs pass clean
after.

## The rule this leaves behind

**Before adding ANY new dynamic testid in a family that already has a `^=` prefix constant
(`grep -n 'PREFIX = ' pages/<page>.py` or similar), check whether the new name STARTS WITH
that prefix's literal string.** If it does, either:
- rename the new testid so it does NOT share that prefix, or
- if the prefix's own existing callers can tolerate a narrower match, tighten the prefix
  selector itself — but that's an edit to a shared-caller constant, subject to the
  additive-only/full-regression discipline (Hard Rule 3), so renaming the NEW testid is
  almost always the cheaper, safer fix.

This is invisible at JSX-review time — the new name looks like ordinary, correct
`{section}-{element}-{type}` naming. It only surfaces as a silent over-count in a
DIFFERENT, unrelated test's assertion. A first test run against the live app is what
caught it here, not source review — this is exactly the class of bug the "run it green
once" gate exists to catch, but it's cheaper to just grep the prefix before naming.
