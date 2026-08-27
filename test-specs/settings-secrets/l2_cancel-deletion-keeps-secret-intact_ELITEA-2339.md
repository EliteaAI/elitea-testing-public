# Test Case: Cancel deletion keeps the secret intact

## Metadata
- **TMS ID**: ELITEA-2339
- **Source case**: `.agents/automation/settings-w05/cases/ELITEA-2339.md` (intake snapshot)
- **Priority**: l2 (case frontmatter `priority: high`) → **pytest marker `@pytest.mark.p1`**
- **Environment Explored**: local (`http://localhost:5173`, project `Private` / 399)
- **User set**: `${TEST_USER}`
- **Analyst**: test-automation-engineer (Axel), combined slot, batch `settings-w05`, 2026-08-27
- **Status**: **ready-for-automation**
- **Surface digest**: `test-specs/settings-secrets/_surface.md`
- **Filed**: none — the product matches the case text on every step.

## Preconditions
- Project `Private` (399) with ≥ 1 secret (121 live).
- **The test creates its OWN run-unique secret and cancels the deletion of THAT one.**
  The digest is explicit (§ Delete flow): never open the dots menu on a real/pre-existing
  secret — all three menu items are `disabled={isDefault}` for system secrets, and a
  mis-click on a real one would corrupt shared project data.

## Test Data
### generate-per-run
- `secret_name`: `autotest_cancel_del_<uuid4-hex[:8]>` (`[A-Za-z0-9_]` only).
- `secret_value`: `cancel-delete-value-<uuid4-hex[:8]>`.

## The product's actual cancel contract (source + live confirmed 2026-08-27)

- Row dots menu (`secret-row-actions-button`) → `SecretActionsMenu.jsx`: exactly
  `Edit value` / `Hide` / `Delete`, testids `secret-actions-menu-*`.
- `Delete` opens the SHARED `Modal.DeleteEntityModal`:
  - `delete-confirm-dialog` (root), title `Delete confirmation`
  - `delete-confirm-message` — live text confirmed **verbatim**:
    `Are you sure to delete the <name>? Enter the name to complete the action.`
  - `delete-confirm-button` — **`disabled: true`** on open (type-to-confirm gate)
  - `delete-confirm-cancel-button` — label `Cancel`
- **Cancel is purely client-side**: after clicking it, `[data-testid="delete-confirm-dialog"]`
  and `[role="dialog"]` are both gone, the row is still rendered with its **unchanged**
  masked value, and the filtered pagination info still reads `1 - 1 of 1`. Verified live
  by a `browser_network_requests` read immediately after: the only secrets-endpoint call
  in that window was the later, deliberate reveal `GET` — **zero `DELETE` requests fired**.

## Test Steps

1. Navigate to `${BASE_URL}/settings/secrets`; verify the page title is `Secrets`.

2. **Setup (not a case step)** — create the run-unique secret via the inline "+" flow;
   verify the create `POST` resolves **201 Created** and its row appears; record the
   row's rendered masked value.

3. **(Case step 2)** Open the created row's three-dot menu and click **Delete**.
   - **Verify**: the menu items are exactly `["Edit value", "Hide", "Delete"]`, in order
     (the case says "three-dot menu → Delete"; asserting the item set makes the click
     target unambiguous rather than positional).

4. **(Case step 3)** Verify a confirmation dialog appears.
   - **Verify**: `delete-confirm-dialog` is visible **and** `delete-confirm-message` text
     is exactly `Are you sure to delete the <secret_name>? Enter the name to complete the
     action.` — the dialog must be the one for *this* secret, not merely "a dialog".
   - **Verify (Axis 2)**: `delete-confirm-button` is **disabled** before anything is typed.

5. **(Case step 4)** Click **Cancel**, **while watching the network**.
   - **Verify**: the dialog closes (`delete-confirm-dialog` count 0).
   - **Verify (Axis 2)**: **no `DELETE` request** to `/secrets/secret/default/` was issued
     during the cancel — the case's "keeps the secret intact" claim is about the *system*,
     and a UI-only check cannot distinguish "nothing was deleted" from "deleted, list not
     refreshed yet".

6. **(Case step 5)** Verify the secret remains in the table **unchanged**.
   - **Verify**: the row for `secret_name` still has count 1.
   - **Verify**: its `secret-name-cell` text is unchanged (`== secret_name`) and its
     `secret-value-cell` text is unchanged (`== "{{secret." + secret_name + "}}"`) — the
     case says "unchanged", not merely "present".

7. **(Axis 2)** Reload the page and re-assert the row is still present with the same
   name/value — a genuine server round-trip, so a client-cache-only survival cannot pass
   (same double-check discipline as ELITEA-2338's delete flow).

8. **(Axis 2)** No unexpected console errors (`#1203` isolated as a soft failure).

**Teardown (mandatory, not a case step):** API `DELETE /secrets/secret/default/{project_id}/{name}`
→ 204. This case's own steps deliberately do NOT delete the secret (that is the point),
so teardown must.

## Handles Reference

| Element | Primary handle (testid-only) | Provenance | Notes |
|---|---|---|---|
| Page title / add button | `secrets-page-title` / `secrets-add-button` | on-`automation/testids` | existing fields |
| Name / value inputs, Save (✓) | `secret-name-input` / `secret-value-input` / `secret-row-save-button` | on-`automation/testids` | existing fields |
| Row / name cell / value cell | `secret-row` / `secret-name-cell` / `secret-value-cell` | on-`automation/testids` | existing fields |
| Row dots menu button | `secret-row-actions-button` | on-`automation/testids` (EliteaAI/EliteaUI@dd47b184) | existing field |
| Menu item Delete | `secret-actions-menu-delete` | on-`automation/testids` (same commit) | existing field |
| Delete dialog root / message | `delete-confirm-dialog` / `delete-confirm-message` | on-`main` — shared `DeleteEntityModal.jsx` | existing fields |
| Delete dialog Delete button | `delete-confirm-button` | on-`main` | existing field |
| **Delete dialog Cancel button** | `delete-confirm-cancel-button` | on-`main` — shared modal | existing `LocatorDescriptor`, **no method yet** — add `cancel_delete()` |

**Zero new testids needed.** No `add-data-testid` work for this case.

## Assertion shape / Fidelity
Every asserted value is produced by the system: the create `POST`'s 201, the rendered
row text, the absence of a `DELETE` request on the wire, and the post-reload re-read.
No `page.route`, no `route.fulfill`, no injected state, no mocked client.

## Implementer notes
- Page-object addition on `SecretsPage`: `cancel_delete()` — click
  `delete_confirm_cancel_button` and wait for `delete_confirm_dialog` to detach. Additive
  only; `confirm_delete()` and every other existing method stay byte-identical.
- Use `open_row_actions_menu(row)` **unconditionally** — its React-`onClick` workaround is
  a safe superset; the digest records the menu-open non-determinism across four sessions
  (`#1222`, OPEN) and warns against simplifying it to a plain click on the strength of one
  green session. (This session's own two menu opens both succeeded with a plain click —
  a fifth data point, still not a resolution.)
- The "no DELETE fired" assertion is best expressed as a request listener collected over
  the cancel window (`page.expect_request` would *wait* for one, which is backwards) —
  attach `page.on("request", …)` filtered on method `DELETE` + the endpoint substring,
  and assert the collected list is empty.
- Filter the table with `secrets-search-input` to the run-unique name before opening the
  menu: the project holds 121 secrets across 13 pages and `secret-row-actions-button` is
  rendered per row.

## Coverage Map

### Axis 1 — every element of the TMS case
| Case element | Expected result (per live product) | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | authenticated session | `auth_state` | fixture | covered |
| Step 1: navigate to Settings → Secrets | page loads | Step 1 | `secrets-page-title` == "Secrets" | asserted |
| Step 2: three-dot menu → Delete on a secret | menu opens with 3 items; Delete opens the modal | Step 3 | menu item texts == `["Edit value","Hide","Delete"]` | asserted |
| Step 3: a confirmation dialog appears | shared type-to-confirm modal, named for this secret | Step 4 | `delete-confirm-dialog` visible + exact `delete-confirm-message` | asserted |
| Step 4: click Cancel | dialog closes, no server call | Step 5 | dialog count 0 + zero `DELETE` requests | asserted |
| Step 5: the secret remains in the table unchanged | row present, name + masked value identical | Step 6 | row count 1 + name-cell + value-cell equality | asserted |
| Expected Final State: secret remains unchanged | as step 5, and after a reload | Steps 6-7 | same, re-asserted post-reload | asserted |

### Axis 2 — asserted beyond the case
| Observable | Why |
|---|---|
| `delete-confirm-button` is disabled before typing | the modal's own safety gate; a regression that pre-enabled it would make an accidental confirm one click away, and the case never checks it |
| zero `DELETE` requests during the cancel | "intact" is a claim about the system; the DOM alone cannot distinguish "not deleted" from "deleted but not refetched" |
| post-reload re-assertion | proves server-side survival, not client-cache survival |
| masked value unchanged (not just row present) | the case says "unchanged" |
| no console errors (`#1203` isolated) | project standard |

## Known Defects / Clarifications
- **#1203 (OPEN)** — React "Maximum update depth exceeded" on mount; isolated soft failure.
- **#1222 (OPEN)** — three-dot menu open is non-deterministic under automation; mitigated
  by the existing `open_row_actions_menu()` workaround, not asserted here.

> **Implementation outcome (2026-08-27, `test_secret_cancel_deletion_keeps_secret.py`):**
> every functional assertion PASSED on the first run — dialog copy exact, Delete button
> disabled before typing, **zero DELETE requests** across the whole flow, row + masked
> value unchanged before and after a reload. `open_row_actions_menu()`'s workaround was
> used unconditionally and worked. `#1203` fired **35 times**, so the spec is
> **sanctioned-RED** on that one signature.

## Blocked Steps
None.
