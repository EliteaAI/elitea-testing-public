# Test Case: Credential — OAuth Authorization Modal Invocation

## Metadata
- **TMS ID**: ELITEA-1982
- **Linked Story**: none
- **Priority**: l1 (case frontmatter: `high`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` @ `2706969d` → DEV backend `https://dev.elitea.ai/api/v2`),
  project 399 "Private" (`Test Bot`)
- **User set**: `${TEST_USER}` (nominal — `auth_state` no-op on localhost)
- **Analyst**: qa-engineer (analyst slot), 2026-08-23
- **Status**: **ready-for-automation**
- **Filed**: none for this case (no product defect; no case-text drift found —
  every one of the nine steps matched the live product verbatim)
- **Cluster**: analysed in one live session with ELITEA-1981. Separate AFS files
  — rationale in ELITEA-1981's AFS § Cluster note.

## Verdict in one line

Executed end-to-end in a clean browser context: Login opens the **Configuration
OAuth** dialog off a real backend handshake, every displayed value matches the
case text exactly (including the `offline_access` prefix), and Cancel closes it
without any further request. The only work needed is **testids** — the whole
`McpAuthModal` + `OAuthFormFields` tree currently has none.

## Preconditions

- A SharePoint credential with Delegated auth, `oauth_discovery_endpoint` and
  `scopes` populated. Created live during this analysis as id **3247**
  (`xautotest_sp_deleg_1`, project 399).
- **Seed it via API — declared transit, not a fidelity violation.** The
  credential is this case's *precondition*, not its observable (contrast
  ELITEA-1981, where the UI create flow IS the subject); the case's own
  observable — the dialog and its contents — is still produced by the live
  product from a real `check_connection` round trip.
  ```
  POST /configurations/configurations/399
  {"type":"sharepoint","label":"<name≤32>","elitea_title":"<name>","data":{
     "client_id":"placeholder-client-id","client_secret":"placeholder-secret",
     "site_url":"https://contoso.sharepoint.com/sites/test",
     "oauth_discovery_endpoint":"https://login.microsoftonline.com/placeholder-tenant",
     "scopes":["Sites.Read.All"]}}
  ```
  Placeholder values are sufficient — the backend still returns a full
  `auth_metadata` (§ Backend contract). Clean up with
  `DELETE /configurations/configuration/399/{id}`.
  *(Building the precondition through the UI is also possible — that is
  ELITEA-1981 — but it costs a full create flow for a precondition.)*

## Steps — as executed live (clean browser context, credential 3247)

| # | Action | Expected (case) | **Observed live** | Verdict |
|---|---|---|---|---|
| 1 | Open an existing SharePoint Delegated credential | detail page loads | `/credentials/all/3247` renders the form; `Delegated` checked; `oauth_discovery_endpoint` = `https://login.microsoftonline.com/placeholder-tenant`, `scopes` = `Sites.Read.All` | ✅ |
| 2 | Verify **Login** next to **Test connection** | Login visible | both present, adjacent in the same `testConnectionContainer` box | ✅ |
| 3 | Click **Login** | "Configuration OAuth" dialog appears | `POST /configurations/check_connection/399/sharepoint` fires → **401 + `requires_authorization`** → dialog becomes visible. Title read live: **`Configuration OAuth`** | ✅ |
| 4 | Message "This MCP server requires OAuth authorization to access its tools." | displayed | **exact match**, no trailing flow hint (the `requiresClientSecret`/`oidc`/`dcr`/`pkce` suffix is empty for this server) | ✅ |
| 5 | `Server:` shows the Oauth Discovery Endpoint as a clickable link | link populated | `href` **and** text both = `https://login.microsoftonline.com/placeholder-tenant`, `target="_blank" rel="noopener noreferrer"`. (Note: this is the *discovery endpoint*, deliberately passed as the display URL by `useCreateConfiguration.jsx:183`, **not** `auth_metadata.server_url`, which is the SharePoint **site** URL.) | ✅ |
| 6 | Scope pre-populated with credential scopes prefixed by `offline_access` | `offline_access <scopes>` | **`offline_access Sites.Read.All`**. The prefix is **backend-sourced**, not a UI concat: `resource_metadata.scopes_supported` / `provided_settings.scopes` come back `["offline_access","Sites.Read.All"]` for a credential whose own `scopes` is `["Sites.Read.All"]` — **and do so regardless of `auto_refresh_token`** (probed true and false, identical). `McpAuthModal.jsx:70` prefers those `resourceScopes` over the form scopes. | ✅ |
| 7 | Scope placeholder `Enter OAuth scopes (space-separated)` | correct when empty | attribute matches exactly; clearing the field renders it | ✅ |
| 8 | `Cancel` and `Authorize` present | both visible | both present. **`Authorize` is ENABLED** in this configuration (the server advertises an authorization endpoint and no client secret is required, so `isAuthorizeDisabled` is false). The dialog renders **one** input — the Scope field only; Client Id / Client Secret inputs are conditional (`needClientId` / `needsClientSecret`) and do **not** render here. | ✅ |
| 9 | Click **Cancel** | dialog closes without taking any action | dialog hidden; **no further POST** in the 2 s after the click (only the step-3 `check_connection` in the whole session) | ✅ |

**No console errors** over the whole flow — **amended during implementation
(2026-08-24): with one expected exception.** Chromium logs every non-2xx fetch
as a console error, so the case's own `check_connection` **401** (the oracle
that opens the dialog) surfaces as `Failed to load resource: the server
responded with a status of 401 (Unauthorized)`. The implemented side channel
filters exactly that one, matched by the failing resource's own `location.url`
(`/configurations/check_connection/`) plus the 401 status — never by "401"
alone, so any other 401 still fails.

## ⚠️ The one trap on this surface — `keepMounted`

`McpAuthModal` renders `<Dialog open={open} keepMounted>` (`McpAuthModal.jsx:370`),
so **`[role="dialog"]` is always in the DOM**, open or not. Worse, a *closed*
instance holds pre-open state: the `Server:` link reads `href=""` and the Scope
input shows the raw credential scopes **without** the `offline_access` prefix —
i.e. it mimics exactly the failure mode steps 5 and 6 are looking for. This cost
this analysis a detour and two retracted issue filings.

- Open: `expect(dialog).to_be_visible()` — **never** `to_have_count(1)`.
- Closed (step 9): `expect(dialog).not_to_be_visible()` — **never**
  `to_have_count(0)`.
- Scope the dialog locator with `.filter(has_text="Configuration OAuth")` or
  `:visible`; a bare `[role="dialog"]` can match a hidden sibling modal
  (`McpLogoutModal` is also mounted on this page).

## Backend contract (the honest oracle for steps 5-6)

```
POST /configurations/check_connection/399/sharepoint   (credential 3247's data)
→ 401
{"success": false, "requires_authorization": true,
 "auth_metadata": {
   "server_url": "https://contoso.sharepoint.com/sites/test",
   "resource_metadata": {
     "authorization_servers": ["https://login.microsoftonline.com/placeholder-tenant"],
     "oauth_authorization_server": {"authorization_endpoint": …, "token_endpoint": …,
                                    "scopes_supported": ["offline_access","Sites.Read.All"]},
     "scopes_supported": ["offline_access","Sites.Read.All"],
     "provided_settings": {"scopes": ["offline_access","Sites.Read.All"]}}}}
```

Recommended shape (per `.agents/testing.md` § How to test a nondeterministic
producer): capture this **real** response via `expect_response` on the
`check_connection` POST and assert the dialog against **it** —
`scope_value == " ".join(body["auth_metadata"]["resource_metadata"]["scopes_supported"])`
— rather than against a hard-coded string. Deterministic, and every value still
comes from the product. Assert the literal `offline_access ` prefix too, since
that is what the case actually asks about. **No `route.fulfill` anywhere** — the
handshake is real and cheap (~1 s).

## Handles Reference

Provenance verified 2026-08-23 after `cd ../EliteaUI && git fetch origin`.
Everything inside the dialog is **needs-adding** — the modal tree has zero
testids today.

| Purpose | Handle | Provenance |
|---|---|---|
| Detail-form fields (precondition assertions) | `toolkit-field-oauth_discovery_endpoint-input`, `toolkit-field-scopes-input`, `toolkit-field-auth-radio-delegated` | on-main ✓ / `automation/testids` (radio, EliteaAI/EliteaUI@c8d5c6af) |
| Test connection (the "next to" anchor) | `credential-form-test-connection-button` | on `automation/testids` (EliteaAI/EliteaUI@5892ae48) |
| **Login button (trigger)** | **testid needed: `credential-form-oauth-login-button`** | needs-adding — `CredentialForm.jsx:342-350`; one attribute (`Button.BaseBtn` spreads `restProps`). **Shared with ELITEA-1981 — add once.** |
| **Dialog container** | **testid needed: `oauth-auth-dialog`** | needs-adding — `McpAuthModal.jsx:369` `<Dialog>`. Pair with a **visibility** assertion (keepMounted, above). |
| **Dialog title** | **testid needed: `oauth-auth-dialog-title`** | needs-adding — `:380` `DialogTitle` |
| **Description paragraph** | **testid needed: `oauth-auth-dialog-description`** | needs-adding — `:397` `Typography` |
| **`Server:` value link** | **testid needed: `oauth-auth-dialog-server-link`** | needs-adding — `:425` MUI `Link`; assert `href` **and** text |
| **Scope input** | **testid needed — caller-supplied prop, e.g. `scopeTestId` → `oauth-auth-dialog-scope-input`** | needs-adding — `OAuthFormFields.jsx:66-70`. `OAuthFormFields` is a **shared** component (`[fsd]/features/mcp/ui/modal/`, also used by the MCP flows), so per `.agents/testing.md` § shared components it must take a **caller-supplied `testId`-style prop** wired at `McpAuthModal`'s call site — never a hardcoded credential-scoped string inside the shared component. Prop naming: `scopeTestId`, **not** `dataScopeTestId`. |
| **Cancel / Authorize** | **testids needed: `oauth-auth-dialog-cancel-button` / `oauth-auth-dialog-authorize-button`** | needs-adding — `:478-492` `DialogActions` |
| Close (X) icon button | **do NOT add** | canon #511 — this case cancels via the Cancel button; the X is never on the executed path |
| Client Id / Client Secret inputs | **do NOT add** | they do not render in this configuration (`needClientId`/`needsClientSecret` false) — untouched by this case |

`Authorize`'s enabled state is read with `to_be_enabled()` on its stable testid —
no state-switched testid (`.agents/testing.md` § Locator policy).

**Zero-functional-impact check for the implementer:** every testid above is a
plain attribute on an element that already exists. No new DOM node, no MUI
built-in replaced, no hook added — `add-data-testid` § Step 5.5 greps must come
back empty.

## Page-object notes for the implementer

- Put the Login button on `CredentialFormFieldsMixin` (shared by the create and
  detail routes — digest § `CredentialFormFieldsMixin` now owns the shared
  `CredentialForm.jsx` handles), so ELITEA-1981 gets it for free.
- The dialog deserves its own page object (`pages/oauth_auth_modal_page.py`), not
  fields bolted onto `CredentialDetailPage` — `McpAuthModal` is shared with the
  MCP/toolkit flows and the next case on it should reuse the object.
- Class-level `LocatorDescriptor(testid=…)` only; the visibility-vs-presence
  discipline above belongs in the page object's methods
  (`wait_for_open()` / `wait_for_closed()`), not in the spec.

## Waits & settling

- `networkidle` is unusable on `/credentials/**` — settle the detail route on
  `GET /configurations/configuration/399/{id}`.
- Step 3: wrap the Login click in `expect_response` on
  `**/configurations/check_connection/399/sharepoint` (returns 401 — assert the
  status explicitly so a silent 200 can't pass), then
  `expect(dialog).to_be_visible()`. Round trip observed ~1 s.
- Step 9: `expect(dialog).not_to_be_visible()`; for "no action taken", assert no
  additional matching request fired (collect requests, compare before/after) —
  the case names no other observable for it.

## Coverage Map

### Axis 1 — every element of the case

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | — | `auth_state` | setup | covered |
| Precondition: SharePoint Delegated credential with endpoint + scopes configured | — | API-seeded fixture (**declared transit**) + assertion that the detail form shows `Delegated` checked with both values | setup / Step 1 | covered |
| Step 1 Open the credential | detail page loads | detail GET settle + field round-trip assertions | Step 1 | covered |
| Step 2 Login present next to Test connection | Login visible | visibility of both buttons | Step 2 | covered |
| Step 3 Click Login → dialog appears | "Configuration OAuth" dialog | `expect_response(check_connection)` 401 + `to_be_visible()` + title text | Step 3 | covered |
| Step 4 Message text | message displayed | exact-text assertion on the description | Step 4 | covered |
| Step 5 `Server:` = endpoint, as a link | link populated | `href` **and** text, both vs the credential's own `oauth_discovery_endpoint` | Step 5 | covered |
| Step 6 Scope pre-populated `offline_access …` | scope value | input value vs the **captured response**'s `scopes_supported`, plus an explicit `startswith("offline_access ")` | Step 6 | covered |
| Step 7 Scope placeholder when empty | placeholder correct | clear the field, assert `placeholder` attribute + empty value | Step 7 | covered |
| Step 8 Cancel + Authorize present | both visible | visibility of both (+ `Authorize` enabled) | Step 8 | covered |
| Step 9 Cancel closes without action | dialog closed, no action | `not_to_be_visible()` + no further `check_connection`/OAuth request | Step 9 | covered |
| Expected Final State | dialog opens with pre-populated server + scope; Cancel dismisses without authorizing | steps 3-9 | Steps 3-9 | covered |
| Pass criterion "Cancel does not trigger an authorization attempt" | no auth attempt | request-absence assertion in step 9 | Step 9 | covered |

### Axis 2 — observables asserted beyond the case

| Extra observable | Why |
|---|---|
| `check_connection` returns **401** with `requires_authorization` | proves the dialog was opened by the real backend handshake and not by some other code path — the honest oracle a `route.fulfill` would have destroyed |
| `Authorize` **enabled** at open | it is enabled in this configuration; asserting it deliberately stops a silent future flip (e.g. a metadata regression that leaves the button dead) from passing unnoticed |
| Exactly one input renders in the dialog (Scope only) | the Client Id / Client Secret fields are conditional; a regression that starts demanding them would change the flow the case describes without failing any text assertion |
| No console errors across the flow | standard side channel; clean apart from the browser's own log line for the expected `check_connection` 401, filtered endpoint-specifically (amended 2026-08-24) |

## Known Defects

None. The flow is clean end-to-end.

**Retracted, for the record:** #1710 (and its sibling #1709) were filed by this
analysis and then **retracted as not reproducible** — artifacts of a wedged
Playwright-MCP browser context in which no click produced a React update.
Disproved by the merged `test_credential_create.py` (green) and by re-running
this exact scenario in a fresh `browser.new_context()`, which produced every ✅
in the step table above. Nothing here depends on them.
