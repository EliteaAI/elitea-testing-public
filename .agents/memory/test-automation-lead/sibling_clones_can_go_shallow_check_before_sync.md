---
name: Sibling clones can go shallow — check before sync-base-branches
description: Both elitea-testing-public and EliteaUI sibling clones were found shallow (no .git/shallow check had ever failed before #102) — the skill's own preconditions step catches it, but only if actually run; a shallow clone gives nonsense ahead/behind counts and misbehaves on merge
type: feedback
---

On #102 (ELITEA-1909), the `sync-base-branches` skill's own Preconditions
step-0 check (`test -f "$d/.git/shallow"`) fired for BOTH sibling clones —
`elitea-testing-public` and `EliteaUI` — despite this being routine, N-th
sync of the session-start ritual. Nothing before this delivery had ever
hit it, so it's easy to skip the check on autopilot and jump straight to
`git merge origin/main`.

**Why it matters:** a shallow clone has no real merge-base with a
force-pushed-free branch history. `git merge` on a shallow clone can
misbehave (wrong merge-base picked, or refuses outright), and
`git rev-list --left-right --count` reports nonsense ahead/behind numbers
that look plausible but are wrong — which would have made the "both
branches 0-behind their mains" verification step at the end of the sync
lie.

**Fix, cheap and idempotent:** `git fetch --unshallow origin` on both
clones before anything else. It's a no-op (fast, no-op fetch) if the clone
is already full, so there's no cost to always running it as the very first
sync-base-branches command rather than trusting memory that "this repo was
full clone last time."

**Actionable:** run the shallow check as a literal command every single
sync-base-branches invocation, don't skip it because prior sessions never
tripped it — clone depth can change under you (a fresh checkout, a CI
runner reusing a shallow cache, etc.) with no visible warning until a merge
or a rev-list count goes wrong downstream.
