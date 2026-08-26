# Test Case: Project Background editor accepts and displays markdown content

## Metadata
- **TMS ID**: ELITEA-2268
- **Source case**: `.agents/automation/settings-w03/cases/ELITEA-2268.md`
  (snapshot; TMS module `settings-project-params`; TMS file
  `settings/project-params/ELITEA-2268_project-background-editor-accepts-and-displays-markdown-cont.md`)
- **Linked Story**: none
- **Priority**: l3 (medium, per case frontmatter). **pytest marker: `@pytest.mark.p2`**
  — project convention: TMS `medium` → AFS `l3_` prefix → pytest `p2`.
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}` = 399), 2026-08-26
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer (Axel), combined analyst+implementer slot
- **Status**: ready-for-automation

## Classification note — declared divergence (reverse-masking guard)

The case calls the control the **"Project Background editor"**. No element, section or
label of that name exists in the product — `grep -rn "Project Background" src/` on both
`origin/main` and `origin/automation/testids` returns two hits, neither a section
heading. The editor the case describes (line-numbered, `</>` / eye icons) is the
**Project Context editor** at `/settings/project-context/edit`. Already filed as
clarification **#1792** by the ELITEA-2266 analysis; no new ticket. The case's
observables are unchanged and all asserted against the live product.

Case step 1 says "Navigate to Settings → Project Context"; the editor is a **separate
route** reached from that page (empty state → **Create**). The test walks that real
user path rather than deep-linking, so the case's step 1 is genuinely executed.

## Preconditions
- User is logged in (localhost dev-token auth).
- The feature is hidden on the **Public** project (`PUBLIC_PROJECT_ID` guard in
  `src/[fsd]/pages/settings/index.jsx`) — the test MUST run against a non-Public
  project. `${ELITEA_PROJECT_ID}` = 399 ("Private") satisfies this.
- **No Project Context exists** for the active project, so `/settings/project-context`
  renders the empty state with its **Create** button (the case's entry point).
  The pre-existing `clean_project_context` fixture
  (`automation/fixtures/data_fixtures.py:2521`) establishes exactly this and tears it
  down afterwards, tolerating the API's 404.

## Test Data
### reuse-existing
- `${ELITEA_PROJECT_ID}` = `399` ("Private").

### generate-per-test
- Markdown body, entered **through the UI** (never seeded):

  ```markdown
  ## Project Overview

  - First bullet
  - Second bullet

  Plain text line.
  ```

  Blank lines are load-bearing: without them CommonMark treats `Plain text line.` as a
  lazy continuation of the second list item (confirmed live — the preview rendered
  `Second bullet\n\nPlain text line.` as ONE `<li>`), which would make the plain-text
  assertion ambiguous.

## Fidelity Declaration

| What is substituted | Transit or terminal | Authority / real observable |
|---|---|---|
| Nothing | — | The content is typed/pasted into the real editor by the test acting as the user; every asserted value (rendered lines, gutter numbers, `contenteditable`, `aria-pressed`, the rendered `<h2>`/`<li>` in preview) is produced by the product. |

`page.evaluate` **is** used, for one thing only: writing the markdown to the system
clipboard so the paste gesture has something to paste (`navigator.clipboard.writeText`).
It writes to the *browser's clipboard*, not to the application's state — the product
still processes the paste through CodeMirror's own transaction pipeline. This is the
pre-existing, reviewed pattern of `ProjectContextPage.set_editor_content_via_paste`
(ELITEA-2272, merged).

**Why paste, not keystrokes:** CodeMirror's `markdown()` extension **auto-continues
list items on Enter**. Typed live 2026-08-26, `pressSequentially` of the body above
produced `- - Second bullet` and `  - Plain text line.` — the editor rewrites the input.
A paste is a single transaction with no Enter keypresses and lands the text verbatim
(confirmed live). This is normal editor behaviour, not a defect; it is a *technique*
choice, and the content asserted is still exactly what the user's gesture put there.

## Test Steps

1. **Setup** — `DELETE` any existing Project Context (tolerate 404) via
   `clean_project_context`, so the empty state renders.
2. Navigate to `${BASE_URL}/settings/project-context` (bare path — project convention),
   then click **Create** (`project-context-create-button`).
   - **Verify**: URL is `${BASE_URL}/settings/project-context/edit` (case step 1–2:
     the page loads and the editor responds by opening).
   - **Verify**: `project-context-editor-content` is visible.
3. Click inside the editor and paste the markdown body (case steps 2–3).
   - **Verify**: the editor's rendered lines are exactly
     `["## Project Overview", "", "- First bullet", "- Second bullet", "", "Plain text line."]`
     — i.e. the field accepted the input and displays it **verbatim**, markdown syntax
     characters included.
4. **Line numbers** (case step 4).
   - **Verify**: the CodeMirror line-number gutter is visible and its rendered numbers
     start `1, 2, 3, …` and cover every content line (6 lines ⇒ `1..6`).
     CodeMirror owns that DOM ⇒ **#579 exception 2**, scoped to the app-owned
     `project-context-editor-wrapper` testid via the existing
     `ProjectContextPage.line_number_gutter()`.
5. **Editable inline, not read-only** (case step 5).
   - **Verify**: `project-context-editor-content` carries `contenteditable="true"`
     (CodeMirror's own read-only rendering sets it to `false`; the product wires
     `readOnly={!canEdit}`).
   - **Verify** (behavioural, stronger than the attribute alone): typing one more
     character in place appends it to the last line, and the character counter drops by
     one — the field really accepts inline editing.
6. Click the **preview (eye)** icon `project-context-mode-preview-button` (case step 6).
   - **Verify**: it becomes the selected mode (`aria-pressed="true"`) and the code-view
     button becomes `aria-pressed="false"`.
   - **Verify**: the CodeMirror editor is **gone** (`project-context-editor-content`
     count 0) — the control responded, the pane switched.
7. **Markdown renders formatted in preview** (case step 7). Scope everything to
   `project-context-preview` (*added during implementation — EliteaAI/EliteaUI@5681f22e*)
   — the app sidebar renders its own `<li>` elements, so an unscoped handle cannot
   disambiguate.
   - **Verify**: the preview contains an `<h2>` whose text is exactly `Project Overview`
     (the `##` became a real heading element).
   - **Verify**: it contains exactly two `<li>` elements, `First bullet` and
     `Second bullet`.
   - **Verify**: its text contains `Plain text line.` and contains **neither** `##`
     **nor** `- First bullet` — the syntax characters were consumed by the renderer.
   `<h2>`/`<li>` are react-markdown's own output ⇒ **#579** (third-party library
   internal render nodes; explicitly named in `.agents/testing.md` § Locator policy),
   scoped to the `project-context-preview` testid parent.
8. Click the **code view (`</>`)** icon `project-context-mode-edit-button` (case step 8).
   - **Verify**: it becomes `aria-pressed="true"`, preview `aria-pressed="false"`.
9. **Raw markdown source is shown again** (case step 9 — the case's Expected Final State).
   - **Verify**: `project-context-preview` count 0 and `project-context-editor-content`
     is visible again.
   - **Verify**: the editor's rendered lines are byte-identical to step 3's list, with
     the extra character from step 5 appended to the last line — the raw source, markers
     and all, survived the round-trip through preview.
10. **Teardown** — `DELETE` the Project Context (tolerate 404). Nothing is ever saved by
    this test, so teardown is belt-and-braces.

## Concrete Handles

| Element | Handle (testid) | Provenance | Verified |
|---|---|---|---|
| Empty-state Create button | `project-context-create-button` | **on-main ✓** | live 2026-08-26 |
| Editor content (`.cm-content`) | `project-context-editor-content` (via `contentTestId`) | **on-main ✓** | live 2026-08-26 |
| Char counter | `project-context-char-counter` | **on-main ✓** | live 2026-08-26 |
| Editor wrapper (gutter scope) | `project-context-editor-wrapper` | on `automation/testids` only (EliteaAI/EliteaUI@b05bbc9a; awaiting human promotion to main) | live 2026-08-26 |
| Code-view (`</>`) mode button | `project-context-mode-edit-button` | on `automation/testids` only (EliteaAI/EliteaUI@b05bbc9a) | live 2026-08-26 |
| Preview (eye) mode button | `project-context-mode-preview-button` | on `automation/testids` only (EliteaAI/EliteaUI@b05bbc9a) | live 2026-08-26 |
| **Preview pane (markdown render container)** | `project-context-preview` | on `automation/testids` only — **added during this case's implementation**, EliteaAI/EliteaUI@5681f22e; awaiting human promotion to main | live 2026-08-26 |
| Line-number gutter | *(no testid — #579 exc. 2)* `.cm-gutters` scoped to `project-context-editor-wrapper` | CodeMirror-internal | live 2026-08-26 |
| Rendered heading / list items | *(no testid — #579)* `h2` / `li` scoped to `project-context-preview` | react-markdown-internal | live 2026-08-26 |

**Provenance verified with a fresh fetch** (`cd ../EliteaUI && git fetch origin`,
2026-08-26), two-stage grep per `.agents/workflow.md` § Closure record:

```
project-context-create-button              main:YES  testids:YES
project-context-editor-content             main:YES  testids:YES
project-context-char-counter               main:YES  testids:YES
project-context-editor-wrapper             main:no   testids:YES
project-context-mode-edit-button           main:no   testids:YES
project-context-mode-preview-button        main:no   testids:YES
project-context-preview                    main:no   testids:YES   (added by this case)
```

**Not touched by this case** (add no testid): Import, Copy, Build-with-AI, Save/Discard
(asserted by ELITEA-2273/2274/2275, not here), the breadcrumb links.

## Coverage Map

### Axis 1 — every case element

| # | Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|---|
| 1 | Navigate to Settings → Project Context | page loads | Step 2 | empty state renders; Create opens the editor route | covered |
| 2 | Click inside the Project Background editor | control responds | Steps 2–3 | editor visible, click focuses it, paste lands | covered (name divergence: it is the Project Context editor — #1792) |
| 3 | Enter markdown with headings, bullets, plain text | field accepts + displays it | Step 3 | per-line equality on the editor's rendered lines | asserted |
| 4 | Editor shows line numbers alongside the content | holds | Step 4 | gutter visible, numbers `1..6` | asserted |
| 5 | Content is editable inline (not read-only) | holds | Step 5 | `contenteditable="true"` + a real keystroke lands | asserted |
| 6 | Click the preview (eye) icon | control responds | Step 6 | `aria-pressed` flips; editor unmounts | asserted |
| 7 | Content renders as formatted markdown in preview | holds | Step 7 | scoped `<h2>` exact text, two `<li>`, no `##`/`-` markers | asserted |
| 8 | Click the code view (`</>`) icon | control responds | Step 8 | `aria-pressed` flips back | asserted |
| 9 | Raw markdown source is shown in the editor | holds (final state) | Step 9 | preview gone, editor back, lines byte-identical incl. `##`/`-` | asserted |
| P | Precondition: user logged in | — | Setup | `auth_state` | covered |

### Axis 2 — observables asserted beyond the case

| Observable | Why |
|---|---|
| The editor **unmounts** in preview mode (count 0) and the preview pane unmounts in code view | The case says "the content renders as formatted markdown *in preview mode*" — asserting the mutual exclusivity turns a two-pane guess into a pinned contract, and it is what makes step 9's "raw source is shown" non-trivial. |
| Character counter decrements on the extra keystroke | Free, and it is the product's own evidence that the edit reached application state, not just the DOM. |
| Absence of `##` / `- First bullet` in the preview text | The positive `<h2>`/`<li>` assertions alone would still pass if the renderer *also* leaked raw syntax; the negative pins "formatted", which is the case's actual word. |
| No console errors across the run | Standard side-channel check on this surface (`utils/console_errors.collect_console_errors`). |

## Known Defects
- **#1792 (case text)** — "Project Background" naming, above. Pre-existing, not re-filed.

## Blocked Steps
None — every step above was executed live and observed 2026-08-26.
