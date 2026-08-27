---
name: to_have_count(0) cannot assert "stays gone"
description: An absence assertion passes instantly if the count is already 0 — place it where the bad state is settled, or it silently asserts nothing
type: feedback
aliases: [stays gone, to_have_count 0, absence assertion race, card reappears, sanctioned-RED soft assert]
tags: [area/playwright, type/assertion-design]
created: 2026-08-27
updated: 2026-08-27
---

## The trap

`expect(x).to_have_count(0, timeout=T)` does **not** observe for `T`. It returns
the moment the count is 0 — which, right after the thing was removed, it always
is. So an assertion meant as *"it stays gone"* placed immediately after the
removal is a guaranteed pass that proves nothing, and a sanctioned-RED member
that was supposed to fire silently drops out of the closed set.

Concrete: ELITEA-2213 (HITL Block). The AFS ordered "the resolved card stays
gone" right after a fast REST read, i.e. ~1 s after the Block click. The card
reappears at ~2-6 s (#1835). Evaluated there it would have passed ~always.

## The fix that keeps the assertion honest

Move the **evaluation point** to where the bad state is settled — for a chat
flow, after the response wait — and keep the assertion itself identical, so it
still flips green unchanged when the product is fixed. Do NOT reach for a sleep,
and do NOT invert it into "wait for the bad thing" unless nothing else works.

`TestSensitiveActionAuthorize` Step 9 in
`automation/tests/ui/chat/test_hitl_sensitive_action_authorization.py` is the
in-repo precedent: the same assertion, ~90 s downstream, deterministic.

Declare the reordering as a declared improvisation — it is a *how*, not a *what*
(the assertion, its soft channel and its defect link are unchanged).

Related: [[hitl_setup_trigger_flake_fires_before_any_assertion]]
