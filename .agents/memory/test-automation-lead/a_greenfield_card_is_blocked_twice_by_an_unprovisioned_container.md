---
name: A greenfield automation card is blocked TWICE by an unprovisioned container — credentials AND npm
description: Factory-mode env checks that only look for credentials/.venv under-report the blocker for a NEW case; new testids additionally need a writable EliteaUI clone on automation/testids plus `npm run dev` under HMR, so a remediation that ships only credentials leaves every greenfield card blocked.
type: gotcha
---

## The trap

The environment blocker filed as **#2378** (2026-09-29) was written from three
`[FIX]` cards — #2376, #2377, #2343 — all of which **adjust an existing spec**.
Its § "what would unblock this" therefore lists credentials, a `.venv`,
Playwright browsers, and the sibling clones. Read as a shopping list, that is
**insufficient for a greenfield card**, and the gap is silent: a human who
provisions exactly what #2378 asks for will watch the next new-case card park
again for a reason the issue never mentioned.

A **greenfield** case (first automation of a TMS case) is blocked on a second,
independent axis:

| Axis | Needed by | Present 2026-09-29? |
|---|---|---|
| credentials + `.venv` + browsers + siblings | *any* UI card | no |
| **`npm` / `npx`** + a **writable** EliteaUI clone on `automation/testids` | **only** a card that adds testids | no — `npm` absent from PATH, `/opt` not writable |

Because the locator policy is testid-only with no fallback rung, a new case
whose elements lack testids **cannot be specced, let alone implemented**,
without adding them to EliteaUI source and observing them live under Vite HMR
on `localhost:5173`. No `npm` ⇒ no dev server ⇒ no `add-data-testid` loop, even
with perfect credentials.

## First move on a greenfield card in factory mode

Check **both** axes before writing the park comment, and say which apply:

```bash
command -v npm npx; ls -d ../EliteaUI ../onetest-ai-tm-Elitea 2>&1
test -w "$(cd .. && pwd)" && echo parent-writable || echo parent-READONLY
ls automation/.env.test 2>&1; ls .venv/bin/pytest 2>&1
```

Then name the greenfield axis explicitly in the comment on the blocker issue —
**as a new occurrence on the existing card, not a new card** (same object, same
trigger ⇒ a duplicate by the project's own dedup doctrine; "never ask twice").
Adding the missing requirement to your own open question card is not asking
twice, it is completing the ask.

## Corollary — do not dispatch the analyst "to at least get the AFS"

Tempting, and wrong. `.agents/role-overrides.md` § Analyst slot requires every
handle row to carry a provenance value verified *at analysis time*, and the AFS
for a greenfield case rests on observables (rendered page copy, card contents)
that must be seen live. An AFS produced without the environment is unverifiable
by construction, and it is worse than no AFS because the implementer and the
reviewer both triangulate against it — all three artifacts agree and all three
are guesses.

Worked instance: **#2382** (ELITEA-2219, Help Center via sidebar icon) — zero
dispatches, parked `Blocked — Waiting on #2378`, with the session's output being
a verified provenance table instead of an unverifiable spec.
