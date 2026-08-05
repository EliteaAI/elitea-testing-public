# Test Case: Eye icon reveals the actual secret value and changes to crossed-out eye

## Metadata
- **TMS ID**: ELITEA-2343
- **Source case**: `.agents/automation/elitea-2343-secret-eye-icon-reveal/cases/ELITEA-2343.md`
- **Linked Story**: none
- **Priority**: l3 (medium, per case frontmatter `priority: medium`). **pytest marker:
  `@pytest.mark.p2`** — medium→l3→p2 convention, per
  `.agents/memory/qa-engineer/priority_marker_drift_afs_vs_pytest_mark.md` (do NOT
  drift to p1).
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}` = 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation

## Preconditions
- User is logged in to the Elitea platform (localhost dev-token auth).
- Active project is `${ELITEA_PROJECT_ID}` (399, "Private").
- **Do not target a pre-existing/real secret for this case, even though the
  Show/Hide toggle itself is non-destructive and NOT gated by `isDefault`**
  (confirmed live and in source — `SecretsTable.jsx` renderActions: the
  Show/Hide `IconButton`'s render condition is
  `checkPermission(PERMISSIONS.secrets.unsecret) && !row.isNew`, with no
  `disabled={isDefault}`, unlike the three-dot menu's three items). The reason
  to still use a run-unique secret is assertion strength, not safety: only a
  secret whose plaintext value the test itself set can be asserted for exact
  equality after reveal — a real secret's actual value is unknown to the test.
  Create it via the existing inline "+" flow (`secrets_page.py`'s
  `click_add_button()` / `fill_new_row()` / `click_save_button()` — already
  covered by ELITEA-2336) and delete it via the existing three-dot-menu delete
  flow (ELITEA-2338) as this case's own cleanup (see § Cleanup).

## Test Data
### generated-per-run
- Secret name: a run-unique value, e.g. `f"autotest_eye_reveal_{uuid4().hex[:8]}"`
  — same non-idempotency rationale as ELITEA-2336/ELITEA-2338's AFS. Confirmed
  live with `autotest_eye_reveal_2343`.
- Secret value: any non-empty string, e.g. `f"reveal-value-{uuid4().hex[:8]}"`
  — confirmed live with `reveal-value-9f8e7d6c`. No format validation beyond
  max-length (shared with the name field per `_surface.md`).

## Test Steps
1. Navigate to `${BASE_URL}/settings/secrets`.
   - **Verify**: page title testid `secrets-page-title` is visible with exact
     text "Secrets".
2. Create a run-unique secret via the existing inline "+" flow (`secrets-add-button`
   → `secret-name-input` / `secret-value-input` → `secret-row-save-button`) and
   confirm the `POST /api/v2/secrets/secrets/default/${ELITEA_PROJECT_ID}` create
   request resolves **201 Created** (reused mechanics from ELITEA-2336's
   `click_save_button()`, which already returns the `Response` for this exact
   assertion).
3. Locate the created secret's row (confirmed live technique, same as
   ELITEA-2338: type its name into the search input so exactly one row
   remains — `secret_row.filter(has_text=name)` is the fully-testid-based
   alternative that needs no search interaction at all, per that AFS's
   Automation Hints).
   - **Verify** the row's Value cell (`secret-value-cell`) shows the masked
     template string, exact format `"{{secret.<name>}}"` — confirmed live:
     `"{{secret.autotest_eye_reveal_2343}}"` (`SecretValueCell.jsx`, `label`
     prop = `row.secretValue`, initially the value the list GET returns —
     the API's own `secret_name` field, see § Network Behavior).
   - **Verify** the row's Show/Hide toggle button (**testid needed**, see
     § Concrete Handles) renders the `VisibilityIcon` (normal/open eye) icon —
     confirmed live via the icon `<svg>`'s own `data-testid="VisibilityIcon"`
     (an MUI `@mui/icons-material` library behavior — the icon component's
     `data-testid` equals its own export name automatically; NOT an
     app-authored attribute, confirmed by grepping `SecretsTable.jsx`: no
     `data-testid` is passed to either `<VisibilityIcon>` or
     `<VisibilityOffIcon>` at the call site — the library sets it).
4. Click the Show/Hide toggle button (eye icon) on that row.
   - **Verify**: a `GET /api/v2/secrets/secret/default/${ELITEA_PROJECT_ID}/<name>`
     request fires and resolves **200 OK** (confirmed live via network capture
     — this is the `useLazySecretShowQuery` `showSecret` lazy query,
     `useSecretVisibility.hooks.js` `handleShowSecret`). Response body shape
     confirmed live: `{"name": "<name>", "secret_name": "{{secret.<name>}}",
     "is_hidden": false, "value": "<plaintext>"}`.
5. Verify the Value column updates to show the actual secret value (plaintext).
   - **Verify**: the `secret-value-cell` text now equals the exact plaintext
     value this test created (confirmed live: `"{{secret.autotest_eye_reveal_2343}}"`
     → `"reveal-value-9f8e7d6c"`, an exact string match, not merely
     "differs from the mask" — the response's `value` field is what the UI
     now renders, per `handleShowSecret`'s `secretValue: data?.value`).
6. Verify the eye icon changes to a crossed-out eye icon.
   - **Verify**: the toggle button's icon `<svg>` now carries
     `data-testid="VisibilityOffIcon"` (confirmed live — same MUI
     library-auto-testid mechanism as step 3, now the OTHER icon component:
     `SecretsTable.jsx`'s `{isSecretVisible ? <VisibilityOffIcon/> :
     <VisibilityIcon/>}` swap).
7. Click the crossed-out eye icon (same button, same testid — the button
   itself keeps ONE static identity per `.agents/testing.md` § Locator
   policy "testid = stable identity"; only the rendered MUI icon underneath
   changes, which is a genuinely different sub-component swapped in, not a
   value-ternary on the SAME element's own testid).
   - **Verify**: **zero** new network requests fire (confirmed live via
     before/after `browser_network_requests` diff — `handleHideSecret` is
     purely client-side: `setRows(... secretValue: row.secret_name ...)`,
     no API call, no `hideSecret` mutation — that mutation belongs to the
     DIFFERENT three-dot-menu "Hide" flow, which permanently un-reveals the
     secret server-side; do not conflate the two "Hide" concepts, see the
     Clarification note below).
8. Verify the value returns to the masked "{{secret.name}}" format.
   - **Verify**: `secret-value-cell` text reverts to the exact original masked
     string, `"{{secret.autotest_eye_reveal_2343}}"` (confirmed live —
     restored from `row.secret_name`, the same string the initial list GET
     supplied, not merely re-derived client-side from the name).
9. Verify the icon reverts to the normal eye icon.
   - **Verify**: the toggle button's icon `<svg>` carries
     `data-testid="VisibilityIcon"` again (confirmed live).

## Expected Results
- Clicking the row's Show/Hide (eye) toggle fires a `GET
  /secrets/secret/default/{project_id}/{name}` request (200) and swaps the
  Value column from the masked `"{{secret.<name>}}"` template to the exact
  plaintext value, while the icon swaps `VisibilityIcon` → `VisibilityOffIcon`.
- Clicking the crossed-out eye icon reverts the Value column to the masked
  template and the icon back to `VisibilityIcon`, with **no network request**
  (purely client-side toggle) — distinct from the three-dot menu's "Hide"
  item, which DOES call a server mutation (see Clarification below).
- No console errors during the flow (side-channel check).

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Secrets | page loads | step 1 | `step 1`: `secrets-page-title` visible | asserted |
| 2 Locate any secret row showing a masked "{{secret.name}}" value | action completes without error, expected UI state | steps 2–3 | `step 3`: `secret-value-cell` text == masked template | asserted *(decomposed — case says "any secret row"; automated as "the row this test itself created", see § Preconditions for why)* |
| 3 Click the eye icon on that row | control responds, next state shown | step 4 | `step 4`: GET request fires, 200 | asserted |
| 4 Verify the Value column updates to show the actual secret value (plaintext) | condition holds | step 5 | `step 5`: `secret-value-cell` text == exact plaintext | asserted |
| 5 Verify the eye icon changes to a crossed-out eye icon | condition holds | step 6 | `step 6`: icon `data-testid` == `VisibilityOffIcon` | asserted |
| 6 Click the crossed-out eye icon | control responds, next state shown | step 7 | `step 7`: zero new network requests (client-side only) | asserted |
| 7 Verify the value returns to the masked "{{secret.name}}" format | condition holds | step 8 | `step 8`: `secret-value-cell` text == original masked template | asserted |
| 8 Verify the icon reverts to the normal eye icon | condition holds | step 9 | `step 9`: icon `data-testid` == `VisibilityIcon` | asserted |

**Axis 2 — Analyst additions:**
- Step 4 asserts the exact `GET .../secret/default/{project}/{name}` request +
  200 + response body shape — *added: the case's step 3 ("click the eye icon")
  under-specifies the network contract; the request/response pair is the
  side-channel proof the "reveal" is a real server round-trip (fetching the
  actual value), not a client-side unmask of an already-present-but-obscured
  value — confirmed live the list GET never returns the plaintext, only
  `secret_name` (the masked template).*
- Step 5 asserts an EXACT string match against the value this test itself
  created, not merely "differs from the mask" — *added: a weaker "not equal to
  mask" assertion would also pass if the UI showed garbage/wrong data; exact
  equality is the only assertion that actually proves correctness.*
- Step 7 asserts ZERO new network requests on hide — *added: this is the
  single most important behavioral fact discovered this session (see
  Clarification below) — the case text doesn't distinguish this row-level
  toggle's "Hide" from the three-dot menu's server-side "Hide", and asserting
  no-network-call is what proves this AFS is testing the right one.*
- Step 8 asserts the reverted text is the exact ORIGINAL masked string (not
  merely "contains the name" or "matches the mask pattern") — *added: proves
  the round-trip is lossless, matching the same rigor ELITEA-2336/2338 already
  apply to save/delete round-trips.*

## Cleanup
- This case's own steps do not delete the generated secret (unlike
  ELITEA-2338, whose steps ARE a delete flow) — cleanup is a separate,
  explicit step at the end of the test: reuse the existing three-dot-menu
  delete flow (`secrets_page.py`'s `open_row_actions_menu()` /
  `click_delete_menu_item()` / `fill_delete_confirm_name()` /
  `confirm_delete()`, already covered by ELITEA-2338) OR the digest's
  documented API-cleanup shortcut (`DELETE
  /api/v2/secrets/secret/default/{project_id}/{name}` → `204`). Confirmed
  live via the UI flow during this analysis session (secret
  `autotest_eye_reveal_2343` created and deleted cleanly, `204`-equivalent
  UI flow, table returned to "No secrets" under the still-active search
  filter).

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only, no fallback ladder**
(`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`). One
button-level testid is new (implementer work via `add-data-testid`); the two
icon-state sub-selectors are **also new, real app-authored testids** (updated
during implementation fix round 2 — see note below the table): the original
declared improvisation, which chained off MUI's own auto-generated
`data-testid` on the icon `<svg>` children, was REJECTED at review because
that attribute is `NODE_ENV`-gated and stripped on every production/deployed
build. Everything else is pre-existing and confirmed live/in-source this
session.

| Element | Testid | Provenance |
|---|---|---|
| Page title | `secrets-page-title` | pre-existing (ELITEA-2336) |
| "+" add button | `secrets-add-button` | pre-existing (ELITEA-2336) |
| Secret row | `secret-row` | pre-existing (ELITEA-2336) |
| Name input (create flow) | `secret-name-input` | pre-existing (ELITEA-2336) |
| Value input (create flow) | `secret-value-input` | pre-existing (ELITEA-2336) |
| Save (✓) button | `secret-row-save-button` | pre-existing (ELITEA-2336) |
| Value cell (masked/plaintext) | `secret-value-cell` | pre-existing (ELITEA-2336), `SecretValueCell.jsx:46` |
| **Show/Hide toggle button** | `secret-row-visibility-toggle-button` | **testid needed** — `SecretsTable.jsx:497-509`, zero testid today (confirmed live DOM query + source read); uniqueness confirmed (`git grep` on EliteaUI `main` AND `automation/testids` — zero hits) |
| Three-dot / more-actions button | `secret-row-actions-button` | pre-existing (ELITEA-2338) |
| "Delete" menu item | `secret-actions-menu-delete` | pre-existing (ELITEA-2338) |
| Delete confirmation dialog + fields | `delete-confirm-dialog` / `delete-confirm-name-input` / `delete-confirm-button` | pre-existing — shared `DeleteEntityModal.jsx` |

**Icon-state sub-selectors (scoped off the button testid above) — UPDATED,
fix round 2 (reviewer finding, PR #1224):**

```python
# class level, on secrets_page.py — scoped off row_actions-style pattern,
# same shape as SECRET_ROW_ACTIONS_BUTTON_SELECTOR
VISIBILITY_ICON_VISIBLE_SELECTOR = '[data-testid="secret-row-visibility-icon-show"]'
VISIBILITY_ICON_HIDDEN_SELECTOR = '[data-testid="secret-row-visibility-icon-hide"]'
```

**Superseded reasoning (original, rejected at review):** the original
version of this selector pair chained off MUI's own auto-generated
`data-testid` on the icon `<svg>` (equal to the icon component's export
name — `VisibilityIcon` / `VisibilityOffIcon`), justified as a scoped
sub-selector closest to canon `#277`'s "same-element conditional pair"
shape. **This was incorrect**: reading
`node_modules/@mui/material/utils/createSvgIcon.js` directly shows the
attribute is set only `process.env.NODE_ENV !== 'production'` — a `vite
build` (every deployed env / promotion gate) strips it to `undefined`.
Green on localhost (Vite dev server) 100% of the time, silently
unlocatable on every deployed environment — exactly the "confirmed live
against a dev server only" trap `.agents/role-overrides.md` warns about
elsewhere in this project.

**Current (fixed) reasoning:** real, app-authored `data-testid`s were added
directly on the two icon call sites in `SecretsTable.jsx`
(`EliteaAI/EliteaUI@e6260731`, on `automation/testids`) —
`secret-row-visibility-icon-show` on `<VisibilityIcon>` (masked state,
click reveals) and `secret-row-visibility-icon-hide` on
`<VisibilityOffIcon>` (revealed state, click hides). `createSvgIcon`'s own
JSX spreads `...props` *after* its internal auto-`data-testid`, so the
explicit prop overrides it in both dev AND prod builds (confirmed by
reading the same file). This is still canon `#277`'s "same-element
conditional pair, both branches referenced" shape (two mutually-exclusive
branches, both named, both referenced by locators on this test's own
executed path — steps 3/6 assert the `-show` testid present, steps 6/9
assert the `-hide` testid present) — now with a real, build-mode-stable
testid instead of a vendor-internal debug artifact. Durable rule recorded:
`.agents/memory/qa-engineer/mui_icons_material_auto_testid_on_icon_svg.md`
— never use an MUI-auto `data-testid` on an icon `<svg>` as a locator
basis, in any capacity; ask for a real app-authored testid instead.

## Network Behavior
- `POST /api/v2/secrets/secrets/default/{project_id}` — create (step 2), `201`.
- `GET /api/v2/secrets/secrets/default/{project_id}` — list refetch, fires on
  navigate/create.
- `GET /api/v2/secrets/secret/default/{project_id}/{name}` — **singular**
  "secret" (same path shape as the DELETE endpoint, different HTTP method) —
  fires on clicking the Show/reveal toggle (step 4), `200 OK`. Response body
  confirmed live: `{"name": "<name>", "secret_name": "{{secret.<name>}}",
  "is_hidden": false, "value": "<plaintext>"}`.
- **No request fires on clicking Hide/crossed-eye** (step 7) — confirmed live
  via before/after `browser_network_requests` diff, zero new entries. This is
  the `useSecretVisibility.hooks.js` `handleHideSecret` function, which is
  100% client-state (`setRows(... secretValue: row.secret_name)`), distinct
  from the DIFFERENT `hideSecret` mutation wired to the three-dot menu's
  "Hide" item (`onClickHide` → `handleHideSecretPermanently` →
  `useSecretHideMutation`), which DOES call the server and shows a
  confirmation dialog first. Do not conflate the two — same button-row area,
  two functionally different "hide" concepts, only one of which this case
  exercises (the row-level toggle, not the menu item).
- `DELETE /api/v2/secrets/secret/default/{project_id}/{name}` — fires on this
  case's own cleanup step, `204 No Content` (reused ELITEA-2338 mechanics).

## Known Defects Found During Exploration
None newly found. Known defect `EliteaAI/elitea-testing-public#1203` (OPEN —
React "Maximum update depth exceeded" console warning on every
`/settings/secrets` mount) was **NOT observed** during this session — 0
console errors/warnings across the full navigate → create → reveal → hide →
delete flow. Same inconclusive pattern ELITEA-2337's and ELITEA-2338's AFS
already documented (fires deterministically in the covering test's own
automated run, but not in every live exploration session) — the implementer
should check their own automated run's console output rather than assume
either way; if `#1203` fires, wrap the console-error assertion(s) with
`expect.soft()` + `# Known defect: #1203` (sanctioned-RED per
`.agents/testing.md` § Merge gate); if it doesn't fire, assert cleanly. This
case adds no NEW defect.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Page object: extend `automation/pages/secrets_page.py` — reuse `navigate()`,
  `click_add_button()`, `fill_new_row()`, `click_save_button()`,
  `get_row_by_name()`, `get_row_value_cell()`, `open_row_actions_menu()`,
  `click_delete_menu_item()`, `fill_delete_confirm_name()`, `confirm_delete()`
  verbatim (all pre-existing from ELITEA-2336/ELITEA-2338). Add ONE new
  method, e.g. `toggle_visibility(row)`, plus a `get_visibility_icon_testid(row)`
  helper reading the scoped icon `<svg>`'s `data-testid` attribute (via
  `.get_attribute("data-testid")` on the scoped locator — no `browser_evaluate`
  needed in the actual test, that was only used live during analysis to probe
  the DOM structure; Playwright's own `Locator.get_attribute()` is the correct
  production mechanism).
- Wait strategy: `page.expect_response()` scoped to
  `SECRET_DELETE_URL_SUBSTRING` (already defined in `secrets_page.py` — the
  reveal GET shares the exact same URL substring as the delete endpoint,
  differing only by HTTP method, so the existing `_is_delete_response`-style
  predicate pattern can be reused with `method == "GET"` instead of
  `"DELETE"`) for the reveal click; for the hide click, assert the ABSENCE of
  a new matching request within a short window instead of waiting on one —
  the value-cell text change is itself the settle signal to wait on
  (`expect(value_cell).to_have_text(masked_string)`).
- `open_row_actions_menu()`'s existing declared-improvisation React-onClick
  workaround (documented in `secrets_page.py`) was tried again live this
  session for the cleanup delete flow and was **NOT needed** — a normal
  Playwright `.click()` opened the three-dot menu successfully on the first
  attempt. Flagged as a possible flakiness/non-determinism in that root cause
  (not resolved here) — the implementer should keep the existing workaround
  in place (safe superset) rather than remove it on the strength of this one
  session's contrary observation.
- The Show/Hide toggle button is NOT gated by `isDefault` (unlike the
  three-dot menu's three items) — confirmed in source
  (`SecretsTable.jsx:496-509`, no `disabled` prop at all on this
  `IconButton`). Irrelevant to this case since it targets a freshly-created,
  never-default secret anyway, but worth knowing if a future case wants to
  test the toggle against a default/system secret specifically.

## Note on the two distinct "hide" mechanisms (no clarification filed — not needed)
This row has TWO functionally different "hide" affordances: the row-level
eye-icon toggle this case exercises (client-side only, no API call — see
§ Network Behavior) and the three-dot menu's "Hide" item (server-side
`hideSecret` mutation via `useSecretRowActions.hooks.js`'s
`handleHideSecretPermanently`, behind its own confirmation dialog). Initially
flagged this as a possible case-text ambiguity worth a clarification ticket,
but a dedup check (`env -u GITHUB_TOKEN gh issue list --repo
EliteaAI/elitea-testing-public --state all`) found **issue #852**
(`[Automate][ELITEA-2344][settings-secrets] Hide option permanently removes
the secret from the Secrets table`) — a SEPARATE sibling TMS case that
exists specifically to cover the three-dot menu's server-side "Hide". Its
existence confirms the two mechanisms are deliberately split across two
different cases, and ELITEA-2343's own steps (3–8) consistently refer to only
the row-level eye icon throughout, never the menu — so there is no actual
case-text drift here, just two similarly-named but legitimately distinct
behaviors. No clarification ticket filed (none was warranted once #852 was
found); noting this here so the implementer doesn't conflate the two when
reading `SecretActionsMenu.jsx` / `useSecretRowActions.hooks.js` and reach
for the wrong hook.
