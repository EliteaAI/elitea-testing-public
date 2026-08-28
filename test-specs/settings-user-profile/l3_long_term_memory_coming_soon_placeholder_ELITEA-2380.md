# Test Case: Long-term memory section shows a "Coming soon" placeholder

## Metadata
- **TMS ID**: ELITEA-2380
- **Priority**: l3 (case priority `medium`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (auth via `auth_state` / `VITE_DEV_TOKEN` on localhost)
- **Analyst**: qa-engineer (Sage), batch `settings-w08`, cluster ELITEA-2371/2372/2373/2380/2387, 2026-08-28
- **Status**: **blocked** — the section under test is not rendered anywhere in the product
- **Surface digest**: `test-specs/settings-user-profile/_surface.md`
- **Filed**: clarification **#1960**

---

## Why this is `blocked`

The component the case describes **exists in source and is dead code**:

```
src/[fsd]/features/settings/ui/memory/MemoryLongTermMemory.jsx        # exists
  → title: 'Long-term Memory'
  → body:  "Coming soon - Manage what the AI remembers about you across conversations"

src/[fsd]/features/settings/ui/memory/MemoryContextManagement.jsx:13
  // import MemoryLongTermMemory from './MemoryLongTermMemory';        # COMMENTED OUT
```

`grep -rn "MemoryLongTermMemory" src/` returns only the definition, the commented import
and its own `displayName`/`export` — **no live importer anywhere in the codebase**.

Confirmed live (2026-08-28), not inferred from source:
- `/settings/memory` renders exactly **one** accordion, `CONTEXT MANAGEMENT`. Its full
  text contains no `Long-term` and no `Coming soon` (regex-tested on
  `[data-testid="settings-content"]` innerText: both `false`).
- `/settings/preferences` renders `GENERAL`, `VOICE PERSONALIZATION`, `SOUND NOTIFICATIONS`
  — no long-term-memory section.
- `/settings/personalization` (the route the case names) → **"Page not found"**.

Every step of the case reads the section's own content, so there is nothing to assert
against the real system and **no honest substitute**: producing the observable would mean
mounting a component the product does not mount (a terminal substitution — forbidden by
`.agents/testing.md` § Fidelity policy; the case text does not ask for simulation).

**Not a product defect** — an unreleased feature that was deliberately commented out is not
a bug, and filing it as one would create false red. Filed as clarification #1960.

---

## Blocked Steps

| Case step | Blocked because | Unblocks when |
|---|---|---|
| 1 — Navigate to Personalization → LONG-TERM MEMORY | route 404s **and** the section does not exist | a human decides: park until the feature ships, or retire the case |
| 2 — section is visible and expandable | nothing renders | `MemoryContextManagement.jsx:13`'s import is uncommented (or the section is mounted elsewhere) |
| 3 — "Coming soon" message about what the AI remembers | copy exists in the file, never in the DOM | same |
| 4 — no interactive controls in the section | — | same |
| 5 — no error state | — | same |

**Recommended disposition for the lead:** park the case (`Blocked`, `Waiting on` the
clarification #1960 decision). When the section ships, this AFS becomes trivially
executable — the expected copy and structure are already captured below.

---

## Handles for when the section ships (captured from source, NOT yet verifiable live)

`MemoryLongTermMemory.jsx` renders a `BasicAccordion` with `title: 'Long-term Memory'` and a
single `<Typography>` body. When it is mounted it will need, per
`.agents/testing.md` § Locator policy:

| Element | Handle | Note |
|---|---|---|
| Section wrapper | `long-term-memory-section` | `<BasicAccordion data-testid=…>` — prop already supported (`BasicAccordion.jsx:40,45`) |
| Section header | `long-term-memory-section-header` | per-item `testId` → lands on the `AccordionSummary` (`BasicAccordion.jsx:70`); carries `aria-expanded` for the expandability assertion |
| "Coming soon" body | `long-term-memory-coming-soon-text` | pure attribute add on the existing `<Typography>` |
| "no interactive controls" (step 4) | absence assertion over `button, input, [role=checkbox], [role=combobox], textarea` scoped inside `long-term-memory-section` | absence assertions are first-class references (canon #511 extension) |

⚠️ These are **specified, not verified** — no element bearing them exists today. The next
analyst must re-execute the case live before an implementer builds it; do not treat this
table as a confirmed handle cache.

---

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 — navigate to the section | loads | — | — | **blocked** |
| Step 2 — visible and expandable | visible | — | — | **blocked** |
| Step 3 — "Coming soon" message | text shown | — | — | **blocked** |
| Step 4 — no interactive controls | none | — | — | **blocked** |
| Step 5 — no error state | clean | — | — | **blocked** |

### Axis 2 — observables asserted beyond the case
None — no spec is produced by this AFS.
