# Adjustment Spec — Toolkit Test Settings (ELITEA-1140)

## Metadata

- **TMS ID**: ELITEA-1140 — *Google and Bitbucket Toolkit CRUD*
  (`../onetest-ai-tm-Elitea/tests/elitea-platform/toolkits-credentials/ELITEA-1140_google-and-bitbucket-toolkit-crud.md`)
- **Tracking issue**: [EliteaAI/elitea-testing-public#1816](https://github.com/EliteaAI/elitea-testing-public/issues/1816)
- **Test under repair**: `automation/tests/ui/toolkits/test_toolkit_parameterized.py::TestToolkitTestSettings::test_toolkit_test_settings`
  (`automation_test_id` Form C: `tests.ui.toolkits.test_toolkit_parameterized.test_toolkit_test_settings` — **unchanged by this repair**)
- **Params affected**: `[github]`, `[jira]`, `[confluence]` — all three, same root cause.
  (`[gitlab]` and `[bitbucket]` carry `skip_reason` and never execute.)
- **Branch**: `fix/1816-elitea-1140-test-settings-route`, cut from `origin/main` @ `c25113893`
  (this test is already promoted; the repair targets `main`, not `automation/base`).
- **Environment explored**: `http://localhost:5173` — EliteaUI `automation/testids` @ `a3b25e95`
  (0 behind `origin/main` @ `87d9ea74`), DEV backend, project `Private` / `399`.
- **Analyst**: qa-engineer, analyst slot, 2026-08-27.
- **Status**: **ready-for-automation (repair)** — class **A** UI drift, fully characterised,
  every replacement handle already on EliteaUI `main`, no `add-data-testid` work, nothing masked.
  **One caveat that is NOT drift and must not be repaired by weakening**: the `[github]`
  parameter additionally cannot reach a green gate on this machine because `GIT_HUB_TOKEN`
  in `.env.test` is expired — see § Class D finding. `[jira]` and `[confluence]` ran green
  end-to-end live.
- **Sibling of**: ELITEA-1866 / issue [#1815](https://github.com/EliteaAI/elitea-testing-public/issues/1815),
  repaired by `c25113893`. That commit's message states the repair was *"designed reusable:
  three sibling specs carry the same drift and are tracked separately"* — **this is one of
  those siblings, and it reuses `ToolkitDetailPage.open_test_surface()` verbatim rather than
  re-deriving it.**

---

## § Adjustment 2026-08-27 — the Test Toolkit surface moved to its own route

### Triage: class **A — UI drift**

Not a product bug, not a promotion gap, not (for the reported symptom) data pollution.

**Evidence, in the order it was gathered:**

1. **The reported failure reproduces locally, on `origin/main` code, against `localhost:5173`.**
   ```
   cd automation && HEADLESS=true ../.venv/bin/pytest \
     "tests/ui/toolkits/test_toolkit_parameterized.py::TestToolkitTestSettings::test_toolkit_test_settings[github]" \
     -v -p no:cacheprovider
   …
   FAILED …::test_toolkit_test_settings[github] - playwright._impl._errors.TimeoutError:
     Locator.wait_for: Timeout 10000ms exceeded.
     Call log: - waiting for get_by_test_id("toolkit-test-empty-tool-select") to be visible
   ERROR elitea.steps:actions.py:49 Step failed: Select a tool in the Test Settings panel
   ============== 1 failed, 3 warnings, 2 rerun in 87.69s (0:01:27) ===============
   ```
   Byte-identical to GHA run 32931571484 on `dev.elitea.ai`. Reproducing on **both**
   environments rules out env/infra (class D) for this symptom.

2. **Promotion-gap pre-check: NEGATIVE.** `toolkit-test-empty-tool-select` is present on
   **both** refs (fresh `git fetch origin`, output pasted in § Handles Reference). The testid
   was never removed or renamed — it simply is not rendered on the URL the test navigates to.

3. **Live DOM proof of the drift** — `/toolkits/all/3491` (a freshly API-created GitHub
   toolkit), after full load:
   ```json
   {"url": "http://localhost:5173/toolkits/all/3491?name=AFS1140+GitHub+Toolkit+…",
    "hasTestSettingsText": false,
    "toolkit-test-empty-tool-select": {"present": false},
    "toolkit-test-tool-select":       {"present": false},
    "toolkit-test-run-tool-button":   {"present": false},
    "chat-message-list":              {"present": false},
    "toolkit-test-button":            {"present": true, "disabled": false, "text": "Test"},
    "toolkit-detail-title":           {"present": true, "text": "AFS1140 GitHub Toolkit …"},
    "toolkit-indexes-panel":          {"present": true, "text": "IndexesIndexing is not available…"}}
   ```
   ![Toolkit detail view — no Test Settings; a 'Test' action-bar button instead](https://github.com/EliteaAI/elitea-testing-public/releases/download/evidence/ELITEA-1140-detail-view-no-test-settings.png)

4. **The product's own route to the surface**, confirmed by clicking it:
   `[data-testid="toolkit-test-button"]` → URL becomes `http://localhost:5173/toolkits/all/3491/test`,
   and `toolkit-test-empty-tool-select` is present there. Source of record:
   `src/routes.js:36 → ToolkitTest: '/toolkits/:tab/:toolkitId/test'`
   → `src/[fsd]/pages/toolkit/ToolkitTest.jsx:84` renders `<ToolkitTestPanel toolkitId={entityId} />`.
   The button itself: `src/[fsd]/features/toolkits/ui/form/ToolkitForm/ToolkitForm.jsx:551`
   (`disabled={isTestDisabled}` — "Save your changes to test"; enabled on a freshly-navigated,
   non-dirty detail view, confirmed live for all three toolkit types).

**Interaction-discovery ladder** (`.agents/role-overrides.md`): not applicable as a "doesn't
work" bug — the decisive source-read step was performed and the intended flow is
button → route, and it works. **4xx/5xx cross-check**: the one console error observed across
the whole walk was `400` from `…/toolkit_validator/prompt_lib/399/3491`, i.e. the *validator
rejecting the expired GitHub token* on the GitHub toolkit only — see § Class D finding. Zero
console errors on the Jira and Confluence walks.

### **Walk the whole flow — the stack trace showed only the FIRST break**

Per the dispatch's instruction (and the ELITEA-1866 precedent, where drift spanned 8 steps),
every step 2→8 was re-executed live on all three toolkit types. **A second, latent break was
found at Step 5** that the stack trace could never have shown, because Step 2 dies first:

> `_fill_test_settings_param()` (`test_toolkit_parameterized.py:713-744`) locates the parameter
> input and then **filters it by `bb["x"] > 700`** ("the right panel"). On the redesigned
> surface the Test Settings column is the **LEFT** column (`ToolkitTestPanel.jsx:42` —
> `styles.leftColumn`, `borderRight`), with Results on the right. Measured live at
> viewport 1728: the Confluence `Label` input sits at **x = 350**. The headless suite runs at
> **1366×768** (`conftest.py:309`), where it is narrower still.
> The `x > 700` filter therefore never matches, and the helper's `if target is None:` branch
> **logs a warning and silently RETURNS without filling anything**. Step 6's `Run Test` button
> is `disabled` until the required param is filled (verified live), so `[confluence]` would
> then die at Step 6 on click actionability — a *different* failure, at a *different* step,
> after Step 2 is repaired.

This is why the repair below is specified for the whole flow, not just the navigation.

### Per-step OLD → NEW

| Step | OLD (what breaks / why) | NEW (verified live) |
|---|---|---|
| **1** | `goto(/toolkits/all)` → `dismiss_popups()` → `goto(/toolkits/all/{tk_id})` → `wait_for_timeout(2000)`. A fixed sleep is not a readiness signal. | Same navigation, then wait on a real readiness handle: `toolkit-detail-title` visible. **Observed twice live**: the first `toolkit-test-button` click on toolkits 3492 and 3493 raised *"does not match any elements"* and succeeded moments later — the action bar is not mounted at `domcontentloaded`. `open_test_surface()` already `wait_for`s the button, which absorbs this; do not re-add a sleep. |
| **1b — NEW STEP** | *(did not exist)* | `ToolkitDetailPage(page).open_test_surface()` — clicks `toolkit-test-button`, waits for `re.compile(r".*/toolkits/[^/]+/\d+/test")`. **Already on `origin/main`** (`automation/pages/toolkit_detail_page.py:183-202`, added by `c25113893`). **Reuse it — do not re-derive, and do not `page.goto()` the `/test` URL**: navigating through the product's own control is required by `.agents/testing.md` § Fidelity policy (a forced URL substitutes the navigation the case exercises). Verified live on all 3 toolkit types → `/toolkits/all/{id}/test`. |
| **2** | `test_settings.open_empty_state_tool_select(...)` — **times out**, the empty state is not on `/toolkits/all/{id}`. | Call is **unchanged**; it now runs on the `/test` route where the element exists. Live text: `"Test toolkit / Choose a tool from the list to configure parameters and run the test. / Select Tool"`. |
| **3** | `Popper.find_visible_search_input(page)` (raw `input[placeholder*="Search"]`) + `Popper.select_menuitem_by_content(page, lambda t: keyword in t.lower())` (raw `[role="menuitem"], [role="option"]`). Both still *function* on the new surface (verified live: the search input filters, options carry `role="menuitem"`), but they are raw handles and the display names drifted (`"List branches"` → **"List branches in repo"**, `"List pages"` → **"List pages with label"**). | `test_settings.select_tool_from_empty_state(tool_key)` — testid-only, already on `origin/main` (`toolkit_test_settings_page.py:169-184`), no search typing needed. **`tool_key` = `cfg.test_tool_result_indicator`** — verified live that the option testid is exactly `select-option-<indicator>` for every param (table below). This retires two raw handles and makes the step immune to display-name drift. |
| **4** | `test_settings.wait_for_panel(...)` | **unchanged** — `toolkit-test-tool-select` mounts once a tool is chosen (live: combobox text = the tool's display name). |
| **5** | `_fill_test_settings_param(page, field_label, value)` — raw `.index-config-field:has(span:text("…")) input` + the **`x > 700` silent-no-op bug** above. | `test_settings.fill_param_field(schema_key, value)` — testid `toolkit-test-param-{key}-input`, already on `origin/main` (`toolkit_test_settings_page.py:284-302`; MUI `press_sequentially` discipline). **Re-key `ToolkitConfig.test_tool_params` from display label to schema key**: `confluence.test_tool_params = {"Label": "test"}` → `{"label": "test"}`. **Delete `_fill_test_settings_param`** — it has no other caller (verified: one call site, line 413). |
| **6** | `dismiss_popups()` + `test_settings.run_tool(...)` | **unchanged.** Live: button text `"Run Test"`, testid unchanged, `disabled` until the form is valid — Playwright click actionability waits it out correctly. |
| **7** | `page.wait_for_function` polling `document.querySelector('main').textContent` for the indicator OR `"Error debugging info"`, wrapped in a bare `except: pass`, then `wait_for_timeout(2000)`. A swallowed timeout means Step 8 asserts against whatever happened to be on screen. | `result_text = test_settings.wait_for_tool_result(timeout=TOOLKIT_EXECUTION_TIMEOUT, tool_key=<tool_key>)` — already on `origin/main` (`toolkit_test_settings_page.py:392-485`): scoped to `[data-testid="chat-message-list"] li.MuiListItem-root`, polls for the `[✅❌]` prefix via auto-retrying `expect(...).to_contain_text`, and carries the ELITEA-1979 mid-wait remount recovery. `TOOLKIT_EXECUTION_TIMEOUT` is already 120 s — comfortably above the model-turn budget (ELITEA-1866 needed 60 s). Removes a `wait_for_function`, a swallowed exception and a 2 s sleep. |
| **8** | `error_locator.is_visible()` on raw `text="Error debugging info"` → `pytest.fail`; then `assert cfg.test_tool_result_indicator in page.locator("main").text_content()`; then optional `result_row.click()` (raw `text="…"`) + `assert cfg.test_tool_result_content in main.text_content()`. | Assert against the **`result_text` string Step 7 returned** — the system-produced result, scoped to the result item instead of the whole `<main>`: `assert cfg.test_tool_result_indicator in result_text` and `assert cfg.test_tool_result_content in result_text`. The diagnostic error branch is **preserved, not dropped** — re-express it as a string check on the same system-produced text (`if "❌" in result_text or "Error debugging info" in result_text: pytest.fail(f"Tool execution failed for {cfg.display_name}: {result_text[:300]}")`) instead of a raw `text=` locator. The `result_row.click()` expand step is no longer needed: verified live that the full result body is already in the item's `textContent` even with the thought accordion collapsed. |

**Verified live result texts** (the item's `textContent`, read from `RESULT_MESSAGE_ITEM`):

| Param | Option testid (= `test_tool_result_indicator`) | Params | Result item text | Indicator ✓ | Content ✓ |
|---|---|---|---|---|---|
| `[jira]` | `select-option-list_projects` | none | `…Thought for less than a second… : list_projects ✅ list_projects (0.368s) Found 6 projects: [{'id': '10165', 'key': 'AIPSDLC', …}]` | ✅ | ✅ (`project`) |
| `[confluence]` | `select-option-list_pages_with_label` | `label="test"` | `…: list_pages_with_label ✅ list_pages_with_label (1.117s) Tool executed successfully` | ✅ | ✅ (`page`, via `list_pages…`) |
| `[github]` | `select-option-list_branches_in_repo` | none (`Max Count`, default 100) | `…: list_branches_in_repo ✅ list_branches_in_repo (0.213s) Failed to list branches: 401 {"message": "Bad credentials", …}` | ✅ | ❌ (`"main"` absent — **§ Class D finding**) |

![Test Toolkit route — Confluence run result](https://github.com/EliteaAI/elitea-testing-public/releases/download/evidence/ELITEA-1140-test-route-confluence-result.png)

> ⚠️ **`✅` is NOT a success oracle.** GitHub returned `✅ list_branches_in_repo (0.213s)`
> with a `401 Bad credentials` body — the *tool ran*, the *call failed*. The only real
> oracle in this test is `test_tool_result_content in result_text`. Do not let a repair
> substitute the ✅ marker for that assertion.

### Preserve-the-nature disposition

| Case observable (FROZEN) | How it is reached/identified (CHANGED) |
|---|---|
| The toolkit's Test surface is reachable from its detail view | *(new navigation step — no new observable)* click `toolkit-test-button`, assert the `/test` URL |
| The tool-selection entry point is present on that surface | unchanged testid, new route |
| The chosen tool's parameter schema renders as live inputs | raw `.index-config-field` + x-filter → `toolkit-test-param-{key}-input` |
| Running the tool returns a result containing the tool's key | `<main>` textContent → the scoped result-item text |
| The result body contains the expected content (`"main"` / `project` / `page`) | `<main>` textContent (+ a row click) → the scoped result-item text |
| A failed run fails the test loudly | raw `text="Error debugging info"` locator → the same check as a string test on the result text |

**Expected-result changes: NONE.** No assertion is deleted, softened, made conditional, or
lowered. Two assertions become **stricter** by scoping from the whole `<main>` element to the
result message item; one swallowed-timeout path (`except: pass`) is removed so a stalled run
now fails instead of silently proceeding. Both are strengthenings and are recorded here per
the rail, in the direction it also requires be made visible.

### Handles Reference — PROVENANCE verified 2026-08-27

Fresh ground truth, same command block (`.agents/role-overrides.md` § fresh ground truth):

```
$ cd ../EliteaUI && git fetch origin
origin/main = 87d9ea74   origin/automation/testids = a3b25e95

toolkit-test-button                main:YES  testids:YES
toolkit-test-empty-tool-select     main:YES  testids:YES
toolkit-test-tool-select           main:YES  testids:YES
toolkit-test-run-tool-button       main:YES  testids:YES
chat-message-list                  main:YES  testids:YES
toolkit-detail-title               main:YES  testids:YES
--- dynamic templates ---
select-option-                     main:YES  testids:YES
toolkit-test-param-                main:YES  testids:YES
--- source lines on origin/main ---
origin/main:src/[fsd]/features/toolkits/ui/form/ToolkitForm/ToolkitForm.jsx:551:  data-testid="toolkit-test-button"
origin/main:src/[fsd]/shared/ui/select/PopoverSelect.jsx:109:       data-testid={option.testId ?? `select-option-${option.value}`}
origin/main:src/[fsd]/shared/ui/select/SingleSelect.jsx:416:        data-testid={option.testId ?? `select-option-${option.value}`}
origin/main:src/[fsd]/shared/ui/select/SingleSelectMenuItem.jsx:117:  data-testid={option.testId ?? `select-option-${option.value}`}
origin/main:src/[fsd]/features/toolkits/ui/toolkit-test/ToolkitTestSettings.jsx:87:  inputTestId={`toolkit-test-param-${key}-input`}
origin/main:src/[fsd]/shared/ui/field/AnyOfPatternField.jsx:49:      data-testid={`toolkit-test-param-${fieldKey}`}
origin/main:src/[fsd]/shared/ui/field/CommonBooleanField.jsx:28:     data-testid={`toolkit-test-param-${fieldKey}`}
origin/main:src/[fsd]/shared/ui/field/CommonStringField.jsx:114,139,161: data-testid={`toolkit-test-param-${fieldKey}`}
origin/main:src/[fsd]/shared/ui/field/CommonStringField.jsx:196:    'data-testid': inputTestId,
```

| Element | testid | Change | PROVENANCE |
|---|---|---|---|
| Detail action-bar "Test" button | `toolkit-test-button` | **NEW to this spec** — the route to the Test surface | **on-main ✓** (`ToolkitForm.jsx:551`) |
| Detail title (readiness anchor) | `toolkit-detail-title` | **NEW to this spec** — replaces `wait_for_timeout(2000)` | **on-main ✓** (`EditToolkit.jsx:401`) |
| Empty-state tool select | `toolkit-test-empty-tool-select` | unchanged testid, **moved route** | **on-main ✓** (`ToolkitTestEmptyState.jsx:39`) |
| Tool combobox (panel mounted) | `toolkit-test-tool-select` | unchanged, moved route | **on-main ✓** (`ToolkitTestSettings.jsx:53`) |
| Tool dropdown option | `select-option-{tool_key}` | **NEW to this spec** — replaces the raw search+role scan | **on-main ✓** (shared `PopoverSelect`/`SingleSelect*`) |
| Tool param wrapper | `toolkit-test-param-{schema_key}` | **NEW to this spec** | **on-main ✓** (`CommonStringField.jsx:114/139/161`) |
| Tool param input | `toolkit-test-param-{schema_key}-input` | **NEW to this spec** — replaces `_fill_test_settings_param` | **on-main ✓** (`ToolkitTestSettings.jsx:87` → `CommonStringField.jsx:196`) |
| Run button | `toolkit-test-run-tool-button` | unchanged testid; label already "Run Test" | **on-main ✓** (`ToolkitTestSettings.jsx:96`) |
| Result message list | `chat-message-list` | **NEW to this spec** — replaces `page.locator("main")` | **on-main ✓** (`ChatMessageList.jsx`); **absent until the first run completes** (`ToolkitTestResults.jsx:29` early-returns `null` while empty) |

**No `testid needed:` rows. No `add-data-testid` work. No promotion-gap risk** — every handle
this repair uses is already on EliteaUI `main`, so the fixed test is green locally **and** on
the deployed DEV env that filed the card.

**One observed testid gap, deliberately NOT used and NOT filed as work here:** the numeric
`Max Count` param on GitHub's `list_branches_in_repo` renders with **no testid at all** (live:
`.index-config-field` with a bare `<input type="tel" value="100">`; the numeric renderer does
not consume `inputTestId`). The test never fills it (GitHub's `test_tool_params` is `{}`, and
the schema default 100 already makes the form valid), so per `.agents/testing.md` § Locator
policy — *testids go ONLY on elements tests actually touch* — adding one would be a
blanket-add. Recorded as an observation for whichever case first needs to drive that field.

### Class D finding — expired `GIT_HUB_TOKEN` (NOT the reported drift, must NOT be masked)

Independent of the drift, and discovered while executing Step 8 for `[github]`:

```
$ python -c "... requests.get('https://api.github.com/user', headers={'Authorization': f'token {GIT_HUB_TOKEN}'})"
token set: True  len: 40
api.github.com/user -> 401
branches            -> 401
```

The token in `.env.test` is rejected by **GitHub itself**, before Elitea is involved. Consequence
for this test: after the route repair, `[github]` still fails at Step 8 —
`assert '"main"' in result_text` — because `list_branches_in_repo` returns
`Failed to list branches: 401 {"message": "Bad credentials", …}`. The `400` console error from
`…/toolkit_validator/prompt_lib/399/3491` observed during the walk has the same single cause.

- **This is class D (test-data / environment), not a product bug and not drift.** Elitea faithfully
  surfaces GitHub's own 401.
- **Do not weaken Step 8 to accommodate it.** Lowering `test_tool_result_content` for `[github]`,
  or asserting the `✅` marker instead of the content, would mask a dead credential and a real
  oracle at the same time.
- **The honest fixes, in order:** (1) refresh `GIT_HUB_TOKEN` in the master `.env.test` — a human
  action; (2) implement the TMS case's **own Step 1** for GitHub.

  > TMS case ELITEA-1140, Step 1: *"Verify your Google/Bitbucket credentials are still valid. If the
  > … token is expired (returns 401), skip … "* → *Expected: Credentials are valid, or you have a
  > clear reason to skip."*

  `_validate_credentials()` already implements exactly this, but `ToolkitConfig.credential_check`
  is populated **only for `bitbucket`** (`toolkit_configs.py:162-167`). `github`, `jira` and
  `confluence` have none, so an expired token cannot produce the case's specified skip and
  surfaces as an opaque assertion failure instead. Adding
  `credential_check={"url": "https://api.github.com/user"}` for `github` **adds** the case's
  specified behaviour — it removes nothing, so it is not masking.

  Because (2) is an addition of specified-but-unimplemented behaviour rather than a locator/flow
  change, it is flagged for the lead's explicit nod rather than assumed in scope
  (`.agents/role-overrides.md` § declared-improvisation protocol, ceiling clause).

**Gate impact:** `[jira]` and `[confluence]` are fully gateable today (both ran green end-to-end
live). `[github]` cannot reach 3×-green on this machine until (1) lands. Whether CI's own
`GIT_HUB_TOKEN` secret on `dev.elitea.ai` is still valid is **unknown from here** — see § Questions.

### TMS case-text drift

The case's **Steps table has no Test Settings step at all** — the requirement this test automates
exists only as the Coverage bullet *"Test Google toolkit settings"* / *"Test Bitbucket toolkit
settings"*, while Steps 1-7 cover credential + toolkit CRUD and cleanup. The case text is therefore
not *wrong* about the Test surface; it is **silent**, which is why no case step needed correcting
by this repair. Recommended additions (a human/TMS decision, not this repair's):

| # | Proposed step | Proposed expected result |
|---|---|---|
| 5b | Open the toolkit's detail view and click **Test** in the action bar | The Test Toolkit view opens at `/toolkits/all/{toolkit_id}/test`, showing a "Test Settings" column with a **Select Tool** control beside a "Results" column |
| 5c | Choose the toolkit's list tool, fill any required parameters, click **Run Test** | The Results column shows the tool's run result, containing the tool key and the expected content |

`automation_test_id` is **unchanged** (same test, same dotted path).

### Questions for a human — stated, not guessed

1. **Is CI's `GIT_HUB_TOKEN` secret (GHA / `dev.elitea.ai`) still valid?** If it is, the drift repair
   alone clears the card on CI and the local `[github]` red is a workstation-only condition. If it is
   not, `[github]` is red on CI too, for a *second* reason this repair deliberately does not touch.
   I could not verify a CI secret from this session.
2. **Should the `credential_check` addition for `github`/`jira`/`confluence` ride this repair?**
   It implements the case's own Step 1 and would convert an expired-token red into the specified
   skip. It is an addition, never a weakening — but it changes when the test runs at all, so it
   needs the lead's nod.
3. **Spec location.** The dispatch named `test-specs/toolkits/…`, which this file follows exactly.
   The repo has no `test-specs/toolkits/` — this module's existing specs (including the `_surface.md`
   digest) all live in **`test-specs/toolkits-credentials/`**, matching the TMS case's
   `module: toolkits-credentials`. Flagging rather than silently relocating; happy to move it.
4. **Case/automation scope mismatch (pre-existing, out of scope, worth a card).** ELITEA-1140 is
   titled *"Google and Bitbucket Toolkit CRUD"* and its Test Data names Google and Bitbucket, but
   the four tests it claims parametrize over `github / jira / gitlab / bitbucket / confluence` —
   with **no Google config at all**, and `bitbucket` unconditionally skipped. The case and its
   automation are describing different things.

### Status after adjustment

**ready-for-automation (repair)** for the class-A drift — flow re-executed end-to-end live on all
three executing params, every replacement handle on `main`, four raw handles retired, a latent
second break (Step 5's silent no-op) found and specified, no assertion weakened, no defect masked,
no product bug found. `[github]`'s gate is additionally gated on the class-D token refresh above.
