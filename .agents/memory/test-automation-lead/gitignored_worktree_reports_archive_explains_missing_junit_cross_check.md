---
name: Gitignored worktree reports/archive explains missing junit cross-check
description: automation/reports/archive/ is gitignored and per-working-tree; a merge gate run in an isolated `git worktree` leaves junit files that vanish once the worktree is removed — the primary tree's archive genuinely won't have them, and that absence is expected, not a fabrication signal
type: feedback
---

`archived_junit_cross_check_for_merge_gate_timing.md` documents matching a closure
record's pasted 3× gate durations/timestamps against `automation/reports/archive/*.xml`
as an independent corroboration technique. That technique implicitly assumes the gate
ran in the **primary working tree** the auditor is standing in.

It doesn't hold when the closure record itself says the gate ran in an **isolated
`git worktree`** (a documented pattern per `git_reset_hard_incident_recurred_use_worktree.md`,
used specifically so the merge-gate checkout never moves the shared tree's HEAD).
`reports/` and `reports/archive/` are listed in `.gitignore` — they're untracked,
per-directory local state, not shared across worktrees the way tracked files are.
Once the worktree is torn down after the merge (routine cleanup), its local
`reports/archive/*.xml` files go with it. The primary tree's archive was never
going to have those specific filenames/timestamps, regardless of whether the gate
genuinely ran.

Confirmed on #222/PR#644 (2026-07-19): closure record cited `junit_20260719_112510/
112534/112609.xml` from an explicitly-isolated-worktree gate; the primary tree's
archive had plenty of files from that day but none at those exact timestamps. Checked
`git worktree list` (only the current worktree remained) and `.gitignore` (confirmed
`reports/`/`reports/archive/` both listed) before concluding this was the expected
"can't verify, and that's fine" case — not a discrepancy — and judged item 5 on the
pasted evidence alone, per the audit's own evidence principle (this class of proof is
non-reproducible without the live UI/original worktree).

**When auditing item 5:** if the closure record says the gate ran in an isolated
worktree, don't expect the primary tree's archive to corroborate it — check
`.gitignore` for `reports/` first so you don't misread an expected absence as a red
flag. Only treat a *primary-tree* gate's archive mismatch as suspicious.
