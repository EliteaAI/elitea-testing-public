---
name: A card moved to Approved with no comment is not an answer — verify, don't guess
description: When a human drags a parked card back without commenting, re-verify every named blocker yourself before assuming any of them changed
type: feedback
aliases: [Approved with no comment, silent unblock, resume protocol, breilian, ELITEA-0143, "#1814"]
tags: [area/process, type/orchestration]
created: 2026-08-28
updated: 2026-08-28
---

## What happened (#1814 / ELITEA-0143, 2026-08-28)

A parked card (`Blocked`, waiting on 3 named issues) was moved back to `Approved` by a real human
(`breilian` — confirmed distinct from the factory's own tracker identity via
`gh api graphql` `timelineItems(itemTypes:[PROJECT_V2_ITEM_STATUS_CHANGED_EVENT])`, which also
timestamps the move and names the actor — useful whenever "did a human really do this" needs an
answer). **No comment was left** on the card or on any of the 3 issues it was waiting on.

The standing protocol says "read the children's threads first (answers and decisions live there)" —
but sometimes they don't. Guessing which blocker was resolved (or assuming none were and re-parking
immediately) are both wrong moves. The right move is cheap and mechanical: **re-verify every named
blocker yourself, fresh, before acting on the Approved status at all.**

## What re-verification found

Of 3 named blockers, re-checking directly found:
- **#1673** (expired token) — unchanged (file mtime, direct curl re-check).
- **#1856** (a decision request) — still unanswered (zero comments, zero reactions).
- **#1821/#1850** (DEV Keycloak rejecting all test users) — **silently resolved**: a live
  `api_auth.get_auth_cookies()` call against the actual environment succeeded. Nobody said so anywhere
  in the tracker; the only way to know was to try it.

That third one was almost certainly *why* the human approved the card — but I only learned that by
testing it, not by being told.

## The technique, generalized

When resuming a parked card with no textual answer: don't ask "what changed" — **re-run the exact
check that produced each blocker in the first place**, using the project's own scripted tools
(`api_auth.get_auth_cookies`, a direct curl, a `list_models.py`-style helper) rather than driving the
full UI. It's cheap, and it turns "someone approved this, unclear why" into a fact table you can post
and act on. Post that table before doing anything else — it makes your next move legible even when the
human's didn't explain theirs.

## The corollary this run also proved

Fixing one blocker doesn't always finish the job — it can just relocate the investigation to a place
that has its own new blocker. Here, DEV access coming back let the analyst chase the real unexplained
symptom, which immediately surfaced a *different*, narrower blocker (CI's per-executor masked project
secrets) that nothing before had visibility into. Re-park on the NEW blocker, explicitly superseding
(not replacing) the still-open original question — don't let progress read as "nothing happened" just
because the case didn't close.

Related: [[a_parked_case_is_a_hypothesis_not_a_verdict]] · [[disproof_beats_a_plausible_root_cause]] · [[dev_repro_use_localhost_not_shared_env_test]]
