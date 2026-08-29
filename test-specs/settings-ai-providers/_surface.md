# Settings → AI Providers surface — exploration digest

Handle cache for live-confirmed handles/quirks on the Settings → AI Providers
surface (`/settings/ai-providers`, renders `AIProviders.jsx` →
`AIProvidersContent.jsx` → `ConfigurationsPanel.jsx`). Not a substitute for
execution — verify a handle as you use it. One writer at a time; first
confirmed by: qa-engineer analyst, ELITEA-2392, 2026-08-06.

## Page identity — the TMS case calls this "AI Configuration"; it isn't
The sidebar/settings-nav label is **"AI Providers"** (`SETTINGS_TABS_CONFIG`
id `ai-providers`, `src/[fsd]/pages/settings/index.jsx`), route
`/settings/ai-providers`. There is no page or nav item literally called "AI
Configuration" anywhere in the app. A *different* page — Settings → General
(`/settings/project-general`) → the "AI Configurations" accordion
(`ProjectGeneralContent.jsx`) — has a component named `ProjectAIConfigurations`
with a "Basic"/"OpenAI Template" toggle (`AIConfigurationToggle.jsx`,
`ProjectGeneralConstants.AIConfigurationTabs = { Basic: 'Basic', OpenAITemplate:
'OpenAI Template' }`) but shows only `OpenAI-BaseURL`/`Server URL`/`Project ID`
fields — NOT the LLM/Embedding/Vector Storage/etc. model sections. ELITEA-2392's
case text conflates these two unrelated surfaces (sections from this page + tabs
from that one). Full write-up + filed clarification in
`test-specs/settings-ai-providers/l3_ai-providers-page-sections-load-without-error_ELITEA-2392.md`.

## Section rendering — empty sections hide entirely (by design)
`ConfigurationSection.jsx`: `if (!configurations || configurations.length ===
0) return null;`. A section with zero configured items for the current
project renders NOTHING — no header, no empty-state placeholder. Confirmed
live on the shared `${TEST_USER}` project (`Private`, id 399): Vector Storage
and AI Credentials both return `200` with `items: []` and are simply absent
from the DOM. **(2026-08-29: only Vector Storage still does — AI Credentials now
shows a shared `ELPS` credential on every project; see the ELITEA-2417 section
at the end.)** Do not treat this as a defect or a load failure — verify via
the underlying API response (200 + zero-count) to distinguish "correctly
hidden" from "silently broke".

## Section order (JSX-authored, `ConfigurationsPanel.jsx`)
LLMs → Embedding Models → Vector Storage → Image Generation → Speech
Recognition (ASR) → Text to Speech (TTS) → AI Credentials. Matches the TMS
case's intended order exactly; only the two zero-config sections are absent
in practice for the current shared project.

## Live data observed (Private project / id 399, 2026-08-06)
- LLMs: 11 configs. Default `Anthropic Claude 4.5 Sonnet`, Low-tier
  `GPT-5.4-mini`, High-tier unset (**as of the ELITEA-2392 session — see the
  ELITEA-2397 note below: this session's own exploration left High-tier set
  to `GPT-5.2` on the shared project, could not be reverted via UI**).
  Grouped by provider (OpenAI/Anthropic/
  Azure AI Foundry — `GROUP_ORDER` in `ConfigurationSection.jsx`).

## Tier selectors are LIVE-EDITABLE, no Save button (ELITEA-2397, 2026-08-06)
Clicking a tier selector (`ai-providers-section-llms-{default|high-tier|low-tier}-model-selector-combobox`)
opens a `listbox` of model options (dynamic testid, pre-existing shared
`Select.SingleSelect` convention, NOT added by 2392: `[data-testid="select-option-{model_id}<<>>{value}"]`,
e.g. `select-option-gpt-5.4<<>>1`). Selecting an option immediately fires
`POST /api/v2/configurations/models/{project_id}` (200, body
`{"result": "success"}`) — no separate Save action — and the section's card
list re-renders from the follow-on GET refetch: the newly-selected model's
`ConfigurationCard` gains a "Default"/"High-Tier"/"Low-Tier" badge, the
previously-assigned model's card loses it, all confirmed live within the
same render pass (no manual reload needed). Badge testid: **needs-adding**
(`ConfigurationCard.jsx`'s three conditional `isDefault`/`isHighTier`/
`isLowTier` `Typography` blocks currently carry none).

**No "clear"/unset option exists in the dropdown** — confirmed live, the
`listbox` only ever lists selectable models, never a blank/"None" entry.
Once a tier has a value there is no UI-only way back to "unset". A test
that finds a tier already unset (High-tier, as of this note) cannot restore
that exact state via the UI after selecting something else — needs an API
route or a documented limitation; see the ELITEA-2397 AFS § Cleanup.

**Only the Default tier feeds the plain `/chat` new-conversation model
selector** (`model-selector-button`) — confirmed live end-to-end (changing
Default to `GPT-5.4` changed a brand-new `/chat` composer's selector text to
`GPT-5.4`). High-tier and Low-tier do NOT: grepping `EliteaUI/src` for every
consumer of `high_tier_default_model_name`/`low_tier_default_model_name`
found Low-tier used ONLY by the chat canvas's Mermaid "Quick Fix" AI-assist
action (`src/components/MermaidDiagramOutput/mermaidQuickFixModel.helpers.js`)
and High-tier used by **no frontend code at all** outside the AI Providers
settings display itself. Filed as a case-text clarification:
EliteaAI/elitea-testing-public#1253 (don't assume tier-parity with Default
for any future case touching these selectors).
- Embedding Models: 3 configs, default `text-embedding-3-small`.
- Vector Storage: 0 configs — section absent.
- Image Generation: 3 configs, default `gpt-image-1`.
- Speech Recognition (ASR): 2 configs, default `gpt-4o-mini-transcribe`.
- Text to Speech (TTS): 1 config, default `gpt-4o-mini-tts`.
- AI Credentials: 0 configs — section absent. **STALE as of 2026-08-29 (ELITEA-2417):**
  a SHARED credential (`ELPS`, `OK • Shared`) is now visible on every non-public
  project (`include_shared=true`), so the section renders with count `1` on BOTH
  400 (`UI Testing`) and 399 (`Private`). Vector Storage is still genuinely 0/absent.
- LLMs section auto-expands by default (`defaultExpanded={!expandSection ||
  expandSection === 'llm'}`); all other sections start collapsed
  (`defaultExpanded={expandSection === '<section>'}`, false without a
  `location.state.expandSection`).

## Testid status — ZERO in the ai-providers component tree (confirmed 2026-08-06)
`grep -n "testid\|testId" src/[fsd]/features/settings/ui/ai-providers/*.jsx
src/[fsd]/pages/settings/AIProviders.jsx` → no hits. `DrawerPageHeader.jsx`
(shared, used here too) still has no `titleTestId` prop threading as of this
session — same gap already flagged by `settings-personal-tokens/_surface.md`
(ELITEA-2277 era), which explicitly named `AIProvidersContent` as one of the
pending consumers. Whoever adds `titleTestId` support to `DrawerPageHeader`
first should wire it at ALL pending call sites in one pass, not just their
own page's.

## Reusable mechanism for the 7 section-accordion testids
`ConfigurationSection.jsx`/`AIProviderAccordion.jsx` take no testid prop
today. Both are feature-scoped (`features/settings/ui/ai-providers/`, not
`shared/`), so a plain per-call-site hardcoded `sectionTestId` prop is
correct (no dynamic templating needed) — each of the 7
`<ConfigurationSection title="...">` call sites in `ConfigurationsPanel.jsx`
already hardcodes a distinct `title`; add a sibling `sectionTestId` at each.

## Network
Three call shapes on page load, all independently 200 for this project:
1. `GET /configurations/models/{project_id}?include_shared=true` (summary,
   no section param).
2. `GET /configurations/models/{project_id}?include_shared=true&section={llm|
   embedding|vectorstorage|image_generation|asr|tts}` — one per section
   (drives the "Default"/tier selector options + labels).
3. `GET /configurations/configurations/{project_id}?...&section=llm&section=
   embedding&section=vectorstorage&section=ai_credentials&section=
   image_generation&section=asr&section=tts&section=embedding_model&
   section=credentials` — the combined card-listing call
   (`useMultiSectionConfigurations`), drives which accordions actually
   render.

## Gotchas
- Console: 0 errors, 0 warnings on page load and after expanding a section
  (checked before AND after interaction).
- "LLM Models" (case wording) vs "LLMs" (live label) — cosmetic label drift,
  not worth a separate clarification on its own (folded into the main one).

## Resolved/added during ELITEA-2397 implementation (2026-08-06)
- **Option values are derivable from the `section=llm` GET response body
  directly** — no need to read the hidden combobox textbox value at all.
  `POST /configurations/models/{project_id}` body is `{name, target_project_id,
  section}` (`section` is `"llm"`/`"llm_high_tier"`/`"llm_low_tier"` —
  confirmed via `EliteaUI/src/api/configurations.js`'s
  `setProjectDefaultModel` mutation + `ConfigurationsPanel.jsx`'s
  `onChangeDefaultModel('llm_high_tier'|'llm_low_tier')` call sites). The
  `section=llm` GET body's top-level `default_model_name`/
  `default_model_project_id` (+ `high_tier_`/`low_tier_` counterparts) give
  the CURRENT tier values directly, and each `items[]` entry carries its own
  `high_tier`/`low_tier` eligibility booleans + `name`/`project_id`/
  `display_name` — enough to construct any option's
  `select-option-{name}<<>>{project_id}` testid without touching the DOM.
  Confirmed live: High-tier dropdown has exactly 7 eligible items, Low-tier 3
  (of 11 total), matching the counts this surface note already recorded for
  High-tier.
- **No "clear" payload shape exists for a tier** — confirmed via
  `setProjectDefaultModel`'s mutation signature (`{name, target_project_id,
  section}`, no nullable variant, no separate clear endpoint anywhere in
  `EliteaUI/src/api/configurations.js`). The AFS § Cleanup's option (a)
  ("capture the exact request body, use it directly for teardown of an
  originally-unset tier") is **not available** — there is no such payload
  shape. Option (b) (restore to a known value; treat "started unset" as
  un-seeded and document rather than silently worsen) is the only one that
  exists today. Not exercised this session — High-tier already carried a
  concrete value (`gpt-5.2`, left there by the ELITEA-2392 analyst session)
  when this implementation ran, so full bit-for-bit restoration succeeded via
  the normal re-select mechanism for all three tiers (verified via a direct
  API read post-test).
- **The outer `ai-provider-configuration-card` testid's text content cannot
  be exact-matched to disambiguate one model from another.** `displayName` +
  `statusText` + the tier-badge Typography render as sibling elements with NO
  whitespace separator in the concatenated `textContent` (e.g. a card reading
  "GPT-5.4" + "OK • Shared" renders as `"GPT-5.4OK • Shared"` in one string) —
  an anchored `^name$` regex filter on the outer card testid alone therefore
  never matches (first live test run of this implementation hit this: a
  `to_be_visible()` wait on the badge timed out because `card_for_model()`
  matched zero cards). Fixed by adding a dedicated
  `ai-provider-configuration-card-name` testid on the `displayName`
  `Typography` alone (`EliteaAI/EliteaUI@e1ea650c`) and filtering the outer
  card via `.filter(has=<name-locator>)` instead of `.filter(has_text=...)`
  directly on the card. Any future case identifying a `ConfigurationCard` by
  exact model name should reuse `AIProvidersPage.card_for_model()` rather than
  re-deriving this.

## Loading state — what it is, and how to observe it honestly (ELITEA-2251, 2026-08-24)
- The loading indicator on this page is **per-section text, not a spinner**:
  `ConfigurationSection.jsx:88-105` renders the section title plus a `Typography`
  reading exactly `Loading...` while `isLoading`. **7 of them** render together
  (LLMs, Embedding Models, Vector Storage, Image Generation, ASR, TTS, AI
  Credentials) — the count is stable even though Vector Storage is hidden once
  loaded, because the hide-when-empty check happens *after* the loading branch.
  **No testid** — needs `{sectionTestId}-loading`, the same derived-id pattern the
  component already uses for `${sectionTestId}-default-selector` (`:148`).
- The only `role="progressbar"` in this flow is the app's **route-chunk/Suspense**
  spinner (~1.5 s on a cold `goto`, <250 ms on an in-app click). It is a *different*
  indicator and is gone before the section loading state appears — never assert it
  for this page's data-loading contract.
- **Timing control that works** (sanctioned by `.agents/testing.md` § Fidelity
  policy — the real response is delayed, never fabricated):
  `page.route('**/api/v2/configurations/configurations/**', h)` where `h` waits N s
  then `route.continue()`s. Measured with N=6 s via direct `goto`: progressbar
  0-1.5 s → 7× `Loading...` 2.0-8.5 s → 12 `ai-providers-section-*` testids at 9.0 s,
  0 console errors. With N=4 s via an in-app click from `/settings/tokens`: 7×
  `Loading...` 0.25-4.75 s → 12 section testids at 5.0 s. Remember `page.unroute`.
- Without a delay the whole fetch completes in well under a second — do not try to
  catch the loading state by racing it.

## Resolved/added during ELITEA-2251 implementation (2026-08-24)
- **`{sectionTestId}-loading` now exists** on `ConfigurationSection.jsx`'s `isLoading`
  branch (`data-testid={sectionTestId ? \`${sectionTestId}-loading\` : undefined}` on the
  `Loading...` `Typography`) — EliteaAI/EliteaUI@c49f61bc, on `automation/testids`, NOT yet
  cherry-picked to `main`. Resolves this digest's "**No testid** — needs
  `{sectionTestId}-loading`" note above. All 7 sections get one; the count is 7 while the
  combined configurations GET is in flight and 0 afterwards.
- **Do NOT count section roots with the bare `[data-testid^="ai-providers-section-"]`
  prefix** — it also matches the derived `-default-selector` / `-high-tier-model-selector`
  / `-low-tier-model-selector` testids. That is why 12 nodes are observed for 5 rendered
  sections. Use the 5 named section-header descriptors
  (`AIProvidersPage.populated_section_headers()`), or the compound
  `[data-testid^="ai-providers-section-"][data-testid$="-loading"]`
  (`AIProvidersPage.SECTION_LOADING_SELECTOR`) for the loading placeholders.
- **A `time.sleep()` inside a `page.route` handler does NOT work for delaying a SINGLE
  request in Playwright's sync API** (it does work for the artifacts-download tests only
  because those delay many requests in sequence). Sync-API route handlers run on the same
  OS thread as the test body, so the sleep freezes the test body too and it resumes at the
  same instant the response lands — racing the re-render it wants to observe. **Working
  pattern: hold and release** — the handler appends the `Route` object to a list and
  returns; the test body asserts the transient state, then calls `route.continue_()` on
  each held route. Fully deterministic, no guessed delay constant, same fidelity class
  (the product's own request is continued, never fulfilled). Always release in a `finally`
  and `page.unroute(...)`.
- **`AIProvidersPage.navigate()` (i.e. `BasePage.navigate()`) is unusable while a request
  is held** — it waits for `networkidle`, which can never be reached; use
  `page.goto(f"{settings.app_base_url}{AI_PROVIDERS_PATH}", wait_until="domcontentloaded")`.
- **The loading branch replaces the whole section**: no accordion header, no cards, no
  selectors — so `ai-providers-section-llms` has count 0 while loading. It is a legitimate
  "content has arrived" proof.
- **Dev-server gotcha (cost one rerun):** the FIRST test run right after editing a JSX file
  loaded the pre-edit module (testid absent) even though the Vite dev server was already
  serving the updated transform (`curl` confirmed). The identical re-run passed. If a
  brand-new testid is "not found" on the first run after adding it, re-run once before
  debugging the JSX.

## AI Credentials section can no longer be empty (ELITEA-2417, 2026-08-29)

The hide-when-empty rule (`ConfigurationSection.jsx` returns `null` for zero
items) is unchanged and still demonstrable — via **Vector Storage**, which is
absent on every project tried. It is **no longer demonstrable via AI
Credentials**: a shared credential `ELPS` is visible in every non-public project
(the page fetches `include_shared=true`), so
`ai-providers-section-ai-credentials` always renders, badge `1`, one
`ai-provider-configuration-card` named `ELPS` / `OK • Shared`. Verified on
projects 400 and 399 in one session. ELITEA-2417 is `blocked` on this; decision
ticket **#1982**.

## The "+" flow on this page (re-confirmed 2026-08-29)

`sidebar-create-button` → `/settings/create-ai-provider?viewMode=owner&from=ai-providers`
→ a type picker with exactly 12 cards: `toolkit-type-card-{ai_dial, amazon_bedrock,
azure_open_ai, embedding_model, image_generation_model, llm_model, ollama, open_ai,
pgvector, asr_model, tts_model, vertex_ai}`. **There is no generic "AI Credentials"
card** — a credential is created by picking a provider type. `open_ai` →
`/settings/create-ai-provider/open_ai`, fields `toolkit-field-{label,elitea_title,
api_base,api_key}-input` + `credential-form-{save,discard,test-connection}-button`
(all pre-existing, owned by `CredentialFormFieldsMixin`). The **Cancel/discard
button is `disabled` while the form is pristine** — navigate away instead of
clicking it to abandon.

⚠️ The type-picker page logs one React *"Each child in a list should have a unique
key prop"* `console.error` (`CategorySection.jsx` ← `GroupedCategory.jsx` ←
`CredentialTypeSelector.jsx`) — tracked as **#656**, expect exactly this one.

⚠️ **Do not `fetch()` the API from `browser_evaluate` on localhost** — the dev
proxy 302s to `dev.elitea.ai/forward-auth/...` and each call logs 2 CORS
`console.error`s, polluting any console-error assertion. Use `page.expect_response`.

## The LLM-model CRUD flow — full form inventory (ELITEA-2395/2396/2408/2409, 2026-08-29)

Confirmed live by the qa-engineer analyst, batch `settings-w10`, cluster of four
cases. Every handle below was exercised in that session.

### Create form — `/settings/create-ai-provider/llm_model?viewMode=owner&from=ai-providers`

Reached by `sidebar-create-button` → `toolkit-type-card-llm_model`, or by a direct
`goto` of the route (which **skips** the type-picker page and therefore its `#656`
React `key` console error). It is the shared **credential form**
(`CredentialFormFieldsMixin` already owns most of these):

| Field / control | Testid | Notes |
|---|---|---|
| Display Name * | `toolkit-field-label-input` | the only field that gates Save today |
| ID * | `toolkit-field-elitea_title-input` | **always `disabled`** on this flow (`ToolBase.jsx:245`; `enableEditEliteaTitle` is set only from a `prefillId` URL param). Auto-derives from Display Name, lowercase + underscores, and **clears when the label clears** |
| Name * (model identifier) | `toolkit-field-name-input` | schema-required, **does NOT gate Save** — defect #1984 |
| Context Window | `toolkit-field-context_window-input` | pre-filled `128000` |
| Max Output Tokens | `toolkit-field-max_output_tokens-input` | pre-filled `16000` |
| Supports Reasoning / Vision / Low Tier / High Tier / Openai Compatible | `toolkit-field-{supports_reasoning,supports_vision,low_tier,high_tier,openai_compatible}-checkbox` (+ `-checkbox-field` for the native input) | all default off |
| Ai Credentials * | `toolkit-credential-select-` · clickable `toolkit-credential-select--combobox` | **the trailing dash is real** — the JSX is `toolkit-credential-select-${type}` (`CredentialsSelect.jsx:519`) and `type` is empty here |
| Save / Cancel / Test connection | `credential-form-save-button` / `credential-form-discard-button` / `credential-form-test-connection-button` | Save + Cancel disabled while pristine |

Credential dropdown options carry **JSON-shaped** testids:
`select-option-{"kind":"create_action","private":true|false}` (the two "New …
credentials" actions) and
`select-option-{"kind":"saved","elitea_title":"<title>","private":false}`.
As a page-object class constant (braces doubled for `.format`):
`'[data-testid=\'select-option-{{"kind":"saved","elitea_title":"{}","private":false}}\']'`.

Schema source of truth: `GET /api/v2/configurations/available/?section=…`; the
`llm_model` entry's `config_schema.properties.data.required` is
`["name","ai_credentials"]` and the top-level `config_schema.required` is
`["elitea_title","label","type","data"]`. `validateRequiredFields`
(`toolBase.helpers.js:146`) walks **only the top level** — that is the root cause
of #1984.

### Edit form — `/settings/edit-ai-provider/{configuration_id}?from=ai-providers`

Reached by clicking an `ai-provider-configuration-card`. Same field inventory,
pre-populated, Save/Discard disabled while pristine. Editing the Display Name
**also re-derives the disabled ID field** (`autotest_llm_model` →
`autotest_llm_model_edited`) — recorded as an observation in ELITEA-2396's AFS,
not filed.

### Delete — the only teardown path (verified end to end)

Card → `controls-menu-button` → `delete-credentials-menuitem` (composed at
runtime by `DotMenu.jsx:58` from `key: 'delete-credentials'` — a bare-substring
grep on `main` finds the key, not the testid) → confirm dialog
`delete-confirm-dialog` with `delete-confirm-entity-name`,
`delete-confirm-name-input` (**type the exact display name**),
`delete-confirm-cancel-button`, `delete-confirm-button`.
⚠️ Immediately after a delete the app GETs the deleted record
(`/api/v2/configurations/configuration/{project}/{id}`) and logs a **404** console
error. Assert any "no console errors" axis **before** teardown.

### LLMs section grouping

Cards are grouped under `GROUP_ORDER` headings (`ConfigurationSection.jsx:17-23`):
**`OpenAI` / `Anthropic` / `Other Providers`**. A newly created custom model lands
in **`Other Providers`**. The group container `Box` and its label `Typography`
carry **no testid** — needed for ELITEA-2395 step 11:
`ai-providers-configuration-group` + `ai-providers-configuration-group-name`
(static, repeated per group — same pattern as `ai-provider-configuration-card`
/ `-card-name`, and needed for the same reason: the group's concatenated text
includes every card's text, so `has_text` cannot identify it).

### Newly created models and the Default selector

A model created here appears immediately in
`ai-providers-section-llms-default-selector-combobox` as
`select-option-{data.name}<<>>{project_id}` (observed `select-option-gpt-4o<<>>400`)
labelled with its **Display Name**. Selecting it flips the combobox label and adds
a `Default` `ai-provider-configuration-badge` to its card; re-selecting the previous
model restores both, losslessly (verified `GPT-5.6 Luna` → new → `GPT-5.6 Luna`).
This session left project 400 at its starting state: 12 LLM cards, Default
`GPT-5.6 Luna`, High-tier `Bedrock-GPT-5.6-Terra`, Low-tier `GPT-5.6 Luna`.

### Gotchas confirmed this session

- **A direct `goto` to the create route mounts the form seconds later** (schema
  fetch first). `fill()` immediately after `goto` fails with "does not match any
  elements". Wait on `toolkit-field-label-input`.
- **A dirty create/edit form arms a native `beforeunload` dialog.** A reload or
  `goto` mid-edit raises it and blocks every subsequent Playwright call until
  handled — cost one recovery turn this session.
- Clean `goto` of `/settings/ai-providers` and of the typed create route each
  logged **0 console errors**. The `#656` React `key` error is the **type-picker**
  page's alone. A handful of CORS errors on
  `configurations/configurations/{400,399,1}?…&shared_limit=200&section=ai_credentials`
  appeared once mid-session and did not reproduce on clean loads — same profile as
  the recurring unrelated-resource noise class in `.agents/testing.md`.

### AFS files from this run (all `ready-for-automation`)

- `l3_create-llm-model-configuration_ELITEA-2395.md` — needs the 2 group testids
- `l3_edit-llm-model-configuration_ELITEA-2396.md`
- `l3_create-llm-model-required-field-validation_ELITEA-2408.md` — **sanctioned-RED** on #1984
- `l3_create-llm-model-id-autopopulated_ELITEA-2409.md` — asserts the live read-only ID contract (clarification #1985)

Not a family AFS: the four differ in **steps** (full create + tier assignment /
update-in-place / required-field gating / client-side derivation), not only in data.

## Resolved/added during ELITEA-2395/2396/2408/2409 implementation (2026-08-29)

- **The two group testids now EXIST** — `ai-providers-configuration-group` +
  `ai-providers-configuration-group-name` on `ConfigurationSection.jsx`'s group
  `Box` / label `Typography` (attribute-only additions, no new DOM nodes):
  EliteaAI/EliteaUI@a64d3308, on `automation/testids`, **not yet cherry-picked to
  `main`**. Resolves the "needs-adding" note in § LLMs section grouping above. Use
  `AIProvidersPage.configuration_group(label)` / `.card_in_group(label, model_name)`
  rather than re-deriving the `.filter(has=…)` shape.
- **`toolkit-field-label-input` carries `maxlength="32"`** (`ToolBase.jsx`'s
  `MAX_NAME_LENGTH`) and truncates **silently** — no helper text, no error. A
  per-run-suffixed Display Name longer than 32 characters is stored truncated and a
  `to_have_value()` assertion fails with a confusing near-miss (cost one rerun on
  ELITEA-2396: `"Autotest LLM Model Edited 1788026764"` landed as
  `"…Edited 178802"`). Keep the LONGEST name a case uses inside 32 characters.
- **The Ai Credentials select DOES gate Save; `name` is the only required field
  that does not.** Verified live in ELITEA-2395's run: with Display Name **and**
  Name filled and no credential chosen, `credential-form-save-button` is
  `disabled`, and it flips to enabled the moment the saved credential is picked.
  So #1984 is narrower than "nested `data.required` is never walked" — it is
  specific to `name`. (Recorded here because the obvious inference from #1984's
  root-cause write-up is the opposite, and acting on it would have produced a
  false assertion.)
- **New page object `automation/pages/ai_provider_form_page.py`
  (`AiProviderFormPage`)** owns the create/edit form's AI-provider-specific
  handles: the Ai Credentials combobox + its JSON-shaped saved-credential option
  template, the tab-bar Discard button, and the three-dot menu +
  `DeleteEntityModal` handles that are the only teardown path for a
  configuration. Every plain field (`toolkit-field-*`) is INHERITED from
  `CredentialFormFieldsMixin` — do not redeclare them.
- **`AIProvidersPage` gained** `configuration_cards` (locator form of the count),
  `configuration_group()`, `card_in_group()` and `open_model_card()` — all
  additive, no existing method changed.
- **Delete is reachable only from the EDIT form**, not from the card: click the
  card → `controls-menu-button` → `delete-credentials-menuitem` → retype the
  display name → `delete-confirm-button`. The confirm dialog detaches on success;
  the app then re-fetches the deleted record and logs a 404 (assert any console
  axis BEFORE teardown — confirmed again this session).
- **A `page.on("dialog", …)` handler is the cheap answer to the `beforeunload`
  trap.** All four specs register `page.on("dialog", lambda d: d.accept())` before
  touching the form; no reload/goto away from a dirty form blocked afterwards.
- Specs landed: `automation/tests/ui/settings/test_llm_model_create.py` (2395),
  `test_llm_model_edit.py` (2396), `test_llm_model_required_field_validation.py`
  (2408, sanctioned-RED on #1984), `test_llm_model_id_autopopulated.py` (2409).

## The Embedding-Model and Vector-Storage (PgVector) CRUD flows (ELITEA-2398/2399/2400/2401/2410/2411, 2026-08-29)

Confirmed live by the qa-engineer analyst, batch `settings-w10`, cluster of six cases,
project `UI Testing` (400), `EliteaAI/EliteaUI` @ `automation/testids` `a64d3308`.
Every handle below was exercised in that session. Complements the LLM-model section
above — the three provider types share ONE schema-driven form and differ only in fields.

### Create forms — the per-type field inventory

Route: `/settings/create-ai-provider/{type}?viewMode=owner&from=ai-providers`, reached
by `sidebar-create-button` → `toolkit-type-card-{type}`, or by a direct `goto` (which
skips the type-picker page and therefore its `#656` React `key` console error).

| Field | `llm_model` | `embedding_model` | `pgvector` |
|---|---|---|---|
| `toolkit-field-label-input` (Display Name *) | ✓ | ✓ | ✓ |
| `toolkit-field-elitea_title-input` (ID *, always `disabled`) | ✓ | ✓ | ✓ |
| `toolkit-field-name-input` (Name *) | ✓ | ✓ | — |
| `toolkit-field-context_window-input` / `-max_output_tokens-input` | ✓ | — | — |
| `toolkit-field-connection_string-input` (secret) | — | — | ✓ |
| `toolkit-credential-select--combobox` (Ai Credentials *) | ✓ | ✓ | **—** |
| `credential-form-{save,discard,test-connection}-button` | ✓ | ✓ | ✓ (test-connection permanently `disabled`: `has_test_connection: false`) |

**Which fields actually gate Save** (live-verified, not inferred):

| Type | Save is enabled when… |
|---|---|
| `llm_model` / `embedding_model` | Display Name **and** an Ai Credential are set. **`name` does NOT gate Save** — #1984, and it is *not* LLM-specific (reproduced identically on `embedding_model` this session; recorded as a comment on #1984, not a duplicate ticket) |
| `pgvector` | **Display Name alone.** `connection_string` does not gate Save — and correctly so: the schema declares it optional (below) |

### The secret field — `toolkit-field-connection_string-input` is a DIV

`SecretField.jsx` puts the caller's testid on the MUI **TextField root**, and derives
the handles automation actually needs (`SecretField.jsx:77,88,342`):

| Handle | Element | Provenance |
|---|---|---|
| `toolkit-field-connection_string-input` | outer **DIV** wrapper — *do not type into it* | on-main ✓ |
| `toolkit-field-connection_string-input-field` | the native `<input type="password">` — **type here** | on-main ✓ (`\`${inputProps['data-testid']}-field\``) |
| `toolkit-field-connection_string-input-helper-text` | inline validation/error text | on-main ✓ |
| `toolkit-field-connection_string-input-toggle-{secret,password}` | the Secret/Password toggle | **`automation/testids` only** (`testIdPrefix`) |

**The stored value never comes back.** Re-opening a saved pgvector record shows a
masked 32-hex placeholder (observed `62ac1990453041258fcbeea7a0bafe8a`), not the typed
URI (`writeOnly: true`). Never write a round-trip assertion on it.

### Schemas — `GET /api/v2/configurations/available/?section={llm|embedding|vectorstorage}`

The product's own declaration of the required set; read it instead of inferring from
the asterisk. For `pgvector`:

```json
{"type": "pgvector", "section": "vectorstorage", "has_test_connection": false,
 "config_schema": {"required": ["elitea_title","label","type","data"],
   "properties": {"data": {"title": "PgVectorConfiguration", "properties": {
     "connection_string": {"default": null, "format": "password",
                           "title": "Connection String", "type": "string",
                           "writeOnly": true}}}}}}
```
**No `required` array inside `data` at all** — `connection_string` is optional, and the
UI correctly renders it without an asterisk. This is why ELITEA-2411 is **blocked**
(decision ticket #1988 § 1), not a bug.

### The "+" type picker has NO "Vector Storage" card

12 flat cards, no grouping step: `toolkit-type-card-{ai_dial, amazon_bedrock,
azure_open_ai, embedding_model, image_generation_model, llm_model, ollama, open_ai,
pgvector, asr_model, tts_model, vertex_ai}`. The card is labelled **"PgVector"**;
"Vector Storage" is the *accordion section* on the list page. Cases saying
*"select 'Vector Storage' → PGVector"* describe two steps that are one click
(#1988 § 2). Same for **"Embedding model"** (lowercase `m`).

### Default-selector option keys differ by section — this is the trap

The option testid is `select-option-{key}<<>>{project_id}`, but `{key}` is **not** the
same field everywhere:

| Section | `{key}` | Option **label** | Live example |
|---|---|---|---|
| LLMs / Embedding / Image / ASR / TTS | `data.name` (the model identifier) | the **Display Name** | `select-option-text-embedding-3-small<<>>400` labelled `Autotest Embedding Model` |
| **Vector Storage** | **`elitea_title`** | the **`elitea_title`** | `select-option-autotest_pgvector_seed<<>>400` labelled `autotest_pgvector_seed` |

Because a pgvector configuration has no `data.name` (the API literally returns
`"name": null`). Two consequences:

1. **#1987 (filed) — a Vector Storage card NEVER gets the `Default` badge.**
   `ConfigurationSection.jsx:212` builds `configKey` as
   `` `${configuration.data?.name || configuration.label}<<>>${configuration.project_id}` `` —
   for pgvector that falls back to the **label** (`Autotest PGVector Seed<<>>400`)
   while `defaultSettingValue` is the **elitea_title** (`autotest_pgvector_seed<<>>400`),
   so `isDefault` can never be true. Every other section supplies `data.name` and works.
   The assignment itself persists correctly (POST 200, GET reports `"default": true`) —
   it is display-only. ELITEA-2401 is sanctioned-RED on this.
2. **Renaming a vector storage changes its option testid**, because the edit form
   re-derives `elitea_title` from the Display Name and the server persists it
   (`autotest_pgvector` → `autotest_pgvector_edited`, verified). Don't cache an option
   testid across an edit.

**A model `name` that duplicates an existing one is safe** — the `<<>>{project_id}`
half disambiguates. Live, `select-option-text-embedding-3-small<<>>1` (shared) and
`…<<>>400` (newly created) coexisted as distinct options. Always assert the
project-scoped one; a bare substring match hits the wrong node and passes vacuously.

### ⚠️ The first Vector Storage in a project is PERMANENTLY UNDELETABLE

`CredentialsControls.jsx:51,63`:
```js
const isProtectedSection = section === 'vectorstorage' || section === 'embedding';
const isLastInSection = isProtectedSection && totalAvailable <= 1;   // own total + SHARED total
// delete menu item: disabled: isDeleting || !credentialDetails?.id || isLastInSection
```
tooltip: *"Cannot delete the only pgVector configuration. At least one is required for
the project."*

- **Embedding** is protected too, but harmless: 3 **shared** configurations mean the
  count never reaches 1, so an embedding artifact is always deletable.
- **Vector Storage has no shared configurations**, so 1 → 0 is impossible via the UI.
  Verified live: with one left, `delete-credentials-menuitem` had `aria-disabled="true"`;
  after creating a second it became clickable immediately.

**Therefore project 400 now carries a deliberate permanent seed:**
**`Autotest PGVector Seed`** / `autotest_pgvector_seed` /
`postgresql://autotest:autotest@localhost:5432/autotest`, and it is the section's
default. It is the documented precondition for ELITEA-2399/2400/2401. Any spec that
creates a vector storage **must guard that the section is already non-empty** and fail
loudly otherwise — an unguarded red run leaves permanent residue. Raised for a human
ruling on #1988 § 4.

### Live data observed (project 400, 2026-08-29)
- LLMs: 12 cards; Default `GPT-5.6 Luna`, High-tier `Bedrock-GPT-5.6-Terra`, Low-tier
  `GPT-5.6 Luna` — unchanged by this session.
- Embedding Models: **3 cards, ALL shared from project 1**
  (`amazon.titan-embed-text-v2:0`, `text-embedding-3-small`, `text-embedding-ada-002`),
  default `text-embedding-3-small` @ project **1** — unchanged by this session.
- Vector Storage: **1** (the seed above) — was 0 before this session.
- Image Generation 3 / ASR 2 / TTS 1 / AI Credentials 1 (`ELPS`) — untouched.
- Embedding Models renders **no `ai-providers-configuration-group` headings** (grouping
  is LLM-only, `groupTheModelsByProvider`); its cards sit in a flat container.

### Gotchas confirmed this session (new, or newly sharper)

- **`delete-confirm-name-input`'s testid is on a DIV wrapper, not the native input.**
  `AiProviderFormPage.delete_current_configuration()` is correct because it **clicks
  the wrapper first** (MUI focuses the inner input) and then `press_sequentially`. A
  bare `fill()`/`press_sequentially` without that click types nowhere and leaves the
  Delete button disabled — cost a turn this session.
- **A direct `goto` of a create route can silently WIPE an early `fill()`.** The
  schema-driven form remounts after `GET /configurations/available/?section=…`
  resolves; a Display Name typed in the gap read back **empty** and Save stayed
  disabled. This is sharper than the existing "wait on `toolkit-field-label-input`"
  note: the field can already be present and still lose the value. If a value reads
  back empty, re-fill rather than hunt for a typo.
- Clearing a required field must go through real key events (focus + select +
  `Backspace`); MUI does not commit React `onChange` on a bare `fill("")`.
- Console on a clean `goto` of `/settings/ai-providers` and of a typed create route:
  **0 errors**. The two expected exceptions are unchanged — `#656` (React `key`, the
  **type-picker** page only) and the post-delete
  `GET /api/v2/configurations/configuration/{project}/{id}` **404**. Assert any console
  axis **before** teardown.

### AFS files from this run

- `l3_create-embedding-model-configuration_ELITEA-2398.md` — ready-for-automation
- `l3_create-embedding-model-required-field-validation_ELITEA-2410.md` — **sanctioned-RED** on #1984
- `l3_create-vector-storage-pgvector-configuration_ELITEA-2399.md` — ready-for-automation
- `l3_edit-vector-storage-configuration_ELITEA-2400.md` — ready-for-automation
- `l3_set-vector-storage-as-default_ELITEA-2401.md` — **sanctioned-RED** on #1987
- `l3_create-vector-storage-connection-string-required_ELITEA-2411.md` — **blocked** on #1988 § 1

Not a family AFS: the six differ in **steps**, not only in data — the embedding create
has a credential-picker interaction pgvector has none of, pgvector has a secret field
embedding has none of, and edit / set-default / required-field-gating are three
different flows. They share page objects, not assertions.

### Page-object gaps for the implementer

`AIProvidersPage` has `vector_storage_section_header` but **no** vector-storage
selector descriptors, and `embedding_models_default_selector` targets the FormControl
wrapper rather than the clickable node. Add:
`ai-providers-section-vector-storage-default-selector-combobox` and
`ai-providers-section-embedding-models-default-selector-combobox`.
Everything else (`card_for_model`, `card_tier_badge`, `select_tier_model`,
`expand_section`, `configuration_cards`, `AiProviderFormPage.navigate_to_create(type)`,
`select_saved_credential`, `save_and_return_to_list`, `delete_current_configuration`)
already covers these flows unchanged.

### Resolved/added during ELITEA-2398/2410/2399/2400/2401 implementation (2026-08-29, test-automation-engineer)

Facts the implementation itself settled. No new testid was needed for any of the five
cases; every handle below already existed.

- **The automation does NOT land on project 400.** The acting user's default project is
  **399 (`Private`)**, whose Vector Storage section is EMPTY. Confirmed from the
  product's own `GET /configurations/models/{id}?include_shared=true&section=vectorstorage`:
  399 → `total: 0`, 400 → `total: 1` (the seed). Both projects carry the same 12 LLMs and
  3 shared embedding models, so a card count cannot tell them apart — only the Vector
  Storage total can. The three vector-storage specs therefore switch to the seeded
  project through the sidebar selector (`settings.ai_providers_seeded_project_id`,
  default `"400"`). **The permanent seed `Autotest PGVector Seed` is intact and was
  verified present before and after every run.**
- **Creating a Vector Storage configuration ASSIGNS it as the section default.**
  Measured: with `autotest_pgvector_seed` the default before the create, the combobox
  read `autotest_pgvector_<run>` straight after, with no selection made. This is the
  OPPOSITE of the LLMs section, where ELITEA-2395 must assign the new model explicitly,
  and it contradicts the Axis-2 row ELITEA-2399's AFS originally carried. Consequences:
  every spec that creates one has mutated the project default and owes a restore; and
  ELITEA-2401's setup must put the pre-existing default back before the case's "select a
  different one" step, or that step is a no-op. Not filed — no case asserts it either
  way, and it is plausibly intended for a section that requires a default.
- **`wait_for_form()` is not enough on these create routes.** It settles on
  `toolkit-field-label-input`, which the form renders in its PRE-schema pass too, so the
  schema-driven re-render that follows `GET /configurations/available/?section=…` can
  wipe a value that was already typed **and asserted**. Measured on ELITEA-2399: Display
  Name typed, read back correctly, Save observed ENABLED — and Save was still disabled
  10 s later at the click. Wait for a field that exists only in the schema render
  (`connection_string` for pgvector, `name` for llm/embedding):
  `AiProviderFormPage.wait_for_schema_field()`.
- **`[data-testid^="select-option-"]` also matches `select-option-selected-icon`** — the
  checkmark the shared `SingleSelect` renders inside the SELECTED option. A 2-option
  dropdown with one selected resolves to THREE elements. Any option-set count must
  exclude it (`AIProvidersPage.SELECT_OPTION_PREFIX_SELECTOR` does).
- **Re-selecting an already-selected option fires NO request.** A helper that waits for
  the `POST /configurations/models/{project_id}` will hang its full timeout. Read the
  persisted default back first and only re-select when it actually moved.
- **`get_configuration_card_count()` is whole-page, and the page's expansion state is not
  stable across a Save.** The LLMs accordion auto-expands only on a fresh page load, so a
  baseline taken before a Save and a count taken after the app's own navigation back are
  not comparable (measured 15 → 4). `AIProvidersPage.isolate_section()` (collapse every
  section, expand one) gives a genuinely section-scoped count.
- **`press_sequentially` can drop the first keystroke** on a freshly-mounted MUI input if
  the click's focus is still settling: `text-embedding-3-small` arrived as
  `ext-embedding-3-small`. `AiProviderFormPage.set_schema_field()` confirms focus first.
  `replace_secret_value()` additionally needs a **blur** to commit — `fill_secret_field()`.
- Teardown is proven: after every run the project read back exactly as found — Vector
  Storage `total: 1` / default `autotest_pgvector_seed`, Embedding `total: 3` / default
  `text-embedding-3-small`.

