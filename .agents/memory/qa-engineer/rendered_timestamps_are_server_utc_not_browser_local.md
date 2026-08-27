---
name: Rendered timestamps are server-UTC digits, not browser-local
description: Elitea serves naive created_at; only convertTime() adds the Z. Never assert a rendered date against datetime.now()
type: project
---

## The fact

Elitea's backend serializes many timestamps **naive** (no `Z`, no offset) —
e.g. an agent version's `created_at` is `"2026-08-27T14:50:56.884709"`
(documented shape: `.claude/skills/elitea-platform/references/api-reference.md`,
`versions[].created_at`).

The UI has a normalizer for exactly this:
`../EliteaUI/src/common/convertChatConversationMessages.js:26-38` —
`convertTime()` appends `'Z'` unless the string already ends in `Z` or contains
`+`. Notifications and chat call it. **Many renderers do not.**

`version.helpers.jsx`'s `formatVersionMeta()` (the VERSION dropdown's
`"{Mon DD, YYYY, HH:MM} · by {author}"` label) does **not** call it — it does
`new Date(created_at)` then `getDate()/getFullYear()/getHours()/getMinutes()`.
A naive date-time string is parsed as **local** (ES2015+), so the local getters
hand back the string's own digits. Net effect: **the label is the SERVER's UTC
wall clock, printed as if it were local.** No timezone conversion happens.

## The trap for tests

`assert rendered_date in {today, today-10min}` (built from `datetime.now()`)
is comparing the **server's** clock to the **machine's** clock. The divergence
is the machine's UTC offset — up to ±14 h — not minutes.

- UTC+3 machine, local 01:30 → server stamps 22:30 *yesterday* → rendered date
  is yesterday, `datetime.now()` is today ⇒ **false fail**, ~3 h/day.
- UTC−5 machine, local ≥19:00 ⇒ false fail, ~5 h/day.
- **GHA runs UTC, so it always passes there.** It fails only on a dev machine at
  the wrong hour — where a 3×-green merge gate goes 3/3 RED deterministically and
  looks exactly like a real regression.

## What to require instead

Assert against the API's own `created_at`, per `.agents/testing.md`
§ Fidelity policy ("the response is the oracle"): parse it with
`datetime.fromisoformat`; if the parsed value is **naive**, format its digits
verbatim; if it is **tz-aware**, `.astimezone()` first — that mirrors exactly
what `new Date()` + local getters do. Zero clock coupling, and strictly stronger
than a today-window (catches wrong day, wrong month, wrong format).

Weaker but acceptable fallbacks: a ±1-day plausibility set (covers every real
offset, still catches `Jan 01, 1970`), or drop the date-VALUE assertion and keep
the format regex — which is all most TMS "shows creation date/time" steps ask.

## Reviewer cue

`grep -rln 'datetime\.now()\|utcnow\|timezone\.utc' automation/tests automation/pages automation/utils`
— any hit that feeds a **rendered** date/time comparison needs this check.
Origin: PR #1878 (ELITEA-1891 repair), caught statically at review.
