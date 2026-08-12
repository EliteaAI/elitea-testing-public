---
name: InviteUserDialog error state re-validates live once already true
description: InviteUserDialog.jsx validation is blur-gated ONLY while error is false; once error=true, a useEffect keyed on [error, inputText] re-validates on every keystroke. Typing a second example into the SAME open dialog after the first errored breaks a "no error yet before blur" assertion for the wrong reason.
type: feedback
---

## What happened (ELITEA-2307)

`InviteUserDialog.jsx`'s `handleBlur` is the only place that calls
`parseEmails` while `error === false` — matching the AFS's "blur-gated, not
live-as-you-type" hint. BUT there's a second effect:

```js
useEffect(() => {
  if (error) {
    const { containInvalidEmail } = validateEmails(
      inputText.split(',').map(i => i.trim()).filter(Boolean),
    );
    setError(containInvalidEmail);
  }
}, [error, inputText]);
```

Once `error` flips `true` (from a prior blur), this effect re-validates on
**every** `inputText` change — i.e. live-as-you-type, no blur needed. So
testing two invalid-email examples in the SAME open dialog (type A, blur,
assert error; type B, assert "no error yet") fails on B's "no error yet"
assertion — not because B's validation broke, but because A's leftover
`error=true` state makes B's field react live.

## Fix

Reopen the dialog between examples (`Escape` then `open_invite_dialog()`
again) — `InviteUserDialog`'s own `if (!open) {...}` effect resets
`inputText`/`emails`/`error`/`helperText`/`selectedRoles` to a clean slate.
This matches how the AFS's own live exploration confirmed each example:
"alone", i.e. against a fresh dialog, not sequentially in one session.

## Where

`automation/tests/ui/admin/test_invite_user_invalid_email_validation.py`,
`automation/pages/admin_users_page.py` (`type_email_in_invite_dialog` /
`blur_invite_emails_field` split into two atomic methods specifically so a
caller can assert in between — a single combined "type-and-blur" helper
would hide this exact pitfall).
