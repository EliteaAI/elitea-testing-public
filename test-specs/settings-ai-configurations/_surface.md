# Surface digest — settings-ai-configurations

The **"AI Configurations" accordion on Settings → General** (`/settings/project-general`),
NOT the AI Providers page. Confirmed live on `http://localhost:5173`
(`EliteaAI/EliteaUI` on `automation/testids`, DEV backend), 2026-08-29, by
qa-engineer analyst, batch `settings-w10`, cluster ELITEA-2393 / ELITEA-2394
(+ ELITEA-2417, which turned out to live on a different surface — see
`test-specs/settings-ai-providers/_surface.md`). Handle cache — verify an entry
against the app before trusting it; not a substitute for execution.

## Page identity — "Settings → AI Configuration" is TWO different things

There is **no page or nav item called "AI Configuration"** anywhere in the app
(the settings drawer's PROJECT group is General / AI Providers / Project Context /
Secrets / Users* / Analytics* / Usage*). TMS cases that say "Settings → AI
Configuration" resolve to one of two unrelated surfaces:

| What the case describes | Where it actually lives |
|---|---|
| LLM / Embedding / Vector Storage / Image Generation / ASR / TTS / **AI Credentials** sections, the "+" provider-create flow | Settings → **AI Providers** (`/settings/ai-providers`) — see `test-specs/settings-ai-providers/_surface.md` |
| **Basic / OpenAI Template** tabs, `OpenAI-BaseURL` / `Server URL` / `OpenAI-Project` / `Project ID` fields, the code template | Settings → **General** (`/settings/project-general`) → the **"AI Configurations"** accordion — THIS digest |

Component tree: `ProjectGeneralContent.jsx` (`data-testid="ai-configurations"` on
the `BasicAccordion`) → `ProjectAIConfigurations.jsx` (holds `selectedTab` in
`useState`, default `Basic`) → `AIConfigurationToggle.jsx` (the two-button
`Tab.TabGroupButton`) → either `AIConfiguration.jsx` (Basic) or
`open-ai-template/OpenAITemplate.jsx` → `CodePreview.jsx` →
`CodePreviewHeader.jsx` + `CodePreviewContent.jsx` (CodeMirror) /
`CodePreviewEmpty.jsx`.

Tab labels are `ProjectGeneralConstants.AIConfigurationTabs = { Basic: 'Basic',
OpenAITemplate: 'OpenAI Template' }` — **the left tab is "Basic", never "AI
Configuration"** (ELITEA-2393's step 5 says otherwise: case-text drift,
clarification filed).

## Confirmed live behaviour (2026-08-29)

- The **accordion is expanded by default** on page load and after clicking the
  sidebar Settings button (`aria-expanded="true"` on its `MuiAccordionSummary`);
  `Basic` is the pre-selected tab (`aria-pressed="true"`).
- **Basic tab** renders four `FieldWithCopy` rows, values observed on project
  `UI Testing` (id 400):
  | Label | Value observed | Source (`AIConfiguration.jsx`) |
  |---|---|---|
  | `OpenAI-BaseURL:` | `https://dev.elitea.ai/llm/v1` | `` `${user.api_url.replace('/api/v2','')}/llm/v1` `` else `Not configured` |
  | `Server URL:` | `https://dev.elitea.ai` | `user.api_url` else `Not configured` |
  | `OpenAI-Project:` | `1` | `model.project_id` — **conditionally rendered**, the whole row is absent when the project has no default LLM model |
  | `Project ID:` | `400` | `useSelectedProjectId()` else `Not configured` |
- **`OpenAI-Project` is the DEFAULT LLM MODEL's project id, not the selected
  project's** — it read `1` (the shared/public project) while `Project ID` read
  `400`. Do not assert the two are equal.
- Switching to **OpenAI Template** unmounts the Basic fields and mounts a
  read-only CodeMirror editor: 23 lines / ~485 chars of Python observed, headed by
  a `Model:` and a `Code:` `Select.SingleSelect` (defaults: the project's default
  LLM display name, `Python`). The code embeds the same values the Basic tab
  shows — `base_url="https://dev.elitea.ai/llm/v1"`, `project="1"`,
  `model="gpt-5.6-luna"`, `api_key="Your_Personal_Token"` (a literal placeholder,
  never a real token).
- Switching back to **Basic** unmounts the editor (`.cm-editor` count 0) and the
  four fields return. Tab state is component-local `useState` — **a page reload
  resets it to Basic**, and there is no URL/query reflection of the selected tab.
- `CodePreviewEmpty` ("Select a LLM Model to see Code examples") renders instead
  of the editor when the project has no default LLM model — not observed live
  (every project tried had one), so treat it as the documented alternative branch,
  not a verified one.
- Console: **0 errors** on load, after both tab switches, on `/settings/project-general`.

## Testids

**Pre-existing (verified with `git fetch origin`, 2026-08-29):**

| Testid | on `main` | on `automation/testids` |
|---|---|---|
| `ai-configurations` (accordion root) | YES | YES |
| `project-general-section` | YES | YES |
| `settings-nav-item-{tabId}` + `data-active`, `settings-content`, `settings-drawer`, `sidebar-settings-button` | no | YES |

**Needed — none of the accordion's own interactive/asserted nodes carries one**
(`document.querySelectorAll('[data-testid]')` inside `ai-configurations` returned
only an MUI icon):

| Testid to add | Element | How (no plumbing required) |
|---|---|---|
| `ai-configuration-tab-basic-button` | "Basic" toggle | `arrayBtn[].buttonProps: { 'data-testid': ... }` in `AIConfigurationToggle.jsx` — the exact mechanism `ProjectContextEditor.jsx:86,92` already uses (`project-context-mode-edit-button`) |
| `ai-configuration-tab-openai-template-button` | "OpenAI Template" toggle | same |
| `ai-configuration-openai-base-url-value` | Basic value `<Typography>` | `FieldWithCopy` **already accepts a `testId` prop** (`ai-providers/FieldWithCopy.jsx`, lands as `data-testid` on the value node) — pass it at the four `AIConfiguration.jsx` call sites; zero component changes |
| `ai-configuration-server-url-value` | " | same |
| `ai-configuration-openai-project-value` | " | same |
| `ai-configuration-project-id-value` | " | same |
| `ai-configuration-code-preview-editor` | CodeMirror container | one `data-testid` on `CodePreviewContent.jsx`'s wrapping `Box` |

State is read from the toggle's **`aria-pressed`** (`true`/`false`) — a stable
testid plus a state attribute, per `.agents/testing.md` § Locator policy. Never
add `-active`/`-inactive` testid variants.

## Network

`/settings/project-general` fires, per page load (all 200 on both projects tried):
`GET /api/v2/configurations/models/{project_id}?include_shared=true&section={llm|
embedding|vectorstorage|image_generation|asr|tts}` (one per section) plus the
combined `GET /api/v2/configurations/configurations/{project_id}?…&section=llm&…`.
**Switching tabs fires no request** — both panels are fed by the same already-cached
RTK-Query results, so a tab click is a pure client-side re-render (do not wait on
network after it; wait on the target panel's testid).

The `{project_id}` path segment of those GETs is the honest oracle for the
`Project ID` field — the product's own request, not a constant the test chose.

## Gotchas

- **The selected project is browser-persisted and is NOT necessarily 399.** This
  session opened on `UI Testing` (400); `settings-navigation/_surface.md`'s
  earlier session was on `Private` (399). Never hardcode `400`/`399` in an
  assertion — read the id from the page's own request URL (above) or from
  `settings.elitea_project_id`, and switch deliberately via
  `SettingsProjectGeneralPage.switch_project()` if the case needs a specific one.
- **Do not `fetch()` the API from `browser_evaluate` on localhost** — the dev
  proxy 302s to `dev.elitea.ai/forward-auth/...` and the browser logs 2 CORS
  `console.error`s per call. It pollutes the very console-error assertion these
  cases make (cost this session 6 self-inflicted errors). Read the values off
  `page.expect_response` / the network log instead.

## AFS files from this run

- `l2_ai-configuration-environment-metadata-fields_ELITEA-2394.md` — ready-for-automation
- `l3_openai-template-tab-loads-code-template_ELITEA-2393.md` — ready-for-automation

Not a family AFS: they differ in **steps** (static field inventory on the default
tab vs a tab round-trip asserting two different panels), not only in data.

---

## Resolved/added during ELITEA-2393 / ELITEA-2394 implementation (2026-08-29, test-automation-engineer)

**Every "Needed" testid above now exists on `automation/testids`**, plus two the
analyst pass could not have known were required:

| Testid | Commit | Note |
|---|---|---|
| `ai-configuration-tab-basic-button` | EliteaAI/EliteaUI@2deb9655 | `arrayBtn[].buttonProps`, as predicted |
| `ai-configuration-tab-openai-template-button` | EliteaAI/EliteaUI@2deb9655 | same |
| `ai-configuration-openai-base-url-value` | EliteaAI/EliteaUI@2deb9655 | `FieldWithCopy` `testId` prop, as predicted |
| `ai-configuration-server-url-value` | EliteaAI/EliteaUI@2deb9655 | same |
| `ai-configuration-openai-project-value` | EliteaAI/EliteaUI@2deb9655 | same |
| `ai-configuration-project-id-value` | EliteaAI/EliteaUI@2deb9655 | same |
| `ai-configuration-code-preview-editor` | EliteaAI/EliteaUI@2deb9655 | `CodePreviewContent.jsx` wrapper `Box`, as predicted |
| **`ai-configuration-accordion-summary`** | EliteaAI/EliteaUI@2deb9655 | **NEW — the digest's "expand state on its `MuiAccordionSummary` `aria-expanded`" is not reachable from `ai-configurations`.** `BasicAccordion` puts the `data-testid` it receives on its OUTER `Box` and exposes the summary through a *separate* `items[].testId` prop. Any future case asserting an accordion's expand state on this app needs the `items[].testId`, not the accordion's own `data-testid`. |
| **`ai-configuration-code-preview-empty`** | EliteaAI/EliteaUI@7418c06f | **NEW — `CodePreviewEmpty.jsx`'s container `Box`.** ELITEA-2393 asserts the empty branch's ABSENCE; a testid + `to_have_count(0)` is the sanctioned shape (`.agents/testing.md` § Locator policy, #511 extension), and it beats matching the empty state's prose. |

Other implementation-time facts:

- **No spinner exists anywhere in `AIConfiguration.jsx`**, so ELITEA-2394's
  "no permanent loading spinner" is asserted through a role-scoped child handle
  (`[data-testid="ai-configurations"] [role="progressbar"]`, count 0) — a
  declared improvisation, documented on
  `SettingsAIConfigurationPage.panel_progress_indicators()`. There is no JSX node
  to add a testid to, so "add the testid" is not an available action here.
- **`page.expect_response` across the sidebar Settings click is a reliable oracle
  for the selected project id** — the `configurations/models/{project_id}?…
  &section=llm` request fires on every settings load and its last path segment is
  the project id the `Project ID` field must equal. Implemented as
  `SettingsAIConfigurationPage.open_via_sidebar()` (returns the `Response`) +
  `project_id_from_models_url()`.
- **Both specs went green first try, 2/2 in 16.16 s, `reruns.json == {}`.** No
  flake observed on this surface; `BasePage.navigate`'s tolerant `networkidle`
  wrapper is the only network wait involved and it did not fire (#1847 did not
  bite here).
- Both specs carry the URL-keyed `#1971` console filter
  (`TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL`), because both drive
  project-scoped navigation — #1971's documented trigger. It did not fire in the
  green run; it is pre-emptive and narrow (never a status-code filter).

Page object: `automation/pages/settings_ai_configuration_page.py`
(`SettingsAIConfigurationPage`). Specs:
`automation/tests/ui/settings/test_ai_configuration_metadata_fields.py` (2394),
`automation/tests/ui/settings/test_ai_configuration_openai_template_tab.py` (2393).
