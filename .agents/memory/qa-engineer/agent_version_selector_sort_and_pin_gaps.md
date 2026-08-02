---
name: Agent version-selector sort order and pin testid gaps
description: VersionSelect.jsx's real sort rule (pinned -> date-desc -> base-last, no status tier) and two pin-related testid gaps
type: project
---

Confirmed live + via code-read (`EliteaUI/src/[fsd]/entities/version/ui/VersionSelect.jsx`,
`versionSelectOptions` comparator) while analysing ELITEA-1890/1891:

- **Real sort rule**: `[pinned/default version] -> [everything else, by created_at DESCENDING —
  Published and Draft interleaved, NO status-based tier at all] -> [base, ONLY if base is not itself
  the pinned/default version]`. A case/spec that assumes "Published always sorts above Draft" is wrong —
  verified live by building base -> v1-draft -> v2-published -> v3-draft in that order and observing
  v3 (Draft, newest) sort ABOVE v2 (Published, older). Filed as a case-text clarification:
  EliteaAI/elitea-testing-public#1091.
- **A freshly created agent's `meta.default_version_id` already equals its own base version's id** —
  base is PINNED (sorts first, shows a pin icon) on a brand-new agent, not last. It only drops to the
  last position once a *different* version is explicitly re-pinned via "Set as a default". Any case
  that asserts "base appears last" needs to sequence that assertion AFTER re-pinning something else, or
  it will fail non-deterministically depending on the agent's freshness.
- **Two testid gaps in the pin flow** (both confirmed absent via live `.inner_html()` inspection,
  neither closed as of 2026-08-02):
  1. The pin `<svg>` icon rendered inside each `version-option-{name}` dropdown option
     (`version.helpers.jsx`'s `buildVersionOption` -> `IconBlock`) has no testid of its own — only the
     option's own `version-option-{name}` wrapper does. Scoped fix: chain a new
     `version-option-pin-icon` testid off the existing `VERSION_OPTION` template.
  2. `SetDefaultVersionDialog.jsx`'s confirm button ("Set as a default") has NO testid at all — any case
     that needs to actively re-pin a version (not just observe an already-pinned one) is blocked on this
     until `add-data-testid` closes it. Suggested name (unclaimed as of this writing):
     `agent-set-default-version-confirm-button`.
- The overflow menu's `set-as-a-default-menuitem` itself IS already testid'd (same generic `DotMenu.jsx`
  `testId: item.key` mechanism as `publish-version-menuitem`/`unpublish-version-menuitem`) — no gap there.
- Version-option text is `"{name} - {DD.MM.YYYY}"` — date is baked into the SAME text node as the name
  (no separate date handle), and only a date shows, never a time-of-day, despite some case text saying
  "date/time".

See `test-specs/agents/_surface.md` for the fuller digest (Publish/Save-As-Version handles, known
defects #611/#614/#524 reproduced-not-new in this area).
