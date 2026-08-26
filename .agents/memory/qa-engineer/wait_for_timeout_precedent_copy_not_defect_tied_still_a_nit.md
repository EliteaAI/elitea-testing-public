---
name: wait_for_timeout copied from an already-merged sibling method — third shape
description: A third wait_for_timeout shape distinct from the other two entries — copies an ALREADY-REVIEWED, already-merged sibling method verbatim, no AFS warning either way. Non-blocking nit, not the 2272 anti-pattern, but also fails the declared/defect-tied 3-point test.
type: feedback
---

## Context (ELITEA-2103/2104 review, PR #1517)

Two sibling memory entries already cover two shapes of `page.wait_for_timeout`
review judgment:

- `wait_for_timeout_copied_despite_afs_warning.md` (ELITEA-2272) — implementer
  copies a `wait_for_timeout` habit into a NEW page object DESPITE an explicit
  AFS warning not to. Real violation.
- `declared_wait_for_timeout_vs_copied_habit.md` (ELITEA-2368/2360) — a
  `wait_for_timeout` tied to a filed, OPEN product defect, justified inline
  (no DOM/network signal exists), declared in the diff. Sanctioned exception —
  the 3-point test: (a) defect-tied, (b) justified, (c) declared.

ELITEA-2103/2104's `ChatPage.clear_conversation_name()` and
`paste_conversation_name()` (both NEW methods this PR) each add
`self.page.wait_for_timeout(100)` after a `.click()` — but this is neither of
the above:

- **Not the 2272 shape**: neither AFS (ELITEA-2103's or ELITEA-2104's) says
  anything about `wait_for_timeout` at all — no warning to violate.
- **Not the 2368 shape**: not tied to any filed defect; the comment is a bare
  `# Wait for focus` / `# Wait for clear to complete`, no "no DOM signal
  exists" reasoning. Fails point (a) of the 3-point test outright.
- **What it actually is**: a verbatim copy of the SAME idiom already used (and
  already reviewed, already merged) in `set_conversation_name()` /
  `set_folder_name()` in the SAME file, for the SAME editor-focus race — the
  new method's own docstring says so explicitly ("Same click() + clear() +
  press_sequentially() idiom as set_folder_name()").

**Review call:** treated as a non-blocking Nit, not `CHANGES_REQUESTED`. The
`role-overrides.md` "precedent is not authority" rule targets a NEW deviation
nobody had a rule to block — this is not that; it's continuing an existing,
already-reviewed pattern in the identical file for the identical purpose,
100ms only, not a "hope it's enough" arbitrary sleep. Blocking it here would
leave the same editor family inconsistent (some methods sleep, some don't)
without addressing the underlying pre-existing debt across the whole file (41
`wait_for_timeout` occurrences in `chat_page.py` before this PR).

**Takeaway for the next reviewer:** when a new `wait_for_timeout` traces to an
ALREADY-MERGED sibling method in the same file (not just "some precedent
somewhere"), that's a third, weaker-but-not-zero signal — cite it as a nit
with a suggested batch-cleanup follow-up, don't silently wave it through and
don't block a single PR over file-wide pre-existing debt it merely continues.
If the SAME new shape recurs a 3rd time in fresh (non-mirrored) code, escalate
to a canon exception request instead of re-litigating per PR (mirrors the
2360 update's "3rd occurrence" trigger).
