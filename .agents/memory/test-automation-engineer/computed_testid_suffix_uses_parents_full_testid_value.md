---
name: Computed testId suffix uses the PARENT's full testId value, not a guessed base name
description: "${testId}-icon"-style computed testids resolve off the actual testId prop string passed at the call site — verify it, don't assume a shorter base
type: feedback
---

## The trap

When a shared component threads a sub-element's testid off its own `testId`
prop via a template (`data-testid={testId ? \`${testId}-icon\` : undefined}`),
the resulting value is `${the actual string passed at THIS call site}-icon` —
not `${some shorter/cleaner name you'd expect}-icon`.

Concretely (ELITEA-2195, `AttachmentButton.jsx`): the popper call site passes
`testId="chat-attach-menuitem-button"` (note: ends in `-button`, matching the
element's own `chat-attach-menuitem-button` testid, which was itself named
after the *button* element, not the abstract "attach menuitem" concept). The
icon Box's `data-testid={testId ? \`${testId}-icon\` : undefined}` therefore
resolves to `chat-attach-menuitem-button-icon` — **not**
`chat-attach-menuitem-icon`. Guessing the shorter form (which reads more
naturally) produced a `LocatorDescriptor` that silently matched nothing —
`Locator.wait_for` timed out at 10s with no other symptom.

## The fix

After adding a computed-suffix testid, **read back the actual rendered DOM**
(`page.evaluate` inspection, or a snapshot) and copy the literal resulting
string into the `LocatorDescriptor` — never derive it by re-reading the JSX
and mentally concatenating. One live check (`btn.outerHTML` via
`browser_evaluate`) caught this in under a minute; the pytest failure alone
(`TimeoutError`) gives no hint that the mismatch is a naming bug vs. a real
HMR/render problem.

## When you hit this again

Any time you thread a testid via `${somePropVariable}-suffix` (or similar
string-building) rather than a hardcoded literal: grep the call site for the
EXACT string passed to that prop first, compute the suffix by hand, and verify
against the live DOM before writing the `LocatorDescriptor` — don't trust the
"obvious" shorter name.
