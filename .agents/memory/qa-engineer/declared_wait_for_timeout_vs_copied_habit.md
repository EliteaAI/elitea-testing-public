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
