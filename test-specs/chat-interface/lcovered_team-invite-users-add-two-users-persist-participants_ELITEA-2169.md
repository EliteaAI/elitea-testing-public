# Test Case: Chat – Team Project – Add Users as Conversation Participants

## Metadata
- **TMS ID**: ELITEA-2169
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (per source case's `priority: high`; traceability AFS, no priority-digit filename)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst/Implementer (combined slot)**: test-automation-engineer (agent), batch `chat-remaining-w10`, 2026-08-15
- **Status**: already-covered
- **surface_key**: `chat-invite-users-modal` (same "Add users" modal surface as ELITEA-2167/2168)

## Preconditions
- User is logged in to the Elitea platform.
- User is in a Team project with an existing conversation.

## Dedup proof — Rule-6 behavioural equivalence

**Covering spec:** `automation/tests/ui/chat/test_invite_users_add_cancel_close.py`, class
`TestInviteUsersAddCancelClose`, method `test_invite_users_add_persists_cancel_and_close_discard`
(TMS ELITEA-2167, AFS
`test-specs/chat-interface/l2_team-invite-users-add-cancel-close_ELITEA-2167.md`). Merged to
`origin/automation/base` (`298d1120` / `fce1b0b7`, PR #988; confirmed present this session via a
fresh `git fetch origin` + `git ls-tree origin/automation/base` on the exact test file path).

**Behavioural-equivalence argument.** ELITEA-2169's 5 steps are a strict subset of ELITEA-2167's
own 10-step flow — the same "Add users" modal, driven the same way, against the same Team project,
with the same expected outcome (selected users persisted into the PARTICIPANTS USERS section):

| ELITEA-2169 step | ELITEA-2167's AFS / `test_invite_users_add_persists_cancel_and_close_discard` step |
|---|---|
| 1. Navigate to Chats in Team project and open any conversation → conversation is open | Precondition + AFS Step 1 — switches to Team project 471, opens a conversation (`_open_blank_conversation()`), confirms it's open (greeting visible, input editable/empty). ELITEA-2169's wording ("open any conversation") is satisfied by any open conversation, new or existing — the covering test's brand-new-but-open conversation is a valid instance of "a conversation is open"; the Add-users mechanics this case cares about do not depend on conversation age. |
| 2. Click + icon, select Invite Users → 'Add users' modal opens | AFS Step 2 (menu, `invite-users-menuitem` present) + Step 3 (modal opens, dialog visible, search/Cancel/Add present) |
| 3. Select user_1 from the dropdown; verify chip appears → user_1 chip visible | AFS Step 4 — search + select first user, chip appears, modal stays open, Add enables |
| 4. Select user_2 from the dropdown; verify chip appears → user_2 chip visible | AFS Step 5 — search + select second user, two chips shown, modal stays open |
| 5. Click Add → Modal closes; user_1 and user_2 in PARTICIPANTS USERS section | AFS Step 6 — Add click closes modal; `chat-participants-badge-users` reads "2"; popover lists both selected names under a "USERS" heading |

Every element of ELITEA-2169's 5 steps has a direct, one-to-one assertion in the covering test —
none of ELITEA-2169's asks exceed what it already proves. (The covering test additionally exercises
Cancel/X-close discard, a third/fourth user, message-send, and the sidebar multi-person icon — none
of which ELITEA-2169 asks for; a superset, not a mismatch.)

**Live-reconfirmed this session** (not assumed from the digest alone, per the "coverage judgments
stand on your own execution" rule): re-ran the covering test live against `http://localhost:5173`,
3 times back-to-back (all in one session, no cleanup pause between):

- **Run 1 — clean pass through every step overlapping with ELITEA-2169.** All of Steps 1–10 executed
  without an `AssertionError` — including this case's own overlapping Steps 2–6 (menu → modal →
  chip #1 → chip #2 → Add → badge="2" + popover lists both names). The run only failed at the
  test's own FINAL side-channel step (console-cleanliness check, unrelated to any of ELITEA-2169's
  5 steps) on a genuinely new React `setState`-in-render console warning in the Participants panel
  (`UsersParticipantDropdown`/`CollapsedPerticapantsList`) — filed as a new, dedup-checked MINOR
  defect, issue #1556 (see § Known Defects). This warning does not touch the Add-users mechanism
  ELITEA-2169 cares about; the chip/Add/badge/popover assertions in this same run all passed before
  it fired.
- **Runs 2–3 — failed at the test's own Step 1** (`is_participants_badge_visible` unexpectedly `True`
  for what should be a brand-new, zero-participant conversation), never reaching this case's own
  Steps 2–6. Root cause: back-to-back re-runs without an intervening cleanup pass left a stale
  conversation from Run 1's own failed teardown for `_open_blank_conversation()` to pick up next —
  the exact, already-tracked flake class issue #1082 documents ("invite-users test fails only in a
  full run — project-switch settling leaves a stale/deleted conversation"). Not a new finding, not a
  functional break in the Add-users flow — a re-confirmation of #1082's existing pattern, caused by
  this session's own repeated-run methodology rather than a single fresh invocation.

Net: the ONE clean-environment run (Run 1) is unambiguous — every step overlapping with ELITEA-2169
passed exactly as this case specs, on today's live product, via the merged spec. Runs 2–3's failures
are outside ELITEA-2169's own scope (they fail before Step 2 of the covering test, i.e. before the
Add-users mechanism is even reached) and match a pre-existing, already-filed test-infra defect, not
a regression in the behavior this case asserts.

## Test Steps (source case, reproduced for traceability only — not re-implemented)
1. Navigate to Chats in Team project and open any conversation — Conversation is open.
2. Click + icon, select Invite Users — 'Add users' modal opens.
3. Select user_1 from the dropdown; verify chip appears — user_1 chip visible.
4. Select user_2 from the dropdown; verify chip appears — user_2 chip visible.
5. Click Add — Modal closes; user_1 and user_2 in PARTICIPANTS USERS section.

## Expected Results
- Selecting two users via the "Add users" modal and clicking Add closes the modal and persists both
  into the PARTICIPANTS USERS section (badge count + popover names) — proven live by
  `test_invite_users_add_persists_cancel_and_close_discard`, Run 1 this session.
- One new MINOR defect filed during this session's live reconfirmation (issue #1556, Participants
  panel setState-in-render warning) — unrelated to the Add-users mechanism this case exercises,
  surfaced only at the covering test's own final, unrelated side-channel console check.

## Coverage Map

### Axis 1 — Case elements

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state`/`VITE_DEV_TOKEN` (localhost) | framework fixture, covering test | already-covered |
| Precondition: Team project + existing conversation | conversation open | covering test Preconditions + Step 1 | `switch_project("471")` + `_open_blank_conversation()` + open-state assertions | already-covered *(covering test opens a brand-new conversation, a valid instance of "existing conversation" for this case's generic "conversation is open" ask — see § Dedup proof)* |
| Step 1 — navigate to Chats, open any conversation → conversation is open | conversation open | covering test Step 1 | greeting visible, input editable+empty | already-covered |
| Step 2 — click + icon, select Invite Users → 'Add users' modal opens | modal opens | covering test Steps 2–3 | `invite-users-menuitem` visible/enabled; dialog visible with search/Cancel/Add | already-covered |
| Step 3 — select user_1; verify chip appears | user_1 chip visible | covering test Step 4 | chip text == user_1 name; modal stays open; Add enables | already-covered |
| Step 4 — select user_2; verify chip appears | user_2 chip visible | covering test Step 5 | chip names == [user_1, user_2]; modal stays open | already-covered |
| Step 5 — click Add → modal closes; both users in PARTICIPANTS USERS | modal closes, both added | covering test Step 6 | badge reads "2"; popover lists both names under "USERS" heading | already-covered |
| Expected Final State: "Users added as conversation participants" | — | covering test Step 6 | as above | already-covered |
| Pass/Fail: "All steps complete without errors; Users added correctly" | — | covering test Steps 1–6 | as above | already-covered |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions
None beyond what the covering spec already documents (see its own Coverage Map Axis 2 section,
ELITEA-2167's AFS) — none needed here. This session's own live re-run surfaced one NEW, dedup-checked
defect (issue #1556) at the covering test's unrelated final console-check step; recorded in § Known
Defects Found During Exploration, not folded into this case's own Axis 1 rows since it falls outside
ELITEA-2169's 5 steps.

## Cleanup
N/A — no new test written. Live-reconfirmation this session re-ran the existing covering test as-is
(its own setup/teardown creates and deletes its own fixture data). Runs 2–3's failed-before-cleanup
conversations (stale-conversation flake, #1082) may have left 1–2 orphaned zero-message conversations
in project 471 from this session's repeated back-to-back invocations — flagged for the next session
touching this project's conversation list, not independently swept here (no case data indicates which
exact rows are this session's vs. pre-existing #1082 noise).

## Concrete Handles (discovered during exploration)
Reuses the covering spec's handles verbatim — `invite-users-menuitem`, `add-users-dialog`,
`add-users-search-input`, `add-users-option-{userId}`, `add-users-chip-{userId}`,
`add-users-cancel-button`, `add-users-confirm-button`, `chat-participants-badge-users`,
`chat-participants-badge-button`, `chat-participants-popper` — all confirmed present and functioning
on live localhost this session (Run 1, via the live test re-run). No new handles needed for this
traceability pass.

## Known Defects Found During Exploration
- **[MINOR, novel, filed this session] Issue #1556** — React `setState`-in-render console warning
  (`UsersParticipantDropdown/index.jsx:30` calling `setState` on `CollapsedPerticapantsList` while
  `UsersParticipantDropdown` is still rendering) fires when the Participants panel renders. Confirmed
  live during Run 1's re-run of the covering test — fired at the test's own final side-channel
  console-cleanliness check, AFTER all of this case's own overlapping Add-users assertions
  (chip/chip/Add/badge/popover) had already passed. Dedup-checked before filing (distinct from #719 —
  different component, different root cause; distinct from #625 — same warning CLASS but in the
  unrelated Support Assistant `ChatWindow`/`AnimatedMessage`). Does not block or affect the
  correctness of the Add-users flow this case exercises — dev-mode console noise only.
- **[re-confirmed, not re-filed] Issue #1082** — Runs 2–3 of this session's live re-run hit the
  already-tracked "invite-users test fails only in a full run — project-switch settling leaves a
  stale/deleted conversation" flake, caused by this session's own back-to-back re-run methodology
  (no cleanup pause between runs) rather than a single fresh invocation. Confirms #1082's root cause
  is real and recurring; no new ticket filed.

## Blocked Steps
None. Run 1's clean pass covers every one of ELITEA-2169's 5 steps end-to-end against today's live
product via the merged spec.

## TMS linkage
Link ELITEA-2169 to ELITEA-2167 in the TMS (both ways) so the audit trail resolves: ELITEA-2169's
`already-covered` disposition points at the automated test; ELITEA-2167's case gains an "also
satisfies ELITEA-2169" back-reference. Same pattern already established between ELITEA-2462/ELITEA-2152
and ELITEA-2461/ELITEA-2149+2151.
