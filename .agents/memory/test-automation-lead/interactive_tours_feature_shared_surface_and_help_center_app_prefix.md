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
