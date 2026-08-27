---
name: Version selector no longer sorts the pinned/default version first
description: EliteaUI PR #857 (EL-6302) removed the pinned-first tier; base is always last, pin is icon-only
type: project
aliases: [version selector order, pinned version, default_version_id, VersionSelect comparator, version-option-pin-icon]
tags: [area/agents, area/versions, type/product-change]
created: 2026-08-27
updated: 2026-08-27
---

## The change

EliteaUI `cf648e9a` — "Feat/el 6302/enhancement of version select (#857)", 2026-08-27,
on `main` and `automation/testids` — **deliberately deleted** the pinned-first tier from
`src/[fsd]/entities/version/ui/VersionSelect.jsx`'s `versionSelectOptions` comparator:

```diff
-      if (a.id === defaultVersionID) return -1;
-      if (b.id === defaultVersionID) return 1;
```

and replaced it with an authored comment:
`// Sort: newest first by created_at; base always last.`
`// Default version stays in its chronological position — not pinned to top.`

**Current rule:** `[everything by created_at DESC] → [base ALWAYS last]`. There is no
pinned tier and no Published/Draft status tier. Pinning a version does not reorder the list.

## What still holds

- A freshly **API-created** agent DOES get `meta.default_version_id` = its `base` version's
  own id (verified live 2026-08-27 on three agents: 10352, 10356, 10367 — each == `versions[0].id`).
  "Nothing is pinned on a new agent" is FALSE; do not infer pin state from list position.
- The pin is still communicated — just by icon, not position: `VersionIconBlock.jsx` renders
  `data-testid="version-option-pin-icon"` + `aria-label="Default version"` on the default version only.
- `set_current_version_as_default()` (actions menu → confirm dialog) still works: PATCH 200,
  pin icon moves correctly.

## Other drift from the same PR

Option text is now `"{name}" + "Mon DD, YYYY, HH:MM · by {Author}"` (two sibling nodes inside the
same `version-option-{name}` element, rendered by the new `VersionSelectOption.jsx` +
`formatVersionMeta()`). The old `"{name} - DD.MM.YYYY"` shape is gone. Note the new format now
DOES include time-of-day, so it matches TMS wording ("date/time") better than the old one did.

New affordance: `version-option-set-default-{name}` — an inline set-default pin button on each
non-default, non-published option row.

Related: [[project_briefing]]
