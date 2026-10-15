---
name: SendMessage-resumed background agents are fragile in factory/unattended mode — prefer fresh foreground dispatch for fix-only rounds
description: A SendMessage-resumed agent runs in the background with no synchronous option; in this project's headless factory mode it got silently killed by process restarts twice in one delivery (issue #88), each time leaving real uncommitted work behind — switching to a fresh foreground Agent() call to finish+land the existing diff worked on the first try
type: feedback
---

## What happened (issue #88, ELITEA-1893, PR #571)

`resuming_subagents_for_narrow_fixups.md` recommends `SendMessage(to: agentId, ...)`
to resume the same implementer session for a narrow, additive fix-only round instead
of a fresh dispatch — cheaper, keeps context. That's still correct advice in an
interactive session. But `SendMessage` **always resumes in the background** — there's
no `run_in_background: false` equivalent the way the `Agent` tool has. In this
project's factory/unattended mode, the delta rules mandate **foreground dispatch,
one at a time** specifically because a background task's result can be lost if the
turn/process ends before it's collected — and that's exactly what happened, twice:

1. Dispatched fix-only round R1 via `SendMessage` to the implementer's existing
   `agentId`. It got resumed in the background. My own in-turn wait (a Bash
   `run_in_background` poll loop) got interrupted by a harness/process restart before
   completion — but so did the resumed agent itself. On the next turn, `git status`
   showed 2 of 4 findings genuinely fixed and pushed-worthy (EliteaUI testid commit
   already pushed), but nothing committed on the test-repo side.
2. Sent a second, narrower `SendMessage` naming exactly the 2 remaining findings.
   Same failure mode: the process restarted again mid-work. `git status` this time
   showed ALL 4 findings' fixes present and *substantively correct* in the working
   tree (verified by reading the diffs, not trusting a summary) — but again nothing
   committed or pushed.

Both times, `interrupted_dispatch_recovery.md`'s check-before-re-dispatching pattern
caught the real state and prevented duplicate work. But two turns were spent
recovering instead of progressing.

## The fix

On the second interruption, abandoned the SendMessage-resume pattern entirely and
dispatched a **fresh, foreground** `Agent()` call (`run_in_background: false`) with a
prompt that explicitly said: the diff already in the working tree is correct, verify
it, don't redo it, then run/commit/push. This landed cleanly on the first attempt —
foreground dispatch blocks until the result is actually returned, so there's no
window for a process restart to silently kill it mid-work.

## Rule going forward (factory/unattended mode specifically)

- **Interactive session**: `resuming_subagents_for_narrow_fixups.md` still applies —
  SendMessage-resume for narrow fixups is fine, the session isn't at risk of the
  kind of process-restart interruption factory mode sees.
- **Factory/unattended mode**: prefer a **fresh foreground `Agent()` dispatch** even
  for a narrow fix-only round, especially on a SECOND resume attempt after one
  interruption already happened. If a resume gets interrupted once, don't try
  `SendMessage` again — switch to foreground `Agent()` and explicitly tell it to
  verify+finish+land whatever's already sitting correct-but-uncommitted in the
  working tree (checked via `git status`/`git diff` first, per
  `interrupted_dispatch_recovery.md`), rather than re-deriving the fix from scratch.
- This does NOT contradict `resuming_subagents_for_narrow_fixups.md` — it narrows its
  applicability. Background resume is a real capability with a real cost profile;
  factory mode's process-restart risk makes that cost bite harder than in an
  interactive session.

## Seen 3× — #2411/ELITEA-2006 (2026-10-07), caught BEFORE any interruption this time

The tell is visible in the **result shape itself**, with no need to wait or poll first:
a foreground `Agent()` call's result IS the subagent's full final report, inline, in
the same tool round (confirmed again this session — the first dispatch returned a
multi-paragraph "[Subagent hand-back]" report directly). A `SendMessage` call to
resume an agent returns only `{"success":true,"message":"Resuming agent...",...}` —
an ack, never the content. Seeing that ack shape is itself the signal to stop and not
wait for a reply in the same turn — don't even bother with one `ListAgents` check to
confirm "running" (though it did, here); `TaskStop` the resumed agent immediately and
re-dispatch foreground with "here's what's already on disk, verify + finish it,
don't redo it." Zero turns lost this time (direct from ack to `TaskStop` to fresh
foreground dispatch), vs. the two interrupted rounds in the #88 occurrence — the
partial work the resumed agent had made (one isolated code edit, no AFS/commit yet)
was intact and reusable exactly as `interrupted_dispatch_recovery.md` predicts.

## Seen 4× — #2410/ELITEA-2051 (2026-10-15): applies to VERIFICATION resumes too, not just fix rounds

Every prior occurrence here was a fix-only implementer round. This one was a
SendMessage-resume of an **analyst doing live-DEV verification** (not writing
code) — same ack-only result shape, same no-synchronous-option problem, but
this time nothing crashed; it just ran far longer than any verification task
should (~10+ bounded poll cycles, no result) with no visible signal of
progress vs. being stuck. Stopped it with `TaskStop` and re-dispatched a FRESH
foreground `Agent()` with a narrower, already-diagnosed prompt — got a full,
useful report on the first call. **Rule now covers any SendMessage-resume in
factory mode, not just fix-only rounds**: the moment you're about to resume an
existing agent rather than dispatching fresh, stop and ask whether the
narrower-context cost saving is worth losing synchronous foreground semantics
— in factory mode, it rarely is. Prefer fresh foreground dispatch as the
default; reach for SendMessage-resume only when the existing agent's context
(a long investigation, a large diff already loaded) is expensive enough to
redo that even the resume risk is worth it, and even then, cap the wait and
bail to fresh-foreground on the first sign of taking too long rather than
after a crash.
