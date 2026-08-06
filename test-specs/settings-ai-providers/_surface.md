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
  `GPT-5.4-mini`, High-tier unset. Grouped by provider (OpenAI/Anthropic/
  Azure AI Foundry — `GROUP_ORDER` in `ConfigurationSection.jsx`).
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
