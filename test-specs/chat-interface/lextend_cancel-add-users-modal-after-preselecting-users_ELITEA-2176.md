# Test Case: Chat – Team Project – Cancel Add Users Modal After Pre-Selecting Users Does Not Add Anyone

## Metadata
- **TMS ID**: ELITEA-2176
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case frontmatter: `priority: medium` → `@pytest.mark.p2`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; project "Elitea Testing Team", `projectId=471`)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: test-automation-engineer (combined analyst+implementer)
- **Status**: extend-existing
- **Extension target**: `automation/tests/ui/chat/test_invite_users_add_cancel_close.py` (its own AFS: `test-specs/chat-interface/l2_team-invite-users-add-cancel-close_ELITEA-2167.md`) — merged `origin/automation/base` (`298d1120`, PR #988)

**Not already-covered — a genuinely new observable, live-confirmed this
session.** Two existing tests already prove "Cancel discards a pending
selection," but both do it with exactly ONE pre-selected chip: ELITEA-2167's
own Step 7 (this covering file) and ELITEA-2168's Step 6
(`test_team_users_mention_and_remove_participants.py`, merged
`6ef5ef7b`). This case's own data — select TWO users, THEN Cancel — is worth
its own proof: it is the only case in this digest exercising Cancel against a
multi-item pending selection, on an EXISTING conversation that already
carries a real, persisted participant baseline (the case's own precondition,
"Team project with an existing conversation," and its own step 1, "note
current participants") rather than a fresh, participant-less one — a
meaningfully different starting state than either sibling test uses.

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- User is in the Team project (`471`) with an EXISTING conversation that
  already has at least one persisted participant beyond the owner — this
  case's own test seeds that state itself (§ Test Data) rather than
  depending on ambient shared-project data, same rationale the covering
  file's own AFS already applies to its own setup.

## Test Data

### Fixed / reused from the covering file's module-level constants
- `USER_1_NAME = "Hrach Sargsyan"` (query `"sa"`) — case's own `user_1`.
- `USER_2_NAME = "Levon Dadayan"` (query `"ad"`) — case's own `user_2`.
- `USER_4_NAME = "Tatiana Bontsevich"` (query `"ta"`) — seed-only, establishes
  the "existing conversation with participants" precondition. Deliberately
  NOT `USER_3_NAME`, kept free for other same-surface cases per this digest's
  own convention of not colliding seed/case-subject users across sibling
  tests in the same session.

### generate-per-test (created by the test's own setup, cleaned up in its own teardown)
- One fresh conversation, seeded with `USER_4_NAME` as a persisted
  participant (Add users → Add → Send), giving PARTICIPANTS USERS a real
  baseline (badge `"2"`: owner + `USER_4_NAME`) before this case's own steps
  begin.

## Test Steps

1. Note current participants — badge `"2"` (owner + `USER_4_NAME`), popover
   lists `USER_4_NAME`.
2. Open Invite Users; search+select `user_1` and `user_2`.
   - **Verify**: two chips shown (`[USER_1_NAME, USER_2_NAME]`).
3. Click Cancel.
   - **Verify**: the modal closes.
4. Verify PARTICIPANTS USERS shows the same participants as before.
   - **Verify**: badge still reads `"2"` — unchanged from the noted baseline.
5. Verify `user_1` and `user_2` are NOT in PARTICIPANTS.
   - **Verify**: popover text excludes both; `USER_4_NAME` (the baseline
     participant) is still present.

## Expected Results
- A conversation with an existing, persisted participant shows that
  participant in PARTICIPANTS USERS at the start.
- Selecting two additional users via search produces two chips; the Add
  button becomes enabled.
- Clicking Cancel closes the modal and discards BOTH pending selections —
  neither is added, and the pre-existing participant baseline is completely
  unaffected (same count, same names).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: Team project, existing conversation with participants | — | Setup | seeded via Add users + Send | asserted |
| 1 Note current participants | Current participants noted | AFS step 1 | step 1: badge `"2"` + popover contains USER_4_NAME | asserted |
| 2 Open modal, select user_1/user_2; verify chips | Two chips shown | AFS step 2 | step 2: `get_add_users_chip_names()` == 2-item list | asserted |
| 3 Click Cancel | Modal closes without saving | AFS step 3 | step 3: dialog hidden | asserted |
| 4 Verify PARTICIPANTS USERS unchanged | No new users added | AFS step 4 | step 4: badge == noted baseline | asserted |
| 5 Verify user_1/user_2 NOT in PARTICIPANTS | user_1/user_2 not added | AFS step 5 | step 5: popover excludes both, baseline participant still present | asserted |
| Expected Final State: "No users added after cancelling the modal" | — | steps 4-5 | covered by the two rows above | asserted |
| Pass/Fail: "Cancel does not add any users" / "Users added despite cancelling" | — | all steps | step 5's exclusion assertion is the negative-control half | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` /
`out-of-scope`. All rows `asserted`.

### Axis 2 — Analyst additions
- Side-channel console-error check across the whole flow — *added: standard
  discipline, same idiom as every sibling test in this file.*
- Baseline participant (`USER_4_NAME`) explicitly re-asserted present at step
  5, not just USER_1/USER_2 absent — *added: proves Cancel didn't
  side-effect the EXISTING participant list (e.g. accidentally clear it),
  not only that it didn't grow it — a stronger check than the case's own
  literal step 5 asks for.*

## Fidelity Declaration
No substitutions. The "existing conversation with participants" precondition
is reached via the real UI (Add users modal → Add → Send, the same
mechanism the covering file's own merged test already uses) — not seeded via
API injection or `page.evaluate()`. Every observable (chips, badge, popover
text) is read from the live DOM/React state the real modal/panel renders.

## Cleanup
1. Delete the seeded conversation via the same context-menu → Delete →
   confirm flow the covering file's own existing test uses
   (`open_conversation_context_menu()` / `click_conversation_menu_item()` /
   `confirm_delete_conversation()`), in a `try/finally`.
2. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

Locator policy on this project is testid-only (`.agents/testing.md` § Locator policy).

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Add users modal container | `add-users-dialog` | on-`main` ✓, on-`automation/testids` ✓ | Pre-existing (ELITEA-2167), reused verbatim. |
| Search input | `add-users-search-input` | on-`main` ✓, on-`automation/testids` ✓ | Pre-existing, reused verbatim. |
| Per-user selected chip | `add-users-chip-{userId}` (dynamic, prefix `ADD_USERS_CHIP_PREFIX`) | on-`main` ✓, on-`automation/testids` ✓ | Pre-existing (ELITEA-2167), reused verbatim. |
| Cancel button | `add-users-cancel-button` | on-`main` ✓, on-`automation/testids` ✓ | Pre-existing, reused verbatim via `click_add_users_cancel()`. |
| Participants badge / popover | `chat-participants-badge-button` / `chat-participants-popper` (section="users") | on-`automation/testids` ✓ only (documented gap, covering file's own docstring) | Pre-existing, reused verbatim. |

Zero new testids needed for this case.

## Network Behavior
- Setup only: `POST .../conversations/prompt_lib/471` → `201`, `POST
  .../participants/prompt_lib/471/{id}` → `200` (same mechanism the covering
  file's merged test already documents — participants persist only at first
  Send).
- Case's own steps 2-5: **zero** new requests — selection is client-side
  filtering, and Cancel is a pure client-side discard (no `PUT`/`POST` fires
  on Cancel-click, same mechanism the covering file's Step 7 already proves
  for a single pre-selected user).

## Known Defects Found During Exploration
None new. The already-filed, isolated `#719` console warning (covering
file's own known-defect filter) fires on option selection here too and is
filtered by the SAME filter already defined in this file — no new filter
needed.

## Blocked Steps
None. All 5 case steps are executable via existing, already-verified
page-object infrastructure.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- Landed as a new test class
  (`TestCancelAddUsersModalAfterPreselectingUsers`) in the covering file — no
  new page-object methods needed. Reuse verbatim: `chat.switch_project()`,
  `chat.open_add_users_modal()`, `chat.search_and_select_add_user_verified()`,
  `chat.wait_for_add_users_chip()`, `chat.get_add_users_chip_names()`,
  `chat.click_add_users_cancel()`, `chat.is_participants_badge_visible()`,
  `chat.get_participants_badge_count()`, `chat.open_participants_popover()` /
  `dismiss_participants_popover()`, `chat.send_message()`,
  `chat.wait_for_participants_badge_count()`.
- Uses the same `_open_genuinely_blank_conversation()` additive helper
  ELITEA-2175's own AFS documents in full (this file's shared setup step) —
  see that AFS's Automation Hints for the infrastructure gotcha it fixes and
  the related, NOT-fixed-here finding about the original merged test's own
  current flakiness against this exact race.
