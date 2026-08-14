# Test Case: AI Providers settings page loads all integration sections without error

## Metadata
- **TMS ID**: ELITEA-2392
- **Linked Story**: none
- **Priority**: l3
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`)
- **User set**: `${TEST_USER}` (via `auth_state` fixture — VITE_DEV_TOKEN on localhost, no login needed)
- **Analyst**: qa-engineer (analyst slot)
- **Status**: ready-for-automation

## Case-identity note (read first — the case text names the wrong page)

The TMS case is titled "AI Configuration page loads all integration sections
without error" and directs the tester to "Settings → AI Configuration". **No
such page/nav-item exists in the live product.** Live exploration
(`git fetch origin` in `EliteaUI` done first) found the described sections
(LLM Models, Embedding Models, Vector Storage, Image Generation, ASR, TTS, AI
credentials) live on the sidebar item labelled **"AI Providers"**
(`RouteDefinitions` id `ai-providers`, route `/settings/ai-providers`, page
component `src/[fsd]/pages/settings/AIProviders.jsx` →
`AIProvidersContent.jsx` → `ConfigurationsPanel.jsx`). This AFS targets that
real page. See § Coverage Map + the filed clarification for the full
divergence, including the tabs claim in case step 12 (a *different* page
entirely — see below).

## Preconditions
- User is logged in to the Elitea platform (`auth_state` fixture, localhost
  dev-token bypass).
- Active project has ≥1 configured model in each of: LLM, Embedding,
  Image Generation, ASR, TTS sections (true for the shared `Private`/`399`
  project used by `${TEST_USER}` today — see § Concrete Handles for observed
  counts). Vector Storage and AI Credentials currently have **zero**
  configured items in this project (see § Coverage Map rows 6/10) — the test
  must not depend on seeding those, per Reverse-masking guard (this is
  correct empty-state product behaviour, not a gap to fill).

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

## Test Steps

1. Navigate to `${BASE_URL}/settings/ai-providers`.
   - **Verify**: page loads, no console errors (confirmed live: 0 errors after
     `networkidle`).
2. Verify the page header reads "AI Providers".
3. Verify the following section accordion headers are present, in this
   relative order (top→bottom, confirmed live): **LLMs**, **Embedding
   Models**, **Image Generation**, **Speech Recognition (ASR)**, **Text to
   Speech (TTS)**. (Vector Storage and AI Credentials are NOT rendered for
   this project — see step 6.)
4. Verify the "LLMs" section (auto-expanded by default) shows a "Default",
   "High-tier", and "Low-tier" model selector, and at least one configuration
   card underneath (confirmed live: 11 cards, default `Anthropic Claude 4.5
   Sonnet`, low-tier `GPT-5.4-mini`).
5. Expand "Embedding Models"; verify it shows a "Default" selector and at
   least one configuration card (confirmed live: 3 cards, default
   `text-embedding-3-small`).
6. Verify no "Vector Storage" accordion header is rendered, AND the
   underlying `GET /api/v2/configurations/models/{project_id}?...&section=
   vectorstorage` request returned 200 with zero items (confirmed live) —
   i.e. the absence is a correct empty-state hide
   (`ConfigurationSection.jsx`: `if (!configurations || configurations.length
   === 0) return null;`), not a silent load failure.
7. Verify the "Image Generation" section shows a "Default" selector and at
   least one card (confirmed live: 3 cards, default `gpt-image-1`) — expand
   via its header to confirm cards render (structurally identical
   `ConfigurationSection`/`ConfigurationCard` components already verified in
   step 5; badge count alone is sufficient corroborating evidence, per
   Automation Hints).
8. Verify "Speech Recognition (ASR)" shows a "Default" selector and at least
   one card (confirmed live: 2 cards, default `gpt-4o-mini-transcribe`).
9. Verify "Text to Speech (TTS)" shows a "Default" selector and at least one
   card (confirmed live: 1 card, default `gpt-4o-mini-tts`).
10. Verify no "AI Credentials" accordion header is rendered, AND the
    underlying `section=ai_credentials` request in the combined
    `GET /api/v2/configurations/configurations/{project_id}?...` call
    returned 200 (confirmed live) — same empty-state-hide reasoning as step 6.
11. (Covered by steps 4/5/7/8/9 individually — each populated section's
    count badge / expanded card list IS the "≥1 configuration card" check.)
12. **Not automated as specced** — see § Known Defects Found /
    Coverage Map row 12. The case's "AI Configuration"/"OpenAI Template"
    tabs do not exist on this page.

## Expected Results
- `/settings/ai-providers` loads with header "AI Providers", zero console
  errors, zero non-2xx responses from any `configurations` endpoint.
- Sections with ≥1 configured item render as an accordion with a count badge
  and, when expanded, ≥1 `ConfigurationCard`; sections with 0 configured
  items render nothing (verified via the API response, not just DOM absence).
- No "AI Configuration"/"OpenAI Template" tab exists on this page (see
  Coverage Map row 12 / filed clarification).

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| desc/title: "AI Configuration page" identity | a page reachable via Settings → AI Configuration | step 1 | `step 1`: real page is "AI Providers" / `/settings/ai-providers` | clarification *(case names a non-existent page/nav-item; filed)* |
| 1 Navigate to Settings → AI Configuration | target page loads successfully | step 1 | `step 1`: page header + no console errors | asserted *(against the real "AI Providers" page)* |
| 2 Verify the page loads without error or blank state | condition holds | step 1 | `step 1`: 0 console errors, all `configurations` requests 200 | asserted |
| 3 Verify sections visible in order | condition holds | step 3 | `step 3`: accordion header order | asserted *(scoped to the 5 sections actually rendered with this project's data — see rows 6/10)* |
| 4 LLM Models (Default/High-tier/Low-tier) | UI state correct | step 4 | `step 4`: 3 selectors + ≥1 card | asserted *(live label is "LLMs", not "LLM Models" — cosmetic, noted)* |
| 5 Embedding Models (Default) | UI state correct | step 5 | `step 5`: selector + ≥1 card | asserted |
| 6 Vector Storage (Default) | UI state correct | step 6 | `step 6`: section absent + API 200/zero-items | clarification *(section is data-dependent; hidden by design when empty — confirmed correct behaviour, not a defect; see § Known Defects)* |
| 7 Image Generation (Default) | UI state correct | step 7 | `step 7`: selector + ≥1 card | asserted |
| 8 Speech Recognition/ASR (Default) | UI state correct | step 8 | `step 8`: selector + ≥1 card | asserted |
| 9 Text to Speech/TTS (Default) | UI state correct | step 9 | `step 9`: selector + ≥1 card | asserted |
| 10 AI credentials (if configured) | UI state correct | step 10 | `step 10`: section absent + API 200 | clarification *(same as row 6 — "if configured" in the case text already hints at this conditionality)* |
| 11 Each section contains ≥1 configuration card | condition holds | steps 4/5/7/8/9 | count badges + one live-expanded section | asserted *(decomposed across the 5 populated sections)* |
| 12 "AI Configuration"/"OpenAI Template" tabs present at top | condition holds | — | — | clarification *(these tabs exist on a DIFFERENT page — the "AI Configurations" accordion on Settings → General/`project-general` — and are literally labelled "Basic"/"OpenAI Template", not "AI Configuration"/"OpenAI Template"; they do not appear on the AI Providers page at all. Filed as a case-text clarification.)* |
| Expected Final State: tabs present at top | condition holds | — | — | clarification *(duplicate of row 12)* |

**Axis 2 — Analyst additions**
- Steps 6/10 assert the underlying API response (200, correct item count)
  in addition to DOM absence — *added: distinguishes "correctly hidden empty
  section" from "silently failed to load", which is the actual intent behind
  the case's "without error" framing; a DOM-only check can't tell the two
  apart.*
- Step 1 asserts zero non-2xx responses across every `configurations`
  endpoint — *added: this is the most direct read of the title's "loads all
  integration sections without error," stronger than "no console errors"
  alone.*

## Cleanup
None — read-only page, no data created or mutated.

## Concrete Handles (discovered during exploration)

All testids below are **needs-adding** — the entire `ai-providers` component
tree has zero `data-testid`/`testId` usage today (confirmed via
`grep -n "testid\|testId"` on every file under
`src/[fsd]/features/settings/ui/ai-providers/` and
`src/[fsd]/pages/settings/AIProviders.jsx`). `DrawerPageHeader.jsx` (the
shared header used by `AIProvidersContent` and 13+ other settings pages) also
has zero title-testid threading today — this exact gap was already
documented by the `settings-personal-tokens` analyst
(`test-specs/settings-personal-tokens/_surface.md` § "`DrawerPageHeader.jsx`
gaps"), re-confirmed live this session; `AIProviders` is explicitly named
there as one of the pending consumers.

| Element | Recommended Locator | Fallback | Provenance |
|---|---|---|---|
| Page header "AI Providers" | `LocatorDescriptor(testid="ai-providers-page-title")` | none — testid-only policy | needs-adding (thread `titleTestId` prop through `DrawerPageHeader.jsx`, same mechanism as `secrets-page-title`/`personal-tokens-page-title`) |
| "LLMs" section accordion header | `LocatorDescriptor(testid="ai-providers-section-llms")` | none | needs-adding (`ConfigurationSection`/`AIProviderAccordion` take no testid prop today — add a `sectionTestId` prop, wire at each `ConfigurationsPanel.jsx` call site) |
| "Embedding Models" section accordion header | `LocatorDescriptor(testid="ai-providers-section-embedding-models")` | none | needs-adding (same mechanism) |
| "Vector Storage" section accordion header | `LocatorDescriptor(testid="ai-providers-section-vector-storage")` | none | needs-adding (same mechanism; only renders when ≥1 config exists) |
| "Image Generation" section accordion header | `LocatorDescriptor(testid="ai-providers-section-image-generation")` | none | needs-adding (same mechanism) |
| "Speech Recognition (ASR)" section accordion header | `LocatorDescriptor(testid="ai-providers-section-asr")` | none | needs-adding (same mechanism) |
| "Text to Speech (TTS)" section accordion header | `LocatorDescriptor(testid="ai-providers-section-tts")` | none | needs-adding (same mechanism) |
| "AI Credentials" section accordion header | `LocatorDescriptor(testid="ai-providers-section-ai-credentials")` | none | needs-adding (same mechanism; only renders when ≥1 config exists) |
| Configuration card (generic, repeated per card) | `LocatorDescriptor(testid="ai-provider-configuration-card")` | none | needs-adding (`ConfigurationCard.jsx`'s outer `Box` — static value repeated per card is fine per existing pattern, e.g. `secret-row`) |

Dynamic-testid note: since a caller-supplied `sectionTestId` differs per
section but the component (`ConfigurationSection.jsx`/
`AIProviderAccordion.jsx`) is feature-scoped (lives under
`features/settings/ui/ai-providers/`, not `shared/`), the prop can be a plain
static string per call site in `ConfigurationsPanel.jsx` — no
`{prefix}-{param}` templating needed (each of the 7 call sites already hard
codes a distinct `title=`; add a sibling hardcoded `sectionTestId=` at each).

## Network Behavior
- `GET /api/v2/configurations/models/{project_id}?include_shared=true` (no
  section param) — overall models summary, fires once on load.
- `GET /api/v2/configurations/models/{project_id}?include_shared=true&section={llm|embedding|vectorstorage|image_generation|asr|tts}` —
  one call per section, each independently 200. `vectorstorage` returns
  `items: []` for the current test project.
- `GET /api/v2/configurations/configurations/{project_id}?...&section=llm&section=embedding&section=vectorstorage&section=ai_credentials&section=image_generation&section=asr&section=tts&section=embedding_model&section=credentials` —
  the combined multi-section card-listing call; 200, drives which accordions
  render (`useMultiSectionConfigurations`).
- All of the above returned `200 OK` in this session — zero errors, zero
  4xx/5xx (checked per `.agents/role-overrides.md` § 4xx/5xx cross-check —
  N/A here since nothing failed).

## Known Defects Found During Exploration
None found — the empty Vector Storage/AI Credentials sections are correct,
intentional empty-state behaviour (`ConfigurationSection.jsx` returns `null`
for a zero-length `configurations` array; both underlying API calls returned
`200` with zero items). Filed a **case-text clarification** instead (see
below) — the case names a nonexistent page/nav-item ("AI Configuration") and
describes tabs from a *different* page/component entirely.

**Filed**: `[Clarification][ELITEA-2392] Case names a nonexistent "AI
Configuration" page/tabs; sections actually live on "AI Providers"` —
EliteaAI/elitea-testing-public#1250
(github-issue style, no umbrella per strict-per-bug policy). Recommendation
in the ticket: retitle the case to reference "Settings → AI Providers", drop
or relocate step 12 (tabs belong to Settings → General → "AI Configurations"
accordion, labelled "Basic"/"OpenAI Template" there — not "AI Configuration"),
and soften steps 6/10 to acknowledge Vector Storage/AI Credentials render
only when the project has configured items.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Page object: new `automation/pages/ai_providers_page.py` — no prior page
  object exists for this surface (grepped `automation/pages/` for
  `ai.provider`/`AIProvider`/`llm.model` — no hits beyond unrelated chat/agent
  LLM-selector pages).
- Since 2 of the 7 sections are absent for the current shared `${TEST_USER}`
  project by design (no seeded data), don't assert unconditional visibility
  for Vector Storage/AI Credentials — assert the API-response-driven absence
  per steps 6/10 instead, so the test stays meaningful without depending on
  fragile shared-project state.
- Reuse `auth_state` fixture — no login flow needed on localhost.
- Wait strategy: `wait_for_response` matching `/configurations/` (or
  `page.wait_for_load_state("networkidle")`, already used by `BasePage.navigate`)
  rather than a fixed sleep before asserting section presence.
