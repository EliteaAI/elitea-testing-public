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
