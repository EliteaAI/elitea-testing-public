---
name: FSD entities-layer shared component testid scope gap
description: role-overrides' shared-component testid rule names only src/components/ and src/[fsd]/shared/ — entities/ components shared across features aren't literally covered
type: feedback
---

## What happened (ELITEA-2600 review, PR #1468)

New testid `agent-publish-terms-content` was added to
`src/[fsd]/entities/version/ui/PublishingTerms.jsx` in EliteaUI. This
component (via its sole caller `PreparationStep.jsx`, itself the sole child
of `PublishWizardModal.jsx`) is genuinely shared between the **agent**-publish
flow (`usePublishVersion*.hooks`) and the **skill**-publish flow
(`usePublishSkill*.hooks`) — confirmed by grepping both call-site families.
Despite that, the call site hardcodes an `agent-publish-*` prefixed testid
unconditionally (two pre-existing siblings already did this before ELITEA-2600:
`agent-publish-category-select`, `agent-publish-agree-checkbox`), so a
skill-publish-wizard render also carries an `agent-publish-*` testid.

This is exactly the shape `.agents/role-overrides.md` § Reviewer slot warns
about — "a feature-scoped testid hardcoded in a shared component" — **except
the rule's directory list is `src/components/` and `src/[fsd]/shared/`
only.** `src/[fsd]/entities/**` (FSD "entities" layer) isn't named, even
though an entities-layer component can be just as cross-feature-shared as one
under `shared/`. Literal-text reading of the rule would say this doesn't
trigger; the *principle* the rule exists for clearly does apply.

## What I did as reviewer

Treated it as a **declared improvisation** (`.agents/role-overrides.md` §
Every role — declared-improvisation protocol): the implementer explicitly
named the shared-ness and the precedent in both the AFS "Implementer
amendments" section and the `publish_terms_content` LocatorDescriptor
docstring. Verified the precedent claim live (grepped both call-site
families, confirmed 2 pre-existing siblings at the same call site already use
the same prefix). Did not block — reasoning is sound and the naming decision
is consistent with what's already shipped at that exact call site — but
flagged it as a `question` finding recommending the canon's directory list be
widened to cover `src/[fsd]/entities/**` (or reworded to be shape-based —
"any component with >1 distinct feature call site" — rather than a fixed
directory allowlist that entities-layer code slips through).

## Takeaway for the next reviewer/implementer

Don't stop at "is this path literally `src/components/` or
`src/[fsd]/shared/`?" when judging a shared-component testid. Check actual
call sites (`grep -rln "<ComponentName>" src/`) — an `entities/` (or any
other FSD layer) component with 2+ distinct feature consumers is shared in
every way that matters, even though the current rule text doesn't name that
directory.
