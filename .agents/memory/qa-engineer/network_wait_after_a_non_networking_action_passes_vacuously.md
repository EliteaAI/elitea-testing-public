---
name: A network wait after a non-networking action passes vacuously
description: networkidle/wait_for_network settles trivially when the action fired no request — an assertion that cannot fail
type: feedback
aliases: [networkidle vacuous, wait_for_network proves nothing, upload fires on send, vacuous wait]
tags: [area/assertions, type/anti-pattern]
created: 2026-08-27
updated: 2026-08-27
---

## The trap

A case step of the shape *"wait for network to settle after X, indicating X was processed"* is
only meaningful if X actually fires a request. When it does not, `wait_for_network()` /
`networkidle` returns **immediately and always** — the test passes because nothing was ever in
flight. It is an assertion that cannot fail, which is indistinguishable in a green run from one
that genuinely verified something.

This is a sibling of [[absence_assertions_can_pass_vacuously]] on the positive side: there, an
absence assertion passes because the detector never worked; here, a wait passes because the
event never existed.

## The worked instance (ELITEA-1802, verified live 2026-08-27)

Support Assistant attach flow. Case Step 8 read *"Wait for network activity to settle after
upload … indicating the file upload request has been processed."* A full network capture across
the attach click + `setFiles` showed **zero** `POST /api/v2/support_assistant/attachments/{uuid}`
— only `config/` and `conversations/` GETs. The upload fires on **Send**
(`MessageInput.handleSend` → `startUpload`); attaching only stages a `PENDING` chip in local
component state. The merged test's `wait_for_network()` had been passing vacuously since 2026-07.

## What to do instead

1. **Capture the network before believing a step's premise.** One filtered capture around the
   action settles whether any request exists. Do this whenever a case step justifies a wait by
   naming a request — the case is asserting a mechanism, and mechanisms drift.
2. **Assert the observable the action genuinely produces.** Here: the staged chip
   (`support-assistant-attachment-chip`, text = the file name) — DOM-observable, system-produced,
   and it fails loudly if the file never landed.
3. **The product is usually right; the case text is what drifted.** File a CLARIFICATION, not a
   bug (reverse-masking guard). ELITEA-1802's went out as `#1827`.

## The general smell

Any wait whose *justification* is a side effect you have not observed. `networkidle`,
`wait_for_load_state`, and bare timeouts all share it. If removing the wait cannot change the
verdict, the wait is not coverage — replace it with the assertion it was standing in for.

Related: [[absence_assertions_can_pass_vacuously]] · [[support_assistant_launcher_click_quirk]]
