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
from the DOM. Do not treat this as a defect or a load failure — verify via
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
- AI Credentials: 0 configs — section absent.
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
