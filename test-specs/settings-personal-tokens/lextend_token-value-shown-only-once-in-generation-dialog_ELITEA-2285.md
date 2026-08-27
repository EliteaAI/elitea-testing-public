# Test Case (extension): Token value is shown only once in the generation dialog

## Metadata
- **TMS ID**: ELITEA-2285
- **Source case**: `.agents/automation/settings-w04/cases/ELITEA-2285.md` (intake snapshot)
- **Priority**: l3 (case frontmatter `priority: medium`) → **pytest marker `@pytest.mark.p2`**
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids` → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}` = 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), batch `settings-w04`, cluster session
  (ELITEA-2285/2289/2290/2291), 2026-08-27
- **Status**: **extend-existing**
- **Covering spec**: `automation/tests/ui/admin/test_personal_token_create_and_verify.py:63`
  — `TestPersonalTokenCreateAndVerify::test_create_personal_token_and_verify_in_table`
  (ELITEA-2280), **merged to `origin/automation/base`** (verified 2026-08-27 with
  `git fetch origin` + `git cat-file -e origin/automation/base:<path>`).
- **Surface digest**: `test-specs/settings-personal-tokens/_surface.md`
- **Filed**: **#1886** — case-text CLARIFICATION (`question` label). The case's Step 7
  premise is stale; see § The case text is wrong about the eye icon.
- **Testid work**: **1 testid, shared with ELITEA-2291** —
  `token-settings-preview-content`. See § Handles Reference and the sequencing note.

## Behavioural overlap — what the covering spec already proves

`test_create_personal_token_and_verify_in_table` runs the identical flow and already
asserts, hard, everything this case's Steps 1-6 ask for:

| ELITEA-2285 step | Already asserted by the covering spec |
|---|---|
| 1 — Navigate to Settings → Personal Tokens and click "+" | its Steps 1-3 (`/settings/create-personal-token` reached, "New Token" title, empty name field, `Days`/`30` defaults) |
| 2 — Enter a name and expiration, click "Generate" | its Steps 4-5 (name accepted, Generate flips disabled→enabled, `POST /api/v2/auth/token/` → 200) |
| 3 — Full token value displayed in the "New token generated!" dialog | its Steps 6-8 (dialog title exact, warning text exact, entered name shown, **non-empty token value captured**, name rendered above value) |
| 4 — "Copy" button present; click it; success confirmation appears | its Step 9 (toast text exact, button text flips to `Copied!`, button becomes disabled, **clipboard content == the token value**) |
| 5 — Close the dialog | its Step 10 (close → back on `/settings/tokens`) |
| 6 — Token value column shows a masked `...XXXX` value | its Step 11 (`token-value-cell` text == `"..." + token_value[-4:]`, built from the captured value) |

That is 6 of 7 steps, asserted more strongly than the case asks. Re-implementing them as
a fresh spec would duplicate an entire merged test to add one observation. Hence
`extend-existing`, not `ready-for-automation`.

## The gap — Step 7, and why it needs rewriting before it can be asserted

> **Case Step 7** — *Verify there is no way to retrieve the full token value again
> **except via the eye icon**.*

### The case text is wrong about the eye icon

Verified live 2026-08-27 with a token whose full value was captured from the dialog
(226-char JWT ending `…7FrjdGrGvQ`):

| Surface | Value shown |
|---|---|
| "New token generated!" dialog | the full JWT `eyJhbGciOiJI…7FrjdGrGvQ` |
| Token value column, after the dialog closes | `...rGvQ` |
| **Eye icon → Settings Preview** (`eliteacode.authToken`) | **`...jdGrGvQ`** — masked, **not** the full token |
| VSCode row download (`settings.json`) | `...jdGrGvQ` |
| Full JWT anywhere in the page after the dialog closes | **absent** — `document.body.innerText` and the full `document.documentElement.innerHTML` both scanned: no match |

`GET /api/v2/auth/token/` returns the token **already masked** — that is why
`TokensTable.jsx:119` can build the display mask as
`'...' + row.token.substring(row.token.length - 4)` (a mask of a mask). No client surface
holds the full value once the dialog closes.

**Reverse-masking guard applied** (`test-case-analysis` § Classify findings): the product
is **stricter** than the case — the case permits one later retrieval path, the product
permits none, and the case's own title ("shown only once") is thereby satisfied more
completely. This is case-text drift, **not** a product defect. Asserting the case text as
written would encode a weaker contract than the product honours. Filed as clarification
**#1886**; this AFS asserts the **live** contract.

## Preconditions
- Unchanged from the covering spec — it already creates its own token and captures the
  full value into `token_value`, which is exactly the oracle this extension needs.
- **`showDownload` must be true** for the eye icon to render
  (`!!model.configuration_uid && selectedProjectId !== PUBLIC_PROJECT_ID`,
  `PersonalTokens.jsx:267`) — true on project 399. Guard it, don't assume it.

## Gap assertions

Append to `test_create_personal_token_and_verify_in_table`, **after its existing Step 11**
(masked value asserted) and **before its Step 12** (expiration status) or after it — the
order is the implementer's call; the token row and `token_value` are in scope throughout.
Each gets its own `with allure.step("Step N — …"):` block, numbered to continue the
existing sequence.

1. **Gap Step A — the full token is gone from the page once the dialog is closed.**
   - **Verify**: `token_value not in page.content()` — the full JWT appears nowhere in the
     rendered document (attributes included, which is why `page.content()` rather than a
     text-only read).
   - **Verify**: `generated-token-dialog-token-value` has count **0** (the dialog really
     unmounted, so the assertion above is not passing merely because it is off-screen).

2. **Gap Step B — the eye icon does not reveal it either (the corrected Step 7).**
   Open the Settings Preview for the created row:
   `get_row_action_icon(row, "token-action-preview-button").click()`.
   - **Verify (precondition guard)**: `token-action-preview-button` exists on the row
     before clicking — `showDownload` true. Absent ⇒ fail loudly with that reason.
   - **Verify**: `token-settings-preview-content` becomes visible.
   - **Verify**: reading the panel body with **`inner_text()`**, `token_value not in body`
     — the preview does **not** expose the full token.
   - **Verify**: `body` *does* contain the masked form the product does expose — assert
     `'"eliteacode.authToken": "..."' `-shaped presence via a parse:
     `json.loads(body)["eliteacode.authToken"].startswith("...")` **and**
     `json.loads(body)["eliteacode.authToken"].endswith(token_value[-4:])`.
     This is the positive half: the panel shows *a* value, and it is the mask **of this
     token** — so the assertion cannot pass against an empty or unrelated field.
   - Close the panel (`token-settings-preview-close-button`) so the spec's existing
     `finally:` cleanup runs against an unobstructed table.

3. **Gap Step C — the masking survives a reload (the full value is never re-served).**
   `page.reload()` + wait for the token-list GET.
   - **Verify**: the row's `token-value-cell` text is still `"..." + token_value[-4:]`.
   - **Verify**: `token_value not in page.content()`.

**Nothing here is soft-asserted** — the product passes every one of these. The two open
defects on this surface (#1884 masked token in the VSCode download, #1885 empty
`integrationUid` in the preview) are owned by the ELITEA-2289 and ELITEA-2291 AFS
respectively and are deliberately **not** re-asserted here: duplicating them would give
one product cause two reds and would make this case sanctioned-RED for a defect it does
not test.

## Handles Reference

| Element | Handle (testid) | Page-object member | PROVENANCE |
|---|---|---|---|
| Generated-dialog token value | `generated-token-dialog-token-value` | `CreatePersonalTokenPage.dialog_token_value` | on-main ✓ |
| Generated-dialog copy button | `generated-token-dialog-copy-button` | `dialog_copy_button` | on-main ✓ |
| Generated-dialog close (X) | `generated-token-dialog-close-button` | `dialog_close_button` / `close_dialog()` | on-main ✓ |
| Token row (repeatable) | `token-row` | `PersonalTokensPage.token_row` | on-main ✓ |
| Row name cell | `token-name-cell` | `TOKEN_NAME_CELL_SELECTOR` / `get_row_name_cell()` | on-main ✓ |
| Row value cell (masked) | `token-value-cell` | `TOKEN_VALUE_CELL_SELECTOR` / `get_row_value_cell()` | on-main ✓ |
| Row eye (preview) icon | `token-action-preview-button` | `get_row_action_icon(row, ...)` | on-main ✓ |
| Preview body (CodeMirror content) | `token-settings-preview-content` | **new** `LocatorDescriptor` | **needs-adding** |
| Preview close (X) button | `token-settings-preview-close-button` | **new** `LocatorDescriptor` | **needs-adding** |

Provenance verified 2026-08-27 with `cd ../EliteaUI && git fetch origin` + the two-stage
`git grep` from `.agents/workflow.md` § Closure record against **both** `origin/main` and
`origin/automation/testids` — full output pasted in the ELITEA-2291 AFS's
§ Handles Reference. Every `on-main ✓` row above returned `main:YES testids:YES`;
`token-settings-preview-content` returned `main:no testids:no`.

### ⚠️ Shared testid dependency — sequencing note for the lead

The two `needs-adding` handles are the **same testids the ELITEA-2291 AFS specs** (that
AFS defines all seven `token-settings-preview-*` testids and their exact call-site
mechanisms — `contentTestId` on `Field.CodeMirrorEditor`, plain `data-testid` on the MUI
`IconButton`). Both cases are in batch `settings-w04`.

- If ELITEA-2291 is built first, this extension consumes the testids and page-object
  fields it added — **no EliteaUI change at all here**.
- If this one is built first, add the two testids per the ELITEA-2291 AFS's
  § Testid work table (identical names, identical mechanism) so ELITEA-2291 inherits them.
- Either way `add-data-testid` is idempotent — verify presence before adding, never add a
  second variant name.

## Automation Hints

- Target: **extend** `automation/tests/ui/admin/test_personal_token_create_and_verify.py`,
  method `test_create_personal_token_and_verify_in_table`. Do **not** write a new spec —
  the whole point of the `extend-existing` verdict is that its Steps 1-11 already are this
  case's Steps 1-6, and `token_value` is already in scope.
- Update that method's module/class docstring `AFS:` reference to name this file
  alongside the ELITEA-2280 one (the file's existing convention — see its lines 15 and 25,
  which already document the ELITEA-2284 extension the same way).
- Page object: add the two `token-settings-preview-*` class-level `LocatorDescriptor`
  fields to `automation/pages/personal_tokens_page.py` if ELITEA-2291 has not already.
- **Read the preview body with `inner_text()`, not `text_content()`** — CodeMirror renders
  each line as its own `<div>` and `text_content()` concatenates them with no separator,
  so the result will not parse as JSON.
- The existing `finally:` cleanup already deletes the created token; Gap Step B must close
  the preview pane before it runs, or the trash icon may be behind the split pane.
- **Never `sleep`.** The preview close is behind a 50 ms `setTimeout`
  (`PersonalTokens.jsx:143-149`) — use auto-retrying expectations.
- **No substitution.** Every value asserted here is produced by the product; the oracle
  (`token_value`) comes from the product's own dialog. Do not fabricate a token, do not
  `route.fulfill` the token list, do not inject state.

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` (localhost `VITE_DEV_TOKEN`) | fixture | covered (existing) |
| Step 1 — Navigate to Settings → Personal Tokens and click "+" | Page loads | covering spec Steps 1-3 | `test_personal_token_create_and_verify.py` Steps 1-3 | covered by merged spec |
| Step 2 — Enter a name and expiration, click "Generate" | Field accepts input, displays value | covering spec Steps 4-5 | same file, Steps 4-5 + `POST` 200 | covered by merged spec |
| Step 3 — Full token value displayed in the "New token generated!" dialog | Condition holds | covering spec Steps 6-8 | same file, Steps 6-8 | covered by merged spec |
| Step 4 — "Copy" button present; click; success confirmation appears | Condition holds | covering spec Step 9 | same file, Step 9 (toast + `Copied!` + disabled + clipboard) | covered by merged spec |
| Step 5 — Close the dialog | Completes, expected UI state | covering spec Step 10 | same file, Step 10 | covered by merged spec |
| Step 6 — Token value column shows a masked `...XXXX` value | Condition holds | covering spec Step 11 | same file, Step 11 | covered by merged spec |
| Step 7 — No way to retrieve the full token again **except via the eye icon** | Condition holds | **Gap Steps A + B** | full JWT absent from `page.content()`; preview body does not contain it and shows the mask of this token | **covered — asserted against the CORRECTED contract; case text filed as clarification #1886** |
| Expected Final State — same as Step 7 | — | Gap Steps A + B + C | same, plus survival across a reload | covered |

### Axis 2 — observables asserted BEYOND the case

| Extra observable | Why it is grounded |
|---|---|
| `generated-token-dialog-token-value` count 0 after close | Gap Step A's "the JWT is nowhere in the page" would also pass if the dialog were merely hidden with the value still in the DOM — this pins that it unmounted, so the absence assertion is meaningful rather than incidental. |
| The preview shows the **mask of this token** (prefix `...`, suffix == last 4 of the real value) | A bare "the full token is not in the preview" passes against an empty field, a crashed panel, or an unrelated token. Asserting the positive form makes the test fail if the panel stops rendering the field at all — the realistic regression. |
| Masking survives a page reload (Gap Step C) | The case's claim is about *retrieval*, not about one render. A reload re-fetches from the API — the only path by which a full value could come back — so this is the assertion that actually tests the server's contract rather than a client-side render. |
| `showDownload` precondition guard before Gap Step B | Page-level boolean; when false the eye icon does not exist and the step would fail as an opaque locator timeout instead of naming the real cause. |

## Known Defects

None asserted by this extension — the product passes every gap assertion.

Two open defects were found on this surface during the same session and are owned
elsewhere, deliberately not re-asserted here:
- **#1884** — VSCode download/preview embed the masked token (owned by the ELITEA-2289
  family AFS, which has the full token in scope).
- **#1885** — preview `integrationUid` always `""` (owned by the ELITEA-2291 AFS).

And one case-text clarification:
- **#1886** — ELITEA-2285's Step 7 "except via the eye icon" is stale; the eye icon does
  not retrieve the full token. Requested rewording is in the issue.

## Blocked Steps
None.
