# Test-repair brief — `test_create_credential[jira]` / `[confluence]` save-click no-op

| field | value |
|---|---|
| **Card** | [#1897](https://github.com/EliteaAI/elitea-testing-public/issues/1897) — `[Fix][ELITEA-1140] test_create_credential_jira — assertion-failure` |
| **TMS case** | ELITEA-1140 (`onetest-ai-tm-Elitea/tests/elitea-platform/toolkits-credentials/ELITEA-1140_google-and-bitbucket-toolkit-crud.md`) |
| **Kind** | tech-task repair brief (not a fresh TMS-case AFS) |
| **Subject** | `automation/tests/ui/toolkits/test_toolkit_parameterized.py::TestCreateCredential::test_create_credential` (Steps 2–6, lines ~205–252) + `_fill_credential_auth_fields` (line ~638) |
| **Status** | `ready-for-automation` |
| **Root cause class** | **test-code issue** (triggered by a transient; the test code is what converts a transient into an opaque red) |
| **Analyst** | qa-engineer, 2026-08-28, live against `https://dev.elitea.ai` (`APP_PREFIX=/app`, deployed EliteaUI `main`) |
| **New testids needed** | **none** — every handle the repair needs already exists on `main` (§ Handles Reference) |
| **Reproduces on** | neither DEV nor localhost on demand — **transient**; the exact failure *signature* was reproduced deterministically by a control (§ Finding 2) |

---

## TL;DR

The product is **not** broken and the test has **not** drifted from the case. On
`dev.elitea.ai` the Jira and Confluence credential forms save correctly, every time
I drove them (§ Finding 1), and the same two params **passed on DEV in the runs
immediately before and after the failing one, including today's** (§ Finding 4).

What failed is the test's ability to *notice* and *report* a transient. Three
test-code defects compound:

1. **Step 5 clicks Save with `save_btn.evaluate("el => el.click()")`.** A JS
   `.click()` on a `disabled` button is a **silent no-op** — no exception, no
   network, no error. The one thing that could have caught the real fault is
   deliberately bypassed.
2. **Step 6's guard is vacuous.** `assert "/credentials" in page.url` is **True**
   on `/credentials/create-credential/jira` — the URL the browser never left. The
   guard that exists to catch "save didn't navigate" cannot fail.
3. **`_fill_credential_auth_fields` silently skips required fields**
   (`if username:` / `if base_url:`) and **never verifies a typed value landed**.

So a transient in which one required field was empty at click time is reported
**two steps downstream** as `Credential '…' not found via API`, with every trace of
the real cause destroyed. That is the whole of this failure.

**The repair is diagnosis and robustness, not assertion weakening.** It also
*restores* two expected results the case states and the test currently drops
(§ Correlation with ELITEA-1140).

---

## Ground truth (verified, not inherited)

GHA run [33066098636](https://github.com/EliteaAI/elitea-testing-public/actions/runs/33066098636),
job `dev-stable - toolkits` (job `98546889808`), user `autotest_user_6`, 2026-08-27:

| param | outcome | duration |
|---|---|---|
| `[github]` | **PASSED** | 15.17 s |
| `[jira]` | **FAILED** — `Credential 'AutoTest Jira 1787836716' not found via API` | 19.84 s |
| `[gitlab]` | skipped — `GITLAB_PRIVATE_TOKEN not set` | 0.35 s |
| `[bitbucket]` | skipped — no active account | 0.34 s |
| `[confluence]` | **FAILED** — identical signature | 20.59 s |

Decisive log line, verbatim from the job log:

```
📸 After save: URL=***/app/credentials/create-credential/jira
📊 Raw API response: {'total': 1, 'items': [{... 'type': 's3_api_credentials' ...}]}
✅ API returned 1 credentials total
```

The browser never left the create form, and the project contained exactly one
(unrelated, pre-existing) credential — **nothing was created**.

Allure step timings for `[jira]` (from `allure-results`, artifact `9648208825`):

```
Step 1 — Navigate to credential creation page   passed  3806 ms
Step 2 — Click credential type card: Jira       passed   152 ms
Step 3 — Fill Display Name                      passed  2355 ms
Step 4 — Fill auth-specific fields              passed  6766 ms
Step 5 — Click Save button                      passed  3103 ms
Step 6 — Verify navigation to credentials list   passed  3002 ms   <-- VACUOUS
Step 7 — Verify credential exists via API       FAILED   320 ms
```

Steps 5 **and 6 both report `passed`** while the save had already failed.

---

## Finding 1 — the product is correct (three independent live runs)

Driven against `https://dev.elitea.ai` as `${TEST_USER}` (Keycloak,
`input[name="username"]`), project 399:

| probe | path | result |
|---|---|---|
| direct navigation to `/credentials/create-credential/jira`, fill 4 fields, JS-click Save | `POST /api/v2/configurations/configurations/399` → **200**, credential id 3453 created, redirect to `/app/credentials/all`, toast **"The credential has been created successfully"** | ✅ |
| **the test's exact path** — `/credentials/create-credential` → `get_by_text("Jira", exact=True).first.click()` → same fills → JS-click Save | same POST 200, same redirect, same toast | ✅ |
| **the real pytest node** retargeted at DEV (`app_base_url = https://dev.elitea.ai/app`) | `3 passed, 2 skipped in 68.50s` — `[github]`, `[jira]`, `[confluence]` all green | ✅ |

Console: no errors. Network: no 4xx/5xx on the credential path. Per
`.agents/role-overrides.md` § "4xx/5xx from the UI" there is nothing to classify —
**there was no error response at all**, on either the failing CI run (no request was
made) or my runs (200).

---

## Finding 2 — the failure signature, reproduced deterministically

Control experiment: fill Display Name + Api Key + Username, **deliberately leave
Base Url empty** — exactly what `if base_url:` does when the env var is empty, and
what a transient value-loss looks like — then click Save the way the test does.

```
CONTROL: Base Url intentionally left empty
save disabled: True
visible field errors: []
networkidle ms: 4
>>> URL after JS click on DISABLED Save: https://dev.elitea.ai/app/credentials/create-credential/jira
>>> credential POSTs fired: []
>>> Step-6 guard `'/credentials' in page.url` evaluates to: True
credential-form-api-error-message count: 0
toast-message count: 0
=== and what a REAL Playwright click would have done instead ===
real click RAISED: TimeoutError Locator.click: Timeout 5000ms exceeded.
```

Every element of the CI signature, reproduced: **same URL, zero POSTs, no toast, no
error message, and the Step-6 guard passing.** And the last line is the repair in
one sentence — a real Playwright click *raises at the true failure point*, because
`click()` auto-waits for the element to be **enabled**.

> ⚠️ **Do not read the Step-5 duration as evidence.** 3103 ms is `wait_for_timeout(3000)`
> plus a ~100 ms `networkidle`, and a **successful** save produces the same 3.1 s
> (measured: networkidle returned in 0–4 ms on both my successful and my no-op runs).
> The duration discriminates nothing. Recorded because it is an inviting wrong turn.

---

## Finding 3 — why `[github]` passes and `[jira]`/`[confluence]` fail

Not luck. The **required-field sets differ**, captured live from the deployed `main`
(`input.required` read off each form's DOM):

| type | required fields | can a missed auth field disable Save? |
|---|---|---|
| **github** | `label`, `elitea_title`, `base_url` — and `base_url` **ships pre-filled** | **No.** Save enables after Display Name alone. Access Token is *not* required. |
| **jira** | `label`, `elitea_title`, `base_url`, `username` | **Yes** |
| **confluence** | `label`, `elitea_title`, `base_url`, `username` | **Yes** |
| gitlab | `label`, `elitea_title`, `url` | yes (skipped param) |
| bitbucket | `label`, `elitea_title`, `url`, `username` | yes (skipped param) |

`api_key` / `access_token` / `private_token` / `password` are **`required: false`**
on every form. So GitHub's Save can never be disabled by anything
`_fill_credential_auth_fields` does or fails to do, while Jira's and Confluence's
can. The param asymmetry in the failing run is fully explained by this table and
needs no other cause.

*(Corollary the same capture settles: the ELITEA-1975 AFS note that GitHub's Base
Url "ships with a live default" is confirmed on DEV.)*

---

## Finding 4 — it is transient, not a regression

Same test, same code (`main`), same environment, adjacent scheduled runs:

| run | date | `[jira]` | `[confluence]` | `[github]` |
|---|---|---|---|---|
| [32885145958](https://github.com/EliteaAI/elitea-testing-public/actions/runs/32885145958) | 08-25 | passed 46.29 s | passed 46.67 s | passed 51.22 s |
| [32931571484](https://github.com/EliteaAI/elitea-testing-public/actions/runs/32931571484) | 08-26 | passed 32.13 s | passed 37.07 s | passed 31.16 s |
| **[33066098636](https://github.com/EliteaAI/elitea-testing-public/actions/runs/33066098636)** | **08-27** | **FAILED 19.84 s** | **FAILED 20.59 s** | passed 15.17 s |
| [33149201954](https://github.com/EliteaAI/elitea-testing-public/actions/runs/33149201954) | 08-28 | passed 29.69 s | passed 21.64 s | passed 24.73 s |

Two things worth carrying forward:

- **The failing run was the fastest of the four, across every param** (github
  15.2 s vs 24.7–51.2 s elsewhere). Consistent with a run in which the app was
  answering fast enough that `wait_for_load_state("networkidle")` returned before
  the type-specific form schema had been fetched — Step 2 took **152 ms**, against
  500–900 ms in my own runs. `toolkit-field-label-input` renders in the generic form
  shell *before* the type schema lands, so Display Name can be typed into a form
  that is about to re-initialise. This is a **plausible, unproven** mechanism: I
  could not force it in 5 attempts. It is offered as the leading hypothesis, not a
  finding.
- **The secrets are all present.** `JIRA_USERNAME`, `JIRA_API_KEY`, `JIRA_BASE_URL`,
  `CONFLUENCE_*` all exist as repo secrets, are declared in
  `test-ui-custom.yml`'s `workflow_call.secrets`, and are exported in the "Run UI
  tests" step's `env:`. No `.env.test` is written in CI, so those env vars are what
  `config.py` resolves. **A permanently-empty env var is ruled out.**

### The one thing I could NOT determine, and why

**Which required field was empty at click time in that run.** The test destroys the
evidence: `pre_save_value` is logged at `INFO` (the run captured `WARNING`+ only),
the pre-save screenshot goes to `/tmp` and is never uploaded, and the failure
screenshot is not in any artifact. This is not a gap in the investigation — it is
the *defect being repaired*. After the repair, the next occurrence names the field
in the assertion message.

---

## Correlation with ELITEA-1140 — the test drops two stated expected results

| case step | case expected result | test today | disposition |
|---|---|---|---|
| 2 | "The form is filled out. **The Save button becomes enabled.**" | **never asserted** | **restore** — this is precisely the state that was wrong |
| 3 | "The page returns to the Credentials list." | `assert "/credentials" in page.url` — **passes without leaving the form** | **strengthen to a real check** |
| 4 | "The credential is found in the list with the matching display name." | asserted via the **API**, not the list | acceptable (API is the stronger oracle) — noted, not mandated |
| 7 | cleanup | `finally:` deletes via API | covered |

Restoring rows 2 and 3 is **not** new scope and **not** a strengthening beyond the
case — the case already asks for both. Per the preserve-the-nature rail this sits on
the "free to change" side: nothing is deleted, weakened, lowered, or made
conditional.

**Case drift, separately (report only, do not act here):** the case is titled
*"Google and Bitbucket Toolkit CRUD"* and its Coverage lists Google and Bitbucket,
but the linked automation parameterises github / jira / gitlab / bitbucket /
confluence and **never touches Google** (there is no `google` entry in
`TOOLKIT_CONFIGS`), while Bitbucket is permanently skipped. The case text is stale
relative to the tests linked to it. → clarification candidate for the operator.

---

## The repair

**Vehicle: route this test through the existing, testid-based `CredentialCreatePage`**
(`automation/pages/credential_create_page.py`, already on `main`, already exercised
green on DEV every night by `test_credential_required_fields_validation`). This is a
pure *how-it-reaches-and-identifies* change and it fixes four things at once:
the fragile grid click, the locator-policy violation, the React-unsafe typing, and
the un-assertable Save button.

### R1 — Step 2: stop clicking the type card; navigate directly *(blocker)*

`page.get_by_text(cfg.display_name, exact=True).first` on
`/credentials/create-credential` is a raw text handle against a **categorised,
lazily-rendered** card grid. I hit it myself: on a later probe the `Jira` card was
present in the DOM but **never became visible within 10 s** (`get_by_text("Jira",
exact=True).count() == 1`, `wait_for(state="visible")` timed out) — Jira sits under
the *Project Management* category, below the fold.

Replace Steps 1+2 with:

```python
create_page = CredentialCreatePage(page)
create_page.navigate_to_type(cfg.url_slug)     # -> /credentials/create-credential/{type}
```

`navigate_to_type()`'s own docstring documents this exact class of breakage
(ELITEA-1963). `cfg.url_slug` already carries the right slug for all five types.

> Coverage note: the case's Step 2 says "Click 'Create credential'. Select the
> toolkit type." The type-card click is **already covered** by
> `test_credential_required_fields_validation`'s sibling entry point
> (`CredentialCreatePage.click_type_card`) and by `toolkit-type-card-{type}`. This
> test's subject is the *save*, not the grid. Record the substitution in the PR body.

### R2 — Step 5: click Save for real, and assert it is enabled first *(blocker)*

```python
with allure.step("Step 5 — Click Save button"):
    expect(create_page.save_button).to_be_enabled(timeout=UI_ELEMENT_TIMEOUT)   # case Step 2's expected result
    create_page.save_button.click()                                             # NOT .evaluate("el => el.click()")
```

Delete the `evaluate("el => el.click()")` outright. Rationale, in the code, one
line: *a JS click on a disabled button is a silent no-op — see #1897.*

### R3 — Step 6: replace the vacuous guard *(blocker)*

```python
with allure.step("Step 6 — Verify navigation to credentials list"):
    page.wait_for_url(re.compile(r"/credentials/all(\?.*)?$"), timeout=NAVIGATION_TIMEOUT)
```

`/credentials/all` is the **observed** post-save destination (three live runs).
Do **not** keep a substring guard — `"/credentials" in page.url` is true on the
create form. Replacing `wait_for_timeout(3000)` with `wait_for_url` also removes a
fixed sleep, per § Hard don'ts.

### R4 — `_fill_credential_auth_fields`: verify what was typed, fail loudly if a required value is missing *(blocker)*

Two changes, both diagnosis:

```python
# jira / confluence branch
create_page.set_base_url(settings.jira_base_url)
expect(create_page.base_url_input).to_have_value(settings.jira_base_url)
```

- Use the page object's `set_base_url` / `set_api_key` / `set_username` /
  `set_display_name` — they use `press_sequentially(value, delay=20)`, which is
  React-safe, instead of the deprecated `.type()`.
- Replace each silent `if value:` guard with an **explicit precondition**: an empty
  env var for a *required* field must `pytest.skip` with the variable name (a config
  gap, not a product verdict), never fall through into a disabled Save. Non-required
  secret fields (`api_key`) may stay conditional.
- Assert every typed value with `to_have_value(...)` immediately after typing. If a
  transient wipes a field, the test now fails **at Step 4 naming the field**, which
  is the missing evidence this whole investigation needed.

### R5 — latent defect in the skipped branches *(non-blocking, record it)*

`_fill_credential_auth_fields` locates `input[type="password"][name="api_key"]` for
**gitlab** and **bitbucket**, but their secret fields are named **`private_token`**
and **`password`** (captured live — `toolkit-field-private_token-input-field`,
`toolkit-field-password-input-field`). Both params are currently skipped, so this has
never fired. Fix it while in the file if it is cheap; otherwise note it in the PR so
it is not rediscovered when those tokens come back.

### What must NOT change

- The Step-7 API oracle: `created_id` resolved by matching `c["label"] == cred_name`,
  and `assert created_id is not None`. **This is the case's observable.** Do not
  soften it to a substring/`in` match, do not make it conditional, do not add a
  retry that could pass on a credential the test did not create.
- The `finally:` cleanup, the `@allure.issue` case link, the `p0` / `credentials`
  markers, and the `allure.step("Step N — …")` structure and numbering.
- The parameterisation over `_all_toolkit_ids()` and the existing skip semantics.
- **No `pytest.skip`, `xfail`, soft-assert or weakened comparison anywhere.** There
  is no product defect here to mask, and a transient is not a licence to weaken.

---

## Handles Reference (testid-only)

All generated by `ToolBaseProperty.jsx` from the schema property key
(`` testId={`toolkit-field-${k}-input`} ``), so they exist for **every** credential
type without new UI work. Verified two ways: the **generator is on `origin/main`**
(`git fetch origin` run 2026-08-28 immediately before the check), and every id below
was **read out of the live DOM on `dev.elitea.ai`**, which serves `main`.

| element | handle | page-object field | PROVENANCE |
|---|---|---|---|
| Display Name | `toolkit-field-label-input` | `display_name_input` (mixin) | on-main ✓ (`ToolBaseProperty.jsx:294/329/603`) · live on DEV ✓ |
| Credential ID (mirror) | `toolkit-field-elitea_title-input` | `id_input` (mixin) | on-main ✓ · live on DEV ✓ |
| Base Url | `toolkit-field-base_url-input` | `base_url_input` | on-main ✓ · live on DEV ✓ (jira, confluence, github) |
| Username | `toolkit-field-username-input` | `username_input` | on-main ✓ · live on DEV ✓ (jira, confluence, bitbucket) |
| Api Key (secret) | `toolkit-field-api_key-input-field` | `api_key_input` | on-main ✓ · live on DEV ✓ (jira, confluence) |
| Access Token (github/token) | `toolkit-field-access_token-input-field` | `access_token_input` | on-main ✓ · live on DEV ✓ |
| Auth method radio | `toolkit-field-auth-radio-{slug}` | `AUTH_METHOD_RADIO` template | on-main ✓ (`ToolSection.jsx:291`) · live on DEV ✓ — github: `none`/`token`/`password`/`app-private-key`; jira+confluence: `basic`/`bearer` |
| Save | `credential-form-save-button` | `save_button` (mixin) | **on-main ✓ (literal, `CredentialsTabBar.jsx:222`)** |
| Server-side error | `credential-form-api-error-message` | `api_error_message` | **on-main ✓ (literal, `CredentialForm.jsx:357`)** |
| Type card | `toolkit-type-card-{type}` | `TYPE_CARD_SELECTOR` template | on-main ✓ (`CategoryItemCard.jsx:14`) · live on DEV ✓ |
| Url (gitlab/bitbucket) | `toolkit-field-url-input` | **not yet on the page object** — add as a `LocatorDescriptor` if R5 is taken | on-main ✓ · live on DEV ✓ |
| Private Token (gitlab) | `toolkit-field-private_token-input-field` | as above | on-main ✓ · live on DEV ✓ |
| Password (bitbucket) | `toolkit-field-password-input-field` | as above | on-main ✓ · live on DEV ✓ |

> **Grep caveat, stated so nobody re-derives it as a false negative.** The
> closure-record two-stage grep reports `main:no` for every `toolkit-field-*` and
> `toolkit-type-card-*` id. That is the documented **runtime-composed** blind spot
> (`.agents/workflow.md`: *"stage 1 cannot see these at all"*) — the testids are
> template-interpolated, so no literal string exists to match. The generators are on
> `main`, and the deployed DEV DOM proves the rendered ids. `credential-form-*` are
> literals and do grep clean. **Do not read `main:no` here as "needs adding".**

**New testids required: none.**

---

## Coverage Map

### Axis 1 — case elements

| case element | expected result | covered by | asserted where | disposition |
|---|---|---|---|---|
| Step 1 — credentials valid / skip if expired | valid, or a clear skip | `toolkit_config` fixture + `_validate_credentials` | fixture | covered (unchanged) |
| Step 2 — open form, select type, fill fields | form filled; **Save becomes enabled** | R1 (`navigate_to_type`) + R4 (typed-value assertions) + **R2 (`to_be_enabled`)** | Steps 2–5 | **restored** — currently dropped |
| Step 3 — click Save, page returns to list | returns to Credentials list | R2 (real click) + **R3 (`wait_for_url`)** | Steps 5–6 | **restored** — currently vacuous |
| Step 4 — credential appears with correct name | found with matching display name | existing API oracle (`label == cred_name`) | Step 7 | covered — unchanged, must not weaken |
| Step 5–6 — toolkit creation | — | `TestCreateToolkit` (sibling test) | — | out of scope for this test |
| Step 7 — cleanup | both deleted | `finally:` block | teardown | covered (unchanged) |
| Case title/Coverage — **Google** | Google credential + toolkit | **nothing** — no `google` entry in `TOOLKIT_CONFIGS` | — | **case drift → clarification** (report; do not automate here) |

### Axis 2 — asserted beyond the case

| observable | reason |
|---|---|
| each typed field holds its value after typing (R4) | the transient this repair exists to expose; without it the failure is undiagnosable |
| required env var present ⇒ else explicit skip (R4) | a config gap must not masquerade as a product failure |

---

## Blocked Steps

None. The repair needs no new testid, no new fixture, and no product change.

---

## Open question for the operator (I did not decide it)

**Should the repaired test also assert the credential is visible in the
`/credentials/all` list UI (case Step 4's literal wording), in addition to the API
oracle?**

- *Option A (recommended):* keep the API oracle only. It is the stronger, less
  flaky oracle, it is what the test does today, and adding a list assertion is new
  scope on a repair branch.
- *Option B:* add a list assertion too, closing the last literal gap against case
  Step 4.

I recommend **A**, and recording the difference as a Coverage-Map note (done above)
rather than expanding the repair. This changes *what* is verified, so per the
preserve-the-nature rail it is not mine to settle.

---

## Evidence

Local, uploadable on request (`.agents/role-overrides.md` § screenshot evidence —
these are analysis artifacts, not issue evidence, so they are cited as paths here
and must be uploaded if any of them lands in a tracker comment):

| file | shows |
|---|---|
| `/tmp/afs1897/jira-01-empty-form.png` | empty Jira create form on DEV |
| `/tmp/afs1897/jira-02-filled-form.png` | all four required fields filled, Save enabled |
| `/tmp/afs1897/jira-03-after-js-save.png` | successful save → `/credentials/all` + success toast |
| `/tmp/afs1897/jira-B01-type-grid.png` | the categorised type-card grid (R1) |
| `/tmp/afs1897/jira-B02-after-card-click.png` | form reached via the test's own card-click path |
| **`/tmp/afs1897/jira-C01-missing-baseurl.png`** | **control — Base Url empty, Save disabled, no field error shown** |
| **`/tmp/afs1897/jira-C02-after-noop-click.png`** | **control — after the JS click: still on the create form, nothing happened** |
| `/tmp/afs1897/grid-now.png` | type grid with `Jira` present in DOM but below the fold |

Repro scripts (throwaway, read secrets from `.env.test` via dotenv and never print
them): `/tmp/afs1897/repro.py`, `repro2.py`, `repro3.py` (the control), `repro4.py`,
`repro5.py`, `repro6.py`, plus `/tmp/afs1897/devtarget.py` (pytest plugin that
retargets the suite at DEV without touching the shared `.env.test` symlink).

---

## Gate expectation for the implementer

Because the failure is transient and does not reproduce, a green gate **cannot**
prove the repair fixed the trigger — and it is not supposed to. The gate proves the
repaired test still passes honestly; the *repair* is proved by the control in
§ Finding 2, which shows the new shape fails loudly where the old one passed
silently. Run the standard 3× consecutive clean-process gate on the three
non-skipped params, and say plainly in the PR body that the transient is not
reproducible on demand.
