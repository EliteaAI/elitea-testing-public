# Test Case: Create a new LLM model configuration

## Metadata
- **TMS ID**: ELITEA-2395
- **Linked Story**: none
- **Priority**: l3 (frontmatter `priority: medium`; matches the folder's
  established medium→l3 mapping — ELITEA-2392, ELITEA-2397)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids` @ `7418c06f`, DEV backend), project `UI Testing` (id 400)
- **User set**: `${TEST_USER}` (via `auth_state` fixture — `VITE_DEV_TOKEN` on
  localhost, no login needed)
- **Analyst**: qa-engineer (analyst slot), 2026-08-29, batch `settings-w10`
- **Status**: ready-for-automation
- **Surface digest**: `test-specs/settings-ai-providers/_surface.md`

## Case-identity note (read first — same root cause as ELITEA-2392)

The case says "Settings → AI Configuration". **No such page or nav item exists.**
Fully documented + filed against ELITEA-2392 (clarification
EliteaAI/elitea-testing-public#1250). The real page is **AI Providers**
(`/settings/ai-providers`); its **LLMs** accordion (case: "LLM Models" /
"Integrations section" — same cosmetic drift) is what this case exercises.

## Case-text drift specific to THIS case — filed as EliteaAI/elitea-testing-public#1985

- **Step 11** — *"under the 'Other LLM providers' section"*. Live, the LLMs
  accordion groups its cards under headings **`OpenAI` / `Anthropic` /
  `Other Providers`** (`ConfigurationSection.jsx:17-23`, `GROUP_ORDER`). It is a
  **group inside the LLMs section**, named **"Other Providers"** — not a section
  of its own. A newly created custom model does land in it (verified live).
- **Step 13** — *"set as default in top menu"*. There is no "top menu". The
  control is the **`Default`** selector at the top of the LLMs accordion
  (`ai-providers-section-llms-default-selector-combobox`). Verified live.
- Per the reverse-masking guard this AFS asserts the **live** contract.

## Preconditions
- `auth_state` fixture (localhost dev-token bypass).
- Active project has ≥1 usable **AI Credential**. Verified live: a SHARED
  credential named **`ELPS`** is visible in every non-public project
  (`include_shared=true`) — see `_surface.md` § AI Credentials. The test picks a
  credential by its `elitea_title` (`elps`), never by list position.
- **This test MUTATES shared, live project configuration** — it creates a real
  LLM model configuration in project 400 and (step 13) temporarily reassigns the
  project's **Default LLM**, which every other UI test in this suite reads.
  § Cleanup is mandatory, not optional.

## Test Data

| Field | Value | Note |
|---|---|---|
| Display Name | `Autotest LLM Model <run-suffix>` | case says `Autotest LLM Model`; **append a per-run suffix** so a leaked leftover can never collide or be silently reused |
| Name (model identifier) | `gpt-4o` | case's own value; also the `{name}` half of the Default-selector option testid |
| Context Window | `128000` | **already the form default** — assert it rather than typing it (see § Automation Hints) |
| Max Output Tokens | `16000` | **already the form default** — same |
| Ai Credentials | saved credential `elps` (displayed `ELPS`) | |

## Test Steps

| # | Action | Expected (verified live 2026-08-29) |
|---|---|---|
| 1 | `/settings/ai-providers` loads; capture the LLMs card count | page title `AI Providers`; `ai-providers-section-llms` present; 12 `ai-provider-configuration-card` nodes in this session |
| 2 | Click `sidebar-create-button` | navigates to `/settings/create-ai-provider?viewMode=owner&from=ai-providers`, a 12-card type picker renders |
| 3 | Click `toolkit-type-card-llm_model` | navigates to `/settings/create-ai-provider/llm_model?viewMode=owner&from=ai-providers`; form renders with `toolkit-field-label-input` |
| 4-5 | Fill Display Name | `toolkit-field-label-input` holds the typed value; `toolkit-field-elitea_title-input` auto-fills the snake_case slug (see ELITEA-2409) |
| 6 | Fill Name | `toolkit-field-name-input` = `gpt-4o` |
| 7 | Context Window | `toolkit-field-context_window-input` value is already `128000` |
| 8 | Max Output Tokens | `toolkit-field-max_output_tokens-input` value is already `16000` |
| 9 | Open `toolkit-credential-select--combobox`, pick the saved `ELPS` option | combobox text becomes `ELPS`; `credential-form-save-button` becomes **enabled** |
| 10 | Click `credential-form-save-button` | POST succeeds; app navigates back to `/settings/ai-providers` |
| 11 | Find the new card in the LLMs section | card count 12 → **13**; a card whose `ai-provider-configuration-card-name` equals the Display Name exists, **inside the `Other Providers` group** |
| 12 | Read the card's content | name node = Display Name; status badge text = `OK • Local` (concatenated card text observed: `Autotest LLM ModelOK • Local`) |
| 13 | Open `ai-providers-section-llms-default-selector-combobox`; capture the current default; select the new model's option; then restore | the new model appears as `select-option-gpt-4o<<>>400`; after selecting, the combobox label reads the new Display Name **and** the card gains an `ai-provider-configuration-badge` reading `Default` |

## Expected Results
1. A new LLM model configuration is created from the "+" → LLM Model flow with
   only Display Name + Name + an existing credential supplied (the two numeric
   fields carry usable defaults).
2. The card lands in the **LLMs → Other Providers** group with the Display Name
   and an `OK • …` status badge.
3. The new model is offered by, and can be assigned through, the LLMs section's
   **Default** selector, and the assignment is reflected on the card as a
   `Default` badge.

## Coverage Map

### Axis 1 — every case element
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` fixture | fixture | covered (setup) |
| 1. Navigate Settings → AI Configuration | page loads | step 1 (real page = AI Providers) | `ai-providers-page-title` == `AI Providers` | covered (identity drift, #1250) |
| 2. Click "+" in Integrations header | control responds | step 2 | URL == `/settings/create-ai-provider?…` | covered |
| 3. Select "LLM Model" | next state shown | step 3 | URL == `/settings/create-ai-provider/llm_model?…` + form present | covered |
| 4. Fill required fields | fields accept input | steps 4-9 | per-field value assertions | covered (decomposed) |
| 5. Display Name `Autotest LLM Model` | accepted | step 4-5 | `toolkit-field-label-input` value | covered (suffixed, see § Test Data) |
| 6. Name `gpt-4o` | accepted | step 6 | `toolkit-field-name-input` value | covered |
| 7. Context Window `128000` | accepted | step 7 | value assertion on the default | covered |
| 8. Max Output Tokens `16000` | accepted | step 8 | value assertion on the default | covered |
| 9. Credentials: existing credential | accepted | step 9 | combobox text == `ELPS`; Save enabled | covered |
| 10. Click Save | next state shown | step 10 | URL back at `/settings/ai-providers` | covered |
| 11. Card appears under "Other LLM providers" | holds | step 11 | card-name node exists AND is inside the `Other Providers` group container | covered — live label is `Other Providers`, drift #1985; **needs the group testid below** |
| 12. Card shows Display Name + status badge | holds | step 12 | name node text; card text contains `OK •` | covered |
| 13. Can be set as default in top menu | holds | step 13 | option present → select → combobox label + `Default` badge | covered — "top menu" = LLMs `Default` selector, drift #1985 |

### Axis 2 — asserted beyond the case
| Extra observable | Why (grounded) |
|---|---|
| LLMs card count 12 → 13 | proves a **create**, not a silent overwrite of an existing card — ELITEA-2396 exercises the update path and must stay distinguishable |
| Save button disabled *before* the credential is chosen, enabled after | the credential is the last required field; the transition is the honest proof the form knows the record is complete |
| The exact `Default` value in place before step 13, restored after | § Cleanup obligation; asserting the restore is what makes the mutation safe for the rest of the suite |
| No console errors on the create form and on `/settings/ai-providers` | verified live: clean `goto` of each is **0 errors**; the React `key` warning belongs to the **type-picker** page only (#656) — see § Automation Hints |

## Cleanup (MANDATORY — this test mutates a shared project)

1. **Restore the Default LLM** captured in step 13 by re-selecting its option.
   Verified live: the round trip is lossless (`GPT-5.6 Luna` →
   `Autotest LLM Model` → `GPT-5.6 Luna`, card badge followed both ways).
   ⚠️ There is **no "unset"/blank option** in these selectors (`_surface.md`) —
   if the Default happens to be unset at test start, do NOT set it; skip step 13's
   mutation and fail loudly instead of leaving the project altered.
2. **Delete the created model**: click its card → `controls-menu-button` →
   `delete-credentials-menuitem` → type the Display Name into
   `delete-confirm-name-input` → `delete-confirm-button`. Verified live end to
   end; the card count returns to its starting value.
3. Run cleanup in a `finally` so a mid-test failure still tears down.

## Concrete Handles (discovered live; **testid-only**, `.agents/testing.md` § Locator policy)

| Purpose | Handle | Provenance (fresh `git fetch origin`, 2026-08-29) |
|---|---|---|
| "+" create button | `sidebar-create-button` | on-main ✓ |
| LLM Model type card | `toolkit-type-card-llm_model` (dynamic `toolkit-type-card-{}`) | on-main ✓ |
| Display Name input | `toolkit-field-label-input` | on-main ✓ |
| ID (read-only) input | `toolkit-field-elitea_title-input` | on-main ✓ |
| Name input | `toolkit-field-name-input` | on-main ✓ |
| Context Window input | `toolkit-field-context_window-input` | on-main ✓ |
| Max Output Tokens input | `toolkit-field-max_output_tokens-input` | on-main ✓ |
| Ai Credentials select | `toolkit-credential-select-` / clickable `toolkit-credential-select--combobox` | on-main ✓ — **the trailing dash is real**: the JSX is `toolkit-credential-select-${type}` (`CredentialsSelect.jsx:519`) and `type` is empty on this form |
| Saved-credential option | `[data-testid='select-option-{{"kind":"saved","elitea_title":"{}","private":false}}']` | on-main ✓ (shared `Select` convention) |
| Save / Cancel | `credential-form-save-button` / `credential-form-discard-button` | on-main ✓ |
| LLMs section root | `ai-providers-section-llms` | on-main ✓ |
| LLMs Default selector | `ai-providers-section-llms-default-selector-combobox` | on-main ✓ |
| Default-selector option | `[data-testid="select-option-{name}<<>>{project_id}"]` e.g. `select-option-gpt-4o<<>>400` | on-main ✓ |
| Model card / card name / tier badge | `ai-provider-configuration-card` / `-card-name` / `ai-provider-configuration-badge` | on-main ✓ — reuse `AIProvidersPage.card_for_model()` (`.filter(has=…)`, never `has_text` on the outer card — `_surface.md`) |
| Delete flow | `controls-menu-button` → `delete-credentials-menuitem` → `delete-confirm-name-input` → `delete-confirm-button` (`delete-confirm-entity-name` shows the name) | on-main ✓ (`delete-credentials-menuitem` is composed at runtime by `DotMenu.jsx:58` from `key: 'delete-credentials'`, present on `origin/main`; the two-stage closure grep cannot see composed testids) |

### testid needed (ONE — step 11's group placement)

| Testid to add | Element | How |
|---|---|---|
| `ai-providers-configuration-group` | the per-group `<Box>` in `ConfigurationSection.jsx:180-183` | static `data-testid`, repeated per group — same pattern as `ai-provider-configuration-card` |
| `ai-providers-configuration-group-name` | the group-label `<Typography>` at `ConfigurationSection.jsx:184-189` | static `data-testid` — same pattern as `ai-provider-configuration-card-name`, and needed for the same reason: the group `Box` concatenates its label with every card's text, so `has_text` on the group cannot identify it |

Then the assertion is `group.filter(has=<group-name locator with text "Other
Providers">)` containing the card locator — the exact `card_for_model()` shape.
**Do not** rung down to a role/text handle (`.agents/role-overrides.md`).

## Network Behavior
- Page load fires the three GET shapes documented in `_surface.md` § Network.
- **Save** issues the create POST and the app then refetches
  `GET /api/v2/configurations/configurations/{project_id}?…` — the card list
  re-renders from the refetch, no manual reload needed.
- **Setting the Default** fires `POST /api/v2/configurations/models/{project_id}`
  (body `{name, target_project_id, section:"llm"}`) → 200 `{"result":"success"}`,
  then a GET refetch. No separate Save.
- The `{project_id}` path segment is the honest oracle for the active project id
  — never hardcode `400`.

## Known Defects Found During Exploration
- **EliteaAI/elitea-testing-public#1984** (filed this session) — the required
  `Name` field does not gate Save on this same form. It does **not** affect this
  case (this case fills Name); it is ELITEA-2408's subject.
- Post-delete, the app fires `GET /api/v2/configurations/configuration/{project}/{id}`
  for the just-deleted record and logs a **404** console error. Cosmetic refetch
  race; it only matters if the test asserts "no console errors" *after* cleanup —
  so assert the console axis **before** teardown.

## Blocked Steps
None.

## Automation Hints
- Page object: extend `automation/pages/ai_providers_page.py` (`AIProvidersPage`
  already owns `create_button`, `click_type_card`, `card_for_model`,
  `card_tier_badge`, `select_tier_model`). The form itself is the shared
  `CredentialFormFieldsMixin` (`display_name_input`, `id_input`, `save_button`,
  `FIELD_INPUT`) — reuse it; a new `LlmModelFormPage`-style class should inherit
  the mixin rather than redeclare the field testids.
- **After a direct `goto` to `/settings/create-ai-provider/llm_model` the form
  fields take a few seconds to mount** (the schema is fetched first). Wait on
  `toolkit-field-label-input`, never on navigation alone — a `fill()` immediately
  after `goto` fails with "does not match any elements" (hit live this session).
- **A dirty create form arms a native `beforeunload` dialog.** Reloading or
  `goto`-ing away mid-edit raises it and blocks every subsequent Playwright call
  until handled. Prefer navigating via the app (Save/Cancel), or register a
  dialog handler.
- Context Window / Max Output Tokens are **pre-filled defaults** (`128000` /
  `16000`), which happen to equal the case's values. Assert them; typing them is
  a no-op that proves nothing.
- Console assertion: use `utils/console_errors.collect_console_errors()` (URL-
  bearing). Carry the `#1971` URL-keyed filter — this flow switches project scope.
  Expect the `#656` React `key` warning **only if** the test walks through the
  type-picker page; a direct `goto` to the typed create route avoids it.
- Steps wrapped in `with allure.step("Step N — …")`. Markers: `p2`/`p3` per
  `pytest.ini`, plus `regression` and the settings feature marker.
