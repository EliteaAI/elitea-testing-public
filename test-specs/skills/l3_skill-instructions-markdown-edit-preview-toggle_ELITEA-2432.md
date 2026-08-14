# Test Case: Skill instructions — Markdown edit and preview toggle

## Metadata
- **TMS ID**: ELITEA-2432
- **Linked Story**: none
- **Priority**: l3 (medium, per case)
- **Environment Explored**: local (`http://localhost:5173`, `automation/testids`)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot)
- **Status**: ready-for-automation

## Preconditions
- User is logged in to the Elitea platform (localhost `auth_state`).
- A skill must already exist to edit — Rule 10 (read-only-by-default)
  evaluated NO: the case mutates the Instructions field and persists it
  (step 5), so an existing stable skill cannot serve; seed a fresh skill
  via `SkillAPI.create_skill()` and clean it up afterward. Same pattern as
  ELITEA-2431 (`TestEditSkill`).

## Test Data
### generate-per-test (seeded via API, deleted in teardown)
- Skill name: `autotest-skill-markdown-toggle` (satisfies the live
  client-side Name pattern `/^[a-z0-9]([a-z0-9-]*[a-z0-9])?$/`)
- Original instructions (seeded, plain text — not asserted, only used to
  reach the detail page in a known starting state):
  `"Always say ORIGINAL"`
- New Markdown instructions (typed in step 2):
  ```
  **Bold text** and a list:
  - Item one
  - Item two
  ```
  (single `\n` between lines, no blank-line paragraph break — see
  **Amended during implementation** below for why). Chosen because it
  exercises two distinct Markdown constructs (inline bold, an unordered
  list) whose rendered form is structurally different from their raw
  source — bold loses the `**` delimiters and becomes a `<strong>` node,
  and list items lose their leading `- ` marker and become `<li>` nodes —
  so a Preview-mode assertion can prove real interpretation happened, not
  just a pass-through render of the raw text.

## Test Steps
1. Open an existing Skill (`/skills/all/{id}`)
   - **Verify**: skill detail page loads with the seeded Instructions value
     shown in Edit mode (the toggle's default state)
2. In the Instructions section, switch to Edit mode and modify the Markdown
   body
   - **Verify**: Edit mode is/was already active (toggle button pressed
     state); the CodeMirror editor's raw text is replaced with the new
     Markdown source, exactly as typed
3. Switch to Preview mode — verify the rendered Markdown output is correct
   - **Verify**: the Preview-mode toggle button becomes the pressed one;
     the rendered content area's text no longer contains the literal
     Markdown syntax markers (`**`, `- `) — proving the bold/list markup
     was interpreted, not echoed verbatim — while the semantic words
     ("Bold text", "Item one", "Item two") are still present
4. Switch back to Edit mode — verify the raw Markdown matches what was
   typed
   - **Verify**: the Edit-mode toggle button becomes the pressed one again;
     the CodeMirror editor's raw text content is byte-identical to what was
     typed in step 2 (including the `**` and `- ` markers) — the
     edit/preview round trip does not mutate the stored source
5. Save and re-open — verify updated instructions persist
   - **Verify**: Save persists the change (`PUT` → `200 OK` + "Skill saved"
     toast, no navigation — same edit-flow mechanics as ELITEA-2431);
     navigating back to the Skills list and re-opening the skill shows the
     Instructions field with the exact new Markdown source from step 2,
     not the original seeded text

## Expected Results
- The Instructions section's Edit/Preview toggle switches between the raw
  Markdown CodeMirror editor and a rendered Markdown preview without losing
  or altering the underlying instructions text.
- Preview mode renders Markdown syntax as real formatting (bold, lists) —
  the raw syntax characters are not visible in the rendered output.
- Switching back to Edit mode shows the exact raw Markdown that was typed,
  unaffected by having been previewed.
- Saving persists the Markdown source (not a rendered/converted form) —
  re-opening the skill shows the identical raw Markdown in the editor.
- No console errors, no unexpected network failures.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open an existing Skill | detail page loads | step 1 | `step 1`: `get_instructions()` == seeded (single-line) value + Edit mode's `aria-pressed` toggle | asserted |
| 2 Switch to Edit mode and modify the Markdown body | action completes, raw text updated | step 2 | `step 2`: `fill_instructions_markdown()` + `get_instructions_multiline()` == typed Markdown | asserted |
| 3 Switch to Preview mode — rendered output is correct | rendered Markdown, no error | step 3 | `step 3`: `click_preview_mode()` + `get_preview_content()` contains rendered words, does NOT contain raw `**`/`- ` markers | asserted |
| 4 Switch back to Edit mode — raw Markdown matches what was typed | raw text unchanged | step 4 | `step 4`: `click_edit_mode()` + `get_instructions_multiline()` == same typed Markdown from step 2 | asserted |
| 5 Save and re-open — updated instructions persist | persists, confirmation shown | step 5 | `step 5`: PUT response status 200 + "Skill saved" toast (inside `save_edits()`) + re-open `get_instructions_multiline()` == typed Markdown | asserted |

**Axis 2 — Analyst additions.**
- None beyond the case. Source-level confirmation (not asserted directly,
  informational): the Preview pane is rendered by the app's shared
  `Markdown` component (`marked`-based lexer, the same renderer used for
  chat messages) — confirmed live that `**Bold text**` renders as
  `<strong>Bold text</strong>` and `- Item one` / `- Item two` render as a
  real `<ul><li>` list, both with the raw syntax characters stripped from
  the accessible text.

## Cleanup
1. Delete the seeded skill via `SkillAPI.delete_skill(skill_id)` in a
   `try/finally` (same pattern as `TestEditSkill`).

## Concrete Handles (discovered during exploration)

All testid-only. Three testids were a **confirmed live gap** and added via
`add-data-testid` this run (pushed to `automation/testids`, commit
`b6e1c7c9`); everything else was already wired.

| Element | Testid | Page-object field/method | Provenance |
|---|---|---|---|
| Instructions editor content (Edit mode) | `skill-instructions-editor-content` | `SkillFormPage.instructions_editor_content` / `fill_instructions()` / `get_instructions()` | pre-existing, on `main` ✓ |
| Edit-mode toggle button | `skill-instructions-edit-mode-button` | **NEW** `SkillDetailPage.instructions_edit_mode_button` / `click_edit_mode()` | added this run — `automation/testids` only (commit `b6e1c7c9`), awaiting human cherry-pick to `main` |
| Preview-mode toggle button | `skill-instructions-preview-mode-button` | **NEW** `SkillDetailPage.instructions_preview_mode_button` / `click_preview_mode()` | added this run — `automation/testids` only (commit `b6e1c7c9`), awaiting human cherry-pick to `main` |
| Preview-mode rendered content container | `skill-instructions-preview-content` | **NEW** `SkillDetailPage.instructions_preview_content` / `get_preview_content()` | added this run — `automation/testids` only (commit `b6e1c7c9`), awaiting human cherry-pick to `main` |
| Save button | `skill-save-button` | `SkillFormPage.save_button` (`is_save_enabled()`); edit-flow save via `SkillDetailPage.save_edits()` | pre-existing, on `main` ✓ |
| Confirmation toast | `toast-message` | `SkillDetailPage.version_toast_message` (reused) | pre-existing, on `main` ✓ |
| Skill list card (re-open) | `entity-card-name` (card) | `SkillsListPage.click_skill_card()` / `skill_exists_in_list()` | pre-existing, on `main` ✓ |

**Handle gap detail.** `CreateSkillForm.jsx`'s Edit/Preview toggle
(`TabGroupButton` fed a `modeButtons` array) had no `data-testid` on either
button, and the rendered-preview wrapper `<Box>` had none either —
confirmed live via a11y snapshot with no `data-testid` visible on the DOM
before this run's fix. `TabButtonItem.jsx` (the shared component
`TabGroupButton` renders each button through) already spreads
`{...item.buttonProps}` onto the underlying MUI `ToggleButton`, so the fix
is caller-side only (`CreateSkillForm.jsx`'s `modeButtons` array literal
gains `buttonProps: { 'data-testid': '...' }` per entry) — no change to
the shared `TabButtonItem.jsx`/`TabGroupButton.jsx` components themselves,
consistent with the "shared components never hardcode feature-scoped
testids" rule (the testid is supplied by the caller, not baked into the
shared component).

## Network Behavior
- Switching Edit/Preview mode is 100% client-side (local `useState`,
  `CreateSkillForm.jsx`) — confirmed live, no network calls fire on toggle.
- `PUT /api/v2/elitea_core/skill/prompt_lib/{project}/{skillId}` fires on
  Save (step 5) → `200 OK`, same mechanics as ELITEA-2431 (updates
  name/description AND the currently selected version's instructions in
  one call, no navigation).
- `GET /api/v2/elitea_core/skills/prompt_lib/{project}/...` re-fires on
  navigating back to the Skills list (step 5).
- `DELETE /api/v2/elitea_core/skill/prompt_lib/{project}/{skillId}` on
  cleanup → `204 No Content`.

## Known Defects Found During Exploration
None product-level. The Edit/Preview toggle behaved exactly per the case's
expected results: Markdown syntax rendered correctly in Preview (bold →
`<strong>`, list → `<ul><li>`), and the raw Markdown source was unchanged
after round-tripping through Preview and back to Edit. The only gap found
was a testid gap (three toggle/preview-container testids), not a
functional defect — fixed via `add-data-testid` in this same run.

**Amended during implementation (two confirmed-live AUTOMATION-technique
gotchas, not product defects — Phase 2 exploration, ELITEA-2432):**
1. **CodeMirror markdown list auto-continuation on Enter.** This editor's
   markdown language mode (`@codemirror/lang-markdown`) auto-inserts a
   fresh `"- "` prefix on the line after a list-item line whenever Enter
   is pressed — a real editor UX feature (continue the list for the
   user), not a bug. Driving multi-line list Markdown via
   `page.keyboard.type()` (which dispatches a discrete Enter keydown per
   `\n`) triggers it and corrupts the typed text (confirmed live: typing
   `"- Item one\n- Item two"` via `type()` rendered as
   `"- Item one\n- - Item two"`). Fix: a new page-object method,
   `SkillFormPage.fill_instructions_markdown()`, uses
   `Keyboard.insert_text()` instead of `Keyboard.type()` for the
   insertion step (same `select_text()` + Backspace clear as
   `fill_instructions()`) — `insert_text()` inserts the whole string as
   one atomic operation with no discrete Enter keydown, so the
   continuation keymap never fires, while still triggering the editor's
   real input handling. `fill_instructions()` itself is untouched
   (additive-only) — it remains correct for the single-line instructions
   every other caller uses.
2. **`text_content()` drops line breaks on multi-line CodeMirror content.**
   `get_instructions()` reads `text_content()`, which concatenates
   CodeMirror's per-line `<div class="cm-line">` elements with NO
   separator between them — correct for every other caller's single-line
   instructions, but confirmed live to silently flatten a multi-line
   Markdown source into one unbroken string. Fix: a new page-object
   method, `SkillFormPage.get_instructions_multiline()`, reads
   `inner_text()` instead — Playwright's `inner_text()` is layout-aware
   and inserts a newline between adjacent block-level elements, so it
   reconstructs the editor's real line breaks with no new selector needed
   (each `cm-line` div is already block-level). `get_instructions()`
   itself is untouched (additive-only).
3. A **blank line** (`"\n\n"`) between the bold-text line and the list in
   the original planned test data produced one extra `"\n"` via
   `inner_text()` — CodeMirror appears to render an empty line's `cm-line`
   div with an inner `<br>` that itself contributes a line break beyond
   the normal block-separator newline, so `inner_text()` double-counts an
   empty line. Confirmed live it does NOT affect Preview rendering either
   way. Test data changed to a single `\n` (no blank-line paragraph break)
   to sidestep the ambiguity rather than special-case it — `marked`
   (the Preview renderer) still correctly parses the list without a
   blank-line separator, confirmed live (Preview still renders a real
   `<ul><li>` list from `"...and a list:\n- Item one\n- Item two"`).

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest, confirmed from `.agents/testing.md`.
- Page objects: `SkillDetailPage` (`automation/pages/skill_detail_page.py`,
  extends `SkillFormPage`) — reuses `save_edits()`, pre-existing
  (ELITEA-2431). New additions on `SkillFormPage`, all additive-only (no
  existing method body touched):
  - `instructions_edit_mode_button` / `instructions_preview_mode_button` /
    `instructions_preview_content` `LocatorDescriptor` fields (the toggle
    lives inside the shared Instructions accordion, present on both
    create and edit forms).
  - `click_edit_mode()` / `click_preview_mode()` — click the toggle.
  - `get_preview_content()` — `text_content()` of the Preview container.
  - `fill_instructions_markdown(text)` — Markdown-safe alternative to
    `fill_instructions()`, uses `Keyboard.insert_text()` instead of
    `Keyboard.type()` (see **Amended during implementation** point 1
    above — avoids the CodeMirror list-continuation corruption).
  - `get_instructions_multiline()` — line-break-preserving alternative to
    `get_instructions()`, uses `inner_text()` instead of `text_content()`
    (see point 2 above). `fill_instructions()` / `get_instructions()`
    themselves are unmodified — still correct and used as-is by every
    other caller (single-line instructions).
- Seed via `SkillAPI.create_skill(name, description, instructions)` →
  returns `{"id": ..., ...}`; `skill_id = created["id"]`.
- Re-open by name (name is not edited by this case, unlike ELITEA-2431):
  `SkillsListPage.click_skill_card(name)` (pre-existing, ELITEA-2435)
  followed by `SkillDetailPage.wait_for_page_load()`.
- Preview-content assertion approach: read `get_preview_content()`'s
  `text_content()` and assert it does NOT contain the literal substrings
  `"**Bold text**"` / `"- Item one"` / `"- Item two"` while it DOES contain
  `"Bold text"` / `"Item one"` / `"Item two"` — a content-based check using
  only the one new testid's `text_content()`, no chained sub-selector
  needed (avoids reaching for the `#579` scoped-raw-handle exception
  entirely, since the assertion doesn't need to address the rendered
  `<strong>`/`<li>` nodes individually).
- Test location: `automation/tests/ui/skills/test_skill_management.py`,
  new class `TestSkillInstructionsMarkdownTogglePersistence` — same file as
  `TestEditSkill` (same form, same lifecycle stage: edit-persistence, just
  covering the Edit/Preview toggle specifically instead of the
  Name/Description/Instructions triad).
