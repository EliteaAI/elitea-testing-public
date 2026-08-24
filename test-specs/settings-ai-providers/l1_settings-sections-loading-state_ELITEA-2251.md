# Test Case: Settings → AI Providers shows a loading state while configurations load, and clears it

## Metadata
- **TMS ID**: ELITEA-2251
- **Priority**: l1 (case priority `high`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (auth via `auth_state` / `VITE_DEV_TOKEN` on localhost), project `Private` (399)
- **Analyst**: qa-engineer (Sage), batch `settings-w01`, 2026-08-24
- **Status**: ready-for-automation
- **Surface digest**: `test-specs/settings-ai-providers/_surface.md`
- **Filed**: reused the existing clarification **#1250** (case text says "AI Configuration"; the page is "AI Providers") — commented this case onto it rather than filing a sibling

## Preconditions
- User logged in (`auth_state`), project `Private` (399) selected — the project must
  be one the user can list configurations in (`200`), otherwise sections render empty
  by design and the loading branch is meaningless.
- Nothing seeded. The case observes a transient render state, not data.

## Fidelity Declaration
| Substitution | Kind | Authority |
|---|---|---|
| `page.route('**/api/v2/configurations/configurations/**')` handler that **holds the real request open** until the loading state has been observed and then `route.continue_()`s it | **Timing control — NOT substitution** | `.agents/testing.md` § Fidelity policy: *"Delaying a real response via `page.route()` so a transient state becomes observable leaves the product as the producer of every asserted value."* Every asserted value here (the `Loading...` branch, the section cards after it) is produced by the app from the real backend response. Nothing is fabricated, nothing is fulfilled. |

The case text ("on a slow or throttled connection") explicitly asks for a slowed
connection, so the delay *is* the case's own precondition — not a workaround.

## Test Data
### reuse-existing
Project 399's real configurations (LLMs: 11 configs; Embedding Models, Image
Generation, ASR, TTS, AI Credentials populated; Vector Storage empty and therefore
hidden by design — see the digest). The assertions are structural (a branch appears,
then is replaced by ≥1 section), so they survive any change in that data.

## Test Steps
1. **Arm the delay before navigating.** Register a route handler on
   `**/api/v2/configurations/configurations/**` that **holds** the real request
   (stores the `Route` object without answering it) and `route.continue_()`s it from
   the test body once the loading assertions have run — the real request, real
   response.
   - **Verify**: nothing yet; this is setup. Register it BEFORE the navigation that
     triggers the fetch, or the request escapes the handler.
   - **Amended at implementation (ELITEA-2251, 2026-08-24):** the analyst's original
     shape — `time.sleep(DELAY)` *inside* the handler, the in-repo artifacts-download
     precedent — is **not usable for a single-request delay** in Playwright's sync
     API: route handlers run on the same OS thread as the test body, so a sleeping
     handler freezes the test body too and it resumes at the same instant the
     response lands, racing the very re-render it is trying to observe. Holding and
     releasing explicitly makes the observation window deterministic (and removes the
     guessed `DELAY` constant entirely). Same fidelity class — the product's own
     request is continued, never fulfilled.
2. Navigate to Settings → AI Providers (`/settings/ai-providers`).
   - Either a direct `page.goto` (verified live) or an in-app click from another
     settings page (also verified live) works — see the timeline below; the direct
     `goto` costs ~1.5-2 s of route-chunk load first and needs no new nav testid.
   - **Amended at implementation:** use a bare `page.goto(..., wait_until="domcontentloaded")`,
     **not** `AIProvidersPage.navigate()` — `BasePage.navigate()` waits for
     `networkidle`, which can never be reached while the configurations request is
     deliberately held open (a 30 s dead wait).
   - **Verify**: `ai-providers-page-title` becomes visible (this is the page shell,
     which renders *before* the configurations arrive).
3. Verify the loading indicator is shown while configurations are loading.
   - **Verify**: `[data-testid="ai-providers-section-llms-loading"]` (**added by this
     implementation**, see Handles) is visible **while** `ai-providers-page-title` is already
     visible and **zero** configuration cards/selectors exist.
   - **Verify (count)**: the loading placeholder renders **once per section = 7**
     (LLMs, Embedding Models, Vector Storage, Image Generation, ASR, TTS, AI
     Credentials) — confirmed live, 7 `Loading...` nodes for the whole delay window.
   - Source: `ConfigurationSection.jsx:88-105` — when `isLoading`, the section
     renders its title plus a `Typography` reading exactly `Loading...`; the card
     list is not rendered at all.
   - ⚠ Do **not** assert `role="progressbar"` here: the only progressbar in this flow
     is the app's route-chunk/Suspense spinner (0 → ~1.5 s of a cold `goto`), which
     is a *different* indicator and is gone before the section loading state appears.
4. Verify the loading indicator disappears once data is fully loaded.
   - **Verify**: the loading testid reaches count 0 (auto-waiting
     `expect(...).to_have_count(0)`, bounded by the 15 s termination budget, asserted
     after the held request is released).
   - **Verify (replaced by real content)**: `ai-providers-section-llms` is visible and
     the section's model cards/selectors render — e.g.
     `ai-providers-section-llms-default-selector-combobox` visible. Disappearing alone
     is not enough: an error state would also make it disappear.
5. Verify the page does not remain in a permanent loading state.
   - **Verify**: within a bounded budget after the request is released (15 s ceiling
     in the spec; live: content at ~1 s), the loading testid count is 0, >=1
     configuration card is rendered, and **each of the 5 populated section headers** —
     LLMs, Embedding Models, Image Generation, ASR, TTS — is visible. Assert the
     *timeout* explicitly — this step's whole content is "it terminates".
   - **Amended at implementation:** the analyst's ">=6 `[data-testid^="ai-providers-section-"]`"
     count is a **mixed** set — that prefix also matches the derived `-default-selector*`
     testids, which is why 12 nodes were observed for 5 rendered sections. Only 5 section
     roots exist for this project (Vector Storage and AI Credentials are empty and hidden
     by design), so the spec asserts those 5 by name instead of a fuzzy prefix count.
6. Side channel.
   - **Verify**: no unexpected console errors across the whole flow (0 observed live
     on this page, both with and without the delay).
   - **Cleanup**: `page.unroute(...)` so the delay cannot leak into another test.

### Live timeline (measured 2026-08-24, sampled every 250-500 ms)

Direct `goto` with a 6 s delay armed:

| t | `role=progressbar` | `Loading...` nodes | `ai-providers-section-*` | page title |
|---|---|---|---|---|
| 0 - 1.5 s | 1 (route chunk) | 0 | 0 | absent |
| 2.0 - 8.5 s | 0 | **7** | 0 | present |
| 9.0 s+ | 0 | 0 | **12** | present |

In-app click from `/settings/tokens` with a 4 s delay armed: progressbar for <250 ms,
then 7 `Loading...` from 250 ms to 4.75 s, then 12 section testids at 5.0 s. Same
contract, no chunk-load phase.

## Handles Reference
| Element | Primary handle (testid-only) | Provenance | Notes |
|---|---|---|---|
| Page title | `ai-providers-page-title` | **on-main ✓** (`git grep` on `origin/main -- src/`, fetched 2026-08-24) | renders during loading — the page shell is not blocked |
| Section loading placeholder | `ai-providers-section-llms-loading` (templated `{sectionTestId}-loading`) | **added by this implementation** — EliteaAI/EliteaUI@c49f61bc on `automation/testids`; **not yet on `main`** (human cherry-pick) | `ConfigurationSection.jsx:88-105`; the component **already receives `sectionTestId`** (`ConfigurationsPanel.jsx:78,110,125,140,154,168,183`) and already builds derived ids from it (`${sectionTestId}-default-selector`, `ConfigurationSection.jsx:148`) — so this is the same established dynamic-testid pattern, one attribute on the `Loading...` `Typography`. Feature-scoped file, not a shared component. **Not** a state-switched testid: the element itself only exists while loading; its testid value never flips (PR #581 ruling respected). |
| LLMs section root | `ai-providers-section-llms` | **on-main ✓** | the "content arrived" proof |
| LLMs default-model selector | `ai-providers-section-llms-default-selector-combobox` | **on-main ✓** (pre-existing, used by ELITEA-2397's merged spec) | stronger "content arrived" proof than the section root alone |
| All section loading placeholders (count) | class constant `'[data-testid^="ai-providers-section-"][data-testid$="-loading"]'` (`AIProvidersPage.SECTION_LOADING_SELECTOR`) | derived from the added testid | UPPER_CASE class constant per `.claude/rules/page-objects.md`; 7 while loading, 0 after. The bare `^="ai-providers-section-"` prefix is NOT used — it also matches the derived `-default-selector*` testids (that is the 12-node count), so it cannot count section roots |
| Populated section roots | the 5 pre-existing `LocatorDescriptor` fields (llms / embedding-models / image-generation / asr / tts) via `AIProvidersPage.populated_section_headers()` | **on-main ✓** (ELITEA-2392) | Vector Storage + AI Credentials are empty for project 399 and correctly absent |

Page object: extend `automation/pages/ai_providers_page.py` (exists; used by
`test_ai_providers_page_sections_load_without_error.py` and
`test_set_llm_model_default_high_low_tier.py`). No new page object needed.

## Coverage Map

### Axis 1 — every element of the TMS case
| Case element | Expected result (per live product) | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | authenticated session | `auth_state` | fixture | covered |
| Step 1: navigate to Settings → **AI Configuration** on a slow/throttled connection | no page called "AI Configuration" exists; the page is **AI Providers** (`/settings/ai-providers`) — same drift already filed as #1250 for ELITEA-2392. "Slow connection" realised as a real-response delay (§ Fidelity Declaration) | Steps 1-2 | route handler + URL + page title | covered — **clarification #1250** for the page-name drift |
| Step 2: loading indicator shown while configurations load | 7 per-section `Loading...` placeholders, page title already visible, zero cards | Step 3 | new `*-loading` testid: visible, count 7 | covered |
| Step 3: loading indicator disappears once data is fully loaded | placeholders gone, sections + selectors rendered | Step 4 | count 0 **and** section/selector visible | covered (decomposed — disappearance alone would also pass on an error state) |
| Step 4: page does not remain in a permanent loading state | content within ~1 s of the release | Step 5 | bounded-timeout (15 s) assertions on the 5 populated section headers + loading count 0 + >=1 card | covered |
| Expected Final State: no permanent loading state | as step 4 | Step 5 | same | covered |

### Axis 2 — asserted beyond the case
| Observable | Why |
|---|---|
| the page **shell** (title) renders *during* loading | "shows a loading state" implies a partial page, not a blank one — a regression that blanks the page while fetching would otherwise pass |
| the loading placeholder count is exactly 7 (one per section) | pins the per-section contract; a regression that collapses all sections into one global spinner is a real behaviour change and should fail loudly |
| the loading state is replaced by *real content*, not merely removed | see step 4 — the difference between "loaded" and "failed silently" |
| no console errors | project standard; this page was clean in every run this session |

## Known Defects / Clarifications
- **#1250 (clarification, OPEN)** — the TMS case text calls the page "AI
  Configuration"; no such page or nav item exists (the label is "AI Providers", route
  `/settings/ai-providers`; a *different* page, Settings → General, has an "AI
  Configurations" accordion with "Basic"/"OpenAI Template" tabs). ELITEA-2392 filed
  it; ELITEA-2251 reuses the same wording, so this session commented the second
  occurrence onto #1250 instead of filing a sibling. Live contract asserted per the
  reverse-masking guard.
- No product defect found on this surface this session.

## Blocked Steps
None.
