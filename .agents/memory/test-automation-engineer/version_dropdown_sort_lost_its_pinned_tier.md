---
name: Version dropdown sort lost its pinned-first tier (EliteaUI #857)
description: Version selector sorts by created_at desc with base always last; the pin icon no longer implies position
type: project
aliases: [version select order, pinned version sort, version-option-pin-icon, VersionSelect comparator, default version position]
tags: [area/agents, area/skills, type/product-change]
created: 2026-08-27
updated: 2026-08-27
---

## What changed

EliteaAI/EliteaUI@cf648e9a ("Feat/el 6302/enhancement of version select", PR
EliteaAI/EliteaUI#857, merged to EliteaUI `main` 2026-08-27) **deleted the pinned-first tier**
from `src/[fsd]/entities/version/ui/VersionSelect.jsx`'s comparator — the two
`defaultVersionID` early returns are gone, leaving the source comment
*"Default version stays in its chronological position — not pinned to top."*

**Current rule:** `[every version by created_at DESCENDING] → [base ALWAYS last]`.
No pinned tier. No Published/Draft status tier either (that one never existed — #1091).

**The pin icon was deliberately KEPT** (`VersionIconBlock.jsx`, `data-testid="version-option-pin-icon"`,
`aria-label="Default version"`) and is now the *sole* indicator of the default version.
**Position and pin are fully decoupled** — `base` is routinely pinned AND last at the same time.
Live-verified order for a base→v1→v2(published)→v3 sequence, identical before and after re-pinning v1:
`['v3-latest-draft', 'v2-published', 'v1-early-draft', 'base']`.

## Three traps this creates for tests

1. **`version-option-` is no longer a safe bare prefix.** #857 added a hover
   "set as default" affordance carrying `data-testid="version-option-set-default-{name}"`.
   A naive `[data-testid^="version-option-"]` order-read counts it as an option.
   `AgentDetailPage.VERSION_OPTION_ANY` already excludes it (and the nested pin icon) —
   reuse that constant, never re-derive the prefix selector.
2. **The pin icon does not render on a PUBLISHED default version.** `VersionIconBlock`
   checks `status === 'published'` FIRST and returns a publish icon, so
   `is_version_option_pinned()` is False for a published default. Not a bug.
3. **Option text is now name+meta concatenated with NO separator.** `VersionSelectOption.jsx`
   renders name and meta as sibling `Typography` nodes, so `text_content()` yields e.g.
   `"baseAug 13, 2026, 11:15 · by Test Bot"`. Meta shape (`version.helpers.jsx`'s
   `formatVersionMeta`) is `"{Mon DD, YYYY, HH:MM} · by {author}"`; the author segment always
   renders (`author_name` → `author_email` → literal `"Author unavailable"`).
   The old `"{name} - {DD.MM.YYYY}"` shape is gone.

## The right repair shape

Replacing `order[0] == pinned_name` with `order[-1] == "base"` and
`order == order_before_repin` is **stronger** than what it replaced: the base-last claim is now
asserted against a *pinned* base (the case that used to contradict it), and the
order-stability claim is a differential across two live reads that a single-snapshot
assertion could never make.

Related: [[afs_is_a_work_order_not_gospel]]
