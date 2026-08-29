# Test Case: Editing an existing configuration persists after page reload

## Metadata
- **TMS ID**: ELITEA-2413
- **Source case**: `../onetest-ai-tm-Elitea/tests/automated-full-regression-ui/settings/ai-configuration/ELITEA-2413_editing-an-existing-configuration-persists-after-page-reload.md`
  (intake snapshot read directly; TMS module `settings-ai-configuration`)
- **Linked Story**: none (`requirements: []`)
- **Priority**: l3 (case frontmatter `priority: medium`). The covering spec
  (ELITEA-2396) is also `priority: medium` and its module `pytestmark` is
  already `p2` — no per-function marker override needed.
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` → DEV backend), project **400 "UI Testing"**
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login)
- **Analyst**: qa-engineer (Sage), analyst slot — cluster session with
  ELITEA-2412 / ELITEA-2414, 2026-08-30
- **Status**: extend-existing
- **Surface**: `settings-ai-providers-llms`

## Case-identity note (inherited, NOT re-filed)
"AI Configuration → LLM Models section" is Settings → **AI Providers**
(`/settings/ai-providers`) → the **LLMs** accordion. Filed long ago as
EliteaAI/elitea-testing-public#1250; the covering spec's docstring already
carries it.

## Extension target

**Covering spec**:
`automation/tests/ui/settings/test_llm_model_edit.py`
(class `TestEditLlmModelConfiguration`, method
`test_edit_llm_model_display_name`) — ELITEA-2396, **merged to
`origin/automation/base`** (verified via `git cat-file -e
origin/automation/base:automation/tests/ui/settings/test_llm_model_edit.py`).

**Behavioural-overlap argument.** This case IS ELITEA-2396 plus a reload. Its
step 1 ("click an existing LLM model card and change the Display Name to
`Reload Test Model`") and step 2 ("click Save") are the covering spec's Steps
2-5 exactly: it opens a card, asserts the edit form is pre-populated and inert
while pristine, rewrites the Display Name, and saves. Its Step 6 then asserts
the section reflects the new name **in place** — new name count 1, old name
count 0, total card count unchanged (no orphan, no duplicate). That is a
stronger version of this case's step 4 in every respect except one: it is read
inside the same SPA session.

**Gap — persistence is never proven.** `grep -rn "reload"
automation/tests/ui/settings/test_llm_model_edit.py` → **zero hits**. Every
post-save assertion runs against the client's re-render of its own mutation
response, so a write that never reached the server (or one the server accepted
and then silently dropped) would still go green. This case's steps 3-4 close
that hole with a reload and a re-read. That is the entire delta — one reload
plus three re-assertions. See § Gap assertions.

## Preconditions
- Logged in on localhost; active project `400`.
- **An existing LLM model configuration to edit.** The covering spec already
  creates its own seed in Step 0 rather than renaming a shared model, and this
  extension MUST keep that: the case says "click on AN existing LLM model card",
  and renaming a live shared model (e.g. the project Default) would alter what
  every other spec on this surface reads. Declared deviation, inherited from
  ELITEA-2396 — the behaviour under test is identical, and a self-created
  subject makes the case safely repeatable.
- Saved credential `ELPS` available in the project (needed by the seed create).

## Test Data
| Field | Value used live | Note |
|---|---|---|
| Seed Display Name | `Persist Test Model 2412` | Live, the subject was the configuration created moments earlier in this same cluster session (id **81**). In the spec, it is the covering spec's own generated seed. |
| Edited Display Name | `Reload Test Model 2413` | The case's literal is `"Reload Test Model"`. **Declared deviation**: keep the covering spec's per-run suffix generator — `toolkit-field-label-input` carries `maxlength="32"`, and the covering spec already trims the suffix so the longer of the two names fits. A fixed literal also collides with leftovers from a failed run. |
| Name (model id) | `gpt-4o` | unchanged by the edit |
| Credential | `ELPS` | unchanged by the edit |

## Test Steps (as executed live, 2026-08-30)

1. **Click the existing card** `Persist Test Model 2412` in the LLMs section.
   *Observed*: navigates to `/settings/edit-ai-provider/81?from=ai-providers`;
   the form is pre-populated — Display Name `Persist Test Model 2412`, ID
   `persist_test_model_2412` (**disabled**), Name `gpt-4o`, credential `ELPS`;
   **Save and Discard are both disabled** while pristine.
2. **Change the Display Name** to `Reload Test Model 2413`.
   *Observed*: Save and Discard both become **enabled**; the disabled ID field
   **re-derives** to `reload_test_model_2413` (live behaviour, already recorded
   by the covering spec as an observation, not a defect).
3. **Click Save** — the case's step 2.
   *Observed*: app returns to `/settings/ai-providers`; the LLMs section shows
   `Reload Test Model 2413`, the old name is **gone**, total card count
   unchanged at 13 (rename in place — no orphan, no duplicate).
4. **Reload the page** (`page.reload()`) — the case's step 3.
5. **Verify the card shows the new name** — the case's step 4.
   *Observed after reload*: `Reload Test Model 2413` present, still in the
   **`Other Providers`** group, status still `OK • Local`; `Persist Test Model
   2412` **absent**; card count still 13; the three LLM tier selectors
   unchanged (`GPT-5.6 Luna` / `Bedrock-GPT-5.6-Terra` / `GPT-5.6 Luna`).

**PASS** — the edit persisted across a full document reload, under the new name
only.

## Expected Results
- After Save, the LLMs section shows the new Display Name and not the old one,
  with an unchanged card count.
- After a full reload, the card is **still** under the new name, still in the
  same group with the same status, the **old name is still absent**, and the
  card count is still unchanged.

## Coverage Map

### Axis 1 — Case coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 — click an existing card, change Display Name | control responds | covering spec Steps 2-4 (form pre-populated, pristine-inert, rename enables Save/Discard) | `test_llm_model_edit.py` Steps 2-4 | already covered |
| Step 2 — click Save | expected next state | covering spec Steps 5-6 (returns to list; new name count 1, old name count 0, total unchanged) | `test_llm_model_edit.py` Steps 5-6 | already covered |
| Step 3 — reload the page | completes without error | **NEW** | § Gap assertions A | gap |
| Step 4 — the card shows the new name (not the previous one) | condition holds | **NEW** | § Gap assertions B+C | gap |
| Expected Final State — card shows `Reload Test Model` | — | **NEW** | § Gap assertions B | gap |
| Precondition — user logged in | — | `auth_state` | conftest | already covered |

### Axis 2 — Analyst additions (each grounded)
| Addition | Why |
|---|---|
| After reload, assert the **old name has count 0** (not merely that the new name exists) | The case's own parenthetical is "(not the previous name)". Without it, a server that persisted a COPY under the new name while leaving the original row intact would pass. Live-confirmed the old name is genuinely gone. |
| After reload, assert the **total card count is unchanged** | Same failure mode from the other direction: catches a rename-implemented-as-create. |
| After reload, assert the card is still in the `Other Providers` group with status `OK •` | A rename must not disturb server-derived grouping or the credential link. Both are re-derived from the server on reload, so this is exactly what a reload is able to check and an in-session re-render is not. |
| Assert `aria-expanded="true"` on the LLMs header before counting | Accordion content unmounts on collapse — a collapsed section reads as "card missing". |

## Gap assertions (implementer: append to the covering spec)

Append after the covering spec's Step 6, **before** the existing "Axis 2 — No
console errors before teardown" step (that step must stay last, since teardown's
delete provokes an expected 404). Extend the docstring + `@allure.issue` set to
name ELITEA-2413 as a second covered case.

```python
with allure.step("Step 7 (ELITEA-2413) — The rename survives a full page reload"):
    # ELITEA-2413: the case's own subject — the write reached the server,
    # not just the client's re-render of its own mutation response.
    providers_page.reload_and_capture_llm_response()
    expect(providers_page.llms_section_header).to_have_attribute("aria-expanded", "true")
    expect(providers_page.card_for_model(edited_display_name)).to_have_count(1)
    expect(providers_page.card_for_model(seed_display_name)).to_have_count(0)
    expect(providers_page.configuration_cards).to_have_count(initial_card_count + 1)
    expect(providers_page.card_for_model(edited_display_name)).to_contain_text("OK •")
```

`reload_and_capture_llm_response()` is the **same new page-object method**
ELITEA-2412's AFS specifies (`automation/pages/ai_providers_page.py`) — whichever
of the two units lands first adds it; the second reuses it.

⚠️ **Do NOT use `BasePage.reload_and_wait()`** — two `networkidle` waits against
an app that holds a persistent Socket.IO poll open: the #1847 race
(`.agents/testing.md`). Wait on the product's own `section=llm` response instead.

## Cleanup
Unchanged from the covering spec, and already correct: its `finally` calls
`_delete_model_if_present(..., [live_display_name, seed_display_name,
edited_display_name])` — it looks the name up rather than assuming which of the
two is live, so a failure anywhere between the rename and the verification
still tears down. The reload adds no new mutation and therefore no new teardown
obligation. Verified live: the configuration was deleted through the real
card → three-dot → type-to-confirm flow and the section returned to its
baseline 12 cards.

## Concrete Handles (confirmed live this session)
| Element | Handle | Provenance |
|---|---|---|
| Card (click target) | `[data-testid="ai-provider-configuration-card"]` filtered by `[data-testid="ai-provider-configuration-card-name"]` | existing `AIProvidersPage.open_model_card()` |
| Edit form URL | `/settings/edit-ai-provider/<id>` | existing `EDIT_URL_PATTERN` |
| Display Name input | `[data-testid="toolkit-field-label-input"]` | existing (`maxlength="32"`) |
| Read-only ID input | `[data-testid="toolkit-field-elitea_title-input"]` | existing, `disabled`, re-derives from the label |
| Save / Discard | `[data-testid="credential-form-save-button"]` / `credential-form-discard-button` | existing; both disabled while pristine |
| Card name / status | `[data-testid="ai-provider-configuration-card-name"]` / `-status` | existing |
| Provider group | `[data-testid="ai-providers-configuration-group"]` / `-group-name` | existing |
| Delete (teardown) | `controls-menu-button` → `delete-credentials-menuitem` → `delete-confirm-name-input` → `delete-confirm-button` | existing |

**No new testid needed.** One live gotcha for the implementer: the
`delete-confirm-name-input` testid sits on the MUI **`FormControl` wrapper**,
not the `<input>` — filling it directly errors with *"Element is not an
`<input>`…"*; the existing page object already targets the inner field.

## Network Behavior
- Save (edit) → the configuration `PUT`, then the standard page re-fetch
  fan-out (`configurations/models/400?include_shared=true` + one call per
  `section=`).
- Reload → the same fan-out from a cold document; `section=llm`'s body is the
  oracle (its `items[]` entry for this model carries the NEW `display_name`).

## Known Defects Found During Exploration
**None new.** The edit + save + reload path produced **zero** console errors.
The session's only two errors were the pre-existing type-picker React
`unique key` warning (**#656**, create flow only) and the expected post-delete
404 re-fetch of the deleted record (`/api/v2/configurations/configuration/400/81`),
which the covering spec already documents and asserts around.

## Blocked Steps
None.

## Automation Hints
- The reload must be a real `page.reload()`; a `goto` of the same URL is not
  what the case asks for.
- Never `networkidle` (#1847).
- Assert the accordion is expanded before counting cards.
- Identify cards via `card_for_model()`; a `has_text` filter on the outer card
  testid never matches (name + status + badge concatenate with no separator).
- Serial only — this spec creates, renames and deletes a real configuration in
  the shared project.
