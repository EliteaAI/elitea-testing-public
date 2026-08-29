# Test Case: OpenAI Template tab loads code template content

## Metadata
- **TMS ID**: ELITEA-2393
- **Linked Story**: none
- **Priority**: l3 (case priority `medium`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (auth via `auth_state` / `VITE_DEV_TOKEN` on localhost)
- **Analyst**: qa-engineer (Sage), batch `settings-w10`, 2026-08-29
- **Status**: ready-for-automation (behaviour is exactly as the case describes;
  drift is in the NAMES of the page and of the return tab)
- **Surface digest**: `test-specs/settings-ai-configurations/_surface.md`
- **Filed**: clarification **EliteaAI/elitea-testing-public#1981** (see
  § Known Defects) — the case's step 5 return tab is called **"Basic"**, not
  "AI Configuration", and the panel lives on Settings → General, not on a page
  named "AI Configuration".
- **Cluster**: dispatched with ELITEA-2394 (same surface, one live session) and
  ELITEA-2417 (diverged onto the AI Providers surface). 2393/2394 differ in
  **steps**, so each has its own AFS.

---

## Case-identity note — read before implementing

"Settings → AI Configuration" is the **"AI Configurations" accordion on Settings
→ General** (`/settings/project-general`), not a page of that name and not
Settings → AI Providers. Inside it a two-button toggle switches between
**"Basic"** (the environment metadata fields — ELITEA-2394's subject) and
**"OpenAI Template"** (a read-only code sample). The case's step 5 ("click back
to the AI Configuration tab") means **click back to "Basic"**; the phrase
"the integrations content returns" means the four metadata fields render again.

## Preconditions
- User logged in (`auth_state`).
- The selected project has a **default LLM model** configured — otherwise the
  template panel renders `CodePreviewEmpty` ("Select a LLM Model to see Code
  examples") instead of an editor and the case's step 4 is unreachable. Verified
  present on every project tried live; assert it via the `section=llm` response's
  `default_model_name` if a run ever hits the empty branch.

## Test Data
### reuse-existing
None. Read-only — the code template is generated client-side from the project's
own configuration, and `api_key` is the literal placeholder
`"Your_Personal_Token"` (no real secret is ever rendered).

---

## Test Steps

1. **Navigate to Settings → General and locate the AI Configurations panel
   (case step 1).**
   - `page.goto` `${BASE_URL}/settings/project-general` (or click
     `sidebar-settings-button`).
   - **Verify**: `ai-configurations` is visible and its summary carries
     `aria-expanded="true"`.
   - **Verify**: `ai-configuration-tab-basic-button` carries
     `aria-pressed="true"` (starting state — needed so step 5's "returns" is a
     real round-trip and not a no-op).
   - **Verify**: `ai-configuration-openai-base-url-value` is visible (the Basic
     panel is genuinely mounted before the switch).

2. **Click the "OpenAI Template" tab (case step 2).**
   - Click `ai-configuration-tab-openai-template-button`.
   - No network request fires on a tab switch — wait on the editor testid, never
     on `networkidle` (`.agents/testing.md` #1847).

3. **Verify the tab becomes active (case step 3).**
   - **Verify**: `ai-configuration-tab-openai-template-button` carries
     `aria-pressed="true"`.
   - **Verify**: `ai-configuration-tab-basic-button` carries
     `aria-pressed="false"` — exclusive selection, not both-on.
   - **Verify**: `ai-configuration-openai-base-url-value` has count 0 — the Basic
     panel unmounted (the two panels are mutually exclusive renders).

4. **Verify the content area shows a non-empty code template (case step 4).**
   - **Verify**: `ai-configuration-code-preview-editor` is visible.
   - **Verify**: its `inner_text()` stripped is non-empty and at least ~100
     characters (observed 485 chars / 23 lines live — a generous floor that still
     fails on an empty or single-line editor).
   - **Verify**: the text contains `from openai import OpenAI` and
     `client = OpenAI(` — it is the OpenAI code template specifically, not
     arbitrary text. (Language selector default is `Python`; the case does not
     change it.)
   - **Verify**: the text contains `base_url="` followed by the same value the
     Basic tab showed for `OpenAI-BaseURL` (captured in step 1) — the template is
     generated from this project's real configuration, not a static blob. This is
     the honest, environment-independent form of "loads code template content".
   - **Verify**: the empty-state text `Select a LLM Model to see Code examples`
     has count 0 (`CodePreviewEmpty`'s branch is NOT what rendered).

5. **Click back to the "Basic" tab and verify the metadata content returns
   (case step 5 / Expected Final State).**
   - Click `ai-configuration-tab-basic-button`.
   - **Verify**: `ai-configuration-tab-basic-button` carries `aria-pressed="true"`
     and the OpenAI Template button `aria-pressed="false"`.
   - **Verify**: `ai-configuration-code-preview-editor` has count 0 (editor
     unmounted).
   - **Verify**: all four value testids (`…openai-base-url-value`,
     `…server-url-value`, `…openai-project-value`, `…project-id-value`) are
     visible again and their texts equal what step 1 captured — "returns"
     means the same content, not merely *some* content.
   - **Verify**: zero console errors across the whole round-trip (observed clean
     live, including both switches).

---

## Expected Results
- The OpenAI Template tab activates exclusively and renders a populated,
  read-only Python code template derived from the project's own AI configuration.
- Clicking back to Basic restores the four metadata fields unchanged and unmounts
  the editor.
- No console errors at any point.

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result (case) | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` fixture | fixture | asserted (setup) |
| Step 1 — Navigate to Settings → AI Configuration | page/section loads | step 1 | step 1 | **clarification** — asserted as the live location (Settings → General → "AI Configurations" accordion) |
| Step 2 — Click the "OpenAI Template" tab | control responds | step 2 | step 2 (settled by step 3/4 assertions) | asserted |
| Step 3 — Verify the tab becomes active | condition holds | step 3 | step 3 | asserted (`aria-pressed`, both buttons) |
| Step 4 — content area shows a code template (non-empty) | condition holds | step 4 | step 4 | asserted (visible + length floor + OpenAI-specific content + derived-from-config check + empty-branch absence) |
| Step 5 / Expected Final State — click back to "AI Configuration" tab, integrations content returns | control responds, expected state | step 5 | step 5 | **clarification** — the return tab is labelled **"Basic"**; "integrations content" = the four metadata fields, asserted equal to the pre-switch capture |

### Axis 2 — observables asserted beyond the case

| Extra observable | Why it is grounded |
|---|---|
| Basic panel absent while OpenAI Template is active (and vice versa) | The two panels are mutually exclusive renders in `ProjectAIConfigurations.jsx`; asserting only the newly-shown one would pass if both rendered at once — a real, invisible regression. |
| Code template contains the Basic tab's own `OpenAI-BaseURL` | Turns "non-empty text" into proof the template is generated from this project's configuration, with no environment-specific literal in the test. |
| `CodePreviewEmpty` text absent | The empty branch also renders non-empty text inside the panel; without this the length check could pass on the "no model selected" state. |
| Field values identical before and after the round-trip | "Content returns" is only meaningful as *the same* content; catches a remount that loses or re-derives values wrongly. |
| Zero console errors | Side-channel check; the surface was clean live. |

---

## Cleanup
None — read-only. Tab state is component-local `useState` and resets to "Basic"
on the next mount, so nothing leaks to the next test.

## Concrete Handles

| Element | Primary handle (testid-only) | Provenance (verified `git fetch origin`, EliteaUI, 2026-08-29) | Notes |
|---|---|---|---|
| AI Configurations accordion | `ai-configurations` | **on `main` ✓** and `automation/testids` | `ProjectGeneralContent.jsx` |
| "Basic" tab | `ai-configuration-tab-basic-button` | **needs-adding** | `AIConfigurationToggle.jsx` `arrayBtn[].buttonProps` — precedent `project-context-mode-edit-button` (`ProjectContextEditor.jsx:86`). State via `aria-pressed`, never a state-named testid. |
| "OpenAI Template" tab | `ai-configuration-tab-openai-template-button` | **needs-adding** | same |
| Code template editor container | `ai-configuration-code-preview-editor` | **needs-adding** | one `data-testid` on `CodePreviewContent.jsx`'s wrapping `Box`. Read the code with `inner_text()` on this container — do **not** address CodeMirror's internal `.cm-line` nodes (library-internal; the #579 exception exists but is unnecessary here). |
| Four Basic values | `ai-configuration-{openai-base-url,server-url,openai-project,project-id}-value` | **needs-adding** | `FieldWithCopy` already accepts `testId`; pass at the `AIConfiguration.jsx` call sites (shared with ELITEA-2394 — add once) |

## Network Behavior
- Page load: the seven `configurations/models/{project_id}` GETs + the combined
  `configurations/configurations/{project_id}` GET, all 200.
- **Tab switches fire nothing** — both panels consume the same cached RTK-Query
  data. Wait on testids, not on network.

## Known Defects Found During Exploration
None — the flow behaves exactly as the case describes.

Case-text drift (NOT a product defect, per the reverse-masking guard) filed as a
clarification `question` issue: the case names a nonexistent "AI Configuration"
page and calls the return tab "AI Configuration" when it is labelled "Basic".
Related, already-open siblings: #1250 (ELITEA-2392 — same nonexistent page name,
different surface), #1772 (settings drawer inventory), #1906 (ELITEA-2346 — the
AI-provider "+" flow).

## Blocked Steps
None.

## Known traps
- **"AI Configuration tab" in step 5 is "Basic" in the product.** Do not write the
  case's wording into the assertion or the docstring.
- **A page reload resets the tab to Basic** (component-local `useState`, no URL
  reflection) — never reload between steps 2 and 5.
- **No network settle after a tab click.** `networkidle` is unusable here anyway
  (persistent Socket.IO polling, #1847).
- **Do not probe the API with `fetch()` from the browser** — the dev proxy 302s
  to an external auth host and logs CORS console errors that would break this
  case's own console-error assertion.
