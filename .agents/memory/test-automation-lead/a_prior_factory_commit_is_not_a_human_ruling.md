---
name: A prior factory commit is not a human ruling
description: The factory commits under the operator's own git/gh identity, so its past decisions read as human rulings — check before citing one as authority
type: feedback
aliases: [who authored this commit, operator precedent, bermudas identity, is this a human ruling, precedent is not authority]
tags: [area/governance, type/trap]
created: 2026-09-09
updated: 2026-09-09
---

## The trap

Factory sessions commit as `Alexander Bychinskiy <bermudas.alexander@gmail.com>`
and comment on the tracker as `bermudas` — **the operator's own identity**, because
`env -u GITHUB_TOKEN` deliberately runs `gh` as the keyring account. So a decision
made by a previous factory run is indistinguishable, at a glance, from one a human
made.

On #2062 I found `88c2f49` in the TMS repo (a sanctioned-RED back-write shape),
saw the operator's name and yesterday's date, and wrote *"applying the operator's
own precedent"* into a closure record. It was **my own predecessor's** choice, from
the #2051 run. I had cited myself as authority and called it a human ruling.

## Why it is worse than an ordinary precedent slip

`.agents/role-overrides.md` § Precedent is not authority already says a merged
example is never a ruling. This trap defeats that rule specifically, because the
identity check is the one signal that *would* have distinguished them — and it
points the wrong way. It converts "some agent did this once" into "the human
decided this", which is exactly the laundering the override rule exists to stop.

## The check, before citing any commit or comment as authority

```bash
git log -1 --format='%an %ad %s' <sha>          # necessary, NOT sufficient
env -u GITHUB_TOKEN gh issue view <N> --json comments  # did a factory card work this?
```

The reliable tell is **not** the author line — it is whether a factory card was
being worked at that moment. A closure record, a `🔧 Factory … works this card`
comment, or a `Found while working #N` trailer on the commit means an agent did it.
A human ruling looks like a comment on a `question` card, or an instruction in a
dispatch — a human steers by commenting, not by committing.

## The reusable move

When canon and a config file appear to contradict, the honest resolution is canon
plus a **declared** choice, not a precedent hunt. Cite the doc and section; if the
only support is a merged example, say "precedent, not authority" out loud and name
the open question card that owns the decision.

Related: [[sanctioned_red_tms_backwrite_shape]] · [[sanctioned_red_is_never_back_written_automated]]
