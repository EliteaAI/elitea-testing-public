# Test Case: Chat – Drag and Drop Conversation Between Two Folders

## Metadata
- **TMS ID**: ELITEA-2144
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case frontmatter `priority: medium` → `@pytest.mark.p2`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` — `auth_state`/`VITE_DEV_TOKEN` on localhost
- **Analyst**: qa-engineer (agent) — cluster dispatch with ELITEA-2142/2143/2145
- **Status**: defect-found
- **surface_key**: `chat-conversation-drag-drop`

Cluster-analysed alongside ELITEA-2142/2143/2145 — see
`test-specs/chat-interface/_surface.md` § ELITEA-2142/2143/2144/2145 for the
shared mechanism/handles. **A MAJOR product defect was found and filed
during this pass, blocking the core of this specific case** — see § Known
Defects. Automation is paused for the CORE move-outcome assertion (this
case's entire point is "conversation ends up in the target folder", and the
defect means it does not); the AFS still documents everything confirmed
along the way so downstream work isn't re-derived once the fix ships.

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- Two folders exist, one containing at least one conversation — test creates
  its own via `conversation_api.create_folder()` ×2 +
  `conversation_api.create_conversation()` +
  `conversation_api.move_conversation_to_folder()` to seed the "already in a
  folder" precondition (real API setup reaching a precondition state, not a
  substitution of this case's own observable — same idiom the `_surface.md`
  ELITEA-2139/2140/2141 section already documents for this exact
  precondition shape).

## Test Data

### generate-per-test (created via API in setup, cleaned up in teardown)
- **`conv_target`** — created via `create_conversation()`, then moved into
  `source_folder` via `move_conversation_to_folder()`.
- **`source_folder`**, **`target_folder`** — two empty folders via
  `create_folder()` ×2.

## Test Steps

1. Navigate to `${BASE_URL}/chat`; expand `source_folder`.
   - **Verify**: `conv_target` is visible inside `source_folder`
     (`FOLDER_ITEM`-scoped `CONVERSATION_ITEM`).
2. Press and hold on `conv_target`'s row to begin dragging.
   - **Verify**: drag activates (`isDragging` opacity transition).
3. Drag toward `target_folder`; verify it becomes highlighted.
   - **Verify**: `target_folder`'s drop-zone shows `data-drop-active="true"`
     (same handle ELITEA-2143 specs) — **live-confirmed working** via
     screenshot this pass (`.playwright-mcp/w07-mid-drag-hover-folderB.png`):
     the dashed-border highlight correctly appears on `target_folder` and
     persists right up to the moment of release.
4. Drop the conversation onto `target_folder`.
   - **BLOCKED — confirmed product defect, [elitea-testing-public#1541](https://github.com/EliteaAI/elitea-testing-public/issues/1541)**:
     the conversation does NOT move into `target_folder`. The `PUT` fires
     with `{"folder_id": null}` instead of `target_folder`'s id — the
     conversation lands in the ungrouped/general list. Reproduced 3× this
     session (fresh page load, single continuous gesture each time; cleanest
     repro re-measured `target_folder`'s bounding box immediately before
     `mouse.up()` and confirmed the pointer was inside it — pristine-repro
     gate satisfied per `.claude/skills/test-case-analysis/references/defect-filing.md`).
5. Expand `target_folder` and verify `conv_target` is inside it.
   - **BLOCKED by the same defect** — `conv_target` is never inside
     `target_folder` given step 4's actual (buggy) outcome.
6. Verify `source_folder` still exists.
   - **Verify (unaffected by the defect)**: `source_folder`'s `FOLDER_ITEM`
     still resolves 1, now with 0 conversations inside (its only conversation
     left, just not to the intended destination).
7. Verify a success toast appears.
   - **Known defect, [elitea-testing-public#1542](https://github.com/EliteaAI/elitea-testing-public/issues/1542)**
     — same toast-gating issue as ELITEA-2142 (source-confirmed:
     `handleDragEnd`'s `toastSuccess(...)` requires `currentDraggedItems.length > 1`).
     No toast fires for this single-item move either, independent of #1541.

## Expected Results (per the case)
- Dragging `conv_target` from `source_folder` onto `target_folder` should
  move it there, remove it from `source_folder`, and leave `source_folder`
  itself intact — **step 4 currently fails this** (#1541).

## Actual Result (live, this pass)
- `conv_target` is removed from `source_folder` (correct) but ends up
  ungrouped in the general list (`folder_id: null`), NOT inside
  `target_folder` — despite `target_folder` being correctly highlighted
  during the drag. `source_folder` remains intact (empty). No toast fires
  (separate defect, #1542).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: ≥2 folders, one with a conversation | Both/precondition satisfied | Setup | API-seeded | asserted |
| 1 Expand a folder containing a conversation | Conversation visible | AFS step 1 | step 1: scoped 1-count | asserted |
| 2 Click and hold to begin dragging | Drag started | AFS step 2 | step 2: `isDragging` transition | asserted |
| 3 Drag toward a different folder; verify highlighted | Target folder highlighted | AFS step 3 | step 3: `data-drop-active="true"`, screenshot-confirmed live | asserted |
| 4 Drop onto the target folder | Conversation removed from source folder | AFS step 4 | step 4: confirmed removed from source, but ALSO not landing in target — see below | blocked *(product defect #1541 — the drop resolves to "ungrouped", not the target folder; "removed from source" half is true, "into target" half fails)* |
| 5 Expand target folder, verify conversation inside | Conversation in target folder | AFS step 5 | step 5: not reachable given step 4's actual outcome | blocked *(same defect #1541)* |
| 6 Verify source folder still exists | Source folder remains | AFS step 6 | step 6: `FOLDER_ITEM` resolves 1, empty | asserted |
| 7 Verify a success toast appears | Toast shown | AFS step 7 | step 7: no toast fires | blocked *(separate defect #1542 — independent of #1541, source-confirmed)* |
| Expected Final State: "Conversation moved from source to target folder" | — | steps 4-5 | contradicted by live behavior | blocked *(#1541 — this is the case's own central assertion)* |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Step 3's highlight assertion reused from ELITEA-2143's own spec rather
  than re-deriving — *added: proves the SAME mechanism ELITEA-2143 asserts,
  confirms it's not itself broken in the folder-to-folder direction (only
  the RESOLUTION at drop-time is broken, not the visual feedback).*
- Step 6 (source folder persists) explicitly asserted even though the case's
  core is blocked — *added: isolates exactly what DOES still work
  (removal-from-source, folder non-deletion) from what doesn't
  (arrival-at-target), narrowing the defect's blast radius for whoever fixes
  it.*
- Network-level confirmation (`PUT` body's `folder_id: null`) used as the
  primary evidence for step 4/5's failure, not just a DOM read — *added:
  removes any doubt the DOM assertion itself was mistargeted; the backend
  agrees the move landed nowhere near `target_folder`.*

## Cleanup
1. Delete `conv_target` via `conversation_api.delete_conversation(id)` —
   works regardless of its actual (buggy) final folder membership.
2. Delete `source_folder`, `target_folder` via `conversation_api.delete_folder(id)`
   — independent `try`/`except` per resource.

## Concrete Handles (discovered during exploration)

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Conversation row (draggable) | `[data-testid="chat-conversation-item-{id}"]`, scoped inside `FOLDER_ITEM` when starting from within a folder | pre-existing ✓ | `ChatPage.CONVERSATION_ITEM`. |
| Folder row (drop target) | `[data-testid="chat-folder-item-{id}"]` | pre-existing ✓ | `ChatPage.FOLDER_ITEM`. |
| Folder drop-zone wrapper (highlight state) | `testid needed` — same spec as ELITEA-2143's AFS (`data-testid="chat-folder-drop-zone-{folder_id}"` + `data-drop-active`) | needs-adding | Reuse ELITEA-2143's addition once it lands; don't re-request. |
| Success toast | `[data-testid="toast-message"]` | pre-existing | This case asserts its ABSENCE (step 7 / #1542). |

## Network Behavior
- `PUT /elitea_core/conversation/prompt_lib/{project_id}/{conv_target_id}`
  fires on drop. **Live-observed body**: `{"folder_id": null}` — NOT
  `{"folder_id": <target_folder_id>}` as the case expects. Resolves `200`
  (the request itself succeeds; it just carries the wrong destination).
- `GET .../folder/prompt_lib/{project_id}` confirms `target_folder`'s
  `conversations: []` (empty) and `total: 0` after the drop — independent
  ground-truth confirmation beyond the single conversation's own `folder_id`
  field.
- Pre-existing, unrelated: `GET /api/v2/secrets/secrets/default/{project_id}`
  `403` — excluded from console-error checks.

## Known Defects Found During Exploration

- **[MAJOR] [elitea-testing-public#1541](https://github.com/EliteaAI/elitea-testing-public/issues/1541)**
  — dropping a conversation from one folder onto another folder does not
  move it there; it lands ungrouped instead, despite the correct target
  being highlighted through to release. **Blocks this case's core
  assertion** (steps 4-5, and the case's own "Expected Final State"). Full
  repro steps, root-cause reasoning, and reproduction count in the issue.
- **[MINOR] [elitea-testing-public#1542](https://github.com/EliteaAI/elitea-testing-public/issues/1542)**
  — no success toast for a single-conversation drag move (source-confirmed
  code gate). Blocks step 7 independently of #1541.

## Blocked Steps
- **Steps 4-5** (drop lands in the target folder / conversation visible
  inside it): blocked by #1541. Once #1541 ships a fix, re-run this case's
  live exploration to confirm the corrected behavior, then convert this AFS
  to `ready-for-automation` and implement steps 3-5 as written (with step 7
  still soft-asserted per #1542 unless that also ships first).
- **Step 7** (success toast): blocked by #1542, independently of #1541.

## Automation Hints
- **Do not implement this case's test yet** — `defect-found` status per
  `.agents/testing.md` § Merge gate / this project's `test-case-analysis`
  contract: the defect (#1541) blocks further meaningful exploration of the
  case's own central assertion (not merely an isolable tail step, unlike
  ELITEA-2142's toast-only issue).
- When #1541 is fixed: the gesture technique confirmed working this pass
  (multi-step `mouse.move()`, re-measuring `target_folder`'s bounding box on
  every iteration, releasing only once the freshly-measured target rect
  contains the pointer) should be reused verbatim for the actual drop
  mechanics — it reliably produces a real `PUT` request; only the
  destination resolution was wrong, not the gesture itself.
- Priority marker: `priority: medium` → `@pytest.mark.p2`.
