# Test Case: Credential — ID Auto-Generation

## Metadata
- **TMS ID**: ELITEA-1972
- **Linked Story**: `EliteaAI/elitea-testing-public#69` (tracker issue; already `In Progress`
  on the Test Automation Factory board — this AFS does not touch board status)
- **Priority**: l1 (case frontmatter: `critical`; case body table's own header line says
  "Priority: medium" — **pre-existing inconsistency in the source case**, same class of
  discrepancy already documented in ELITEA-1971's AFS, not introduced here. Per dispatch
  instruction, `critical` is treated as authoritative: it matches both the case frontmatter
  *and* the tracker issue #69 body, which explicitly states "Priority: critical". Recommend
  the TMS case body table be corrected upstream — not filed as a defect, it's a case-authoring
  nit, not a product bug.)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (localhost `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`; no toolkit-specific token is required for this case — the credential is
  created as a GitHub-type credential purely as a stable, already-supported type to create
  through, with `Auth: Anonymous` left at its default and **no GitHub token entered or
  needed** — this case never exercises "Test connection" or any GitHub-authenticated call)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation
- **Case-gate note**: case frontmatter carries `status: draft`, `execution_type: manual`.
  `.agents/testing.md` has no documented `TMS case-gate` exclusion list for this project, so
  per the skill's default ("if absent, default to fetching all and flag the gap") this run
  proceeded and executed the case end-to-end. Flagging the gap again here (already flagged
  in ELITEA-1971's AFS) for scout to fill `.agents/testing.md` § TMS case-gate.

## Preconditions
- User is logged in to Elitea (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- No credential named `My Test Credential` (or the automated test's unique variant) exists
  from a previous failed run — the test's own setup creates a fresh one; the implementer
  should suffix the display name with a timestamp per the project's existing per-test
  uniqueness convention (see `test_toolkit_indicators_for_credentials.py`'s
  `f"autotest_tk_cred_{ts}"[:32]` pattern, also called out in ELITEA-1971's AFS) rather than
  the literal case-data string, to avoid label collisions across parallel/retried CI runs.

## Test Data

### generate-per-test (created in test setup, cleaned up in its own teardown)
- Credential type: **GitHub** (`toolkit-type-card-github`) — chosen as a stable, already
  fully-supported credential type with no required-field friction (`Base Url` defaults to
  `https://api.github.com`, `Auth` defaults to `Anonymous`); the case itself doesn't care
  which type is used, only that ID auto-generation and URL stability hold, so type choice is
  incidental to the case's own subject.
- Initial Display Name: `My Test Credential` per the case's own Test Data table (suffix with
  a timestamp in the automated version, e.g. `f"My Test Credential {ts}"`, to avoid
  collisions — the exact live-confirmed slug transform, see Test Steps step 4, still lowercases
  and underscores whatever string is given, so a timestamp suffix doesn't change the shape of
  the assertion).
- Renamed Display Name: a second, distinct string (e.g. `My Renamed Credential {ts}`) — must
  differ from the initial name; the exact value is not asserted, only that (a) the Display
  Name field reflects it and (b) the URL's numeric ID does not change.

No shared/reused fixture applies — the case inherently requires creating a new credential
record and mutating it mid-test (Display Name rename) to assert URL/ID stability across the
rename; a shared/reused credential would risk cross-test interference on the renamed field.

**Entry-point decision (differs from ELITEA-1971):** unlike ELITEA-1971 (whose subject was
the Discard flow on an *existing* credential, where API-level setup was the right call), this
case's own subject **is** the creation-time ID auto-generation. Steps 1–2 of the case are
literal UI steps ("Create a new credential... Save the credential"), and this run confirmed
live that the **UI create-form's live slug generation** (`toolkit-field-elitea_title-input`
mirroring `toolkit-field-label-input` character-for-character, lowercased + spaces→underscores)
is a **different code path** from `CredentialAPI.create_github_credential()`'s server-side
`elitea_title` generation, which prefixes the type and appends a timestamp (confirmed in
ELITEA-1971's exploration: `autotest_discard_cred` → `github_autotest_discard_cred_1784120706909`).
Since this case's Test Data table explicitly expects `my_test_credential` (or similar) from
`My Test Credential` — i.e., the clean lowercase-underscore transform, no type prefix, no
timestamp suffix — **the UI create-form is the entry point that actually matches the case's
expected result**, not the `CredentialAPI` helper. Automate via the UI create flow
(`CredentialCreatePage`), not `credential_api` setup.

## Test Steps

1. Navigate to `${BASE_URL}/credentials/all`, click the **GitHub** credential-type card
   (`toolkit-type-card-github`), landing on
   `${BASE_URL}/credentials/create-credential/github`.
   - **Verify**: create form renders with `Display Name`, `ID *` (disabled, empty), and
     `Base Url *` (prefilled `https://api.github.com`) fields; **Save** button is `[disabled]`
     (confirmed live via snapshot immediately after navigating to the type card).

2. Fill the Display Name field (`toolkit-field-label-input`) with `My Test Credential`.
   - **Verify**: Display Name field shows `My Test Credential` (confirmed live). **Save**
     button becomes enabled (confirmed live — `button "Save" [ref=e513]` with no `[disabled]`
     marker, vs `[disabled]` immediately beforehand).

3. Click **Save** (`credential-form-save-button`).
   - **Verify**: `POST /api/v2/configurations/configurations/{project_id}` fires and returns
     `200` (confirmed live via `browser_network_requests`); the app navigates to
     `${BASE_URL}/credentials/all` and the new credential's card
     (`[data-testid="entity-card"]` filtered by text `My Test Credential`) appears in the list
     (confirmed live).

4. Open the credential detail page by clicking its card, then verify the **ID field is
   populated with an auto-generated slug**.
   - **Verify**: URL becomes
     `${BASE_URL}/credentials/all/{numeric_id}?viewMode=owner&name=My%20Test%20Credential`
     (confirmed live: numeric id `1560` in this run). The `ID *` field
     (`toolkit-field-elitea_title-input`) shows **exactly** `my_test_credential` — confirmed
     live, this is the **exact** transform the case's own Test Data table names
     ("my_test_credential (or similar)"): lowercase the Display Name, replace each space with
     an underscore. No type prefix, no timestamp/uniqueness suffix is added by this code path
     (contrast with the `CredentialAPI` server-side path noted above — see Test Data
     § Entry-point decision).

5. Verify the ID field is disabled (read-only).
   - **Verify**: `toolkit-field-elitea_title-input`'s accessibility snapshot shows
     `textbox "ID *" [disabled]` both immediately after Save (step 4) and on this fresh page
     load after re-opening from the credentials list (confirmed live in both places) — this is
     the genuine HTML `disabled` attribute (Playwright's accessibility tree only reports
     `[disabled]` from the underlying DOM property, not a CSS-only visual state), not merely a
     visual/CSS-only lock.

6. Verify a numeric ID appears in the credential detail page's URL path.
   - **Verify**: already captured in step 4's URL check
     (`/credentials/all/1560?viewMode=owner&name=...`) — folded into step 4 rather than a
     separate action, since step 4's navigation *is* the action that produces this URL (same
     decomposition pattern ELITEA-1971's AFS used for its own case Steps 5/6).

7. Change the Display Name to a new value (e.g. `My Renamed Credential`) and click **Save**
   again.
   - **Verify**: while editing (before Save), the `ID *` field **live-mirrors** the new
     Display Name value with the same transform — confirmed live: typing `My Renamed
     Credential` updates `toolkit-field-elitea_title-input` to `my_renamed_credential` in
     real time, still `[disabled]` (matches the reactive-mirroring behavior ELITEA-1971's AFS
     flagged as a side-observation for this same field — here it's a first-class assertion
     since this case's whole subject is the ID field's derivation). After clicking **Save**,
     `PUT /api/v2/configurations/configuration/399/1560` fires and returns `200` (confirmed
     live via `browser_network_request`) — same numeric id `1560` in the request path — and
     the app navigates back to `${BASE_URL}/credentials/all`, where the card now shows the
     new Display Name (`My Renamed Credential`, confirmed live).

8. Re-open the credential from the list and verify the numeric ID in the URL does NOT change.
   - **Verify**: URL is now
     `${BASE_URL}/credentials/all/1560?viewMode=owner&name=My%20Renamed%20Credential` —
     **same numeric id `1560`** as step 4, only the `?name=` query param and the page's own
     Display Name field changed (confirmed live via `browser_snapshot` immediately after
     re-opening). The `ID *` field now shows `my_renamed_credential` (persisted, disabled) —
     confirmed live via the detail-page `GET
     /api/v2/configurations/configuration/399/1560` response body:
     `{"id": 1560, "uuid": "44b2ec13-ea83-4d88-96cf-51af0d1755d5", "elitea_title":
     "my_renamed_credential", "label": "My Renamed Credential", "type": "github", ...}` —
     i.e. the backend's own numeric `id` (used in the URL) is a **separate, stable** field
     from both `uuid` and `elitea_title`; renaming only ever touches `label` and
     `elitea_title`, never `id`.

**Side-channel check (all steps):** one pre-existing React console error observed
(`Warning: Each child in a list should have a unique "key" prop` in
`CredentialTypeSelector.jsx` / `CategorySection.jsx` / `GroupedCategory.jsx`) — present on
**every** visit to the credential-type-selector screen (step 1), including on a cold page
load before any interaction of this case's own flow. Not caused by, and unrelated to, this
case's own ID-autogeneration/URL-stability assertions (steps 2–8 produce zero *additional*
console errors/warnings beyond this one pre-existing one). See Known Defects below.

## Expected Results
Matches the case's Pass criteria exactly, live-verified end-to-end: the ID field
(`elitea_title`) is auto-generated from the Display Name via a lowercase + underscore
transform at both creation time and on every subsequent Display Name edit (step 4, step 7),
remains genuinely disabled throughout (step 5), and the numeric URL-path ID (`id`, distinct
from `uuid`) is stable across a Display Name rename (step 8: `1560` before and after). No
functional defect found in the ID-autogeneration/URL-stability contract itself.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | AFS Preconditions | `auth_state` fixture (localhost dev token) | asserted |
| Precondition: project + Credentials section accessible | — | AFS Preconditions | project `399` selected, `/credentials/all` loads | asserted |
| 1 Create new credential with Display Name "My Test Credential" | form accepts the name | steps 1–2 | step 2: Display Name field value, Save enables | asserted |
| 2 Save the credential | saved successfully | step 3 | step 3: `POST .../configurations/399` returns 200, card appears in list | asserted |
| 3 Open the credential detail page | detail page loads | step 4 | step 4: URL navigation to `/credentials/all/{id}` | asserted |
| 4 Verify ID field populated with auto-generated slug | ID field contains the slug | step 4 | step 4: `toolkit-field-elitea_title-input` == `my_test_credential`, exact transform confirmed | asserted |
| 5 Verify ID field is disabled | read-only, not editable | step 5 | step 5: `[disabled]` on the field, both post-save and on fresh reload | asserted |
| 6 Verify a numeric ID appears in the URL path | URL contains numeric segment | step 4 (folded) | step 4's own URL assertion already covers this — case Step 6 restates Step 4's observable rather than adding a new action | asserted *(decomposed/folded — case Steps 4 and 6 collapse to one AFS step, same treatment ELITEA-1971 gave its own duplicate Steps 5/6)* |
| 7 Change the Display Name to a new value | Display Name field updates | step 7 | step 7: field value + live ID-mirror + Save round-trip | asserted |
| 8 Verify the numeric ID in the URL does NOT change | URL numeric ID remains the same | step 8 | step 8: URL numeric id `1560` unchanged vs step 4's `1560`, plus response-body `id` field cross-check | asserted |
| Expected Final State: ID auto-generated, read-only, numeric URL ID stable regardless of Display Name changes | — | steps 4, 5, 7, 8 | steps 4/5/7/8 jointly | asserted |

### Axis 2 — Analyst additions

- step 1 documents the create-form's own baseline state (Save disabled, ID field empty and
  disabled before any Display Name is typed) — *added: gives the implementer a concrete
  "before" state to diff step 2's "after" against, same pattern as ELITEA-1971's step 2
  baseline documentation.*
- step 4 documents the **exact live transform rule** (lowercase + space→underscore, no
  prefix, no suffix) rather than accepting the case's vague "or similar" — *added: the case's
  own Test Data table hedges with "(or similar)"; this AFS pins the precise, live-confirmed
  rule so the automated assertion is exact-match, not a fuzzy regex.*
- Test Data § Entry-point decision documents that the UI create-form and the
  `CredentialAPI` helper produce **different** `elitea_title` values for the same Display
  Name (no prefix/suffix vs. `{type}_{name}_{timestamp}`) — *added: this is the reason the
  entry point must be the UI form for this specific case, unlike ELITEA-1971; an implementer
  who defaults to `credential_api` setup (the project's usual convention) would produce an
  `elitea_title` that doesn't match the case's expected pattern.*
- step 7 documents the **live-mirroring** behavior of the ID field while editing (before
  Save) — *added: ELITEA-1971's AFS flagged this as a side-observation for the Discard case;
  here it's promoted to a first-class assertion since this case's actual subject is the ID
  field's derivation from Display Name.*
- step 8 documents the full detail-page API response body (`id`, `uuid`, `elitea_title` as
  three distinct fields) — *added: makes explicit, with a concrete captured payload, that the
  numeric `id` used in the URL is architecturally separate from both `uuid` and
  `elitea_title` — the case only asks to verify the URL doesn't change, but the response body
  is the ground truth that explains *why* it doesn't.*
- "zero *additional* console errors/warnings beyond the one pre-existing, case-unrelated
  React key-prop warning" — *added: side-channel check per this skill's standard discipline;
  see Known Defects for the pre-existing warning itself.*

## Cleanup
1. Delete the credential created in step 2 (and renamed in step 7) via
   `CredentialAPI.delete_credential(credential_id)` in test teardown (regardless of
   pass/fail) — confirmed live via the UI equivalent (credential detail page's overflow menu
   → **Delete** → type-to-confirm dialog → **Delete**): `DELETE
   .../configurations/configuration/{project_id}/{id}`-equivalent succeeds, credential no
   longer appears in `/credentials/all`. This exploration run deleted credential `id=1560`
   after completing all 8 steps.
2. No other product state is created by this case — one credential record is created,
   renamed once, and deleted; no orphaned data results.
3. No route interception, mocked network, or browser-context state needs explicit teardown
   beyond the normal per-test browser context lifecycle.

## Concrete Handles (discovered during exploration)

**Summary: zero new testids needed.** Every handle this case touches already exists and is
already wired into `automation/pages/credential_create_page.py`,
`automation/pages/credential_detail_page.py`, and the shared
`automation/pages/credential_form_fields.py` mixin (all landed for ELITEA-1971 / ELITEA-1975).
This is a near-total handle-reuse case, as anticipated in dispatch.

| Element | Recommended Locator | Fallback |
|---|---|---|
| GitHub credential-type card (entry point, `CredentialCreatePage.navigate_to_type("github")`) | `page.get_by_test_id("toolkit-type-card-github")` — **confirmed live, existing** (`CredentialCreatePage.TYPE_CARD_SELECTOR.format("github")`) | none needed — testid confirmed present and unique |
| Display Name field (create form + detail page, shared mixin) | `page.get_by_test_id("toolkit-field-label-input")` — **confirmed live, existing** (`CredentialFormFieldsMixin.display_name_input`) | `page.get_by_role("textbox", { name: "Display Name" })` |
| ID field (disabled, `elitea_title`) | `page.get_by_test_id("toolkit-field-elitea_title-input")` — **confirmed live, existing** (`CredentialDetailPage.id_input`; also present, same testid, on the create form — not yet exposed as a class field on `CredentialCreatePage`, see Automation Hints) | `page.get_by_role("textbox", { name: "ID *" })` |
| Save button (create form + detail page tab-bar, shared mixin) | `page.get_by_test_id("credential-form-save-button")` — **confirmed live, existing** (`CredentialFormFieldsMixin.save_button`) | `page.get_by_role("button", { name: "Save" })` scoped outside any dialog |
| Credentials list → credential card (re-open entry point) | `page.locator('[data-testid="entity-card"]').filter(has_text=display_name)` — **confirmed live, existing** (`CredentialDetailPage.ENTITY_CARD_SELECTOR`, already used by `open_credential_by_name()`) | none needed — testid confirmed present and unique per card |
| Credential detail overflow menu → Delete (cleanup only, not a case step) | `page.get_by_test_id("controls-menu-button")` then `page.get_by_test_id("delete-credentials-menuitem")` — **confirmed live, existing testids**, not yet wired into any page object (this AFS's cleanup used them ad hoc via the UI; the project's established cleanup convention is `CredentialAPI.delete_credential()`, which the automated test should prefer over this UI path) | `page.get_by_role("menuitem", { name: "Delete" })` |

## Network Behavior
- `POST /api/v2/configurations/configurations/{project_id}` — fires on step 3's Save
  (credential creation), returns `200` with the new credential's `id`/`uuid`/`elitea_title`.
- `GET /api/v2/configurations/configuration/{project_id}/{id}` — fires on every detail-page
  load/navigation (steps 4 and 8), returns the full credential record including `id`
  (numeric, URL-stable), `uuid` (separate, not used in this route's URL param despite the
  route param being named `:credential_uid` — see Known Defects), and `elitea_title` (the
  auto-generated/mirrored slug).
- `PUT /api/v2/configurations/configuration/{project_id}/{id}` — fires on step 7's Save
  (rename), same numeric `{id}` in the path as the preceding GET — confirms the rename never
  touches the URL-path identifier.

## Known Defects Found During Exploration
1. **[Informational — not filed, consistent with ELITEA-1971's Known Defects #1/#2] Route
   param named `:credential_uid` actually resolves the numeric `id`, not the `uuid`.**
   Re-confirmed live in this run: the detail-page URL is
   `/credentials/all/{numeric_id}?viewMode=owner&name=...` (e.g. `/credentials/all/1560`),
   and the response body for that route's `GET` carries a *separate* `uuid` field
   (`44b2ec13-ea83-4d88-96cf-51af0d1755d5` in this run) that is never used in the URL. This is
   the same naming-vs-behavior mismatch ELITEA-1971 already documented (dead-code
   `useCredentialActions.js` aside); not re-filed here. This case's own Steps 6/8 pass
   regardless, since the click-through/re-open entry point always resolves the numeric `id`
   correctly.
2. **[Informational — not filed, low severity, unrelated to this case's subject] Pre-existing
   React console warning on the credential-type-selector screen:** `Warning: Each child in a
   list should have a unique "key" prop` in `CredentialTypeSelector.jsx` (via
   `CategorySection.jsx` / `GroupedCategory.jsx`), fired on every visit to
   `/credentials/create-credential`, including a cold load before any of this case's own
   interactions. A React list-rendering code-quality issue, not a functional defect — doesn't
   affect the ID-autogeneration or URL-stability behavior this case asserts, and produces no
   user-visible symptom. Not filed as a tracker ticket per this project's bug-filing policy
   (routes *product* defects, not internal React dev warnings with no user-facing effect);
   documented here for awareness only, same treatment as ELITEA-1971's Known Defects #1
   (documented, not filed, because it has no live user-facing effect).
3. **[Confirmed, not a defect] `elitea_title` generation differs between the UI create-form's
   live-typing path and the `CredentialAPI` server-side create path** — see Test Data §
   Entry-point decision above. Not a bug (both paths are internally consistent and neither
   contradicts the case), but worth flagging for anyone who later tries to automate this case
   via API-level setup: it will *not* reproduce the case's expected `my_test_credential`
   pattern.

No functional product defect was found in the case's own ID-autogeneration/URL-stability
contract. All 8 case steps live-verified end-to-end.

## Blocked Steps
None. All 8 case steps were executed end-to-end live against the real DEV backend, including
the full create → observe-ID → rename → re-verify-URL round trip and cleanup.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Likely home:
  `automation/tests/ui/toolkits/test_credential_id_auto_generation.py` (new file — grep of
  `automation/tests/ui/toolkits/` found `test_credential_discard_changes.py` (ELITEA-1971,
  Discard flow) and the create-form required-fields test (ELITEA-1975), but no existing test
  exercising the ID-autogeneration/URL-stability contract itself).
- Reuse `CredentialCreatePage` (`automation/pages/credential_create_page.py`) for steps 1–3
  (`navigate_to_type("github")`, `set_display_name(...)`, `save_button.click()`) and
  `CredentialDetailPage` (`automation/pages/credential_detail_page.py`) for steps 4–8
  (`id_input`, `display_name_input`/`set_display_name()`, `save_button`,
  `open_credential_by_name()`). No new page-object file needed.
- **One small, optional page-object addition worth considering** (not required — the analyst
  doesn't write code, but flagging for the implementer): `CredentialCreatePage` currently
  doesn't expose `id_input` as a class field the way `CredentialDetailPage` does, even though
  the same testid (`toolkit-field-elitea_title-input`) is present and live on the create form
  too (confirmed in step 2). If the implementer wants to assert the ID field's live-mirroring
  behavior *on the create form itself* (this AFS's step 2 only asserts Save-enabling there,
  not the ID mirror — the ID mirror is asserted on the detail page in steps 4 and 7 instead),
  hoisting `id_input` up to the shared `CredentialFormFieldsMixin` (both pages already inherit
  it) would avoid duplicating the `LocatorDescriptor` field. Not required for this case as
  written — the case's own asserted checkpoints (steps 4, 5, 7, 8) are all on the detail page,
  where `id_input` already exists.
- Extracting the numeric ID from the URL: `page.url` (Playwright's `Page.url` property, not a
  page-object method) plus a small regex (e.g. `re.search(r"/credentials/all/(\d+)", page.url)`)
  is the simplest live-confirmed approach — no existing helper method does this yet; a small
  `get_credential_id_from_url()` method on `CredentialDetailPage` would be a reasonable,
  non-duplicating addition (parallel to how other detail pages expose
  `get_agent_id_from_info()` per `.claude/rules/ui-tests.md`'s example).
- Checking the ID field's disabled state: Playwright's `Locator.is_disabled()` (already the
  convention elsewhere in this codebase, e.g. `is_save_enabled()` wraps
  `save_button.is_enabled()`) — a parallel `is_id_field_disabled()` wrapping
  `id_input.is_enabled()` (negated) keeps the same pattern; not currently on
  `CredentialDetailPage`, worth adding since this case asserts it directly (case Step 5).
- Wait strategy: no fixed timeouts needed. `wait_for_page_load()` (existing on both page
  objects) already waits for `display_name_input` to be visible, which is a sufficient signal
  before reading `id_input`'s value in every step of this case.
- Cleanup: prefer `CredentialAPI.delete_credential(credential_id)` (existing, reused by
  ELITEA-1971's test) over the UI delete-with-typed-confirmation flow this exploration used
  ad hoc — the API path is faster and matches the project's established teardown convention;
  the UI delete flow's testids (`controls-menu-button`, `delete-credentials-menuitem`) are
  documented in Concrete Handles above only for completeness, not as the recommended
  automation path.
