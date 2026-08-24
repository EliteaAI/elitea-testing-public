# AFS — ELITEA-1948: MCP Form/Raw JSON View Toggle — Data Consistency

| Field | Value |
|---|---|
| **TMS case** | ELITEA-1948 |
| **Status** | `ready-for-automation` |
| **Priority** | medium (`p2`) |
| **Surface** | UI — MCP detail page (`/mcps/all/{id}`), Form ⇄ Raw Json view toggle |
| **Feature dir** | `test-specs/mcp/` · suite dir `automation/tests/ui/toolkits/` |
| **Analysed** | 2026-08-24, live against `http://localhost:5173`, project 399, toolkit **3134** (`autotest_conn_tools_a1`) |
| **Analyst** | qa-engineer (Sage), batch `mcp-w03` |
| **Case snapshot** | `.agents/automation/mcp-w03/cases/ELITEA-1948.md` |
| **Defects filed** | none new. Case-text gap on step 9 (the Discard confirmation modal) — **already tracked as #1718**, new occurrence commented there, not re-filed. |

---

## Verdict in one line

**All 9 steps executed live and passed.** Form ⇄ Raw Json is a two-way, in-memory
projection of the same Formik model: an unsaved Raw-Json edit is visible in the Form
view and survives a round trip back, and the (modal-confirmed) Discard reverts both
views. Nothing is persisted anywhere in the flow — the network log for the whole
execution contained **zero** `PUT`/`POST`/`PATCH`/`DELETE`.

---

## Why this is NOT already covered

Read before implementing — three merged neighbours are close and none of them proves
this case's observable:

| Merged spec | What it proves | Why it is not this case |
|---|---|---|
| `automation/tests/ui/toolkits/test_mcp_edit_raw_json_description.py` (ELITEA-1927) | Raw-Json description edit → **Save** → persists after reload | The whole point of ELITEA-1948 is the **unsaved** path. 1927 never switches back to Form with the edit pending and never discards. |
| `automation/tests/ui/toolkits/test_mcp_edit_discard_changes.py` (ELITEA-1928) | Description edited **in Form view**, Discard modal, revert, no `PUT` | Single view only. 1948 requires the revert to be observed **in both views** after an edit made in the *other* view. |
| `automation/tests/ui/toolkits/test_mcp_view_toggle.py` (ELITEA-1944) | MCP **dashboard** card/table view toggle | Different surface entirely (list page), no relation to the detail Form/Raw-Json toggle. |

⇒ `ready-for-automation` (fresh spec), reusing `McpFormPage` wholesale.

---

## Preconditions

- Logged in (localhost `auth_state` bypass via `VITE_DEV_TOKEN`).
- One Remote MCP exists and is open on `/mcps/all/{id}`.

### § Test Data — seed a disposable Remote MCP (`generate-shared-with-cleanup`)

Same reasoning as the sibling ELITEA-1927/1928 specs: `ToolkitAPI.list_all_toolkits()`
returns `[]` on this environment regardless of auth method, so an existing MCP's id
cannot be rediscovered at runtime. Seed through the real UI create flow and delete in
teardown:

```
form.navigate_to_create(); form.select_remote_mcp_type()
form.fill_name(f"autotest_mcp_viewsync_{uuid4().hex[:6]}")   # base name 21 chars, MAX_NAME_LENGTH=32
form.fill_description(ORIGINAL_DESCRIPTION)                   # NON-EMPTY — see below
form.fill_url("https://mcp.example.com/sse")                  # stored only, never dialled
toolkit_id = form.save_and_wait_for_created(project_id)["id"]
```

**Seed a NON-EMPTY original description.** The analysis MCP (3134) had `description: null`
⇄ Form `""`, which makes step 9's revert a revert-*to-empty* — a weak observable. With a
non-empty original, step 9 asserts a real value coming back. (`ORIGINAL_DESCRIPTION` /
`UPDATED_DESCRIPTION` are test-chosen; the case names no data.)

**`null` ⇄ `""` mapping is real and must be tolerated by the assertion helper:** an absent
description serialises as JSON `null` while the Form input reads `""`. Assert
`raw["description"] == form_description or (raw["description"] is None and form_description == "")`
only if the seed can be empty — with the seed above it is always a string, so a plain
equality assertion is correct and preferred.

---

## Execution log — case steps as executed (all live)

| # | Case action | Case expected | **Observed live (2026-08-24, toolkit 3134)** | Verdict |
|---|---|---|---|---|
| 1 | Open a Remote MCP detail page in Form view | Loads in Form view | `/mcps/all/3134` → `toolkit-form-view-toggle` `aria-pressed="true"`, `toolkit-raw-json-view-toggle` `aria-pressed="false"`; `toolkit-detail-title` = `autotest_conn_tools_a1`; Save **and** Discard both **disabled** (pristine) | ✅ |
| 2 | Note Toolkit Name, Description, Url, Timeout, Cache TTL, Enable Caching, Ssl Verify | Values observed | Name `autotest_conn_tools_a1`; Description `""`; **after `expand_configuration_section()`** → Url `https://mcp.deepwiki.com/mcp`, Timeout `300`, Cache TTL `300`, Enable Caching `true`, Ssl Verify `true`. **Before the expand the DOM holds ZERO `toolkit-field-*` nodes** | ✅ |
| 3 | Click "Raw Json" toggle | JSON editor displayed | `toolkit-raw-json-editor-content` visible; raw toggle `aria-pressed="true"`, form toggle `"false"`; **`toolkit-form-name-input` is UNMOUNTED** (the two views swap, they do not co-exist) | ✅ |
| 4 | Verify JSON matches Form (name, description, settings.url, settings.timeout, …) | JSON values match Form | `name` = `autotest_conn_tools_a1`; `description` = `null` (Form `""`); `settings.url` = `https://mcp.deepwiki.com/mcp`; `timeout` 300; `cache_ttl` 300; `ssl_verify` true; `enable_caching` true; plus `scopes`/`headers`/`client_id`/`client_secret` null, `selected_tools` (3), `available_mcp_tools` | ✅ |
| 5 | Modify `description` in Raw Json view | Editor shows updated description | Per-line edit (click line → `End` → `Shift+Home` → type) → `  "description": "Modified via Raw Json",`. **Save and Discard both flip to ENABLED** | ✅ |
| 6 | Click "Form" toggle (without saving) | Form view displayed | `toolkit-form-view-toggle` `aria-pressed="true"`, `toolkit-form-description-input` mounted | ✅ |
| 7 | Verify Form shows the updated description | Description reflects the change | `toolkit-form-description-input.input_value()` == `Modified via Raw Json`; Name unchanged; Save still enabled | ✅ |
| 8 | Click "Raw Json" again — JSON still has the modification | JSON retains the unsaved change | `  "description": "Modified via Raw Json",` still present. **Line count 30 → 29** — the JSON is *re-serialised from the form model* on every view switch, so CodeMirror's auto-indent artefact from step 5 is normalised away | ✅ |
| 9 | Click Discard — verify both views revert | Both views show original values | **A confirmation modal intervenes** (case text omits it — #1718): `toolkit-detail-discard-confirm-modal` text = `WarningAre you sure you want to discard changes?CancelDiscard`. After `toolkit-detail-discard-confirm-button`: modal **detaches**; still in Raw Json view (`aria-pressed="true"`); editor shows `  "description": null,` and is back to 30 lines; Save + Discard back to **disabled**; switching to Form → description `""`. **Network log: no `PUT`/`POST`/`PATCH`/`DELETE` at any point** | ✅ (modal step is an addition to the case text) |

**Console:** 0 errors across the entire detail-page flow (`browser_console_messages level=error` → 0).

---

## Handles Reference

Locator policy is **testid-only** (`.agents/testing.md` § Locator policy). Provenance
verified 2026-08-24 with `cd ../EliteaUI && git fetch origin` first.

| Element | Testid (primary, the ONLY handle) | Provenance | Notes |
|---|---|---|---|
| Form view toggle | `toolkit-form-view-toggle` | **on-main ✓** | state read via `aria-pressed` (`"true"`/`"false"`) — attribute on the testid'd element, compliant |
| Raw Json view toggle | `toolkit-raw-json-view-toggle` | **on-main ✓** | same |
| Raw Json editor content | `toolkit-raw-json-editor-content` | **on-main ✓** | CodeMirror **virtualises** — use `McpFormPage.get_raw_json_full()`, never `get_raw_json()`, for this ~200-line payload |
| Toolkit Name input | `toolkit-form-name-input` | **on-main ✓** | inline on the detail page (`NameDescriptionInput.jsx`) |
| Description input | `toolkit-form-description-input` | **on-main ✓** | inline — do **not** call `expand_configuration_section()` for it |
| Configuration expander | `toolkit-configuration-show-more` | **on-main ✓** | mandatory before ANY `toolkit-field-*` read; mounts late; unmounts once clicked |
| Url field | `toolkit-field-url-input` | runtime-composed (``toolkit-field-${k}-input``) — **present on main ✓**, the literal string is not greppable | schema-driven, `ToolBaseProperty.jsx` |
| Timeout / Cache TTL | `toolkit-field-timeout-input`, `toolkit-field-cache_ttl-input` | same generic emitter, on-main ✓ | |
| Enable Caching / Ssl Verify | `toolkit-field-enable_caching-checkbox-field`, `toolkit-field-ssl_verify-checkbox-field` | same, on-main ✓ | the `-field` suffix is the real `<input type=checkbox>`; the bare `-checkbox` testid is the MUI wrapper (`.checked` is meaningless on it) |
| Detail Save | `toolkit-detail-save-button` | **on-main ✓** | ⚠️ `is_save_button_disabled()` targets the **create-form** Save and times out here — use `detail_save_button` |
| Detail Discard | `toolkit-detail-discard-button` | **on-main ✓** | |
| Discard-confirm modal | `toolkit-detail-discard-confirm-modal` | **on `automation/testids` only** — EliteaAI/EliteaUI@a51c9318, **NOT yet on `main`** (re-verified after `git fetch`, 2026-08-24) | testid sits on the MUI `Dialog` root ⇒ `text_content()` includes title + both button labels → assert with `in`, never `==` |
| Discard-confirm "Discard" button | `toolkit-detail-discard-confirm-button` | **on `automation/testids` only** — same commit, **NOT yet on `main`** | |
| Detail title | `toolkit-detail-title` | **on-main ✓** | placeholder `"Edit MCP"` until data lands — `McpFormPage.wait_for_page_load()` handles it |

**No new testid is needed for this case.** Every element it touches already carries one.

**Promotability:** this case's tests will be **green on localhost, red on any deployed env**
until a human cherry-picks EliteaAI/EliteaUI@a51c9318 (the two discard-confirm testids) to
`main`. Same gap ELITEA-1928 already carries.

---

## Page-object reuse — `automation/pages/mcp_form_page.py`

Everything needed already exists (used by ELITEA-1925/1927/1928/1930):
`navigate_to_create`, `select_remote_mcp_type`, `fill_name`, `fill_description`,
`fill_url`, `save_and_wait_for_created`, `navigate_to_detail`, `wait_for_page_load`,
`expand_configuration_section`, `switch_to_raw_json_view`, `switch_to_form_view`,
`get_raw_json_full`, `fill_raw_json_line`, `scroll_raw_json_to_top`,
`detail_save_button`, `detail_discard_button`, the discard-confirm pair.

Only a **thin** addition may be needed: a `switch_to_form_view()` equivalent if absent —
check before adding, and keep it symmetric with `switch_to_raw_json_view()`.

---

## Automation hints (each one cost a probe this session)

1. **NEVER `.fill()` the raw-JSON editor.** Reconfirmed live this session: it is a
   contenteditable CodeMirror root, so `fill()` replaces the **entire document**
   (observed 30 lines → 1, JSON invalid, Save stays disabled, only a reload recovers).
   Use `McpFormPage.fill_raw_json_line(old_line, new_line)` — click the line, `End`,
   `Shift+Home`, `keyboard.type(...)`.
2. **CodeMirror auto-indents the retyped line** (`  ` → `    ` was observed). The JSON
   stays valid and a view round-trip normalises it, so assert on the **parsed** value
   (`json.loads(get_raw_json_full())["description"]`), never on the raw line text.
3. **`get_raw_json()` vs `get_raw_json_full()`** — the editor virtualises; only ~30 of
   ~200 lines are in the DOM at a time. `get_raw_json_full()` (scroll-and-collect) is
   mandatory here.
4. **`expand_configuration_section()` before every `toolkit-field-*` read**, and again
   after any reload (the section re-collapses).
5. **Discard is modal-gated.** `wait_for(state="visible")` on the modal, assert its text
   with `in`, click the confirm button, then `wait_for(state="detached")` before reading
   the reverted values — the revert lands with the modal's unmount.
6. **The two views swap, they do not co-exist.** After switching, the other view's inputs
   are unmounted — assert with `to_have_count(0)`, not `not_to_be_visible()`.
7. **No success/failure toast anywhere in this flow** — never wait on `toast-message`.
8. **Console listener registration:** the seed goes through `/mcps/create`, which emits
   the known React `key` warning (#656). Register the console listener **after** seeding,
   or filter it, or the assertion fails on scaffolding. The detail page itself was clean
   (0 errors).

---

## Coverage Map

### Axis 1 — every element of the case

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | — | `auth_state` (localhost bypass) | setup | covered |
| Precondition: existing Remote MCP on its detail page | — | seeded disposable MCP (§ Test Data) + `navigate_to_detail` | setup | covered (test-data substitution of the *precondition*, declared) |
| Step 1 — open detail in Form view | Detail page loads in Form view | Step 1 | `form_view_toggle` `aria-pressed=="true"` + raw toggle `"false"` + title == seeded name + Save/Discard disabled | covered |
| Step 2 — note the 7 field values | Current values observed | Step 2 | expand, then read all 7 into locals; assert each is non-None (Url/Timeout/Cache TTL/Enable Caching/Ssl Verify equal the seeded/default values) | covered |
| Step 3 — click Raw Json toggle | JSON editor displayed | Step 3 | editor visible, `aria-pressed` flip, `toolkit-form-name-input` `to_have_count(0)` | covered |
| Step 4 — JSON values match Form values | JSON matches Form | Step 4 | parsed JSON `name`/`description`/`settings.url`/`timeout`/`cache_ttl`/`enable_caching`/`ssl_verify` each `==` the step-2 local | covered |
| Step 5 — modify description in Raw Json | Editor shows updated description | Step 5 | `fill_raw_json_line`, then parsed `description == UPDATED_DESCRIPTION` | covered |
| Step 6 — click Form toggle (unsaved) | Form view displayed | Step 6 | form toggle `aria-pressed=="true"`, description input visible | covered |
| Step 7 — Form shows the updated description | Description field reflects the change | Step 7 | `expect(description_input).to_have_value(UPDATED_DESCRIPTION)` | covered |
| Step 8 — Raw Json again, modification retained | JSON retains the unsaved change | Step 8 | parsed `description == UPDATED_DESCRIPTION` | covered |
| Step 9 — Discard reverts both views | Both views show original values | Step 9 (decomposed: click → modal → confirm → assert raw → switch → assert form) | parsed `description == ORIGINAL_DESCRIPTION` **and** `to_have_value(ORIGINAL_DESCRIPTION)` in Form | covered |
| Expected Final State | Both views show original values, no unsaved modifications | Step 9 tail | the two assertions above **plus** Save and Discard both `to_be_disabled()` | covered |
| Pass criterion "no errors" | — | Axis 2 console assertion | end of test | covered |

### Axis 2 — assertions beyond the case, each grounded

| Extra observable | Why |
|---|---|
| Save **and** Discard disabled on the pristine page (step 1) and disabled again after the revert (step 9) | The product's own "the form is clean" signal — it is what makes "no unsaved modifications" in the Expected Final State testable rather than a claim. Honest here (unlike the create form, #633): the detail page gates both buttons on `isFormDirtyExcluding`. |
| Save/Discard become **enabled** after the raw-JSON edit (step 5) | Proves the edit actually entered the shared model rather than just painting text into CodeMirror — without it, steps 6-8 could pass on a UI that merely echoes the editor buffer. |
| Confirmation-modal visible + its text contains `Are you sure you want to discard changes?` | The modal is an unavoidable part of the live step 9; asserting it pins the behaviour the case text silently assumes away (clarification #1718). |
| Modal **detached** after confirm | Ordering guard — the revert lands with the unmount; reading before it is a guaranteed flake. |
| **No `PUT`/`POST`/`PATCH` fires between step 5 and the end** | The case says "without saving" and "reverts"; a network assertion is the only way to prove the discard was genuinely server-side inert rather than a save-then-restore. Observed empty live. |
| The inactive view's inputs are unmounted (`to_have_count(0)`) after each toggle | Distinguishes a real view swap from a hidden-but-present duplicate form — the latter would make "the other view shows the same value" vacuous. |
| Console errors == 0 on the detail page (listener registered after seeding) | Case Pass criterion is "All steps complete without errors". Observed 0 live. |

---

## Known Defects / clarifications touching this case

- **#1718** (`question` + `case-text-drift`, OPEN) — the Discard confirmation modal is
  missing from the case text. **Third case to hit it** (ELITEA-1928, ELITEA-1971,
  now ELITEA-1948). New occurrence commented on #1718; **not re-filed**. Does not block
  automation — the AFS asserts the live contract.
- **#656** (OPEN) — `/mcps/create` React `key` warning. Only relevant to the seeding step
  (see hint 8). Not on the surface under test.

## Blocked Steps

None.

## Fidelity Declaration

| Substituted | Transit or terminal | Authority |
|---|---|---|
| The case's precondition "an existing Remote MCP" is satisfied by a **UI-seeded disposable MCP** instead of a pre-existing one | **Transit** — the seed only *reaches* the detail page; every observable the case asks for (JSON values, Form values, revert, button states, absence of a `PUT`) is produced by the live product on that page | Same-interface seeding (the real UI create flow, not an API back door); `ToolkitAPI.list_all_toolkits()` returns `[]` here so no existing MCP is discoverable at runtime |

No response is fabricated, no state is injected, no client is replaced, and no
`page.route`/`page.evaluate` is required anywhere in this spec.

## Suggested spec location

`automation/tests/ui/toolkits/test_mcp_form_raw_json_view_sync.py`
→ `TestMcpFormRawJsonViewSync::test_form_raw_json_view_sync_and_discard`
Markers: `ui`, `toolkits`, `mcp`, `p2`, `regression`.
