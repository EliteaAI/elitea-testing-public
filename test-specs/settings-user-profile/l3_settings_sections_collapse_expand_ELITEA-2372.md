# Test Case: All collapsible settings sections can be collapsed and expanded

## Metadata
- **TMS ID**: ELITEA-2372
- **Priority**: l3 (case priority `medium`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (auth via `auth_state` / `VITE_DEV_TOKEN` on localhost)
- **Analyst**: qa-engineer (Sage), batch `settings-w08`, cluster ELITEA-2371/2372/2373/2380/2387, 2026-08-28
- **Status**: ready-for-automation (**case-text drift — asserts the LIVE contract**)
- **Surface digest**: `test-specs/settings-user-profile/_surface.md`
- **Filed**: clarification **#1960** (new, this cluster). Sibling of #1238 and #1772 — cross-linked, not a duplicate.
- **Cluster**: five cases, one live session. They differ in **steps**, not in data, so each has its own AFS.

---

## ⚠️ Case-text drift — read this before implementing

The case says "Navigate to Personalization" and then repeats the collapse/expand
cycle over five sections **on that one page**. There is no such page.

| Case text | Live product (verified 2026-08-28, localhost:5173) |
|---|---|
| "Navigate to Personalization" | `GET /settings/personalization` → the app's global **"Page not found. Try Home page"** view (no Settings drawer, no content pane). No `personalization` entry exists in the Settings drawer. |
| `GENERAL`, `VOICE PERSONALIZATION`, `SOUND NOTIFICATIONS` | All three on **`/settings/preferences`** (page header `Preferences`), in that DOM order. |
| `DEFAULT CONTEXT MANAGEMENT` | **`/settings/memory`**, accordion titled `CONTEXT MANAGEMENT` (already tracked by #1238). |
| `LONG-TERM MEMORY` | **Renders nowhere.** `MemoryLongTermMemory.jsx` exists but its import is commented out (`MemoryContextManagement.jsx:13`); `grep -rn "MemoryLongTermMemory" src/` finds no live importer. |

Per the reverse-masking guard, this spec asserts the **live** contract: the
collapse/expand behaviour of the four sections that actually exist, across the two
routes they actually live on. The fifth repetition (`LONG-TERM MEMORY`) is
unsatisfiable and is dispositioned `blocked` in the Coverage Map — it is **not**
silently dropped, and it is the subject of its own case (ELITEA-2380, `blocked`).

**Do not "fix" this by asserting the case's page**: `/settings/personalization` 404s.

---

## Preconditions
- User logged in (`auth_state`; login skipped on localhost via `VITE_DEV_TOKEN`).
- No seeding, no writes, no cleanup — accordion expand/collapse is **local UI state only**
  (MUI `Accordion` `defaultExpanded`, no persistence): verified live, a reload restores all
  sections to expanded. No autosave `PUT` fires on a header click (network capture confirmed:
  only the page's own `GET`s).
- Sections are **expanded by default** on both routes — `BasicAccordion`'s own default is
  `defaultExpanded = true` (`src/[fsd]/shared/ui/accordion/BasicAccordion.jsx:35`), so this
  holds even for `SoundNotificationSection`, which does not pass the prop.

## Test Data
### reuse-existing
None.

---

## Test Steps

### Step 1 — Open `/settings/preferences`
Navigate via the Settings drawer (`settings-nav-item-preferences`) or directly.
**Expected:** page renders; `settings-content` present; the three accordions
`GENERAL`, `VOICE PERSONALIZATION`, `SOUND NOTIFICATIONS` are present and each
summary carries `aria-expanded="true"`.

### Step 2 — Collapse `GENERAL` (chevron click on its header)
Click the accordion **summary** (the whole header row is the click target; the chevron
is inside it).
**Expected (observed live):**
- summary `aria-expanded` flips `"true"` → `"false"`;
- the section's content becomes **not visible** — the `MuiCollapse-root` gains
  `MuiCollapse-hidden`, `height: 0px`, and **`visibility: hidden`**.

### Step 3 — Verify the content is hidden
**Expected:** the section's content element is `not_to_be_visible()`.
⚠️ **`to_have_count(0)` is WRONG here** — MUI `Collapse` keeps children **mounted**
(verified live: `max-context-tokens-input` still returns count 1 while collapsed).
The children are invisible only because the collapse container is `visibility: hidden`,
which Playwright honours (`element.checkVisibility()` → `false`, verified live).
This is a *different* mechanism from the `context-management-toggle`'s conditional
unmount documented in `_surface.md` — don't reuse that assertion shape here.

### Step 4 — Expand `GENERAL` again (second chevron click)
**Expected:** `aria-expanded` back to `"true"`; the `MuiCollapse-root` returns to
`MuiCollapse-entered` with a non-zero height; the content is visible again.

### Step 5 — Repeat Steps 2–4 for `VOICE PERSONALIZATION` and `SOUND NOTIFICATIONS`
Same route, same assertions. Verified live for both (collapsed → `aria-expanded="false"`,
`height: 0px`; re-expanded → `"true"`, non-zero height).

### Step 6 — Repeat Steps 2–4 for `CONTEXT MANAGEMENT` on `/settings/memory`
Navigate to `/settings/memory` (`settings-nav-item-memory`). The accordion wrapper
already carries `context-management-section`.
**Expected:** identical collapse/expand behaviour. Verified live.
⚠️ **`/settings/memory` emits a known console error on every load** — the
`disableUnderline` React warning from `MemorySummarization.jsx`'s `StyledInputEnhancer`
(tracked as **#1771**). A "no console errors" step on this route needs that filter or
it is red for a pre-existing, unrelated defect. This spec asserts no console errors
**other than** #1771's `disableUnderline` message.

### Step 7 — (`LONG-TERM MEMORY`) — NOT EXECUTABLE
See § Blocked Steps.

---

## Concrete Handles

All handles are **testid-only** (`.agents/testing.md` § Locator policy). `BasicAccordion`
already supports both shapes needed, with **no new DOM node and no new hook** — it reads
`'data-testid': dataTestId` onto its wrapper `<Box>` and a per-item `testId` straight onto
the `StyledAccordionSummary` (`BasicAccordion.jsx:40,45,70`). So every handle below is a
pure prop/attribute add at the call site.

| Element | Handle | Provenance (verified `git fetch origin`, 2026-08-28) |
|---|---|---|
| Settings content pane | `settings-content` | on `automation/testids` (EliteaAI/EliteaUI@e1e031a1); **not on `main`** |
| Preferences nav item | `settings-nav-item-preferences` | on `automation/testids`; not on `main` |
| Memory nav item | `settings-nav-item-memory` | on `automation/testids`; not on `main` |
| GENERAL accordion wrapper | `preferences-general-section` | **testid needed** — `PreferenceGeneral.jsx`, `<BasicAccordion data-testid=…>` |
| GENERAL accordion header (click target + `aria-expanded`) | `preferences-general-section-header` | **testid needed** — same file, `items[0].testId` |
| VOICE PERSONALIZATION wrapper | `voice-personalization-section` | **on `automation/testids`** (pre-existing, `VoicePersonalizationSection.jsx:40`); main: verify at implementation |
| VOICE PERSONALIZATION header | `voice-personalization-section-header` | **testid needed** — same file, `items[0].testId` |
| SOUND NOTIFICATIONS wrapper | `sound-notifications-section` | **testid needed** — `SoundNotificationSection.jsx`, `<BasicAccordion data-testid=…>` |
| SOUND NOTIFICATIONS header | `sound-notifications-section-header` | **testid needed** — same file, `items[0].testId` |
| CONTEXT MANAGEMENT wrapper | `context-management-section` | on `automation/testids` (also on `main` per `_surface.md`) |
| CONTEXT MANAGEMENT header | `context-management-section-header` | **testid needed** — `MemoryContextManagement.jsx`, `items[0].testId` |
| Collapsed/expanded state | `aria-expanded` on the **header** testid | standard ARIA attribute — state on an attribute, never a state-switched testid (PR #581 ruling) |
| "content is hidden/visible" observable | an already-testid'd child inside each section | `max-context-tokens-input` (Memory); for Preferences use `voice-preview-button` (pre-existing) and, for GENERAL / SOUND NOTIFICATIONS, the section wrapper's own collapse container — see the note below |

**Note on the "content" observable for GENERAL / SOUND NOTIFICATIONS.** Neither section
has a testid'd child today. Two compliant options, implementer's call (declare which):
(a) assert `aria-expanded` on the header **plus** `to_have_css("visibility", "hidden")` on
a `[data-testid="<wrapper>"] .MuiCollapse-root`-shaped **class constant** — this is a raw
CSS hop off a testid parent and should be avoided if (b) is available; or (b) **preferred**
— add one testid on the section's own content `<Box>` (`preferences-general-content`,
`sound-notifications-content`), a pure attribute add on an existing node, and assert
`not_to_be_visible()`. Option (b) is the shape this AFS specifies.

⚠️ **`aria-controls` is NOT a usable discriminator**: `BasicAccordion` hardcodes
`panel-content-${index}` per *item*, and every section here is a one-item accordion, so
**all four sections share `aria-controls="panel-content-0"`** (verified live). Never key a
locator on it.

---

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 — Navigate to Personalization | page loads | Steps 1 + 6 (two real routes: `/settings/preferences`, `/settings/memory`) | page-load assertions | **clarification #1960** — the case's route 404s |
| Step 2 — click chevron on GENERAL | section collapses | Step 2 | `aria-expanded="false"` | covered |
| Step 3 — content hidden | content not visible | Step 3 | `not_to_be_visible()` on the content | covered |
| Step 4 — click again, expands, content visible | section expands | Step 4 | `aria-expanded="true"` + visible content | covered |
| Step 5 — repeat for DEFAULT CONTEXT MANAGEMENT | same | Step 6 | same assertions on `context-management-section` | covered (title is `CONTEXT MANAGEMENT`) |
| Step 5 — repeat for VOICE PERSONALIZATION | same | Step 5 | same | covered |
| Step 5 — repeat for SOUND NOTIFICATIONS | same | Step 5 | same | covered |
| Step 5 — repeat for LONG-TERM MEMORY | same | — | — | **blocked** — section does not render (see § Blocked Steps, ELITEA-2380, #1960) |

### Axis 2 — observables asserted beyond the case

| Extra observable | Why |
|---|---|
| All sections start `aria-expanded="true"` on load (Step 1) | The collapse assertion is meaningless without pinning the starting state; also pins `BasicAccordion`'s `defaultExpanded=true` default, which `SoundNotificationSection` relies on implicitly |
| No console errors other than the known #1771 `disableUnderline` warning | Side-channel discipline; the filter is named and scoped to one known-defect message, never a blanket suppression |
| Collapse state does **not** persist across a reload | Guards against someone "fixing" a flake by assuming persistence; verified live |

---

## Blocked Steps

- **`LONG-TERM MEMORY` repetition (case Step 5, one of five).** The section is dead code:
  `MemoryLongTermMemory.jsx` exists and contains the "Coming soon" copy, but its only
  import is commented out at `MemoryContextManagement.jsx:13`. Nothing in `src/` imports
  it. Confirmed live on `/settings/memory` and `/settings/preferences`: no `Long-term`
  and no `Coming soon` text anywhere. **This does not block the case** — the other four
  repetitions are fully executable — but the row must stay visible, and it is the entire
  subject of ELITEA-2380 (`blocked`). Tracked on #1960.

---

## Known traps

- **Collapsed ≠ unmounted.** See Step 3. The Memory page's *toggle* unmounts; the
  *accordion* only hides. Using the wrong assertion here passes for the wrong reason
  (or fails for the wrong reason).
- **`aria-controls` collides across all four sections** (`panel-content-0`).
- **`/settings/memory` console error #1771** fires on every load.
- The three Preferences accordions are siblings inside `settings-content`; positional
  `nth=` selectors work today but are forbidden — add the testids.
