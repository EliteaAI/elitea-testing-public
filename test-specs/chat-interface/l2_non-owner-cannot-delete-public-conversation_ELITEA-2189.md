# Test Case: Chat – Team Project – Non-Owner User Cannot Delete Public Conversation

## Metadata
- **TMS ID**: ELITEA-2189
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; Team project "Elitea Testing Team", `projectId=471`)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login (dev-token identity renders as "Test Bot"/"TB", confirmed live as `author_id: 659`)
- **Analyst**: qa-engineer (agent)
- **Status**: **blocked** — the case's own precondition ("non-owner user … public conversation owned by ANOTHER user") requires two distinct authenticated identities. Only one exists in this project's test-data (`${TEST_USER}`, the sole credential in `.env.test`); localhost's `auth_state` is hardwired to a single static `VITE_DEV_TOKEN` identity. Confirmed live via `GET /api/v2/elitea_core/folder/prompt_lib/471?grouped=true`: every conversation currently reachable by this account has `author_id: 659` (the same identity) — there is no second-owner conversation to view as a non-owner. See § Blocked Steps for the full investigation and the filed question.

## Preconditions
- User is logged in to the Elitea platform.
- **UNSATISFIABLE with current test data**: a second, distinct user identity that is a member of the same Team project and owns a public conversation. See § Blocked Steps.

## Test Data

| Field | Value |
|-------|-------|
| (none required by the case) | — |

## Test Steps

1. Log in as a non-owner user in a Team project.
   - **Verify**: logged in as a distinct, non-owner identity. **BLOCKED — no second credential exists** (see § Blocked Steps).
2. Navigate to Chats and find a public conversation owned by another user.
   - **Verify**: a public conversation authored by a different `author_id` is visible in the sidebar. **BLOCKED** — confirmed live that, under the single available identity, every conversation in project 471 has `author_id: 659` (this same account); there is no other-owned conversation to find.
3. Hover over it and click the three-dot icon.
   - Not reached — depends on step 2.
4. Verify Delete option is disabled or absent.
   - Not reached — depends on steps 1–3.
5. Verify only limited options shown (e.g. Playback, Pin on top).
   - Not reached — depends on steps 1–3.

## Expected Results
- Non-owner cannot delete a public conversation owned by another user.
- Not verified — precondition unsatisfiable in current environment/test-data.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Log in as a non-owner user | Logged in as non-owner | step 1 | — | blocked *(no second credential)* |
| 2 Find a public conversation owned by another user | Public conversation found | step 2 | — | blocked *(no second-owner conversation exists in current test data — confirmed live via API)* |
| 3 Hover + click three-dot icon | Context menu appears with limited options | step 3 | — | blocked *(depends on 1–2)* |
| 4 Verify Delete disabled/absent | Delete disabled/absent | step 4 | — | blocked *(depends on 1–3)* |
| 5 Verify only limited options shown | Limited menu shown | step 5 | — | blocked *(depends on 1–3)* |

### Axis 2 — Analyst additions
- None — no step was reachable to add assertions to.

## Cleanup
None performed — no test data was created (blocked before any action).

## Concrete Handles (discovered during exploration)

Per `.agents/testing.md` § Locator policy (testid-only, no fallback ladder). These
are the OWNER-side baseline handles already established in this suite (e.g.
ELITEA-2114/2188) — reusable once a second identity is provisioned; NOT yet
confirmed from a non-owner's perspective, since that view could not be reached.

| Element | Testid / Handle | State |
|---|---|---|
| Conversation sidebar item | `[data-testid="chat-conversation-item-{id}"]` (`CONVERSATION_ITEM` template, existing) | `data-active`, `data-pinned` |
| Context-menu (three-dot) button | `[data-testid="conversation-menu-menu-button"]` scoped inside `CONVERSATION_ITEM` (existing, `get_conversation_menu_button()`) | — |
| Context menu items (owner's full set) | `CONVERSATION_MENU_ITEM_KEYS = ("rename", "move-to", "playback", "make-public", "share", "pin", "delete")` — existing, `chat_page.py:1009` | — |
| Delete-confirmation dialog | `delete-confirm-dialog` / `delete-confirm-title` / `delete-confirm-message` / `delete-confirm-cancel-button` / `delete-confirm-button` (existing `LocatorDescriptor`s, `chat_page.py:1100-1126`) | — |

**Gap for the implementer, once unblocked**: it is not yet known whether the
non-owner's context menu is a genuinely SHORTER item set (a different render
path / fewer `CONVERSATION_MENU_ITEM_KEYS` entries) or the SAME item set with
`delete` rendered disabled (`aria-disabled`/`disabled` attribute) — the case
text says "disabled or absent" without distinguishing. Whichever shape the
live product uses once reachable, assert it directly (menu-item absence via
`to_have_count(0)`, or presence + `to_be_disabled()`) — do not assume.

## Network Behavior
- Not observed — no non-owner session was reachable.
- For reference (owner-side, existing precedent): `DELETE
  .../conversation/prompt_lib/471/{id}` is the delete endpoint chat's own
  `delete_conversation_ui()`/`confirm_delete_conversation()` methods drive
  (ELITEA-2114). A non-owner's attempt against this endpoint (whether blocked
  client-side via a hidden/disabled menu item, or server-side via a `403`)
  is exactly the fact this case needs to observe and currently cannot.

## Known Defects Found During Exploration
None found — no product behavior was exercised (blocked before any action
under test).

## Blocked Steps

**All case steps are blocked on one shared precondition: no second real-user
identity exists to act as the "non-owner".**

Investigation performed this session (not merely assumed):
1. `.agents/profile.md` § Roles & sample users and `.env.test` both checked —
   the only UI/Keycloak credential is `${TEST_USER}` (`TEST_USER_EMAIL`/
   `TEST_USER_PASSWORD`). No second credential of any kind exists in
   `.env.test` (checked every key, e.g. no `SECOND_TEST_USER_*`,
   `VIEWER_TEST_USER_*`, etc.).
2. `../EliteaUI/.env`'s `VITE_DEV_TOKEN` is a single, static token — grepped
   `../EliteaUI/src` for its usages (`root.jsx`, `upload.js`,
   `useArtifactContentFetch.hooks.js`, `SupportAssistant.jsx`): always the
   SAME fixed identity, never user-selectable. `auth_state`
   (`automation/fixtures/session_fixtures.py`) skips login entirely on
   localhost via this token — there is no code path to authenticate as a
   different identity locally.
3. Live-queried `GET /api/v2/elitea_core/folder/prompt_lib/471?sort_by=updated_at&sort_order=desc&grouped=true`
   against the Team project "Elitea Testing Team" (471): all 3 conversations
   returned have `"author_id": 659` (this account) and `"is_private": true` —
   no other-owned conversation, public or private, is currently reachable.
4. The "Invite Users" flow (ELITEA-2167 precedent) adds named users ("Hrach
   Sargsyan", "Levon Dadayan", …) as **participants** of a conversation this
   same account still owns — it does not grant login credentials for them;
   they come back from a user-search endpoint with no corresponding
   password/token available to this suite.
5. Considered and rejected as workarounds (all forbidden substitutions per
   `.agents/testing.md` § Fidelity policy — "bypassed subject",
   "wrong-interface precondition", "injected app state" — none of which this
   case's text asks for): reusing `auth_state` and hand-editing `author_id`
   client-side; calling the delete endpoint directly with `${TEST_USER}`'s
   own token against `${TEST_USER}`'s own conversation (proves nothing about
   a *different* user); injecting a mock `author_id` via `page.evaluate()`.

**Filed**: [Question #1563](https://github.com/EliteaAI/elitea-testing-public/issues/1563)
— "No second-user credential — blocks non-owner/ownership cases (ELITEA-2189,
ELITEA-2190, ELITEA-2191)". Covers all three cases in this cluster since they
share the identical root cause. Engineer: do not attempt to unblock via a
substitution — this is a test-data/environment provisioning decision routed
to a human (per `.agents/role-overrides.md` § Analyst slot: "cost/determinism
arguments belong in the declaration, not in the verdict" — there is no
declaration here because there is no honest way to produce this observable at
all, not merely an inconvenient one).

## Automation Hints
- Framework: Playwright/pytest, testid-only locators (`.agents/testing.md` §
  Locator policy).
- Page object: `automation/pages/chat_page.py` already has every owner-side
  handle this case would need (context menu, delete-confirm dialog) — see §
  Concrete Handles. No new page-object work is needed until the credential
  gap is resolved.
- Once a second identity is provisioned (issue #1563), re-run this analysis:
  log in as the second identity, have `${TEST_USER}` create + make public a
  conversation in project 471, switch session to the second identity, and
  execute steps 2–5 live.
