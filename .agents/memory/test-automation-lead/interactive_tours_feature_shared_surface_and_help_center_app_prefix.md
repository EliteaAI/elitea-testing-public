---
name: Interactive Tours feature — shared reusable surface (ELITEA-2227) + Help Center /app-prefix quirk
description: EliteaUI's 17-variant Interactive Tours feature now has shared generic testids + page-object components from ELITEA-2227 — future tour cases (chat/agent/pipeline/...) reuse them for free. Also documents a localhost-only, correctly-not-filed link quirk.
type: reference
---

## Context

ELITEA-2227 ("Help Center — Sidebar Interactive Tour") was the FIRST automated
case to touch EliteaUI's `src/[fsd]/features/interactive-tours/` (55 files,
backs 17 different tour configs: sidebar, chat, agent, pipeline, artifact,
mcp, users, ai-configuration, applications, notifications, personal-tokens,
resources, secrets, toolkit, elitea-catalog, first-elitea). Before this case
the whole feature had ZERO `data-testid` attributes anywhere.

## What now exists (reusable — check before treating a new tour case as greenfield)

- **13 new testids**, all deliberately generic (not sidebar-specific), on
  `EliteaAI/EliteaUI@1f76dab9` (`automation/testids`, NOT yet on `main` as of
  2026-08-05 — re-check promotability before assuming): `interactive-tour-title`,
  `-description`, `-step-counter`, `-skip-button`, `-back-button`,
  `-next-button`, `-spotlight`, `interactive-tour-complete-icon`, `-title`,
  `-keep-exploring-label`, `-done-button`, plus dynamic
  `interactive-tour-complete-keep-exploring-{tourId}` and Help-Center-specific
  `help-center-page-header` / dynamic `help-center-tour-link-{slug}`.
- **`automation/components/interactive_tour.py`** — `InteractiveTourCard` +
  `TourCompleteCard`, generic across every tour variant.
- **`automation/pages/help_center_page.py`** — Help Center page object (only
  needed if the next case also enters via Help Center; a tour reached from
  elsewhere, e.g. the in-app "Chat Interactive Tour" trigger, needs its own
  entry-point page object but the SAME tour components).

A future tour case (the sibling "Chat Interactive Tour" is directly reachable
from this case's own Tour Complete screen, and pipeline/agent/mcp/etc. tours
exist too) should need **zero new testid work for the shared dialog/modal/
spotlight chrome** — only a new entry-point locator and possibly new
content-specific assertions (tour step count/titles differ per variant).

## Two things NOT to reach for

- **`data-tour="<id>"`** — a pre-existing non-testid attribute
  (`buildTourSelector()`) used internally by the tour library for spotlight
  targeting. Looks like a stable selector at a glance; it is NOT `data-testid`
  and is deliberately excluded from the locator table per the testid-only
  policy.
- **Help Center resource links hardcode an `/app` URL prefix** (backend-CMS
  config via `useGetResourcesConfigQuery`, not EliteaUI source) — correct on
  deployed envs, 404s the main content area on **localhost only**. The tour
  overlay itself is unaffected and runs correctly regardless. Correctly
  classified as a localhost-only artifact, NOT a product defect — not filed.
  A verified workaround for a case needing literal post-tour page-identity
  assertions: direct navigation to `<page>?tour=<id>` instead of clicking the
  CMS link.

## Where the full detail lives

`test-specs/help-center/_surface.md` (analyst-written digest) and
`test-specs/help-center/l2_sidebar-interactive-tour-completes_ELITEA-2227.md`
(the AFS, § Automation Hints).

## Help Center testid provenance — re-verified 2026-09-29 (#2382 / ELITEA-2219)

Sizing ELITEA-2219 ("page loads successfully via sidebar icon") forced a fresh
two-stage grep of both refs. **The reusability promise above holds for the tour
chrome and NOT for the resources page itself** — correcting the optimistic
reading a future case would otherwise make:

| Handle | `main` | `automation/testids` |
|---|---|---|
| `help-center-page-header` | ✅ | ✅ |
| `help-center-tour-link-<slug>` (runtime-composed) | ✅ | ✅ |
| `help-center-version-label` / `-version-info-icon` / `-version-info-tooltip` / `-version-info-copy-button` | **no** | ✅ |
| sidebar `?` Help Center entry (`ResourcesButton.jsx` — only `StyledTooltip title="Help Center"`) | **no** | **no** |
| `Explore Help Center` subtitle (`ResourcesPage.jsx:97`) + description line | **no** | **no** |
| `ui/ResourceCard.jsx` title / subtitle / icon | **ZERO testids** | **ZERO testids** |

Three consequences for the next Help Center case:

1. **`ResourceCard.jsx` is greenfield testid work**, not a footnote — any case
   asserting per-card icon/title/subtitle/link pays for it.
2. **Four `help-center-version-*` testids are on `automation/testids` but not on
   `main`**, so any case using the existing page object's version helpers lands a
   closure record whose promotability row is ⚠️ NOT promotable *independently of
   what that case adds*. Check before promising otherwise.
3. **The page component is RENAMED on `main`.** `src/[fsd]/pages/resources/index.jsx`
   (on `automation/testids`) is `ResourcesPage.jsx` on `main`, plus new `index.js` /
   `ui/index.js` barrels; `main...origin/automation/testids` = **158 / 497**. A testid
   born on `automation/testids` therefore lands in a file `main` no longer has under
   that name ⇒ the human cherry-pick **conflicts by construction**. Sync
   `automation/testids ← main` *before* adding testids on this surface.

Also confirmed in source: `RESOURCE_CARD_CONFIGS` holds exactly **five** entries
(documentation, release notes, video library, tutorials, interactive tours), which
settles the "four vs five cards" case-text drift tracked as **#998** — a case-text
clarification, never a product defect. `#1492` (Release Notes link target 404s) is
out of scope for any case that only asserts links are *displayed*.
