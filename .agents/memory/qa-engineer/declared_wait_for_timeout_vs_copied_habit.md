---
name: Declared wait_for_timeout (defect workaround) is not the copied-habit anti-pattern
description: A wait_for_timeout that is declared in-code + AFS, tied to a filed defect with no DOM signal available, is a sanctioned exception — don't conflate with wait_for_timeout_copied_despite_afs_warning.md
type: feedback
---

## Context (ELITEA-2368 review, PR #1233)

`.agents/conventions.md`'s hard rule is "No `sleep`/`waitForTimeout` —
framework waits only", and a sibling memory entry
(`wait_for_timeout_copied_despite_afs_warning.md`, ELITEA-2272) documents an
implementer copying a `wait_for_timeout` habit into a NEW page object despite
an explicit AFS warning not to — a real violation.

ELITEA-2368's `page.wait_for_timeout(1000)` before `click_start_chat()` is a
**different shape** and should NOT be reviewed the same way:

- It targets an already-tracked, open product defect
  (EliteaAI/elitea-testing-public#1043 — `AgentModal.jsx`'s `onStartConversation`
  reads `agentDetails.version_details.*` from a `useState(null)` that commits
  on a later render tick than the network response the page object already
  awaits).
- The AFS documents WHY no condition-wait is possible: the modal's visible
  content (name/description/CHAT STARTERS/Welcome Message) renders from a
  synchronously-available prop, so nothing in the DOM distinguishes
  "agentDetails loaded" from "still null" for a no-starters agent — both
  states render identical empty-state text.
- It's declared in three places (test docstring/inline comment citing #1043,
  AFS § Known Defects + § Automation Hints, role-memory entry
  `test-automation-engineer/catalog_start_chat_1043_needs_extra_wait.md`) —
  not silently copied.
- It's in the SPEC file (test synchronization for an unobservable gap), not
  smuggled into a page-object method as reusable "normal" behavior.
- #1043 already lists 8+ sibling cases (ELITEA-2356/57/58/59/60/61/62/69) that
  will hit the same race — this wait will recur across that whole family
  until the product fix ships; expect it and don't re-litigate it per case.

**Review test:** is the wait (a) tied to a filed, open defect, (b) justified
with a stated reason no DOM/network signal exists, and (c) declared in the
diff itself (not just the AFS)? All three → sanctioned declared improvisation,
non-blocking. Missing any → treat as the ELITEA-2272 anti-pattern instead.

## UPDATE (2026-08-11, ELITEA-2360 review, `tests/2360-start-chat-fix`)

The wait moved from being redeclared at each call site (2368/2369's shape,
above) to living **inside** `AgentHubPage.click_start_chat()` itself — the
one factor this entry originally listed as a *positive* ("not smuggled into
a page-object method as reusable 'normal' behavior") now flips. Reviewed
this deliberately rather than treating the flip as automatically
disqualifying:

- Verified independently (not taken on faith): root cause against
  `AgentModal.jsx` source (`onStartConversation`, line 277; `useState(null)`,
  line 52; async fetch, lines 81-90 — exact match), #1043 still open/labelled
  `bug`, and the claimed precedent — `git log --all -p -- agent_hub_page.py`
  shows `wait_for_timeout` NEVER existed in the page object before this PR;
  the real precedent is call-site copies in the two merged 2368/2369 test
  files (`grep -n wait_for_timeout` on `origin/automation/base` confirms
  both, immediately before their own `click_start_chat()` calls).
- The 3-point test still holds: (a) #1043 open, (b) justified — confirmed
  `isFetching` guards ONLY the separate "Show instructions" modal, not the
  Start Chat button, and `modal_show_instructions_link` renders
  unconditionally (source-verified), (c) declared at length in the method
  docstring, not silent.
- The "smuggled into a page object" risk is real in principle (a future
  caller sees a working method, not a documented gap) but is mitigated here
  by an unusually long, specific docstring naming the exact defect, line
  numbers, and repro thresholds right at the call site — a future reader
  can't miss it the way a bare `page.wait_for_timeout(1000)` with no comment
  would be missed.
- Flagged (non-blocking, per role-overrides.md's declared-improvisation
  protocol — sound reasoning can't solo-FAIL) that a click-retry-until-
  `wait_for_url`-succeeds loop was available and not discussed: the click is
  a verified no-op when it hits the race (no `dispatch()` before the throw),
  so retrying is safe, and `capture_console_errors()` only hooks
  `page.on("console")` — NOT `pageerror` — so a retry attempt's uncaught
  TypeError would not even trip this suite's own `assert not console_errors`
  checks. A flat sleep is a weaker design than a bounded retry on the actual
  downstream observable, even when it's the declared, defect-linked,
  precedented kind. Recommended (not required) as a hardening follow-up +
  a formal canon exception in `.agents/testing.md` given this is now the
  3rd occurrence of the identical shape for the identical defect.

**Takeaway for the next reviewer:** page-object consolidation of a declared
wait_for_timeout is not itself a red flag — re-run the same 3-point test
against the CURRENT diff's own evidence (don't just trust a docstring's
claimed precedent; grep for it) — but do treat 3 uses of the same workaround
as a trigger to ask "should this become an explicit canon exception instead
of a per-PR re-justification," not just re-approve indefinitely.
