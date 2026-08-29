# Test Case: Saving a new LLM model configuration persists after page reload

## Metadata
- **TMS ID**: ELITEA-2412
- **Source case**: `../onetest-ai-tm-Elitea/tests/automated-full-regression-ui/settings/ai-configuration/ELITEA-2412_saving-a-new-llm-model-configuration-persists-after-page-rel.md`
  (intake snapshot read directly; TMS module `settings-ai-configuration`)
- **Linked Story**: none (`requirements: []`)
- **Priority**: l3 (case frontmatter `priority: medium`). The covering spec's
  module-level `pytestmark` is already `p2`, and its own case (ELITEA-2395) is
  also `priority: medium` — so this extension inherits the correct marker and
  needs **no** per-function `@pytest.mark.pN` override (contrast
  ELITEA-2337/2286, where the priorities differed).
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` → DEV backend), project **400 "UI Testing"**
  (= `settings.ai_providers_seeded_project_id`)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot — cluster session with
  ELITEA-2413 / ELITEA-2414, 2026-08-30
- **Status**: extend-existing
- **Surface**: `settings-ai-providers-llms`

## Case-identity note (inherited, NOT re-filed)
The case says "LLM Models section" of an "AI Configuration" page. There is no
such page — the surface is Settings → **AI Providers** (`/settings/ai-providers`),
whose **LLMs** accordion holds these cards. Already filed as
EliteaAI/elitea-testing-public#1250 and documented in
`test-specs/settings-ai-providers/_surface.md` § Page identity; the covering
spec's module docstring already carries the note. Nothing new to file.

## Extension target

**Covering spec**:
`automation/tests/ui/settings/test_llm_model_create.py`
(class `TestCreateLlmModelConfiguration`, method
`test_create_llm_model_and_set_as_default`) — ELITEA-2395, **merged to
`origin/automation/base`** (verified with `git cat-file -e
origin/automation/base:automation/tests/ui/settings/test_llm_model_create.py`).

**Behavioural-overlap argument.** This case's steps 1-2 ("create a new LLM
model with Display Name / Name / valid credentials"; "click Save — verify the
card appears in the LLM Models section") are covered **verbatim in substance**
by the covering spec's Steps 2-12: it drives the same real UI flow
(`+` → LLM Model type card → Display Name → Name → saved credential → Save),
then asserts the card count grew by exactly one, that the card lands in the
LLMs "Other Providers" group, and that it carries an `OK •` status badge.
Re-implementing that half would duplicate ~60 lines of an already-merged spec
for zero new signal.

**Gap — the case's actual subject is untested.** The covering spec never
reloads. Its assertions all run inside the SPA session that created the record,
so they prove "the client re-rendered", not "the server persisted it". Grep
evidence: `grep -rn "reload" automation/tests/ui/settings/test_llm_model_create.py
automation/tests/ui/settings/test_llm_model_edit.py
automation/tests/ui/settings/test_set_llm_model_default_high_low_tier.py` →
**zero hits**. The covering spec's Step 13 does re-navigate
(`navigate_and_capture_llm_response()`, a fresh `goto`) and does then read the
new model out of the server's own `section=llm` response — which is close, but
(a) it is a soft-navigation helper aimed at the Default selector, not a reload,
and (b) it never asserts the CARD's own survival after a document reload, which
is this case's stated Expected Final State. So the gap is real but small: one
reload + a re-assert of the card. See § Gap assertions.

## Preconditions
- Logged in on localhost (dev-token auth, no Keycloak).
- Active project `400` ("UI Testing"). Not load-bearing beyond the fact that
  the project must expose a usable saved AI credential (below).
- A saved AI credential exists in the project. Live: exactly one, `elitea_title`
  `elps`, displayed **ELPS**, shared into every non-project (`include_shared=true`).
  The covering spec already selects it by title, never by list position.
- **Nothing about the LLMs section's existing contents is assumed** — the
  covering spec captures its own baseline count first.

## Test Data
| Field | Value used live | Note |
|---|---|---|
| Display Name | `Persist Test Model 2412` | The case's literal name is `"Persist Test Model"`. **Declared deviation**: the covering spec already generates a per-run unique name (`f"Autotest LLM Model {int(time.time())}"`) and the extension MUST keep that generator, not the case's fixed literal — a fixed name collides with a leftover from a previous failed run and the create then fails on a duplicate. The behaviour under test (persistence across reload) is name-agnostic. `toolkit-field-label-input` carries `maxlength="32"`, so any generated name must stay inside it. |
| Name (model id) | `gpt-4o` | The case's own value; already the covering spec's `MODEL_NAME`. |
| Credential | `ELPS` (`elitea_title` `elps`) | The case says only "valid credentials". |
| Context Window | `128000` (form default) | Asserted, never typed. |
| Max Output Tokens | `16000` (form default) | Asserted, never typed. |

## Test Steps (as executed live, 2026-08-30)

1. **Navigate** `${BASE_URL}/settings/ai-providers`.
   *Observed*: page title `AI Providers`; the LLMs accordion auto-expands
   (`aria-expanded="true"`); 12 LLM cards; Default `GPT-5.6 Luna`, High-tier
   `Bedrock-GPT-5.6-Terra`, Low-tier `GPT-5.6 Luna`.
   ⚠️ On the very first load of the session the LLMs accordion was found
   **collapsed** while TTS was expanded — a leftover `expandSection` route
   state from a previous session. After an explicit `page.reload()` the LLMs
   accordion reliably auto-expanded. Never assume expansion without asserting it.
2. **Click `+`** (`sidebar-create-button`) → lands on
   `/settings/create-ai-provider?viewMode=owner&from=ai-providers`.
3. **Click the `LLM Model` type card** (`toolkit-type-card-llm_model`) → lands on
   `/settings/create-ai-provider/llm_model?...`. Save is disabled.
4. **Fill Display Name** → the disabled ID field auto-derives
   (`Persist Test Model 2412` → `persist_test_model_2412`).
5. **Fill Name** `gpt-4o`. Context Window / Max Output Tokens already carry
   `128000` / `16000`. Save still **disabled**.
6. **Select the saved credential `ELPS`** → Save becomes **enabled**.
7. **Click Save** → app returns to `/settings/ai-providers`.
   *Observed*: 13 cards (12 + 1); the new card sits in the **`Other Providers`**
   group; its status reads **`OK • Local`**; LLMs accordion expanded.
8. **Reload the page** (`page.reload()`) — the case's step 3.
9. **Verify the card survived** — the case's step 4.
   *Observed after reload*: card `Persist Test Model 2412` present, still in
   the `Other Providers` group, status still `OK • Local`, card count still 13,
   LLMs accordion auto-expanded, Default selector unchanged (`GPT-5.6 Luna`).

**PASS** — the configuration persisted across a full document reload.

## Expected Results
- After Save, the LLMs section holds exactly one more card than the baseline,
  in the `Other Providers` group, with an `OK •` status.
- After a full page reload, that same card is **still present**, in the same
  group, with the same status, and the section count is unchanged.
- No console error is produced by the reload itself (see § Known Defects for the
  two errors that ARE expected, neither from the reload).

## Coverage Map

### Axis 1 — Case coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 — create LLM model (Display Name, Name, valid credentials) | completes, state updates | covering spec Steps 2-10 | `test_llm_model_create.py` Steps 2-10 | already covered |
| Step 2 — Save; card appears in the LLM Models section | card visible | covering spec Steps 10-12 (count +1, group, `OK •` badge) | `test_llm_model_create.py` Steps 11-12 | already covered |
| Step 3 — Reload the page | completes without error | **NEW** | § Gap assertions A | gap |
| Step 4 — card still present in the LLM Models section | condition holds | **NEW** | § Gap assertions B | gap |
| Expected Final State — card still present | — | **NEW** | § Gap assertions B | gap |
| Precondition — user logged in | — | `auth_state` (localhost bypass) | conftest | already covered |

### Axis 2 — Analyst additions (beyond the case text, each grounded)
| Addition | Why |
|---|---|
| After the reload, assert the card is still in the **`Other Providers` group** (not just present anywhere) | A persisted record that lost its provider grouping would still satisfy "card is present" while the section rendered wrongly. The group is server-derived, so it is part of what persistence must preserve. |
| After the reload, assert the card's status is still `OK •` | "The row came back" is weaker than "the row came back healthy" — a persisted-but-unconfigurable model (credential link lost on write) would show a non-OK status and still pass a bare presence check. |
| After the reload, assert the **card count is unchanged** vs the post-save count | Catches a duplicate-on-persist bug: the card being present says nothing about it being present *once*. |
| Assert the LLMs accordion is expanded after reload before reading cards | Accordion content **unmounts on collapse** (`AIProviderAccordion.jsx`), so a collapsed section produces a false "card missing". Live-confirmed hazard — see Step 1's note. |

## Gap assertions (implementer: append to the covering spec)

Insert a new step between the covering spec's Step 12 and Step 13 (i.e. after
the card/status assertions, **before** the Default-selector work, so the reload
observes a pure create and not a create+tier-change), and extend the docstring
+ `@allure.issue` set to name ELITEA-2412 as a second covered case.

```python
with allure.step("Step 13 (ELITEA-2412) — The new card survives a full page reload"):
    # ELITEA-2412: the case's own subject — persistence, not re-render.
    providers_page.reload_and_capture_llm_response()
    expect(providers_page.llms_section_header).to_have_attribute("aria-expanded", "true")
    expect(providers_page.card_in_group(OTHER_PROVIDERS_GROUP, display_name)).to_have_count(1)
    expect(providers_page.card_for_model(display_name)).to_contain_text("OK •")
    expect(providers_page.configuration_cards).to_have_count(initial_card_count + 1)
```

**New page-object method required** (`automation/pages/ai_providers_page.py`) —
mirror of the existing `navigate_and_capture_llm_response`:

```python
def reload_and_capture_llm_response(self) -> Response:
    """Reload the current page while capturing the `section=llm` models GET."""
    with self.page.expect_response(_is_llm_models_response, timeout=NAVIGATION_TIMEOUT) as response_info:
        self.page.reload()
    return response_info.value
```

⚠️ **Do NOT use `BasePage.reload_and_wait()`** — it reloads with
`wait_until="networkidle"` and then calls `wait_for_network()`, i.e. TWO
`networkidle` waits. This app holds a persistent Socket.IO polling transport
open on every page, which is exactly the structural race tracked as **#1847**
(`.agents/testing.md` § `networkidle` flake). Waiting on the product's own
`section=llm` response is the prescribed fix, and it is also the value the
spec already treats as its oracle.

Renumber the covering spec's existing Steps 13 → 14 (set-as-default) and
13-cleanup-half → 14-cleanup-half, or label the insert `Step 12b` — the
implementer's call; the AFS only requires the reload to sit between the card
assertions and the Default work.

## Cleanup
Unchanged from the covering spec, and already correct: its `finally` restores
the original Default (guarded by `default_changed`, set **before** the mutating
call — the ordering `.agents/testing.md` § Teardown-guard ordering requires)
and deletes the created configuration, then asserts the card count returned to
baseline. This extension adds **no new mutation**, so it adds no new teardown
obligation. Verified live: after deleting the model and restoring the Default,
the project was back to 12 cards / `GPT-5.6 Luna` / `Bedrock-GPT-5.6-Terra` /
`GPT-5.6 Luna`.

## Concrete Handles (discovered/confirmed live this session)
All testid-only; every one below was exercised in this session.

| Element | Handle | Provenance |
|---|---|---|
| Page title | `[data-testid="ai-providers-page-title"]` | on-main ✓ (pre-existing, in `AIProvidersPage.page_title`) |
| `+` create control | `[data-testid="sidebar-create-button"]` | on-main ✓ (shared sidebar testid) |
| LLM Model type card | `[data-testid="toolkit-type-card-llm_model"]` | on-main ✓ |
| LLMs accordion header | `[data-testid="ai-providers-section-llms"]` (+ `aria-expanded`) | existing `llms_section_header` |
| Display Name input | `[data-testid="toolkit-field-label-input"]` | existing (`maxlength="32"`) |
| Read-only ID input | `[data-testid="toolkit-field-elitea_title-input"]` | existing, `disabled` |
| Model identifier input | `[data-testid="toolkit-field-name-input"]` | existing `FIELD_INPUT` template |
| Credential picker | `[data-testid="toolkit-credential-select--combobox"]` | existing (double dash is real) |
| Saved-credential option | `[data-testid='select-option-{"kind":"saved","elitea_title":"elps","private":false}']` | existing `SAVED_CREDENTIAL_OPTION` |
| Save | `[data-testid="credential-form-save-button"]` | existing |
| Configuration card | `[data-testid="ai-provider-configuration-card"]` | existing `CONFIGURATION_CARD_SELECTOR` |
| Card display name | `[data-testid="ai-provider-configuration-card-name"]` | existing `CARD_NAME_SELECTOR` (EliteaAI/EliteaUI@e1ea650c) |
| Card status | `[data-testid="ai-provider-configuration-card-status"]` | existing `CARD_STATUS_SELECTOR` |
| Provider group / name | `[data-testid="ai-providers-configuration-group"]` / `-group-name` | existing |

**No new testid is needed for this case.** Every handle the extension touches
already exists and is already wired into `AIProvidersPage`.

## Network Behavior
- Create Save → `POST`/`PUT` on the configurations API, then the page re-fetches:
  `GET /api/v2/configurations/models/400?include_shared=true` (summary) plus one
  `&section={llm,embedding,vectorstorage,image_generation,asr,tts}` per section.
- Reload → the same fan-out repeats from a cold document. `section=llm` is the
  one to wait on; its body carries `items[]` (each with `name`, `project_id`,
  `display_name`, `high_tier`/`low_tier` flags) plus the current
  `default_model_name` / `high_tier_…` / `low_tier_…`.
- The created model appears in that body as `name: "gpt-4o", project_id: 400`
  (option value `gpt-4o<<>>400`) — a **project-local** model, unlike the shared
  models which carry `project_id: 1`.

## Known Defects Found During Exploration
**None new.** Exactly two console errors were produced across the whole
cluster session (verified from the session's own console log, not from the
`all: true` buffer which also carries a previous session's messages):

1. React `Each child in a list should have a unique "key" prop` from
   `CredentialTypeSelector.jsx` — fires on the **create type-picker page only**.
   Pre-existing, already tracked as **#656** and already excluded by the
   covering spec by scoping its console axis to after the type-picker.
2. `404 (Not Found) @ /api/v2/configurations/configuration/400/81` — the app
   re-fetching the record it just **deleted**, during teardown. Already
   documented in the covering spec ("asserted BEFORE the delete: the app
   re-fetches the deleted record afterwards and logs a 404").

The reload itself produced **zero** console errors.

## Blocked Steps
None.

## Automation Hints
- **The reload is the whole point — do not substitute a `goto`.** `navigate()`
  is a fresh `goto` of the same URL and would technically re-fetch, but
  `page.reload()` is what the case asks for and is the only form that also
  re-runs the app's boot path. (The covering spec's Step 13 `goto` is why this
  is `extend-existing` rather than `already-covered` — close, but not the
  case's stated observable.)
- **Never wait on `networkidle`** here (#1847) — see § Gap assertions.
- **Assert `aria-expanded="true"` on the LLMs header before counting cards.**
  Accordion content unmounts when collapsed, and the session's first load
  arrived with LLMs collapsed / TTS expanded from stale route state.
- Card identity: use `AIProvidersPage.card_for_model()` / `card_in_group()` —
  a `has_text` filter on the outer card testid does NOT work, because
  displayName + status + badge concatenate without separators
  (`"GPT-5.4OK • Shared"`); the page object already filters via the dedicated
  `-card-name` testid.
- Status text for a project-local model is `OK • Local` (shared ones read
  `OK • Shared`). Assert the `OK •` prefix, as the covering spec already does,
  rather than the full string.
- Serial only — this spec mutates project-level configuration.
