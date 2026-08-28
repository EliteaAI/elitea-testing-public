# Read the sibling card's thread before dispatching anything

**Date:** 2026-08-28 · **Evidence:** #1893 (ELITEA-2002) vs #1872 (ELITEA-1888) / #1874

A `[Fix][...]` card arrives describing a failure as if it were novel. It often is not.
#1893's own body said *"same pattern as #1872, #1873"* — and #1872's **closure record
named #1893's exact spec** as the next red with the byte-identical signature, while
#1874 already carried the proven mechanism and the fix shape.

**So: before the first dispatch, read every issue the card references, and their
closure records — not just their titles.** It converted this card from
"investigate a version-id assertion failure" into "confirm a known mechanism applies
here", which is a much cheaper and much better-specified analyst dispatch.

**But do NOT let the prior become the evidence.** The analyst dispatch said, in these
words: *"This is a prior, not evidence. A same-shaped symptom can still have a
different cause. Your brief must stand on YOUR OWN live observation, and you must
explicitly test and refute the competing hypothesis (backend relabels in place =
product bug)."* The analyst did refute it with its own network capture. Without that
instruction the cheap path is for the analyst to pattern-match and inherit a
conclusion — which is exactly how a real product bug would get filed as a test bug.

**Corollary — a fix card's stated scope is a lower bound, not the scope.** #1893 named
one spec; the same `confirm_new_version` call site was failing a second one
(ELITEA-2003). Ask the analyst to enumerate the **call sites**, not the reported
failures. Fixing one and leaving its twin red is a delivery that reads as complete and
is not.

**Corollary 2 — card metadata is not fact.** #1893 asserted "AFS: Not found" (it
existed) and framed the failure as deployed-env-only (it reproduced 2/2 on localhost).
Both wrong, both cheap to check, both would have mis-steered the work. Verify the
card's own claims as part of intake.
