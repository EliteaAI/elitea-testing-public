# Test Case: Clicking the masked secret value copies the real value to the clipboard

## Metadata
- **TMS ID**: ELITEA-2335
- **Source case**: `.agents/automation/settings-w05/cases/ELITEA-2335.md` (intake snapshot)
- **Priority**: l3 (case frontmatter `priority: medium`) → **pytest marker `@pytest.mark.p2`**
- **Environment Explored**: local (`http://localhost:5173`, project `Private` / 399, 121 secrets)
- **User set**: `${TEST_USER}`
- **Analyst**: test-automation-engineer (Axel), combined slot, batch `settings-w05`, 2026-08-27
- **Status**: **ready-for-automation**
- **Surface digest**: `test-specs/settings-secrets/_surface.md`
- **Filed**: none for this case — the product matches the case text on every step it can
  be observed on.

## Preconditions
- Project `Private` (399); the case's step 2 needs "any secret row showing a masked
  `{{secret.name}}` value" — **every** row is masked on load (ELITEA-2342), so the
  condition is the page's default state.
- **The test creates its OWN run-unique secret** rather than clicking a real project
  secret's value cell: the case's step 6 requires knowing what "the actual secret value"
  IS, and reading a live shared secret's plaintext into a test process (and into a
  failure message) is both a data-safety and a correctness hazard. The created secret is
  deleted in teardown (API `DELETE`, digest § Cleanup shortcut).

## Test Data
### generate-per-run
- `secret_name`: `autotest_copy_<uuid4-hex[:8]>` (create-flow char class is
  `[A-Za-z0-9_]` only — no hyphens, ELITEA-2337).
- `secret_value`: `copy-test-value-<uuid4-hex[:8]>` — a value **only this run** knows,
  so a stale clipboard entry can never be mistaken for a fresh copy.

## The product's actual copy contract (source + live confirmed 2026-08-27)

`SecretValueCell.jsx` renders the masked template as the **label of an MUI `Button`**;
the button's `onClick` is `handleDirectCopy` (Safari excluded — `isSafari()` renders
the button without a handler and the tooltip switches to "Use copy icon in actions to
copy secret"; Chromium is the automated target, so the handler is live).

`handleDirectCopy`:
1. `await showSecret({projectId, name})` →
   `GET /api/v2/secrets/secret/default/{project_id}/{name}` → **200 OK**, body
   `{"name","secret_name","is_hidden","value"}` (live-confirmed this session:
   `GET …/secret/default/399/autotest_w05_base_a1b2c3d4` → 200).
2. `await copyToClipboard(data.value)` — `navigator.clipboard.writeText`, with an
   `execCommand` fallback (`src/utils/browserUtils.js:56-68`).
3. `toastInfo("The <name> values have been copied.")` on success, or
   `toastInfo("Failed to copy to the clipboard.")` if the write threw.

Live-confirmed toast (captured with a `MutationObserver` on `toast-message` because the
`info` severity auto-hides after **3 s** — `TOAST_DURATION_DEFAULTS.info`):

```
info :: The autotest_w05_base_a1b2c3d4 values have been copied.
```

The masked cell text is **unchanged** by the copy (still `{{secret.<name>}}`) — copying
is not revealing.

### Clipboard readback — live-session limitation, resolved in the automated run
The Playwright **MCP** browser session could not read the clipboard
(`NotAllowedError: Read permission denied` — the MCP context grants no clipboard
permission). The **pytest** context does: `automation/conftest.py:304` passes
`permissions=["clipboard-read", "clipboard-write"]`, and `BasePage.get_clipboard_text()`
/ `clear_clipboard()` already exist and are used by `test_artifacts_file_preview_actions_dropdown.py`
and `test_chat_interface.py`. The clipboard **write** demonstrably succeeded in the live
session (the success toast only fires when `copyToClipboard` resolves), so the only part
of step 5-6 not observed live is the readback itself — asserted for real in the
automated run (see § Implementation outcome).

## Test Steps

1. Navigate to `${BASE_URL}/settings/secrets`; verify the page title is `Secrets`.
   - **Verify**: `secrets-page-title` text == `"Secrets"`.

2. **Setup (not a case step)** — create the run-unique secret via the inline "+" flow;
   verify the create `POST` resolves **201 Created** and its row appears.

3. **(Case step 2)** Locate the created secret's row and verify its Value column shows
   the masked reference.
   - **Verify**: the row's `secret-value-cell` text == `"{{secret." + secret_name + "}}"`.

4. **(Case step 3)** Clear the clipboard (precondition hygiene — never the assertion's
   source), then click the masked value text.
   - **Verify**: the click fires `GET …/secrets/secret/default/{project_id}/{name}`
     → **200**; capture the response body as the **oracle**.

5. **(Case step 4)** Verify the success confirmation appears.
   - **Verify**: `toast-alert` is visible with `data-severity="info"` and `toast-message`
     text == `"The <secret_name> values have been copied."` (exact).

6. **(Case steps 5-6)** Read the clipboard back and verify it holds the **actual secret
   value**, not the masked reference.
   - **Verify**: `clipboard == secret_value` (the value the create flow persisted) **and**
     `clipboard == response.json()["value"]` (the value the server just returned — the
     system is the producer of the asserted value, not the test).
   - **Verify**: `clipboard != "{{secret." + secret_name + "}}"` — the case's explicit
     "not the masked reference" clause, stated as its own assertion so a regression that
     copied the template could never pass by coincidence.

7. **(Axis 2)** Verify the masked cell text is **unchanged** after the copy
   (`{{secret.<name>}}`) — copying must not reveal the value in the table.

8. **(Axis 2)** No unexpected console errors (`#1203` isolated as a soft failure).

**Teardown (mandatory, not a case step):** API `DELETE /secrets/secret/default/{project_id}/{name}`
→ 204.

## Handles Reference

| Element | Primary handle (testid-only) | Provenance | Notes |
|---|---|---|---|
| Page title | `secrets-page-title` | on-`automation/testids` | existing field |
| Add "+" button | `secrets-add-button` | on-`automation/testids` | existing field |
| Name / value inputs | `secret-name-input` / `secret-value-input` | on-`automation/testids` | existing fields |
| Save (✓) | `secret-row-save-button` | on-`automation/testids` | existing field |
| Row | `secret-row` | on-`automation/testids` | `get_row_by_name()` |
| Masked value cell (the click target) | `secret-value-cell` | on-`automation/testids` | existing field; **the clickable element is the wrapping `Button`, but the click lands correctly on the label** (live-confirmed twice this session) |
| Toast container | `toast-alert` (+ `[data-severity="info"]`) | on-`main` — generic `src/components/Toast.jsx:60` | **new `LocatorDescriptor` on `SecretsPage`**, same shared-modal precedent as `delete_confirm_dialog`; `agent_detail_page.py:479-490` is the existing repo pattern |
| Toast message text | `toast-message` | on-`main` — `Toast.jsx:74` | same |

**Zero new testids needed.** No `add-data-testid` work for this case.

## Assertion shape / Fidelity
- The asserted clipboard content is checked against **two system-produced values**: the
  reveal endpoint's own `value` field, and the value the create `POST` persisted. No
  hand-authored payload is the oracle.
- `clear_clipboard()` before the click is **precondition hygiene, not substitution** —
  it removes a stale value so a passing read cannot be a false positive. The value later
  asserted on is written by the product. (Same justification already carried by
  `BasePage.clear_clipboard`'s own docstring and `help_center_page.copy_version_info`.)
- `page.evaluate` appears only inside the pre-existing `BasePage.get_clipboard_text()` /
  `clear_clipboard()` helpers — reading the OS clipboard is the only way to observe the
  case's own observable; nothing about the app's state is injected or fabricated.
  No `page.route`, no `route.fulfill`, no mocked client.

## Implementer notes
- Page-object additions on `SecretsPage`: `toast_alert` / `toast_message`
  `LocatorDescriptor`s + a `TOAST_ALERT_SEVERITY` class constant
  (`'[data-testid="toast-alert"][data-severity="{}"]'`, mirroring
  `agent_detail_page.py`), and `copy_secret_value(row)` which clicks the value cell
  **inside `expect_response`** on `/secrets/secret/default/` and returns the response.
- The `info` toast lives **3 s** — attach the assertion immediately after the click
  (Playwright's web-first `expect` starts polling before the toast mounts). Do NOT
  read it with a one-shot `text_content()`.
- The reveal `GET` and the row-level eye-icon reveal use the **same URL**; this case never
  clicks the eye icon, so a single `expect_response` on that substring is unambiguous.

## Coverage Map

### Axis 1 — every element of the TMS case
| Case element | Expected result (per live product) | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | authenticated session | `auth_state` | fixture | covered |
| Step 1: navigate to Settings → Secrets | page loads | Step 1 | `secrets-page-title` == "Secrets" | asserted |
| Step 2: locate a row with a masked `{{secret.name}}` value | every row is masked; the run-unique row included | Step 3 | value cell == `{{secret.<name>}}` | asserted |
| Step 3: click the masked value text | fires the reveal GET, writes the clipboard | Step 4 | `GET …/secret/default/…` → 200 | asserted |
| Step 4: a success confirmation appears ("Copied!" toast) | `info` toast `The <name> values have been copied.` | Step 5 | `toast-alert[data-severity="info"]` visible + exact `toast-message` text | asserted |
| Step 5: paste the clipboard into a text editor | clipboard readback (the automation equivalent of pasting) | Step 6 | `get_clipboard_text()` | asserted |
| Step 6: the pasted content is the actual secret value, not the masked reference | it is the plaintext | Step 6 | `clipboard == value` (×2 oracles) **and** `clipboard != "{{secret.<name>}}"` | asserted |
| Expected Final State: pasted content is the real value | as step 6 | Step 6 | same | asserted |

### Axis 2 — asserted beyond the case
| Observable | Why |
|---|---|
| the masked cell text is unchanged after the copy | copying must not double as revealing — a real security-relevant regression the case never states |
| the clipboard equals the reveal response's `value` (second, server-side oracle) | proves the UI copied what the server returned rather than any locally-held string |
| create `POST` → 201 before the case's own steps | the case's "any secret row" precondition is made deterministic and run-unique instead of depending on shared data |
| no console errors (`#1203` isolated) | project standard |

## Known Defects / Clarifications
- **#1203 (OPEN)** — React "Maximum update depth exceeded" on `/settings/secrets` mount;
  isolated soft failure, sanctioned-RED signature for every spec on this surface.
- Case-text wording: the case says the toast is "e.g. 'Copied!'" — the live copy is
  `The <name> values have been copied.` The "e.g." makes this an illustration, not a
  contract, so **no clarification is filed**; the AFS asserts the live text exactly.

## Blocked Steps
None.
