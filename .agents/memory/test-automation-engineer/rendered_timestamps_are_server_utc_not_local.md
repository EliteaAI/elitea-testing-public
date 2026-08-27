---
name: Rendered timestamps are server UTC, not browser local (formatVersionMeta skips convertTime)
description: Never assert a rendered timestamp against the test machine's clock — derive it from the API's own created_at
type: project
aliases: [timestamp assertion, created_at oracle, convertTime, formatVersionMeta, version date, UTC vs local, clock-coupled assertion]
tags: [area/agents, type/assertion-design, type/product-quirk]
created: 2026-08-27
updated: 2026-08-27
---

## The trap

This backend serializes **naive** timestamps — verified live:
`created_at = '2026-08-27T15:30:31.728088'` (no `Z`, no offset, 6-digit microseconds).

The codebase has its own normalizer for exactly this — `convertTime()` in
`src/common/convertChatConversationMessages.js:25` (appends `Z` when a stamp carries neither
`Z` nor `+`). `NotificationListItem.jsx:109` and `src/components/Chat/hooks.js` call it.
**`version.helpers.jsx`'s `formatVersionMeta()` does NOT.** It runs `new Date(created_at)` on
the raw string and then reads `getDate()/getFullYear()/getHours()/getMinutes()`.

With **no offset in the input there is nothing to convert from**, so the local getters return
the string's own digits. ⇒ **The UI renders the SERVER's wall clock, labelled as local.**

Measured 2026-08-27 on a UTC+4 machine: version created at local **19:30**, backend stamped
**15:30**, dropdown rendered **`"v2-publishedAug 27, 2026, 15:30 · by Test Bot"`**. Four hours off.

## Why a `datetime.now()`-based assertion is a false-RED generator

It bounds the wrong risk. The exposure is `|server UTC − machine local|`, up to **±14 h** — not
a midnight edge. And it is **invisible where it matters**: GHA runs UTC, so `datetime.now()` *is*
the server clock there and it always passes. It surfaces as a deterministic 3/3 RED on someone's
laptop at the wrong hour and reads exactly like a real regression.

## The fix — the API response is the oracle

`.agents/testing.md` § Fidelity policy already prescribes this shape: *capture the real response
and assert the UI against it*. Mirror the product's own arithmetic:

```python
stamp = datetime.fromisoformat(created_at)
if stamp.tzinfo is not None:                      # should the backend ever send one
    stamp = stamp.astimezone().replace(tzinfo=None)
return (f"{_MONTH_ABBR[stamp.month-1]} {stamp.day:02d}, {stamp.year}",
        f"{stamp.hour:02d}:{stamp.minute:02d}")
```

Worked reference: `test_agent_version_selector_order.py::_expected_created_label`.
Strictly stronger than a clock check — catches a wrong day, month, year, format **and** time,
with zero clock coupling.

**Mirror the product; do not compensate for it.** The UTC-vs-local inconsistency between this
dropdown and notifications/chat is a real filed product observation. A test that "corrects" the
offset would hide the very thing that was filed.

## Generalise

Any rendered date/time in this app is suspect. Before asserting one, check whether its formatter
calls `convertTime()`. If it does not, the digits are the server's.

Related: [[version_dropdown_sort_lost_its_pinned_tier]]
