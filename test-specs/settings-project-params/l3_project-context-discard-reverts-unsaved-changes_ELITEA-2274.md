# Test Case: Discard button reverts unsaved changes

## Metadata
- **TMS ID**: ELITEA-2274
- **Source case**: `.agents/automation/settings-w03/cases/ELITEA-2274.md`
  (snapshot; TMS module `settings-project-params`; TMS file
  `settings/project-params/ELITEA-2274_discard-button-reverts-unsaved-changes.md`)
- **Linked Story**: none
- **Priority**: l3 (medium) → **`@pytest.mark.p2`**
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}` = 399), 2026-08-26
- **User set**: `${TEST_USER}` (localhost `auth_state`)
- **Analyst**: test-automation-engineer (Axel), combined analyst+implementer slot
- **Status**: ready-for-automation

## Classification note — declared divergence (reverse-masking guard)

**Discard leaves the editor.** `ProjectContextEditor.handleDiscard` calls
`setIsDirty(false)` then `onNavigate('saved')`, so clicking Discard returns to
`/settings/project-context` — it does not stay in the editor showing reverted text
(confirmed live 2026-08-26). Case step 5 ("the editor reverts to the previously saved
content") is therefore asserted by **re-opening the editor** after the Discard and
reading it: the content is the pre-edit baseline, the edit is gone. Case step 6 ("no
changes are persisted") is asserted independently, against the **server**, via a full
page reload.

Nothing is weakened — the case's observable is *the edit did not survive Discard*, and
that is asserted twice (client re-render and server truth). Same module-level case-text
drift already filed as **#1792**; no new ticket.

## Preconditions
- User is logged in (localhost dev-token auth).
- Non-Public project (`${ELITEA_PROJECT_ID}` = 399 "Private").
- **A Project Context with saved content exists** — case step 2 says "Note the *current*
  content", so the editor must open in **edit** mode (its sibling button reads
  `Discard`; in create mode it reads `Cancel` and does something different —
  `handleCancel` navigates to the empty state). Established by the pre-existing
  `project_context_seed` fixture.

## Test Data
### reuse-existing
- `${ELITEA_PROJECT_ID}` = `399`.
- Fixture `project_context_seed` (`automation/fixtures/data_fixtures.py:2542`).

### generate-per-test
- Seed body: `## ELITEA-2274 baseline\n\nSaved content that Discard must restore.`
- Appended marker (the "change" of case step 3): `\nUNSAVED EDIT` — one new line, so the
  appended text is the editor's own last line and can be asserted exactly.

## Fidelity Declaration

| What is substituted | Transit or terminal | Authority / real observable |
|---|---|---|
| Precondition seeding of the Project Context **`content`** via `PUT` instead of typing + saving it in the UI | **Transit** | It only establishes "saved content exists" so the editor opens in edit mode with a Discard button. The case's observable is the *revert*, and the baseline it is compared against is **read off the product** in step 3 (`get_editor_text()`), not taken from the seed string — so even a seed that mismatched would not make this test pass falsely. |
| The **`enabled` flag** carried by that same `PUT` | **Not substituted** | `project_context_seed` is called with `content` only; `enabled` defaults to `None` = echo the product's own current value (`.agents/testing.md`, pinned by `tests/unit/test_project_context_seed_enabled_flag_not_authored.py`). This case never asserts the flag. |

`page.evaluate` is used only for the clipboard write behind the paste gesture
(pre-existing reviewed pattern). No `route.fulfill`, no injected app state.

## Test Steps

1. **Setup** — `project_context_seed("## ELITEA-2274 baseline\n\nSaved content that
   Discard must restore.")` (content only).
2. Navigate to `${BASE_URL}/settings/project-context` — case step 1.
   - **Verify**: the saved view renders (`project-context-toggle-card` visible).
   Then click **Edit** (`project-context-edit-button`).
   - **Verify**: URL is `${BASE_URL}/settings/project-context/edit` and the editor is
     visible.
3. **Note the current content** — case step 2. Read the editor's rendered lines into a
   local `baseline` (a value **produced by the product**, which is what every later
   assertion compares against).
   - **Verify**: `baseline` is non-empty (a silent empty read would make the whole
     comparison vacuous).
   - **Verify**: Save and Discard are **disabled** (nothing changed yet) and the
     Discard button's label is exactly `Discard` (edit mode, not `Cancel`).
4. **Make a change** — case step 3: move the caret to the end of the document
   (`ControlOrMeta+End`, CodeMirror's own binding) and type `UNSAVED EDIT` on a new line.
   - **Verify**: the editor's lines now differ from `baseline` and end with
     `UNSAVED EDIT`.
   - **Verify**: Save and Discard are now **enabled**.
5. **Click Discard** — case step 4.
   - **Verify**: the app returns to `${BASE_URL}/settings/project-context` and the saved
     view renders (the product's own response to the click).
   - **Verify**: the saved view's rendered markdown does **not** contain `UNSAVED EDIT`.
6. **The editor reverts to the previously saved content** — case step 5.
   - Click **Edit** again.
   - **Verify**: the editor's rendered lines equal `baseline` **exactly**.
   - **Verify**: `UNSAVED EDIT` is absent from the editor.
   - **Verify**: Save and Discard are **disabled** again (the reverted state is clean).
7. **No changes are persisted** — case step 6, the case's Expected Final State, checked
   against the **server** rather than the client cache.
   - Perform a full browser reload of `${BASE_URL}/settings/project-context/edit`
     (a hard reload defeats RTK-Query's cache, so what renders is what the server has).
   - **Verify**: the editor's lines equal `baseline` and `UNSAVED EDIT` is absent.
8. **Teardown** — fixture deletes the Project Context (tolerates 404).

## Concrete Handles

| Element | Handle (testid) | Provenance | Verified |
|---|---|---|---|
| Saved-view toggle card (saved-view readiness) | `project-context-toggle-card` | on `automation/testids` only (EliteaAI/EliteaUI@b05bbc9a) | live 2026-08-26 |
| Saved-view Edit button | `project-context-edit-button` | on `automation/testids` only (EliteaAI/EliteaUI@b05bbc9a) | live 2026-08-26 |
| Editor content | `project-context-editor-content` | **on-main ✓** | live 2026-08-26 |
| Editor wrapper (line scope) | `project-context-editor-wrapper` | on `automation/testids` only (EliteaAI/EliteaUI@b05bbc9a) | live 2026-08-26 |
| Save button | `project-context-save-button` | **on-main ✓** | live 2026-08-26 |
| Discard button | `project-context-discard-button` | on `automation/testids` only (EliteaAI/EliteaUI@b05bbc9a) | live 2026-08-26 |
| Settings content pane (render scope) | `settings-content` | on `automation/testids` only | live 2026-08-26 |

## Coverage Map

### Axis 1 — every case element

| # | Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|---|
| 1 | Navigate to Settings → Project Context | page loads | Step 2 | saved view renders; Edit opens the editor route | covered |
| 2 | Note the current content in the editor | completes, expected UI state | Step 3 | `baseline` read off the product + non-empty assertion + clean-state assertion | asserted |
| 3 | Make changes to the content | completes | Step 4 | content differs from `baseline`, ends with the marker; buttons enable | asserted |
| 4 | Click Discard | control responds | Step 5 | navigation back to the saved view; marker absent from the render | asserted |
| 5 | Editor reverts to the previously saved content | holds | Step 6 | re-opened editor equals `baseline`; marker absent; buttons disabled | asserted (location divergence declared) |
| 6 | No changes are persisted | holds (final state) | Step 7 | full reload (server truth) equals `baseline`, marker absent | asserted |
| P | Precondition: user logged in | — | Setup | `auth_state` | covered |
| P | Precondition: saved content exists | — | Setup | `project_context_seed` (transit, declared) | covered |

### Axis 2 — observables asserted beyond the case

| Observable | Why |
|---|---|
| Discard's label is exactly `Discard` (not `Cancel`) | The same button is `Cancel` in create mode and calls a **different** handler (`handleCancel` → empty state). Asserting the label pins that the test really exercised the *edit-mode Discard* the case is about. |
| Save/Discard disabled → enabled → disabled across the flow | Free, and it is the product's own dirty-state signal; it turns "content reverted" into "the editor returned to a genuinely clean state". (ELITEA-2275 owns this observable as its subject; here it is corroboration, and both cases assert their own values.) |
| `baseline` non-empty | Guards the comparison itself: an empty read would make every later equality trivially true. |
| Marker absent from the **saved view's render**, not only the editor | Two independent renderers of the same server state; a revert that fooled one would still fail the other. |
| No console errors across the run | Standard side-channel check on this surface. |

## Known Defects
- **#1792 (case text)** — module-wide "Project Background" naming and the assumption
  that Discard keeps you in the editor. Pre-existing, not re-filed.

## Blocked Steps
None — every step above was executed live and observed 2026-08-26.
