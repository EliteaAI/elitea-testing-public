# Test Case: Edit Credential — Rename

## Metadata
- **TMS ID**: ELITEA-1963
- **Linked Story**: none
- **Priority**: l1 (case frontmatter: `critical`; case body header says `high` —
  same class of frontmatter/body priority inconsistency already documented in
  ELITEA-1971's and ELITEA-1974's AFS; frontmatter is treated as authoritative
  per that established convention. Not filed as a defect — case-authoring nit,
  not a product bug.)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend, project `Private` /
  `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (localhost `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation
- **Case-gate note**: case frontmatter carries `status: draft`,
  `execution_type: manual`. Per `.agents/test-automation.yaml` § `intake`,
  `status: draft` is the intake-eligible value for this project (cases
  awaiting automation), not an exclusion — this confirms the case is
  in-scope, not a gate finding. Proceeded to full execution.

## Preconditions
- User is logged in to Elitea (on localhost, `auth_state` fixture skips
  login).
- A project is selected/accessible (`Private`, id `399` in this run).
- The Credentials section is accessible (`/credentials/all`,
  `/credentials/create-credential/{type}`).
- No pre-seeded credential is required — this case creates its own via the
  UI (case Step 1), unlike ELITEA-1974 which needed pre-seeded data to prove
  relative list ordering. Rename/reload/persist assertions only need the one
  credential this case creates.

## Test Data

### generate-per-test (created in test setup step, cleaned up in its own teardown)
- Initial Display Name: `autotest_cred_edit_<ts>` (timestamp suffix
  recommended for the implementer to avoid cross-run name collisions in a
  shared DEV project — the case's own literal test data omits a suffix,
  live-verified this run using the literal un-suffixed name with no
  collision, but a shared project makes collision plausible across parallel
  runs).
- Credential type: Github (`/credentials/create-credential/github`).
- Base Url: `https://api.github.com` (pre-filled default on the Github
  create form, not touched by this case — Auth left at default "Anonymous",
  matching the case's scope of only exercising rename, not credential
  validity).
- Renamed Display Name: `autotest_cred_renamed_<ts>` (same suffix
  reasoning).

## Test Steps

1. Navigate to `${BASE_URL}/credentials/create-credential/github` and create
   a credential with Display Name `autotest_cred_edit`.
   - **Verify**: form loads (confirmed live: Display Name, ID *, Base Url *,
     Auth radio group, "Test connection" button); Save is **disabled**
     before any Display Name is entered (confirmed live); typing the
     Display Name live-mirrors it into the disabled ID field
     (`autotest_cred_edit`) and enables Save (confirmed live). Clicking Save
     fires `POST /api/v2/configurations/configurations/399` → **200 OK**
     (confirmed live via `browser_network_requests`), then the app
     redirects to `${BASE_URL}/credentials/all` where the new
     `autotest_cred_edit` card is visible (confirmed live via snapshot,
     credential numeric id `1596` in this run).

2. Open the credential detail page (click the `autotest_cred_edit` card).
   - **Verify**: page loads at
     `${BASE_URL}/credentials/all/1596?viewMode=owner&name=autotest_cred_edit`
     (confirmed live), Display Name field shows `autotest_cred_edit`
     (confirmed live), ID field shows `autotest_cred_edit` and is
     **disabled** (confirmed live), Save and Discard are both disabled at
     rest (confirmed live — no pending edit yet).

3. Change Display Name to `autotest_cred_renamed`.
   - **Verify**: Display Name field updates to `autotest_cred_renamed`
     (confirmed live). **Side observation, directly relevant to case Step
     8**: the ID field **live-mirrors** the new value too —
     `autotest_cred_renamed`, still disabled — *before* Save is even
     clicked (confirmed live via re-snapshot). This is the same
     live-mirroring behavior already documented and asserted correct in
     ELITEA-1972's AFS/test (`test_credential_id_auto_generation.py`); see
     Known Defects / Observations below for why this contradicts the case's
     Step 8 text.

4. Verify the Save button becomes enabled.
   - **Verify**: confirmed live — `credential-form-save-button` transitions
     from `[disabled]` to enabled/clickable the instant the Display Name
     field's value differs from its saved value (same debounce-free
     transition observed in ELITEA-1971/1975's AFS for this shared Save
     button).

5. Click Save.
   - **Verify**: `PUT /api/v2/configurations/configuration/399/1596` fires
     and returns **200 OK** (confirmed live via `browser_network_requests`).
     **Live-observed navigation behavior, relevant to the implementer**: the
     app does **not** stay on the detail page after Save — it redirects to
     `${BASE_URL}/credentials/all`, same as the create-flow redirect in Step
     1 (confirmed live: URL changes from `/credentials/all/1596?...` to
     `/credentials/all`). The list card's title text updates to
     `autotest_cred_renamed` immediately (confirmed live via snapshot).

6. Reload the page.
   - **Verify** (two-part, both required since Save redirected away from
     the detail page in Step 5): (a) re-open the renamed credential's detail
     page (click the `autotest_cred_renamed` card) — URL is
     `${BASE_URL}/credentials/all/1596?viewMode=owner&name=autotest_cred_renamed`,
     **same numeric id `1596`** as Step 2 (confirmed live); (b) perform an
     actual full-page reload on that URL (`page.reload()` — confirmed live
     equivalent via re-`goto` of the identical URL, which is a full
     navigation/reload, not an SPA client-side route change) — page
     re-renders with the same URL and the same field values (confirmed live
     via post-reload snapshot).

7. Verify Display Name shows `autotest_cred_renamed`.
   - **Verify**: confirmed live — post-reload, `toolkit-field-label-input`
     (Display Name) value is `autotest_cred_renamed`. Renamed value
     persisted correctly across the reload, matching the case's Pass
     criterion exactly.

8. Verify the ID field remains unchanged (auto-generated, disabled).
   - **Verify — CASE-TEXT DRIFT, live behavior contradicts the case's
     literal expectation (see Known Defects / Observations #1 for the full
     writeup and filed clarification)**: the ID field (`elitea_title`) is
     confirmed **disabled** (read-only) post-reload — that half of the
     case's expectation holds. But its **value** is `autotest_cred_renamed`,
     **not** the original `autotest_cred_edit` — it regenerated to mirror
     the renamed Display Name and that regenerated value is what persists
     (confirmed live via post-reload snapshot, and matches ELITEA-1972's
     already-confirmed live behavior for the same field). The case's own
     literal Step 8 text ("ID field has the original auto-generated value")
     does **not** hold. The stable, actually-unchanging identifier across
     rename is the **numeric URL id** (`1596` in this run, confirmed
     unchanged from Step 2 through Step 6/7), not the `elitea_title` string
     field. This AFS asserts the corrected/live-true expectation: ID field
     stays **disabled** throughout (case's literal claim, holds), and the
     **numeric URL id** stays stable across rename+reload (the actually
     correct "unchanged ID" observable) — not that the `elitea_title` string
     value is frozen at its pre-rename value, which it is not.

## Expected Results
Matches the case's Pass criteria for Steps 1–7 exactly, live-verified
end-to-end: the credential is renamed, Save persists it via `PUT .../
configuration/399/{id}` → 200, and the renamed Display Name survives a full
page reload. Step 8 as literally authored does **not** hold — the ID
(`elitea_title`) field's *value* changes to mirror the rename (confirmed
disabled/read-only throughout, but not value-frozen); the AFS substitutes
the numeric URL id as the correct "stays unchanged" observable, consistent
with ELITEA-1972's already-established finding for the same field. This is
classified as case-text drift (reverse-masking), not a product defect — see
Known Defects / Observations #1. Filed as CLARIFICATION:
[elitea-testing-public#541](https://github.com/EliteaAI/elitea-testing-public/issues/541).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | AFS Preconditions | `auth_state` fixture (localhost dev token) | asserted |
| Precondition: project + Credentials section accessible | — | AFS Preconditions | `/credentials/all` + `/credentials/create-credential/github` load | asserted |
| 1 Create credential "autotest_cred_edit" (Github) | credential created successfully | step 1 | step 1: `POST .../configurations/399` 200, card visible on list | asserted |
| 2 Open credential detail page | detail page loads with "autotest_cred_edit" displayed | step 2 | step 2: URL + Display Name + ID field values confirmed | asserted |
| 3 Change Display Name to "autotest_cred_renamed" | input field updates with new name | step 3 | step 3: Display Name field value confirmed; ID-mirror side observation flagged | asserted |
| 4 Verify Save button becomes enabled | Save is active/clickable | step 4 | step 4: `credential-form-save-button` enabled state confirmed | asserted |
| 5 Click Save | credential saved with new name | step 5 | step 5: `PUT .../configuration/399/1596` 200, list card title updates | asserted |
| 6 Reload the page | page reloads | step 6 | step 6: full `page.reload()`-equivalent navigation on the detail URL, decomposed into re-open + reload since Save redirects away from detail (case's single action implies both, only asserting one leaves the redirect behavior unverified) | asserted *(decomposed — see step 6 note)* |
| 7 Verify Display Name shows "autotest_cred_renamed" | renamed value persisted correctly | step 7 | step 7: post-reload Display Name field value confirmed | asserted |
| 8 Verify ID field remains unchanged (auto-generated, disabled) | ID field has original value, not editable | step 8 | step 8: disabled-state half confirmed true; value-unchanged half confirmed **false** (case-text drift) — numeric URL id substituted as the corrected stable-identifier assertion | **disposition: clarification** (filed elitea-testing-public#541), not a straight pass — see step 8 and Known Defects #1 |
| Expected Final State: renamed, persists after reload, ID unchanged | — | steps 5–8 | rename+persist proven (steps 5–7); "ID unchanged" proven only for the numeric URL id, not the `elitea_title` string (step 8) | **partially asserted** — see Known Defects #1 |

### Axis 2 — Analyst additions

- step 1 documents the create-flow's Save-gating and post-save redirect
  behavior — *added: the case's own Step 1 is a one-line precondition-style
  action ("Create a credential"), but the implementer needs the concrete
  form-fill + Save + redirect mechanics to automate it, same treatment as
  ELITEA-1975's create-form documentation.*
- step 3 documents the live ID-mirroring side effect *before* Save — *added:
  this is the earliest point in the flow where the case's Step 8 assumption
  starts to look questionable; flagging it here lets an implementer catch
  the drift before writing a doomed assertion, rather than discovering it
  only at Step 8.*
- step 5 documents the post-Save redirect-to-list navigation — *added: not
  mentioned by the case text at all, but directly affects how Step 6
  ("reload the page") must be implemented — you cannot reload the detail
  page if Save has already navigated you off it.*
- step 6 documents the redirect-driven need to re-open the credential before
  a literal reload can be performed — *added: without this, "reload the
  page" would reload the list page instead of the detail page, and Step
  7/8's field-level assertions would have nothing to check.*
- step 8 substitutes the numeric URL id as the corrected "stays unchanged"
  observable — *added: preserves the spirit of the case's Pass criterion
  (something about the credential's identity should NOT change across
  rename) using the field that is actually live-confirmed stable, per the
  reverse-masking guard, rather than asserting the case's literal (and
  disproven) `elitea_title`-value claim.*
- "zero console errors/warnings across the full flow" — *added: side-channel
  check per this skill's standard discipline; not itself a case requirement.*

## Cleanup
1. Delete the credential created in Test Data via
   `CredentialAPI.delete_credential(credential_id)` in test teardown
   (regardless of pass/fail) — confirmed live this run via the UI's
   three-dot-menu → Delete → type-to-confirm flow instead (API client
   equivalent: `DELETE /api/v2/configurations/configuration/399/{id}`,
   same pattern as ELITEA-1972/1974/1975's teardown); re-verify via
   `CredentialAPI.list_all_credentials()` that the id no longer appears.
2. No other product state is created by this case.
3. No route interception, mocked network, or browser-context state needs
   explicit teardown beyond the normal per-test browser context lifecycle.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Create form → Display Name input (`ToolBaseProperty` renderer) | `page.get_by_test_id("toolkit-field-label-input")` — **confirmed live, existing testid**, already wired as `CredentialCreatePage.display_name_input` / `CredentialFormFieldsMixin.display_name_input` | none needed — testid-only per project policy |
| Create form → ID field (auto-mirrored, disabled) | `page.get_by_test_id("toolkit-field-elitea_title-input")` — **confirmed live, existing testid**, already wired as `CredentialCreatePage.id_input` (inherited path) / `CredentialDetailPage.id_input` | none needed |
| Create form → Save button | `page.get_by_test_id("credential-form-save-button")` — **confirmed live, existing testid**, already wired as `CredentialFormFieldsMixin.save_button`, shared by create + detail pages | none needed |
| Credentials list → credential card by name | `CredentialDetailPage.ENTITY_CARD_SELECTOR` (`[data-testid="entity-card"]`, scoped by `.filter(has_text=display_name)`) — **confirmed live, existing helper**, `CredentialDetailPage.open_credential_by_name()` already implements this exact click-through | none needed |
| Detail page → Display Name / ID / Save (same fields as create form) | Same testids as above, already unified via `CredentialFormFieldsMixin` — no new locators required for this case | none needed |
| Detail page → numeric URL id extraction | `CredentialDetailPage.get_credential_id_from_url()` — **confirmed live, existing helper** (regex over `/credentials/all/(\d+)`), already used by ELITEA-1972's test for the exact "stays stable across rename" assertion this case's corrected Step 8 needs | none needed |
| Detail page → ID-field-disabled check | `CredentialDetailPage.is_id_field_disabled()` — **confirmed live, existing helper** | none needed |

**Summary for the implementer / `add-data-testid`:** **zero new testid gaps**
— every element this case touches (Display Name, ID, Save button, the
credential card, the numeric URL id) already has a landed testid and an
existing page-object method from ELITEA-1971/1972/1974/1975's prior work on
`CredentialCreatePage` / `CredentialDetailPage` / `CredentialFormFieldsMixin`.
No `add-data-testid` round-trip is needed for this case.

## Network Behavior
- `POST /api/v2/configurations/configurations/{project_id}` — fires on
  create (Step 1), returns `200 OK`. Response body includes `id` (numeric,
  `1596` this run), `elitea_title`, `label`.
- `PUT /api/v2/configurations/configuration/{project_id}/{id}` — fires on
  rename-save (Step 5), returns `200 OK`. Response body's `elitea_title`
  mirrors the renamed Display Name (`autotest_cred_renamed` this run),
  consistent with ELITEA-1972's already-documented `PUT` response shape for
  the same endpoint.
- `DELETE /api/v2/configurations/configuration/{project_id}/{id}` — cleanup,
  via `CredentialAPI.delete_credential()` or the UI's confirm-by-name delete
  flow (both exercised in this run's cleanup; only the UI flow was
  live-verified in this specific run since the credential was created via
  UI, not API).
- Standard `GET /api/v2/configurations/configuration/{project_id}/{id}` /
  `GET /api/v2/configurations/configurations/{project_id}?...` list/detail
  loads accompany navigation, consistent with the pattern documented in
  ELITEA-1971/1972/1974's AFS.

## Known Defects / Observations Found During Exploration

1. **[CLARIFICATION — filed as
   [elitea-testing-public#541](https://github.com/EliteaAI/elitea-testing-public/issues/541),
   label `bug`, "Found while working #83"] Case Step 8's literal
   expectation ("ID field has the original auto-generated value") is stale
   / contradicted by live product behavior.** Live-confirmed this run (and
   independently already confirmed in ELITEA-1972's prior run): the ID
   (`elitea_title`) field regenerates to mirror the Display Name on every
   edit including rename — both as a live client-side preview *before* Save
   and as the persisted value *after* Save + reload. The field stays
   correctly **disabled** (that half of the case's expectation holds), but
   its *value* is not frozen at creation time. This is the
   reverse-masking pattern: the product's behavior is intentional and
   already validated correct by ELITEA-1972's dedicated ID-auto-generation
   case — the *case text* for ELITEA-1963 is what needs correcting, not the
   product. This AFS's Step 8 substitutes the numeric URL id (which
   genuinely does stay stable across rename, confirmed live: `1596`
   throughout) as the corrected assertion. **Not filed as a product Bug** —
   filed as a CLARIFICATION per this project's bug-filing policy (behavior
   is correct, case text is wrong).

No functional product defect was found. All 8 case steps were live-executed
end-to-end; 7 of 8 pass exactly as authored, and Step 8 is covered with a
corrected assertion per the clarification above.

## Blocked Steps
None. All 8 case steps were executed end-to-end live against the real DEV
backend, including the full create → open → rename → save → reopen → reload
→ verify → delete round trip.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Likely home:
  `automation/tests/ui/toolkits/test_credential_edit_rename.py` (new file —
  grep of `automation/tests/ui/toolkits/` found no existing test named for
  rename specifically; `test_credential_id_auto_generation.py` covers
  adjacent but distinct ground — ID-slug mirroring + numeric-id stability as
  its primary subject, not Display-Name-persists-after-a-literal-reload as
  its primary subject. Given the near-total testid/locator/helper overlap
  with `CredentialDetailPage`/`CredentialCreatePage` (zero new handles
  needed, see Concrete Handles), this is a small, focused new test built
  entirely on existing page-object methods, not a page-object extension.
- Existing `CredentialAPI` (`automation/api/client.py:949` region) already
  provides `create_github_credential()`, `list_all_credentials()`, and
  `delete_credential()` — usable for setup if the implementer prefers API
  seeding over the UI-create flow this AFS exercised live (both are valid;
  this AFS chose UI-create to literally match the case's own Step 1 wording
  "Create a credential ... of type Github", mirroring ELITEA-1975's
  create-form-first approach rather than ELITEA-1974's API-seed approach).
- No new page-object methods or testids are needed — `CredentialCreatePage`,
  `CredentialDetailPage`, and `CredentialFormFieldsMixin` already expose
  every method this case's steps require:
  `navigate_to_type()`, `set_display_name()`, `is_save_enabled()`,
  `save_button.click()` + `page.expect_response(...)` (same pattern as
  `test_credential_id_auto_generation.py`), `open_credential_by_name()`,
  `get_credential_id_from_url()`, `is_id_field_disabled()`,
  `get_display_name()`, `id_input.input_value()`.
- Wait strategy: wait on `page.expect_response()` for the `POST`
  (create) and `PUT` (rename) calls rather than a fixed sleep — same
  pattern already used in `test_credential_id_auto_generation.py`. For the
  literal "reload the page" step, use Playwright's `page.reload()`
  directly (not a re-`goto`, which this AFS used only because it was
  driving the browser via raw MCP tool calls without page-object access) —
  followed by `detail_page.wait_for_page_load()`.
- Assertion for case's corrected Step 8: assert
  `detail_page.get_credential_id_from_url() == credential_id_before_rename`
  (numeric URL id stability, mirrors `test_credential_id_auto_generation.py`
  Step 8's identical assertion) AND
  `detail_page.is_id_field_disabled() is True` post-reload. Do **not**
  assert `detail_page.id_input.input_value() == original_elitea_title` —
  that assertion is false per this AFS's live findings and would make the
  test fail against correct product behavior.
