---
name: JS evaluate-click silently no-ops on a disabled control
description: locator.evaluate("el => el.click()") on a disabled button does nothing and raises nothing — never use it on a validation-gated control; a real click() auto-waits for enabled and fails at the true point
type: feedback
---

## The rule

`locator.evaluate("el => el.click()")` dispatches a DOM click that a
**disabled** button ignores: no handler, no request, no navigation, **and no
exception**. Playwright's own `locator.click()` auto-waits for the element to be
*enabled* and raises `TimeoutError` if it never becomes so.

So an evaluate-click on any control whose enabled-ness is the product's own
validation signal **deletes the one check that could catch the fault**, and the
test dies several steps later on an unrelated-looking assertion.

## Where this bit us — #1897 / ELITEA-1140

`test_create_credential[jira]`/`[confluence]` failed nightly on DEV with
`Credential 'AutoTest Jira …' not found via API` (Step 7). Root cause was two
steps upstream:

- Step 5 used `save_btn.evaluate("el => el.click()")` on a Save button that was
  **disabled** because a required field was empty → silent no-op, allure step
  `passed`.
- Step 6's guard `assert "/credentials" in page.url` was **vacuous** — true on
  `/credentials/create-credential/jira`, the URL the browser never left.

Negative control (repaired shape, required field wiped before Save, DEV):

```
E   AssertionError: Locator expected to be enabled
E   Actual value: disabled
E     - waiting for get_by_test_id("credential-form-save-button")
```

versus the pre-repair shape under the identical condition: Steps 5 **and** 6
both `passed`, failing only at Step 7 with the misleading API message.

## The two rules that follow

1. **Never evaluate-click a validation-gated control.** Use
   `expect(btn).to_be_enabled()` + a real `btn.click()`.
2. **A URL guard must not be satisfied by the page you are trying to leave.**
   `assert "/credentials" in page.url` is vacuous when the origin URL is
   `/credentials/create-credential/...`. Use
   `page.wait_for_url(re.compile(r".*/credentials/all/?(\?.*)?$"))`.

## Scope — this does NOT retire the evaluate-click workaround

[[mui_menu_stays_open_backdrop_intercepts_outside_clicks]] and
`AgentFormPage.click_save()` legitimately use it to defeat a **pointer-event
interception** (a high-z-index MUI backdrop over an *enabled* element). That
stays valid. The line is: JS click to beat an **overlay**, never to beat a
**disabled state** — and if you cannot tell which one you are beating, use the
real click and read the error.
