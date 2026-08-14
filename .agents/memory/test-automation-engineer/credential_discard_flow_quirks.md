---
name: Credential discard-flow quirks (implementer)
description: DiscardButton/BaseModal testid wiring pattern, MUI Dialog testid landing on the outer wrapper not role=dialog, a Ctrl+A select-all failure on the credential label field (use select_text() instead), and a filed CredentialsList mount-race crash (elitea-testing-public#518)
type: feedback
---

## Context
ELITEA-1971 (Credential — Discard Changes). New page object
`automation/pages/credential_detail_page.py` + test
`automation/tests/ui/toolkits/test_credential_discard_changes.py`.

## Testid wiring pattern (reusable)
`DiscardButton.jsx` (shared by Agents/Skills/Toolkits/Pipelines/Applications/
Credentials — many callers) already rendered `Modal.BaseModal`, which already
supported `data-testid`/`confirmButtonDataTestId` props — but `DiscardButton`
never forwarded anything to it. Same "capability existed, wiring gap" shape
as ELITEA-1915's `GenerateEntityModal`. Fix: add 3 new optional props
(`dataTestId`, `modalDataTestId`, `confirmButtonDataTestId`) to
`DiscardButton`, all `undefined` by default, forwarded to the trigger
`BaseBtn` and to `Modal.BaseModal`. Only the credential call site
(`CredentialsTabBar.jsx`) supplies concrete values — every other
`Button.DiscardButton` caller is unaffected (verified via
`git diff <file> | grep -E '^-[^-]'` — empty on both files).

**The credential-list card needed no new testid at all** — before running
`add-data-testid`, check whether the element already has one via the shared
component it's rendered through. `src/components/Card.jsx` (`EntityCard`,
used by every card-rendered list page: Applications, Pipelines, Toolkits,
Credentials, ...) already carries `data-testid="entity-card"` +
`data-testid="entity-card-name"`. The AFS claimed "zero testid, plain
`div[cursor=pointer]`" — that was stale/wrong; always re-verify a
"testid needed" claim against the actual current source before wiring a new
one, especially for a widely-shared list-card component.

## MUI Dialog testid lands on the wrapper, not role="dialog"
`<Dialog data-testid={x}>` (MUI) puts the attribute on the outer
`role="presentation"` div (`.MuiDialog-root`/`.MuiModal-root`), NOT on the
inner Paper element that carries `role="dialog"`. Confirmed via
`document.querySelector('[data-testid="..."]').outerHTML`. `get_by_test_id()`
finds it fine either way (attribute search, not role search) — but don't
assume a `role=dialog`-based ref from a snapshot search is the same DOM node
the testid landed on if you're cross-referencing the two.

## Ctrl+A does NOT reliably select-all on this app — use select_text()
`.claude/rules/mui-patterns.md`'s documented pattern
(`field.click(); field.press("Control+a"); field.type(...)`) **silently
failed** on the credential Display Name field
(`toolkit-field-label-input`). Live-verified via
`el.evaluate("el => ({s: el.selectionStart, e: el.selectionEnd})")`:
after `Control+a`, `selectionStart === selectionEnd === 0` — the caret moved
to position 0 WITHOUT selecting anything (something in the app intercepts or
rewrites the Ctrl+A keydown). Subsequent typing then PREPENDED instead of
replacing, producing a corrupted-but-plausible-looking value
(`"autotesautotest_debug_..."` — first N chars of the new value glued onto
the untouched old value), which reads exactly like a flaky/wrong assertion
rather than an input-mechanics bug unless you check the raw selection state.

**Fix:** `field.click(); field.select_text(); field.type(value)` — Playwright's
`select_text()` sets the DOM selection directly (`setSelectionRange`), which
is immune to whatever eats the Ctrl+A keydown. Verified via the same
`selectionStart/selectionEnd` eval (`0, 25` after `select_text()` on a
25-char value) before trusting it.

**Action for a future case:** if you hit an MUI field where the documented
Ctrl+A recipe doesn't visibly replace the old value, don't assume it's a
one-off — check `selectionStart`/`selectionEnd` via eval first, and default
to `select_text()` over `press("Control+a")` for full-field replacement on
this app generally. Consider escalating this to amend
`.claude/rules/mui-patterns.md` if a second case reproduces it on an
unrelated field (would confirm it's not specific to this one component).

## Filed defect: /credentials/all mount-race crash
`CredentialsList.jsx`'s mount effect calls `onRefetch()` TWICE unconditionally
when `pathname === DEFAULT_CREDENTIALS_PATHNAME` (i.e. exactly the
`/credentials/all` entry point). `useLoadCredentials.js`'s underlying RTK
Query `refetch()` throws "Cannot refetch a query that has not been started
yet" if the query hasn't started, which trips React Router's default error
boundary and crashes the ENTIRE page (~60% reproduction rate observed across
10 runs). Root cause is source-confirmed, NOT React-StrictMode-specific (the
double call is unconditional, not just a dev double-invoke artifact) — filed
as **elitea-testing-public#518** with the full stack trace and a suggested
fix (guard on `isUninitialized` before calling `refetch()`, or drop the
duplicate call).

This is out of scope for any Discard-flow assertion, so it is NOT masked in
the test. `CredentialDetailPage.open_credential_by_name()` calls
`_recover_from_credentials_list_crash()` right after navigating — detects the
"Unexpected Application Error!" boundary text and reloads once (documented,
links #518) before proceeding. Any future case that navigates to
`/credentials/all` directly should call this same recovery (or inherit
`CredentialDetailPage`) rather than re-discovering the flake independently.
Also: scope any console-error side-channel assertion to start AFTER this
recovery point, not from test start — otherwise the recovered-from error's
console log will fail an otherwise-correct "zero console errors" check on the
in-scope flow.
