# Test Case: Remote MCP — Timeout / Cache TTL Configuration (FAMILY)

## Metadata
- **TMS IDs**: ELITEA-1956 (Timeout, 300 → 60), ELITEA-1957 (Cache TTL, 300 → 600)
- **Family AFS**: yes — both cases are pure **data** variants of ONE flow (open a Remote
  MCP detail page in Form view → expand the configuration section → verify the numeric
  field's default `300` → verify its info icon → type the new value → Save → reload →
  verify persistence → switch to Raw Json → verify the same value under `settings` →
  restore `300`). Same actions, same order; only the *field*, the *new value* and the
  *JSON key* differ. Implement as ONE parameterized spec, one row per TMS case, each row
  asserting its OWN expected values.
- **Linked Story**: none
- **Priority**: l2 (both cases: frontmatter `priority: medium`, body prose
  `**Priority:** medium` — consistent for once; no contradictory metadata to report)
- **Markers**: `pytest.mark.ui`, `pytest.mark.toolkits`, `pytest.mark.mcp`,
  `pytest.mark.p2`, `pytest.mark.regression`
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @
  `automation/testids`, DEV backend), 2026-08-24
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (analyst slot), cluster dispatch, batch `mcp-w04`, 2026-08-24
- **Status**: ready-for-automation
  - Both cases executed live end-to-end on one seeded Remote MCP (toolkit **3247**,
    project `${ELITEA_PROJECT_ID}`). Every step passed against the live product.
    No product defect found. Two non-blocking findings: one **testid gap** (the info
    icon of § Step 3 — a work order, not a waiver) and one **case-text drift**
    (the Raw-Json value type — see § Known Defects / Clarifications).

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs:
  Keycloak login as `${TEST_USER}`).
- Project context set from `${ELITEA_PROJECT_ID}`.
- **A Remote MCP whose Timeout and Cache TTL are still at their defaults (`300`).**
  Seed it per-test via the UI create flow (§ Test Data) — do NOT reuse a leftover
  toolkit: this family's very first assertion is "the field shows the default `300`",
  which a previously-edited MCP would silently invalidate.
  `ToolkitAPI.list_all_toolkits()` returns `[]` on this environment regardless of auth
  method (documented quirk), so there is no reliable read-only discovery path — the
  UI create flow is the stable seeding choice, same precedent as ELITEA-1929.
- **The create form must be reached by CLICKING the Remote MCP type card**, never by
  direct navigation to `/mcps/create/mcp` (redirects back to the type picker —
  ELITEA-1921 finding, still true).

## Test Data

### Parameter table (one row per TMS case)

| TMS case | Field | Field handle | Info-icon handle (testid needed) | Default (confirmed live) | New value | Raw-Json key | Raw-Json value observed live | Sibling field that must stay unchanged |
|---|---|---|---|---|---|---|---|---|
| ELITEA-1956 | Timeout | `toolkit-field-timeout-input` | `toolkit-field-timeout-info-icon` | `"300"` | `"60"` | `settings.timeout` | `"60"` (**JSON string**, not the number `60` the case text prints) | `cache_ttl` stays `300` |
| ELITEA-1957 | Cache TTL | `toolkit-field-cache_ttl-input` | `toolkit-field-cache_ttl-info-icon` | `"300"` | `"600"` | `settings.cache_ttl` | `"600"` (**JSON string**, not the number `600` the case text prints) | `timeout` stays `300` |

### generate-per-test (created by the test, deleted in its own teardown)
- **Toolkit Name**: `autotest_mcp_ttl_<6hex>` (24 chars — well under the silently
  truncating `MAX_NAME_LENGTH = 32` on the Name field).
- **Url**: `https://mcp.example.com/sse` — never dialled (this family never clicks Load
  Tools), so its unreachability is irrelevant. Confirmed live: creation succeeds and the
  detail page renders fully.

### reuse-existing
- `${TEST_USER}` — deployed envs only; localhost skips login entirely.

## Test Steps

Written once for the family. `{field}`, `{field_handle}`, `{info_icon_handle}`,
`{new_value}`, `{json_key}`, `{sibling_field}` resolve per the parameter-table row.

**Setup (not a case step — precondition materialisation).** Navigate to `/mcps/create`,
click `toolkit-type-card-mcp`, fill `toolkit-form-name-input` and
`toolkit-field-url-input`, click `toolkit-form-save-button`, wait for the create **POST
201** and capture `response["id"]` as `toolkit_id`. The app navigates to
`/mcps/all/{toolkit_id}` by itself.
*Confirmed live:* the create response body carries
`settings.timeout == 300` and `settings.cache_ttl == 300` as **JSON numbers** — an
untouched default is stored numeric; only a UI-typed value becomes a string (see
§ Known Defects / Clarifications).

1. **Open the Remote MCP detail page in Form view.**
   - Action: `McpFormPage.navigate_to_detail(toolkit_id, project_id)` then
     `wait_for_page_load()`.
   - **Verify**: `/mcps/all/{toolkit_id}` is in `page.url`; `toolkit-detail-title` shows
     the seeded toolkit name (retrying `expect(...).to_have_text(...)` — the header lags
     the data, a bare read is a guaranteed flake on this surface).
   - **Then call `expand_configuration_section()`** — on the detail page **no**
     `toolkit-field-*` element exists in the DOM until the
     `toolkit-configuration-show-more` control is clicked. This is a hard precondition of
     every step below; the toggle also **mounts ~1 s late**, so never probe it with a
     non-waiting read.

2. **Verify `{field}` shows its default `300`.**
   - **Verify**: `{field_handle}.input_value() == "300"`.
   - *Confirmed live for both rows:* value `"300"` (the element **also** carries
     `placeholder="300"`, derived from the schema default at
     `ToolBaseProperty.jsx:592-596` — assert `input_value()`, never the placeholder, or a
     genuinely empty field would pass).

3. **Verify the info icon is present next to the `{field}` label.**
   - **Verify**: `{info_icon_handle}` is visible.
   - **⚠ testid needed** — see § Handles Reference. Live the icon renders as
     `<span data-info-tooltip="true"><svg …></span>` inside the field's `<label>`, with
     **no testid**. Locator policy is testid-only: the implementer runs `add-data-testid`
     (exact work order in § Handles Reference) — do NOT substitute a role/CSS/attribute
     handle "for now".

4. **Change `{field}` to `{new_value}`.**
   - Action: `fill_timeout("60")` / `fill_cache_ttl("600")` (both helpers already exist).
   - **Verify**: `{field_handle}.input_value() == "{new_value}"`, **and**
     `toolkit-detail-save-button` is now **enabled** (it is disabled on the pristine
     detail page — confirmed live `disabled: true` before the edit, `false` after).
     Unlike the create form (#633) this dirty→enabled assertion is honest here.

5. **Save the MCP.**
   - Action: `save_and_wait_for_updated(project_id, toolkit_id)`.
   - **Verify**: the update **PUT returns 200** and its body's
     `settings["{json_key}"]` equals `"{new_value}"`.
   - **Do NOT wait for a success toast** — the MCP detail Save renders none
     (`toast-message` never appears; confirmed again this session). The PUT 200 + the
     persisted state is the operation-completed observable.

6. **Reload the page and verify `{field}` still shows `{new_value}`.**
   - Action: `page.reload()` → `wait_for_page_load()` → **`expand_configuration_section()`
     again** (the section re-collapses on every reload).
   - **Verify**: `{field_handle}.input_value() == "{new_value}"`.
   - **Verify (Axis 2)**: `{sibling_field}` still reads `"300"` — the edit is scoped to
     the one field.

7. **Switch to Raw Json and verify `settings.{json_key}`.**
   - Action: `switch_to_raw_json_view()` → `get_raw_json_full()` (the payload is longer
     than CodeMirror's virtualization window; `get_raw_json()` would read a truncated
     document).
   - **Verify**: `str(raw["settings"]["{json_key}"]) == "{new_value}"`.
     *Live the value is the JSON **string** `"60"` / `"600"`, while the case text prints
     the bare number.* Assert via `str(...)` so the assertion states the case's
     requirement ("JSON shows the new value") without hard-coding a type the case never
     specified — and additionally assert the concrete observed shape
     `isinstance(raw["settings"]["{json_key}"], str)` so a silent product change of the
     persisted type is caught. Same precedent as the merged
     `test_mcp_create_remote.py:196-199`.
   - **Verify (Axis 2)**: `raw["settings"]["{sibling_field}"]` is unchanged.

8. **Restore the default and save.**
   - Action: `switch_to_form_view()` → `expand_configuration_section()` →
     `fill_{field}("300")` → `save_and_wait_for_updated(...)`.
   - **Verify**: the PUT 200 body's `settings["{json_key}"]` is `"300"`.
   - **ELITEA-1956** carries this as its own case step 8 ("Change back to 300 and save →
     Timeout is restored to default") → assert it as a case step.
     **ELITEA-1957** has no restore step; for that row this is Axis-2 coverage doubling as
     the family's state restoration (grounded: it proves the field is freely re-editable
     in both directions and returns the seeded MCP to its documented default before
     teardown). Executed and asserted identically for both rows.

## Handles Reference

All handles below were exercised live in this session unless the PROVENANCE column says
`needs-adding`.

| # | Element | Primary handle (testid) | PROVENANCE (verified 2026-08-24, after `git fetch origin` in `../EliteaUI`) | Notes |
|---|---|---|---|---|
| 1 | Remote MCP type card | `toolkit-type-card-mcp` | on-main ✓ — runtime-composed `` data-testid={`toolkit-type-card-${itemKey}`} `` at `CategoryItemCard.jsx:14`, present on `origin/main` and `origin/automation/testids` | seeding only; mounts asynchronously |
| 2 | Toolkit Name input | `toolkit-form-name-input` | on-main ✓ | seeding only |
| 3 | Url input | `toolkit-field-url-input` | on-main ✓ — runtime-composed `` testId={`toolkit-field-${k}-input`} `` at `ToolBaseProperty.jsx:281,316` on both refs | seeding only |
| 4 | Save (create form) | `toolkit-form-save-button` | on-main ✓ | seeding only |
| 5 | Configuration "show more" | `toolkit-configuration-show-more` | on-main ✓ | **mandatory** before any `toolkit-field-*` read on the detail page; re-required after every reload |
| 6 | Timeout input | `toolkit-field-timeout-input` | on-main ✓ (same composed template as #3) | already bound: `McpFormPage.timeout_input` |
| 7 | Cache TTL input | `toolkit-field-cache_ttl-input` | on-main ✓ (same composed template as #3) | already bound: `McpFormPage.cache_ttl_input` |
| 8 | Detail Save button | `toolkit-detail-save-button` | on-main ✓ | `McpFormPage.detail_save_button`. **Not** `toolkit-form-save-button` — that one does not exist on the detail page (cost a probe this session) |
| 9 | Detail title | `toolkit-detail-title` | on-main ✓ | placeholder `"Edit MCP"` until the GET resolves |
| 10 | Raw Json view toggle | `toolkit-raw-json-view-toggle` | on-main ✓ | |
| 11 | Raw Json editor content | `toolkit-raw-json-editor-content` | on-main ✓ | read via `get_raw_json_full()` |
| 12 | Form view toggle | `toolkit-form-view-toggle` | on-main ✓ | |
| 13 | **Timeout info icon** | **`toolkit-field-timeout-info-icon`** | **ADDED during implementation** — EliteaAI/EliteaUI@25c47d7d on `automation/testids`; NOT yet on `main` (human cherry-pick) | work order below, executed as written |
| 14 | **Cache TTL info icon** | **`toolkit-field-cache_ttl-info-icon`** | **ADDED during implementation** — EliteaAI/EliteaUI@25c47d7d on `automation/testids`; NOT yet on `main` (human cherry-pick) | work order below, executed as written |

### Work order — the two info-icon testids (`add-data-testid`, rows 13/14)

The plumbing already exists end to end; only the **call-site props** are missing.
`ToolBaseProperty.jsx` renders the label's info icon through
`Input.StyledInputEnhancer` → `InputBase` → `InfoTooltip`, and `InfoTooltip` already
accepts `testId` / `contentTestId`. `ToolBaseProperty.jsx` already supplies them — but
**only for `k === 'bucket'`**:

```jsx
// src/[fsd]/features/toolkits/ui/form/ToolBase/ToolBaseProperty.jsx:615-618 (current)
{...(k === 'bucket' && {
  tooltipTestId: 'toolkit-field-bucket-info-icon',
  tooltipContentTestId: 'toolkit-field-bucket-info-tooltip-content',
})}
```

Extend that same per-key allow-list with `timeout` and `cache_ttl`, naming them
`toolkit-field-timeout-info-icon` / `toolkit-field-cache_ttl-info-icon` — exactly the
`toolkit-field-bucket-info-icon` precedent already on `origin/main`.

- **Only `tooltipTestId` is needed.** Neither case opens the tooltip (both say only
  "info icon is visible"), so **do not** add the `-info-tooltip-content` sibling —
  an unreferenced testid inflates the presence-based coverage metric (#511).
- **Scope it per key, do not make it generic.** Passing `tooltipTestId` for *every*
  schema field would blanket-add testids to untested elements — the exact anti-pattern
  `.agents/testing.md` § Locator policy forbids.
- **Zero functional impact**: two additive props on an existing call, no new DOM node,
  no new hook, no removed line — clears the `add-data-testid` § Step 5.5 greps.

**Shipped during ELITEA-1956/1957 implementation (2026-08-24)** exactly as specified —
EliteaAI/EliteaUI@25c47d7d on `automation/testids`:

```jsx
{...((k === 'timeout' || k === 'cache_ttl') && {
  tooltipTestId: `toolkit-field-${k}-info-icon`,
})}
```

Only `tooltipTestId`, scoped per key, added as a SECOND spread beside the existing
`bucket` one (leaving that line byte-identical). All three `add-data-testid` § Step 5.5
greps returned 0 hits (no new hook, no new DOM node, no removed line).

## Coverage Map

### Axis 1 — every element of the original cases

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| 1956/1957 precondition: user logged in | — | Setup (localhost auto-auth) | — | covered |
| 1956/1957 precondition: existing Remote MCP open in Form view | detail page in Form view | Setup + Step 1 | Step 1 | covered (seeded per test) |
| 1956 step 1 / 1957 step 1 — open detail page in Form view | Detail page loads in Form view | Step 1 | url + `toolkit-detail-title` | covered |
| 1956 step 2 — Timeout default is 300 | Field shows 300 | Step 2 (row 1956) | `timeout_input.input_value() == "300"` | covered |
| 1957 step 2 — Cache TTL default is 300 | Field shows 300 | Step 2 (row 1957) | `cache_ttl_input.input_value() == "300"` | covered |
| 1956 step 3 / 1957 step 3 — info icon present | Info icon visible | Step 3 | `{info_icon_handle}` visible | covered **after** the testid work order (rows 13/14) |
| 1956 step 4 — change Timeout to 60 | Field displays 60 | Step 4 (row 1956) | `input_value() == "60"` | covered |
| 1957 step 4 — change Cache TTL to 600 | Field displays 600 | Step 4 (row 1957) | `input_value() == "600"` | covered |
| 1956 step 5 / 1957 step 5 — Save | Operation completes successfully | Step 5 | PUT 200 + response `settings` | covered (no toast exists — see Step 5) |
| 1956 step 6 / 1957 step 6 — reload, value persists | Field shows the new value | Step 6 | `input_value()` after reload | covered |
| 1956 step 7 — Raw Json shows `"timeout": 60` | JSON shows timeout as 60 | Step 7 (row 1956) | `str(raw["settings"]["timeout"]) == "60"` | covered — **value type is a clarification**, see § Known Defects |
| 1957 step 7 — Raw Json shows `"cache_ttl": 600` | JSON shows cache_ttl as 600 | Step 7 (row 1957) | `str(raw["settings"]["cache_ttl"]) == "600"` | covered — same clarification |
| 1956 step 8 — change back to 300 and save | Timeout restored to default | Step 8 (row 1956) | PUT 200 body `settings.timeout == "300"` | covered |
| 1956 "Expected Final State" — updated, persisted, confirmed in both views, restored | — | Steps 4–8 | — | covered |
| 1957 "Expected Final State" — updated to 600, persisted after reload, correct in Raw Json | — | Steps 4–7 | — | covered |
| 1956/1957 Pass criterion — "all steps complete without errors" | no errors | Step 5 PUT 200 + console-error check (see § Automation Hints) | every step | covered |

### Axis 2 — observables asserted BEYOND the case text

| Extra assertion | Grounded reason |
|---|---|
| Detail Save button is **disabled** on the pristine page and **enabled** after the edit (Step 4) | The case's "Save MCP" step presumes an actionable Save; asserting the dirty gate makes the precondition explicit and catches a regression where Save is dead. Honest on this surface (unlike the create form's #633). |
| The **PUT status is 200** and its body carries the new value (Step 5) | "Operation completes successfully" has no toast to observe on this surface; the network response is the only real success observable. |
| The **sibling** numeric field is unchanged after the save (Steps 6 & 7) | Both fields live in one `settings` object saved by one PUT — a serializer bug that clobbers the neighbour would otherwise pass both cases silently. Cheap, high-value. |
| `isinstance(raw["settings"][key], str)` (Step 7) | Pins the concrete persisted shape observed live, so a silent product change of the stored type is caught rather than absorbed by `str()`. Same precedent as merged `test_mcp_create_remote.py:196-199`. |
| Restore-and-verify executed for **ELITEA-1957** too (Step 8) | Returns the seeded MCP to its documented default before teardown and proves the field is editable in both directions. Case-mandated for 1956; Axis 2 for 1957. |
| No unexpected console errors across the flow | Standard side-channel check (§ Automation Hints has this session's live baseline). |

## Known Defects / Clarifications

**No product defect found.** Both cases pass end-to-end against the live product.

### CLARIFICATION #1745 (case-text drift, both cases) — Raw-Json value is a JSON *string*

Both case texts print the expected Raw-Json entry as a bare number
(`"timeout": 60`, `"cache_ttl": 600`). Live, a value typed into either field persists and
renders as a **JSON string**:

```
ELITEA-1956 → settings.timeout   == "60"    (type: str)
ELITEA-1957 → settings.cache_ttl == "600"   (type: str)
```

An **untouched** default is stored as a **number** (`300`) — the create response for the
freshly seeded MCP 3247 carried `"timeout": 300, "cache_ttl": 300` numerically, and the
sibling field kept that numeric `300` through both saves.

This is the product's actual (if inconsistent) schema behaviour, already established at
ELITEA-1922 and asserted by merged `test_mcp_create_remote.py:196-199`. Per the
reverse-masking guard this is **case-text drift, not a defect**: the case's real
requirement ("the JSON reflects the new value") is satisfied. Asserted with `str(...)`
plus an explicit type assertion — no soft-assert, no `# Known defect`, no red.
→ Filed as **#1745** (`[Clarification][ELITEA-1956/1957] …`, label `question`) for the TMS
owner; **not filed as a `bug`** (per `.agents/profile.md` § Bug filing + the reverse-masking
guard). Automation is unblocked.

### Not a defect, but load-bearing for the implementer

- **No success toast on the MCP detail Save.** Pre-existing, already recorded in the
  surface digest; re-confirmed this session. Never wait on `toast-message` here.
- **Console was completely clean** across both full flows this session (0 error-type
  messages, including the `#291` React dev-mode warnings and the `#549` MUI-Tabs warning
  that `test_mcp_edit_toggle_enable_caching.py` filters/soft-fails for). See
  § Automation Hints for how to treat that.

## Blocked Steps

None. Every step of both cases was executed and observed live.

## Cleanup

- The seeded MCP is deleted in the test's own teardown (`ToolkitAPI` delete, or the
  detail page's three-dot **Delete** — `test_mcp_delete.py` precedent). Prefer the API.
- Step 8 restores both fields to `300` before teardown, so an interrupted run leaves the
  toolkit in its documented default state rather than a half-edited one.
- **Toolkit 3247** (`autotest_mcp_ttl_*`) was created by this analysis session and left
  behind with both fields restored to `300` — a harmless artefact; the implementer may
  delete it or ignore it (the spec must seed its own, never reuse it).

## Automation Hints

- **Everything this family needs already exists in `McpFormPage`** — `navigate_to_create`,
  `select_remote_mcp_type`, `fill_name`, `fill_url`, `save_and_wait_for_created`,
  `navigate_to_detail`, `wait_for_page_load`, `expand_configuration_section`,
  `fill_timeout`, `fill_cache_ttl`, `save_and_wait_for_updated`,
  `switch_to_raw_json_view`, `switch_to_form_view`, `get_raw_json_full`,
  `detail_save_button`. The only new page-object work is the **two info-icon
  `LocatorDescriptor` fields** (rows 13/14) once the testids are added.
- **Parameterize with `pytest.mark.parametrize`**, one id per TMS case
  (`ELITEA-1956` / `ELITEA-1957`), so each row reports separately and the TMS
  back-write can name one node-id per case.
- **Traps that cost time this session (all avoidable):**
  1. `is_save_button_disabled()` binds the **create** form's `toolkit-form-save-button`
     and times out on the detail page — use `detail_save_button` there.
  2. `expand_configuration_section()` is required **again after every `page.reload()`**.
  3. `get_raw_json()` (non-`_full`) reads a CodeMirror-virtualized, truncated document —
     always `get_raw_json_full()` for this payload.
- **Console-error assertion.** This session observed **zero** error-type console messages
  across both flows, including the `#291` dev-mode warnings and the `#549` MUI-Tabs
  warning that the merged ELITEA-1929 spec still filters/soft-fails. Do **not** conclude
  those are fixed — this probe ran headless in a fresh context and may simply not have
  hit them. Reuse ELITEA-1929's exact split-filter shape (known `#291` filtered, known
  `#549` soft, anything else a hard fail); it degrades gracefully to a clean pass if the
  warnings really are gone.
- Wrap each step in `with allure.step("Step N — …")`, one block per numbered step above.

**Implemented (2026-08-24):**
`automation/tests/ui/toolkits/test_mcp_edit_timeout_cache_ttl.py::test_mcp_edit_timeout_cache_ttl[ELITEA-1956]`
and `…[ELITEA-1957]` — one parameterized spec as specified. `BasePage.reload_and_wait()`
was used for Step 6's reload (it already dispatches to `McpFormPage.wait_for_page_load()`,
so the AFS's `page.reload()` + `wait_for_page_load()` pair needs no separate call). Every
step's assertion landed as written; the Step 5 / Step 8 PUT bodies do carry
`settings[<key>]` as specified. Ran GREEN 2/2 first try, 61.7 s, zero reruns.
