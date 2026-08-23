---
name: Credential form — schema-typed fields commit on BLUR, not on keystrokes
description: Typing with real keys is not enough on array-typed credential fields; Save stays disabled until the field blurs
type: feedback
aliases: [save button disabled, scopes field, enableAutoBlur, formik dirty credential, sharepoint delegated save]
tags: [area/credentials, type/gotcha]
created: 2026-08-24
updated: 2026-08-24
---

## The fact

`credential-form-save-button` is gated on `hasErrors || !useFormDirtyExcluding()`
(`CredentialsTabBar.jsx:115`). The known half of this is that Playwright `fill()`
leaves formik non-dirty — hence `set_display_name()`'s select-all + type.

The half that costs a rerun: on **schema-typed** fields the typed value only
reaches form state on **blur**. SharePoint's `scopes` is `array`-typed and the
shared `Input`/`InputBase` renderer runs with `enableAutoBlur`, so with focus
still in `scopes` Save stays **disabled** no matter how many characters were
typed — the required-field check still reads the field as empty.

Measured on ELITEA-1981 (2026-08-24, localhost:5173):

| State | Save |
|---|---|
| App-only fields filled (client_id / client_secret / site_url) | enabled |
| after selecting the **Delegated** radio | disabled |
| after typing oauth_discovery_endpoint + scopes, focus still in scopes | disabled |
| after `scopes.blur()` (or any click that blurs it — e.g. the Auto Refresh Token checkbox) | **enabled** |

## What to do

`CredentialFormFieldsMixin.type_into_field()` blurs after typing — use it for
any schema-driven credential field and don't "optimise" the blur away. Reading
the Save button's state immediately after a `press_sequentially` on the last
field is the failure shape.

Sibling gotcha on the same flow: `McpAuthModal` renders `<Dialog keepMounted>`, so the
OAuth dialog is always in the DOM — assert visibility, never a count.
