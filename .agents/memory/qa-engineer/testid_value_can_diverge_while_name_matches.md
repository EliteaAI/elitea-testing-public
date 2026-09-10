---
name: A testid can break on main while its NAME still matches — check the value expression
description: Provenance greps by testid name pass while the rendered value diverges; grep the template's value expression across refs, and read the live DOM on both envs.
type: feedback
aliases: [testid value divergence, chat-participant-row, testid-loss guard blind spot, ParticipantNormalCard, EL-6405]
tags: [area/locators, area/testids, type/gotcha]
created: 2026-09-10
updated: 2026-09-10
---

## The trap

The closure-record / promotability grep answers *"is this testid NAME on `main`?"*.
It cannot answer *"does `main` render the same VALUE?"* — and neither can
`sync-base-branches`' testid-loss guard, which diffs the **set of names**.

Worked case (ELITEA-1793, board #2142, root cause #2013): UI-team commit
`b4d00fcc` (EL-6405, EliteaAI/EliteaUI#887) extracted
`ParticipantItem.jsx` → `ParticipantNormalCard.jsx` and rewrote the row testid's
value in passing:

```
origin/main               data-testid={`chat-participant-row-${participant.id ?? participant.entity_meta?.id}`}   -> chat-participant-row-9249
origin/automation/testids data-testid={`chat-participant-row-${getChatParticipantUniqueId(participant)}`}         -> chat-participant-row-application_9249_399
```

Name identical on both refs ⇒ every name-based check reported `main: YES`.
The guard logged "0 lost, 1101 → 1177", correctly. The spec was green on
localhost and structurally impossible on DEV.

## What to do instead

1. For a **templated** testid, grep the literal the template contributes with
   `git grep -F -- 'chat-participant-row-${'` on BOTH refs, then **read the two
   hits** — do not count them.
2. If a component file differs between refs at all, `git diff origin/main
   origin/automation/testids -- <file>` instead of trusting any grep (#2013's own
   advice; a runtime-composed value is invisible to a substring grep).
3. Confirm by reading the **rendered attribute out of the live DOM on both
   environments**. That is the only evidence that settles it. A tiny throwaway
   pytest probe reusing the framework's own auth + page objects gets it in ~50 s
   per environment and never exposes credentials.

## The chronology question that changes the disposition

Ask **"was our form ever on `main`?"** — `git grep <testid> b4d00fcc^` /
`git log -S'<value expression>' origin/main`. Two very different verdicts:

- *never promoted* ⇒ class **F** promotion gap; wait for a human cherry-pick.
- *promoted, then overwritten by a refactor* ⇒ `.agents/workflow.md` § Divergence
  rule **bullet 1** — main's structure, our attribute **re-added on top**;
  "losing one here is a defect, not an acceptable merge outcome." The
  `automation/testids` side is then the CORRECT ref and `main` is degraded.

Tell-tale that it was collateral, not a deliberate rename: the commit subject is
unrelated (a warning-frame bug fix), and sibling call sites were left on the old
form — here `UserMenu.jsx` kept the composite shape, leaving EliteaUI `main`
internally inconsistent with itself.

Related: [[participant_row_blast_radius_users_vs_entity_rows]]
