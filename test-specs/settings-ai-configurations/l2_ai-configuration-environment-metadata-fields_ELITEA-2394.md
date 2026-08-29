# Test Case: Settings landing — the AI Configurations panel shows correct environment metadata fields

## Metadata
- **TMS ID**: ELITEA-2394
- **Linked Story**: none
- **Priority**: l2 (case priority `high`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (auth via `auth_state` / `VITE_DEV_TOKEN` on localhost)
- **Analyst**: qa-engineer (Sage), batch `settings-w10`, 2026-08-29
- **Status**: ready-for-automation (case-text drift on the page/tab NAME only —
  every observable the case asks for exists and is correct)
- **Surface digest**: `test-specs/settings-ai-configurations/_surface.md`
- **Filed**: no new issue — the "AI Configuration is selected and active by
  default" drift is the same root cause already tracked by clarification
  **EliteaAI/elitea-testing-public#1772** (row 3); a new occurrence comment was
  added there rather than a duplicate ticket.
- **Cluster**: dispatched with ELITEA-2393 (same surface, one live session) and
  ELITEA-2417 (diverged — different surface, see its own AFS). 2393 and 2394
  differ in **steps**, so each has its own AFS.

---

## Case-identity note — read before implementing

The case says *"Click Settings in the left sidebar"* → *"AI Configuration is
selected and active by default"*. Live, there is **no "AI Configuration" nav item
at all**. The sidebar Settings button hardcodes `/settings/project-general`
("General"), and the four fields the case enumerates
(`OpenAI-BaseURL`, `Server URL`, `OpenAI-Project`, `Project ID`) live inside the
**"AI Configurations" accordion on that General page** — expanded by default,
with its **"Basic"** tab pre-selected. So the case's *intent* ("land on Settings,
the AI-configuration panel is showing, its metadata fields are populated") is
satisfied exactly; only the names are stale. Asserting the live contract per the
reverse-masking guard.

Do **not** confuse this panel with Settings → **AI Providers**
(`/settings/ai-providers`), which is where the LLM/Embedding/AI-Credentials
*sections* live (ELITEA-2392's AFS).

## Preconditions
- User logged in (`auth_state`). The case's "Admin role" is satisfied by
  `${TEST_USER}` on its own projects; nothing on this panel is role-gated (no
  permission check exists in `AIConfiguration.jsx`).
- A project is selected (any). The values are project-scoped but the assertions
  below are project-agnostic (see § Known traps).

## Test Data
### reuse-existing
None. Read-only.

---

## Test Steps

1. **Navigate away from Settings, then click "Settings" in the left sidebar
   (case steps 1–2).**
   - Start on a non-settings route (e.g. `/agents/all`) so the click is a real
     navigation, then click `sidebar-settings-button`.
   - **Verify**: URL is `${BASE_URL}/settings/project-general`.
   - **Verify**: `settings-nav-item-project-general` carries `data-active="true"`.

2. **Verify the AI-configuration panel is showing and active by default
   (case step 3, asserted against the live names).**
   - **Verify**: `ai-configurations` (the accordion) is visible and its summary
     button carries `aria-expanded="true"` — i.e. the panel is open without any
     user action.
   - **Verify**: `ai-configuration-tab-basic-button` carries
     `aria-pressed="true"` and `ai-configuration-tab-openai-template-button`
     carries `aria-pressed="false"` — "Basic" is the default active tab.

3. **Verify the four environment metadata fields render with non-empty values
   (case steps 4–8).**
   - **Verify**, for each of `ai-configuration-openai-base-url-value`,
     `ai-configuration-server-url-value`, `ai-configuration-openai-project-value`,
     `ai-configuration-project-id-value`: the element is visible and its text is
     non-empty after stripping whitespace.
   - **Verify**: the corresponding labels `OpenAI-BaseURL:`, `Server URL:`,
     `OpenAI-Project:`, `Project ID:` are present in the `ai-configurations`
     panel text (proves the value nodes are the ones the case names, not just
     four arbitrary populated nodes).

4. **Verify no value is "undefined", blank, or a permanent loading state
   (case step 9 / Expected Final State).**
   - **Verify**, for each of the four values: the text does not equal (case
     insensitively) `undefined`, `null`, `NaN`, `Not configured`, and is not the
     empty string. (`Not configured` is `AIConfiguration.jsx`'s own fallback for
     a missing `user.api_url` / `projectId` — it is exactly the "blank" state the
     case forbids, rendered as words.)
   - **Verify**: zero `[role="progressbar"]` / MUI `CircularProgress` nodes
     inside `ai-configurations` once the values are visible — no permanent spinner.
   - **Verify**: `Project ID` equals the `{project_id}` path segment of the page's
     own `GET …/configurations/models/{project_id}?…&section=llm` request,
     captured with `page.expect_response` during step 1's navigation — the
     product's own value, not a constant the test chose.
   - **Verify**: `OpenAI-BaseURL` == `Server URL` with any trailing `/api/v2`
     stripped, plus `/llm/v1` — the product-internal invariant
     `AIConfiguration.jsx` computes; catches a regression that leaves one of the
     two stale or malformed without pinning an environment-specific literal.
   - **Verify**: zero console errors on this page (observed clean live).

---

## Expected Results
- Clicking Settings lands on `/settings/project-general` with General active.
- The "AI Configurations" accordion is expanded with the "Basic" tab active,
  without any user interaction.
- All four metadata fields render with real, non-placeholder values.
- No `undefined`/blank/`Not configured` value, no spinner left behind, no console
  errors.

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result (case) | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` fixture | fixture | asserted (setup) |
| Step 1 — Log in as a user with Admin role | authenticated, lands on expected page | step 1 | step 1 | asserted (role is not a differentiator on this panel — nothing here is permission-gated; see § Preconditions) |
| Step 2 — Click "Settings" in the left sidebar | control responds, next state shown | step 1 | step 1 | asserted |
| Step 3 — "AI Configuration" selected and active by default | condition holds | step 2 | step 2 | **clarification (#1772)** — asserted as the live equivalent: General tab active + AI Configurations accordion expanded + "Basic" tab pressed |
| Step 4 — main content area shows the following fields with non-empty values | condition holds | step 3 | step 3 | asserted |
| Step 5 — OpenAI-BaseURL | expected UI state | step 3 + 4 | step 3, 4 | asserted |
| Step 6 — Server URL | expected UI state | step 3 + 4 | step 3, 4 | asserted |
| Step 7 — OpenAI-Project | expected UI state | step 3 + 4 | step 3, 4 | asserted (**conditional row** — see § Known traps) |
| Step 8 — Project ID | expected UI state | step 3 + 4 | step 3, 4 | asserted |
| Step 9 / Expected Final State — no "undefined", blank, or permanent loading spinner | condition holds | step 4 | step 4 | asserted |

### Axis 2 — observables asserted beyond the case

| Extra observable | Why it is grounded |
|---|---|
| `Not configured` treated as a failing value | It is the component's own fallback string for a missing `user.api_url`/`projectId` — a rendered-blank. Accepting it would let the case pass on exactly the state it exists to catch. |
| `Project ID` == the project id in the page's own `section=llm` request URL | "Non-empty" alone passes on a stale id from a previous project. Comparing to the product's own concurrent request proves the panel reflects the *selected* project, with no test-authored constant (fidelity: the value comes from the system). |
| `OpenAI-BaseURL` derives from `Server URL` | Pins the documented relationship without hardcoding `dev.elitea.ai`, so the spec survives an environment change and still fails on a real regression. |
| Labels asserted alongside values | Guards against a future reorder/rename silently pointing the four testids at different fields. |
| Zero console errors | Standard side-channel check; this page was clean live, so a strict assertion is honest. |

---

## Cleanup
None — read-only.

## Concrete Handles

| Element | Primary handle (testid-only) | Provenance (verified `git fetch origin`, EliteaUI, 2026-08-29) | Notes |
|---|---|---|---|
| Sidebar "Settings" entry | `sidebar-settings-button` | on `automation/testids` only | `BasePage.sidebar_settings_button` |
| Settings drawer nav item | `settings-nav-item-project-general` + `data-active` | on `automation/testids` only | `SettingsDrawerPage.SETTINGS_NAV_ITEM` |
| AI Configurations accordion | `ai-configurations` | **on `main` ✓** and `automation/testids` | `ProjectGeneralContent.jsx`; expand state on its `MuiAccordionSummary` `aria-expanded` |
| "Basic" tab | `ai-configuration-tab-basic-button` | **needs-adding** | `AIConfigurationToggle.jsx`, via `arrayBtn[].buttonProps: { 'data-testid': … }` — same mechanism as `project-context-mode-edit-button` (`ProjectContextEditor.jsx:86`). State via `aria-pressed`. |
| "OpenAI Template" tab | `ai-configuration-tab-openai-template-button` | **needs-adding** | same |
| `OpenAI-BaseURL` value | `ai-configuration-openai-base-url-value` | **needs-adding** | `FieldWithCopy` already accepts `testId` — pass at the `AIConfiguration.jsx` call site, no component change |
| `Server URL` value | `ai-configuration-server-url-value` | **needs-adding** | same |
| `OpenAI-Project` value | `ai-configuration-openai-project-value` | **needs-adding** | same |
| `Project ID` value | `ai-configuration-project-id-value` | **needs-adding** | same |

New page object suggested: `pages/settings_ai_configuration_page.py`
(`SettingsAIConfigurationPage`) — or extend `SettingsProjectGeneralPage`, which
already owns `/settings` navigation and the project selector. Implementer's call;
do not duplicate the project-selector fields.

## Network Behavior
- On load: `GET /api/v2/configurations/models/{project_id}?include_shared=true[&section=…]`
  ×7 and `GET /api/v2/configurations/configurations/{project_id}?…` — all 200.
- **No request fires on a tab switch** (both panels read the same cached data).
- No mutating requests anywhere in this case.

## Known Defects Found During Exploration
None on this surface (0 console errors, all four fields populated).

## Blocked Steps
None.

## Known traps
- **The `OpenAI-Project` row is conditionally rendered** —
  `{model.project_id && (<Box>…)}`. On a project with no default LLM model the
  whole row is absent, and the correct verdict is "no default model configured",
  not "the field is blank". Every project observed live had one; if the assertion
  ever fails by absence, check the `section=llm` response's
  `default_model_project_id` before calling it a bug.
- **`OpenAI-Project` ≠ `Project ID`.** Observed `1` vs `400` — the former is the
  default *model's* project (the shared/public project), the latter the selected
  project. Never assert equality.
- **Do not hardcode a project id or `dev.elitea.ai`.** The selected project is
  browser-persisted and differed between sessions (400 here, 399 in the
  settings-navigation digest).
- **Do not probe the API with `fetch()` from inside the browser** — the localhost
  dev proxy 302s to an external auth host and the browser logs CORS console
  errors that break the console-error assertion of this very case.
