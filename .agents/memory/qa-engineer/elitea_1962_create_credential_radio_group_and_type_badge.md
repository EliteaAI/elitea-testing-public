---
name: ELITEA-1962 create-credential — Auth radio group testid pattern + type-badge handle
description: Shared RadioButtonGroup.jsx had zero testids (5 consumers); added opt-in testId prop wired only at the credential Auth call site; entity-card-tag-chip already exists for list type badges; zero-credential project auto-redirects past the list+"+" button entirely
type: feedback
---

## Shared `RadioButtonGroup.jsx` (`src/[fsd]/shared/ui/checkbox/`) had zero distinguishing testids

Used by 5 features: credential/toolkit Auth-method section (`ToolSection.jsx`),
index-schedule modal, pipeline schedule/webhook modals, LLM max-tokens section. All
options rendered from a `.map(item => ...)` with only generic, repeated MUI icon
testids (`RadioButtonUncheckedIcon`/`RadioButtonCheckedIcon`) and a shared
`name="radio-buttons-group"` — zero way to target one option.

Fix pattern (per the shared-component testid ruling — generic testid OR
caller-supplied `testId` prop, never feature-scoped inside the shared component):
added an **optional** `testId` prop to `RadioButtonGroup`, templated per-option as
`${testId}-${item.value.toLowerCase().replace(/\s+/g,'-')}`, left `undefined` (no-op)
unless a caller passes it. Wired it at exactly ONE call site — `ToolSection.jsx`'s
Auth-section render — as `testId={`toolkit-field-${sectionKey}-radio`}`. The other 4
callers are untouched (no testid noise on elements no test yet touches, per the
team's "scope is load-bearing" ruling). Landed: `toolkit-field-auth-radio-token`,
`-none` (NOT `-anonymous` — **label text ≠ underlying value**, "Anonymous" option's
`item.value` is literally `"none"`), `-password`, `-app-private-key`.

Committed `EliteaAI/EliteaUI@c8d5c6af` on `automation/testids`. If another case needs
a different `RadioButtonGroup` consumer (schedule modals, max-tokens section)
testid'd, follow the same pattern — pass `testId` at THAT call site, don't assume
the credential wiring covers it (it doesn't; it's opt-in per caller by design).

## `entity-card-tag-chip` already exists — don't re-add it

The Credentials list card's type badge (e.g. "Github" text next to the pin button)
already carries `data-testid="entity-card-tag-chip"` — pre-existing, shared
`Card.jsx` testid (same family as `entity-card`/`entity-card-name`, reused across
Applications/Pipelines/Toolkits/Credentials list pages). No `add-data-testid` work
needed for any case asserting a list-page type badge. Verified live:
`<span data-testid="entity-card-tag-chip"><span>Github</span></span>` nested inside
the matched `entity-card`.

## Zero-credential project auto-redirects past the list page + "+" button entirely

`/credentials/all` on a project with ZERO existing credentials auto-redirects
straight to `/credentials/create-credential` (`CredentialsList.jsx`'s "Navigate to
New Credential page for private projects with no credentials" effect — pre-existing,
already noted in `credential_create_page.py`'s docstring from ELITEA-1963, but not
previously in memory). Any case whose steps require the list page to render, or the
sidebar `sidebar-create-button` ("+" button) to be clickable, needs ≥1 credential
seeded first (API-created, cheapest) — otherwise steps 1–2 of a "navigate to list →
click +" flow have nothing to act on. Not a defect; reverse-masking guard applies if
a case's text assumes the list always renders.
