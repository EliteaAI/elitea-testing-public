---
name: Skill Copy Link / Share menu pattern (ELITEA-2439)
description: SkillControls.jsx's two "Share" menuitems mirror AgentControls' useCopyLinkMenu 1:1
type: feedback
---

`SkillControls.jsx` wires the exact same `useCopyLinkMenu()` hook +
`DotMenu.jsx` `testId: item.key` convention as `ApplicationControls.jsx`
(Agent flow, ELITEA-1898) and the Pipeline flow (ELITEA-2049) — this is a
shared entity-agnostic pattern, not a Skill-specific feature. When a case
asks for "Copy Link" on any entity's detail/overflow menu, expect:

- Two visually-identical "Share" menu items, one per DotMenu section
  (VERSION-scoped and entity-scoped), never a standalone "Copy Link" button —
  case text describing a standalone button is case-text drift, file a
  sibling CLARIFICATION (don't treat it as a product bug). Existing
  siblings: #1288 (Agent), #1337 (Pipeline), #1451 (Skill).
- VERSION-group item: `share-version-menuitem`, built via
  `useProjectEntityLink({ versionId: currentVersionId })` → URL gains
  `/${versionId}` as a trailing path segment.
- Entity-group item (SKILL/AGENT/PIPELINE): `share-<entity>-menuitem`, built
  via `useProjectEntityLink()` with **no** `versionId` override → generic,
  version-less URL. This is the negative-control target for a "does the URL
  actually carry the version id" assertion — visually identical label, easy
  mis-click target for the wrong menuitem.
- Confirmation is always a toast, exact text
  `"The link has been copied to the clipboard."` (`toast-message` /
  `toast-alert[data-severity="info"]`), never a tooltip/icon-change — the
  menu closes on click (`DotMenu.jsx`'s `withClose`).
- Reading the clipboard: grant `["clipboard-read", "clipboard-write"]` on
  the `BrowserContext` before the click, clear the clipboard first
  (`navigator.clipboard.writeText('')`), then poll
  `navigator.clipboard.readText()` via `page.wait_for_function` — a raw
  MCP `browser_evaluate` call to `readText()` without a granted permission
  throws `NotAllowedError` (not a hang, in this session — differs from the
  ELITEA-1898 AFS's "hangs on a permission prompt" note, but same root
  cause: missing permission grant).
- `SkillDetailPage` had no page-object fields for either Share menuitem
  before ELITEA-2439 — both were pre-existing testids on `main` with zero
  prior LocatorDescriptor coverage. If another Skill case needs the same
  menu, the fields now exist (`share_version_menuitem`/`share_skill_menuitem`).
- A `base` version's Information-panel "Version ID" can differ from the
  Skill ID even when the URL shows only one digit segment (confirmed live:
  skill 951 shows Version ID 979 while its URL is just `/skills/all/951`).
  `SkillDetailPage.get_version_id()`'s URL-only parsing returns the skill id
  for `base`, not the true version id — only matters for a case that needs
  "the base version's real version id"; for a **named** version the URL
  always carries the real id as its second digit segment, so this doesn't
  affect the copy-link flow itself.
