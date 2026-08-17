# Test Case: Chat – Team Project – Cancel Remove User Dialog Keeps User in Participants List

## Metadata
- **TMS ID**: ELITEA-2171
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (per source case's `priority: medium`; traceability AFS, no priority-digit filename)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend;
  Team project "Elitea Testing Team", `projectId=471`)
- **User set**: `${TEST_USER}` — localhost: no login needed, `VITE_DEV_TOKEN` auto-auths (dev-token user
  renders as "Test Bot"/"TB")
- **Analyst**: qa-engineer (agent), batch `chat-remaining-w10`, cluster dispatch with ELITEA-2172, 2026-08-15
- **Status**: **already-covered**
- **surface_key**: `chat-users-participant-dropdown` (shared with ELITEA-2172 — same "Users" dropdown
  remove-control surface, different behavior asked)

## Preconditions
- User is logged in to the Elitea platform.
- A conversation with at least 2 participants exists in a Team project.

## Dedup proof — Rule-6 behavioural equivalence

**Covering spec:** `automation/tests/ui/chat/test_team_users_mention_and_remove_participants.py`, class
`TestTeamUsersMentionAndRemoveParticipants`, method `test_team_users_mention_and_remove_participants`
(TMS ELITEA-2168, AFS
`test-specs/chat-interface/l2_team-users-mention-and-remove-participants_ELITEA-2168.md`), **Step 10**
(source lines 560–576). Merged to `origin/automation/base` (confirmed present this session via a fresh
`git fetch origin` and `git show origin/automation/base:automation/tests/ui/chat/test_team_users_mention_and_remove_participants.py`
on the exact path).

**Behavioural-equivalence argument.** ELITEA-2171's 3 steps are, verbatim, ELITEA-2168's own Step 10:

| ELITEA-2171 step | ELITEA-2168's covering test, Step 10 (lines 560–576) |
|---|---|
| 1. Open the conversation, click avatar group, hover over user_1, click trash bin → 'Remove user?' modal appears | `chat.open_remove_user_dialog(participant_id_by_name[USER_1_NAME], ...)` — opens the Users popover, hovers user_1's row (Hrach Sargsyan — same "user_1" mapping ELITEA-2171's own Test Data table uses), clicks its delete icon, returns the confirmation dialog. Dialog text confirmed live this session (see below): `"Remove user?Are you sure to remove the {name} user from chat?CancelRemove"` — the exact 'Remove user?' modal ELITEA-2171 Step 1 expects. |
| 2. Click Cancel → Modal closes without removing user | `Dialog.click_button(dialog, "Cancel")` + `Dialog.wait_for_hidden(page, ...)` — clicks Cancel, asserts the dialog closes. |
| 3. Verify user_1 still listed in USERS dropdown and PARTICIPANTS → user_1 still present | `assert badge_count == "5"` (unchanged PARTICIPANTS count) + `assert USER_1_NAME in popper_text` (still listed in the USERS dropdown popover) — both the PARTICIPANTS badge and the USERS dropdown listing ELITEA-2171 Step 3 asks for. |

Every element of ELITEA-2171's 3 steps has a direct, one-to-one assertion in the covering test's Step 10 —
none of ELITEA-2171's asks exceed what it already proves. (The covering test's other 11 steps exercise
add/deselect/mention/remove/@everyone flows on the same conversation — a superset, not a mismatch; Step 10
specifically is the Cancel-preserves-user flow.)

**Live-reconfirmed this session — direct manual repro of the EXACT 3-step flow, via Playwright MCP**
(localhost:5173, Team project 471, conversation `/chat/420` "Review attached documents"):

1. **Step 1** — opened the Users participants dropdown (badge click → popover), hovered a non-owner
   participant row (Daniyar Chambylov, added for this check), clicked its delete icon — the
   "Remove user?" dialog appeared with the EXACT text ELITEA-2168's test also asserts: `"Remove user?" /
   "Are you sure to remove the Daniyar Chambylov user from chat?" / Cancel / Remove` (confirmed via
   accessibility snapshot).
2. **Step 2** — clicked **Cancel** (`delete-confirm-cancel-button`) — the dialog closed (no dialog node
   left in the next accessibility snapshot).
3. **Step 3** — confirmed the PARTICIPANTS badge stayed unchanged (`"3"` before and after Cancel) AND
   the USERS dropdown popover still listed "Daniyar Chambylov" — both the badge-count and dropdown-listing
   halves of ELITEA-2171's own Step 3 ask.

This is a direct, live, positive confirmation of ELITEA-2171's exact 3 steps against today's product —
not an inference from the covering test's source alone. (A pytest re-run of the covering test was also
attempted twice this session and hit the already-tracked issue #1082 stale-conversation flake at its own
Setup stage before reaching Step 10 both times — coincidentally, one of those failed pytest runs appears
to have landed on and modified THIS SAME shared conversation, `/chat/420`, mid-session, which is what
supplied the extra participants used for the manual Cancel repro above; see the memory note filed this
session on running pytest and manual Playwright-MCP exploration concurrently against the same dev server.
Not pursued further as a pytest artifact — the manual repro above is conclusive on its own and is the
adopted evidence for this AFS.) Conversation `/chat/420` was restored to its original state (badge "1",
only the owner) before ending the session.

## Test Steps (source case, reproduced for traceability only — not re-implemented)
1. Open the conversation, click avatar group, hover over user_1, click trash bin — 'Remove user?' modal appears.
2. Click Cancel — Modal closes without removing user.
3. Verify user_1 still listed in USERS dropdown and PARTICIPANTS — user_1 still present.

## Expected Results
- Clicking Cancel in the "Remove user?" dialog closes it without removing the participant — both the
  PARTICIPANTS badge count and the USERS dropdown popover listing stay unchanged — proven by
  `test_team_users_mention_and_remove_participants`'s Step 10, and independently re-confirmed live this
  session via manual dialog-mechanism repro.

## Coverage Map

### Axis 1 — Case elements

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state`/`VITE_DEV_TOKEN` (localhost) | framework fixture | already-covered |
| Precondition: conversation with ≥2 participants in a Team project | — | covering test's Setup (seeds owner + 2 users) | `wait_for_participants_badge_count("3", ...)` | already-covered |
| 1. Open conversation, click avatar group, hover user_1, click trash bin → 'Remove user?' modal | modal appears | covering test Step 10, `open_remove_user_dialog()` | `Dialog.wait_for()` resolves; dialog text confirmed live this session via manual repro | already-covered |
| 2. Click Cancel → modal closes, not removed | modal closes | covering test Step 10 | `Dialog.click_button(dialog, "Cancel")` + `Dialog.wait_for_hidden()` | already-covered |
| 3. Verify user_1 still in USERS dropdown and PARTICIPANTS | still present | covering test Step 10 | `badge_count == "5"` (unchanged) + `USER_1_NAME in popper_text` | already-covered |
| Expected Final State: "User not removed after cancelling" | — | covering test Step 10 | as above | already-covered |
| Pass/Fail: "Cancel preserves user in list" | — | covering test Step 10 | as above | already-covered |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions
None beyond what the covering spec (ELITEA-2168's AFS) already documents — its own Axis 2 covers the
residual-hover gotcha this exact interaction needs (`page.mouse.move(0, 0)` reset before the next row's
hover-reveal). This session's manual live repro used a fresh popover open (no prior row interaction), so
the residual-hover gotcha did not need to be exercised to confirm the dialog mechanism.

## Cleanup
N/A — no new test written. This session's manual Playwright-MCP repro touched a shared, pre-existing
conversation (`/chat/420`, "Review attached documents", used by ELITEA-2091's test artifacts) to
exercise the dropdown/dialog live: added and removed Hrach Sargsyan (badge mechanism check), then
(after a concurrent pytest run appears to have added Daniyar Chambylov + Ihar Bylitski to this same
conversation mid-session — see § Dedup proof note) used Daniyar Chambylov for the Cancel-path repro
and removed both stray participants afterward. Badge confirmed back to "1" (its original state) before
ending the session. No orphaned conversations or participants left by this AFS's own exploration.

## Concrete Handles (discovered during exploration)
Reuses the covering spec's handles verbatim — `chat-participants-badge-button`,
`chat-participant-row-user_{userId}_` (dynamic, trailing segment empty for "user" participants),
`chat-participant-remove-button` (scoped inside the row), the shared `Modal.DeleteEntityModal`/`Dialog`
confirmation component (`Cancel`/`Remove` buttons). All confirmed present and functioning on live
localhost this session — provenance re-verified fresh (`git fetch origin` this session):

| Testid | main | automation/testids |
|---|---|---|
| `chat-participants-badge-button` | ✅ | ✅ |
| `chat-participant-row-{unique_id}` (dynamic) | ✅ | ✅ |
| `chat-participant-remove-button` | ✅ | ✅ |

No new handles needed for this traceability pass.

## Known Defects Found During Exploration
None novel this session. The already-tracked issue #1082 (stale-conversation-on-create flake) was
re-hit once during the live pytest re-run (Run 1, at the test's own Setup stage) — not re-filed, matches
the existing, already-documented pattern.

## Blocked Steps
None. The manual live repro plus the covering test's existing, reviewed Step 10 source together confirm
every element of ELITEA-2171's 3 steps against today's live product.

## TMS linkage
Link ELITEA-2171 to ELITEA-2168 in the TMS (both ways) so the audit trail resolves: ELITEA-2171's
`already-covered` disposition points at the automated test; ELITEA-2168's case gains an "also satisfies
ELITEA-2171" back-reference. Same pattern already established between ELITEA-2169/ELITEA-2167.
