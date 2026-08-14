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
- **UPDATE 2026-08-06 (ELITEA-2437 analysis)**: both gaps below are now CLOSED for the **Agent** flow —
  confirmed live via source read of current `version.helpers.jsx` /
  `useSetDefaultVersion.hooks.jsx`: `version-option-pin-icon` is landed (unconditional on the
  default-version row), and `agent-set-default-version-confirm-button` is landed and wired. **But a THIRD
  gap this 2026-08-02 entry never called out is still open, for ALL consumers (agent/skill/pipeline)**:
  the *clickable* "set as default" hover icon on a NON-default row (`version.helpers.jsx`'s
  `<Box id="show-on-hover" onClick={() => handleSetDefaultVersion(id)}>` wrapping a bare `<PinIcon />`)
  has NO testid at all — only a non-unique CSS `id="show-on-hover"` used purely for the hover-reveal
  styling. This is the ACTUAL trigger a test must click to change the default version; the
  `version-option-pin-icon` testid only marks the *already-default* row, it isn't clickable/actionable.
  Full writeup + the Skill-side confirm-button gap (Skill's `EditSkill.jsx` never wires
  `confirmButtonTestId`, unlike Agent):
  `test-specs/skills/l3_skill-version-dropdown-set-default_ELITEA-2437.md`.
- **Two testid gaps in the pin flow, as they stood on 2026-08-02** (historical — see UPDATE above for
  current state):
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
