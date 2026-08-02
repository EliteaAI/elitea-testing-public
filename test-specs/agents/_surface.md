# Agents surface — exploration digest

Handle cache for live-confirmed handles/quirks on the Agent detail page's VERSION area
(`/agents/all/{id}?viewMode=owner`). Not a substitute for execution — verify a handle as you use it.
One writer at a time; last confirmed by: qa-engineer analyst, ELITEA-1890/1891 run.

## VERSION selector (all pre-existing, confirmed live repeatedly across ELITEA-1888/1889/1892/1890/1891)
- `agent-version-selector-trigger` — combobox trigger, text = current version name only (no date/status).
- `version-option-{version_name}` — dynamic per-option testid (`AgentDetailPage.VERSION_OPTION` template).
  Option text = `"{name} - {DD.MM.YYYY}"` (date baked into the SAME node's text, no separate handle; no
  time-of-day shown despite some case text saying "date/time").
- `agent-actions-menu-button` → overflow menu; `publish-version-menuitem` / `unpublish-version-menuitem` /
  `set-as-a-default-menuitem` all derive automatically from `DotMenu.jsx`'s `testId: item.key` mechanism
  (`ApplicationControls.jsx`'s menu-item `key` fields) — confirmed live for all three.

## Sort order (VersionSelect.jsx `versionSelectOptions`, code-confirmed + live-confirmed)
`[pinned/default version] → [everything else by created_at DESCENDING, Published/Draft interleaved, NO
status tier] → [base, ONLY if base is not itself pinned]`. A freshly created agent's `meta.default_version_id`
already equals its own base version's id, so **base is pinned (and sorts FIRST) on a brand-new agent** —
it only moves to last once a different version is explicitly pinned. Case text that implies "Published
always sorts above Draft" or "base always sorts last" is stale — see
EliteaAI/elitea-testing-public#1091 for the full write-up.

## Pin ("Set as a default") flow
- Trigger: `agent-actions-menu-button` → `set-as-a-default-menuitem` (aria-disabled="true" when the
  currently-viewed version IS already default).
- Opens `SetDefaultVersionDialog` — **NO testid on its confirm button** ("Set as a default", plain text
  match only) or Cancel button. **Testid gap** — needed by any case that must actively re-pin a version.
- Pin icon (`PinIcon`) renders inside the option list (`buildVersionOption`'s `IconBlock`, no testid) AND
  inside the closed trigger's `customRenderValue` (`VersionSelect.jsx`, no testid). **Testid gap** on
  both; only the option-list one has been needed/flagged so far (ELITEA-1891) — flag the trigger one too
  if a future case needs to assert the pin icon on the CLOSED selector specifically.
- `PUT/POST .../default_version/prompt_lib/{project}/{agentId}` fires on confirm.

## Save As Version / Publish (fully testid'd, see ELITEA-1888/1892 AFS for the complete handle table)
- `agent-save-as-version-button` → `agent-version-dialog-name-input` → `agent-version-dialog-save-button`.
- `publish-version-menuitem` → 3-step wizard (`agent-publish-version-name-input`,
  `agent-publish-category-select`, `agent-publish-agree-checkbox`, `agent-publish-continue-button` →
  AI `publish_validate` gate → `agent-publish-confirm-button`). Publish clones the version rather than
  flipping status in place; auto-navigation after Publish is unreliable (issue #614) — always
  explicitly re-select the new version by name afterward, never trust the URL to land there.
- AI validation gate needs: non-empty Tags + substantive (non-trivial) Instructions to pass on the first
  attempt — seed both directly in the agent-creation API payload to avoid throwaway `422` round-trips.

## Known defects reproduced (not new, don't re-file)
- #611 — Publish-wizard Stepper leaks MUI boolean props onto `<svg>`, 4 console warnings, cosmetic only.
- #614 — post-Publish/re-pin client-side status staleness (VERSION trigger, overflow-menu Publish/Unpublish
  item can lag the true server state for a beat); `select_version_by_name()` / `wait_for_publish_status_menuitem()`
  on `AgentDetailPage` already harden against it with retry+reload+API-tie-breaker patterns.

## Agent creation payload gotcha (still open, #524)
`temperature` + a non-`"none"` `reasoning_effort` 400s on the project's default reasoning-capable model.
Every disposable-agent fixture in this area uses `reasoning_effort: "none"` and omits `temperature`.
