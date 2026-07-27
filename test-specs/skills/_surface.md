# Surface digest: Skills (`/skills/all`, `/skills/all/{id}`, `/skills/create`)

Confirmed handles/waits/quirks from live exploration. This is a cache for
same-surface analysts and the implementer — it does NOT replace live
execution; verify handles as you use them, and update this file (create or
edit) after your own run. Lives on the base branch — commit alongside your
AFS, never on a case branch.

## Skill Import flow (`SkillImportModal.jsx`, `useSkillImport.hooks.js`) — GAP-061, 2026-07-24

Entry point: Skills-list toolbar Import button
(`skills-import-button` — **on-`automation/testids` ✓**, already wired as
`SkillsListPage.import_button`).

| Purpose | Testid | Status |
|---|---|---|
| Import button | `skills-import-button` | on-`automation/testids` ✓ |
| Preview dialog container | `skill-import-preview-dialog` | on-`automation/testids` ✓ |
| Preview name | `skill-import-preview-name` | on-`automation/testids` ✓ |
| Preview "Type: ... \| Version: ..." | `skill-import-preview-type-version` | on-`automation/testids` ✓ — **hardcoded literal** `"Type: Skill \| Version: base"` (`LATEST_VERSION_NAME` constant), unconditional on the uploaded file's own frontmatter — confirmed for both a same-project import (ELITEA-1737/1738) and a fresh static fixture (GAP-061) |
| Preview description (expandable) | `skill-import-preview-description` | on-`automation/testids` ✓ |
| Preview instructions (expandable) | `skill-import-preview-instructions` | on-`automation/testids` ✓ |
| Success/error toast | `toast-message` | on-`automation/testids` ✓ — generic app-wide Toast container, reused across success AND error severities (same as the ELITEA-1934 finding for MCP) |
| **PROJECT selector (dialog)** | none — **`testid needed: skill-import-project-select`** | `<ProjectSelect name="skillImportProject" .../>` in `SkillImportModal.jsx` (~line 46) has no `data-testid`. One-line fix: add the prop directly to the JSX element — it flows through `ProjectSelect`'s `...last` spread into `SingleSelect`'s `dataTestId`, which wires BOTH `data-testid={dataTestId}` on the trigger `<Select>` and `SelectDisplayProps={{'data-testid': `${dataTestId}-combobox`}}` on its display div. No component-internals change needed. |
| PROJECT dropdown option (dynamic) | `select-option-{projectId}` | **on-`automation/testids` ✓ already** — same shared `SingleSelectMenuItem` family used by the Fork wizard's project picker (ELITEA-1893: `select-option-399/400/471`); confirmed live it ALSO fires correctly for this dialog's options without any extra wiring. |
| **Dialog Import (confirm) button** | none — **`testid needed: skill-import-confirm-button`** | Bare `Button.BaseBtn` in `SkillImportModal.jsx`'s `actions`. Add `data-testid="skill-import-confirm-button"` directly. |
| Dialog Cancel button | none (not yet needed) | Only add `skill-import-cancel-button` when a case actually clicks Cancel — GAP-061 doesn't; don't add it speculatively (scope discipline, `.agents/role-overrides.md`). |

### Behavior confirmed live

- **Wrong-extension rejection is 100% client-side, no network call**:
  `useSkillImport.hooks.js`'s `stageFile()` checks
  `!file.name.toLowerCase().endsWith('.md')` BEFORE any request; on failure
  shows `toastError('Only .md files can be imported.')` and never sets
  `pending` (so the preview dialog's `isModalOpen: !!pending` stays false —
  it never renders at all, confirmed via `document.querySelector` +
  `[role="dialog"]` count `0`).
- **Frontmatter validation is the second client-side gate**: a `.md` file
  whose frontmatter is missing `name` or `description` gets a different
  toast (`` `The [${file.name}] is missing required metadata...` ``) — not
  independently live-verified this session (GAP-061's case doesn't exercise
  it), but confirmed by reading `stageFile()` source; flag as a candidate
  observable for a future case on this same hook.
- **Cross-project import correctly skips navigation.** `confirmImport()`
  compares `importProjectId` (the dialog's locally-selected target) against
  `projectId` (the app's active project); only navigates
  (`goToSkill(result.id)`) when they're equal. Confirmed live: importing
  into a DIFFERENT project (`400`/"UI Testing" while `399`/"Private" was
  active) left the URL and page `<title>` completely unchanged
  (`http://localhost:5173/skills/all`, `"Skills: all - Private"`)
  immediately after the confirm click — the app never navigates away, by
  design, not by omission.
- **The dialog's PROJECT selector is local component state**
  (`useState` inside `SkillImportModal.jsx`, `forLocalUsage` mode on the
  shared `ProjectSelect`) — selecting a different project INSIDE the
  dialog does **not** touch the global Redux `project` / the navbar's
  `project-selector-trigger`. The app's active project is unaffected by
  what you pick in this dialog; only the import's OWN target changes.
- **Steps "reject invalid file" → "retry with valid file" work correctly
  back-to-back in the same page session** — no stale detached `<input>`
  or app-side leakage between two consecutive `openFileDialog()`
  invocations. Safe to implement as one continuous test.
- **File input mechanics (tooling note, not app behavior)**: the app's
  `openFileDialog()` (`useSkillImport.hooks.js`) creates the `<input
  type=file>` via `document.createElement`, sets `.accept = '.md,text/markdown'`,
  and calls `.click()` **without ever appending it to the document** — it
  stays a detached node the whole time. Playwright's
  `page.expect_file_chooser()` / `file_chooser.set_files()` handles this
  natively with no special-casing needed (this is exactly the API's
  purpose). A hand-rolled CDP harness (`DOM.setFileInputFiles` targeting a
  detached `backendNodeId`) does NOT reliably attach files to a detached
  node in this Chrome version — irrelevant to the real Playwright-based
  test, but worth knowing if a future analyst reaches for raw CDP on this
  same dialog.

### Cross-project test-data note (shared with the Fork-wizard finding, ELITEA-1893)

The fixed localhost `VITE_DEV_TOKEN` identity's permissions are **not**
uniform across projects. Confirmed-safe target for a "different project"
fixture, for BOTH agents (ELITEA-1893) AND skills (this session): `UI
Testing` (id `400`) — full create+delete, no permission toast, matches
`Private` (399)'s own default permission level. Avoid `Elitea Testing
Team` (471) for entity-delete cleanup unless independently re-verified for
the specific entity type — it's known to lack `application.delete` for
agents; not re-tested for skills, so treat as unconfirmed/risky rather
than assuming parity.

### Cleanup gotcha — `skill_api` fixture is single-project-scoped

`automation/fixtures/api_fixtures.py`'s session-scoped `skill_api` fixture
constructs `SkillAPI(browser_cookies=_browser_cookies)` with **no
`project_id` override** → defaults to `settings.elitea_project_id` (399).
Any test that imports/creates a skill in a DIFFERENT project must build its
own `SkillAPI(browser_cookies=_browser_cookies, project_id="<id>")`
directly (request the existing `_browser_cookies` fixture, don't re-derive
cookies) for that project's cleanup — the shared fixture will silently
target the wrong project.

## Skill detail page — existing testids (reused, no gaps, confirmed live again)

`skill-name-input-field`, `skill-description-input-field`,
`skill-tag-chip`, `skill-instructions-editor-content`,
`skill-version-select-combobox`, `skill-controls-menu-button`,
`skill-delete-menu-item` — all already wired via `SkillFormPage`/
`SkillDetailPage`, all confirmed present and correct via a live field
readback + full delete flow in project `400` this session. No changes
needed.
