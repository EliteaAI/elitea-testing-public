# Test Case: Chat – Team Project – Remove Pre-Selected User from Add Users Modal by Clicking X on Chip

## Metadata
- **TMS ID**: ELITEA-2175
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case frontmatter: `priority: medium` → `@pytest.mark.p2`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; project "Elitea Testing Team", `projectId=471` — `TEAM_PROJECT_ID` in the covering file)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: test-automation-engineer (combined analyst+implementer)
- **Status**: extend-existing
- **Extension target**: `automation/tests/ui/chat/test_invite_users_add_cancel_close.py` (its own AFS: `test-specs/chat-interface/l2_team-invite-users-add-cancel-close_ELITEA-2167.md`) — merged `origin/automation/base` (`298d1120`, PR #988)

**Not already-covered — a genuinely new observable, live-confirmed this
session.** `ChatPage.remove_add_users_chip()` already exists with one caller:
ELITEA-2168's own test (`test_team_users_mention_and_remove_participants.py`,
merged `origin/automation/base` `6ef5ef7b`) selects 4 users then removes the
**LAST** chip (`user_4`) before confirming. This case's own data — select 3
users, click X on the **MIDDLE** chip (`user_2`) — is not the same
observable: it is the only case in this digest that proves removal is keyed
by the clicked chip's own identity rather than array position, and that the
two SURROUNDING selections (not just "the remaining ones" generically)
survive a middle-item removal in the correct order. Confirmed live this
session (see § Test Steps) rather than assumed from the LAST-position
precedent — `remove_add_users_chip()`'s own implementation resolves the
target chip via `ADD_USERS_CHIP_PREFIX` filtered by name (position-agnostic
by construction), but the digest's own standing rule is that coverage
judgments stand on execution, not source-reading alone.

Routed `extend-existing` against the ELITEA-2167 covering file (not the
ELITEA-2168 file that first introduced `remove_add_users_chip()`) because
ELITEA-2167's file is thematically the Add/Cancel/Close-mechanics home for
this modal, is a smaller/faster-running file to extend, and per the
merged-target rule either an already-base-merged file is a valid
`extend-existing` target — no functional difference in which of the two
qualifies.

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- User is in the Team project (`471`, "Elitea Testing Team") — "Invite Users"
  is offered only there (`PlusChatButton.jsx`'s `!isPrivateProject` guard,
  already documented by the covering file).

## Test Data

### Fixed / reused from the covering file's module-level constants
- `USER_1_NAME = "Hrach Sargsyan"` (query `"sa"`)
- `USER_2_NAME = "Levon Dadayan"` (query `"ad"`) — the case's own `user_2`,
  the one removed via chip X.
- `USER_3_NAME = "Mariam Hakobyan"` (query `"ma"`)
- Same AFS-level substitution already established by ELITEA-2167/2168's own
  AFS files: the case's own generic `user_1/user_2/user_3` placeholders map
  to these three real org users in this environment.

## Test Steps

1. Switch to the Team project; click + Chat; open Invite Users; search+select
   `user_1`, `user_2`, `user_3` in order.
   - **Verify**: three chips shown, in selection order
     (`[USER_1_NAME, USER_2_NAME, USER_3_NAME]`).
2. Click the X (delete icon) on `user_2`'s own chip.
   - **Verify**: `user_2`'s chip is gone; `user_1` and `user_3` remain, in
     order (`[USER_1_NAME, USER_3_NAME]`); the Add button stays enabled (2
     selections remain > 0).
3. Click Add.
   - **Verify**: the modal closes; `user_1` and `user_3` are the queued
     PARTICIPANTS USERS (badge reads `"2"`, popover lists both names);
     `user_2` is NOT listed.

## Expected Results
- Selecting three users via search produces three chips, in the order
  selected.
- Clicking a specific chip's own X (delete) icon removes ONLY that
  selection — the other two chips remain, in their original relative order,
  and the Add button stays enabled (disabled only at zero selections).
- Confirming via Add closes the modal and queues exactly the two SURVIVING
  selections as PARTICIPANTS USERS — the removed user is never added, no
  network call for participant persistence fires yet (same queued-until-Send
  mechanism the covering file's own AFS already documents).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in, Team project | — | Setup | `auth_state` fixture + `switch_project()` | asserted |
| 1 Open modal, select user_1/2/3; verify 3 chips | Three chips shown | AFS step 1 | step 1: `get_add_users_chip_names()` == 3-item list | asserted |
| 2 Click X on user_2's chip | user_2 removed; user_1/user_3 remain | AFS step 2 | step 2: `get_add_users_chip_names()` == 2-item list, Add still enabled | asserted |
| 3 Click Add | Modal closes; user_1/user_3 in PARTICIPANTS; user_2 NOT listed | AFS step 3 | step 3: badge `"2"` + popover text contains user_1/user_3, excludes user_2 | asserted |
| Expected Final State: "user_2 not added after chip removal; user_1 and user_3 added" | — | step 3 | covered by the row above | asserted |
| Pass/Fail: "Chip removal works; only remaining users added" / "All users added despite chip removal" | — | all steps | step 3's exclusion assertion is the negative-control half | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` /
`out-of-scope`. All rows `asserted`.

### Axis 2 — Analyst additions
- Side-channel console-error check across the whole flow — *added: standard
  discipline, same idiom as every sibling test in this file.*
- (nothing else added beyond the case — remaining steps map 1:1 onto the
  case's own literal steps.)

## Fidelity Declaration
No substitutions. Every observable (chips, Add-enabled state, participants
badge/popover) is read from the live DOM/React state the real modal renders;
no `page.route`/`page.evaluate`/mocked client is used anywhere in this test.

## Cleanup
No conversation is ever created server-side by this test — participants are
only persisted at the first message Send (documented mechanism, covering
file's own AFS), and this case's own scope ends at the post-Add queued
state, before any Send. Nothing to clean up.

## Concrete Handles (discovered during exploration)

Locator policy on this project is testid-only (`.agents/testing.md` § Locator policy).

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Add users modal container | `add-users-dialog` | on-`main` ✓, on-`automation/testids` ✓ | Pre-existing (ELITEA-2167), reused verbatim. |
| Search input | `add-users-search-input` | on-`main` ✓, on-`automation/testids` ✓ | Pre-existing, reused verbatim. |
| Per-user selected chip | `add-users-chip-{userId}` (dynamic, prefix `ADD_USERS_CHIP_PREFIX`) | on-`main` ✓, on-`automation/testids` ✓ | Pre-existing (ELITEA-2167), reused verbatim via `get_add_users_chip_names()`. |
| Chip's own delete (X) icon | `add-users-remove-chip-{userId}` (dynamic, prefix `ADD_USERS_CHIP_REMOVE_PREFIX`) | on-`main` ✓, on-`automation/testids` ✓ | Pre-existing (ELITEA-2168), used by `remove_add_users_chip()` — this case is its SECOND caller, first to target a non-last chip. Verified via fresh `git fetch origin` + `git grep` against `EliteaAI/EliteaUI` both refs this session. |
| Add (confirm) button | `add-users-confirm-button` | on-`main` ✓, on-`automation/testids` ✓ | Pre-existing, reused verbatim. |
| Participants badge / popover | `chat-participants-badge-button` / `chat-participants-popper` (section="users") | on-`automation/testids` ✓ only (documented gap, covering file's own docstring — `UsersParticipantDropdown/index.jsx`) | Pre-existing, reused verbatim. |

Zero new testids needed for this case.

## Network Behavior
- No network request fires on chip selection or chip removal (client-side
  filter/state only — same mechanism the covering file already documents for
  selection).
- No participants-persist request fires on Add either — queuing is entirely
  client-side until the first message Send (out of this case's own scope).

## Known Defects Found During Exploration
None new. The already-filed, isolated `#719` (MUI `sx`-on-raw-`svg` console
warning on option selection, covering file's own known-defect filter) fires
on this flow too and is filtered by the SAME console-error filter the
covering file already defines — no new filter needed.

## Blocked Steps
None. All 3 case steps are executable via existing, already-verified
page-object infrastructure (`open_add_users_modal()`,
`search_and_select_add_user_verified()`, `remove_add_users_chip()`,
`click_add_users_confirm()`-equivalent inline sequence).

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- Landed as a new test class (`TestRemovePreselectedUserViaChipX`) in the
  covering file — no new page-object methods needed. Reuse verbatim:
  `chat.switch_project()`, `chat.open_add_users_modal()`,
  `chat.search_and_select_add_user_verified()`, `chat.wait_for_add_users_chip()`,
  `chat.get_add_users_chip_names()`, `chat.remove_add_users_chip()`,
  `chat.is_add_users_confirm_enabled()`, `chat.is_add_users_results_open()` +
  `chat.dismiss_add_users_dropdown()` (the blind-Escape-after-chip-removal
  gotcha ELITEA-2168's test already documents), `chat.wait_for_participants_badge_count()`,
  `chat.open_participants_popover()` / `dismiss_participants_popover()`.
- **Infrastructure gotcha found + fixed this implementation**: the covering
  file's own `_open_blank_conversation()` helper (single check: the
  new-conversation greeting is visible) is not sufficient on this shared dev
  backend — `ChatPage.navigate_to_chat()`'s own docstring already documents
  that "the SPA may redirect to the last-viewed conversation stored in the
  browser session," and this redirect can fire as a DELAYED effect, after
  the greeting and a momentary 0 message count are both already observed,
  silently snapping the view back to a pre-existing conversation with real
  history. Reproduced 4/4 times against a bare `_open_blank_conversation()`
  reuse; a parallel manual Playwright MCP session confirmed the identical UI
  mechanism works reliably when driven slowly with pauses, isolating this as
  a race rather than a product defect. Added an ADDITIVE sibling helper,
  `_open_genuinely_blank_conversation()` (does not modify
  `_open_blank_conversation()` or its existing ELITEA-2167 caller — Hard Rule
  3), which adds a settle window + re-check (message count AND URL both
  re-verified blank after a brief wait) before proceeding. Used by both new
  test classes in this file.
- **Related finding, NOT fixed here (out of scope — shared-caller function,
  additive-only)**: the ORIGINAL, already-merged
  `TestInviteUsersAddCancelClose` test (using the weaker
  `_open_blank_conversation()`) now fails consistently (reproduced 2/2) in
  the CURRENT live environment on this exact race — an assertion at its own
  Step 1 (`assert not chat.is_participants_badge_visible(...)`) fails because
  it lands on a restored conversation with participants. This is a
  pre-existing-test regression unrelated to this case's own code; flagged to
  the orchestrator as a finding for a follow-up fix-only dispatch (apply the
  same settle+recheck guard to `_open_blank_conversation()` itself, which
  would then require the shared-file regression protocol: enumerate/re-run
  every caller).
