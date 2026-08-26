---
name: Empty-state preconditions are usually unreachable on the shared localhost identity
description: Before speccing any "shows empty state when no X exist" case, check whether an X-free project/user is obtainable at all — usually it is not, and the case is blocked, not automatable
type: feedback
aliases: [empty state, no secrets, no tokens, empty precondition, blocked precondition]
tags: [area/settings, type/fidelity]
created: 2026-08-24
updated: 2026-08-24
---

## The pattern

TMS cases of the shape *"page shows the empty state when no <entity> exist"* look
trivial (assert a message + a create button) but their real cost is the
**precondition**. On this project the shared `${TEST_USER}` on localhost has:

- **Secrets** (project-scoped, `GET /api/v2/secrets/secrets/default/{project_id}`):
  of 5 selectable projects only `Private` (399, 120 secrets) and `UI Testing`
  (400, 4 secrets) answer `200`; 406 / 25 / 471 answer **403**. A 403 project
  renders the ordinary `"No secrets"` empty state (query is skipped client-side) —
  a *permission* artefact, not an empty project. No create-project affordance
  exists in the project selector. Bug #1773.
- **Personal tokens** (USER-scoped — `useTokenListQuery` takes no project id): 5
  persistent tokens, two of them **expired** and therefore unrecreatable, and
  ELITEA-2284's merged test reads its `expired` branch off exactly those rows.
- **A second identity**: `auth_state_user_b` exists but `pytest.skip`s on localhost
  by design (`automation/fixtures/session_fixtures.py:133`).

## What to do

Check the precondition FIRST (one API call per candidate project / one page load),
before speccing steps. If no empty tenant exists: the case is **blocked** and gets
routed to a human — deleting shared data to reach an empty state and fabricating an
empty list response are both out (`.agents/testing.md` § Fidelity policy). Say in
the AFS exactly which routes were checked and why each fails; that is the artifact
the human needs.

Related: [[settings_drawer_had_zero_testids]]
