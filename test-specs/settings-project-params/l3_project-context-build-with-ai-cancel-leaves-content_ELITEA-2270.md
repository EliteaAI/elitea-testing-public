# Test Case: Build with AI can be cancelled without modifying the editor content

## Metadata
- **TMS ID**: ELITEA-2270
- **Source case**: `.agents/automation/settings-w03/cases/ELITEA-2270.md`
  (snapshot; TMS module `settings-project-params`; TMS file under
  `settings/project-params/`)
- **Linked Story**: none
- **Priority**: l3 (medium, per case frontmatter). **pytest marker: `@pytest.mark.p2`**
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}` = 399), 2026-08-26
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer (Axel), combined analyst+implementer slot
- **Status**: ready-for-automation

## Classification note — declared divergence (reverse-masking guard), filed as #1797

The case's step order is **not executable as written**, and the divergence is a real
product behaviour, not a defect:

> Step 2 — Enter manual content in the Project Background editor
> Step 3 — Click **"Build with AI"** to open the dialog

`ProjectContextEditor.jsx` swaps the toolbar's AI control on `content.trim()`:

```jsx
{content.trim() ? <AIEditProjectContextButton/>   /* "Edit with AI" */
                : <GenerateProjectContextButton/> /* "Build with AI" */}
```

Confirmed live 2026-08-26: with an empty editor the toolbar renders **Build with AI**
(`generate-project-context-open-button` count 1); after typing manual content that
button is **gone** (count 0) and **Edit with AI**
(`ai-edit-project-context-open-button`) renders in its place. So once step 2 is done,
step 3's control does not exist.

**Filed as clarification #1797** (`question` label) — the case text needs splitting or
rewording. Not a bug: two different dialogs (generate-a-draft vs refine-existing).

**Nothing is weakened to accommodate this.** The case's *observable* — "cancel the AI
dialog ⇒ the editor content is unchanged" — is asserted twice, once per control, so
both the literal Build-with-AI path and the case's manual-content intent are covered:

- **Phase A** (case steps 3–5 literally, on the state where Build with AI exists):
  empty editor → **Build with AI** → Cancel → editor still empty, Save/Discard still
  disabled.
- **Phase B** (case steps 2–5 with the product's real control): type manual content →
  **assert the toolbar now shows Edit with AI** (the divergence itself, asserted as
  observed rather than assumed) → open it → Cancel → editor content byte-identical to
  what was typed.

Also, the case says "Project Background editor"; no such section exists — it is the
Project Context editor (clarification **#1792**, already filed, not re-filed).

## Preconditions
- User is logged in (localhost dev-token auth).
- Non-Public project (`${ELITEA_PROJECT_ID}` = 399 "Private") — the tab is hidden on
  the Public project.
- **No Project Context exists**, so the page renders the empty state and **Create**
  opens a genuinely empty editor (Phase A's precondition). `clean_project_context`
  establishes and tears this down, tolerating the API's 404.

## Test Data
### reuse-existing
- `${ELITEA_PROJECT_ID}` = `399` ("Private").

### generate-per-test
- Manual editor content (case step 2), typed through the UI:
  `Manual project background entered by hand.`
  Deliberately single-line: CodeMirror's `markdown()` extension rewrites multi-line
  typed input (auto-continued list items — digest gotcha), and this case needs a
  *typed* "enter manual content" gesture, not a paste.

## Fidelity Declaration

| What is substituted | Transit or terminal | Authority / real observable |
|---|---|---|
| Nothing | — | The content is typed into the real editor by the test acting as the user; the "unchanged" observable is read back off the product's own CodeMirror lines. Both dialogs are opened and cancelled for real; no generation request is ever issued (Cancel from the input step fires none). |

No `page.route`, `route.fulfill`, `monkeypatch`, `page.evaluate` or mock of any kind.

## Concrete Handles

| Element | Handle | Provenance |
|---|---|---|
| Empty-state **Create** | `project-context-create-button` | on-main ✓ |
| Toolbar **Build with AI** | `generate-project-context-open-button` | **added during ELITEA-2269** — EliteaAI/EliteaUI@d6eb52b6 on `automation/testids` |
| Build-with-AI dialog | `generate-project-context-modal` | added during ELITEA-2269 (same commit) |
| Build-with-AI **Cancel** | `generate-project-context-cancel-button` | added during ELITEA-2269 (same commit) |
| Toolbar **Edit with AI** | `ai-edit-project-context-open-button` | on-main ✓ |
| Edit-with-AI dialog | `ai-edit-project-context-modal` | pre-existing on `automation/testids` |
| Edit-with-AI **Cancel** | `ai-edit-project-context-cancel-button` | pre-existing on `automation/testids` |
| Editor (CodeMirror) | `project-context-editor-content` | on-main ✓ |
| Editor wrapper (scope for `.cm-line`) | `project-context-editor-wrapper` | on `automation/testids` only |
| Save / Discard | `project-context-save-button` / `project-context-discard-button` | Save on-main ✓; Discard on `automation/testids` |

## Test Steps

1. **Setup** — `clean_project_context` deletes any existing context (tolerating 404).
2. Navigate to `${BASE_URL}/settings/project-context` and click **Create**
   (case step 1).
   - **Verify**: URL is `${BASE_URL}/settings/project-context/edit`, the editor is
     visible and **empty** (a single empty `.cm-line`).
   - **Verify**: the toolbar's AI control is **Build with AI**.
   - **Verify**: Save and Discard are both **disabled** (nothing dirty yet).
3. **Phase A — cancel Build with AI on an untouched editor** (case steps 3–5).
   - Click **Build with AI**; **Verify**: `generate-project-context-modal` is visible
     and its title is exactly `Build with AI`.
   - Click **Cancel** (case step 4 — "close or cancel the dialog without submitting").
   - **Verify**: the dialog is gone (count 0).
   - **Verify** (case step 5): the editor content is **still empty**, and Save and
     Discard are **still disabled** — cancelling touched nothing, not even the dirty
     flag.
4. **Phase B — enter manual content, then cancel the AI dialog** (case step 2 + 3–5).
   - Type `Manual project background entered by hand.` into the editor.
   - **Verify**: the editor's lines are exactly that one line — the field accepted the
     input and displays the entered value (case step 2's expected result).
   - **Verify** (the declared divergence, asserted): **Build with AI** is now **absent**
     (count 0) and **Edit with AI** is present with that exact label.
   - Click **Edit with AI**; **Verify**: `ai-edit-project-context-modal` is visible and
     its title is exactly `Edit with AI`.
   - Click its **Cancel** (case step 4).
   - **Verify**: the dialog is gone.
   - **Verify** (case step 5 / expected final state): the editor's lines are still
     **exactly** `["Manual project background entered by hand."]` — byte-identical to
     what was typed, unmodified by opening and cancelling the dialog.
   - **Verify**: Save is still enabled (the manual edit's dirty state survived — the
     cancel did not clear the user's own work either).
5. **No console errors** across the whole flow (Axis 2 addition, project convention).

## Coverage Map

### Axis 1 — the case's own elements

| Case element | Disposition | Where asserted |
|---|---|---|
| Precondition: user logged in | setup | `auth_state` |
| Step 1 — Navigate to Settings → Project Context | asserted | Step 2 — page loads, Create opens the editor at the expected route |
| Step 2 — Enter manual content in the editor | asserted | Step 4 — typed content, editor displays exactly the entered value |
| Step 3 — Click "Build with AI" to open the dialog | asserted, **adapted** (see § Classification note, #1797) | Step 3 — literal Build-with-AI dialog opened (empty editor); Step 4 — the product's actual post-content control, Edit with AI, opened, and the swap itself asserted |
| Step 4 — Close or cancel the dialog without submitting | asserted | Step 3 (Build-with-AI Cancel) and Step 4 (Edit-with-AI Cancel) |
| Step 5 — Editor content is unchanged | asserted | Step 3 (still empty, still not dirty) and Step 4 (byte-identical to the typed line) |
| Expected final state — content unchanged | asserted | Step 4 (same) |

### Axis 2 — additions beyond the case

| Addition | Why it is grounded |
|---|---|
| Save/Discard still disabled after Phase A's cancel | "unchanged" means the *dirty state* is untouched too, not just the visible text; without it a cancel that silently dirtied the form would pass |
| The Build-with-AI → Edit-with-AI swap is asserted | it is the product behaviour that makes the case text unexecutable; asserting it pins the divergence so a future revert fails loudly instead of silently re-enabling a stale case |
| Dialog titles asserted verbatim | proves *which* dialog was opened — the two are otherwise indistinguishable by "a modal is visible" |
| No console errors | project convention on this surface |

## Automation Hints
- Cancel from the **input** step issues no network request at all
  (`GenerateEntityModal.handleClose` just resets state) — nothing to wait on beyond the
  dialog's disappearance.
- Do not navigate while the editor is dirty: a `beforeunload` dialog fires (observed
  live). Phase B ends dirty on purpose; the test finishes there and teardown is
  API-only.
- Type, do not paste, the manual content — the case's step 2 is a typing gesture and
  the content is single-line, so CodeMirror's markdown auto-continuation is not in play.

## Blocked Steps
None.
