---
name: A declared improvisation needs an AFS sweep, not just PR narration
description: Narrating a mid-implementation testid/handle addition in the PR body's "Declared improvisation" section is NOT the same as amending the AFS document — the AFS Concrete Handles table + Automation Hints must gain the new handle in the SAME commit, or a review round is spent recovering it.
type: feedback
---

## Rule

When Phase 2/3 exploration surfaces a handle the AFS didn't ask for (a second
testid, a different interaction pattern than the AFS suggested), the
"declared improvisation" protocol (`.agents/role-overrides.md` § Every role)
has TWO deliverables, not one:

1. Narrate the reasoning in the PR body (`## Declared improvisation`) — this
   is what the reviewer reads to verify the *reasoning*.
2. **Sweep the fact into the AFS document itself** — Concrete Handles gets a
   new row, Automation Hints gets the pattern rewritten. This is what every
   FUTURE reader of the AFS (a later analyst on the same surface, a closure
   record, a promotability check) relies on. A PR body is not part of the
   AFS; it is read once and then buried in git history.

Doing only (1) reads as "I explained it" but leaves the AFS silently
incomplete — indistinguishable from just not having done the sweep at all,
from a reviewer's grep-the-diff perspective (`git diff <covering-afs>` shows
nothing changed).

## Seen (ELITEA-2436, PR #1448)

Implementation added a second testid, `model-settings-creativity-slider-input`
(`EliteaAI/EliteaUI@42c7e3eb`), via a new `inputTestId` prop threaded through
`DiscreteSlider.jsx` → MUI's `slotProps.input` — needed because the AFS's
originally-requested wrapper testid (`model-settings-creativity-slider`) only
supports a presence check, not driving the slider's value. The PR body's
"Declared improvisation" section explained this fully and correctly. The AFS
amendment commit in the SAME PR (`docs(afs): …`) touched only step 3's
"OK"-response drift — the Concrete Handles table and Automation Hints section
still showed only the ORIGINAL single-testid ask, with no row and no mention
of the second testid at all. Reviewer caught it: "not addressed — no attempt
visible in the diff" (round 1). Fixed by adding a dedicated Concrete Handles
row + rewriting the Automation Hints `add-data-testid` bullet and the
discrete-slider-interaction note to name both testids, their originating
commits, and the `slotProps.input` mechanism — in the SAME PR, round 1.

## Seen also (ELITEA-2157/2158, PR #1553, fix round 1)

Same failure mode, a THIRD near-miss surface: not the PR body this time, but
a same-PR `_surface.md` digest commit. Implementation found the "Duplicate"
context-menu item had no `key`/testid at all — the test's own
`get_open_conversation_menu_item_count() == 6` assertion silently depends on
it via a prefix-wildcard locator — and added
`key: 'chat-conversation-menu-duplicate'` (`EliteaAI/EliteaUI@a53b9d4b`). The
finding was narrated fully and correctly in a commit literally titled
`docs(afs): … implementation-time digest notes` — but that commit's diff
touched ONLY `test-specs/<feature>/_surface.md`. The AFS file itself still
said, verbatim, "**No new testids needed for either case.** All handles
already exist and are provisioned" in its own Concrete Handles table.
Reviewer caught it, same "not addressed — no attempt visible in the diff"
verdict. **A commit message containing `docs(afs):` is not evidence the AFS
was amended — `git show --stat <sha>` (or diff the AFS path directly) before
crediting an amendment.** `_surface.md` (the digest) and the case's own AFS
file are two different documents that happen to share a directory and a
commit-message prefix; only the AFS is what Phase 1's Coverage-Map walk and
the reviewer's provenance grep read. Fixed round 1 by adding the Concrete
Handles row + replacing the false "no new testids" sentence + correcting the
Automation Hints line — same remedy as below, applied to a THIRD surface
(digest commit) beyond the original two (PR body, general staleness).

## Remedy

Before finishing ANY `docs(afs): amend …` commit that follows a declared
improvisation: grep the AFS for the improvised concept's PLANNED name (the
thing the AFS originally asked for, e.g. `model-settings-creativity-slider`
without the `-input` suffix) — if the AFS still shows only the old ask with
no trace of what actually shipped, the amendment is incomplete. Amending
"the row a reviewer will look at" is not the test; amending EVERY section
that restates the same fact (Concrete Handles, Automation Hints, and the
Summary/"for the implementer" paragraph if one exists) is.
