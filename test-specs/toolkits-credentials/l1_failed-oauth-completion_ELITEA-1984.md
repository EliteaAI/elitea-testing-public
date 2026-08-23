# Test Case: Credential — Failed OAuth Completion

## Metadata
- **TMS ID**: ELITEA-1984
- **Linked Story**: none
- **Priority**: l1 (case frontmatter: `high`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` → DEV backend `https://dev.elitea.ai/api/v2`), project 399
  "Private" (`Test Bot`)
- **User set**: `${TEST_USER}` (nominal — `auth_state` no-op on localhost)
- **Analyst**: qa-engineer (analyst slot), 2026-08-24
- **Status**: **blocked**
- **Blocked on**: no real OAuth provider test identity (§ Blocked Steps) — a human
  decision: provision one, or rescope the case
- **Filed**: **#1713** (`bug`) — closing the OAuth popup gives no feedback for
  5 minutes (no popup-close detection; generic timeout wording)
- **Cluster**: same surface as ELITEA-1981 / ELITEA-1982 (merged on this trunk,
  `9eb58e08`). Their AFS + `_surface.md` § SharePoint Delegated / OAuth supplied
  the handles; this analysis is the *failure* half of the same dialog.

## Verdict in one line

Executed live end-to-end. Steps 1-4 reproduce perfectly (**Authorize opens exactly
one popup, navigating to the provider's real authorize URL with the invalid scope
carried through verbatim**) — but the case's actual subject, *"the provider denies
authorization and Elitea shows an informative error"*, **cannot be produced against
the real system**: with the placeholder tenant/client the provider answers a bare
**HTTP 404 with an empty body** and never redirects back, so Elitea receives
nothing. Producing a genuine provider *denial* (`error=invalid_scope` redirected to
`/mcp-auth-callback`) needs a **real Entra tenant + registered OAuth app**, which
this project does not have as test data. Per `.agents/testing.md` § Fidelity policy
that is a route-to-human, not a workaround → **blocked**.

## Preconditions (all satisfied live)

- A SharePoint credential, **Delegated** auth, `oauth_discovery_endpoint` +
  `scopes` populated. Seeded through the API exactly as ELITEA-1982 does
  (**declared transit** — the credential is this case's precondition, not its
  observable); observed live as id **3265**, cleaned up after the run.
  ```
  POST /configurations/configurations/399
  {"type":"sharepoint","label":"<name≤32>","elitea_title":"<name>","data":{
     "client_id":"placeholder-client-id","client_secret":"placeholder-client-secret",
     "site_url":"https://contoso.sharepoint.com/sites/test",
     "oauth_discovery_endpoint":"https://login.microsoftonline.com/placeholder-tenant",
     "scopes":["Sites.Read.All"]}}
  ```

## Steps — as executed live (headless Chromium, credential 3265, 2026-08-24)

| # | Action | Expected (case) | **Observed live** | Verdict |
|---|---|---|---|---|
| 1 | Open a SharePoint credential with Delegated auth | detail page loads | `/credentials/all/3265` renders the form, `Delegated` checked | ✅ |
| 2 | Click **Login** | "Configuration OAuth" dialog opens | dialog opens off the real `POST /configurations/check_connection/399/sharepoint` → **401 + `requires_authorization`** | ✅ |
| 3 | Modify scopes to include an invalid scope | Scope field updated | field read `offline_access Sites.Read.All` → cleared + typed → **`Invalid.Scope.xyz`**; **Authorize stays ENABLED** (it is gated on metadata + client creds, never on scope validity) | ✅ |
| 4 | Click **Authorize** | browser redirects to the OAuth provider login page | exactly **one popup** opened, navigated to `https://login.microsoftonline.com/placeholder-tenant/v2.0/oauth2/authorize?response_type=code&client_id=placeholder-client-id&redirect_uri=http%3A%2F%2Flocalhost%3A5173%2Fmcp-auth-callback&state=<32-char random>&scope=Invalid.Scope.xyz`. **The parent page makes no API request** — the whole handshake lives in the popup. Parent dialog flips to `Authorizing…` (Authorize disabled) | ✅ (mechanically) |
| 5 | Verify the OAuth provider shows an error / denies authorization | provider displays an error or access-denied message | **NOT OBSERVABLE.** The popup rendered an **empty body**; the URL answers **HTTP 404, `Content-Length: 0`** (verified independently with `curl` — bare 404, no error page, no `error=` redirect). The rejection is caused by the **placeholder tenant**, not by the invalid scope, so even a non-empty error page would be evidence of the wrong thing | ⛔ **blocked** |
| 6 | Verify Elitea handles the failure gracefully (error message, no crash) | informative error message, no crash | **No crash — and no message.** The provider never redirects back to `/mcp-auth-callback`, so `createAuthorizationMonitor`'s three channels (postMessage / BroadcastChannel / localStorage) never fire. Dialog stays `Authorizing…`. The *only* message is the monitor's **5-minute** fallback `Authorization timed out. Please try again.` — measured at **t+305 s** (silent at +15/+73/+131/+189/+247 s) | ⛔ **blocked** (the case's observable — an error message *about the failure* — is unreachable without a real provider) |
| 7 | Alternatively, click Authorize then cancel/close the OAuth provider page | provider page closed by the user | popup closed programmatically at ~t+10 s; parent unaffected, no crash | ✅ |
| 8 | Verify Elitea shows a message about incomplete/cancelled authorization | message displayed | **NOTHING for 5 minutes.** No popup-close detection exists (`mcpAuthWindow.helpers.js` never polls `authWindow.closed`, though `McpAuthModal` holds the handle in `authWindowRef`). At **t+305 s** the same generic `Authorization timed out. Please try again.` appears and Authorize re-enables — never a *cancellation* message | ❌ **defect — #1713** |

**Side channels:** no console errors across the whole flow apart from the expected
`check_connection` **401** (ELITEA-1982's own oracle; Chromium logs every non-2xx
fetch). No unhandled rejection, no React error boundary, no navigation away.
**Cancel remains functional throughout the frozen `Authorizing…` window**, so the
user is never trapped — which is why #1713 is a UX gap, not a hang.

Evidence: `automation/test-results/screenshots/ELITEA-1984-step-04-parent-after-authorize.png`,
`…-step-05-provider-error.png`, `…-step-08-after-popup-close.png`,
`…-step-08b-after-5min.png` (the last two also uploaded to the `evidence` release
and embedded in #1713).

## Blocked Steps — exactly what could not be produced

| Case element | What is missing | Who unblocks it |
|---|---|---|
| Step 5 — "the provider shows an error or denies authorization" | A **real OAuth provider identity**: an Entra/Microsoft tenant + a registered OAuth application whose redirect URI includes `http://localhost:5173/mcp-auth-callback` (and the deployed-env equivalent), plus a user account able to consent. With the placeholder tenant the provider returns a bare 404 and never reaches a consent/denial screen | human — provision the tenant/app as test data (à la `GIT_HUB_TOKEN`), or rescope the case |
| Step 6 — "Elitea displays an informative error message" | The same. Elitea's error path is **implemented** (`createAuthorizationMonitor.handleAuthResult` surfaces `data.error_description \|\| data.error` in the dialog's error box) but is only reachable when the provider **redirects back** with `error=invalid_scope`. That redirect requires a real registered client | human — same decision |

Both are **terminal** for this case: the observables in steps 5-6 are the case's
subject, so simulating them (`route.fulfill` of the callback, `postMessage` injection
into the parent, a fake provider at a stub URL) would be a **terminal substitution**
— forbidden by `.agents/testing.md` § Fidelity policy, and the case text nowhere asks
for simulation ("Verify the OAuth provider shows an error…" is an instruction to
observe the real provider).

## What IS honestly automatable today — if a human rescopes the case

Recorded so a rescope needs no second exploration. Everything below was observed live
in this run and needs **no** provider identity:

1. **Steps 1-4 as a "failure-path entry" spec** — invalid scope typed into the dialog,
   Authorize enabled, exactly one popup, and the popup's **authorize URL asserted
   field-by-field**: host = the credential's `oauth_discovery_endpoint`,
   `response_type=code`, `client_id` = the credential's own, `redirect_uri` =
   `{base}/mcp-auth-callback`, a non-empty `state`, and **`scope=Invalid.Scope.xyz`**
   — i.e. the product faithfully carries the user-edited scope into the request. That
   is a real, valuable assertion produced entirely by the product.
2. **The graceful-degradation contract** — after the popup dies the app does not crash:
   dialog still visible, `Authorizing…`, no console errors, **Cancel still works and
   closes the dialog**.
3. **The 5-minute timeout message** — reachable, but a spec asserting it costs **>5 min
   of wall clock** per run, i.e. >15 min across the 3× merge gate. Not worth it as a
   standalone; if wanted, assert it once with a generous timeout and `p3`/`slow`.

Cost note for whoever rescopes: the probe that produced this AFS ran **321 s**, almost
all of it waiting for the timeout.

## Handles Reference

Provenance verified 2026-08-24 after `cd ../EliteaUI && git fetch origin`.
**Nothing new is needed — the whole tree was testid'd for ELITEA-1982.**

| Purpose | Handle | Provenance |
|---|---|---|
| Login button (opens the dialog) | `credential-form-oauth-login-button` | `automation/testids` only (EliteaAI/EliteaUI@7d7b21d4) — awaiting human cherry-pick to `main` |
| Dialog root / title / description / server link | `oauth-auth-dialog`, `-title`, `-description`, `-server-link` | same commit; **assert visibility, never count** (`keepMounted`) |
| Scope input (step 3 edits it) | `oauth-auth-dialog-scope-input` | same commit — supplied to the shared `OAuthFormFields` via the caller-side `scopeTestId` prop |
| Cancel / Authorize | `oauth-auth-dialog-cancel-button` / `oauth-auth-dialog-authorize-button` | same commit. `Authorize`'s label flips to `Authorizing…` while in flight — read the **state** with `to_be_disabled()`, never a text-keyed locator |
| The error / timeout message box | **needs-adding** — `oauth-auth-dialog-error` on `McpAuthModal.jsx:454-467` (the `authError` block) | only required if a rescoped case asserts the timeout/error text (§ What IS honestly automatable, item 3). Not added by this analysis — canon #511: no test executes it yet |
| The provider page | **third-party** — assert the popup's **URL**, never its DOM | `page.expect_popup()`; per `.agents/testing.md` § Locator policy the provider's markup is outside `EliteaUI/src` and gets no testid |

Page objects already exist and need no change: `CredentialDetailPage.open_by_id()`,
`CredentialFormFieldsMixin.oauth_login_button`, `pages/oauth_auth_modal_page.py`
(`OAuthAuthModalPage`). A rescoped spec would only add a `press_sequentially` on the
scope field and a popup-URL assertion.

## Waits & settling

- `networkidle` is unusable on `/credentials/**` — settle on
  `GET /configurations/configuration/399/{id}` (`open_by_id` already does).
- Login → dialog: wrap in `expect_response` on `**/configurations/check_connection/**`
  (401), then `expect(dialog).to_be_visible()`. ~1 s.
- Authorize → popup: `with page.expect_popup() as pi:` — the popup appears
  synchronously (`window.open` is `onAuthorize`'s first act). The **parent makes no
  request**, so a request-count wait would hang forever.
- Do **not** wait on the popup's `load` — a 404 with an empty body settles instantly
  but carries nothing to wait for.

## Coverage Map

### Axis 1 — every element of the case

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | — | `auth_state` | setup | covered |
| Precondition: SharePoint Delegated credential exists | — | API seed (declared transit) + `Delegated` checked on the detail form | setup | covered |
| Step 1 Open the credential | detail page loads | `open_by_id` settle + form assertions | Step 1 | covered |
| Step 2 Click Login | dialog opens | `check_connection` 401 + dialog visible | Step 2 | covered |
| Step 3 Invalid scope typed | field updated | input value == `Invalid.Scope.xyz` | Step 3 | covered |
| Step 4 Click Authorize | redirect to provider | one popup; authorize-URL parameters incl. the edited scope | Step 4 | covered |
| **Step 5 Provider shows an error / denies** | provider error message | — | — | **blocked** (no provider identity; bare 404, and the invalid *scope* is not the cause) |
| **Step 6 Elitea shows an informative error, no crash** | error message, no crash | *no-crash half* observable; *error-message half* unreachable | — | **blocked** (split element — see § Blocked Steps) |
| Step 7 Close the provider page | page closed | popup `close()` | Step 7 | covered |
| **Step 8 Message about incomplete/cancelled authorization** | message displayed | — | — | **defect #1713** — nothing for 5 min, then a generic timeout message |
| Expected Final State: both flows handled gracefully with appropriate messages | — | partially — no crash in either flow; **no appropriate message in either** | — | blocked + defect |
| Pass criterion "no crashes" | — | dialog alive, Cancel functional, zero console errors | Steps 4-8 | covered |
| Pass criterion "clear, user-friendly error/informational messages" | — | — | — | **fails today** (#1713); for the *failed* flow, unverifiable without a provider identity |

### Axis 2 — observables asserted beyond the case

| Extra observable | Why |
|---|---|
| The authorize URL's `scope` parameter equals the user-edited value | the only *honest* proof that the product carried the invalid scope to the provider — the mechanism step 3-4 exist to exercise |
| The parent page issues **no** API request on Authorize | documents that a request-based guard is meaningless on this flow (the ELITEA-1982 fix-round lesson) — protects the next author from a hanging wait |
| Cancel still closes the dialog while `Authorizing…` | separates "no feedback" (#1713) from "user trapped" — a real hang would be a far higher severity |

## Known Defects

- **#1713** (filed by this analysis) — closing the OAuth popup gives no feedback for
  5 minutes; the eventual message is a generic timeout, never a cancellation notice.
  Root cause: `createAuthorizationMonitor` never polls `authWindow.closed`. Shared
  dialog → the same gap affects the MCP / toolkit / OpenAPI OAuth flows.
- No other defect. No crash, no console error, no stuck app state.
