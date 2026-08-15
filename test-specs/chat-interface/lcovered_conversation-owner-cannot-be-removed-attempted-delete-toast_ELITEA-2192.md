# Test Case: Chat – Team Project – Conversation Owner Cannot Be Removed from Participants

## Metadata
- **TMS ID**: ELITEA-2192
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (per source case's `priority: high`; traceability AFS, no priority-digit filename)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend;
  Team project "Elitea Testing Team", `projectId=471`)
- **User set**: `${TEST_USER}` — localhost: no login needed, `VITE_DEV_TOKEN` auto-auths (dev-token user
  renders as "Test Bot"/"TB")
- **Analyst**: qa-engineer (agent), batch `chat-remaining-w11`, cluster dispatch with ELITEA-2193/2194, 2026-08-15
- **Status**: **already-covered**
- **surface_key**: `chat-users-participant-dropdown` (shared with ELITEA-2171/2172/2193/2194 — same "Users"
  dropdown remove-control surface)

## Preconditions
- User is logged in to the Elitea platform.
- A public (Team project) conversation with multiple participants exists (owner + ≥1 non-owner).

## Dedup proof — Rule-6 behavioural equivalence

**Covering spec:** `automation/tests/ui/chat/test_owner_has_no_remove_control_in_users_dropdown.py`, class
`TestOwnerHasNoRemoveControlInUsersDropdown`, method
`test_owner_has_no_remove_control_in_users_dropdown` (TMS ELITEA-2172, AFS
`test-specs/chat-interface/l2_conversation-owner-has-no-remove-control-in-users-dropdown_ELITEA-2172.md`).
Merged to `origin/automation/base` (confirmed present this session via a fresh `git fetch origin` and
`git log origin/automation/base --oneline -- automation/tests/ui/chat/test_owner_has_no_remove_control_in_users_dropdown.py`
→ commit `84651741`, PR #1561, "chat-remaining wave-10").

**Behavioural-equivalence argument.** ELITEA-2192's 5 steps map directly onto the covering test:

| ELITEA-2192 step | Covering test |
|---|---|
| 1. Open public conversation, PARTICIPANTS panel visible | Setup — seeds a Team-project conversation with owner + 1 non-owner, `wait_for_participants_badge_count("2", section="users")` |
| 2. Click avatar group → USERS dropdown shows all participants | Step 1 — `open_participants_popover(section="users")`, asserts non-owner name present in popper text |
| 3. Hover owner's row → no trash bin icon visible | Steps 3-4 — resolves owner via `conv_data.get("author_id")`, hovers the owner's row (`hover_participant_user_row`), asserts `not_to_be_visible()` on the scoped `chat-participant-remove-button` |
| 5. Verify owner remains in dropdown | Same popover instance throughout Steps 3-5 — owner row never disappears (there is no removal path to exercise it) |
| (positive control, not a separate case step) | Step 5 — hovers the non-owner row in the SAME dropdown instance, asserts the delete icon DOES reveal — rules out a stale-popover/timing artifact |

Every element of ELITEA-2192's own steps 1, 2, 3, 5 has a direct, one-to-one assertion in the covering
test. **Step 4 ("Attempt to trigger a delete action on the owner row → Red error toast: 'Cannot delete
author of the conversation'") is addressed below — it does not add uncovered ground, it is UNREACHABLE
via any real UI interaction, per this session's own live investigation.**

**Live-reconfirmed this session** (Playwright MCP, localhost:5173, Team project 471, conversation
`/chat/566` "HI Chat" — owner "Test Bot" + non-owner "Hrach Sargsyan"):
1. Hovered the owner's row (`menuitem "TB Test Bot"`) — the post-hover accessibility snapshot shows NO
   "Remove user" button, matching the covering test's own assertion.
2. Hovered the non-owner's row in the SAME popover instance — immediately produced
   `button "Remove user"` (positive control, same as the covering test's own Step 5).
3. **Investigated step 4's reachability directly via DOM inspection** (`getComputedStyle` on both rows'
   `#DeleteButton`, not hover-dependent): the delete `IconButton` is present in BOTH rows' DOM at all
   times; the CSS mechanism (`UserMenu.jsx`'s `userItemStyles`) sets `visibility: hidden` as the base
   state and only flips to `visible` on hover **for a selectable row** (`isSelectable = selectable &&
   user.entity_meta?.id !== currentUserId`) — for the owner's own row `isSelectable` is permanently
   `false`, so the button never becomes visible under ANY real-mouse interaction. `visibility: hidden`
   (unlike `pointer-events: none` alone) removes the element from the browser's own hit-testing —
   a genuine mouse click at that screen position lands on whatever is visually beneath it, not the
   hidden button. **There is no code path — button, keyboard shortcut, or otherwise — by which a real
   user can ever "attempt to trigger a delete action on the owner row."**
4. Cross-checked the client-side error-toast wiring (`useDeleteParticipant.js`): a `toastError(...)`
   IS wired for a failed `deleteParticipant` API call — so a server-side "cannot remove the author"
   guard, if it exists, would surface as a toast **if the request were ever sent**. But since the owner
   row's delete control is never reachable by a real user, no user-triggered request can ever reach
   that guard through the case's own described interaction. No "Cannot delete author of the
   conversation" string exists anywhere in the EliteaUI frontend source (`grep -rn "Cannot delete
   author" src/` → 0 hits) — this exact wording, if it exists at all, would have to come from the
   backend's own error body, which no real user action can trigger.

## Case-text drift — CLARIFICATION, not a defect (reverse-masking guard)

The live product does not implement "clickable-but-guarded, error toast on attempt" for owner removal
— it implements "the removal affordance never renders for the owner's own row at all" (CSS
`visibility: hidden`, which blocks real pointer hit-testing). This is **more restrictive than, and
inconsistent with, the case's own step 4/5 wording**, which describes an "attempt + red error toast"
UX that has no live equivalent. Per the reverse-masking guard (`.agents/testing.md`, this skill's
Phase 5), the live product is correct and more defensive than the case describes — the case text is
stale/inaccurate about the exact mechanism, not the product. Filed as a CLARIFICATION (not a defect):
**issue [elitea-testing-public#1564](https://github.com/EliteaAI/elitea-testing-public/issues/1564)**.

## Test Steps (source case, reproduced for traceability only — not re-implemented)
1. Open a public conversation with multiple participants — PARTICIPANTS panel visible.
2. Click avatar group to open USERS dropdown — dropdown shows all participants.
3. Hover over conversation owner's row — no trash bin icon visible for owner.
4. Attempt to trigger a delete action on the owner row — red error toast: 'Cannot delete author of the
   conversation'. **Unreachable via real UI interaction (see § Case-text drift above) — the product's
   actual, stronger guarantee (no control ever renders/activates for the owner row) is what the
   covering test proves instead.**
5. Verify owner remains in dropdown — owner still listed.

## Expected Results
- The owner's row in the Users participants dropdown never reveals a delete/"Remove user" control, on
  hover or otherwise, and consequently is never removable — proven by the covering test's Steps 3-4,
  re-confirmed live this session, PLUS this session's own additional DOM-level investigation
  establishing WHY step 4's literal "attempt + toast" mechanism can never be exercised.
- No product defect — the live behavior is a strict superset of protection vs. what the case describes
  (fully unreachable, not merely guarded-with-an-error). Filed as a CLARIFICATION (issue #1564), not a
  Bug.

## Coverage Map

### Axis 1 — Case elements

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state`/`VITE_DEV_TOKEN` (localhost) | framework fixture | already-covered |
| Precondition: public conversation with multiple participants | — | covering test's Setup (seeds owner + 1 non-owner) | `wait_for_participants_badge_count("2", ...)` | already-covered |
| 1. Open conversation → PARTICIPANTS panel visible | visible | covering test's Setup/Step 1 | popper opens, lists all participants | already-covered |
| 2. Click avatar group → USERS dropdown shows all participants | shows all | covering test Step 1 | `open_participants_popover(section="users")`; non-owner name in popper text | already-covered |
| 3. Hover owner's row → no trash bin icon | no icon | covering test Steps 3-4 | `chat-participant-remove-button` scoped in owner row `not_to_be_visible()` | already-covered |
| 4. Attempt delete on owner row → red error toast 'Cannot delete author of the conversation' | toast shown | — | — | **clarification — unreachable via real UI (see § Case-text drift); issue #1564** |
| 5. Verify owner remains in dropdown | still listed | covering test Steps 3-5 (same popover instance never loses the owner row) | popper text still contains owner name throughout | already-covered |
| Expected Final State / Pass-Fail: "Owner cannot be removed; error toast shown on attempt" | — | steps 3, 5 (removal-proof half); step 4 (toast half) | as above | already-covered (removal-proof) + clarification (toast wording) |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions
- The DOM-level `visibility`/hit-testing investigation (this session, live) — *added: the covering
  test's own AFS (ELITEA-2172) already established the hover-reveal CSS mechanism, but did not
  specifically investigate whether the button could EVER be reached by a real user through some other
  path (keyboard, force-click) — this session closes that question definitively for ELITEA-2192's own
  step 4 ask, which the covering test never needed to address.*
- `useDeleteParticipant.js`'s `toastError` wiring — *added: confirms the CLIENT-side error-toast
  MECHANISM exists in the codebase (so the case's "toast on failure" concept isn't fabricated out of
  nothing), while also confirming no code path exists to ever trigger it for an owner-removal attempt
  specifically — this distinction is what grounds the clarification instead of a defect.*
- Console/network side-channel checked throughout this session's live exploration — no new errors.

## Cleanup
No new conversation created by this AFS's own exploration — reused the existing `/chat/566` "HI Chat"
conversation (owner + Hrach Sargsyan, pre-existing from an earlier session in this same batch) for the
hover/DOM investigation. No mutating action was taken (Cancel was clicked on the one confirm dialog
opened while investigating ELITEA-2193/2194 in the same session — see those AFS files). Conversation
left in its pre-existing state (badge "2", both participants present).

## Concrete Handles (discovered during exploration)
Reuses the covering spec's handles verbatim — `chat-participants-badge-button`,
`chat-participant-row-user_{userId}_` (dynamic), `chat-participant-remove-button` (scoped inside the
row). All confirmed present and functioning on live localhost this session — provenance re-verified
fresh (`git fetch origin` this session):

| Testid | main | automation/testids |
|---|---|---|
| `chat-participants-badge-button` | ✅ | ✅ |
| `chat-participant-row-{unique_id}` (dynamic) | ✅ | ✅ |
| `chat-participant-remove-button` | ✅ | ✅ |

No new handles needed for this traceability pass.

## Known Defects Found During Exploration
None. One CLARIFICATION filed — issue #1564 (case-text drift on the owner-removal-attempt mechanism;
live product is stricter/correct, case text describes an unreachable UX).

## Blocked Steps
None. The covering test's existing Steps 3-5 plus this session's own DOM-level investigation together
resolve every element of ELITEA-2192's 5 steps against today's live product.

## TMS linkage
Link ELITEA-2192 to ELITEA-2172 in the TMS (both ways) so the audit trail resolves: ELITEA-2192's
`already-covered` disposition points at the automated test; ELITEA-2172's case gains an "also satisfies
ELITEA-2192" back-reference. Same pattern already established between ELITEA-2169/ELITEA-2167 and
ELITEA-2171/ELITEA-2168.
