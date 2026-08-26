---
name: No second user identity — blocks all "non-owner cannot X" cases
description: Only one credential (${TEST_USER}/VITE_DEV_TOKEN) exists anywhere; a case needing a DIFFERENT person is blocked outright, not just a different role
type: project
---

## The gap

`.env.test` defines exactly one UI credential pair (`TEST_USER_EMAIL`/
`TEST_USER_PASSWORD`), and localhost's `auth_state` bypasses login entirely via a
single static `VITE_DEV_TOKEN` (`../EliteaUI/.env`) — the SAME fixed identity
(`author_id: 659`, "Test Bot") every time, wired in `root.jsx`/`upload.js`/
`useArtifactContentFetch.hooks.js`/`SupportAssistant.jsx`. There is no code path
on localhost to authenticate as a second, distinct human. Confirmed live
(ELITEA-2189/2190/2191, 2026-08-15): `GET
/api/v2/elitea_core/folder/prompt_lib/471?grouped=true` returns every
conversation in the shared Team project with `author_id: 659` — no
other-authored conversation, public or private, is reachable.

**"Invite Users" is a trap here** — it adds named users ("Hrach Sargsyan", "Levon
Dadayan", …) as **participants** of a conversation `${TEST_USER}` still
owns/authors. Those names come from a user-search endpoint with no
corresponding password/token this suite holds. Adding someone as a participant
is NOT the same as being able to log in as them.

## What this means for a case

Any case shaped "non-owner cannot X", "user B cannot see/edit/delete user A's
private/public Y", or generally requiring TWO distinct authenticated identities
in the same live flow is **`blocked` outright** on localhost — there is no
partial-coverage path (unlike the RBAC-role gap in
`no_non_admin_test_user_credential_exists.md`, which sometimes has an
admin-provable half). Don't spend a session hunting for a workaround:
`page.evaluate()`-injected `author_id`, reusing `auth_state` with a hand-edited
identity, or seeding via API "as" a different user are all forbidden
substitutions (`.agents/testing.md` § Fidelity policy — "bypassed subject",
"injected app state") unless the case text itself asks for simulation (it
won't, for this shape of case).

Check [Question #1563](https://github.com/EliteaAI/elitea-testing-public/issues/1563)
first — it already covers this exact gap (filed for ELITEA-2189/2190/2191, one
issue for the shared root cause, precedent-matched to #1314's analogous
RBAC-role gap) before re-investigating from scratch.

Worked examples (all `blocked`, same session):
`test-specs/chat-interface/l2_non-owner-cannot-delete-public-conversation_ELITEA-2189.md`,
`l2_non-owner-cannot-edit-messages-public-conversation_ELITEA-2190.md`,
`l2_non-owner-cannot-regenerate-response-public-conversation_ELITEA-2191.md`.

## See also

`no_non_admin_test_user_credential_exists.md` — the sibling gap: one identity,
always admin-equivalent, no LOWER-ROLE identity. That one sometimes has a
partial (admin-side) coverage path; this one (no SECOND PERSON at all) never
does when the case's whole premise is the other person's viewpoint.
