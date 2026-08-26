---
name: Verifying a red-green claim statically
description: How a static reviewer confirms an assertion can actually fail, without re-running it — read the producing JSX for conditional rendering
type: feedback
aliases: [red-green claim, vacuous assertion, static assertion strength, can this assertion fail]
tags: [area/review, type/technique]
created: 2026-08-27
updated: 2026-08-27
---

## The problem

The reviewer slot is STATIC — an implementer's "I temporarily asserted
`to_have_count(2)` and it failed with `Actual value: 1`" is a claim you cannot
re-run. Inheriting it defeats the point of an adversarial gate; disbelieving it
with no method just stalls the loop.

## The method — read the PRODUCER, not the assertion

An assertion discriminates iff the element it counts is **conditionally
rendered** on the state under test. Check that in the source that renders it:

1. Find the testid in the owning repo on the branch the dev server serves
   (`git fetch origin` first, then `git grep -n -- "<testid>" origin/automation/testids -- src/`).
2. Open the component and look for the render guard. A chip guarded by
   `{attachments.length > 0 && (...)}` renders **zero** nodes when nothing is
   staged ⇒ `to_have_count(1)` genuinely fails if the flow breaks.
   An element rendered unconditionally would make the same assertion theatre.
3. Confirm the asserted TEXT is bound to product data, not a literal —
   `<span>{attachment.name}</span>` means `to_contain_text("<file>.txt")` reads a
   value the widget derived from the real `File`, i.e. real provenance.

Worked case: ELITEA-1802 / PR #1828 (`support-assistant-attachment-chip`,
`elitea_assistant` `src/components/chat/attachments/AttachmentChip.tsx:35`,
rendered under `MessageInput.tsx:208`'s `attachments.length > 0` guard).

## The inverse tell — a wait that cannot fail

`wait_for_network()` / `networkidle` placed after an action that fires **no
request** settles because nothing was in flight. When a diff removes one, do not
score it as "coverage dropped" reflexively: check the analyst's network capture
for the flow. Removing an assertion with no failure mode and adding one with a
real failure mode is a STRENGTHENING, and the declared-improvisation ceiling is
not engaged. The stale case text is a CLARIFICATION (reverse-masking guard) and
must have a filed ticket — verify the ticket exists and is `question`, not `bug`.

Related: [[git_worktree_can_leave_main_checkout_on_wrong_branch]]
