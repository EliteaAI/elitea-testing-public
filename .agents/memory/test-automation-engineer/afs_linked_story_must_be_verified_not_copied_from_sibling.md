---
name: AFS Linked Story field must be verified, not copied from a sibling case's AFS
description: When a batch case-snapshot's "Intake context" block quotes another (sibling) case's tracker issue for background, that number is NOT automatically this case's own Linked Story — verify via a real-time gh issue list before writing it into a new AFS's Metadata block.
type: feedback
---

## What happened (ELITEA-2226/2228/2229/2230, PR #1495, 2026-08-14)

Four combined analyst+implementer cases shared an "Intake context" preamble
(injected by the batch orchestrator) that described prior merged work on the
same surface, referencing `EliteaAI/elitea-testing-public#734` — the
`[Automate][ELITEA-2227]` tracker card for the SIBLING case whose spec these
4 cases extend. I copied `#734` into all 4 new AFS files' `Linked Story`
metadata field, following the pattern of ELITEA-2227's own AFS, without
verifying that a card actually existed for ELITEA-2226/2228/2229/2230
themselves.

A real-time check (`gh issue list --repo … --state all --limit 1000 --json
number,title`, then keyword-matching locally — never `--search`, per the
project's dedup-lag rule) found **no** `[Automate][ELITEA-2226]` /
`-2228` / `-2229` / `-2230` cards exist at all. `#734` is case-specific to
ELITEA-2227 and CLOSED — not a shared story for the cluster. Caught this
myself before handoff (not by a reviewer) by trying to post the mandatory
"comment PR link on originating issue" step and finding the target issue was
wrong for 4 of my own claims.

## The fix

Corrected all 4 AFS `Linked Story` lines to state plainly that no card was
found, with the verification command + result inline, rather than silently
keeping the copied `#734`. Skipped the "comment PR link on originating
issue" step entirely for these 4 cases (nothing exists to comment on) and
reported the gap in findings for the orchestrator instead of inventing a
target.

## The reusable check

Before writing an AFS `Linked Story` field, when the case arrived via a
batch dispatch whose "Intake context" block cites a NUMBER — don't assume
it's shared across every case in the same dispatch. Run the real-time issue
list (per `.agents/profile.md` § Issue tracker dedup rule — no `--search`)
and keyword-match your OWN case ID before writing the field. A shared
surface digest / covering spec does not imply a shared tracker card — those
are two different artifacts (test-specs digest vs. GitHub issue), and a
batch's cases may have been carded individually, carded as one cluster, or
(as here) never carded at all.
