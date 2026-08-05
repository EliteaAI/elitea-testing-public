---
name: Disabled-button multi-gate assertion isolation
description: A `disabled={A || B || C}` assertion only proves the gate under test if the others are pre-satisfied
type: feedback
---

Many MUI/EliteaUI confirm/submit buttons gate `disabled` on an OR of several
independent conditions, e.g. `InviteUserDialog.jsx`:

```jsx
disabled={!emails.length || !selectedRoles.length || error}
```

An assertion like `expect(confirm_button).to_be_disabled()`, written to prove
"the button stays disabled while the *email validation* error is showing," is
**meaningless on its own** if another gate in the expression (here,
`!selectedRoles.length` — no role ever selected) is ALSO true throughout the
test. The assertion passes, but it proves nothing about the gate it claims to
exercise — it would pass identically even if `error` were always `false`.

**Before writing a "button (still) disabled" assertion as evidence of a
specific validation state:**

1. Read the component source for the full `disabled` boolean expression.
2. Identify every gate in it.
3. Pre-satisfy every gate EXCEPT the one under test, so the assertion's
   pass/fail is driven purely by that one condition.
4. If pre-satisfying a gate requires an action the case's own steps never
   mention (e.g. selecting a role for an email-validation case), that's fine
   — it's dialog-setup *technique*, not a scope change, as long as the
   case's own steps/expected-results stay untouched.

Caught at review (ELITEA-2307 fix round 1, PR #1183) — first-pass
implementation asserted the Invite button disabled at Step 2 (no emails) and
Step 4 (invalid-email error) without ever selecting a role, so both
assertions were trivially true via the role gate regardless of the emails/
error state they were meant to isolate.
