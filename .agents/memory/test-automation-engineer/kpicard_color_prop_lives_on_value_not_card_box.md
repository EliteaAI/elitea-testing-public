---
name: KpiCard color prop lives on value node, not card Box
description: A conditional color prop on a shared card component only affects the inner value Typography — testid the value node, not the card wrapper, or the negative-branch assertion is a no-op
type: feedback
---

## The trap

`KpiCard.jsx` (`EliteaUI/src/[fsd]/features/settings/ui/analytics/components/`)
takes an optional `color` prop and applies it ONLY to the value `Typography`'s
`sx`: `sx={[styles.kpiValue, color ? { color } : {}]}`. The card's outer `Box`
(`styles.kpiCard`) sets no `color` at all.

An AFS (ELITEA-2313) originally specced testid-ing the card `Box` and reading
`to_have_css("color", ...)` on it to assert the "9 non-Errors cards stay
default-colored" negative branch. Live-verified via `getComputedStyle` this is
a **no-op assertion**: the card's own computed color is constant across ALL 10
cards (`rgb(169, 183, 193)`, an inherited/ambient value) regardless of the
Errors branch — it never reflects the value node's explicit `color` override.
A real color-prop regression on ANY card would still pass this check.

## Fix

When a shared card/row component applies a conditional `color`/style prop to
one INNER element (not the outer wrapper), testid that inner element
specifically — not the container. Here: added a uniform
`valueTestId`/`analytics-user-detail-kpi-value` prop wired on the value
`Typography`, passed on ALL 10 call sites (same index order as the card list),
not just the Errors one. `expect(values.nth(i)).to_have_css("color", ...)`
against the value node is the only check that actually exercises the
component's conditional-color logic.

## General check before shipping a "verify default state on the other N
siblings" assertion

Before writing a negative-branch color/style check, grep the component's
`styles` object for where the conditional prop's `sx` actually lands. If it's
not on the element you're about to testid, the assertion will pass whether or
not the logic is broken.
