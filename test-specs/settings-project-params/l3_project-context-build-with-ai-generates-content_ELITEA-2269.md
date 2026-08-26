# Test Case: Build with AI button generates project context content

## Metadata
- **TMS ID**: ELITEA-2269
- **Source case**: `.agents/automation/settings-w03/cases/ELITEA-2269.md`
  (snapshot; TMS module `settings-project-params`; TMS file under
  `settings/project-params/`)
- **Linked Story**: none
- **Priority**: l3 (medium, per case frontmatter). **pytest marker: `@pytest.mark.p2`**
  — project convention: TMS `medium` → AFS `l3_` prefix → pytest `p2`.
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}` = 399), 2026-08-26
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer (Axel), combined analyst+implementer slot
- **Status**: ready-for-automation

## Classification note — declared divergence (reverse-masking guard)

The case calls the target the **"Project Background editor"**. No section of that name
exists in the product; the editor is the **Project Context editor** at
`/settings/project-context/edit`. Already filed as clarification **#1792**
(module-wide, ELITEA-2266 analysis) — not re-filed. Note the *review form* inside the
Build-with-AI dialog **does** carry a `Project Background` field label
(`GenerateProjectContextReviewForm.jsx`), which is where the case's wording comes from.

Case step 1 says "Navigate to Settings → Project Context"; the **Build with AI** button
lives on that page's empty state (`ProjectContextEmptyState.jsx`) and navigates to the
editor route with the dialog auto-opened (`onNavigate('create', { openAi: true })` →
`ProjectContextEditor`'s first-render `openAiModal` effect). The test walks that real
user path, so case steps 1–2 are genuinely executed.

## Preconditions
- User is logged in (localhost dev-token auth).
- The feature is hidden on the **Public** project (`PUBLIC_PROJECT_ID` guard in
  `src/[fsd]/pages/settings/index.jsx`) — the test MUST run against a non-Public
  project. `${ELITEA_PROJECT_ID}` = 399 ("Private") satisfies this.
- **No Project Context exists** for the active project, so `/settings/project-context`
  renders the empty state carrying **Create** + **Build with AI** (the case's entry
  point). The pre-existing `clean_project_context` fixture
  (`automation/fixtures/data_fixtures.py:2521`) establishes exactly this and tears it
  down afterwards, tolerating the API's 404.

## Test Data
### reuse-existing
- `${ELITEA_PROJECT_ID}` = `399` ("Private").

### generate-per-test
- The project description typed into the dialog (case step 4), entered through the UI:

  ```
  Elitea is an AI collaboration platform. The team uses React on the frontend and
  Python on the backend. Deployment is via Kubernetes.
  ```

- One extra character typed into the editor after Apply, to prove editability
  (case step 6).

**Nothing about the generated content is authored by the test.** The draft is whatever
the live model returns; the assertions read that response and check the UI carried it
through faithfully (see § Fidelity Declaration).

## Fidelity Declaration

| What is substituted | Transit or terminal | Authority / real observable |
|---|---|---|
| Nothing | — | The draft is produced by a **live** `POST /elitea_core/generate_project_context_draft/prompt_lib/{project_id}` call. Its response body is the oracle: the review field and the editor are asserted **against the response**, never against a hand-written payload. |

This follows `.agents/testing.md` § *How to test a NONDETERMINISTIC producer without
substituting it*, and the in-repo precedent
`tests/ui/agents/test_agent_build_with_ai.py` (ELITEA-1909/1911, live
`click_generate_and_wait_for_response()`).

**No `page.route` / `route.fulfill` / `page.evaluate` / mock of any kind is used in this
spec.** The generation is slow (10–30 s observed live); that cost is accepted rather
than mocked away.

## Concrete Handles

| Element | Handle | Provenance |
|---|---|---|
| Empty-state **Build with AI** | `project-context-build-with-ai-button` | **added during this case** — EliteaAI/EliteaUI@d6eb52b6 on `automation/testids` (awaiting human cherry-pick to `main`) |
| Dialog container | `generate-project-context-modal` | added during this case (same commit) — caller-supplied `modalTestId` prop, pre-existing on shared `GenerateEntityModal` |
| Prompt textarea | `generate-project-context-prompt-input` | added during this case (same commit) — `promptInputTestId` |
| Loading indicator | `generate-project-context-loading-indicator` | added during this case (same commit) — `loadingIndicatorTestId` |
| **Generate Draft** | `generate-project-context-submit-button` | added during this case (same commit) — `generateButtonTestId` |
| Review **Project Background** field | `generate-project-context-review-background-input` | added during this case (same commit) — `slotProps.htmlInput['data-testid']`, lands on the real `<textarea>` so `input_value()` works |
| **Apply** | `generate-project-context-approve-button` | added during this case (same commit) — `approveButtonTestId` |
| Dialog title | `generate-project-context-title` | added during this case — EliteaAI/EliteaUI@aacfb6e on `automation/testids`; `GenerateEntityModal` gained an additive `titleTestId` pass-through to `Modal.BaseModal`'s pre-existing `titleTestId` prop |
| Editor (CodeMirror) | `project-context-editor-content` | on-main ✓ |
| Editor wrapper (scope for `.cm-line`) | `project-context-editor-wrapper` | on `automation/testids` only (EliteaAI/EliteaUI@b05bbc9a) |
| Save | `project-context-save-button` | on-main ✓ |
| Character counter | `project-context-char-counter` | on-main ✓ |

Every testid added by this case is referenced on the test's executed code path (#511).
`Back to prompt`, the dialog's close (X) and the generate-failure alert are **not**
given testids: no case exercises them, and an unreferenced testid inflates the
presence-based coverage metric. `GenerateProjectContextModalPage` therefore overrides
the base `wait_for_review_form()` (which waits on a back button) to key on `Apply` +
the populated Project Background field instead.

`GenerateEntityButton` was not modified at all. `GenerateEntityModal` gained exactly
one additive prop — `titleTestId`, defaulting to `undefined` and forwarded to the
`titleTestId` prop `Modal.BaseModal` already accepted — identical in shape to the nine
testid props it already took, so its other callers are untouched.

## Test Steps

1. **Setup** — `DELETE` any existing Project Context (tolerate 404) via
   `clean_project_context`, so the empty state renders.
2. Navigate to `${BASE_URL}/settings/project-context` (case step 1).
   - **Verify**: the empty state's **Build with AI** button is visible.
3. Click **Build with AI** (case step 2).
   - **Verify**: the URL is `${BASE_URL}/settings/project-context/edit` — the control
     responded and the expected next state is shown.
4. **A dialog appears** (case step 3).
   - **Verify**: `generate-project-context-modal` is visible and its title is exactly
     `Build with AI`.
   - **Verify**: the prompt textarea is visible and empty, and **Generate Draft** is
     **disabled** while it is (`disabled={!description.trim()}`).
5. **Provide a description of the project** (case step 4).
   - Type the description into `generate-project-context-prompt-input`.
   - **Verify**: **Generate Draft** becomes enabled.
   - Click **Generate Draft** and wait on the real network response
     (`POST **/generate_project_context_draft/**`, live, up to 30 s).
   - **Verify**: response status is `200` — "action completes without error".
   - **Verify**: the review step is reached: **Apply** is visible and the
     `Project Background` review field is visible.
   - **Verify**: the review field's value equals the response body's
     `project_background` **exactly** — the UI carried the model's own output through
     without dropping or mangling it. (Also assert the body's `project_background` is
     non-empty: the producer really produced something.)
6. **AI-generated content is inserted into the editor** (case step 5).
   - Click **Apply**.
   - **Verify**: the dialog is gone (`generate-project-context-modal` count 0).
   - **Verify**: the editor's rendered `.cm-line` list equals
     `response_body["project_background"].split("\n")` — line for line, the generated
     text is what the editor now holds. (CodeMirror's `.cm-content` has no newlines in
     `textContent`; per-line comparison is the only correct shape — digest gotcha.)
   - **Verify**: **Save** is now **enabled** (`isDirty` set by the AI insert) — but the
     content is **not saved**: the API `GET` still reports `content == ""`.
7. **The generated content is editable before saving** (case step 6 / expected final
   state).
   - Type one extra character at the end of the editor content.
   - **Verify**: the editor's last line now ends with that character, i.e. the editor
     accepted an inline edit of the generated text.
   - **Verify**: the character counter dropped by exactly one.
   - **Verify** (still unsaved): the API `GET` reports `content == ""` — everything
     above happened **before** saving, as the case requires.
8. **No console errors** across the whole flow (Axis 2 addition, project convention —
   `utils/console_errors.collect_console_errors`).

## Coverage Map

### Axis 1 — the case's own elements

| Case element | Disposition | Where asserted |
|---|---|---|
| Precondition: user logged in | setup | `auth_state` (localhost dev token) |
| Step 1 — Navigate to Settings → Project Context | asserted | Step 2 — empty state's Build with AI visible |
| Step 2 — Click "Build with AI" | asserted | Step 3 — URL becomes `/settings/project-context/edit` |
| Step 3 — a dialog / AI-assisted input appears | asserted | Step 4 — modal visible, title `Build with AI`, prompt field present, Generate disabled while empty |
| Step 4 — Provide a description when prompted | asserted | Step 5 — Generate enabled after typing; live POST returns 200; review step reached |
| Step 5 — AI-generated content inserted into the editor | asserted | Step 6 — editor lines == response `project_background` lines |
| Step 6 — generated content is editable before saving | asserted | Step 7 — extra character lands, counter drops, API still reports empty content |
| Expected final state — editable before saving | asserted | Step 7 (same) |

### Axis 2 — additions beyond the case

| Addition | Why it is grounded |
|---|---|
| Generate Draft disabled while the prompt is empty | the product's own gate (`disabled={!description.trim()}`); makes "provide a description **when prompted**" a real precondition rather than an unchecked click |
| Response `project_background` is non-empty | without it, "content was generated" could pass on an empty string |
| Save enabled after Apply, content still unsaved server-side | this is what makes step 6's "**before saving**" a fact rather than an assumption |
| No console errors | project convention on this surface |

## Automation Hints
- **Timing**: the live generation took ~5–20 s in exploration. Use a 30 s response
  timeout (`LIVE_GENERATE_RESPONSE_TIMEOUT`, same constant name as the agents' spec).
- The dialog opened from the **empty state** is a *second* `GenerateProjectContextModal`
  instance rendered by `ProjectContextEditor` (line ~370), distinct from the toolbar
  button's. Only one is ever mounted at a time (MUI `Dialog` without `keepMounted`;
  count verified 0 when closed), so the shared testids never collide.
- Navigating away from a **dirty** editor fires a `beforeunload` dialog. This spec never
  navigates while dirty; do not add such a step without handling it.
- After Apply the toolbar swaps **Build with AI** → **Edit with AI**
  (`content.trim()` non-empty) — expected, and the subject of ELITEA-2270 / #1797.

## Blocked Steps
None.
