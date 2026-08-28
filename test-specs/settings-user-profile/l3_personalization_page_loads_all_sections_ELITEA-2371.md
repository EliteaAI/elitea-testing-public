# Test Case: Personalization page loads with all sections visible and correctly structured

## Metadata
- **TMS ID**: ELITEA-2371
- **Priority**: l3 (case priority `medium`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (auth via `auth_state` / `VITE_DEV_TOKEN` on localhost)
- **Analyst**: qa-engineer (Sage), batch `settings-w08`, cluster ELITEA-2371/2372/2373/2380/2387, 2026-08-28
- **Status**: **blocked** — the subject of the case does not exist in the product
- **Surface digest**: `test-specs/settings-user-profile/_surface.md`
- **Filed**: clarification **#1960** (this cluster). Siblings: #1238, #1772.

---

## Why this is `blocked` and not `ready-for-automation`

The case's subject is **one page** that carries a profile area *and* five collapsible
sections, all "expanded by default", all loading without blank areas. **No such page
exists**, and the divergence is not a rename or a moved route — the content the case
describes is distributed across **three** different pages plus **one section that renders
nowhere**:

| Case step | Case expects | Live product (verified 2026-08-28) |
|---|---|---|
| 1 | Navigate to Personalization | `GET /settings/personalization` → the app's global **"Page not found. Try Home page"** view. No Settings drawer, no `settings-content`. No `personalization` item in the drawer (12 `settings-nav-item-*` nodes: 6 PROJECT + 6 PERSONAL, PERSONAL = Profile / Preferences / AI Personality / Memory / Personal Tokens / Notifications) |
| 2 | Page header shows "Personalization" | Nearest page header is **`Preferences`** (`/settings/preferences`) |
| 3 | Profile area at top: avatar, display name, email | Only on **`/settings/profile`** — a different page, with no accordion sections at all |
| 5 | `GENERAL` section | `/settings/preferences` |
| 6 | `DEFAULT CONTEXT MANAGEMENT` (+ nested `DEFAULT SUMMARIZATION`) | `/settings/memory`, titled `CONTEXT MANAGEMENT` / `Automatic Summarization` (tracked on #1238) |
| 7 | `LONG-TERM MEMORY` section | **Renders nowhere** — `MemoryLongTermMemory.jsx`'s only import is commented out (`MemoryContextManagement.jsx:13`); `grep -rn "MemoryLongTermMemory" src/` finds no live importer |
| 8 | `VOICE PERSONALIZATION` section | `/settings/preferences` |
| 9 | `SOUND NOTIFICATIONS` section | `/settings/preferences` |
| 10 | All sections expanded by default | True **per page** — `BasicAccordion` defaults `defaultExpanded = true`, and all three Preferences accordions plus `CONTEXT MANAGEMENT` read `aria-expanded="true"` on load |
| 11 | No blank areas / errors / permanent loading | Holds per page, except the known console error **#1771** (`disableUnderline`) on `/settings/memory` |

Rewriting this into "the Preferences page loads with its three sections" would **change
what is verified** — it drops the profile area, the context-management section and the
long-term-memory section, i.e. more than a third of the case including two of its five
named sections. Per `.agents/role-overrides.md` § Declared-improvisation protocol
(ceiling #1), changing *what* a case verifies is a **human decision**, not something an
analyst declares its way past. So this is routed rather than reshaped.

**This is NOT a product defect.** Every individual page loads correctly. The case text is
stale; the clarification is #1960.

---

## Blocked Steps

| Blocked element | What is needed to unblock |
|---|---|
| Steps 1–2 (the page itself) | A human decision on the TMS case: **split** it into per-page structural cases (`Preferences` sections; `Memory` sections; `Profile` identity area) — or **retire** it as superseded by ELITEA-2372 (collapse/expand) + ELITEA-2373 (profile area) + ELITEA-2242 (drawer inventory / default tab, already automated) |
| Step 3 (profile area on this page) | Covered elsewhere: ELITEA-2373, `/settings/profile` |
| Step 7 (`LONG-TERM MEMORY`) | The section must actually ship (uncomment the import). Same blocker as ELITEA-2380 |

## What already covers the case's *intent* (for whoever triages this)

- **Sections load / are expanded by default** — asserted in ELITEA-2372's Step 1 for all
  four existing sections.
- **Profile area (avatar / name / email)** — ELITEA-2373.
- **Settings drawer inventory + default landing tab** — already automated:
  `automation/tests/ui/settings/test_settings_page_sections_and_default_tab.py` (ELITEA-2242).

If the human decision is "split", the residual new coverage this case would add is small:
a per-page "renders without blank areas / permanent loading / console errors" assertion for
`/settings/preferences`. That is one cheap spec, and it is worth writing **as its own case**
rather than under this id.

---

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 — navigate to Personalization | page loads | — | — | **blocked** (route 404s) |
| Step 2 — header "Personalization" | header text | — | — | **blocked** (no such header) |
| Step 3 — profile area: avatar / name / email | shown | ELITEA-2373 (different page) | — | **out-of-scope here** |
| Steps 4–5 — `GENERAL` present | present | ELITEA-2372 Step 1 | — | **out-of-scope here** |
| Step 6 — `DEFAULT CONTEXT MANAGEMENT` present | present | ELITEA-2372 Step 6 | — | **out-of-scope here** |
| Step 7 — `LONG-TERM MEMORY` present | present | — | — | **blocked** (never rendered; ELITEA-2380) |
| Step 8 — `VOICE PERSONALIZATION` present | present | ELITEA-2372 Step 5 | — | **out-of-scope here** |
| Step 9 — `SOUND NOTIFICATIONS` present | present | ELITEA-2372 Step 5 | — | **out-of-scope here** |
| Step 10 — all expanded by default | `aria-expanded="true"` | ELITEA-2372 Step 1 | — | **out-of-scope here** |
| Step 11 — no blank areas / errors / loading | clean load | — | — | **blocked** (no page to assert it on) |

### Axis 2 — observables asserted beyond the case
None — no spec is produced by this AFS.

---

## Handles observed (for whoever picks this up after the human decision)

`settings-content`, `settings-nav-item-{tabId}` (+ `data-active`), `settings-drawer`,
`settings-drawer-menu` — all on `automation/testids`, none on `main` (verified with
`git fetch origin`, 2026-08-28). Section-level handles and their `testid needed` rows are
enumerated in ELITEA-2372's AFS; the profile-area handles in ELITEA-2373's.
