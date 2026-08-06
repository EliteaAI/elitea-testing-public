# Test Case: Set a LLM model as Default / High-tier / Low-tier

## Metadata
- **TMS ID**: ELITEA-2397
- **Linked Story**: none
- **Priority**: l3 (frontmatter `priority: medium`; matches the sibling
  `settings-ai-providers` case ELITEA-2392's l3 mapping)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids`)
- **User set**: `${TEST_USER}` (via `auth_state` fixture — `VITE_DEV_TOKEN` on
  localhost, no login needed)
- **Analyst**: qa-engineer (analyst slot)
- **Status**: ready-for-automation

## Case-identity note (read first — same root cause as ELITEA-2392)

The case navigates to "Settings → AI Configuration" — **no such page/nav-item
exists.** This is the identical page-identity drift already fully documented
and filed against ELITEA-2392
(`test-specs/settings-ai-providers/l3_ai-providers-page-sections-load-without-error_ELITEA-2392.md`,
clarification EliteaAI/elitea-testing-public#1250). This AFS reuses that
finding rather than re-filing it: the real page is **"AI Providers"**
(`/settings/ai-providers`), and its "LLMs" section (case says "LLM Models" —
same cosmetic label drift 2392 already noted) is the one with the
Default/High-tier/Low-tier selectors this case exercises.

## Case-text drift specific to THIS case — filed separately

Case step 9 ("Repeat steps 2–8 for High-tier and Low-tier selectors")
implies High-tier/Low-tier feed the "start a new chat" default model
exactly like the Default tier does. **Live source inspection + live
verification shows this is only true for Default.** Full write-up + filed
clarification: EliteaAI/elitea-testing-public#1253. Summary (see
§ Coverage Map row 9 and § Known Defects Found for the evidence):
- Default tier: confirmed live, end-to-end — changing it changes what a
  brand-new `/chat` composer's model selector shows.
- Low-tier: consumed only by the chat canvas's Mermaid "Quick Fix" AI-assist
  action (`mermaidQuickFixModel.helpers.js`), a different, narrow surface —
  not "starting a chat".
- High-tier: **zero** frontend consumers found anywhere in `EliteaUI/src`
  outside the AI Providers settings page's own display code. Setting it has
  no UI-visible effect on any chat/agent/pipeline surface as of this session.

This AFS therefore automates the FULL causal chain (selector → badge →
new-chat model) for **Default only**, and automates the selector-and-badge
mechanics only (steps 2–6, decomposed per tier) for High-tier/Low-tier — per
the Reverse-masking guard, it does not force a "used when starting a chat"
assertion for tiers the live product doesn't wire into that surface.

## Preconditions
- User is logged in (`auth_state` fixture, localhost dev-token bypass).
- Active project (`${TEST_USER}`'s `Private`/`399`) has ≥2 LLM configurations
  in at least two different tier-eligible groups, so there is always a
  genuinely *different* model to select for each tier (true today — 11 LLM
  configs; confirmed live High-tier's own dropdown offered 7 alternatives,
  Default's offered 10, Low-tier's is unconfirmed by count but the same
  mechanism applies).
- **This test MUTATES shared, live project configuration** (Default/
  High-tier/Low-tier LLM assignments for the whole `Private`/`399` project —
  the same project every other UI test in this suite runs against). It MUST
  capture the original three values before mutating anything and restore
  them in a `finally`/teardown block — see § Cleanup, this is not optional
  boilerplate here.

## Test Data

| Field | Value |
|-------|-------|
| Default tier — new value used this run | any LLM model ≠ the project's current Default (confirmed live: selecting "GPT-5.4" while "Anthropic Claude 4.5 Sonnet" was Default) |
| High-tier — new value used this run | any LLM model present in the High-tier dropdown's option list (confirmed live: "GPT-5.2") |
| Low-tier — new value used this run | any LLM model present in the Low-tier dropdown's option list ≠ its current value |

Don't hardcode specific model names in the implementation — the live model
catalogue for this shared project can and will change (2392's AFS already
observed 11 LLM configs; do not assume this count or these exact names stay
stable). Read the CURRENT selector text / dropdown options live, pick
"whatever the first non-current option is," and assert relative to that.

## Test Steps

*(Executed live this session — full round-trip for the Default tier,
including the new-chat verification; High-tier's selector/badge mechanics
also executed live and confirmed identical; Low-tier's selector/badge
mechanics not independently re-executed this session but share the exact
same component/testid/network mechanism as Default and High-tier, verified
via source — `ConfigurationSection.jsx` renders all three selectors through
the same `Select.SingleSelect` + the same per-section PATCH-on-select
handler.)*

1. Navigate to `${BASE_URL}/settings/ai-providers`.
   - **Verify**: page loads, "LLMs" section (auto-expanded) shows Default/
     High-tier/Low-tier selectors and ≥1 configuration card. Confirmed live
     (this is the same page-load assertion ELITEA-2392 already automates —
     don't re-derive it here, just reach the state).
2. **Capture the current Default/High-tier/Low-tier selector values** (for
   later restoration) by reading each selector's visible text.
   - **Verify**: all three selector texts are captured (High-tier may be
     blank/unset — confirmed live: an unset tier selector renders with no
     visible model name and no corresponding badge on any card).
3. Click the "Default" tier selector (`ai-providers-section-llms-default-selector-combobox`).
   - **Verify**: a `listbox` of LLM model options opens. Confirmed live.
4. Select a model different from the captured current Default value.
   - **Verify**: (a) the request `POST /api/v2/configurations/models/{project_id}`
     fires and returns `200` with body `{"result": "success"}`; (b) the
     Default selector's visible text updates to the newly-selected model,
     immediately, no separate Save action. Confirmed live.
5. Verify the newly-selected model's `ConfigurationCard` gains a "Default"
   badge.
   - **Verify**: within the card whose display name matches the
     newly-selected model, a "Default" badge is now present. Confirmed live
     (`GPT-5.4`'s card gained the badge the instant the selector updated —
     no additional page reload/refetch needed, the card list re-rendered
     from the SAME `POST` response's follow-on refetch).
6. Verify the previously-Default model's card no longer shows the "Default"
   badge.
   - **Verify**: within the card whose display name matches the ORIGINAL
     (pre-step-4) Default value, no "Default" badge is present. Confirmed
     live (`Anthropic Claude 4.5 Sonnet`'s card lost the badge in the same
     re-render as step 5).
7. Navigate to `${BASE_URL}/chat` (a brand-new, not-yet-sent conversation —
   NOT an existing conversation via `conversation_id`, which would carry its
   own already-resolved model instead of reading the project default).
   - **Verify**: page loads to the blank-composer greeting state. Confirmed
     live.
8. Verify the selected Default model is used when starting a chat.
   - **Verify**: `model-selector-button` (existing `ChatPage` testid) shows
     the SAME model name just set as Default in step 4. **Confirmed live,
     end-to-end**: setting Default to "GPT-5.4" in steps 3–4 caused a
     brand-new `/chat` composer's `model-selector-button` to read "GPT-5.4".
9. Repeat for High-tier and Low-tier — **scoped per § Case-text drift above**:
   - Repeat steps 3–6 (selector interaction + badge gain/loss) for High-tier,
     targeting `ai-providers-section-llms-high-tier-model-selector-combobox`
     and the "High-Tier" badge text. **Confirmed live**: selecting "GPT-5.2"
     for High-tier updated the selector immediately and the "GPT-5.2" card
     gained a "High-Tier" badge, with the same `POST` mechanism as step 4.
   - Repeat steps 3–6 for Low-tier, targeting
     `ai-providers-section-llms-low-tier-model-selector-combobox` and the
     "Low-Tier" badge text. Not independently re-executed live this session
     (see note above) — same component/mechanism, low risk, but the
     implementer should do one live confirmation pass before shipping.
   - **Do NOT repeat steps 7–8 for High-tier or Low-tier** — per the filed
     clarification (EliteaAI/elitea-testing-public#1253), neither tier
     feeds the plain `/chat` `model-selector-button`; asserting that would
     be asserting a false contract (reverse-masking guard).
10. **Restore the original Default/High-tier/Low-tier values** captured in
    step 2. See § Cleanup — this step has a real automation gap (no UI
    "clear" affordance for an originally-unset tier) that the implementer
    must resolve, not skip.

## Expected Results
- Default tier: selector-change → badge-swap → new-chat-model-selector chain
  holds fully, verified live end-to-end.
- High-tier / Low-tier: selector-change → badge-swap holds; NO claim is made
  about a plain new-chat's model selector reflecting either tier (confirmed
  false for both, for different reasons — see § Case-text drift).
- The shared project's LLM tier configuration is bit-for-bit restored after
  the test, or the test explicitly documents/asserts why it couldn't be
  (e.g., an originally-unset tier with no UI "clear" affordance).

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| desc/title: "Settings → AI Configuration" page identity | reachable via that nav path | step 1 | same root cause as ELITEA-2392, reused not re-derived | clarification *(already filed, EliteaAI/elitea-testing-public#1250 — reused, not re-filed)* |
| 1 Navigate to Settings → AI Configuration | target page loads | step 1 | page loads, LLMs section visible | asserted *(against real "AI Providers" page)* |
| 2 Click the "Default" tier dropdown selector | action completes, no error | steps 3 | listbox opens | asserted |
| 3 Select a different model from the list | control responds, next state shown | step 4 | selector text updates + `POST` 200 | asserted |
| 4 Verify the selector updates to show the newly selected model | condition holds | step 4 | selector text == newly-selected model | asserted |
| 5 Verify the corresponding model card gains a "Default" badge | condition holds | step 5 | new-default card shows "Default" badge | asserted |
| 6 Verify the previously default model card no longer shows the "Default" badge | condition holds | step 6 | old-default card has no "Default" badge | asserted |
| 7 Navigate to new chat and start a conversation | target page loads | step 7 | `/chat` loads to blank-composer state | asserted *("start a conversation" scoped to reaching the composer — see Automation Hints on why sending a message isn't required to prove the observable)* |
| 8 Verify that selected default model is used when starting a chat | condition holds | step 8 | `model-selector-button` text == Default model | asserted, confirmed live end-to-end |
| 9 Repeat steps 2–8 for High-tier and Low-tier selectors | same chain holds for all 3 tiers | step 9 | selector+badge mechanics repeated (steps 3–6 shape) for High-tier (confirmed live) and Low-tier (mechanism-verified, not independently re-executed) | **partial — clarification filed, EliteaAI/elitea-testing-public#1253** *(steps 7–8's "used when starting a chat" claim does not hold for High-tier — zero frontend consumers found — or Low-tier — consumed only by the Mermaid Quick Fix feature, a different surface; asserting it would be reverse-masking a false contract)* |
| Expected Final State: "Repeat steps 2–8 for High-tier and Low-tier" | condition holds | step 9 | same as row 9 | same disposition as row 9 |

**Axis 2 — Analyst additions**
- Step 2 (capture original values before mutating) — *added: this case
  mutates shared live project state (the whole `Private`/`399` project's LLM
  tier defaults); nothing in the case text acknowledges this or requires
  restoring it, but leaving it mutated would corrupt every other suite test
  that reads these values (e.g. ELITEA-2090's "default model is pre-selected
  in a new chat" assertion) — see § Cleanup.*
- Step 4's `POST` status/body assertion — *added: the case only describes
  the visible UI effect; asserting the underlying network call succeeded
  distinguishes "genuinely saved" from "UI optimistically updated but the
  save silently failed," which a DOM-only check can't tell apart (same
  reasoning ELITEA-2392 already applied to the vectorstorage-absence check).*
- Step 10 (restore original values) — *added, same reasoning as step 2.*

## Cleanup

**Real automation gap, not boilerplate — read before implementing.**

- Default and Low-tier: both had a concrete, non-blank value before this
  session's exploration (`Anthropic Claude 4.5 Sonnet` / `GPT-5.4-mini`) —
  restoring them is a normal "select the captured original value again"
  UI action, same mechanism as steps 3–4.
- **High-tier had NO value set before this session's exploration** (blank
  selector, no card carried a "High-Tier" badge). **The MUI Select dropdown
  offers no "clear"/blank option** — confirmed live, its `listbox` only ever
  lists selectable models, never an empty/"None" entry. There is currently
  no UI-only way to return a tier selector to "unset" once it has a value.
  - **This session's own exploration left the shared project's High-tier
    at "GPT-5.2"** (was unset before) — could not be reverted via UI. Flagged
    here so the implementer/reviewer knows this is a pre-existing state
    change on the shared `Private`/`399` project as of 2026-08-06, not
    something to "fix" by re-running this analysis.
  - **Implementer must resolve this before shipping**, options in
    likely-preference order: (a) if the underlying `POST
    /api/v2/configurations/models/{project_id}` payload supports clearing a
    tier field (e.g. `high_tier_default_model_id: null`) — capture the
    exact request body live (this session's network capture only retained
    the response, `{"result": "success"}`, not the request payload — verify
    the shape during the Automate phase) and use that directly for teardown
    of an originally-unset tier; (b) if no such payload shape exists, restore
    to a KNOWN value instead of "unset" and treat "was originally unset" as
    a state this test must not run against un-seeded (i.e. skip/seed rather
    than silently leave it worse than found) — flag to the lead if this
    turns out to be the only option, since it means the test can't safely
    run against an environment where High-tier starts unset.
- Use a `finally` block (or fixture teardown) around the mutation, mirroring
  the existing pattern in `test_conversation_management.py`
  (`finally: conversation_api.delete_conversation(...)`), so a mid-test
  failure still restores state.

## Concrete Handles (discovered during exploration)

All page-level testids below **already exist** on `automation/testids`
(added by the ELITEA-2392 implementation, `EliteaAI/EliteaUI@5119ba70` /
`EliteaAI/EliteaUI@ff547e50`) and are already wired in
`automation/pages/ai_providers_page.py` — this case reuses that page object,
it does not need a new one.

| Element | Locator | Provenance |
|---|---|---|
| LLMs section header | `AIProvidersPage.llms_section_header` (`ai-providers-section-llms`) | on `automation/testids` — reuse |
| Default tier selector (trigger) | `AIProvidersPage.llms_default_selector` (`ai-providers-section-llms-default-selector`) | on `automation/testids` — reuse |
| High-tier selector (trigger) | `AIProvidersPage.llms_high_tier_selector` (`ai-providers-section-llms-high-tier-model-selector`) | on `automation/testids` — reuse |
| Low-tier selector (trigger) | `AIProvidersPage.llms_low_tier_selector` (`ai-providers-section-llms-low-tier-model-selector`) | on `automation/testids` — reuse |
| Selector's clickable combobox (opens the listbox) | `[data-testid="{selector-testid}-combobox"]` — confirmed live: the shared `Select.SingleSelect` component auto-derives this suffix from the testid already threaded onto the field | pre-existing shared-component convention, confirmed live 2026-08-06 |
| Dropdown option (dynamic, per model) | `[data-testid="select-option-{model_id}<<>>{value}"]` — e.g. `select-option-gpt-5.4<<>>1`, `select-option-eu.anthropic.claude-sonnet-4-5-20250929-v1:0<<>>1` | pre-existing shared-`Select` convention (NOT added by 2392 — confirmed present on the shared component before this case), confirmed live 2026-08-06 — dynamic testid, template as a class constant per `.agents/testing.md` § Locator policy: `SELECT_OPTION = '[data-testid="select-option-{}"]'`, format with the model's own testid-suffix value (readable from the selector's own hidden `textbox` value, e.g. `gpt-5.4<<>>1`) |
| Configuration card (generic, repeated per card) | `AIProvidersPage.CONFIGURATION_CARD_SELECTOR` (`ai-provider-configuration-card`) | on `automation/testids` — reuse; **amended during implementation** — see `card_for_model()` row below, plain `.filter(has_text=...)` on this testid alone cannot exact-match (see § Implementer amendment) |
| Tier badge on a card ("Default" / "High-Tier" / "Low-Tier" text) | `AIProvidersPage.TIER_BADGE_SELECTOR` (`ai-provider-configuration-badge`) — added on all three conditional `Typography` blocks in `ConfigurationCard.jsx` (`isDefault`/`isHighTier`/`isLowTier`) | **added this implementation**, `EliteaAI/EliteaUI@4213b6c8` — on `automation/testids` |
| Card display-name (exact-match anchor) | `AIProvidersPage.CARD_NAME_SELECTOR` (`ai-provider-configuration-card-name`) — added on the `displayName` `Typography` alone, used via `AIProvidersPage.card_for_model()`'s `.filter(has=...)` | **added this implementation** (not anticipated by the original AFS handles table — see § Implementer amendment), `EliteaAI/EliteaUI@e1ea650c` — on `automation/testids` |
| New-chat model selector | `ChatPage.model_selector` (`model-selector-button`) — existing, `automation/pages/chat_page.py:133` | pre-existing, reuse — `get_selected_model()` method already returns its text |
| New-chat navigation | `ChatPage.navigate_to_chat()` (`/chat`) | pre-existing, reuse |

### Implementer amendment (2026-08-06, ELITEA-2397 implementation)

The original handles table proposed scoping a model's card via
`.filter(has=page.get_by_text(model_name, exact=True))` directly on
`CONFIGURATION_CARD_SELECTOR`. **This does not work as written**: the card's
`displayName` + `statusText` + tier-badge Typography render as SIBLING
elements with no whitespace separator in the concatenated text content (e.g.
`"GPT-5.4OK • Shared"`), so an exact-match filter tested against the whole
card's text never matches (confirmed live — the first test run of this
implementation timed out on a badge visibility wait because zero cards
matched). Resolved by adding a dedicated `ai-provider-configuration-card-name`
testid on the `displayName` Typography alone and filtering the outer card via
`.filter(has=<name-locator>)` instead — see
`AIProvidersPage.card_for_model()`. Full write-up:
`test-specs/settings-ai-providers/_surface.md` § "Resolved/added during
ELITEA-2397 implementation".

Also confirmed live: the dropdown option's runtime value (`SELECT_OPTION`
template argument) does **not** require reading the selector's hidden
textbox — it's derivable directly from the `section=llm` GET response body
(`items[].name` + `items[].project_id`, filtered by `items[].high_tier`/
`items[].low_tier` for those two tiers). See
`AIProvidersPage.pick_alternative_llm_model()` and the `_surface.md` note.

## Network Behavior
- `POST /api/v2/configurations/models/{project_id}` — fires on EVERY tier
  selector change (Default/High-tier/Low-tier alike), confirmed live,
  response `200` with body `{"result": "success"}`. Request payload shape
  not captured this session (network buffer had rotated the body out by the
  time it was queried) — implementer must capture it live during the
  Automate phase, both for the assertion in step 4 and for the teardown
  discussed in § Cleanup.
- Same three GET call shapes ELITEA-2392 already documented
  (`/configurations/models/{project_id}?...`, per-section and combined) fire
  again after the `POST`, refreshing the card list — this is what produces
  the badge swap in steps 5/6 without a manual page reload.

## Known Defects Found During Exploration
None — this is case-text drift (§ Case-text drift above), not a product
defect. Filed as a clarification: EliteaAI/elitea-testing-public#1253.

## Blocked Steps
None — all steps executable; step 9's Low-tier repeat and step 10's
High-tier-unset restoration are implementer-owned follow-ups (documented
above), not blockers on writing the test.

## Automation Hints
- Framework: Playwright + pytest (`.agents/testing.md`).
- Page objects: `AIProvidersPage` (existing, reuse) + `ChatPage` (existing,
  reuse `navigate_to_chat()` / `model_selector` / `get_selected_model()`).
  No new page object needed — only the one new testid (tier badge) on the
  existing `ConfigurationCard.jsx`.
- Step 7 ("start a conversation") is satisfied by reaching the blank-composer
  state and reading the model selector — the case's own step 8 only asks to
  verify the model, not the AI response; actually sending a message and
  waiting ~2s for a WebSocket reply would prove nothing extra about tier
  selection and would add avoidable flake/latency. If the implementer wants
  the fuller "used when starting a chat" claim (a completed exchange), that's
  a valid strengthening, not a requirement this AFS demands.
- Wait strategy: after clicking a tier's combobox, wait for the `listbox`
  role to be visible before clicking an option (standard Playwright
  web-first assertion) rather than a sleep. After selecting an option, wait
  for the `POST /api/v2/configurations/models/` response (`expect_response`)
  before asserting the badge swap — the DOM update is React-render-async
  relative to the network call, confirmed live it completes well within a
  normal element-timeout but a race is possible under load.
- Serial execution required (`.agents/testing.md` § Test data strategy) —
  this test mutates shared project state; it must not run concurrently with
  any other test reading/writing the same project's LLM configuration
  (notably ELITEA-2090's chat-default-LLM test, `test_conversation_management.py`).
- Model-name-matching gotcha: use EXACT text match (`exact=True`) when
  filtering cards/options by display name — confirmed live, some names are
  string-prefixes of others (`GPT-5.4` vs `GPT-5.4-mini`), so a substring
  `has_text` filter would false-positive-match both.
