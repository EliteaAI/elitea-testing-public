# Test Case: Chat – Conversation deletion with cancel and confirm flow

## Metadata
- **TMS ID**: ELITEA-2456
- **Linked Story**: none
- **Priority**: l2 (per source case's `high`; traceability AFS, no priority-digit filename)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: test-automation-engineer (agent, combined analyst+implementer slot), session 2026-08-14
- **Status**: already-covered

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`).
- A conversation exists in the left panel.

## Dedup proof — Rule-6 behavioural equivalence

**Covering spec:** `automation/tests/ui/chat/test_conversation_deletion_flow.py`
(TMS ELITEA-2114, AFS
`test-specs/chat-interface/l2_conversation-deletion_ELITEA-2114.md`), merged to
`origin/automation/base` (commit `2dd43004`, PR #696,
"test(ELITEA-2114): conversation deletion flow (cancel + delete on active
conversation)"). Confirmed on `origin/automation/base` via
`git log origin/automation/base -- automation/tests/ui/chat/test_conversation_deletion_flow.py`
this session (fresh `git fetch origin` first).

**Behavioural-equivalence argument.** ELITEA-2456 asks for exactly the flow the
covering spec's single test, `test_conversation_deletion_cancel_then_delete_active_conversation`,
already implements END TO END: hover → 3-dot menu → context-menu enumeration →
Delete → confirmation modal (title/body/buttons) → **Cancel** (modal closes,
conversation unchanged) → reopen the SAME conversation's delete flow again →
**confirm Delete** (modal closes, conversation gone, next conversation
auto-selected/highlighted, main panel no longer shows the deleted conversation's
content). Every one of ELITEA-2456's 13 steps maps onto an already-asserted
step in the covering test — same mechanism, same sequence (cancel-then-delete
on the SAME conversation, opened as the ACTIVE conversation first, which is
precisely what the covering test's own AFS calls out as its differentiator
from the OTHER two adjacent merged tests it doesn't fold into,
`test_delete_conversation_with_confirmation`/`test_delete_conversation_cancel`
in `test_conversation_management.py`).

| ELITEA-2456 step | Covered by (`test_conversation_deletion_flow.py`) |
|---|---|
| 1. Hover conversation in left panel → target loads | Setup (`:148-174`) creates `conv_target`, navigates and opens it as active; Step 2 (`:189-199`) hovers it |
| 2. Verify 3-dot icon appears on the right side | Step 2 (`:192-199`) — `get_conversation_menu_button()` hidden→visible transition on hover (position not literally asserted as "right side"; the icon's presence/visibility is the behavioral proxy, same as ELITEA-2116's AFS treats "left"/"right" via DOM order) |
| 3. Click 3-dot → context menu with Delete/Edit/Move to/Export/Playback/Pin on top | Step 3 (`:201-217`) — live 5-item set asserted (`rename, move-to, playback, pin, delete`) via `EXPECTED_MENU_ITEM_KEYS`; the case's literal 6-item list (including non-existent "Edit"/"Export") is the SAME stale case-text drift the covering test's own AFS documents as CLARIFICATION-2 — not a gap, a pre-existing documented mismatch between case text and live product |
| 4. Click Delete → responds | Step 4 (`:219-230`) |
| 5. Verify confirmation modal title "Delete conversation?" + body text | Step 4 title assertion (`:228-230`, asserts live text `"Delete confirmation"` — same documented drift, #695) + Step 5 body assertion (`:232-236`) |
| 6. Verify Cancel (secondary) + Delete (red/primary) buttons | Step 6 (`:238-240`) — both buttons' visibility asserted (styling depth is ELITEA-2116's distinct territory, not part of this case's own narrower "buttons present" ask — case text says "Cancel (secondary)" as a label/description, not a separate styling assertion; covering test asserts presence, which is what the case step literally verifies) |
| 7. Click Cancel → modal closes, conversation remains unchanged | Step 7 (`:242-254`) — dialog hidden + conversation still in Today group + URL still shows `conv_target` |
| 8. Hover same conversation, reopen menu, click Delete again → no error, expected state | Step 8 (`:256-268`) — dialog reopens cleanly (also asserts count==1, guarding against stale-modal residue — a stronger check than the case asks) |
| 9. Verify confirmation modal appears again | Step 8 (`:263`) — `delete-confirm-dialog` visible assertion |
| 10. Click Delete → responds | Step 9 (`:270-280`) |
| 11. Verify modal closes, deleted conversation no longer in left panel | Step 9 dialog-hidden (`:281`) + Step 10 (`:283-286`) item count 0 |
| 12. Verify no error message, next conversation highlighted as selected | Step 11 (`:288-319`) — console-error check + URL routes to a different, real (API-verified) conversation id + `data-active="true"` on that id |
| 13. Verify main chat panel doesn't display deleted conversation content | Step 12 (`:326-372`) — network-verified refetch of the auto-selected conversation's content (200) + message-list empty-state check (both test conversations are zero-message by design, so the network check is what genuinely distinguishes "refreshed to the new conversation" from "stuck on stale content" — same CLARIFICATION-3 discipline documented in the covering AFS) |

**Scope note (no gap, so no `extend-existing`).** ELITEA-2456's 13 steps are a
strict subset of the covering test's 12 (already-numbered) steps plus its
Setup — the covering test does everything this case asks, in the same order,
against the same kind of data (API-created, zero-message conversations), and
additionally proves the underlying `DELETE`/`GET` network calls rather than
relying on DOM state alone. No case element lacks a corresponding assertion in
the covering spec.

## Test Steps (source case, reproduced for traceability only — not re-implemented)
1. Navigate to the Chats section and hover over any conversation in the left panel — Target page/section loads successfully.
2. Verify the three-dot icon appears on the right side of the conversation row — Condition holds as described.
3. Click the three-dot icon and verify a context menu appears with options: Delete, Edit, Move to, Export, Playback, Pin on top — Control responds; expected next state is shown.
4. Click Delete — Control responds; expected next state is shown.
5. Verify a confirmation modal appears with title "Delete conversation?" and body text "Are you sure to delete conversation? It can't be restored." — Condition holds as described.
6. Verify the modal contains Cancel (secondary) and Delete (red/primary) buttons — Condition holds as described.
7. Click Cancel and verify the modal closes and the conversation remains in the list unchanged — Control responds; expected next state is shown.
8. Hover over the same conversation, open the context menu and click Delete again — Action completes without error and produces the expected UI state.
9. Verify the confirmation modal appears again — Condition holds as described.
10. Click Delete — Control responds; expected next state is shown.
11. Verify the modal closes and the deleted conversation is no longer present in the left panel — Condition holds as described.
12. Verify no error message is shown and the next conversation is highlighted as selected — Condition holds as described.
13. Verify the main chat panel does not display the deleted conversation content — Condition holds as described.

## Expected Results
- Cancel preserves the conversation unchanged; re-opening delete and
  confirming removes it, auto-selects the next conversation, and the main
  panel reflects the new selection — proven live by
  `test_conversation_deletion_flow.py` (see Dedup proof above).

## Coverage Map

### Axis 1 — Case elements

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 — hover conversation | page loads, hover works | covering test Setup + Step 2 | `:148-199` | already-covered |
| Step 2 — 3-dot icon appears | icon visible on hover | covering test Step 2 | `:192-199` | already-covered |
| Step 3 — context menu with Delete option | menu shown | covering test Step 3 | `:201-217` | already-covered |
| Step 4 — click Delete | responds | covering test Step 4 | `:219-230` | already-covered |
| Step 5 — modal title + body | correct text shown | covering test Steps 4–5 | `:228-236` | already-covered |
| Step 6 — Cancel/Delete buttons present | both visible | covering test Step 6 | `:238-240` | already-covered |
| Step 7 — Cancel preserves conversation | modal closes, unchanged | covering test Step 7 | `:242-254` | already-covered |
| Step 8 — reopen Delete flow | no error | covering test Step 8 | `:256-268` | already-covered |
| Step 9 — modal reappears | dialog visible | covering test Step 8 | `:263` | already-covered |
| Step 10 — click Delete | responds | covering test Step 9 | `:270-280` | already-covered |
| Step 11 — modal closes, conversation gone | removed | covering test Steps 9–10 | `:281-286` | already-covered |
| Step 12 — no error, next conversation highlighted | correct | covering test Step 11 | `:288-319` | already-covered |
| Step 13 — main panel doesn't show deleted content | correct | covering test Step 12 | `:326-372` | already-covered |

### Axis 2 — Analyst additions
- None beyond the covering spec's own additions (already documented in
  `l2_conversation-deletion_ELITEA-2114.md`'s Coverage Map Axis 2) — none
  needed here.

## Cleanup
N/A — no new test written; nothing new to clean up. Covering spec's own
`finally` block deletes `conv_sibling`/`conv_target` via
`conversation_api.delete_conversation(id)`.

## Concrete Handles (discovered during exploration)
Reuses the covering spec's handles verbatim — `delete-confirm-dialog`,
`delete-confirm-title`, `delete-confirm-message`, `delete-confirm-button`,
`delete-confirm-cancel-button`, `conversation-menu-menu-button` (scoped),
`chat-conversation-menu-{key}-menuitem`, `data-active` state attribute — all
already on `main` (ELITEA-2114's `automation/testids` commit `20567b81`,
confirmed promoted). No new handles needed for this traceability pass.

## TMS linkage
Link ELITEA-2456 to ELITEA-2114 in the TMS (both ways) so the audit trail
resolves: ELITEA-2456's `already-covered` disposition points at ELITEA-2114's
automated test; ELITEA-2114's case gains an "also satisfies ELITEA-2456"
back-reference.
