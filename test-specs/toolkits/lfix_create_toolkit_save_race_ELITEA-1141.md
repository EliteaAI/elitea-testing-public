# Test-repair brief — `test_create_toolkit[github]` / `[jira]` premature save assertion

| field | value |
|---|---|
| **Card** | [#2123](https://github.com/EliteaAI/elitea-testing-public/issues/2123) — `[FIX][ELITEA-1141] assertion-failure: Toolkit creation flow does not navigate away from create page` |
| **TMS case** | ELITEA-1141 (`onetest-ai-tm-Elitea/tests/automated-full-regression-ui/toolkits_UI/ELITEA-1141_github-toolkit-and-credentials.md`) |
| **Kind** | tech-task repair brief (not a fresh TMS-case AFS) |
| **Subject** | `automation/tests/ui/toolkits/test_toolkit_parameterized.py::TestCreateToolkit::test_create_toolkit` (Steps 1–8, lines ~291–360) + `_select_credential_dropdown` (~line 786) + `_fill_toolkit_form_fields` (~line 826) |
| **Status** | `ready-for-automation` |
| **Root cause class** | **test-code issue** — a fixed 3-second budget for an asynchronous save, then an instantaneous URL assert with no wait |
| **Analyst** | qa-engineer, 2026-09-10, live against `http://localhost:5173` (EliteaUI `automation/testids`, DEV backend), project 399 |
| **New testids needed** | **none** — every handle the repair needs is already on `origin/main` (§ Handles Reference) |
| **Reproduces on demand** | **YES** — deterministic control, § Finding 2 |
| **Defect filed** | [#2158](https://github.com/EliteaAI/elitea-testing-public/issues/2158) — product bug found during this analysis (drives R5) |

---

## TL;DR

**The product is not broken and the test has not drifted.** The toolkit was **created
successfully** in both failing CI params — the test asserted while the create request
was still in flight.

Three test-code defects compound:

1. **Step 7 waits on nothing.** `wait_for_load_state("networkidle")` returns in
   ~0.05 s on this app (a persistent `/socket.io/` poll means network silence never
   arrives *and* is never needed — measured), so the step is really just
   `wait_for_timeout(3000)`: a hard-coded 3-second budget for a backend POST.
2. **Step 8 asserts instantly, with no wait.** `assert "/toolkits/create" not in page.url`
   is a point-in-time read. If the POST has not resolved yet, it fails — reporting
   *"the form did not complete navigation"* when the form was mid-save.
3. **The step that could have caught a genuine non-save asserts nothing at all.**
   The API lookup that follows sets `created_id` and never asserts it. If the toolkit
   was never created, `created_id` stays `None`, **the test passes**, and cleanup
   silently skips.

The card's headline — *"This is a product regression in the toolkit creation flow"* —
is **refuted** (§ Ground truth, § Finding 1).

**Consequence beyond the false RED:** because Step 8 raises before the lookup runs,
`created_id` is `None`, so the `finally:` block deletes nothing. Both failing CI params
**leaked a real toolkit** into the CI project. The repair must set the id on the
pessimistic side (§ R2, `.agents/testing.md` § Teardown-guard ordering).

> ⚠️ **The card's auto-generated Instruction 3 — *"Use regular locators (role, text,
> label) instead of data-testid attributes"* — is boilerplate from the intake pipeline
> and is OVERRIDDEN by `.agents/role-overrides.md` + `.agents/testing.md` § Locator
> policy. This project is testid-only. Every handle this repair adds is a testid.**

---

## Ground truth (verified, not inherited)

GHA run [34331579791](https://github.com/EliteaAI/elitea-testing-public/actions/runs/34331579791)
(DEV Stable #114), job `dev-stable - toolkits`, 2026-09-09. Allure step durations, read
out of the downloaded `*-result.json`:

| step | `[github]` | `[jira]` | `[confluence]` (PASSED) |
|---|---|---|---|
| 1 — Navigate to toolkit creation page | 18 953 ms | 13 692 ms | 25 974 ms |
| 2 — Click toolkit type card | 1 095 ms | 1 094 ms | 1 118 ms |
| 3 — Fill Toolkit Name | 9 985 ms | 6 260 ms | 9 797 ms |
| 4 — Fill Description | 2 654 ms | 1 860 ms | 2 963 ms |
| 5 — Select credential from dropdown | **307 ms** | **324 ms** | **308 ms** |
| 6 — Fill type-specific fields | 1 843 ms | 0 ms | 1 010 ms |
| 7 — Click Save button | **3 074 ms** | **3 060 ms** | **3 071 ms** |
| 8 — Verify navigation away from create form | **failed, 3 ms** | **failed, 0 ms** | passed, 1 417 ms |
| total | 37 915 ms | 26 291 ms | 45 660 ms |

Two rows decide the whole investigation:

- **Step 7 is 3.06–3.07 s in ALL THREE params, pass and fail alike.** That is
  `wait_for_timeout(3000)` plus a `networkidle` that returned in single-digit
  milliseconds. The step contains **no** signal from the save at all.
- **Step 8 fails in 0–3 ms.** The failing assert is the step's *first* statement and it
  never waits. `[confluence]`'s 1 417 ms is the `list_toolkits()` HTTP call *after* the
  same instantaneous assert happened to pass.

So the only difference between the passing param and the two failing ones is **whether
the create POST resolved inside a fixed 3-second window**. Nothing else differs.

Failure message, both params:

```
AssertionError: assert '/toolkits/create' not in 'https://dev.elitea.ai/app/toolkits/create/github'
AssertionError: assert '/toolkits/create' not in 'https://dev.elitea.ai/app/toolkits/create/jira'
```

### The failure screenshots settle the mechanism

Both allure failure screenshots
(`/tmp/ar2123/4cb73d93-…png` = github, `/tmp/ar2123/d56c5007-…png` = jira) show a
fully and correctly filled form — name, description, the fixture's credential selected
(`GitHub 1788944489` / `Jira 1788944533`), Repository `EliteaAI/elitea-testing`,
branches — **no error toast, no field error**, still on the create page, and:

> **Save is greyed AND Cancel is greyed.**

That pair is the tell, and it is decidable from source:

```jsx
// src/pages/Toolkits/CreateToolkitToolTabBar.jsx
const shouldDisableSave = useMemo(() => isLoading || !formik?.dirty, [isLoading, formik?.dirty]);
<MuiButton data-testid="toolkit-form-save-button" disabled={shouldDisableSave} …/>
<Button.DiscardButton title="Cancel" disabled={isLoading} dataTestId="toolkit-form-cancel-button" …/>
```

Cancel is disabled by `isLoading` **only**. Verified live on all three states
(§ Finding 1, probe C):

| live state | Save | Cancel |
|---|---|---|
| form just rendered, nothing dirty | **DISABLED** | enabled |
| dirty but invalid (Name + required Repository empty) | enabled | enabled |
| Save clicked on an invalid form — no POST fires | enabled | enabled |
| **create POST in flight** | **DISABLED** | **DISABLED** |

⇒ **Both greyed can only mean `isLoading === true`: the create mutation was pending.**
It was not a disabled-button no-op (that would leave Cancel enabled), and it was not a
blocked validation (that leaves both enabled and fires nothing).

Corroboration: run 34331579791 is the same run that produced the gateway-500 sibling
cards #2074/#2076 — 8 of 10 jobs failed. DEV was degraded; a >3 s create POST is exactly
what that predicts. Step 1's own 13.7–26.0 s (vs ~2 s locally) says the same.

---

## Finding 1 — the product is correct (live, localhost → DEV backend)

Driven with Playwright against `http://localhost:5173`, project 399, with credentials
created through the same factories the `managed_credential` fixture uses.

| probe | result |
|---|---|
| github: type card → fill name/description/repository → **real** Save click | `POST /api/v2/elitea_core/tools/prompt_lib/399` → **201**, navigates to `/toolkits/all/3625`, then `/toolkits/all/3625?name=AFS2123+github+…` |
| jira: same (jira has no required schema field) | **201**, `/toolkits/all/3624?name=…` |
| github, third run, capturing the response body | **201**, body carries top-level `id`, `name`, `settings`, `type`, … ; `wait_for_url("**/toolkits/all/*")` returned in **0.00 s** |
| github via Playwright MCP, manual walk | `/toolkits/all/3619` → `/toolkits/all/3619?name=…` |

Console: no errors on the save path. Network: no 4xx/5xx on the create path (there is an
unrelated `GET /elitea_core/toolkit_validator/prompt_lib/399/{id}` that returned 400 on
one localhost run and 200 on another — it fires **after** navigation, is not the case's
observable, and is out of scope here).

### The post-save destination — OBSERVED, four times

```
POST /api/v2/elitea_core/tools/prompt_lib/{project_id}   -> 201 Created  (body.id = new toolkit id)
then the app navigates to:   /toolkits/all/{id}
and shortly after appends:   /toolkits/all/{id}?name=<url-encoded toolkit name>
```

Confirmed in source — `CreateToolkitToolTabBar.jsx` navigates to
`RouteDefinitions.ToolkitsWithTab.replace(':tab','all') + '/' + data.data.id`.

It is the new toolkit's **detail page**, *not* the toolkits list. Any regex must tolerate
the trailing query string:

```python
re.compile(r"/toolkits/all/\d+(\?.*)?$")
```

### What actually gates the Save button — measured, not assumed

`shouldDisableSave = isLoading || !formik.dirty`. **Validity is not part of it** — there
is a `//@todo` in the source saying exactly that. Measured live on the github form:

```
A) form just rendered, nothing typed        save=DISABLED  cancel=enabled
B) credential AUTO-SELECTED ~0.8-1.0 s later,
   Name still ""  and required Repository still ""   save=enabled   cancel=enabled
C) click Save in state B  ->  NO POST, stays on /toolkits/create/github,
                              no visible error, save=enabled cancel=enabled
D) fill Name + Repository, click Save  ->  POST 201, /toolkits/all/3627
```

Two consequences the repair must honour:

- **`expect(save_button).to_be_enabled()` is NOT a validity oracle on this form** (it is
  on the credential form — that is why #1897's R2 does not transfer). Save is enabled the
  moment the credential auto-selects, with every required field empty. Asserting it is
  harmless and worth keeping as a precondition, but it proves nothing about the save.
- **The only honest oracle is the create request and the resulting navigation** — hence
  R1.

### Step 5 has never opened the dropdown

`_select_credential_dropdown` early-returns when the credential name is already visible,
via `page.wait_for_timeout(300)`. Step 5's CI durations — **307 / 308 / 324 ms across all
three params** — are that sleep. The app **auto-selects** the newest credential
(`configurations?sort_by=created_at&sort_order=desc` → `savedCredentialsMenuData[0]`,
which is the fixture's), so the dropdown is never opened and the credential is never
asserted. Confirmed live: the select showed `AFS2123 github` ~0.8 s after the form
rendered, with no interaction.

---

## Finding 2 — the CI signature, reproduced deterministically

Control (`/tmp/afs2123/control.py`). **Timing control only** — the REAL create POST is
issued and its REAL 201 response is delivered 8 s late. Nothing is fabricated
(`.agents/testing.md` § Fidelity policy: *"Delaying a real response for timing control is
NOT substitution"*). Steps 7 and 8 are then executed exactly as the test does them today:

```
before click: {'save': 'enabled', 'cancel': 'enabled'}
  networkidle returned after 0.05s
  after wait_for_timeout(3000): 8.92s  buttons={'save': 'DISABLED', 'cancel': 'DISABLED'}
>>> URL at Step 8: http://localhost:5173/toolkits/create/github
>>> `assert '/toolkits/create' not in page.url` -> FAIL
>>> POST statuses (real, delayed): [201]   final URL: http://localhost:5173/toolkits/all/3626?name=AutoTest+github+Toolkit+…
```

Every element of the CI failure, reproduced: `networkidle` returning in 50 ms, **both
buttons greyed**, the same URL, the same assertion failing — **while the toolkit was
created successfully (201) and the app navigated moments later.** Screenshot:
`/tmp/afs2123/control-github-step8.png`.

This is the proof the repair works: with R1 in place the same run is GREEN, and a run
where the POST genuinely never fires is RED at the click, naming the real problem.

---

## Finding 3 — the vacuous siblings (the card asked; here they are)

**Yes, there is a second vacuous check, and it is worse than the first.**

### 3a. The API lookup asserts nothing — a hidden green

```python
toolkits = toolkit_api.list_toolkits()
rows = toolkits if isinstance(toolkits, list) else toolkits.get("rows", [])
for t in rows:
    if t.get("name") == tk_name:
        created_id = t["id"]
        break
# ... and that is the end of Step 8. No assert.
```

If the toolkit was **not** created, `created_id` stays `None`, no assertion fires, the
test **passes**, and the `finally:` block deletes nothing. The whole "was it actually
created?" question is unasserted. The sibling `test_create_credential` has
`assert created_id is not None` (line ~272) — this is a straight omission, not a
deliberate difference.

Combined with 3b below, **the current test passes on any run that navigates away from the
create form for any reason.**

### 3b. `list_toolkits()` returns a single page

`ToolkitAPI.list_toolkits()` — *"Return toolkit list (single page)"*. `list_all_toolkits()`
is the paginating variant and already exists. On a project with more toolkits than one
page, a freshly-created toolkit can be absent from that page, so even a correct save
yields `created_id is None` → silent skip of cleanup → **leak**. The credential sibling
already uses `list_all_credentials()`.

### 3c. Step 8's URL guard is weak in the other direction too

`assert "/toolkits/create" not in page.url` passes on **any** URL that is not the create
form. It cannot distinguish "toolkit created, landed on its detail page" from "navigated
somewhere else". The correct positive statement is the observed destination:
`/toolkits/all/{id}`.

### 3d. The credential is never asserted

The case's own expected result is *"Toolkit linked to credential"*. The test selects
nothing (§ Finding 1) and asserts nothing about which credential the form holds. If
auto-select picks a different credential, the toolkit is created with the wrong one and
the test still passes.

---

## Finding 4 — product defect found during this analysis → #2158 (drives R5)

Re-clicking the **already-selected** credential option in the toolkit form's
"&lt;Type&gt; Configuration" select toggles it OFF in form state
(`CredentialsSelect.jsx` `onSelectItem` → `onSelectConfiguration(null)` — deliberate),
but the select **keeps displaying the credential** and the option keeps
`aria-selected="true"`, because `selectedOption` falls back to
`savedCredentialsMenuData[0]` when the value is blank, while `hasAutoSelectedRef.current`
is already `true` so it is never re-applied to formik.

Measured, 2/2 runs:

```
after filling name+repo             value='AFS2123 github'  save=enabled  cancel=enabled
clicking the already-selected option
after re-clicking selected option   value='AFS2123 github'  save=enabled  cancel=enabled
visible errors: []
click Save -> POST status: None ; url still /toolkits/create/github
```

Filed as **#2158** (Major). **Direct consequence for this repair:** a naive "always open
the dropdown and click the credential" implementation would put the form into this exact
dead end and produce a *new* false RED — and, because the select still shows the
credential name, a UI-text assertion would not catch it. R5 forbids it.

---

## Finding 5 — SECOND leak, found at implementation time: the name is truncated at 32

**Added by the implementer, 2026-09-10 (#2123). This one leaks on PASSING runs too, so
it is wider than the failure the card was opened for.**

The repair's new Step-3 assertion — `expect(name_input).to_have_value(tk_name)` — failed
on the very first `[github]` run:

```
E   AssertionError: Locator expected to have Value 'AutoTest GitHub Toolkit 1789003922'
E   Actual value: AutoTest GitHub Toolkit 17890039
E     locator resolved to <input … maxlength="32" data-testid="toolkit-form-name-input" …/>
```

`Toolkit Name` carries `inputProps={{ maxLength: MAX_NAME_LENGTH }}`
(`NameDescriptionInput.jsx`) and `MAX_NAME_LENGTH = 32`
(`EliteaUI src/common/constants.js:66`). The browser drops the overflow **silently** —
no error, no toast, no field error.

`tk_name` was `f"AutoTest {display} Toolkit {ts}"`, i.e. **34 / 34 / 37 / 38 characters**
for github / gitlab / bitbucket / confluence (jira is exactly 32 and fit). So for those
params the toolkit was stored under a truncated name, the old Step-8 lookup searched for
the **full** name, never matched, left `created_id is None` — and, because that lookup
asserted nothing (§ Finding 3a), the test **reported PASS while leaking a toolkit**.
Confirmed against control run A below: the leaked object's stored name was
`AutoTest GitHub Toolkit 17890038` — 32 chars, visibly truncated.

**Repair (in scope — the test cannot go green without it):** the generated name is now
`f"AT {cfg.display_name} {_ts()}"` (24 chars at worst), guarded by
`TOOLKIT_NAME_MAX_LEN = 32` and an explicit precondition assert that names the cap. The
Step-3 value assertion is what keeps it honest: any future name that overflows fails
loudly at Step 3 instead of leaking quietly. Nothing about the case's observable is
weakened — this is test data being made able to survive a real product constraint.

Recorded for the next spec on this surface in `test-specs/toolkits/_surface.md`
§ "Name field is capped at 32 characters".

---

## Implementer control results (2026-09-10, localhost, real pytest invocations)

Executed through a throwaway pytest plugin (`/tmp/impl2123/ctrl_plugin.py`, never
committed) that routes only the create POST — so the REAL spec code ran in all three:

| control | code | create POST | outcome |
|---|---|---|---|
| **A** | **pre-repair** (`automation/base`) | real, **201**, response held 8 s | **FAIL at Step 8** — `assert '/toolkits/create' not in 'http://localhost:5173/toolkits/create/github'`, and toolkit **3631 leaked** (deleted by hand afterwards) |
| **B** | repaired | real, **201**, response held 8 s | **PASS**, 25.6 s — the exact condition that broke A |
| **C** | repaired | **aborted** (genuine non-save) | **FAIL at Step 7** — `AssertionError: No create request (POST .../elitea_core/tools/prompt_lib/...) was observed within 30000 ms of clicking Save — the toolkit was not created.` |

A is the CI signature reproduced against the real spec; B is the proof the repair fixes
it; C is the proof the repair did not buy green by going blind.

**Implementation note on C:** `expect_response`'s native timeout reads only
`Timeout 30000ms exceeded while waiting for event "response"`, which names neither the
request nor the step's meaning. It is re-raised as an `AssertionError` naming the missing
POST and the current URL. Side effects, both benign and deliberate: the allure status
becomes `failed` rather than `broken` (nothing keys on it — `conftest.py` keys on
`report.outcome`), and the failure leaves `pytest.ini`'s `--only-rerun "TimeoutError"`
bucket, which is correct — a save that never fires is deterministic, not a flake.

---

## Correlation with ELITEA-1141

| case step | case expected result | test today | disposition |
|---|---|---|---|
| "Navigate to Toolkits, create GitHub toolkit" | **"Toolkit created with credential selector"** | URL substring guard + an unasserted API lookup | **restore** — R1 + R2 |
| "Select credential, configure toolkit" | **"Toolkit linked to credential"** | never selected (Step 5 is a 300 ms sleep), never asserted | **restore** — R5 |
| "Navigate to Credentials, create GitHub credential" | credential created, visible in list | `TestCreateCredential` (sibling, repaired under #1897) | out of scope here |
| "Click Test Settings" → connection test passes | | `TestToolkitTestSettings` (sibling) | out of scope here |

Restoring rows 1 and 2 is **not new scope** — the case already asks for both, and both
are silently unasserted today. Nothing is deleted, weakened, lowered, or made conditional.

**Case-metadata note (report only, do not act here):** ELITEA-1141's `automation_test_id`
list still names four `tests.ui.toolkits.test_github_toolkit.*` refs alongside the
parameterized one. That file exists, so nothing is broken — but the overlap between the
GitHub-specific file and the `[github]` param of the parameterized file is worth an
operator decision. → clarification candidate, not this card's work.

---

## The repair

**Vehicle: route Steps 1–7 through the existing `ToolkitCreationPage`**
(`automation/pages/toolkit_creation_page.py`, on `automation/base`, testid-only, already
used by `test_toolkit_creation_create_bucket_verify_list_files.py:494` and two chat
specs). It is a pure *how-it-reaches-and-identifies* change that fixes the raw handles,
the fixed sleeps, and the save wait in one move.

> ⚠️ **Do NOT deep-link the form.** Unlike the credential form (#1897 R1's
> `navigate_to_type`), `GET /toolkits/create/{type}` renders the **type picker**, not the
> form — verified live: the header reads "New Github Toolkit" while the body is "Choose
> the toolkit type". The type card must be clicked. `ToolkitCreationPage.select_toolkit_type(
> search_term, type_key)` does exactly that, by testid.

### R1 — Step 7/8: wait for the SAVE, not for a sleep *(blocker — this is the card)*

Delete `save_btn.evaluate(...)`, `wait_for_load_state("networkidle", …)` and
`wait_for_timeout(3000)`. Replace with a real click plus a real wait on the real
completion signals:

```python
with allure.step("Step 7 — Click Save and wait for the toolkit to be created"):
    # `networkidle` is NOT a save signal on this app — a persistent /socket.io/ poll
    # means it returned in ~0.05 s in every measured run (#2123, #1847). The former
    # `wait_for_timeout(3000)` was therefore a hard 3-second budget for a backend POST;
    # on a loaded DEV it expires and Step 8 reports "did not navigate" for a save that
    # succeeded moments later (CI run 34331579791).
    expect(toolkit_form.save_button).to_be_enabled(timeout=UI_ELEMENT_TIMEOUT)
    with page.expect_response(
        lambda r: "/elitea_core/tools/prompt_lib/" in r.url and r.request.method == "POST",
        timeout=TOOLKIT_SAVE_TIMEOUT,          # 30_000 — DEV is slower than localhost
    ) as create_resp:
        toolkit_form.save_button.click()       # a REAL click, never evaluate("el => el.click()")
    response = create_resp.value
    assert response.status == 201, (
        f"Toolkit create POST returned {response.status}, expected 201 — "
        f"the toolkit was not created"
    )
    created_id = response.json()["id"]         # see R2 — set BEFORE anything else can fail

with allure.step("Step 8 — Verify navigation to the new toolkit's detail page"):
    # Observed destination, four live runs: /toolkits/all/{id}, then the app appends
    # ?name=<toolkit name>. The former guard (`"/toolkits/create" not in page.url`)
    # only said "not on the create form" — it never stated where the app actually goes.
    page.wait_for_url(
        re.compile(rf"/toolkits/all/{created_id}(\?.*)?$"), timeout=NAVIGATION_TIMEOUT
    )
```

`ToolkitCreationPage.save_creation(timeout=…)` is the alternative vehicle — it clicks
Save, waits `**/toolkits/all/*` and returns the parsed id. It is acceptable **only** if
the id is still captured on the pessimistic side (R2); the `expect_response` form above
is preferred precisely because it captures the id from the response, which cannot be
lost to a navigation timeout.

### R2 — teardown guard: set `created_id` from the create response, not from a later lookup *(blocker)*

`.agents/testing.md` § Teardown-guard ordering: *"a teardown guard flag is set IMMEDIATELY
BEFORE / as soon as the mutation is known to have happened"*. Today `created_id` is set
only at the very end of Step 8, **after** an assert that can raise — which is exactly why
both failing CI params leaked a toolkit. R1 sets it from the 201 body, before the
navigation wait. Nothing between the POST and the assignment can raise.

### R3 — Step 8: assert the API oracle, and paginate *(blocker)*

The case's observable is that the toolkit exists. Make it an assertion, and use the
paginating client:

```python
with allure.step("Step 9 — Verify the toolkit exists via API"):
    rows = toolkit_api.list_all_toolkits()      # NOT list_toolkits() — that is one page
    match = next((t for t in rows if t.get("name") == tk_name), None)
    assert match is not None, (
        f"Toolkit '{tk_name}' not found via API among {len(rows)} toolkits"
    )
    assert match["id"] == created_id
```

Renumber the allure steps consistently; keep one `allure.step` per action.

### R4 — Steps 1–6 through `ToolkitCreationPage`, testid-only, no fixed sleeps *(blocker)*

Every locator in Steps 1–6 today is a raw handle plus a `wait_for_timeout`:
`page.get_by_text(cfg.ui_card_text).first`, `page.get_by_role("textbox", name="Toolkit Name")`,
`…name="Description"`, `page.locator('[role="combobox"]').first`, four sleeps totalling
2.6 s. These are tracked tech debt (#25/#42), **not precedent** — anything this repair
touches becomes testid-only:

```python
toolkit_form = ToolkitCreationPage(page)
toolkit_form.navigate("/toolkits/create")                       # or the existing page-object nav
toolkit_form.select_toolkit_type(cfg.display_name, cfg.toolkit_type, timeout=NAVIGATION_TIMEOUT)
toolkit_form.fill_name(tk_name)
expect(toolkit_form.name_input).to_have_value(tk_name, timeout=UI_ELEMENT_TIMEOUT)
toolkit_form.fill_description(f"Test {cfg.display_name} toolkit for automation")
```

`ToolkitCreationPage` has `name_input`, `save_button`, `cancel_button`,
`TOOLKIT_TYPE_CARD`, `TOOLKIT_FIELD_INPUT`, `fill_name`, `fill_field`,
`select_toolkit_type`, `save_creation`. It does **not** yet have a description field or a
credential select — add both as class-level `LocatorDescriptor` / UPPER_CASE template
constants (§ Handles Reference; both testids already exist on `main`):

```python
description_input = LocatorDescriptor(testid="toolkit-form-description-input", description="…")
CREDENTIAL_SELECT = '[data-testid="toolkit-credential-select-{}"]'
CREDENTIAL_SELECT_COMBOBOX = '[data-testid="toolkit-credential-select-{}-combobox"]'
CREDENTIAL_OPTION_BY_TITLE = '[data-testid^="select-option-"][data-testid*="\\"elitea_title\\":\\"{}\\""]'
```

Note `cfg.toolkit_type` is the schema key the card testid uses (`github`, `jira`,
`confluence`) — `cfg.ui_card_text` is the display text and is no longer needed for
locating. Removing the `.first`-on-text card click also removes the ambiguity risk
across the 71 cards the picker renders (measured live).

### R5 — Step 5: verify the credential, and NEVER re-click a selected option *(blocker)*

The form auto-selects, so the honest shape is *assert what is selected, and only open the
dropdown if it is the wrong one*:

```python
with allure.step("Step 5 — Verify the fixture's credential is selected"):
    # The form AUTO-SELECTS the newest saved credential of this type (~0.8-1.0 s after
    # the form renders) — the fixture's, since the API sorts created_at desc. Step 5 has
    # therefore never opened this dropdown in CI (307-324 ms = the old wait_for_timeout(300)).
    # KNOWN DEFECT #2158: clicking the option that is ALREADY selected toggles the
    # credential OFF in form state while the select keeps displaying it and shows no
    # error — Save then fires no request at all. So: assert first, and only interact when
    # the wrong credential is selected.
    expect(toolkit_form.credential_select(cfg.toolkit_type)).to_contain_text(
        cred_name, timeout=UI_ELEMENT_TIMEOUT
    )
```

If the implementer finds the assertion failing because auto-select picked a different
credential, the fallback is to open the combobox and click
`CREDENTIAL_OPTION_BY_TITLE.format(managed_credential["elitea_title"])` — the saved
option's testid is
`select-option-{"kind":"saved","elitea_title":"<elitea_title>","private":true}` (captured
live). Use the prefix+contains form above rather than the full JSON: it is a literal
`data-testid` selector (policy-compliant), and it does not depend on key order or on the
`private` flag. **Guard it with the currently-selected check so #2158 cannot fire.**

> **IMPLEMENTED — assertion only; the dropdown fallback was deliberately NOT wired
> (implementer, #2123, declared).** The assertion never failed: auto-select picked the
> fixture's credential in 3/3 Phase-2 probe runs and in every gate run across all three
> params, which is what the mechanism predicts (the backend sorts `created_at desc` and
> `managed_credential` creates ours milliseconds before the form opens). Wiring an
> unexercised recovery path here would have cost the two extra handles
> (`CREDENTIAL_SELECT_COMBOBOX`, `CREDENTIAL_OPTION_BY_TITLE`) as dead references —
> which canon ruling #511 explicitly rejects, since a testid wired into a page object
> but never called on the executed path is not "referenced" — and its only exercise
> would be the one interaction defect **#2158** makes dangerous. If a future run does
> see the wrong credential auto-selected, that red is truthful (the case's "Toolkit
> linked to credential" really is violated) and the fallback is the AFS-sanctioned fix.

### R6 — `_fill_toolkit_form_fields`: key by schema key, assert what landed *(blocker)*

Today:

```python
field = page.get_by_role("textbox", name=field_label)
if field.is_visible():            # not visible -> SILENTLY SKIPPED
    if not existing:              # already filled -> silently skipped
        field.click(); field.type(value)   # deprecated .type(), no assertion
```

A required field left empty produces exactly the state I reproduced in probe C: Save
enabled, click does nothing, no POST, no error, Step 8 fails with the same message as
this card. Mirror #1897's R4:

- Re-key `ToolkitConfig.ui_form_fields` from **UI label** to **schema key** (captured
  live: github → `repository` (required), `active_branch`/`base_branch` (pre-filled
  `main`); jira → none; confluence → `space_key` (required), plus `limit`, `labels`,
  `max_pages`, `number_of_retries`, `min_retry_seconds`, `max_retry_seconds`), and fill
  via `toolkit_form.fill_field(key, value)` (testid `toolkit-field-{key}-input`).
- `expect(toolkit_form.get_field_locator(key)).to_have_value(value)` after each fill.
- An empty config value behind a **required** field is a `pytest.skip` naming the
  variable (a config gap, not a product verdict) — never a silent fall-through into a
  save that cannot succeed. `settings.gitlab_repository` is currently `''`; `[gitlab]` is
  skipped for other reasons, so this is latent, not live.

### R7 — keep `to_be_enabled()`, but document that it is not a validity oracle *(non-blocking)*

One comment line, so nobody later "strengthens" it into a validity check:

```python
# `shouldDisableSave = isLoading || !formik.dirty` (CreateToolkitToolTabBar.jsx) — Save
# is enabled the moment the credential auto-selects, with every required field empty
# (measured, #2123). This asserts the button is clickable, NOT that the form is valid.
# The real oracle is the 201 on the create POST below.
```

### R8 — `TOOLKIT_SAVE_TIMEOUT` as a named constant *(non-blocking)*

Add `TOOLKIT_SAVE_TIMEOUT = 30_000` beside the existing constants. This is **not** a
"longer timeout to make a red go green": today there is no wait at all, and the failure
is asserted *before* any budget expires. R1 introduces the first real wait; 30 s is the
budget for it, in line with `NAVIGATION_TIMEOUT`/`FORM_SAVE_TIMEOUT` and the observed
DEV latency. If a save genuinely exceeds 30 s, the test goes RED at the click with
`expect_response` naming the missing POST — which is the correct, truthful failure.

### R9 — assert the credential link at the API level *(recommended, not blocking)*

The case's second expected result is *"Toolkit linked to credential"*. R5 asserts it at
the UI level before saving; an API-level assertion on the created toolkit's settings
would close it after saving. The create-response body carries a `settings` object — the
exact key holding the credential (`configuration.elitea_title` on the github section, per
the form's schema) **must be confirmed against a live response at implementation time**;
I observed the key's presence but did not dump its shape. Do not guess it. If the shape
turns out awkward, leave R5 as the coverage and record it here.

> **IMPLEMENTED — key confirmed live 2026-09-10 (implementer, #2123), not guessed.**
> Dumped off the real 201 body for github, jira AND confluence:
> `settings["{toolkit_type}_configuration"]["elitea_title"]`, e.g.
> `{"github_configuration": {"private": true, "elitea_title": "github_1789003516095"}, …}`.
> The spec asserts it equals `managed_credential["elitea_title"]`. Shape also recorded in
> `test-specs/toolkits/_surface.md`.

### What must NOT change

- **The case's observable — "a toolkit was created" — must stay an assertion that can
  fail.** R3 strengthens it; it must never become conditional, a substring match, or a
  retry that could match some other toolkit.
- The `managed_credential` fixture, the `toolkit_config` fixture and its skip semantics,
  the parameterisation over `_all_toolkit_ids()`.
- The `finally:` cleanup, the `@allure.issue` case link, the `p0` marker, and the
  `with allure.step("Step N — …")` structure.
- **No `pytest.skip`, `xfail`, `expect.soft`, or weakened comparison for the failure this
  card is about.** There is no product defect behind the CI red — a genuine non-save must
  go RED at Step 7 with the missing POST named. (#2158 is a *different* defect, found
  here, and is avoided by R5 rather than masked.)
- Do **not** delete `TestCreateCredential`, `TestToolkitTestSettings` or
  `TestChatWithToolkit`, and do not touch `test_toolkit_indicators_for_credentials` — the
  other reds in that job belong to other cards.

---

## Handles Reference (testid-only)

Provenance verified 2026-09-10 with `cd ../EliteaUI && git fetch origin` **immediately
before** the check, two-stage grep per `.agents/workflow.md` § Closure record:

```
toolkit-form-name-input            main:YES  testids:YES
toolkit-form-description-input     main:YES  testids:YES
toolkit-form-save-button           main:YES  testids:YES
toolkit-form-cancel-button         main:YES  testids:YES
toolkit-type-card-                 main:YES  testids:YES
toolkit-credential-select-         main:YES  testids:YES
toolkit-field-                     main:YES  testids:YES
```

| element | handle | page-object field | PROVENANCE |
|---|---|---|---|
| Toolkit type card | `toolkit-type-card-{type}` | `ToolkitCreationPage.TOOLKIT_TYPE_CARD` | on-main ✓ (`CategoryItemCard.jsx:14`) · live ✓ (71 cards enumerated) |
| Type-picker search | `toolkit-wizard-type-search-input` | `type_search_input` | on-main ✓ · live ✓ |
| Toolkit Name | `toolkit-form-name-input` | `name_input` | on-main ✓ (`NameDescriptionInput.jsx:78`) · live ✓ |
| Description | `toolkit-form-description-input` | **add** `description_input` | on-main ✓ (`NameDescriptionInput.jsx:113`) · live ✓ |
| Credential select (display) | `toolkit-credential-select-{type}` | **add** `CREDENTIAL_SELECT` template | on-main ✓ (`CredentialsSelect.jsx`, `Select.SingleSelect data-testid`) · live ✓ (`…-github`, `…-jira`, `…-confluence`, and a second `…-pgvector` on the same form) |
| Credential select (combobox) | `toolkit-credential-select-{type}-combobox` | **add** `CREDENTIAL_SELECT_COMBOBOX` | on-main ✓ (shared Select suffix) · live ✓ |
| Saved credential option | `select-option-{"kind":"saved","elitea_title":"…","private":…}` | **add** `CREDENTIAL_OPTION_BY_TITLE` (prefix + `*=` on `elitea_title`) | on-main ✓ (shared Select option) · live ✓ — ⚠ the value contains `"` so a double-quoted CSS attribute selector is a `SyntaxError`; use single quotes |
| Schema-driven field | `toolkit-field-{key}-input` | `TOOLKIT_FIELD_INPUT` | on-main ✓ (`ToolBaseProperty.jsx:296/331/605`) · live ✓ (`repository`, `active_branch`, `base_branch`, `space_key`, `limit`, `labels`, `max_pages`, `number_of_retries`, `min_retry_seconds`, `max_retry_seconds`) |
| Save | `toolkit-form-save-button` | `save_button` | **on-main ✓ (literal, `CreateToolkitToolTabBar.jsx:189`)** |
| Cancel | `toolkit-form-cancel-button` | `cancel_button` | **on-main ✓ (literal, `CreateToolkitToolTabBar.jsx`)** |
| Project selector | `project-selector-trigger` / `-combobox` | (analysis only) | on-main ✓ · live ✓ |

> **Grep caveat, so nobody re-derives it as a false negative.** `toolkit-field-*`,
> `toolkit-type-card-*`, `toolkit-credential-select-*` and `select-option-*` are
> **runtime-composed** template literals — the documented stage-1 blind spot
> (`.agents/workflow.md`: *"stage 1 cannot see these at all"*). The rows above are
> verified by locating the generator on `origin/main` **and** by reading the rendered ids
> out of the live DOM. Do not read a prefix grep as "needs adding".

**New testids required: none.** Nothing in this repair is gated on a human cherry-pick.

---

## Fidelity Declaration

| what | transit or terminal | authority |
|---|---|---|
| `page.route` + `route.fetch()` delaying the REAL create POST response by 8 s, in the **analysis control only** (`/tmp/afs2123/control.py`) | neither — **timing control** on a real response; every asserted value came from the system (real 201, real body, real navigation) | `.agents/testing.md` § Fidelity policy: *"Delaying a real response via `page.route()` … leaves the product as the producer of every asserted value"* |
| credentials created through `CredentialAPI` for the live probes | transit — the observable (toolkit creation) is produced by the UI + backend | mirrors the spec's own `managed_credential` fixture, which the case's preconditions already assume |

**The repair itself specs ZERO substitutions.** No `route.fulfill`, no `page.evaluate`
for state, no stubbed client. Every value R1–R9 assert on — the 201, the response `id`,
the URL, the API list, the credential label — is produced by the system.

---

## Coverage Map

### Axis 1 — case elements

| case element | expected result | covered by | asserted where | disposition |
|---|---|---|---|---|
| Preconditions — valid GitHub token | credential available | `toolkit_config` + `managed_credential` fixtures | fixtures | covered (unchanged) |
| "Navigate to Toolkits, create GitHub toolkit" | **"Toolkit created with credential selector"** | R1 (real click + 201) + R4 (testid navigation) | Steps 1–7 | **restored** — today a fixed sleep and an instant URL read |
| — the toolkit actually exists | found in the list | **R3** (`list_all_toolkits` + `assert`) | Step 9 | **restored** — today an unasserted lookup on one page (hidden green) |
| "Select credential, configure toolkit" | **"Toolkit linked to credential"** | **R5** (assert the selected credential) + R6 (type-specific fields asserted) + R9 (optional API link) | Steps 5–6 | **restored** — today a 300 ms sleep and no assertion |
| "Click Test Settings" → connection passes | | `TestToolkitTestSettings` (sibling class) | — | out of scope for this test |
| "Navigate to Credentials, create GitHub credential" | | `TestCreateCredential` (sibling, repaired under #1897) | — | out of scope for this test |
| Cleanup | toolkit removed | `finally:` + **R2** (id captured from the 201) | teardown | **restored** — today the id is set after an assert that can raise, so failures leak |
| Cleanup (2nd path) | toolkit removed | **Finding 5** — name kept inside the product's 32-char cap, asserted at Step 3 | Step 3 + teardown | **restored** — today the name is silently truncated, so the lookup never matches and github / gitlab / bitbucket / confluence leak on **passing** runs too |

### Axis 2 — asserted beyond the case

| observable | reason |
|---|---|
| the create POST returns **201** (R1) | the case's "toolkit created" needs a producer-side oracle; without it a stall is indistinguishable from a failure — this is the whole of #2123 |
| each typed field holds its value (R6) | a silently-skipped required field puts the form into the "Save enabled, click does nothing" state I reproduced live; without this the failure surfaces two steps later with the wrong subsystem named |
| the destination URL is `/toolkits/all/{created_id}` (R1) | states where the app actually goes instead of only where it is not; the id ties the navigation to *this* test's toolkit |

---

## Blocked Steps

None. The repair needs no new testid, no new fixture, no product change, and nothing from
a human.

---

## Evidence

Local analysis artifacts (paths only — none of these is issue evidence; the one
screenshot that reached the tracker was uploaded to the `evidence` release per
`.agents/role-overrides.md`):

| file | shows |
|---|---|
| `/tmp/ar2123/4cb73d93-…-attachment.png` | CI `[github]` failure — filled form, **Save AND Cancel both greyed** |
| `/tmp/ar2123/d56c5007-…-attachment.png` | CI `[jira]` failure — identical signature |
| **`/tmp/afs2123/control-github-step8.png`** | **control — the reproduced CI state at Step 8, with a real 201 arriving afterwards** |
| `/tmp/afs2123/invalid-save.png` | Save clicked on an invalid form: no POST, no error, both buttons enabled |
| `/tmp/afs2123/ELITEA-1141-step05-reclick-credential-silent-dead-end.png` | #2158 — re-clicked credential, select still shows it, no error, no request (uploaded to the `evidence` release) |

Throwaway scripts (read config via `config.settings`, never print secrets):
`/tmp/afs2123/probe.py`, `probe2.py`, `probe3.py`, `probe4.py`, `probe5.py`, `probe6.py`,
`control.py`, `mkcred.py`. All probe-created toolkits (3619–3627) and credentials
(3628–3630) were deleted at the end of the session — verified.

---

## Gate expectation for the implementer

The failure **does** reproduce on demand (§ Finding 2), so unlike #1897 the repair is
directly provable:

1. Run the control before and after the change: pre-repair it fails at Step 8 while the
   toolkit is created; post-repair the same delayed-response run passes, and a run where
   the POST is blocked entirely fails at Step 7 naming the missing POST.
2. Then the standard gate — 3 separate consecutive clean-process invocations of the three
   non-skipped params:
   `cd automation && HEADLESS=true ../.venv/bin/pytest "tests/ui/toolkits/test_toolkit_parameterized.py::TestCreateToolkit::test_create_toolkit" -v -p no:cacheprovider`
3. Say plainly in the PR body that the CI red was a **false RED on a successful save**,
   and that two toolkits were leaked in CI run 34331579791 as a result.
