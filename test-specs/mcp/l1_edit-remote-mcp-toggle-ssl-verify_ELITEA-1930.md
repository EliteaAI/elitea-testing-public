# Test Case: Edit Remote MCP — Toggle SSL Verify

## Metadata
- **TMS ID**: ELITEA-1930
- **Linked Story**: none
- **Priority**: l1 (case frontmatter: `priority: critical`; case body says
  "medium" — same pre-existing inconsistency recorded in the ELITEA-1929 /
  ELITEA-1926 AFS; frontmatter authoritative)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @
  `automation/testids`, DEV backend), project 399
- **User set**: `${TEST_USER}` (localhost: `VITE_DEV_TOKEN` auto-auth)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot), session 2026-08-24
- **Status**: ready-for-automation

## Preconditions
- User is authenticated; project id from `${ELITEA_PROJECT_ID}`.
- A Remote MCP exists and its detail page is open in Form view.
- "Ssl Verify" is checked by default — **confirmed live**: a freshly created
  Remote MCP has `settings.ssl_verify == true`.

## Test Data

### generate-shared-with-cleanup

Identical reasoning to the sibling ELITEA-1929 (Enable Caching) AFS: no
discoverable pre-existing Remote MCP, and flipping `ssl_verify` is destructive to
whatever toolkit is used → the test seeds its own disposable Remote MCP through
the real UI create flow and deletes it in teardown.

| Field | Value | Why |
|---|---|---|
| Seed name | `autotest_mcp_ssl_<6hex>` (23 chars) | ≤ `MAX_NAME_LENGTH = 32` |
| Url | `https://mcp.example.com/sse` | stored only; never dialled (no Load Tools in this case) |
| (case Test Data) | none required | — |

## Test Steps

Live-executed 2026-08-24 against `http://localhost:5173` (seeded toolkit id 3029,
deleted after the run).

| # | Action | Expected (case) | Observed live |
|---|--------|-----------------|---------------|
| 1 | Open a Remote MCP detail page in Form view | Detail page loads in Form view | `toolkit-form-view-toggle` `aria-pressed == "true"`; `toolkit-detail-title` == seeded name |
| 2 | Note current state of "Ssl Verify" checkbox (checked by default) | Checkbox is checked | **`toolkit-field-ssl_verify-checkbox-field` count == 0 until the configuration section is expanded** (digest § MCP DETAIL page: configuration fields are COLLAPSED). After `expand_configuration_section()`: `.checked is True`. Expanding does **not** dirty the form — Save/Discard stay disabled. |
| 3 | Click "Ssl Verify" to uncheck it | Checkbox becomes unchecked | click the MUI `<span>` (`toolkit-field-ssl_verify-checkbox`); the real `<input>` (`...-checkbox-field`) flips to `.checked is False`; Save becomes enabled |
| 4 | Click Save | Operation completes successfully | `PUT /tool/prompt_lib/{project}/{id}` → **200**; response body `settings.ssl_verify is False`. **No success toast is rendered on this surface** (digest, confirmed on two prior probes) — the PUT + the persisted state is the confirmation. |
| 5 | Reload page — verify "Ssl Verify" is unchecked | Checkbox remains unchecked after reload | after `reload_and_wait()` the field is **again count == 0 until expanded** (the collapse state is not remembered); after expanding, `.checked is False` |
| 6 | Switch to Raw Json — verify `"ssl_verify": false` in JSON | JSON shows ssl_verify as false | `get_raw_json()["settings"]["ssl_verify"] is False` (the boolean, not the string). Verified live, full editor payload was 376 chars — well under the CodeMirror virtualization threshold, so `get_raw_json()` is safe here; `get_raw_json_full()` is not needed. Note the key lives under **`settings`**, not at the JSON root. |

## Expected Results
- Ssl Verify is checked on a freshly created Remote MCP.
- Unchecking it dirties the form and enables Save.
- Save issues a `PUT` returning 200 whose body carries `settings.ssl_verify: false`.
- The unchecked state survives a full page reload (server-side persistence).
- The Raw Json view shows the boolean `false` under `settings.ssl_verify`.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Disposition | Where asserted |
|---|---|---|
| Precondition: logged in | precondition | framework `auth_state` |
| Precondition: existing Remote MCP open in Form view | precondition (substituted seed) | seeded via the UI create flow — § Test Data; Form view asserted in step 1 |
| Precondition: "Ssl Verify" is checked by default | asserted | step 2's `is_ssl_verify_checked() is True` on the freshly seeded MCP |
| Step 1 — detail page loads in Form view | asserted | `form_view_toggle` `aria-pressed == "true"` + `detail_title` == seeded name |
| Step 2 — checkbox is checked | asserted | `is_ssl_verify_checked() is True` (after expanding configuration) |
| Step 3 — checkbox becomes unchecked | asserted | `is_ssl_verify_checked() is False` |
| Step 4 — Save completes successfully | asserted | PUT 200 + body `settings.ssl_verify is False` |
| Step 5 — unchecked after reload | asserted | post-reload (+ re-expand) `is_ssl_verify_checked() is False` |
| Step 6 — Raw Json shows `ssl_verify: false` | asserted | `get_raw_json()["settings"]["ssl_verify"] is False` |
| Expected Final State — toggle unchecked, saved, reflected in Raw Json | asserted | steps 4-6 together |
| Pass criterion: no errors during the flow | asserted | console-error listener (known #291 filtered, #549 soft — sibling-spec pattern) |

### Axis 2 — Analyst additions

| Addition | Why grounded |
|---|---|
| Save-button state assertions (disabled pristine → enabled after the toggle) | Step 4 presupposes Save is clickable; the dirty gate is real on this surface (unlike the create form's #633) and was read in source + confirmed live. |
| PUT-response body assertion | Step 4's "operation completes successfully" is otherwise unobservable — no toast is rendered here. |
| `is` (identity) check on the boolean rather than truthiness | The case says `"ssl_verify": false` — a string `"false"` would be a real defect and must not pass. Mirrors the sibling ELITEA-1929 spec. |
| Explicit `expand_configuration_section()` before every ssl_verify read | The detail page renders **no** `toolkit-field-*` node until expanded — without it the case's steps 2/5 cannot be executed at all. |
| Restore-and-resave at the end | Cleanliness discipline copied from ELITEA-1929; here it is belt-and-braces only, since the seeded toolkit is deleted in teardown. **Not implemented** — teardown deletes the toolkit, so a restore would assert nothing new. See § Cleanup. |
| Console-error monitoring | Case Pass criterion "All steps complete without errors". |

## Cleanup
The seeded toolkit is deleted in a `finally:` block via
`ToolkitAPI.delete_toolkit(id)`. No shared state is mutated (unlike ELITEA-1929,
which pre-dated the seed-and-delete pattern being routine and restored the flag
in-flow), so no in-flow restore is needed — the flag dies with the toolkit.

## Concrete Handles (discovered during exploration)

| Element | Handle | Provenance |
|---|---|---|
| Ssl Verify click target (MUI span) | `toolkit-field-ssl_verify-checkbox` | on-main ✓ |
| Ssl Verify real `<input>` (`.checked`) | `toolkit-field-ssl_verify-checkbox-field` | on-main ✓ |
| Configuration show-more | `toolkit-configuration-show-more` | on `automation/testids` |
| Detail Save button | `toolkit-detail-save-button` | on `automation/testids` (ELITEA-1929, EliteaUI PR #572) |
| Detail Discard button (baseline only) | `toolkit-detail-discard-button` | on `automation/testids` (ELITEA-1929, EliteaUI PR #572) |
| Form view toggle | `toolkit-form-view-toggle` | on-main ✓ |
| Raw Json view toggle / editor | `toolkit-raw-json-view-toggle` / `toolkit-raw-json-editor-content` | on-main ✓ |
| Detail title | `toolkit-detail-title` | on-main ✓ |

No new testid is required for this case.

## Network Behavior
- `POST /tools/prompt_lib/{project}` → 201 (seed).
- `GET /tool/prompt_lib/{project}/{id}` on detail load and after reload.
- `PUT /tool/prompt_lib/{project}/{id}` → 200 on Save.
- The URL is **never dialled** — nothing in this case triggers `mcp_sync_tools`.

## Known Defects Found During Exploration
None.

**Framework gotcha found (not a product defect):**
`toolkit-configuration-show-more` **mounts asynchronously** after a page load —
polled live right after a `goto` on the detail page it was absent on the first
read and present ~1 s later, while `toolkit-detail-title` had already resolved to
the real name. `McpFormPage.expand_configuration_section()` early-returns on
`count() == 0`, so calling it too early silently no-ops and every subsequent
`toolkit-field-*` read then times out. Fixed in this unit — see § Automation Hints.

## Blocked Steps
None.

## Automation Hints
- `expand_configuration_section()` is required **twice**: once on first load and
  once again after `reload_and_wait()` (the section re-collapses).
- Its "already expanded?" test must key off the **fields**, not the toggle
  (the toggle mounts late; the fields are the state that actually matters).
- Use `get_raw_json()` (not `get_raw_json_full()`): this toolkit has no
  discovered tools, so the payload is 376 chars and never virtualization-truncated.
- The Raw Json key is nested under `settings`.
- Assert `is False` / `is True`, not truthiness — a string `"false"` must fail.
